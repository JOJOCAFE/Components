"""Deterministic discovery and validation for hierarchical circuit packages.

This module plans hierarchy only.  It deliberately does not construct chips or
change net semantics; the circuit runner may consume a validated plan later.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .circuit_package import (
    CIRCUIT_ROOT,
    BoundaryEndpoint,
    BoundaryConcatEndpoint,
    BoundarySelectorEndpoint,
    CircuitChip,
    CircuitPackage,
    CircuitWiring,
    NumericEndpoint,
    SymbolicEndpoint,
    load_circuit_package,
)


NON_BINDING_DIRECTIONS = frozenset({"internal", "absent", "power"})
PROOF_GATE_BEHAVIOR_KEYS = frozenset({"coverage_rule", "system_rule"})


@dataclass(frozen=True)
class HierarchyIssue:
    code: str
    path: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "message": self.message}


class CircuitHierarchyError(ValueError):
    """Raised with all deterministic hierarchy diagnostics."""

    def __init__(self, issues: list[HierarchyIssue]):
        self.issues = tuple(sorted(issues, key=lambda item: (item.path, item.code, item.message)))
        detail = "; ".join(
            f"{item.path} [{item.code}] {item.message}" for item in self.issues
        )
        super().__init__(f"invalid circuit hierarchy: {detail}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": "invalid_circuit_hierarchy",
            "issues": [item.to_dict() for item in self.issues],
        }


@dataclass(frozen=True)
class CompositeInstance:
    instance_path: str
    ref: str
    package_id: str
    part: str
    port_nets: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class LeafInstance:
    instance_path: str
    ref: str
    part: str


@dataclass(frozen=True)
class FlattenedHierarchy:
    root_package_id: str
    composites: tuple[CompositeInstance, ...]
    leaves: tuple[LeafInstance, ...]
    nets: tuple[str, ...]


@dataclass(frozen=True)
class FlattenedExecution:
    """A fail-closed, one-Board materialization of an explicit hierarchy.

    ``package`` contains only concrete leaf chips and scalar nets.  The root
    package's public boundaries are kept separately because an ordered vector
    boundary need not be represented by one physical wire in the flattened
    package.  This is intentionally an internal runner contract, not a new
    source-file format.
    """

    package: CircuitPackage
    boundary_lines: Mapping[str, tuple[str, ...]]


class _UnionFind:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def add(self, item: str) -> None:
        self.parent.setdefault(item, item)

    def find(self, item: str) -> str:
        self.add(item)
        if self.parent[item] != item:
            self.parent[item] = self.find(self.parent[item])
        return self.parent[item]

    def union(self, left: str, right: str) -> None:
        left_root, right_root = self.find(left), self.find(right)
        if left_root != right_root:
            self.parent[right_root] = left_root


def discover_circuit_packages(root: str | Path = CIRCUIT_ROOT) -> dict[str, CircuitPackage]:
    """Load packages in stable path order and index directory names and IDs.

    Directory names are the canonical values currently used by ``chips[].part``.
    IDs are accepted aliases.  Any ambiguous alias fails instead of selecting a
    package based on filesystem iteration order.
    """

    packages: dict[str, CircuitPackage] = {}
    owners: dict[str, Path | None] = {}
    issues: list[HierarchyIssue] = []
    for path in sorted(Path(root).glob("*/circuit.json"), key=lambda item: item.as_posix()):
        package = load_circuit_package(path)
        for key in (path.parent.name, package.id):
            if key in packages and packages[key].source_path != package.source_path:
                issues.append(HierarchyIssue(
                    "ambiguous_package_name",
                    str(path),
                    f"package key {key!r} is already provided by {owners[key]}",
                ))
                continue
            packages[key] = package
            owners[key] = package.source_path
    if issues:
        raise CircuitHierarchyError(issues)
    return packages


def flatten_circuit_hierarchy(
    package: CircuitPackage,
    catalog: Mapping[str, CircuitPackage] | None = None,
) -> FlattenedHierarchy:
    """Validate explicit child bindings and return a stable flattened plan."""

    available = catalog if catalog is not None else discover_circuit_packages()
    issues: list[HierarchyIssue] = []
    composites: list[CompositeInstance] = []
    leaves: list[LeafInstance] = []
    nets: set[str] = set()

    def walk(current: CircuitPackage, prefix: str, ancestry: tuple[str, ...]) -> None:
        if current.id in ancestry:
            cycle = " -> ".join((*ancestry, current.id))
            issues.append(HierarchyIssue("hierarchy_cycle", prefix or current.id, cycle))
            return

        proof_gate_reason = _independent_proof_gate_reason(current, available)
        if proof_gate_reason is not None:
            issues.append(HierarchyIssue(
                "independent_proof_scenarios_not_composable",
                prefix or current.id,
                proof_gate_reason,
            ))
            return

        local_nets = {wire.net: _qualify(prefix, wire.net) for wire in current.wiring}
        nets.update(local_nets.values())
        endpoint_bindings: dict[tuple[str, str], list[str]] = {}
        for wire in current.wiring:
            qualified_net = local_nets[wire.net]
            for endpoint in wire.connections:
                if isinstance(endpoint, SymbolicEndpoint):
                    endpoint_bindings.setdefault((endpoint.ref, endpoint.name), []).append(qualified_net)

        for chip in sorted(current.chips, key=lambda item: item.ref):
            instance_path = _qualify(prefix, chip.ref)
            child = available.get(chip.part)
            if child is None:
                leaves.append(LeafInstance(instance_path, chip.ref, chip.part))
                continue

            bindings: list[tuple[str, str]] = []
            required = sorted(
                port.name for port in child.ports if port.direction not in NON_BINDING_DIRECTIONS
            )
            for port_name in required:
                matches = endpoint_bindings.get((chip.ref, port_name), [])
                issue_path = f"{instance_path}.{port_name}"
                if not matches:
                    issues.append(HierarchyIssue(
                        "missing_child_port_mapping",
                        issue_path,
                        f"{chip.part}.{port_name} is not connected by parent wiring",
                    ))
                elif len(matches) > 1:
                    issues.append(HierarchyIssue(
                        "duplicate_child_port_mapping",
                        issue_path,
                        f"mapped to multiple parent nets: {', '.join(sorted(matches))}",
                    ))
                else:
                    bindings.append((port_name, matches[0]))

            declared = {port.name for port in child.ports}
            for (ref, port_name), mapped_nets in sorted(endpoint_bindings.items()):
                if ref == chip.ref and port_name not in declared:
                    issues.append(HierarchyIssue(
                        "unknown_child_port",
                        f"{instance_path}.{port_name}",
                        f"{chip.part} has no port {port_name!r}; mapped on {', '.join(sorted(mapped_nets))}",
                    ))

            composites.append(CompositeInstance(
                instance_path,
                chip.ref,
                child.id,
                chip.part,
                tuple(sorted(bindings)),
            ))
            walk(child, instance_path, (*ancestry, current.id))

    walk(package, "", ())
    if issues:
        raise CircuitHierarchyError(issues)
    return FlattenedHierarchy(
        package.id,
        tuple(sorted(composites, key=lambda item: item.instance_path)),
        tuple(sorted(leaves, key=lambda item: item.instance_path)),
        tuple(sorted(nets)),
    )


def flatten_circuit_for_execution(
    package: CircuitPackage,
    catalog: Mapping[str, CircuitPackage] | None = None,
) -> FlattenedExecution:
    """Materialize explicit child wiring into one concrete, shared Board.

    This compiler never uses matching names as a connection rule.  A parent
    wire must name every child port it crosses; selectors are applied only to
    their declared source boundary.  Each generated wire is scalar so ordered
    ranges become an unambiguous collection of Board nets.
    """

    available = catalog if catalog is not None else discover_circuit_packages()
    issues: list[HierarchyIssue] = []
    uf = _UnionFind()
    leaves: list[tuple[str, CircuitChip]] = []
    pin_nodes: list[tuple[str, NumericEndpoint, int, str]] = []
    # Flattened execution retains physical rails.  A child package's VCC/GND
    # net must not silently become an un-driven ordinary net when its numeric
    # pins are materialized onto the parent Board.
    rail_lines: dict[str, set[str]] = {"VCC": set(), "GND": set()}

    def node(scope: str, kind: str, name: str, index: int) -> str:
        return f"{scope}|{kind}|{name}|{index}"

    def wire_nodes(scope: str, name: str) -> tuple[str, ...]:
        from .circuit_package import expand_boundary_name
        values = tuple(node(scope, "wire", name, index) for index, _ in enumerate(expand_boundary_name(name)))
        for value in values:
            uf.add(value)
        return values

    def port_nodes(scope: str, name: str) -> tuple[str, ...]:
        from .circuit_package import expand_boundary_name
        values = tuple(node(scope, "port", name, index) for index, _ in enumerate(expand_boundary_name(name)))
        for value in values:
            uf.add(value)
        return values

    def boundary_nodes(scope: str, current: CircuitPackage, endpoint: object) -> tuple[str, ...] | None:
        from .circuit_package import expand_boundary_name
        names = {port.name for port in current.ports} | {wire.net for wire in current.wiring}
        if isinstance(endpoint, BoundaryEndpoint):
            if endpoint.text not in names:
                return None
            return port_nodes(scope, endpoint.text) if endpoint.text in {p.name for p in current.ports} else wire_nodes(scope, endpoint.text)
        if isinstance(endpoint, BoundarySelectorEndpoint):
            if endpoint.base not in names:
                return None
            base = port_nodes(scope, endpoint.base) if endpoint.base in {p.name for p in current.ports} else wire_nodes(scope, endpoint.base)
            return tuple(base[index] for index in endpoint.indices)
        if isinstance(endpoint, BoundaryConcatEndpoint):
            result: list[str] = []
            ports = {port.name for port in current.ports}
            for term in endpoint.terms:
                result.extend(port_nodes(scope, term) if term in ports else wire_nodes(scope, term))
            return tuple(result)
        return None

    def join(left: tuple[str, ...], right: tuple[str, ...], path: str, detail: str) -> None:
        if len(left) != len(right):
            issues.append(HierarchyIssue("hierarchy_width_mismatch", path, detail))
            return
        for left_line, right_line in zip(left, right):
            uf.union(left_line, right_line)

    def walk(current: CircuitPackage, scope: str, ancestry: tuple[str, ...]) -> None:
        if current.id in ancestry:
            issues.append(HierarchyIssue("hierarchy_cycle", scope or current.id, " -> ".join((*ancestry, current.id))))
            return
        proof_reason = _independent_proof_gate_reason(current, available)
        if proof_reason is not None:
            issues.append(HierarchyIssue("independent_proof_scenarios_not_composable", scope or current.id, proof_reason))
            return

        for port in current.ports:
            port_nodes(scope, port.name)
        # A package port and a same-named package wire are the package's own
        # declared boundary implementation.  Joining them is local to this
        # package (not cross-child name inference), and mirrors the direct
        # CircuitRunner contract where an input named T2 drives the T2 wire.
        # Child-to-parent joins still require an explicit `CHILD.port` entry.
        local_wire_names = {wire.net for wire in current.wiring}
        for port in current.ports:
            if port.name in local_wire_names:
                join(
                    port_nodes(scope, port.name), wire_nodes(scope, port.name),
                    f"{scope}.{port.name}".strip("."),
                    f"package port {port.name!r} width does not match its same-named local wire",
                )
        for wire in current.wiring:
            lines = wire_nodes(scope, wire.net)
            if wire.net.upper() in rail_lines:
                rail_lines[wire.net.upper()].update(lines)
            for endpoint in wire.connections:
                boundary = boundary_nodes(scope, current, endpoint)
                if boundary is not None:
                    join(lines, boundary, f"{scope}.{wire.net}".strip("."), f"boundary {endpoint.text!r} width does not match net {wire.net!r}")

        child_map = {chip.ref: available.get(chip.part) for chip in current.chips}
        mappings: dict[tuple[str, str], list[tuple[str, ...]]] = {}
        for wire in current.wiring:
            lines = wire_nodes(scope, wire.net)
            for endpoint in wire.connections:
                if isinstance(endpoint, SymbolicEndpoint) and child_map.get(endpoint.ref) is not None:
                    mappings.setdefault((endpoint.ref, endpoint.name), []).append(lines)

        leaf_scopes: dict[str, str] = {}
        for chip in current.chips:
            child = child_map[chip.ref]
            child_scope = _qualify(scope, chip.ref)
            if child is None:
                leaves.append((child_scope, chip))
                leaf_scopes[chip.ref] = child_scope
                continue

            declared = {port.name: port for port in child.ports}
            for port_name, port in declared.items():
                if port.direction in NON_BINDING_DIRECTIONS:
                    continue
                matches = mappings.get((chip.ref, port_name), [])
                path = f"{child_scope}.{port_name}"
                if not matches:
                    issues.append(HierarchyIssue("missing_child_port_mapping", path, f"{chip.part}.{port_name} is not connected by parent wiring"))
                elif len(matches) != 1:
                    issues.append(HierarchyIssue("duplicate_child_port_mapping", path, "mapped to multiple parent nets"))
                else:
                    join(matches[0], port_nodes(child_scope, port_name), path, f"parent mapping width does not match {chip.part}.{port_name}")
            for (ref, port_name), _matches in mappings.items():
                if ref == chip.ref and port_name not in declared:
                    issues.append(HierarchyIssue("unknown_child_port", f"{child_scope}.{port_name}", f"{chip.part} has no port {port_name!r}"))
            walk(child, child_scope, (*ancestry, current.id))

        # Follow CircuitRunner's ordered scalar-run rule across *all* concrete
        # chips on a wire.  An 8-bit net may intentionally join two 4-bit ICs.
        for wire in current.wiring:
            lines = wire_nodes(scope, wire.net)
            endpoints = [endpoint for endpoint in wire.connections
                         if isinstance(endpoint, NumericEndpoint) and endpoint.ref in leaf_scopes]
            scalar: list[NumericEndpoint] = []
            def flush_scalars() -> None:
                if not scalar:
                    return
                if len(scalar) % len(lines):
                    issues.append(HierarchyIssue("hierarchy_width_mismatch", scope or current.id,
                        f"{wire.net!r} has {len(scalar)} scalar pins for width {len(lines)}"))
                else:
                    for index, item in enumerate(scalar):
                        pin_nodes.append((leaf_scopes[item.ref], item, item.start, lines[index % len(lines)]))
                scalar.clear()
            for endpoint in endpoints:
                if len(endpoint.pins) == 1:
                    scalar.append(endpoint)
                    if len(scalar) == len(lines):
                        flush_scalars()
                else:
                    flush_scalars()
                    if len(endpoint.pins) != len(lines):
                        issues.append(HierarchyIssue("hierarchy_width_mismatch", f"{scope}.{endpoint.text}".strip("."), f"pin range width does not match {wire.net!r}"))
                    else:
                        for line, pin in zip(lines, endpoint.pins):
                            pin_nodes.append((leaf_scopes[endpoint.ref], endpoint, pin, line))
            flush_scalars()

    walk(package, "", ())
    if issues:
        raise CircuitHierarchyError(issues)

    groups: dict[str, list[tuple[str, NumericEndpoint, int]]] = {}
    for path, endpoint, pin, line in pin_nodes:
        groups.setdefault(uf.find(line), []).append((path, endpoint, pin))
    # A vector input may intentionally expose only one selected bit to a child.
    # Keep the other public lines as real Board nets so vector source ordering
    # stays visible; an unconnected *output* remains a runner error below.
    for port in package.ports:
        for port_line in port_nodes("", port.name):
            groups.setdefault(uf.find(port_line), [])
    def flat_net_name(group: str, index: int) -> str:
        # Use a qualified source node for diagnostics/snapshots rather than an
        # anonymous counter.  It is generated only after explicit unioning.
        members = sorted(item for item in uf.parent if uf.find(item) == group)
        scope, _kind, name, bit = members[0].split("|", 3)
        prefix = scope.replace(".", "_") or "root"
        safe_name = name.replace(".", "_")
        return f"__flat_{prefix}_{safe_name}_{bit}_{index}"
    line_for_group = {group: flat_net_name(group, index) for index, group in enumerate(sorted(groups), 1)}
    rails_by_group: dict[str, set[str]] = {}
    for rail, lines in rail_lines.items():
        for line in lines:
            rails_by_group.setdefault(uf.find(line), set()).add(rail)
    wires = tuple(
        CircuitWiring(
            line_for_group[group],
            tuple(NumericEndpoint(f"{path.replace('.', '_')}.{pin}", path.replace('.', '_'), pin, pin)
                  for path, _endpoint, pin in sorted(endpoints, key=lambda item: (item[0], item[2])))
            + tuple(BoundaryEndpoint(rail) for rail in sorted(rails_by_group.get(group, ()))),
        )
        for group, endpoints in sorted(groups.items())
    )
    flat_chips = tuple(
        CircuitChip(path.replace(".", "_"), chip.part, chip.role, chip.symbolic_endpoints)
        for path, chip in sorted(leaves)
    )
    boundary_lines: dict[str, tuple[str, ...]] = {}
    for port in package.ports:
        lines: list[str] = []
        for port_line in port_nodes("", port.name):
            group = uf.find(port_line)
            lines.append(line_for_group[group])
        boundary_lines[port.name] = tuple(lines)
    if issues:
        raise CircuitHierarchyError(issues)
    raw = dict(package.raw)
    raw["chips"] = []
    raw["wiring"] = []
    return FlattenedExecution(
        CircuitPackage(package.schema, package.version, package.id, package.title, package.source_path,
                       package.source_project_name, package.sources, flat_chips, package.ports, wires,
                       package.verification, raw),
        boundary_lines,
    )


def _qualify(prefix: str, name: str) -> str:
    return f"{prefix}.{name}" if prefix else name


def _independent_proof_gate_reason(
    package: CircuitPackage,
    catalog: Mapping[str, CircuitPackage],
) -> str | None:
    """Identify a verification aggregate that is not an electrical hierarchy.

    A proof gate may list circuit packages so their separate results are all
    required, but that does not authorize tying same-named ports together.
    The package contract must explicitly describe proof reuse and must contain
    more than one child circuit before this guard applies.
    """

    behavior = package.raw.get("behavior")
    if not isinstance(behavior, Mapping):
        return None
    statements = [
        str(behavior[key]).lower()
        for key in sorted(PROOF_GATE_BEHAVIOR_KEYS)
        if key in behavior
    ]
    explicitly_reuses_proofs = any(
        "references existing executable circuit proofs" in statement
        or "proofs must all be part of the gate" in statement
        for statement in statements
    )
    child_refs = sorted(chip.ref for chip in package.chips if chip.part in catalog)
    if not explicitly_reuses_proofs or len(child_refs) < 2:
        return None
    return (
        "verification children are independent proof scenarios, not electrical "
        f"subcircuits ({', '.join(child_refs)}); run their proofs separately and "
        "aggregate results instead of paralleling same-named ports"
    )
