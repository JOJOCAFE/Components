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


class CircuitTimingBinding:
    """Apply DB timing to transitions produced by one loadable package."""

    def __init__(self, runner: CircuitRunner, timed: TimedRunner | None = None):
        self.runner = runner
        self.timed = timed or TimedRunner()
        self._chips = {chip.ref: chip for chip in runner.package.chips}
        self._profiles: dict[str, TimingProfile] = {}

    @classmethod
    def load(cls, path: str | Path) -> "CircuitTimingBinding":
        return cls(CircuitRunner.load(path))

    def pulse_clock(self, input_port: str = "CLK") -> tuple[BoundTimingEvent, ...]:
        """Execute a real functional clock edge and schedule changed outputs."""

        path = self._require_path(input_port)
        before = self.runner.read()
        after = self.runner.pulse_clock(input_port)
        return self._schedule_changes(input_port, before, after, path, clock_to_q=True)

    def set_input(self, input_port: str, value: Any) -> tuple[BoundTimingEvent, ...]:
        """Execute a functional input change when the package declares its path."""

        path = self._require_path(input_port)
        before = self.runner.read()
        self.runner.set_input(input_port, value)
        after = self.runner.read()
        return self._schedule_changes(input_port, before, after, path, clock_to_q=False)

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
