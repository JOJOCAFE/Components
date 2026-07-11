"""Deterministic discovery and validation for hierarchical circuit packages.

This module plans hierarchy only.  It deliberately does not construct chips or
change net semantics; the circuit runner may consume a validated plan later.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .circuit_package import CIRCUIT_ROOT, CircuitPackage, SymbolicEndpoint, load_circuit_package


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
