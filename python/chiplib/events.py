"""Deterministic, scheduler-only event queue using integer picoseconds."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import heapq
from typing import Any, Callable, Mapping


class EventPhase(IntEnum):
    """Same-delta processing order used by the circuit runner architecture."""

    APPLY_DRIVERS = 10
    RESOLVE_NETS = 20
    DETECT_TRANSITIONS = 30
    CHECK_TIMING = 40
    CAPTURE_SEQUENTIAL = 50
    EVALUATE_MODELS = 60
    COMMIT_STATE = 70
    SCHEDULE_OUTPUTS = 80
    SAMPLE_PROBES = 90


class SchedulerLimitError(RuntimeError):
    """Raised when bounded same-time execution cannot converge."""

    def __init__(self, code: str, snapshot: Mapping[str, Any]):
        super().__init__(f"{code} at {snapshot['time_ps']} ps")
        self.code = code
        self.snapshot = dict(snapshot)


@dataclass(frozen=True, order=True)
class ScheduledEvent:
    """One immutable and deterministically ordered scheduler event."""

    time_ps: int
    delta: int
    phase: EventPhase
    sequence: int
    event_id: int
    kind: str
    payload: Any
    cancellation_key: str | None = None
    generation: int | None = None
    transport: bool = False

    def snapshot(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "time_ps": self.time_ps,
            "delta": self.delta,
            "phase": self.phase.name,
            "phase_order": int(self.phase),
            "sequence": self.sequence,
            "kind": self.kind,
            "payload": _stable_value(self.payload),
            "cancellation_key": self.cancellation_key,
            "generation": self.generation,
            "transport": self.transport,
        }


EventHandler = Callable[[ScheduledEvent, "EventScheduler"], None]


class EventScheduler:
    """Priority queue independent of chips, nets, and the current core module."""

    def __init__(self, *, max_delta_cycles: int = 1000, max_same_time_events: int = 10_000):
        if max_delta_cycles < 0:
            raise ValueError("max_delta_cycles must be non-negative")
        if max_same_time_events < 1:
            raise ValueError("max_same_time_events must be positive")
        self.max_delta_cycles = max_delta_cycles
        self.max_same_time_events = max_same_time_events
        self.time_ps = 0
        self._queue: list[ScheduledEvent] = []
        self._sequence = 0
        self._event_id = 0
        self._generations: dict[str, int] = {}
        self._running_event: ScheduledEvent | None = None
        self._processed_events = 0

    def schedule(
        self,
        kind: str,
        payload: Any = None,
        *,
        delay_ps: int = 0,
        time_ps: int | None = None,
        phase: EventPhase = EventPhase.APPLY_DRIVERS,
        cancellation_key: str | None = None,
        transport: bool = False,
    ) -> ScheduledEvent:
        """Schedule an event; keyed events are inertial unless transport is true."""

        if not isinstance(kind, str) or not kind:
            raise ValueError("event kind must be a non-empty string")
        if isinstance(delay_ps, bool) or not isinstance(delay_ps, int) or delay_ps < 0:
            raise ValueError("delay_ps must be a non-negative integer")
        if time_ps is not None and delay_ps:
            raise ValueError("specify either time_ps or delay_ps, not both")
        due = self.time_ps + delay_ps if time_ps is None else time_ps
        if isinstance(due, bool) or not isinstance(due, int) or due < self.time_ps:
            raise ValueError("event time must be an integer at or after current time")
        phase = EventPhase(phase)
        payload = _stable_value(payload)

        delta = 0
        current = self._running_event
        if current is not None and due == current.time_ps:
            delta = current.delta + (phase <= current.phase)

        generation = None
        if cancellation_key is not None and not transport:
            generation = self._generations.get(cancellation_key, 0) + 1
            self._generations[cancellation_key] = generation

        self._sequence += 1
        self._event_id += 1
        event = ScheduledEvent(
            due, delta, phase, self._sequence, self._event_id, kind, payload,
            cancellation_key, generation, transport,
        )
        heapq.heappush(self._queue, event)
        return event

    def run_next_time(self, handler: EventHandler | None = None) -> tuple[ScheduledEvent, ...]:
        """Run all live events at the next physical timestamp, including deltas."""

        first = self._peek_live()
        if first is None:
            return ()
        target = first.time_ps
        self.time_ps = target
        result: list[ScheduledEvent] = []
        while True:
            event = self._peek_live()
            if event is None or event.time_ps != target:
                break
            heapq.heappop(self._queue)
            if event.delta > self.max_delta_cycles:
                self._raise_limit("scheduler.max_delta_cycles", event)
            if len(result) >= self.max_same_time_events:
                self._raise_limit("scheduler.max_same_time_events", event)
            self._running_event = event
            result.append(event)
            self._processed_events += 1
            if handler is not None:
                handler(event, self)
        self._running_event = None
        return tuple(result)

    def run_until(self, time_ps: int, handler: EventHandler | None = None) -> tuple[ScheduledEvent, ...]:
        """Run complete timestamps through ``time_ps`` and advance to the boundary."""

        if isinstance(time_ps, bool) or not isinstance(time_ps, int) or time_ps < self.time_ps:
            raise ValueError("run-until time must be an integer at or after current time")
        result: list[ScheduledEvent] = []
        while (event := self._peek_live()) is not None and event.time_ps <= time_ps:
            result.extend(self.run_next_time(handler))
        self.time_ps = time_ps
        return tuple(result)

    def snapshot(self) -> dict[str, Any]:
        """Return a stable, JSON-serializable view with stale inertial work omitted."""

        queue = [event.snapshot() for event in sorted(self._queue) if self._is_live(event)]
        return {
            "time_ps": self.time_ps,
            "processed_events": self._processed_events,
            "next_sequence": self._sequence + 1,
            "next_event_id": self._event_id + 1,
            "limits": {
                "max_delta_cycles": self.max_delta_cycles,
                "max_same_time_events": self.max_same_time_events,
            },
            "generations": {key: self._generations[key] for key in sorted(self._generations)},
            "queue": queue,
        }

    def _peek_live(self) -> ScheduledEvent | None:
        while self._queue and not self._is_live(self._queue[0]):
            heapq.heappop(self._queue)
        return self._queue[0] if self._queue else None

    def _is_live(self, event: ScheduledEvent) -> bool:
        return event.generation is None or self._generations.get(event.cancellation_key) == event.generation

    def _raise_limit(self, code: str, event: ScheduledEvent) -> None:
        self._running_event = None
        snapshot = self.snapshot()
        snapshot["blocked_event"] = event.snapshot()
        raise SchedulerLimitError(code, snapshot)


def _stable_value(value: Any) -> Any:
    """Copy a payload into a deterministic JSON-compatible representation."""

    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        if not all(isinstance(key, str) for key in value):
            raise TypeError("event payload mapping keys must be strings")
        return {key: _stable_value(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [_stable_value(item) for item in value]
    raise TypeError(f"event payload is not serializable: {type(value).__name__}")
