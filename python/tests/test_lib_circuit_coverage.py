"""Enforce evidence-backed RV8GR circuit coverage claims."""

from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INDEX_PATH = ROOT / "Lib" / "Circuits" / "RV8GR_COVERAGE_INDEX.json"
README_PATH = ROOT / "Lib" / "Circuits" / "README.md"
PHYSICAL_PLAN = "Lib/Circuits/physical_capture_plan.json"


def load_index() -> dict:
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


def load_evidence_test(reference: str) -> ast.FunctionDef:
    path_text, separator, symbol = reference.partition("::")
    path = ROOT / path_text
    assert path.is_file(), reference
    assert separator and symbol.startswith("test_"), reference
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    matches = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == symbol
    ]
    assert len(matches) == 1, reference
    test = matches[0]
    assert any(isinstance(node, ast.Assert) for node in ast.walk(test)), reference
    assert any(isinstance(node, ast.Call) for node in ast.walk(test)), reference
    return test


def assert_covered_layer_evidence(layer: str, refs: list[str]) -> None:
    file_refs = [ref for ref in refs if "::" not in ref]
    test_refs = [ref for ref in refs if "::" in ref]

    assert test_refs, (layer, refs)
    tests = [load_evidence_test(ref) for ref in test_refs]
    names = [test.name for test in tests]
    if layer == "structural":
        assert any(ref.endswith("/circuit.json") for ref in file_refs), refs
        assert any("package_shape" in name for name in names), refs
    elif layer == "vector_equation":
        assert any("/tests/" in ref and ref.endswith(".json") for ref in file_refs), refs
        assert not any("package_shape" in name for name in names), refs
    elif layer == "live_component_model":
        assert any("component_model" in name for name in names), refs
    elif layer == "composed_system":
        assert any(
            token in name
            for name in names
            for token in (
                "trace",
                "bus_driver",
                "bus_policy",
                "whole_system",
                "sequence",
                "flow",
                "assumption",
                "state",
                "fault",
            )
        ), refs


def test_rv8gr_coverage_index_has_allowed_layer_statuses_and_evidence():
    index = load_index()
    layers = index["coverage_layers"]
    allowed = index["allowed_statuses"]

    assert index["version"] == 2
    assert layers == [
        "structural",
        "vector_equation",
        "live_component_model",
        "composed_system",
        "physical",
    ]
    assert set(allowed) == set(layers)
    assert index["physical_evidence_plan"] == PHYSICAL_PLAN

    actual_packages = {
        path.parent.name
        for path in (ROOT / "Lib" / "Circuits").glob("RV8GR_*/circuit.json")
    }
    packages = {item["circuit"]: item for item in index["packages"]}
    assert set(packages) == actual_packages

    for package in packages.values():
        assert set(package["coverage"]) == set(layers), package["circuit"]
        for layer, claim in package["coverage"].items():
            assert claim["status"] in allowed[layer], (package["circuit"], layer, claim)
            refs = claim["evidence_refs"]
            if claim["status"] == "covered":
                assert refs, (package["circuit"], layer)
                assert_covered_layer_evidence(layer, refs)
            elif claim["status"] == "not_covered":
                assert refs == [], (package["circuit"], layer)
            for reference in refs:
                path_text = reference.partition("::")[0]
                assert (ROOT / path_text).is_file(), reference


def test_rv8gr_physical_coverage_remains_planned_and_not_measured():
    index = load_index()
    plan = json.loads((ROOT / PHYSICAL_PLAN).read_text(encoding="utf-8"))

    assert plan["status"] == "prepared_no_board_measurements"
    assert plan["blank_measurement_values"]["result_pass_fail"] == "not_measured"
    for package in index["packages"]:
        physical = package["coverage"]["physical"]
        assert physical == {
            "status": "planned_not_measured",
            "evidence_refs": [PHYSICAL_PLAN],
        }, package["circuit"]


def test_rv8gr_readme_coverage_table_matches_index():
    index = load_index()
    readme = README_PATH.read_text(encoding="utf-8")
    display = {"covered": "C", "not_covered": "-", "planned_not_measured": "P/NM"}

    assert "| Circuit | Structural | Vector/equation | Live model | Composed/system | Physical |" in readme
    assert "| Tested |" not in readme
    for package in index["packages"]:
        cells = [f"`{package['circuit']}`"]
        cells.extend(display[package["coverage"][layer]["status"]] for layer in index["coverage_layers"])
        assert "| " + " | ".join(cells) + " |" in readme, package["circuit"]


def test_each_circuit_readme_keeps_a_standalone_student_test_guide():
    circuit_root = ROOT / "Lib" / "Circuits"
    packages = [item["circuit"] for item in load_index()["packages"]]
    for package in packages:
        text = (circuit_root / package / "README.md").read_text(encoding="utf-8")
        lower = text.lower()
        assert "guide" in lower and "test" in lower, package
        for required in ("pass", "stop", "temporary wiring", "boundary"):
            assert required in lower, (package, required)
        if package != "RV8GR_WholeSystemChipLevelVirtual":
            assert "manual" in lower, package
            assert "integration" in lower, package


if __name__ == "__main__":
    test_rv8gr_coverage_index_has_allowed_layer_statuses_and_evidence()
    test_rv8gr_physical_coverage_remains_planned_and_not_measured()
    test_rv8gr_readme_coverage_table_matches_index()
    test_each_circuit_readme_keeps_a_standalone_student_test_guide()
    print("Components circuit coverage tests passed")
