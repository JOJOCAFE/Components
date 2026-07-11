"""Fail-loudly gate for the committed RV8GR circuit test campaign."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
GENERATOR_PATH = ROOT / "tools" / "circuit_campaign_report.py"
CAMPAIGN_JSON = ROOT / "examples" / "circuits" / "RV8GR_CIRCUIT_TEST_CAMPAIGN.json"
CAMPAIGN_MD = ROOT / "examples" / "circuits" / "RV8GR_CIRCUIT_TEST_CAMPAIGN.md"
RUNTIME_JSON = ROOT / "examples" / "circuits" / "RV8GR_CIRCUIT_RUNTIME_EVIDENCE.json"
PHYSICAL_PLAN = ROOT / "examples" / "circuits" / "physical_capture_plan.json"
EXPECTED_PACKAGE_COUNT = 22
ALLOWED_OUTCOMES = {
    "pass",
    "not_applicable",
    "not_directly_executed",
    "physical_measurement_required",
}
PASS_STATUSES = {"pass", "passed"}


def load_json(path: Path) -> dict:
    if not path.is_file():
        raise AssertionError(f"required campaign artifact is missing: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_generator():
    if not GENERATOR_PATH.is_file():
        raise AssertionError(
            "campaign generator is missing: tools/circuit_campaign_report.py"
        )
    spec = importlib.util.spec_from_file_location("circuit_campaign_report", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load campaign generator: {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def regenerate(output_json: Path, output_md: Path, runtime_json: Path) -> None:
    generator = load_generator()
    generate = getattr(generator, "generate_reports", None)
    if callable(generate):
        generate(output_json, output_md, runtime_json)
        return

    # Support the repository's established report-generator convention.
    patched = False
    for name in ("JSON_REPORT", "JSON_OUTPUT", "OUTPUT_JSON"):
        if hasattr(generator, name):
            setattr(generator, name, output_json)
            patched = True
    for name in ("MARKDOWN_REPORT", "MD_REPORT", "MARKDOWN_OUTPUT", "OUTPUT_MD", "REPORT"):
        if hasattr(generator, name):
            setattr(generator, name, output_md)
            patched = True
    main = getattr(generator, "main", None)
    if patched and callable(main):
        result = main()
        if result not in (None, 0):
            raise AssertionError(f"campaign generator main() returned {result!r}")
        return
    raise AssertionError(
        "unsupported campaign generator API: provide generate_reports(json_path, md_path) "
        "or main() with patchable JSON/Markdown output constants"
    )


def package_rows(campaign: dict) -> list[dict]:
    for key in ("packages", "campaign", "results"):
        rows = campaign.get(key)
        if isinstance(rows, list):
            return rows
    raise AssertionError("campaign JSON must contain a packages/results list")


def package_name(row: dict) -> str:
    for key in ("package", "circuit", "name"):
        value = row.get(key)
        if isinstance(value, str) and value:
            return value
    raise AssertionError(f"campaign row has no package identity: {row!r}")


def walk_records(value, path="campaign"):
    if isinstance(value, dict):
        yield path, value
        for key, child in value.items():
            yield from walk_records(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_records(child, f"{path}[{index}]")


class CircuitCampaignGateTests(unittest.TestCase):
    def test_committed_campaign_is_byte_for_byte_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            generated_json = Path(tmp) / CAMPAIGN_JSON.name
            generated_md = Path(tmp) / CAMPAIGN_MD.name
            generated_runtime = Path(tmp) / RUNTIME_JSON.name
            regenerate(generated_json, generated_md, generated_runtime)
            for generated, committed in (
                (generated_json, CAMPAIGN_JSON),
                (generated_md, CAMPAIGN_MD),
                (generated_runtime, RUNTIME_JSON),
            ):
                self.assertTrue(generated.is_file(), f"generator did not write {generated.name}")
                self.assertTrue(committed.is_file(), f"committed output is missing: {committed}")
                self.assertEqual(
                    generated.read_bytes(),
                    committed.read_bytes(),
                    f"{committed.relative_to(ROOT)} is stale; regenerate with "
                    "python3 tools/circuit_campaign_report.py",
                )

    def test_campaign_covers_exactly_all_22_circuit_packages(self):
        campaign = load_json(CAMPAIGN_JSON)
        names = [package_name(row) for row in package_rows(campaign)]
        actual = sorted(
            path.parent.name
            for path in (ROOT / "examples" / "circuits").glob("RV8GR_*/circuit.json")
        )
        self.assertEqual(len(actual), EXPECTED_PACKAGE_COUNT, "package inventory changed")
        self.assertEqual(len(names), EXPECTED_PACKAGE_COUNT, "campaign must have 22 rows")
        self.assertEqual(len(names), len(set(names)), "campaign contains duplicate packages")
        self.assertEqual(sorted(names), actual)

    def test_statuses_and_evidence_are_explicit_and_valid(self):
        campaign = load_json(CAMPAIGN_JSON)
        status_fields = (
            "logical_status",
            "direct_live_model_status",
            "composition_static_status",
            "modeled_timing_status",
            "physical_status",
        )
        for row in package_rows(campaign):
            package = package_name(row)
            self.assertTrue(row.get("stage"), package)
            self.assertTrue(row.get("proof_focus"), package)
            self.assertEqual(set(row.get("status_basis", {})), {
                "logical", "direct_live_model", "composition_static", "modeled_timing", "physical"
            }, package)
            for field in status_fields:
                self.assertIn(row.get(field), ALLOWED_OUTCOMES, f"{package}.{field}")
            evidence = row.get("evidence_refs")
            self.assertIsInstance(evidence, list, package)
            self.assertTrue(evidence, package)
            for reference in evidence:
                self.assertIsInstance(reference, str, package)
                path_text = reference.partition("::")[0]
                self.assertTrue((ROOT / path_text).is_file(), f"{package}: {reference}")
            self.assertIsInstance(row.get("limitations"), list, package)
            self.assertTrue(row["limitations"], package)

            self.assertIn(row["logical_status"], {"pass", "not_directly_executed"}, package)
            self.assertEqual(row["composition_static_status"], "pass", package)
            self.assertIn(row["direct_live_model_status"], {"pass", "not_directly_executed"}, package)
            self.assertIn(row["modeled_timing_status"], {
                "pass", "not_applicable", "not_directly_executed"
            }, package)
            self.assertIn(row["physical_status"], {
                "not_applicable", "physical_measurement_required"
            }, package)

    def test_unmeasured_physical_plan_cannot_produce_a_physical_pass(self):
        plan = load_json(PHYSICAL_PLAN)
        unmeasured = (
            plan.get("status") == "prepared_no_board_measurements"
            or plan.get("blank_measurement_values", {}).get("result_pass_fail")
            == "not_measured"
        )
        self.assertTrue(unmeasured, "test requires the physical plan to remain unmeasured")
        campaign = load_json(CAMPAIGN_JSON)
        for path, record in walk_records(campaign):
            label = " ".join(str(record.get(key, "")) for key in ("layer", "kind", "type", "name"))
            if "physical" in (path + " " + label).lower() and "status" in record:
                self.assertNotIn(record["status"], PASS_STATUSES, f"false physical pass at {path}")

    def test_direct_and_timing_statuses_are_execution_derived_and_fail_closed(self):
        campaign = load_json(CAMPAIGN_JSON)
        runtime = load_json(RUNTIME_JSON)
        self.assertTrue(runtime["generation_policy"]["execution_derived"])
        self.assertTrue(runtime["generation_policy"]["logical_tests_executed"])
        self.assertTrue(runtime["generation_policy"]["fail_closed"])
        self.assertFalse(
            runtime["generation_policy"]["modeled_timing_is_physical_evidence"]
        )
        self.assertEqual(runtime["package_count"], EXPECTED_PACKAGE_COUNT)

        for row in package_rows(campaign):
            package = package_name(row)
            evidence = runtime["packages"][package]
            self.assertEqual(row["runtime_evidence"], evidence, package)

            logical = evidence["logical"]
            if row["logical_status"] == "pass":
                self.assertEqual(logical["status"], "passed", package)
                self.assertTrue(logical["test_ref"].startswith("python/tests/"), package)
                self.assertIn("::test_", logical["test_ref"], package)
                self.assertEqual(logical["runner"], "direct_python_test_function", package)
                self.assertFalse(logical["blocks"], package)
            else:
                self.assertEqual(logical["status"], "blocked", package)
                self.assertTrue(logical["blocks"], package)

            functional = evidence["functional"]
            if row["direct_live_model_status"] == "pass":
                self.assertEqual(functional["status"], "promoted", package)
                self.assertFalse(functional["blocks"], package)
                self.assertTrue(functional["observations"], package)
            else:
                self.assertEqual(functional["status"], "blocked", package)
                self.assertTrue(functional["blocks"], package)

            timing = evidence["timing"]
            if row["modeled_timing_status"] == "pass":
                self.assertEqual(timing["status"], "passed", package)
                self.assertFalse(timing["blocks"], package)
                self.assertEqual(timing["runner"], "CircuitTimingBinding", package)
                self.assertEqual(len(timing["checks"]), 9, package)
            elif row["modeled_timing_status"] == "not_applicable":
                self.assertEqual(timing["status"], "not_applicable", package)
                self.assertFalse(timing["blocks"], package)
            else:
                self.assertEqual(timing["status"], "blocked", package)
                self.assertTrue(timing["blocks"], package)
            self.assertTrue(timing["modeled_only"], package)
            self.assertEqual(timing["physical_status"], "not_measured", package)

    def test_ring_counter_timing_pass_requires_enforced_thresholds(self):
        runtime = load_json(RUNTIME_JSON)
        timing = runtime["packages"]["RV8GR_RingCounter"]["timing"]
        self.assertEqual(timing["status"], "passed")
        self.assertFalse(timing["blocks"])
        self.assertEqual(len(timing["checks"]), 9)
        for constraint in ("setup", "hold", "minimum_pulse_width"):
            rows = [row for row in timing["checks"] if row["constraint"] == constraint]
            self.assertEqual([row["offset_ps"] for row in rows], [-1, 0, 1])
            self.assertEqual([row["violation"] for row in rows], [True, False, False])

    def test_logical_status_ignores_index_coverage_label_and_executes_named_test(self):
        generator = load_generator()
        record = generator.logical_record(
            "RV8GR_RingCounter",
            [
                "examples/circuits/RV8GR_RingCounter/tests/ring_counter.json",
                "python/tests/test_lib_circuits.py::test_rv8gr_ring_counter_sequence_and_reset",
            ],
        )
        self.assertEqual(record["status"], "passed")
        blocked = generator.logical_record(
            "RV8GR_RingCounter",
            ["examples/circuits/RV8GR_RingCounter/tests/ring_counter.json"],
        )
        self.assertEqual(blocked["status"], "blocked")

    def test_model_timing_never_implies_hardware_timing(self):
        campaign = load_json(CAMPAIGN_JSON)
        for path, record in walk_records(campaign):
            context = (path + " " + " ".join(str(value) for value in record.values())).lower()
            if "model" not in context or "timing" not in context:
                continue
            status = record.get("hardware_status", record.get("physical_status"))
            if status is not None:
                self.assertNotIn(status, PASS_STATUSES, f"model promoted to hardware at {path}")
            claim = str(record.get("claim", record.get("claim_boundary", ""))).lower()
            self.assertFalse(
                "hardware timing pass" in claim or "physical timing pass" in claim,
                f"model timing overclaim at {path}",
            )


if __name__ == "__main__":
    unittest.main()
