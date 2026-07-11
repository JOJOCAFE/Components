"""Package-level binding between functional circuits and modeled timing.

This adapter deliberately requires an explicit package timing path.  It does
not infer coverage from a component default or claim physical signoff.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Mapping

from .circuit_runner import CircuitRunner
from .db import load_digital_definition
from .timed_runner import TimedRunner
from .timing import ConstraintKind, TimingProfile, TimingSelection


@dataclass(frozen=True)
class CircuitTimingIssue:
    code: str
    path: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "message": self.message}


class CircuitTimingError(ValueError):
    """A timing binding failure with a stable machine-readable diagnostic."""

    def __init__(self, issue: CircuitTimingIssue):
        self.issue = issue
        super().__init__(f"{issue.path} [{issue.code}] {issue.message}")

    def to_dict(self) -> dict[str, Any]:
        return {"error": "circuit_timing_error", "issue": self.issue.to_dict()}


@dataclass(frozen=True)
class BoundTimingEvent:
    circuit: str
    input_port: str
    output_port: str
    chip_ref: str
    part: str
    package_path: str
    before: Any
    after: Any
    selection: TimingSelection
    model_provenance: Mapping[str, Any]
    modeled_only: bool = True

    def snapshot(self) -> dict[str, Any]:
        return {
            "circuit": self.circuit,
            "input_port": self.input_port,
            "output_port": self.output_port,
            "chip_ref": self.chip_ref,
            "part": self.part,
            "package_path": self.package_path,
            "before": self.before,
            "after": self.after,
            "delay_ps": self.selection.delay_ps,
            "timing_provenance": self.selection.provenance,
            "timing_source": self.selection.source,
            "model_provenance": dict(self.model_provenance),
            "modeled_only": self.modeled_only,
        }


@dataclass(frozen=True)
class CompiledTimingPath:
    """Executable lib/standard/package binding used by every timed package operation."""

    name: str
    chip_ref: str
    part: str
    clock_pin: str
    clock_net: str
    constrained_nets: tuple[str, ...]
    output_ports: tuple[str, ...]
    trigger_edge: str
    deadband_ps: int


class CircuitTimingBinding:
    """Apply DB timing to transitions produced by one loadable package."""

    def __init__(self, runner: CircuitRunner, timed: TimedRunner | None = None):
        self.runner = runner
        self.timed = timed or TimedRunner()
        self._chips = {chip.ref: chip for chip in runner.package.chips}
        self._profiles: dict[str, TimingProfile] = {}
        self._compiled: dict[str, CompiledTimingPath] = {}

    @classmethod
    def load(cls, path: str | Path) -> "CircuitTimingBinding":
        return cls(CircuitRunner.load(path))

    def pulse_clock(
        self, input_port: str = "CLK", *, setup_ps: int | None = None,
        high_ps: int | None = None, constrained_change_ps: int | None = None,
    ) -> tuple[BoundTimingEvent, ...]:
        """Execute a package clock pulse with automatic DB constraint checks."""

        path = self._require_path(input_port)
        compiled = self._compile_path(input_port, path)
        profile = self._profile(compiled.part)
        setup = profile.select_constraint(ConstraintKind.SETUP)
        pulse = profile.select_constraint(ConstraintKind.MINIMUM_PULSE_WIDTH)
        setup_wait = setup.delay_ps or 0 if setup_ps is None else setup_ps
        pulse_wait = pulse.delay_ps or 0 if high_ps is None else high_ps
        if setup_wait < 0 or pulse_wait < 0:
            raise ValueError("timing intervals must be non-negative")
        self.timed.run_until(self.timed.time_ps + setup_wait)
        self.timed.check_clock_transition(compiled.clock_net, 0, 1, profile)
        self.timed.check_active_edge(
            compiled.clock_net, compiled.constrained_nets, profile
        )
        constrained_before = {
            net: self.runner.board.net(net).value for net in compiled.constrained_nets
        }
        before = self.runner.read()
        after = self.runner.pulse_clock(input_port)
        events = self._schedule_changes(input_port, before, after, path, clock_to_q=True)
        earliest_output_ps = min(event.selection.delay_ps or 0 for event in events)
        constrained_delay = (
            earliest_output_ps if constrained_change_ps is None else constrained_change_ps
        )
        if constrained_delay < 0:
            raise ValueError("constrained_change_ps must be non-negative")
        for net, old in constrained_before.items():
            new = self.runner.board.net(net).value
            if new != old:
                self.timed.drive(net, new, time_ps=self.timed.time_ps + constrained_delay)
        self.timed.run_until(self.timed.time_ps + pulse_wait)
        self.timed.check_clock_transition(compiled.clock_net, 1, 0, profile)
        return events

    def set_input(self, input_port: str, value: Any) -> tuple[BoundTimingEvent, ...]:
        """Execute a functional input change when the package declares its path."""

        path = self._require_path(input_port)
        before = self.runner.read()
        self.runner.set_input(input_port, value)
        after = self.runner.read()
        return self._schedule_changes(input_port, before, after, path, clock_to_q=False)

    def compiled_path(self, input_port: str = "CLK") -> CompiledTimingPath:
        path = self._require_path(input_port)
        return self._compile_path(input_port, path)

    def constraint_provenance(
        self, input_port: str = "CLK"
    ) -> dict[str, dict[str, Any]]:
        """Return constraints selected from the DB part named by a package path."""

        path = self._require_path(input_port)
        part = self._path_part(path)
        profile = self._profile(part)
        result: dict[str, dict[str, Any]] = {}
        for kind in ConstraintKind:
            try:
                selected = profile.select_constraint(kind)
            except LookupError as exc:
                result[kind.value] = {"status": "blocked", "reason": str(exc)}
                continue
            result[kind.value] = {
                "status": selected.status,
                "delay_ps": selected.delay_ps,
                "provenance": selected.provenance,
                "source": selected.source,
                "part": part,
                "package_path": str(path.get("name", "")),
                "modeled_only": True,
            }
        return result

    def _schedule_changes(
        self,
        input_port: str,
        before: Mapping[str, Any],
        after: Mapping[str, Any],
        path: Mapping[str, Any],
        *,
        clock_to_q: bool,
    ) -> tuple[BoundTimingEvent, ...]:
        events: list[BoundTimingEvent] = []
        for output in self.runner.package.ports:
            if output.direction != "output" or before.get(output.name) == after.get(output.name):
                continue
            ref = self._output_ref(output.name, output.source)
            chip = self._chips[ref]
            part = chip.part
            declared_part = self._path_part(path)
            if declared_part != part:
                self._blocked(
                    "timing_path_part_mismatch",
                    f"timing.paths.{path.get('name', '<unnamed>')}",
                    f"path declares {declared_part!r}, but {output.name!r} is driven by {ref}.{part}",
                )
            profile = self._profile(part)
            signal = f"{self.runner.package.id}.{output.name}"
            self.timed.signals.setdefault(signal, before[output.name])
            selection = self.timed.schedule_output(
                signal,
                before[output.name],
                after[output.name],
                profile,
                path=str(path.get("name", "")),
                clock_to_q=clock_to_q,
            )
            self.timed.observe_driver_transition(
                signal, before[output.name], after[output.name],
                required_deadband_ps=self._deadband_ps(path),
            )
            live_chip = self.runner.board.chips[ref]
            events.append(BoundTimingEvent(
                self.runner.package.id,
                input_port,
                output.name,
                ref,
                part,
                str(path.get("name", "")),
                before[output.name],
                after[output.name],
                selection,
                dict(live_chip.model_provenance),
            ))
        if not events:
            self._blocked(
                "no_observable_transition",
                f"ports.{input_port}",
                "functional execution produced no changed package output",
            )
        return tuple(events)

    def _compile_path(
        self, input_port: str, path: Mapping[str, Any]
    ) -> CompiledTimingPath:
        name = str(path.get("name", ""))
        if name in self._compiled:
            return self._compiled[name]
        origin = str(path.get("from", ""))
        match = re.fullmatch(r"([A-Za-z][A-Za-z0-9_]*)\.([^./]+)", origin)
        if match is None or match.group(1) not in self._chips:
            self._blocked("invalid_timing_origin", f"timing.paths.{name}.from", origin)
        ref, pin_name = match.groups()
        chip = self.runner.board.chips[ref]
        try:
            pin = chip.pin(pin_name)
        except KeyError:
            self._blocked(
                "unknown_timing_pin", f"timing.paths.{name}.from",
                f"{ref} has no DB pin named {pin_name!r}",
            )
        if pin.direction != "in" or pin.net is None:
            self._blocked(
                "timing_origin_not_clock_input", f"timing.paths.{name}.from",
                "timing origin must resolve to a connected DB input pin",
            )
        if self._endpoint_name(origin) != input_port:
            self._blocked(
                "timing_input_mismatch", f"timing.paths.{name}.from",
                f"path origin {origin!r} does not bind package input {input_port!r}",
            )
        part = self._path_part(path)
        if self._chips[ref].part != part:
            self._blocked(
                "timing_path_part_mismatch", f"timing.paths.{name}.source_part",
                f"path declares {part!r}, but {ref} is {self._chips[ref].part!r}",
            )
        constrained = tuple(sorted({
            candidate.net.name for candidate in chip.pins.values()
            if candidate.direction == "in" and candidate.net is not None
            and candidate.number != pin.number and self._is_constrained_pin(candidate.name)
        }))
        outputs = tuple(sorted(
            port.name for port in self.runner.package.ports
            if port.direction == "output" and self._output_ref(port.name, port.source) == ref
        ))
        if not outputs:
            self._blocked(
                "timing_path_has_no_output", f"timing.paths.{name}.to",
                "path source chip drives no observable package output",
            )
        compiled = CompiledTimingPath(
            name, ref, part, pin.name, pin.net.name, constrained, outputs,
            str(self.runner.package.raw.get("timing", {}).get("trigger_edge", "rising")),
            self._deadband_ps(path),
        )
        self._compiled[name] = compiled
        for net in constrained:
            self.timed.signals.setdefault(net, self.runner.board.net(net).value)
            self.timed.last_change_ps.setdefault(net, self.timed.time_ps)
        self.timed.signals.setdefault(pin.net.name, self.runner.board.net(pin.net.name).value)
        return compiled

    @staticmethod
    def _is_constrained_pin(name: str) -> bool:
        normalized = name.upper().replace("_N", "").lstrip("/")
        asynchronous = {"CLR", "CLEAR", "PRE", "PRESET", "RESET", "RST"}
        return normalized not in asynchronous

    @staticmethod
    def _deadband_ps(path: Mapping[str, Any]) -> int:
        value = path.get("deadband_ps", 0)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError("package timing deadband_ps must be a non-negative integer")
        return value

    def _require_path(self, input_port: str) -> Mapping[str, Any]:
        timing = self.runner.package.raw.get("timing", {})
        paths = timing.get("paths", []) if isinstance(timing, Mapping) else []
        candidates = []
        for path in paths if isinstance(paths, list) else []:
            if not isinstance(path, Mapping):
                continue
            origin = str(path.get("from", ""))
            if self._endpoint_name(origin) == input_port:
                candidates.append(path)
        if len(candidates) != 1:
            code = "missing_package_timing_path" if not candidates else "ambiguous_package_timing_path"
            self._blocked(
                code,
                f"timing.paths.{input_port}",
                f"expected one explicit path from input {input_port!r}; found {len(candidates)}",
            )
        return candidates[0]

    def _path_part(self, path: Mapping[str, Any]) -> str:
        part = str(path.get("source_part", "")).strip()
        if not part:
            self._blocked(
                "missing_timing_source_part",
                f"timing.paths.{path.get('name', '<unnamed>')}.source_part",
                "package timing path must name the DB source part",
            )
        return part

    def _output_ref(self, name: str, source: str | None) -> str:
        match = re.match(r"^([A-Za-z][A-Za-z0-9_]*)\.", source or "")
        if match is None or match.group(1) not in self._chips:
            self._blocked(
                "missing_output_chip_source",
                f"ports.{name}.source",
                "output must identify its driving chip as REF.pin",
            )
        return match.group(1)

    def _profile(self, part: str) -> TimingProfile:
        if part not in self._profiles:
            self._profiles[part] = TimingProfile.from_definition(load_digital_definition(part))
        return self._profiles[part]

    @staticmethod
    def _endpoint_name(endpoint: str) -> str:
        return endpoint.rsplit(".", 1)[-1]

    @staticmethod
    def _blocked(code: str, path: str, message: str) -> None:
        raise CircuitTimingError(CircuitTimingIssue(code, path, message))
