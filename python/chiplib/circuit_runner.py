"""Executable vertical slice for concrete ``components.lib.circuit`` packages."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Mapping

from .circuit_package import (
    BoundaryEndpoint,
    BoundaryConcatEndpoint,
    BoundarySelectorEndpoint,
    CIRCUIT_ROOT,
    ROOT,
    CircuitPackage,
    NumericEndpoint,
    SymbolicEndpoint,
    expand_boundary_name,
    load_circuit_package,
)
from .core import Board, Logic, LogicSource, X, Z, normalize_logic
from .model_loader import ModelLoadError, create_live_db_chip, load_live_chip_memory
from .virtual_runtime import (
    ClockSourceAdapter,
    DelayNoiseAdapter,
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

    def __init__(self, package: CircuitPackage, *, boundary_lines: Mapping[str, tuple[str, ...]] | None = None):
        self.package = package
        self.board = Board()
        self.inputs: dict[str, LogicSource | tuple[LogicSource, ...]] = {}
        self.outputs: dict[str, tuple[str, ...]] = {}
        self.probes: dict[str, tuple[str, ...]] = {}
        self._net_lines: dict[str, tuple[str, ...]] = {}
        self.virtual_adapters: dict[str, VirtualAdapter] = {}
        self.virtual_bindings: dict[str, tuple[str, ...]] = {}
        self._chips: dict[str, Any] = {}
        self._virtual_sources_by_line: dict[str, list[LogicSource]] = {}
        self._boundary_lines: dict[str, tuple[str, ...]] = dict(boundary_lines or {})
        self._virtual_refs = {
            item.ref for item in package.chips
            if item.part == "Virtual" or (ROOT / "lib" / "standard" / "virtual" / item.part).is_dir()
        }
        self._build()

    @classmethod
    def load(cls, path: str | Path) -> "CircuitRunner":
        return cls(load_circuit_package(path))

    @classmethod
    def from_hierarchy(cls, package: CircuitPackage, catalog: Mapping[str, CircuitPackage] | None = None) -> "CircuitRunner":
        """Execute an explicitly mapped composite package on one shared Board.

        The hierarchy compiler supplies all joins.  This method deliberately
        has no fallback that connects child ports by matching their names.
        """
        from .circuit_hierarchy import flatten_circuit_for_execution
        flattened = flatten_circuit_for_execution(package, catalog)
        return cls(flattened.package, boundary_lines=flattened.boundary_lines)

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
        self._chips = chips
        if not issues:
            for wire_index, wire in enumerate(self.package.wiring):
                for endpoint_index, endpoint in enumerate(wire.connections):
                    if not isinstance(endpoint, SymbolicEndpoint):
                        continue
                    try:
                        self._resolve_symbolic_endpoint(wire.net, endpoint)
                    except ValueError as exc:
                        issues.append(CircuitRunnerIssue(
                            "ambiguous_symbolic_width",
                            f"$.wiring[{wire_index}].connections[{endpoint_index}]",
                            str(exc),
                        ))
        if not issues:
            for index, port in enumerate(self.package.ports):
                if port.direction not in {"output", *self._INOUT_DIRECTIONS}:
                    continue
                wire = next((w for w in self.package.wiring if w.net == port.name), None)
                if wire is None or port.direction in self._INOUT_DIRECTIONS:
                    if port.name in self._boundary_lines:
                        continue
                    continue
                endpoints = wire.connections
                drivers = [
                    chips[e.ref].pin(pin) for e in endpoints
                    if isinstance(e, NumericEndpoint) and e.ref in chips for pin in e.pins
                ]
                virtual_driver = any(
                    isinstance(endpoint, NumericEndpoint)
                    and isinstance(self.virtual_adapters.get(endpoint.ref), (ClockSourceAdapter, SwitchAdapter, DelayNoiseAdapter))
                    for endpoint in endpoints
                )
                if not virtual_driver and not any(pin.direction in {"out", "bidir"} for pin in drivers):
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
            for endpoint in wire.connections:
                if isinstance(endpoint, BoundaryEndpoint) and endpoint.text.upper() not in {"VCC", "GND"}:
                    previous = self._boundary_lines.get(endpoint.text)
                    if previous is not None and previous != lines:
                        self._operation_error(
                            "ambiguous_boundary_mapping", endpoint.text,
                            f"boundary {endpoint.text!r} maps to both {previous!r} and {lines!r}",
                        )
                    self._boundary_lines[endpoint.text] = lines
            numeric_connections = self._expand_numeric_connections(
                wire.net, wire.connections, ignored_refs=self._virtual_refs
            )
            for line, endpoint, pin in numeric_connections:
                self.board.connect(line, chips[endpoint.ref], pin)
            for endpoint in wire.connections:
                if isinstance(endpoint, SymbolicEndpoint):
                    pins = self._resolve_symbolic_endpoint(wire.net, endpoint)
                    for line, pin in zip(lines, pins):
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
                                source = self.board.logic_source(name, line, initial)
                                self._virtual_sources_by_line.setdefault(line, []).append(source)
            for endpoint in wire.connections:
                if isinstance(endpoint, BoundaryEndpoint) and endpoint.text.upper() in {"VCC", "GND"}:
                    for line in lines:
                        self.board.attach_rail(endpoint.text.upper(), line)
            if wire.net.upper() in {"VCC", "GND"}:
                for line in lines:
                    self.board.attach_rail(wire.net.upper(), line)

        for port in self.package.ports:
            lines = self._boundary_lines.get(
                port.name, self._net_lines.get(port.name, self._expand_name(port.name))
            )
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
                for line in lines:
                    for source in self._virtual_sources_by_line.get(line, ()):
                        source.enabled = False
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

        numeric_by_net: dict[str, list[NumericEndpoint]] = {}
        for wire_index, wire in enumerate(self.package.wiring):
            numeric_by_net[wire.net] = []
            for endpoint_index, endpoint in enumerate(wire.connections):
                path = f"$.wiring[{wire_index}].connections[{endpoint_index}]"
                if isinstance(endpoint, NumericEndpoint):
                    numeric_by_net[wire.net].append(endpoint)
                elif isinstance(endpoint, (BoundarySelectorEndpoint, BoundaryConcatEndpoint)):
                    # Selectors are an explicit hierarchy-planning construct.
                    # A live runner must not silently turn one net into another
                    # via an inferred directional source.
                    issues.append(CircuitRunnerIssue(
                        "boundary_transform_not_executable", path,
                        "boundary selectors and concatenations require flattened child execution; this runner only executes concrete DB pins",
                    ))
                elif isinstance(endpoint, SymbolicEndpoint):
                    # Width and pin-name resolution require the live model and are
                    # checked immediately after model construction.
                    pass

            try:
                self._expand_numeric_connections(
                    wire.net, wire.connections, ignored_refs=self._virtual_refs
                )
            except ValueError as exc:
                issues.append(CircuitRunnerIssue("ambiguous_range_width", f"$.wiring[{wire_index}]", str(exc)))

        net_names = set(numeric_by_net)
        for index, port in enumerate(self.package.ports):
            path = f"$.ports[{index}]"
            if port.direction in {"internal", "absent", "passive"}:
                continue
            if port.direction not in {"input", "output", *self._INOUT_DIRECTIONS}:
                issues.append(CircuitRunnerIssue("unsupported_port_direction", f"{path}.direction", f"direction {port.direction!r} is not executable"))
            if port.name not in net_names and port.name not in self._boundary_lines and port.direction == "output":
                code = "unresolved_output" if port.direction == "output" else "unresolved_input"
                issues.append(CircuitRunnerIssue(code, f"{path}.name", f"port {port.name!r} has no concrete net"))
            elif port.name in numeric_by_net and port.direction == "output" and not numeric_by_net[port.name]:
                issues.append(CircuitRunnerIssue("unresolved_output", f"{path}.name", f"output {port.name!r} has no concrete chip endpoint"))
        return issues

    def _resolve_symbolic_endpoint(
        self, net: str, endpoint: SymbolicEndpoint
    ) -> tuple[int, ...]:
        chip = self._chips.get(endpoint.ref)
        if chip is None:
            raise ValueError(
                f"symbolic endpoint {endpoint.text!r} has no concrete live chip instance"
            )
        width = len(self._expand_name(net))
        exact = [pin.number for pin in chip.pins.values() if pin.name == endpoint.name]
        indexed: list[tuple[int, int]] = []
        for pin in chip.pins.values():
            match = re.fullmatch(re.escape(endpoint.name) + r"(\d+)", pin.name)
            if match:
                indexed.append((int(match.group(1)), pin.number))
        candidates = tuple(exact) if exact else tuple(pin for _, pin in sorted(indexed))
        if len(candidates) != width:
            raise ValueError(
                f"symbolic endpoint {endpoint.text!r} resolves to width {len(candidates)}, "
                f"expected {width} for {net!r}"
            )
        return candidates

    @classmethod
    def _expand_name(cls, name: str) -> tuple[str, ...]:
        return expand_boundary_name(name)

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
        return self._set_input(name, value, run_declared_clock_edges=False)

    def set_input_with_declared_clock_edges(
        self, name: str, value: Logic | int | tuple[Logic, ...] | list[Logic]
    ) -> Any:
        """Drive one public input and deliver only its declared derived edges.

        This is deliberately narrower than automatic edge propagation.  A
        package must enumerate a source output pin, its concrete clock-sink
        pins, and the public input that may cause that edge in
        ``runtime.declared_clock_edges``.  The runner validates that every
        source and sink is physically joined on the flattened Board before it
        invokes ``clock_edge``.  Ordinary data outputs never become clocks by
        inference.
        """
        return self._set_input(name, value, run_declared_clock_edges=True)

    def _set_input(
        self, name: str, value: Logic | int | tuple[Logic, ...] | list[Logic], *,
        run_declared_clock_edges: bool,
    ) -> Any:
        if name not in self.inputs:
            self._operation_error("unknown_input", name, f"input port {name!r} is not bound")
        declared_edges = self._declared_clock_edges_for_trigger(name) if run_declared_clock_edges else ()
        before = {
            edge["id"]: self.board.net(edge["source_line"]).value
            for edge in declared_edges
        }
        binding = self.inputs[name]
        sources = (binding,) if isinstance(binding, LogicSource) else binding
        values = self._coerce_vector(name, value, len(sources))
        for source in sources:
            for net in self.board.nets.values():
                if source in net.sources:
                    for virtual in self._virtual_sources_by_line.get(net.name, ()):
                        virtual.enabled = False
        result = tuple(
            self.board.set_source(source.name, item, enabled=True) for source, item in zip(sources, values)
        )
        self.board.settle()
        for edge in declared_edges:
            if before[edge["id"]] != 0 or self.board.net(edge["source_line"]).value != 1:
                continue
            for chip, pin in edge["targets"]:
                chip.clock_edge(pin)
        if declared_edges:
            self.board.settle()
        return result[0] if len(result) == 1 else result

    def _declared_clock_edges_for_trigger(self, trigger: str) -> tuple[dict[str, Any], ...]:
        """Validate and resolve the package's explicit derived-clock clauses.

        The schema is intentionally runtime-local rather than a general net
        expression language::

            {"id": "...", "trigger_input": "T2", "edge": "rising",
             "source": {"chip": "U33", "pin": 8},
             "sinks": [{"chip": "U31", "pin": 3, "kind": "clock"}]}

        A source must be an output/bidirectional pin.  Each declared sink must
        be an input pin named as a clock and share the exact concrete net with
        that source.  These checks make a bad topology fail loudly and prevent
        arbitrary output transitions from being treated as clock events.
        """
        runtime = self.package.raw.get("runtime", {})
        specs = runtime.get("declared_clock_edges", []) if isinstance(runtime, Mapping) else []
        if not isinstance(specs, list):
            self._operation_error("invalid_declared_clock_edges", "runtime.declared_clock_edges", "must be a list")
        resolved: list[dict[str, Any]] = []
        ids: set[str] = set()
        for index, spec in enumerate(specs):
            path = f"runtime.declared_clock_edges[{index}]"
            if not isinstance(spec, Mapping):
                self._operation_error("invalid_declared_clock_edge", path, "edge must be an object")
            edge_id, trigger_input, edge = spec.get("id"), spec.get("trigger_input"), spec.get("edge")
            if not isinstance(edge_id, str) or not edge_id:
                self._operation_error("invalid_declared_clock_edge", path, "edge must have a non-empty id")
            if edge_id in ids:
                self._operation_error("duplicate_declared_clock_edge", path, f"duplicate edge id {edge_id!r}")
            ids.add(edge_id)
            if trigger_input != trigger:
                continue
            if trigger_input not in self.inputs:
                self._operation_error("invalid_declared_clock_edge", path, "trigger_input must name a public input")
            if edge != "rising":
                self._operation_error("invalid_declared_clock_edge", path, "only source-backed rising edges are supported")
            source = spec.get("source")
            sinks = spec.get("sinks")
            if not isinstance(source, Mapping) or not isinstance(sinks, list) or not sinks:
                self._operation_error("invalid_declared_clock_edge", path, "edge must declare source and non-empty sinks")
            source_chip, source_pin = source.get("chip"), source.get("pin")
            if not isinstance(source_chip, str) or not isinstance(source_pin, int) or source_chip not in self._chips:
                self._operation_error("invalid_declared_clock_edge", path, "source must name a live chip and numeric pin")
            source_obj = self._chips[source_chip].pin(source_pin)
            if source_obj.direction not in {"out", "bidir"} or source_obj.net is None:
                self._operation_error("invalid_declared_clock_edge", path, "source must be a connected output/bidirectional pin")
            targets: list[tuple[Any, int]] = []
            for sink_index, sink in enumerate(sinks):
                sink_path = f"{path}.sinks[{sink_index}]"
                if not isinstance(sink, Mapping) or sink.get("kind") != "clock":
                    self._operation_error("invalid_declared_clock_sink", sink_path, "sink must explicitly declare kind=clock")
                chip_ref, pin = sink.get("chip"), sink.get("pin")
                if not isinstance(chip_ref, str) or not isinstance(pin, int) or chip_ref not in self._chips:
                    self._operation_error("invalid_declared_clock_sink", sink_path, "sink must name a live chip and numeric pin")
                target = self._chips[chip_ref].pin(pin)
                if target.direction != "in" or "CLK" not in target.name.upper() or target.net is not source_obj.net:
                    self._operation_error(
                        "invalid_declared_clock_sink", sink_path,
                        "sink must be a connected CLK input on the declared source net",
                    )
                targets.append((self._chips[chip_ref], pin))
            resolved.append({"id": edge_id, "source_line": source_obj.net.name, "targets": tuple(targets)})
        return tuple(resolved)

    def release_input(self, name: str) -> Any:
        """Release an input or inout boundary to high impedance."""
        result = self.set_input(name, Z)
        binding = self.inputs[name]
        sources = (binding,) if isinstance(binding, LogicSource) else binding
        for source in sources:
            for net in self.board.nets.values():
                if source in net.sources:
                    for virtual in self._virtual_sources_by_line.get(net.name, ()):
                        virtual.enabled = True
                    net.resolve()
        self.board.settle()
        return result

    def load_memory_image(
        self, ref: str, image: str | Path, *, offset: int = 0,
        fmt: str = "auto", clear: int | None = None,
    ) -> int:
        """Load ROM/RAM through a model's public mutable memory contract."""

        chip = self._chips.get(ref)
        if chip is None:
            self._operation_error("unknown_chip", ref, f"chip ref {ref!r} is not bound")
        try:
            count = load_live_chip_memory(chip, image, offset=offset, fmt=fmt, clear=clear)
        except ModelLoadError as exc:
            self._operation_error("memory_image_not_loadable", ref, str(exc))
        self.board.settle()
        return count

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

    def pulse_clock(
        self, name: str = "CLK", *, return_low: bool = False,
        propagated_rising_on_fall: tuple[str, ...] = (),
    ) -> dict[str, Logic]:
        """Pulse a public clock input, optionally completing its low phase.

        ``propagated_rising_on_fall`` names real gated-clock nets which must
        rise while the public source returns low.  It is explicit because the
        event scheduler must not infer clock events from arbitrary data-net
        transitions.  This supports active-low gated clocks such as RV8GR
        ``ACC_CLK = NAND(T2, AC_WR)`` without forcing a register output or
        private model state.
        """
        if name not in self.inputs:
            self._operation_error("unknown_clock", name, f"clock port {name!r} is not bound")
        unknown_edges = [edge for edge in propagated_rising_on_fall if edge not in self._net_lines]
        if unknown_edges:
            self._operation_error(
                "unknown_propagated_clock", unknown_edges[0],
                f"clock net {unknown_edges[0]!r} is not a concrete circuit net",
            )
        self.set_input(name, 0)
        binding = self.inputs[name]
        if not isinstance(binding, LogicSource):
            self._operation_error("vector_clock", name, f"clock port {name!r} must be scalar")
        self.board.set_source(binding.name, 1)
        # A hierarchy compiler is free to qualify the physical net name.  The
        # public port name is only a boundary label, so never use it to locate
        # clock receivers.  This mattered first for RV8GR_PC16: its flattened
        # clock is ``__flat_PC16_CLK...``, not the root boundary label ``CLK``.
        # Drive the public source above, then deliver the edge to every real
        # pin attached to that resolved boundary line.
        clock_lines = self._boundary_lines.get(name, self._net_lines.get(name, (name,)))
        for line in clock_lines:
            net = self.board.net(line)
            for pin in tuple(net.pins):
                pin.chip.clock_edge(pin.number)
        self.board.settle()
        if not return_low:
            if propagated_rising_on_fall:
                self._operation_error(
                    "propagated_clock_requires_return_low", name,
                    "gated clocks declared on the falling phase require return_low=True",
                )
            return self.read()

        before = {
            edge: tuple(self.board.net(line).value for line in self._net_lines[edge])
            for edge in propagated_rising_on_fall
        }
        self.board.set_source(binding.name, 0)
        self.board.settle()
        for edge in propagated_rising_on_fall:
            after = tuple(self.board.net(line).value for line in self._net_lines[edge])
            if not any(old == 0 and new == 1 for old, new in zip(before[edge], after)):
                self._operation_error(
                    "propagated_clock_no_rising_edge", edge,
                    f"declared gated clock {edge!r} did not rise during {name!r} pulse",
                )
            for line, old, new in zip(self._net_lines[edge], before[edge], after):
                if old != 0 or new != 1:
                    continue
                for pin in tuple(self.board.net(line).pins):
                    pin.chip.clock_edge(pin.number)
        self.board.settle()
        return self.read()

    def run_modeled_post_clock_samples(self, clock: str) -> tuple[dict[str, Any], ...]:
        """Run package-declared delayed sampling that is part of a model contract.

        This is deliberately *not* a general clock inference feature.  A package
        must name each target pin and its source-backed delay in
        ``runtime.modeled_post_clock_samples``.  It is useful where the
        authoritative chip-level RTL samples a real clock after a model delay
        (RV8GR U21 is the first case).  The generic chip model remains an
        ordinary edge-triggered device; only the owning circuit opts in.
        """
        runtime = self.package.raw.get("runtime", {})
        specs = runtime.get("modeled_post_clock_samples", []) if isinstance(runtime, Mapping) else []
        results: list[dict[str, Any]] = []
        for index, spec in enumerate(specs):
            if not isinstance(spec, Mapping) or spec.get("clock") != clock:
                continue
            delay_ns = spec.get("delay_ns")
            targets = spec.get("targets")
            if (not isinstance(delay_ns, int) or isinstance(delay_ns, bool) or delay_ns < 0
                    or not isinstance(targets, list) or not targets):
                self._operation_error(
                    "invalid_modeled_post_clock_sample", f"runtime.modeled_post_clock_samples[{index}]",
                    "sample must declare a non-negative delay_ns and one or more targets",
                )
            resolved: list[tuple[Any, int, str]] = []
            for target in targets:
                if not isinstance(target, Mapping):
                    self._operation_error("invalid_modeled_post_clock_sample", f"runtime.modeled_post_clock_samples[{index}].targets", "target must name a chip and pin")
                chip_ref, pin = target.get("chip"), target.get("pin")
                if not isinstance(chip_ref, str) or not isinstance(pin, int) or chip_ref not in self._chips:
                    self._operation_error("invalid_modeled_post_clock_sample", f"runtime.modeled_post_clock_samples[{index}].targets", "target chip/pin is not a live component")
                if clock not in self._net_lines or not any(
                    candidate.chip is self._chips[chip_ref] and candidate.number == pin
                    for line in self._net_lines[clock] for candidate in self.board.net(line).pins
                ):
                    self._operation_error("invalid_modeled_post_clock_sample", f"runtime.modeled_post_clock_samples[{index}].targets", "target pin must be connected to the declared clock net")
                resolved.append((self._chips[chip_ref], pin, chip_ref))

            # Board time is advanced through its event queue; no output or
            # private state is forced.  The explicit clock_edge is the delayed
            # sample event specified by the package's authoritative RTL model.
            for chip, pin, _chip_ref in resolved:
                self.board.schedule(delay_ns, lambda c=chip, p=pin: c.clock_edge(p))
            self.board.settle()
            results.append({"name": spec.get("name", f"sample_{index}"), "clock": clock,
                            "delay_ns": delay_ns, "targets": tuple(ref for _, _, ref in resolved)})
        return tuple(results)

    def initialize_state(self, state: str, value: Logic | int | tuple[Logic, ...] | list[Logic]) -> dict[str, Any]:
        """Load a declared state through public inputs and its real clock edge.

        Packages opt in using ``runtime.state_initializers``.  The contract is
        deliberately limited to a named data boundary, fixed public controls,
        and a declared gated-clock transition; it cannot reach into a chip
        model or force an output.  This makes an independent proof vector's
        initial register state reproducible through the same edge behavior used
        by the circuit.
        """
        runtime = self.package.raw.get("runtime", {})
        initializers = runtime.get("state_initializers", []) if isinstance(runtime, Mapping) else []
        spec = next((item for item in initializers if isinstance(item, Mapping) and item.get("state") == state), None)
        if spec is None:
            self._operation_error("unknown_state_initializer", state, f"state {state!r} has no declared public initializer")
        required = ("data_input", "controls", "clock_input", "gated_clock", "observe")
        missing = [key for key in required if key not in spec]
        if spec.get("kind") != "clocked_write" or missing:
            self._operation_error("invalid_state_initializer", state, "initializer must declare clocked_write data, controls, clock, gated_clock, and observe")
        data_input = spec["data_input"]
        controls = spec["controls"]
        clock_input = spec["clock_input"]
        gated_clock = spec["gated_clock"]
        observe = spec["observe"]
        if not all(isinstance(item, str) and item in self.inputs for item in (data_input, clock_input)):
            self._operation_error("invalid_state_initializer", state, "initializer data_input and clock_input must be public input ports")
        if not isinstance(controls, Mapping) or any(name not in self.inputs for name in controls):
            self._operation_error("invalid_state_initializer", state, "initializer controls must name public input ports")
        if not isinstance(gated_clock, str) or gated_clock not in self._net_lines:
            self._operation_error("invalid_state_initializer", state, "initializer gated_clock must name a concrete circuit net")
        if not isinstance(observe, str) or observe not in self.probes:
            self._operation_error("invalid_state_initializer", state, "initializer observe must name a public output or bidirectional port")
        self.set_input(clock_input, 0)
        self.set_input(data_input, value)
        for name, control_value in controls.items():
            self.set_input(name, control_value)
        self.pulse_clock(
            clock_input, return_low=True,
            propagated_rising_on_fall=(gated_clock,),
        )
        samples = self.run_modeled_post_clock_samples(gated_clock)
        observed = self.read(observe)
        expected = self._coerce_vector(data_input, value, len(self._expand_name(observe)))
        if observed != (expected[0] if len(expected) == 1 else expected):
            self._operation_error(
                "state_initializer_mismatch", state,
                f"{state!r} initializer observed {observed!r}, expected {expected!r}",
            )
        return {"state": state, "observed": observed, "clock": gated_clock, "modeled_samples": samples}

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
