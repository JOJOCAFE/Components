"""Normalized, scheduler-independent component timing data."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, Mapping


class DelayKind(str, Enum):
    """Canonical output transitions and sequential clock-to-Q delays."""

    LOW_TO_HIGH = "tPLH"
    HIGH_TO_LOW = "tPHL"
    Z_TO_HIGH = "tPZH"
    Z_TO_LOW = "tPZL"
    HIGH_TO_Z = "tPHZ"
    LOW_TO_Z = "tPLZ"
    CLOCK_TO_Q_HIGH = "clock_to_q_high"
    CLOCK_TO_Q_LOW = "clock_to_q_low"

    @classmethod
    def for_transition(cls, before: object, after: object, *, clock_to_q: bool = False) -> "DelayKind":
        old = _logic_class(before)
        new = _logic_class(after)
        if clock_to_q:
            if new == "1":
                return cls.CLOCK_TO_Q_HIGH
            if new == "0":
                return cls.CLOCK_TO_Q_LOW
            raise ValueError("clock-to-Q transition must end at 0 or 1")
        try:
            return _TRANSITIONS[(old, new)]
        except KeyError as exc:
            raise ValueError(f"unsupported timing transition: {old}->{new}") from exc


_TRANSITIONS = {
    ("0", "1"): DelayKind.LOW_TO_HIGH,
    ("1", "0"): DelayKind.HIGH_TO_LOW,
    ("Z", "1"): DelayKind.Z_TO_HIGH,
    ("Z", "0"): DelayKind.Z_TO_LOW,
    ("1", "Z"): DelayKind.HIGH_TO_Z,
    ("0", "Z"): DelayKind.LOW_TO_Z,
}


class ConstraintKind(str, Enum):
    """Canonical sequential timing requirements."""

    SETUP = "setup"
    HOLD = "hold"
    MINIMUM_PULSE_WIDTH = "minimum_pulse_width"


@dataclass(frozen=True)
class TimingSelection:
    kind: DelayKind | ConstraintKind
    delay_ps: int | None
    provenance: str
    source: str
    status: str
    path: str | None = None
    reason: str | None = None

    @property
    def applicable(self) -> bool:
        return self.status != "not_applicable"


@dataclass(frozen=True)
class TimingProfile:
    """Normalized timing profile built without changing simulation scheduling."""

    part: str
    parameters: Mapping[DelayKind, Mapping[str, Any]]
    constraints: Mapping[ConstraintKind, Mapping[str, Any]]
    paths: Mapping[str, Any]
    default_ps: int | None
    default_source: str | None = None

    @classmethod
    def from_definition(cls, definition: Mapping[str, Any]) -> "TimingProfile":
        timing = _timing_block(definition)
        parameter_block = timing.get("timing_parameters", {})
        raw_parameters = parameter_block.get("parameters", {}) if isinstance(parameter_block, Mapping) else {}
        parameters: dict[DelayKind, Mapping[str, Any]] = {}
        for kind in DelayKind:
            record = raw_parameters.get(kind.value) if isinstance(raw_parameters, Mapping) else None
            if not isinstance(record, Mapping):
                raise ValueError(f"{definition.get('part', '<unknown>')}: missing timing parameter {kind.value}")
            status = record.get("status")
            if status not in {"exact", "generic", "missing", "not_applicable"}:
                raise ValueError(f"{definition.get('part', '<unknown>')}: invalid {kind.value} status {status!r}")
            parameters[kind] = dict(record)
        constraints: dict[ConstraintKind, Mapping[str, Any]] = {}
        for kind in ConstraintKind:
            record = raw_parameters.get(kind.value) if isinstance(raw_parameters, Mapping) else None
            if not isinstance(record, Mapping):
                raise ValueError(f"{definition.get('part', '<unknown>')}: missing timing constraint {kind.value}")
            status = record.get("status")
            if status not in {"exact", "generic", "missing", "not_applicable"}:
                raise ValueError(f"{definition.get('part', '<unknown>')}: invalid {kind.value} status {status!r}")
            constraints[kind] = dict(record)

        delay = timing.get("delay", {})
        delay = delay if isinstance(delay, Mapping) else {}
        public = delay.get("public_timing", {})
        public = public if isinstance(public, Mapping) else {}
        paths = public.get("paths", timing.get("paths", {}))
        paths = dict(paths) if isinstance(paths, Mapping) else {}
        default_ns = delay.get("default_ns", delay.get("model_delay_ns"))
        return cls(
            part=str(definition.get("part", timing.get("part", ""))),
            parameters=parameters,
            constraints=constraints,
            paths=paths,
            default_ps=ns_to_ps(default_ns) if default_ns is not None else None,
            default_source=str(delay.get("source")) if delay.get("source") else None,
        )

    def select(self, kind: DelayKind | str, *, path: str | None = None) -> TimingSelection:
        kind = DelayKind(kind)
        record = self.parameters[kind]
        status = str(record["status"])
        source = str(record.get("source_field") or record.get("source") or kind.value)
        if status == "not_applicable":
            return TimingSelection(kind, None, "not_applicable", source, status, path, str(record.get("reason", "")) or None)

        values = record.get("values_ns")
        if path:
            matched = _path_values(values, path)
            if matched:
                return TimingSelection(kind, _max_ps(matched), status, source, status, path)

        numbers = _numbers(values)
        if status in {"exact", "generic"} and numbers:
            return TimingSelection(kind, _max_ps(numbers), status, source, status, path)

        if path and path in self.paths:
            return TimingSelection(kind, _max_ps(_numbers(self.paths[path])), "path", f"public_timing.paths.{path}", "path", path)
        if self.default_ps is not None:
            return TimingSelection(kind, self.default_ps, "default", self.default_source or "timing.delay.default_ns", "default", path)
        raise LookupError(f"{self.part}: no timing value for {kind.value}" + (f" path {path}" if path else ""))

    def select_constraint(
        self, kind: ConstraintKind | str, *, path: str | None = None
    ) -> TimingSelection:
        """Select a conservative minimum requirement with source provenance."""

        kind = ConstraintKind(kind)
        record = self.constraints[kind]
        status = str(record["status"])
        source = str(record.get("source_field") or record.get("source") or kind.value)
        if status == "not_applicable":
            return TimingSelection(
                kind, None, "not_applicable", source, status, path,
                str(record.get("reason", "")) or None,
            )
        values = record.get("values_ns")
        if path:
            matched = _path_values(values, path)
            if matched:
                return TimingSelection(kind, _max_ps(matched), status, source, status, path)
        numbers = _numbers(values)
        if status in {"exact", "generic"} and numbers:
            return TimingSelection(kind, _max_ps(numbers), status, source, status, path)
        raise LookupError(
            f"{self.part}: no timing constraint for {kind.value}"
            + (f" path {path}" if path else "")
        )


def ns_to_ps(value: object) -> int:
    """Convert a numeric nanosecond value to an exact integer picosecond value."""

    if isinstance(value, bool):
        raise TypeError("boolean is not a timing value")
    try:
        picoseconds = Decimal(str(value)) * 1000
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid nanosecond value: {value!r}") from exc
    if not picoseconds.is_finite() or picoseconds != picoseconds.to_integral_value():
        raise ValueError(f"nanosecond value is not an integer number of picoseconds: {value!r}")
    if picoseconds < 0:
        raise ValueError("timing delay cannot be negative")
    return int(picoseconds)


def _timing_block(definition: Mapping[str, Any]) -> Mapping[str, Any]:
    timing = definition.get("timing")
    if isinstance(timing, Mapping) and "timing_parameters" in timing:
        return timing
    layers = definition.get("definition_layers", {})
    if isinstance(layers, Mapping) and isinstance(layers.get("timing"), Mapping):
        return layers["timing"]
    raise ValueError(f"{definition.get('part', '<unknown>')}: timing definition is missing")


def _logic_class(value: object) -> str:
    text = str(value).upper()
    if value in (0, False) or text == "0":
        return "0"
    if value in (1, True) or text == "1":
        return "1"
    if text == "Z":
        return "Z"
    raise ValueError(f"timing transition requires 0, 1, or Z, got {value!r}")


def _numbers(value: object) -> list[object]:
    if isinstance(value, Mapping):
        result: list[object] = []
        for child in value.values():
            result.extend(_numbers(child))
        return result
    if isinstance(value, (list, tuple)):
        result = []
        for child in value:
            result.extend(_numbers(child))
        return result
    if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool):
        return [value]
    return []


def _path_values(values: object, path: str) -> list[object]:
    target = path.lower().replace("-", "_")
    if not isinstance(values, Mapping):
        return []
    matched: list[object] = []
    for key, value in values.items():
        normalized = str(key).lower().replace("-", "_")
        if normalized == target or target in normalized or normalized in target:
            matched.extend(_numbers(value))
        elif isinstance(value, Mapping):
            matched.extend(_path_values(value, path))
    return matched


def _max_ps(values: list[object]) -> int:
    if not values:
        raise ValueError("timing values contain no numbers")
    return max(ns_to_ps(value) for value in values)
