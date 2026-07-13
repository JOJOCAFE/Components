"""Tests for strict, runtime-independent circuit package parsing."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from chiplib.circuit_package import (
    BoundaryEndpoint,
    BoundaryConcatEndpoint,
    BoundarySelectorEndpoint,
    CircuitPackageValidationError,
    NumericEndpoint,
    SymbolicEndpoint,
    load_circuit_package,
    parse_circuit_package,
)


ROOT = Path(__file__).resolve().parents[2]
CIRCUIT_FILES = sorted((ROOT / "examples" / "circuits").glob("*/circuit.json"))


def valid_package() -> dict:
    return {
        "schema": "components.lib.circuit",
        "version": 1,
        "id": "parser-fixture",
        "title": "Parser fixture",
        "source_project": {"name": "Components", "paths": ["python/chiplib/db.py"]},
        "chips": [
            {"ref": "U1", "part": "74HC04", "role": "inverter"},
            {"ref": "BLOCK", "part": "descriptive", "role": "boundary", "symbolic_endpoints": ["OUT"]},
        ],
        "ports": [{"name": "IN", "direction": "input"}, {"name": "OUT", "direction": "output"}],
        "wiring": [
            {"net": "IN", "connections": ["IN", "U1.1"]},
            {"net": "OUT", "connections": ["U1.2", "BLOCK.OUT", "OUT"]},
        ],
        "verification": {"tests": ["python/tests/test_circuit_package.py"]},
    }


class CircuitPackageTests(unittest.TestCase):
    def test_all_23_library_packages_parse(self) -> None:
        self.assertEqual(23, len(CIRCUIT_FILES))
        packages = [load_circuit_package(path) for path in CIRCUIT_FILES]
        self.assertEqual(23, len(packages))
        self.assertEqual(23, len({package.id for package in packages}))
        self.assertTrue(all(package.schema == "components.lib.circuit" for package in packages))

    def test_returns_typed_chips_ports_wiring_and_verification(self) -> None:
        package = parse_circuit_package(valid_package(), source_path=ROOT / "fixture.json")
        self.assertEqual("U1", package.chips[0].ref)
        self.assertEqual("input", package.ports[0].direction)
        self.assertIsInstance(package.wiring[0].connections[0], BoundaryEndpoint)
        self.assertIsInstance(package.wiring[0].connections[1], NumericEndpoint)
        self.assertIsInstance(package.wiring[1].connections[1], SymbolicEndpoint)
        self.assertEqual((1,), package.wiring[0].connections[1].pins)
        self.assertTrue(package.verification[0].resolved_path.is_file())

    def test_numeric_ranges_are_preserved_and_expanded(self) -> None:
        data = valid_package()
        data["wiring"][0]["connections"][1] = "U1.1..6"
        package = parse_circuit_package(data, source_path=ROOT / "fixture.json")
        endpoint = package.wiring[0].connections[1]
        self.assertIsInstance(endpoint, NumericEndpoint)
        self.assertEqual((1, 2, 3, 4, 5, 6), endpoint.pins)

    def test_boundary_selector_is_explicit_ordered_source_mapping(self) -> None:
        data = valid_package()
        data["ports"][0]["name"] = "IRH0..IRH7"
        data["wiring"][0] = {"net": "CTRL", "connections": ["IRH0..IRH7[3]", "U1.1"]}
        package = parse_circuit_package(data, source_path=ROOT / "fixture.json")
        endpoint = package.wiring[0].connections[0]
        self.assertIsInstance(endpoint, BoundarySelectorEndpoint)
        self.assertEqual("IRH0..IRH7", endpoint.base)
        self.assertEqual((3,), endpoint.indices)

    def test_rejects_selector_width_and_index_errors(self) -> None:
        data = valid_package()
        data["ports"][0]["name"] = "IRH0..IRH7"
        data["wiring"][0] = {"net": "CTRL0..CTRL1", "connections": ["IRH0..IRH7[9]", "U1.1"]}
        with self.assertRaises(CircuitPackageValidationError) as caught:
            parse_circuit_package(data, source_path=ROOT / "fixture.json")
        self.assertEqual(
            {"selector_index_out_of_range", "selector_width_mismatch"},
            {item.code for item in caught.exception.issues},
        )

    def test_boundary_concat_is_an_explicit_ordered_mapping(self) -> None:
        data = valid_package()
        data["ports"] = [
            {"name": "IRL0..IRL7", "direction": "input"},
            {"name": "DP0..DP6", "direction": "input"},
            {"name": "OUT", "direction": "output"},
        ]
        data["wiring"][0] = {"net": "A0..A14", "connections": ["{IRL0..IRL7,DP0..DP6}"]}
        package = parse_circuit_package(data, source_path=ROOT / "fixture.json")
        endpoint = package.wiring[0].connections[0]
        self.assertIsInstance(endpoint, BoundaryConcatEndpoint)
        self.assertEqual(("IRL0..IRL7", "DP0..DP6"), endpoint.terms)

    def test_rejects_concat_with_wrong_total_width(self) -> None:
        data = valid_package()
        data["ports"][0]["name"] = "IRL0..IRL7"
        data["ports"].append({"name": "DP0..DP7", "direction": "input"})
        data["wiring"][0] = {"net": "A0..A14", "connections": ["{IRL0..IRL7,DP0..DP7}"]}
        with self.assertRaises(CircuitPackageValidationError) as caught:
            parse_circuit_package(data, source_path=ROOT / "fixture.json")
        self.assertEqual({"concat_width_mismatch"}, {item.code for item in caught.exception.issues})

    def test_collects_structured_duplicate_and_reference_errors(self) -> None:
        data = valid_package()
        data["chips"].append(deepcopy(data["chips"][0]))
        data["wiring"].append(deepcopy(data["wiring"][0]))
        data["wiring"][0]["connections"].extend(["U9.1", "MISSING", "U1.99"])
        data["verification"]["tests"].append("missing-proof.json")
        with self.assertRaises(CircuitPackageValidationError) as caught:
            parse_circuit_package(data, source_path=ROOT / "fixture.json")
        payload = caught.exception.to_dict()
        codes = {item["code"] for item in payload["issues"]}
        self.assertTrue({"duplicate_ref", "duplicate_net", "unknown_ref", "undeclared_boundary", "unknown_pin", "proof_not_found"}.issubset(codes))
        self.assertEqual("invalid_circuit_package", payload["error"])

    def test_rejects_undeclared_symbolic_chip_boundary(self) -> None:
        data = valid_package()
        data["wiring"][1]["connections"][1] = "BLOCK.SECRET"
        with self.assertRaises(CircuitPackageValidationError) as caught:
            parse_circuit_package(data, source_path=ROOT / "fixture.json")
        self.assertIn("undeclared_symbolic_endpoint", {item.code for item in caught.exception.issues})

    def test_rejects_boundary_alias_bound_to_two_different_nets(self) -> None:
        data = valid_package()
        data["ports"].append({"name": "ALIAS", "direction": "input"})
        data["wiring"][0]["connections"].append("ALIAS")
        data["wiring"][1]["connections"].append("ALIAS")
        with self.assertRaises(CircuitPackageValidationError) as caught:
            parse_circuit_package(data, source_path=ROOT / "fixture.json")
        self.assertIn("ambiguous_boundary_mapping", {item.code for item in caught.exception.issues})

    def test_rejects_missing_source_and_malformed_json(self) -> None:
        data = valid_package()
        data["source_project"]["paths"] = ["does/not/exist.md"]
        with self.assertRaises(CircuitPackageValidationError) as caught:
            parse_circuit_package(data, source_path=ROOT / "fixture.json")
        self.assertIn("source_not_found", {item.code for item in caught.exception.issues})

        bad = ROOT / "python" / "tests" / "_not_written_invalid.json"
        with self.assertRaises(CircuitPackageValidationError):
            load_circuit_package(bad)

    def test_parser_does_not_import_runtime_or_tests(self) -> None:
        module = (ROOT / "python" / "chiplib" / "circuit_package.py").read_text(encoding="utf-8")
        self.assertNotIn("chiplib.chips", module)
        self.assertNotIn("chiplib.netlist", module)
        self.assertNotIn("python.tests", module)


if __name__ == "__main__":
    unittest.main()
