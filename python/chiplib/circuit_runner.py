"""Executable vertical slice for concrete ``components.lib.circuit`` packages."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Mapping

from .circuit_package import (
    BoundaryEndpoint,
    CIRCUIT_ROOT,
    ROOT,
    CircuitPackage,
    NumericEndpoint,
    SymbolicEndpoint,
    load_circuit_package,
)
from .core import Board, Logic, LogicSource, X, Z, normalize_logic
from .model_loader import ModelLoadError, create_live_db_chip
from .virtual_runtime import (
    ClockSourceAdapter,
    SwitchAdapter,
    VirtualAdapter,
    VirtualRuntimeError,
    create_virtual_adapter,
)


@dataclass(frozen=True)
class CircuitRunnerIssue:
    code: str
    path: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "message": self.message}


class CircuitRunnerError(ValueError):
    """A structured package compilation or session-operation failure."""

    def __init__(self, issues: list[CircuitRunnerIssue], source: Path | None = None):
        self.issues = tuple(issues)
        self.source = source
        detail = "; ".join(f"{i.path} [{i.code}] {i.message}" for i in issues)
        super().__init__((f"{source}: " if source else "") + detail)

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": "circuit_runner_error",
            "source": str(self.source) if self.source else None,
            "issues": [issue.to_dict() for issue in self.issues],
        }


class CircuitRunner:
    """Run concrete scalar and unambiguous vector circuit-package wiring."""

    _INOUT_DIRECTIONS = {"input/output", "input_output", "bidirectional"}

    def __init__(self, package: CircuitPackage):
        self.package = package
        self.board = Board()
        self.inputs: dict[str, LogicSource | tuple[LogicSource, ...]] = {}
        self.outputs: dict[str, tuple[str, ...]] = {}
        self.probes: dict[str, tuple[str, ...]] = {}
        self._net_lines: dict[str, tuple[str, ...]] = {}
        self.virtual_adapters: dict[str, VirtualAdapter] = {}
        self.virtual_bindings: dict[str, tuple[str, ...]] = {}
        self._virtual_refs = {
            item.ref for item in package.chips
            if item.part == "Virtual" or (ROOT / "DB" / "Virtual" / item.part).is_dir()
        }
        self._build()

    @classmethod
    def load(cls, path: str | Path) -> "CircuitRunner":
        return cls(load_circuit_package(path))

    def _build(self) -> None:
        issues = self._validate_executable_subset()
        chips = {}
        if not issues:
            for index, item in enumerate(self.package.chips):
                if item.ref in self._virtual_refs:
                    try:
                        self.virtual_adapters[item.ref] = create_virtual_adapter(item.part, item.ref)
                    except (VirtualRuntimeError, TypeError, ValueError) as exc:
                        code = (
                            "virtual_part_not_executable"
                            if item.part == "Virtual"
                            else "virtual_adapter_not_executable"
                        )
                        issues.append(CircuitRunnerIssue(
                            code,
                            f"$.chips[{index}].part",
                            str(exc),
                        ))
                    continue
                try:
                    chips[item.ref] = create_live_db_chip(item.part, item.ref)
                except ModelLoadError as exc:
                    issues.append(CircuitRunnerIssue(
                        "unsupported_part", f"$.chips[{index}].part", str(exc)
                    ))
        if not issues:
            for index, port in enumerate(self.package.ports):
                if port.direction not in {"output", *self._INOUT_DIRECTIONS}:
                    continue
                wire = next((w for w in self.package.wiring if w.net == port.name), None)
                if wire is None or port.direction in self._INOUT_DIRECTIONS:
                    continue
                endpoints = wire.connections
                drivers = [
                    chips[e.ref].pin(pin) for e in endpoints
                    if isinstance(e, NumericEndpoint) and e.ref in chips for pin in e.pins
                ]
                if not any(pin.direction in {"out", "bidir"} for pin in drivers):
                    issues.append(CircuitRunnerIssue(
                        "unresolved_output",
                        f"$.ports[{index}].name",
                        f"output {port.name!r} has no concrete output driver",
                    ))
        if issues:
            raise CircuitRunnerError(issues, self.package.source_path)

        for ref, chip in chips.items():
            self.board.add_chip(ref, chip)
        for wire in self.package.wiring:
            lines = self._expand_name(wire.net)
            self._net_lines[wire.net] = lines
            numeric_connections = self._expand_numeric_connections(
                wire.net, wire.connections, ignored_refs=self._virtual_refs
            )
            for line, endpoint, pin in numeric_connections:
                self.board.connect(line, chips[endpoint.ref], pin)
            for endpoint in wire.connections:
                if isinstance(endpoint, NumericEndpoint) and endpoint.ref in self.virtual_adapters:
                    self.virtual_bindings[endpoint.ref] = lines
                    adapter = self.virtual_adapters[endpoint.ref]
                    if isinstance(adapter, (ClockSourceAdapter, SwitchAdapter)):
                        initial = adapter.idle_state if isinstance(adapter, ClockSourceAdapter) else adapter.state
                        for index, line in enumerate(lines):
                            name = f"virtual:{endpoint.ref}" if len(lines) == 1 else f"virtual:{endpoint.ref}[{index}]"
                            if name not in self.board.sources:
                                self.board.logic_source(name, line, initial)
            for endpoint in wire.connections:
                if isinstance(endpoint, BoundaryEndpoint) and endpoint.text.upper() in {"VCC", "GND"}:
                    for line in lines:
                        self.board.attach_rail(endpoint.text.upper(), line)
            if wire.net.upper() in {"VCC", "GND"}:
                for line in lines:
                    self.board.attach_rail(wire.net.upper(), line)

        for port in self.package.ports:
            lines = self._net_lines.get(port.name, self._expand_name(port.name))
            if port.direction == "input" or port.direction in self._INOUT_DIRECTIONS:
                initial: Logic = Z if port.direction in self._INOUT_DIRECTIONS else 0
                sources = tuple(
                    self.board.logic_source(
                        f"port:{port.name}" if len(lines) == 1 else f"port:{port.name}[{index}]",
                        line,
                        initial,
                    )
                    for index, line in enumerate(lines)
                )
                self.inputs[port.name] = sources[0] if len(sources) == 1 else sources
            if port.direction == "output" or port.direction in self._INOUT_DIRECTIONS:
                self.outputs[port.name] = lines
                self.probes[port.name] = lines
        self.board.settle()

    def _validate_executable_subset(self) -> list[CircuitRunnerIssue]:
        issues: list[CircuitRunnerIssue] = []
        circuit_root = CIRCUIT_ROOT
        refs: set[str] = set()
        for index, chip in enumerate(self.package.chips):
            path = f"$.chips[{index}]"
            if chip.ref in refs:
                issues.append(CircuitRunnerIssue("duplicate_ref", f"{path}.ref", f"duplicate ref {chip.ref!r}"))
            refs.add(chip.ref)
            if (circuit_root / chip.part / "circuit.json").is_file():
                issues.append(CircuitRunnerIssue("composite_not_executable", f"{path}.part", f"nested circuit {chip.part!r} is not executable"))
            if chip.symbolic_endpoints:
                issues.append(CircuitRunnerIssue("symbolic_aggregate_not_executable", f"{path}.symbolic_endpoints", f"symbolic endpoints on {chip.ref!r} are not executable"))

        numeric_by_net: dict[str, list[NumericEndpoint]] = {}
        for wire_index, wire in enumerate(self.package.wiring):
            numeric_by_net[wire.net] = []
            for endpoint_index, endpoint in enumerate(wire.connections):
                path = f"$.wiring[{wire_index}].connections[{endpoint_index}]"
                if isinstance(endpoint, NumericEndpoint):
                    numeric_by_net[wire.net].append(endpoint)
                elif isinstance(endpoint, SymbolicEndpoint):
                    issues.append(CircuitRunnerIssue("symbolic_aggregate_not_executable", path, f"symbolic endpoint {endpoint.text!r} is not executable"))
                elif isinstance(endpoint, BoundaryEndpoint) and endpoint.text != wire.net and endpoint.text.upper() not in {"VCC", "GND"}:
                    issues.append(CircuitRunnerIssue("symbolic_aggregate_not_executable", path, f"boundary alias {endpoint.text!r} is not executable"))

            try:
                self._expand_numeric_connections(
                    wire.net, wire.connections, ignored_refs=self._virtual_refs
                )
            except ValueError as exc:
                issues.append(CircuitRunnerIssue("ambiguous_range_width", f"$.wiring[{wire_index}]", str(exc)))

        net_names = set(numeric_by_net)
        for index, port in enumerate(self.package.ports):
            path = f"$.ports[{index}]"
            if port.direction in {"internal", "absent"}:
                continue
            if port.direction not in {"input", "output", *self._INOUT_DIRECTIONS}:
                issues.append(CircuitRunnerIssue("unsupported_port_direction", f"{path}.direction", f"direction {port.direction!r} is not executable"))
            if port.name not in net_names and port.direction == "output":
                code = "unresolved_output" if port.direction == "output" else "unresolved_input"
                issues.append(CircuitRunnerIssue(code, f"{path}.name", f"port {port.name!r} has no concrete net"))
            elif port.direction == "output" and not numeric_by_net[port.name]:
                issues.append(CircuitRunnerIssue("unresolved_output", f"{path}.name", f"output {port.name!r} has no concrete chip endpoint"))
        return issues

    @classmethod
    def _expand_name(cls, name: str) -> tuple[str, ...]:
        match = re.fullmatch(r"(.*?)(\d+)\.\.(?:\1)?(\d+)", name)
        if match is None:
            return (name,)
        prefix, start_text, end_text = match.groups()
        start, end = int(start_text), int(end_text)
        step = 1 if end >= start else -1
        return tuple(f"{prefix}{index}" for index in range(start, end + step, step))

    @classmethod
    def _expand_numeric_connections(
        cls,
        net: str,
        endpoints: tuple[Any, ...],
        *,
        ignored_refs: set[str] | None = None,
    ) -> list[tuple[str, NumericEndpoint, int]]:
        lines = cls._expand_name(net)
        width = len(lines)
        ignored = ignored_refs or set()
        numeric = [
            endpoint for endpoint in endpoints
            if isinstance(endpoint, NumericEndpoint) and endpoint.ref not in ignored
        ]
        if width == 1:
            if any(len(endpoint.pins) != 1 for endpoint in numeric):
                raise ValueError(f"scalar net {net!r} cannot bind a multi-pin range")
            return [(lines[0], endpoint, endpoint.start) for endpoint in numeric]

        result: list[tuple[str, NumericEndpoint, int]] = []
        scalar_run: list[NumericEndpoint] = []

        def flush() -> None:
            if not scalar_run:
                return
            if len(scalar_run) % width:
                raise ValueError(
                    f"vector net {net!r} has {len(scalar_run)} scalar endpoints; expected a multiple of width {width}"
                )
            for offset, endpoint in enumerate(scalar_run):
                result.append((lines[offset % width], endpoint, endpoint.start))
            scalar_run.clear()

        for endpoint in numeric:
            pins = endpoint.pins
            if len(pins) == 1:
                scalar_run.append(endpoint)
                if len(scalar_run) == width:
                    flush()
            else:
                flush()
                if len(pins) != width:
                    raise ValueError(
                        f"pin range {endpoint.text!r} has width {len(pins)}, expected {width} for {net!r}"
                    )
                result.extend(
                    (line, endpoint, pin) for line, pin in zip(lines, pins)
                )
        flush()
        return result

    def set_input(self, name: str, value: Logic | int | tuple[Logic, ...] | list[Logic]) -> Any:
        if name not in self.inputs:
            self._operation_error("unknown_input", name, f"input port {name!r} is not bound")
        binding = self.inputs[name]
        sources = (binding,) if isinstance(binding, LogicSource) else binding
        values = self._coerce_vector(name, value, len(sources))
        result = tuple(
            self.board.set_source(source.name, item) for source, item in zip(sources, values)
        )
        self.board.settle()
        return result[0] if len(result) == 1 else result

    def release_input(self, name: str) -> Any:
        """Release an input or inout boundary to high impedance."""

        return self.set_input(name, Z)

    def _coerce_vector(self, name: str, value: Any, width: int) -> tuple[Logic, ...]:
        if width == 1:
            return (normalize_logic(value),)
        if isinstance(value, int) and not isinstance(value, bool):
            if value < 0 or value >= (1 << width):
                self._operation_error("vector_value_out_of_range", name, f"value {value} does not fit width {width}")
            return tuple((value >> index) & 1 for index in range(width))
        if isinstance(value, str) and value in {X, Z}:
            return (value,) * width
        if not isinstance(value, (tuple, list)) or len(value) != width:
            self._operation_error("vector_width_mismatch", name, f"expected {width} logic values")
        return tuple(normalize_logic(item) for item in value)

    def reset(self, assignments: Mapping[str, Logic] | None = None) -> dict[str, Logic]:
        values = dict(assignments or {
            port.name: 0 for port in self.package.ports
            if port.direction == "input" and port.active_low
        })
        if not values:
            self._operation_error("reset_not_bound", "reset", "no reset assignments or active-low input ports are available")
        for name, value in values.items():
            self.set_input(name, value)
        return self.read()

    def pulse_clock(self, name: str = "CLK") -> dict[str, Logic]:
        if name not in self.inputs:
            self._operation_error("unknown_clock", name, f"clock port {name!r} is not bound")
        self.set_input(name, 0)
        binding = self.inputs[name]
        if not isinstance(binding, LogicSource):
            self._operation_error("vector_clock", name, f"clock port {name!r} must be scalar")
        self.board.set_source(binding.name, 1)
        net = self.board.net(name)
        for pin in tuple(net.pins):
            pin.chip.clock_edge(pin.number)
        self.board.settle()
        return self.read()

    def run_package_proofs(self) -> dict[str, Any]:
        """Execute supported declared proof vectors through fresh live sessions."""

        if self.package.source_path is None:
            self._operation_error(
                "proof_source_not_bound", "verification", "package has no source path"
            )
        proofs = [self._run_proof_file(item.resolved_path) for item in self.package.verification]
        return {
            "circuit": self.package.id,
            "passed": all(proof["passed"] for proof in proofs),
            "proofs": proofs,
        }

    def _run_proof_file(self, path: Path) -> dict[str, Any]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            self._operation_error("invalid_proof", str(path), str(exc))
        if data.get("circuit") != self.package.id:
            self._operation_error(
                "proof_circuit_mismatch",
                str(path),
                f"proof names {data.get('circuit')!r}, expected {self.package.id!r}",
            )

        checks: list[dict[str, Any]] = []
        reset = data.get("reset")
        sequence = data.get("sequence_after_reset")
        if isinstance(reset, dict) and isinstance(sequence, list):
            session = self._fresh_session()
            reset_inputs = reset.get("input", {})
            actual_reset = session.reset(reset_inputs)
            checks.append(self._check("reset", reset.get("expect"), actual_reset))
            active_low_inputs = {
                port.name for port in self.package.ports
                if port.direction == "input" and port.active_low
            }
            for name, value in reset_inputs.items():
                if name in active_low_inputs and value == 0:
                    session.set_input(name, 1)
            for index, vector in enumerate(sequence, 1):
                actual = session.pulse_clock()
                checks.append(self._check(f"clock_{index}", vector.get("expect"), actual))

            before = session.read()
            session.set_input("CLK", 0)
            checks.append(self._check("falling_edge_holds", before, session.read()))
            session.set_input("CLK", 0)
            checks.append(self._check("no_rising_edge_holds", before, session.read()))

        recovery = data.get("illegal_lower_state_recovery")
        unsupported_states: list[Mapping[str, Logic]] = []
        if isinstance(recovery, dict):
            normal = recovery.get("normal_states", [])
            max_clocks = recovery.get("max_clocks", 0)
            for state in recovery.get("states", []):
                if state != {name: 0 for name in self.outputs}:
                    unsupported_states.append(state)
                    continue
                session = self._fresh_session()
                session.reset({"/CLR": 0})
                session.set_input("/CLR", 1)
                history = []
                recovered = False
                for _ in range(max_clocks):
                    observed = session.pulse_clock()
                    history.append(observed)
                    if observed in normal:
                        recovered = True
                        break
                checks.append({
                    "name": "illegal_state_recovery_000",
                    "passed": recovered,
                    "expected": {"normal_within_clocks": max_clocks},
                    "actual": history,
                })

        return {
            "source": str(path),
            "passed": all(check["passed"] for check in checks),
            "checks": checks,
            "unexercised": [{
                "reason": "live model has no public state-load interface",
                "state": dict(state),
            } for state in unsupported_states],
        }

    def _fresh_session(self) -> "CircuitRunner":
        if self.package.source_path is None:
            self._operation_error("session_source_not_bound", "source", "cannot reload package")
        return type(self).load(self.package.source_path)

    @staticmethod
    def _check(name: str, expected: Any, actual: Any) -> dict[str, Any]:
        return {
            "name": name,
            "passed": actual == expected,
            "expected": expected,
            "actual": actual,
        }

    def read(self, name: str | None = None) -> Any:
        if name is not None:
            if name not in self.outputs and name not in self.probes:
                self._operation_error("unknown_probe", name, f"output or probe {name!r} is not bound")
            nets = self.probes[name] if name in self.probes else self.outputs[name]
            values = tuple(self.board.net(net).value for net in nets)
            return values[0] if len(values) == 1 else values
        return {port: self.read(port) for port in self.outputs}

    def snapshot(self) -> dict[str, Any]:
        return {
            "circuit": self.package.id,
            "source": str(self.package.source_path) if self.package.source_path else None,
            "ports": {
                "inputs": {
                    name: source.value if isinstance(source, LogicSource)
                    else tuple(item.value for item in source)
                    for name, source in self.inputs.items()
                },
                "outputs": self.read(),
            },
            "provenance": {
                ref: dict(chip.model_provenance) for ref, chip in self.board.chips.items()
            },
            "virtual_adapters": {
                ref: {**adapter.snapshot(), "nets": self.virtual_bindings.get(ref, ())}
                for ref, adapter in self.virtual_adapters.items()
            },
            "board": self.board.snapshot(),
        }

    def _operation_error(self, code: str, path: str, message: str) -> None:
        raise CircuitRunnerError([CircuitRunnerIssue(code, path, message)], self.package.source_path)


def load_circuit_runner(path: str | Path) -> CircuitRunner:
    return CircuitRunner.load(path)
