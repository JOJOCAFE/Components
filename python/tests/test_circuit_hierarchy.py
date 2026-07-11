"""Tests for deterministic hierarchical circuit package planning."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from chiplib.circuit_hierarchy import (
    CircuitHierarchyError,
    discover_circuit_packages,
    flatten_circuit_hierarchy,
)
from chiplib.circuit_package import parse_circuit_package


ROOT = Path(__file__).resolve().parents[2]


def package_data(package_id: str, chips: list[dict], ports: list[dict], wiring: list[dict]) -> dict:
    return {
        "schema": "components.lib.circuit",
        "version": 1,
        "id": package_id,
        "title": package_id,
        "source_project": {"name": "test", "paths": ["python/chiplib/core.py"]},
        "chips": chips,
        "ports": ports,
        "wiring": wiring,
        "verification": {"tests": ["python/tests/test_circuit_hierarchy.py"]},
    }


def fixtures():
    leaf_data = package_data(
        "leaf",
        [{"ref": "U1", "part": "74HC04", "role": "invert"}],
        [{"name": "IN", "direction": "input"}, {"name": "OUT", "direction": "output"}],
        [
            {"net": "IN", "connections": ["IN", "U1.1"]},
            {"net": "OUT", "connections": ["U1.2", "OUT"]},
        ],
    )
    leaf = parse_circuit_package(leaf_data, source_path=ROOT / "leaf.json")
    parent_data = package_data(
        "parent",
        [{
            "ref": "BLOCK",
            "part": "LeafPackage",
            "role": "child",
            "symbolic_endpoints": ["IN", "OUT"],
        }],
        [{"name": "A", "direction": "input"}, {"name": "Y", "direction": "output"}],
        [
            {"net": "A", "connections": ["A", "BLOCK.IN"]},
            {"net": "Y", "connections": ["BLOCK.OUT", "Y"]},
        ],
    )
    parent = parse_circuit_package(parent_data, source_path=ROOT / "parent.json")
    return leaf, parent, parent_data


class CircuitHierarchyTests(unittest.TestCase):
    def test_discovers_all_library_packages_by_directory_and_id(self) -> None:
        catalog = discover_circuit_packages()
        sources = {package.source_path for package in catalog.values()}
        self.assertEqual(22, len(sources))
        self.assertIn("RV8GR_BusOwnership", catalog)
        self.assertIn("rv8gr_bus_ownership", catalog)

    def test_flattens_explicit_mapping_with_stable_qualified_names(self) -> None:
        leaf, parent, _ = fixtures()
        plan = flatten_circuit_hierarchy(parent, {"LeafPackage": leaf})
        self.assertEqual((('IN', 'A'), ('OUT', 'Y')), plan.composites[0].port_nets)
        self.assertEqual("BLOCK.U1", plan.leaves[0].instance_path)
        self.assertEqual(("A", "BLOCK.IN", "BLOCK.OUT", "Y"), plan.nets)

    def test_rejects_missing_mapping_with_structured_diagnostic(self) -> None:
        leaf, _, parent_data = fixtures()
        parent_data["wiring"] = parent_data["wiring"][:1]
        parent = parse_circuit_package(parent_data, source_path=ROOT / "parent.json")
        with self.assertRaises(CircuitHierarchyError) as caught:
            flatten_circuit_hierarchy(parent, {"LeafPackage": leaf})
        payload = caught.exception.to_dict()
        self.assertEqual("invalid_circuit_hierarchy", payload["error"])
        self.assertIn("missing_child_port_mapping", {row["code"] for row in payload["issues"]})
        self.assertIn("BLOCK.OUT", {row["path"] for row in payload["issues"]})

    def test_rejects_duplicate_mapping_deterministically(self) -> None:
        leaf, _, parent_data = fixtures()
        parent_data["wiring"].append({"net": "A_COPY", "connections": ["BLOCK.IN"]})
        parent = parse_circuit_package(parent_data, source_path=ROOT / "parent.json")
        with self.assertRaises(CircuitHierarchyError) as caught:
            flatten_circuit_hierarchy(parent, {"LeafPackage": leaf})
        issue = next(row for row in caught.exception.issues if row.code == "duplicate_child_port_mapping")
        self.assertEqual("BLOCK.IN", issue.path)
        self.assertIn("A, A_COPY", issue.message)

    def test_detects_recursive_package_cycle(self) -> None:
        leaf, parent, _ = fixtures()
        loop_data = deepcopy(leaf.raw)
        loop_data["id"] = "loop"
        loop_data["chips"] = [{
            "ref": "SELF", "part": "LoopPackage", "role": "cycle",
            "symbolic_endpoints": ["IN", "OUT"],
        }]
        loop_data["wiring"] = [
            {"net": "IN", "connections": ["IN", "SELF.IN"]},
            {"net": "OUT", "connections": ["SELF.OUT", "OUT"]},
        ]
        loop = parse_circuit_package(loop_data, source_path=ROOT / "loop.json")
        with self.assertRaises(CircuitHierarchyError) as caught:
            flatten_circuit_hierarchy(loop, {"LoopPackage": loop, "LeafPackage": leaf, "Parent": parent})
        self.assertIn("hierarchy_cycle", {row.code for row in caught.exception.issues})

    def test_current_composites_fail_loudly_until_mappings_are_explicit(self) -> None:
        catalog = discover_circuit_packages()
        for name in ("RV8GR_FullControlOpcodeSweep", "RV8GR_WholeSystemChipLevelVirtual"):
            with self.subTest(name=name), self.assertRaises(CircuitHierarchyError) as caught:
                flatten_circuit_hierarchy(catalog[name], catalog)
            self.assertIn(
                "missing_child_port_mapping",
                {row.code for row in caught.exception.issues},
            )


if __name__ == "__main__":
    unittest.main()
