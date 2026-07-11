#!/usr/bin/env python3
"""Generate the deterministic RV8GR 22-circuit evidence campaign report."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PYTHON_ROOT = ROOT / "python"
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from chiplib.circuit_proofs import PackagePromotion, audit_all_packages
from chiplib.circuit_timing import CircuitTimingBinding, CircuitTimingError
CIRCUITS = ROOT / "examples" / "circuits"
INDEX_PATH = CIRCUITS / "RV8GR_COVERAGE_INDEX.json"
TIMING_PATH = CIRCUITS / "timing_margins.json"
PHYSICAL_PATH = CIRCUITS / "physical_capture_plan.json"
JSON_OUTPUT = CIRCUITS / "RV8GR_CIRCUIT_TEST_CAMPAIGN.json"
MD_OUTPUT = CIRCUITS / "RV8GR_CIRCUIT_TEST_CAMPAIGN.md"
RUNTIME_OUTPUT = CIRCUITS / "RV8GR_CIRCUIT_RUNTIME_EVIDENCE.json"

PASS = "pass"
NOT_APPLICABLE = "not_applicable"
NOT_DIRECT = "not_directly_executed"
PHYSICAL_REQUIRED = "physical_measurement_required"
EXPECTED_PACKAGE_COUNT = 22


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def require_file(ref: str) -> None:
    file_ref = ref.split("::", 1)[0]
    path = ROOT / file_ref
    if not path.is_file():
        raise ValueError(f"evidence reference does not exist: {ref}")


def status(outcome: str, basis: str) -> dict[str, str]:
    return {"outcome": outcome, "basis": basis}


def normalized_issue_path(path: str) -> str:
    root = str(ROOT)
    return path[len(root) + 1:] if path.startswith(root + "/") else path


def portable(value: Any) -> Any:
    """Remove workspace-specific prefixes from generated runtime evidence."""

    if isinstance(value, str):
        return normalized_issue_path(value)
    if isinstance(value, dict):
        return {key: portable(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [portable(child) for child in value]
    return value


def promotion_record(result: PackagePromotion) -> dict[str, Any]:
    return {
        "status": result.status,
        "circuit_id": result.circuit_id,
        "circuit_path": relative(result.circuit_path),
        "proof_paths": [relative(path) for path in result.proof_paths],
        "observations": result.observations,
        "blocks": [
            {
                "code": block.code,
                "path": normalized_issue_path(block.path),
                "message": block.message,
            }
            for block in result.blocks
        ],
    }


def logical_record(package: str, evidence_refs: list[str]) -> dict[str, Any]:
    """Execute the one named Python logical proof; never trust index status alone."""

    named = [ref for ref in evidence_refs if "::" in ref]
    if len(named) != 1:
        return {
            "status": "blocked",
            "blocks": [{
                "code": "logical_test_reference_invalid",
                "path": relative(INDEX_PATH),
                "message": f"expected one named logical test for {package}; found {len(named)}",
            }],
        }
    reference = named[0]
    file_ref, function_name = reference.split("::", 1)
    test_path = ROOT / file_ref
    if not test_path.is_file() or not function_name.startswith("test_"):
        return {
            "status": "blocked",
            "test_ref": reference,
            "blocks": [{
                "code": "logical_test_reference_invalid",
                "path": reference,
                "message": "named logical evidence must reference an existing test_* function",
            }],
        }
    try:
        module_name = "_components_campaign_" + test_path.stem
        spec = importlib.util.spec_from_file_location(module_name, test_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load {file_ref}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        proof = getattr(module, function_name, None)
        if not callable(proof):
            raise AttributeError(f"named test function does not exist: {function_name}")
        result = proof()
        if result is not None:
            raise AssertionError(f"named logical test returned unexpected value {result!r}")
    except Exception as exc:
        return {
            "status": "blocked",
            "test_ref": reference,
            "blocks": [{
                "code": "logical_test_execution_failed",
                "path": reference,
                "message": f"{type(exc).__name__}: {exc}",
            }],
        }
    return {
        "status": "passed",
        "test_ref": reference,
        "runner": "direct_python_test_function",
        "blocks": [],
    }


def timing_record(package: str, promotion: PackagePromotion) -> dict[str, Any]:
    """Execute package timing evidence, or return a fail-closed blocker."""

    if package == "RV8GR_VirtualTestHelpers":
        return {
            "status": "not_applicable",
            "modeled_only": True,
            "physical_status": "not_measured",
            "blocks": [],
        }
    if not promotion.promoted:
        return {
            "status": "blocked",
            "modeled_only": True,
            "physical_status": "not_measured",
            "blocks": [{
                "code": "functional_promotion_required",
                "path": relative(promotion.circuit_path),
                "message": "package timing cannot pass before its live functional proof is promoted",
            }],
        }
    if package == "RV8GR_RingCounter":
        checks = []
        probe = CircuitTimingBinding.load(promotion.circuit_path)
        probe.runner.reset({"/CLR": 0})
        probe.runner.set_input("/CLR", 1)
        constraints = probe.constraint_provenance("CLK")
        cases = (
            ("setup", "timing.setup_violation", "setup_ps"),
            ("minimum_pulse_width", "timing.pulse_width_violation", "high_ps"),
            ("hold", "timing.hold_violation", "constrained_change_ps"),
        )
        for name, code, argument in cases:
            required = constraints[name]["delay_ps"]
            if not isinstance(required, int) or required <= 0:
                raise ValueError(f"{name} has no positive package timing threshold")
            for offset, should_violate in ((-1, True), (0, False), (1, False)):
                binding = CircuitTimingBinding.load(promotion.circuit_path)
                binding.runner.reset({"/CLR": 0})
                binding.runner.set_input("/CLR", 1)
                kwargs = {argument: required + offset}
                if name == "hold":
                    kwargs["high_ps"] = required + 1
                events = binding.pulse_clock(**kwargs)
                violated = any(item.code == code for item in binding.timed.diagnostics)
                if violated != should_violate or not events:
                    raise ValueError(
                        f"{name} threshold check failed at offset {offset}: "
                        f"expected violation={should_violate}, observed={violated}"
                    )
                checks.append({
                    "constraint": name,
                    "required_ps": required,
                    "offset_ps": offset,
                    "violation": violated,
                })
        return {
            "status": "passed",
            "modeled_only": True,
            "physical_status": "not_measured",
            "runner": "CircuitTimingBinding",
            "checks": checks,
            "blocks": [],
        }
    try:
        binding = CircuitTimingBinding.load(promotion.circuit_path)
        raise ValueError("no package-specific threshold-enforcing timing execution adapter")
    except Exception as exc:
        if isinstance(exc, CircuitTimingError):
            block = exc.issue.to_dict()
        else:
            block = {
                "code": "timing_execution_failed",
                "path": relative(promotion.circuit_path),
                "message": str(exc) or "no package-specific timing execution adapter",
            }
        return {
            "status": "blocked",
            "modeled_only": True,
            "physical_status": "not_measured",
            "blocks": [block],
        }


def build_runtime_evidence() -> dict[str, Any]:
    index = load_json(INDEX_PATH)
    logical_refs = {
        row["circuit"]: row["coverage"]["vector_equation"]["evidence_refs"]
        for row in index["packages"]
    }
    promotions = audit_all_packages()
    packages = {}
    for result in promotions:
        packages[result.package] = {
            "logical": portable(logical_record(result.package, logical_refs[result.package])),
            "functional": portable(promotion_record(result)),
            "timing": portable(timing_record(result.package, result)),
        }
    return {
        "schema": "components.lib.rv8gr.circuit_runtime_evidence",
        "version": 1,
        "generation_policy": {
            "execution_derived": True,
            "logical_tests_executed": True,
            "fail_closed": True,
            "modeled_timing_is_physical_evidence": False,
        },
        "package_count": len(packages),
        "packages": packages,
    }


def build_campaign(runtime: dict[str, Any] | None = None) -> dict[str, Any]:
    index = load_json(INDEX_PATH)
    timing = load_json(TIMING_PATH)
    physical = load_json(PHYSICAL_PATH)
    packages = index["packages"]
    runtime = runtime or build_runtime_evidence()
    runtime_packages = runtime["packages"]
    if len(packages) != EXPECTED_PACKAGE_COUNT:
        raise ValueError(f"expected exactly {EXPECTED_PACKAGE_COUNT} indexed packages")
    if set(runtime_packages) != {row["circuit"] for row in packages}:
        raise ValueError("runtime evidence and coverage index package sets differ")

    timing_rows = {row["circuit"]: row for row in timing["timing_coverage_matrix"]}
    if set(timing_rows) != {row["circuit"] for row in packages}:
        raise ValueError("coverage index and timing coverage matrix package sets differ")

    physical_by_circuit: dict[str, dict[str, Any]] = {}
    for stage in physical["stages"]:
        for circuit in stage["circuits"]:
            if circuit in physical_by_circuit:
                raise ValueError(f"circuit appears in multiple physical stages: {circuit}")
            physical_by_circuit[circuit] = stage

    rows = []
    for indexed in packages:
        circuit = indexed["circuit"]
        package_dir = CIRCUITS / circuit
        circuit_path = package_dir / "circuit.json"
        circuit_data = load_json(circuit_path)
        declared_tests = circuit_data.get("verification", {}).get("tests", [])
        proof_paths = sorted((package_dir / "tests").glob("*.json"))
        proof_refs = [relative(path) for path in proof_paths]
        if not proof_refs:
            raise ValueError(f"{circuit} has no proof JSON")
        if declared_tests:
            declared_refs = {relative(package_dir / item) for item in declared_tests}
            if declared_refs != set(proof_refs):
                raise ValueError(f"declared and present proof JSON differ: {circuit}")
        for ref in proof_refs:
            proof = load_json(ROOT / ref)
            if not str(proof.get("schema", "")).startswith("components.lib.circuit.test"):
                raise ValueError(f"unexpected proof schema: {ref}")

        coverage = indexed["coverage"]

        live_coverage = coverage["live_component_model"]
        runtime_row = runtime_packages[circuit]
        logical_evidence = runtime_row["logical"]
        functional_evidence = runtime_row["functional"]
        timing_evidence = runtime_row["timing"]
        if logical_evidence["status"] == "passed":
            logical = status(PASS, "named_logical_test_executed")
        else:
            logical = status(NOT_DIRECT, "named_logical_test_blocked")
        if functional_evidence["status"] == "promoted":
            live = status(PASS, "runtime_package_proof_passed")
        else:
            live = status(NOT_DIRECT, "runtime_package_proof_blocked")

        composed = coverage["composed_system"]
        structural = coverage["structural"]
        if composed["status"] == "covered":
            composition = status(PASS, "executable_composed_system_test")
            composition_refs = composed["evidence_refs"]
        elif structural["status"] == "covered":
            composition = status(PASS, "executable_static_package_check")
            composition_refs = structural["evidence_refs"]
        else:
            composition = status(NOT_DIRECT, "no_composed_or_static_executable_check")
            composition_refs = []

        timing_row = timing_rows[circuit]
        timing_class = timing_row["coverage"]
        if timing_evidence["status"] == "passed":
            modeled_timing = status(PASS, "runtime_package_timing_passed")
        elif timing_evidence["status"] == "not_applicable":
            modeled_timing = status(NOT_APPLICABLE, "runtime_timing_not_applicable")
        else:
            modeled_timing = status(NOT_DIRECT, "runtime_package_timing_blocked")

        if timing_row["physical_status"] == "not_applicable":
            physical_status = status(NOT_APPLICABLE, timing_row["physical_status"])
        else:
            physical_status = status(PHYSICAL_REQUIRED, timing_row["physical_status"])

        evidence_refs = list(dict.fromkeys(
            [relative(INDEX_PATH), relative(circuit_path)]
            + proof_refs
            + coverage["vector_equation"]["evidence_refs"]
            + live_coverage["evidence_refs"]
            + composition_refs
            + [relative(TIMING_PATH), relative(PHYSICAL_PATH), relative(RUNTIME_OUTPUT)]
        ))
        stage = physical_by_circuit.get(circuit)
        limitations = [timing_row["claim_boundary"]]
        if logical["outcome"] == NOT_DIRECT:
            limitations.append("Logical proof execution is blocked; see runtime_evidence.logical.blocks.")
        if live["outcome"] == NOT_DIRECT:
            limitations.append("Direct live execution is blocked; see runtime_evidence.functional.blocks.")
        if modeled_timing["outcome"] == NOT_DIRECT:
            limitations.append("Package-level modeled timing is blocked; see runtime_evidence.timing.blocks.")
        if composed["status"] != "covered":
            limitations.append("Composition/static pass is package-shape validation, not composed-system execution.")
        if stage:
            limitations.append(
                f"Physical stage {stage['id']} ({stage['name']}) remains an unmeasured capture contract."
            )
        elif physical_status["outcome"] == PHYSICAL_REQUIRED:
            limitations.append("No package-specific physical stage exists; shared board captures still gate physical claims.")
        else:
            limitations.append("Virtual test infrastructure has no independent physical package to measure.")

        for ref in evidence_refs:
            require_file(ref)
        rows.append({
            "package": circuit,
            "stage": indexed["stage"],
            "proof_focus": indexed["proof_focus"],
            "logical_status": logical["outcome"],
            "direct_live_model_status": live["outcome"],
            "composition_static_status": composition["outcome"],
            "modeled_timing_status": modeled_timing["outcome"],
            "physical_status": physical_status["outcome"],
            "status_basis": {
                "logical": logical["basis"],
                "direct_live_model": live["basis"],
                "composition_static": composition["basis"],
                "modeled_timing": modeled_timing["basis"],
                "physical": physical_status["basis"],
            },
            "evidence_refs": evidence_refs,
            "runtime_evidence": runtime_row,
            "limitations": limitations,
        })

    return {
        "schema": "components.lib.rv8gr.circuit_test_campaign",
        "version": 1,
        "package_count": len(rows),
        "generation_policy": {
            "deterministic": True,
            "package_runtime_executed": True,
            "source_artifacts": [
                relative(INDEX_PATH),
                "examples/circuits/RV8GR_*/circuit.json",
                "examples/circuits/RV8GR_*/tests/*.json",
                relative(TIMING_PATH),
                relative(PHYSICAL_PATH),
                "python/tests/test_lib_circuits.py",
            ],
            "outcomes": [PASS, NOT_APPLICABLE, NOT_DIRECT, PHYSICAL_REQUIRED],
            "claim_boundary": "Direct and modeled-timing passes require fresh public runtime execution; modeled timing never proves physical behavior.",
        },
        "runtime_execution": {
            "status": "completed",
            "manifest": relative(RUNTIME_OUTPUT),
            "claim": "Package proof and timing adapters were executed in-process; structured blockers fail closed.",
        },
        "packages": rows,
    }


def render_json(campaign: dict[str, Any]) -> str:
    return json.dumps(campaign, indent=2, ensure_ascii=True) + "\n"


def render_markdown(campaign: dict[str, Any]) -> str:
    lines = [
        "# RV8GR 22-Circuit Logical and Modeled-Timing Campaign",
        "",
        "Generated deterministically by `tools/circuit_campaign_report.py`. Logical, direct live-model, and modeled-timing passes require fresh execution of named evidence. Blocked adapters remain visible and modeled timing never implies physical signoff.",
        "",
        "Allowed outcomes: `pass`, `not_applicable`, `not_directly_executed`, and `physical_measurement_required`.",
        "",
        "| Package | Logical | Direct live model | Composition/static | Modeled timing | Physical |",
        "|---|---|---|---|---|---|",
    ]
    for row in campaign["packages"]:
        lines.append(
            "| {package} | {logical} | {live} | {composition} | {timing} | {physical} |".format(
                package=row["package"],
                logical=row["logical_status"],
                live=row["direct_live_model_status"],
                composition=row["composition_static_status"],
                timing=row["modeled_timing_status"],
                physical=row["physical_status"],
            )
        )
    lines.extend(["", "## Package Evidence", ""])
    for row in campaign["packages"]:
        lines.extend([
            f"### {row['package']}",
            "",
            f"- Stage: `{row['stage']}`",
            f"- Focus: {row['proof_focus']}",
            f"- Logical: `{row['logical_status']}` ({row['status_basis']['logical']})",
            f"- Direct live model: `{row['direct_live_model_status']}` ({row['status_basis']['direct_live_model']})",
            f"- Composition/static: `{row['composition_static_status']}` ({row['status_basis']['composition_static']})",
            f"- Modeled timing: `{row['modeled_timing_status']}` ({row['status_basis']['modeled_timing']})",
            f"- Physical: `{row['physical_status']}` ({row['status_basis']['physical']})",
            f"- Evidence: {', '.join(f'`{ref}`' for ref in row['evidence_refs'])}",
            f"- Logical blockers: `{json.dumps(row['runtime_evidence']['logical']['blocks'], ensure_ascii=True)}`",
            f"- Functional blockers: `{json.dumps(row['runtime_evidence']['functional']['blocks'], ensure_ascii=True)}`",
            f"- Timing blockers: `{json.dumps(row['runtime_evidence']['timing']['blocks'], ensure_ascii=True)}`",
            f"- Limitations: {' '.join(row['limitations'])}",
            "",
        ])
    return "\n".join(lines)


def write_or_check(path: Path, content: str, check: bool) -> None:
    if check:
        if not path.is_file() or path.read_text(encoding="utf-8") != content:
            raise SystemExit(f"generated output is stale: {relative(path)}")
        return
    path.write_text(content, encoding="utf-8")


def generate_reports(
    output_json: Path = JSON_OUTPUT,
    output_md: Path = MD_OUTPUT,
    runtime_output: Path = RUNTIME_OUTPUT,
) -> None:
    """Write both report views; exposed for the repository determinism gate."""
    runtime = build_runtime_evidence()
    runtime_output.write_text(render_json(runtime), encoding="utf-8")
    campaign = build_campaign(runtime)
    output_json.write_text(render_json(campaign), encoding="utf-8")
    output_md.write_text(render_markdown(campaign), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if generated files differ")
    args = parser.parse_args()
    runtime = build_runtime_evidence()
    write_or_check(RUNTIME_OUTPUT, render_json(runtime), args.check)
    campaign = build_campaign(runtime)
    write_or_check(JSON_OUTPUT, render_json(campaign), args.check)
    write_or_check(MD_OUTPUT, render_markdown(campaign), args.check)
    action = "verified" if args.check else "generated"
    print(f"{action} {campaign['package_count']} circuit campaign rows")


if __name__ == "__main__":
    main()
