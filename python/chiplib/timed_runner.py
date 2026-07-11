"""Deterministic digital timing primitives; not a physical signoff simulator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .events import EventPhase, EventScheduler, ScheduledEvent
from .timing import ConstraintKind, DelayKind, TimingProfile, TimingSelection

Logic4 = int | str


def normalize_logic4(value: object) -> Logic4:
    if value in (0, False) or str(value) == "0":
        return 0
    if value in (1, True) or str(value) == "1":
        return 1
    text = str(value).upper()
    if text in {"X", "Z"}:
        return text
    raise ValueError(f"logic value must be 0, 1, X, or Z, got {value!r}")


@dataclass(frozen=True)
class TimingDiagnostic:
    code: str
    time_ps: int
    signal: str
    message: str
    required_ps: int | None = None
    observed_ps: int | None = None
    provenance: str | None = None
    source: str | None = None
    modeled_only: bool = True

    def snapshot(self) -> dict[str, Any]:
        return dict(self.__dict__)


class TimedRunner:
    """Small integration surface for scheduler, timing profiles, and checks."""

    def __init__(self, *, max_delta_cycles: int = 1000):
        self.scheduler = EventScheduler(max_delta_cycles=max_delta_cycles)
        self.signals: dict[str, Logic4] = {}
        self.last_change_ps: dict[str, int] = {}
        self.last_edge_ps: dict[tuple[str, Logic4], int] = {}
        self.diagnostics: list[TimingDiagnostic] = []
        self.trace: list[dict[str, Any]] = []
        self._hold_windows: list[tuple[str, int, int, TimingSelection]] = []
        self._contention_active: set[str] = set()
        self._disabled_at: dict[str, int] = {}

    @property
    def time_ps(self) -> int:
        return self.scheduler.time_ps

    def drive(self, signal: str, value: Logic4, *, time_ps: int | None = None) -> None:
        value = normalize_logic4(value)
        self.scheduler.schedule(
            "drive", {"signal": signal, "value": value}, time_ps=time_ps,
            phase=EventPhase.APPLY_DRIVERS, transport=True,
        )

    def schedule_output(
        self, signal: str, before: Logic4, after: Logic4, profile: TimingProfile,
        *, path: str | None = None, clock_to_q: bool = False, transport: bool = False,
    ) -> TimingSelection:
        before, after = normalize_logic4(before), normalize_logic4(after)
        if "X" in {before, after}:
            selection = TimingSelection(
                DelayKind.LOW_TO_HIGH, 0, "unknown", "four_state_transition", "unknown", path,
                "X transitions have no datasheet delay class",
            )
            delay_ps = 0
        else:
            selection = profile.select(
                DelayKind.for_transition(before, after, clock_to_q=clock_to_q), path=path
            )
            if selection.delay_ps is None:
                raise ValueError(f"{profile.part}: transition is not applicable")
            delay_ps = selection.delay_ps
        self.scheduler.schedule(
            "timed_output",
            {
                "signal": signal, "value": after, "part": profile.part,
                "delay_kind": selection.kind.value, "provenance": selection.provenance,
                "source": selection.source, "modeled_only": True,
            },
            delay_ps=delay_ps, phase=EventPhase.APPLY_DRIVERS,
            cancellation_key=f"output:{signal}", transport=transport,
        )
        return selection

    def check_active_edge(
        self, clock: str, constrained_signals: Iterable[str], profile: TimingProfile,
        *, setup_path: str | None = None, hold_path: str | None = None,
    ) -> None:
        setup = profile.select_constraint(ConstraintKind.SETUP, path=setup_path)
        hold = profile.select_constraint(ConstraintKind.HOLD, path=hold_path)
        now = self.time_ps
        for signal in sorted(constrained_signals):
            observed = now - self.last_change_ps.get(signal, 0)
            if setup.delay_ps is not None and observed < setup.delay_ps:
                self._violation("timing.setup_violation", signal, setup, observed)
            if hold.delay_ps:
                self._hold_windows.append((signal, now, now + hold.delay_ps, hold))
        self.trace.append({"time_ps": now, "kind": "active_edge", "clock": clock})

    def check_clock_transition(
        self, clock: str, old: Logic4, new: Logic4, profile: TimingProfile,
        *, pulse_path: str | None = None,
    ) -> None:
        old, new = normalize_logic4(old), normalize_logic4(new)
        now = self.time_ps
        if "X" in {old, new} or "Z" in {old, new}:
            self.diagnostics.append(TimingDiagnostic(
                "timing.unknown_clock_edge", now, clock,
                f"clock transition {old}->{new} is not a recognized digital edge",
            ))
            return
        requirement = profile.select_constraint(
            ConstraintKind.MINIMUM_PULSE_WIDTH, path=pulse_path
        )
        prior = self.last_edge_ps.get((clock, old))
        if prior is not None and requirement.delay_ps is not None:
            observed = now - prior
            if observed < requirement.delay_ps:
                self._violation("timing.pulse_width_violation", clock, requirement, observed)
        self.last_edge_ps[(clock, new)] = now

    def resolve_bus(
        self, net: str, drivers: Mapping[str, Logic4], *, enforce_single_owner: bool = False
    ) -> Logic4:
        normalized = {name: normalize_logic4(value) for name, value in drivers.items()}
        owners = [name for name, value in normalized.items() if value != "Z"]
        active = {value for value in normalized.values() if value != "Z"}
        contention = "X" in active or (0 in active and 1 in active)
        ownership_overlap = enforce_single_owner and len(owners) > 1
        if contention or ownership_overlap:
            if net not in self._contention_active:
                self.diagnostics.append(TimingDiagnostic(
                    "simulation.bus_contention", self.time_ps, net,
                    "multiple active drivers violate bus ownership",
                ))
                self._contention_active.add(net)
            return "X" if contention else next(iter(active))
        self._contention_active.discard(net)
        if not active:
            return "Z"
        return next(iter(active))

    def mark_driver_disabled(self, net: str) -> None:
        self._disabled_at[net] = self.time_ps

    def mark_driver_enabled(self, net: str, *, required_deadband_ps: int) -> None:
        if required_deadband_ps < 0:
            raise ValueError("required deadband must be non-negative")
        disabled = self._disabled_at.get(net)
        if disabled is None:
            self.diagnostics.append(TimingDiagnostic(
                "timing.deadband_violation", self.time_ps, net,
                "driver enabled before another driver was observed disabled",
                required_ps=required_deadband_ps,
            ))
            return
        observed = self.time_ps - disabled
        if observed < required_deadband_ps:
            self.diagnostics.append(TimingDiagnostic(
                "timing.deadband_violation", self.time_ps, net,
                "bus ownership deadband is shorter than required",
                required_ps=required_deadband_ps, observed_ps=observed,
                provenance="circuit_constraint", source="circuit proof vector",
            ))

    def run_until(self, time_ps: int) -> tuple[ScheduledEvent, ...]:
        return self.scheduler.run_until(time_ps, self._dispatch)

    def snapshot(self) -> dict[str, Any]:
        return {
            "time_ps": self.time_ps,
            "signals": {key: self.signals[key] for key in sorted(self.signals)},
            "diagnostics": [item.snapshot() for item in self.diagnostics],
            "trace": list(self.trace),
            "scheduler": self.scheduler.snapshot(),
            "boundary": "modeled digital timing only; physical signoff requires measurement",
        }

    def _dispatch(self, event: ScheduledEvent, _scheduler: EventScheduler) -> None:
        if event.kind not in {"drive", "timed_output"}:
            return
        signal = event.payload["signal"]
        value = normalize_logic4(event.payload["value"])
        old = self.signals.get(signal, "Z")
        if value == old:
            return
        for held_signal, opened, deadline, selection in tuple(self._hold_windows):
            if signal == held_signal and opened < event.time_ps < deadline:
                self._violation("timing.hold_violation", signal, selection, event.time_ps - opened)
        self._hold_windows = [window for window in self._hold_windows if window[2] >= event.time_ps]
        self.signals[signal] = value
        self.last_change_ps[signal] = event.time_ps
        self.trace.append({
            "time_ps": event.time_ps, "kind": event.kind, "signal": signal,
            "before": old, "after": value,
            "provenance": event.payload.get("provenance"),
            "source": event.payload.get("source"),
        })

    def _violation(
        self, code: str, signal: str, selection: TimingSelection, observed_ps: int
    ) -> None:
        self.diagnostics.append(TimingDiagnostic(
            code, self.time_ps, signal,
            f"observed {observed_ps} ps is below required {selection.delay_ps} ps",
            selection.delay_ps, observed_ps, selection.provenance, selection.source,
        ))
