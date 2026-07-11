"""Deterministic runtime contracts for named virtual test instruments.

These adapters stimulate, observe, assert, or add modeled stress. They are not
physical chip models and never constitute hardware timing signoff.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import random
from typing import Any, Iterable, Mapping

from .timed_runner import normalize_logic4

Logic4 = int | str
MODELED_BOUNDARY = "modeled virtual instrument only; physical signoff requires measurement"


class VirtualRuntimeError(ValueError):
    """Raised when a virtual part has no safe executable contract."""


class OutputAssertionFailure(AssertionError):
    """Raised when an OutputAssert expectation does not match observation."""


@dataclass(frozen=True)
class VirtualTransition:
    time_ps: int
    value: Logic4
    kind: str = "drive"
    modeled_only: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.time_ps, int) or isinstance(self.time_ps, bool) or self.time_ps < 0:
            raise ValueError("transition time_ps must be a non-negative integer")
        object.__setattr__(self, "value", normalize_logic4(self.value))

    def snapshot(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class VirtualAdapter:
    ref: str
    part: str = field(init=False)
    role: str = field(init=False)
    modeled_only: bool = field(default=True, init=False)
    claim_boundary: str = field(default=MODELED_BOUNDARY, init=False)

    def snapshot(self) -> dict[str, Any]:
        return {
            "ref": self.ref,
            "part": self.part,
            "role": self.role,
            "modeled_only": self.modeled_only,
            "claim_boundary": self.claim_boundary,
        }


@dataclass
class ClockSourceAdapter(VirtualAdapter):
    period_ps: int = 100_000
    idle_state: Logic4 = 0
    part: str = field(default="ClockSource", init=False)
    role: str = field(default="stimulus", init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.period_ps, int) or isinstance(self.period_ps, bool) or self.period_ps < 2:
            raise ValueError("period_ps must be an integer of at least 2 ps")
        self.idle_state = normalize_logic4(self.idle_state)
        if self.idle_state not in (0, 1):
            raise ValueError("clock idle_state must be 0 or 1")

    def ticks(self, count: int, *, start_ps: int = 0) -> tuple[VirtualTransition, ...]:
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            raise ValueError("clock tick count must be a non-negative integer")
        if not isinstance(start_ps, int) or isinstance(start_ps, bool) or start_ps < 0:
            raise ValueError("start_ps must be a non-negative integer")
        active = 1 - self.idle_state
        half = self.period_ps // 2
        events: list[VirtualTransition] = []
        for index in range(count):
            origin = start_ps + index * self.period_ps
            events.append(VirtualTransition(origin, active, "clock_edge"))
            events.append(VirtualTransition(origin + half, self.idle_state, "clock_edge"))
        return tuple(events)

    def manual_tick(self, *, start_ps: int = 0) -> tuple[VirtualTransition, ...]:
        return self.ticks(1, start_ps=start_ps)


@dataclass
class SwitchAdapter(VirtualAdapter):
    state: Logic4 = 0
    part: str = field(default="Switch", init=False)
    role: str = field(default="stimulus", init=False)

    def __post_init__(self) -> None:
        self.state = normalize_logic4(self.state)
        if self.state not in (0, 1):
            raise ValueError("switch state must be 0 or 1")

    def set_state(self, value: Logic4, *, time_ps: int = 0) -> VirtualTransition:
        value = normalize_logic4(value)
        if value not in (0, 1):
            raise ValueError("switch state must be 0 or 1")
        self.state = value
        return VirtualTransition(time_ps, value, "switch")

    def pulse(self, duration_ps: int, *, start_ps: int = 0, active_state: Logic4 = 1) -> tuple[VirtualTransition, ...]:
        if not isinstance(duration_ps, int) or isinstance(duration_ps, bool) or duration_ps <= 0:
            raise ValueError("duration_ps must be a positive integer")
        active = normalize_logic4(active_state)
        if active not in (0, 1):
            raise ValueError("active_state must be 0 or 1")
        idle = 1 - active
        self.state = idle
        return (
            VirtualTransition(start_ps, active, "switch"),
            VirtualTransition(start_ps + duration_ps, idle, "switch"),
        )


@dataclass
class ProbeAdapter(VirtualAdapter):
    part: str = field(default="Probe", init=False)
    role: str = field(default="observation", init=False)
    samples: list[dict[str, Any]] = field(default_factory=list, init=False)

    def sample(self, value: Logic4, *, time_ps: int = 0) -> dict[str, Any]:
        sample = {"time_ps": time_ps, "value": normalize_logic4(value), "modeled_only": True}
        VirtualTransition(time_ps, sample["value"], "probe_sample")
        self.samples.append(sample)
        return dict(sample)

    def snapshot(self) -> dict[str, Any]:
        return {**super().snapshot(), "samples": list(self.samples)}


@dataclass
class BusProbeAdapter(VirtualAdapter):
    part: str = field(default="BusProbe", init=False)
    role: str = field(default="observation", init=False)
    samples: list[dict[str, Any]] = field(default_factory=list, init=False)

    def sample(self, drivers: Mapping[str, Logic4], *, time_ps: int = 0) -> dict[str, Any]:
        normalized = {name: normalize_logic4(value) for name, value in sorted(drivers.items())}
        owners = [name for name, value in normalized.items() if value != "Z"]
        active = {value for value in normalized.values() if value != "Z"}
        conflict = "X" in active or (0 in active and 1 in active)
        value: Logic4 = "X" if conflict else (next(iter(active)) if active else "Z")
        sample = {
            "time_ps": time_ps,
            "value": value,
            "drivers": normalized,
            "active_drivers": owners,
            "conflict": conflict,
            "modeled_only": True,
        }
        VirtualTransition(time_ps, value, "bus_probe_sample")
        self.samples.append(sample)
        return dict(sample)

    def snapshot(self) -> dict[str, Any]:
        return {**super().snapshot(), "samples": list(self.samples)}


@dataclass
class OutputAssertAdapter(VirtualAdapter):
    part: str = field(default="OutputAssert", init=False)
    role: str = field(default="assertion", init=False)
    checks: list[dict[str, Any]] = field(default_factory=list, init=False)

    def check(
        self, actual: Logic4, expected: Logic4 | None = None, *, mode: str = "equals",
        time_ps: int = 0, window_start_ps: int | None = None,
        window_end_ps: int | None = None,
    ) -> dict[str, Any]:
        actual = normalize_logic4(actual)
        expected_value = normalize_logic4(expected) if expected is not None else None
        in_window = (
            window_start_ps is not None and window_end_ps is not None
            and window_start_ps <= time_ps <= window_end_ps
        )
        predicates = {
            "equals": expected_value is not None and actual == expected_value,
            "not_equals": expected_value is not None and actual != expected_value,
            "is_high_z": actual == "Z",
            "is_unknown": actual == "X",
            "within_timing_window": expected_value is not None and actual == expected_value and in_window,
        }
        if mode not in predicates:
            raise VirtualRuntimeError(f"OutputAssert mode {mode!r} is not supported by this adapter")
        result = {
            "time_ps": time_ps, "mode": mode, "actual": actual,
            "expected": expected_value, "passed": predicates[mode], "modeled_only": True,
            "window_start_ps": window_start_ps, "window_end_ps": window_end_ps,
        }
        VirtualTransition(time_ps, actual, "assert_sample")
        self.checks.append(result)
        if not result["passed"]:
            raise OutputAssertionFailure(
                f"{self.ref} failed at {time_ps} ps: mode={mode}, actual={actual}, expected={expected_value}"
            )
        return dict(result)

    def snapshot(self) -> dict[str, Any]:
        return {**super().snapshot(), "checks": list(self.checks)}


@dataclass
class RCParasiticAdapter(VirtualAdapter):
    source_resistance_ohm: float = 50
    wire_capacitance_pf: float = 20
    chip_input_capacitance_pf: float = 10
    probe_capacitance_pf: float = 10
    extra_capacitance_pf: float = 0
    part: str = field(default="RCParasitic", init=False)
    role: str = field(default="timing_stress", init=False)

    def __post_init__(self) -> None:
        values = self._values()
        if any(value < 0 for value in values.values()):
            raise ValueError("R/C profile values must be non-negative")

    def _values(self) -> dict[str, float]:
        return {
            "source_resistance_ohm": float(self.source_resistance_ohm),
            "wire_capacitance_pf": float(self.wire_capacitance_pf),
            "chip_input_capacitance_pf": float(self.chip_input_capacitance_pf),
            "probe_capacitance_pf": float(self.probe_capacitance_pf),
            "extra_capacitance_pf": float(self.extra_capacitance_pf),
        }

    def estimate(self) -> dict[str, Any]:
        values = self._values()
        total_pf = sum(value for key, value in values.items() if key.endswith("capacitance_pf"))
        tau_ns = values["source_resistance_ohm"] * total_pf / 1000
        return {
            **values,
            "total_capacitance_pf": total_pf,
            "tau_ns": tau_ns,
            "settling_10_90_ns": 2.2 * tau_ns,
            "delay_ps": round(2.2 * tau_ns * 1000),
            "modeled_only": True,
            "claim_boundary": self.claim_boundary,
        }


@dataclass
class DelayNoiseAdapter(VirtualAdapter):
    seed: int
    base_delay_ps: int = 0
    jitter_ps: int = 0
    glitch_probability: float = 0.0
    glitch_width_ps: int = 0
    drop_edge_probability: float = 0.0
    part: str = field(default="DelayNoise", init=False)
    role: str = field(default="timing_stress", init=False)
    _rng: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.seed, int) or isinstance(self.seed, bool):
            raise ValueError("DelayNoise requires an integer deterministic seed")
        if any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in (self.base_delay_ps, self.jitter_ps, self.glitch_width_ps)):
            raise ValueError("delay and jitter values must be non-negative integer picoseconds")
        for name, value in (("glitch_probability", self.glitch_probability), ("drop_edge_probability", self.drop_edge_probability)):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        self._rng = random.Random(self.seed)

    def transform(self, transitions: Iterable[VirtualTransition]) -> tuple[VirtualTransition, ...]:
        output: list[VirtualTransition] = []
        for transition in transitions:
            if self._rng.random() < self.drop_edge_probability:
                continue
            jitter = self._rng.randint(0, self.jitter_ps) if self.jitter_ps else 0
            time_ps = transition.time_ps + self.base_delay_ps + jitter
            if self._rng.random() < self.glitch_probability:
                opposite: Logic4 = 1 - transition.value if transition.value in (0, 1) else "X"
                output.append(VirtualTransition(time_ps, opposite, "modeled_glitch"))
                output.append(VirtualTransition(time_ps + self.glitch_width_ps, transition.value, "delayed_drive"))
            else:
                output.append(VirtualTransition(time_ps, transition.value, "delayed_drive"))
        return tuple(output)


_ADAPTERS = {
    "ClockSource": ClockSourceAdapter,
    "Switch": SwitchAdapter,
    "Probe": ProbeAdapter,
    "BusProbe": BusProbeAdapter,
    "OutputAssert": OutputAssertAdapter,
    "RCParasitic": RCParasiticAdapter,
    "DelayNoise": DelayNoiseAdapter,
}


def create_virtual_adapter(part: str, ref: str, **config: Any) -> VirtualAdapter:
    """Create a named virtual adapter; generic or unknown placeholders fail loudly."""
    if part == "Virtual":
        raise VirtualRuntimeError(
            f"{ref}: generic Virtual has no executable contract; use a named virtual instrument"
        )
    adapter = _ADAPTERS.get(part)
    if adapter is None:
        raise VirtualRuntimeError(f"{ref}: unsupported virtual part {part!r}")
    if adapter is DelayNoiseAdapter:
        # Package wiring uses the deterministic no-noise profile unless a proof overrides it.
        config.setdefault("seed", 0)
    return adapter(ref=ref, **config)
