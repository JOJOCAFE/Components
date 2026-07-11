"""Student-facing contract checks for functional circuit service adapters."""

from pathlib import Path

from chiplib.services import CircuitCommandService


ROOT = Path(__file__).resolve().parents[2]
RING = ROOT / "examples" / "circuits" / "RV8GR_RingCounter" / "circuit.json"
UNSUPPORTED = ROOT / "examples" / "circuits" / "RV8GR_WholeSystemChipLevelVirtual" / "circuit.json"


def test_pass_result_preserves_contract_and_evidence_boundary():
    response = CircuitCommandService().run(RING, operations=["clock CLK"])
    assert response["contract"] == "components.service.v1"
    result = response["result"]
    assert response["ok"] is result["ok"] is True
    assert result["contract"] == "components.circuit_runner.student.v1"
    assert result["status"] == "pass"
    assert "physical timing" in result["evidence_boundary"]["does_not_prove"]


def test_unsupported_package_is_blocked_not_passed():
    response = CircuitCommandService().validate(UNSUPPORTED)
    assert response["ok"] is False
    assert response["result"]["status"] == "blocked"
    assert response["result"]["violations"]


def test_unknown_probe_retains_runner_issue_path():
    response = CircuitCommandService().probe("NOT_A_PROBE", RING)
    assert response["ok"] is False
    assert response["error"]["code"] == "unknown_probe"
    assert response["error"]["details"]["issues"][0]["path"] == "NOT_A_PROBE"


def test_timed_run_exposes_modeled_provenance_and_blocks_unsupported_paths():
    service = CircuitCommandService()
    passed = service.timed_run(RING, operations=["reset", "release /CLR", "clock CLK"])
    result = passed["result"]
    assert passed["ok"] is result["ok"] is True
    assert result["command"] == "timed-run"
    assert result["timing"]["modeled_only"] is True
    event = result["executed_steps"][-1]["events"][0]
    assert event["timing_source"]
    assert event["modeled_only"] is True

    blocked = service.timed_run(RING, operations=["set /CLR 0"])
    assert blocked["ok"] is False
    assert blocked["result"]["status"] == "blocked"
    assert blocked["error"]["code"] == "timing.unsupported"


def test_violation_explanation_and_evidence_preserve_the_original_diagnostic():
    service = CircuitCommandService()
    blocked = service.timed_run(RING, operations=["set /CLR 0"])
    explained = service.explain_violations(blocked)
    assert explained["result"]["status"] == "needs_attention"
    assert explained["result"]["explanations"][0]["code"] == "timing.unsupported"
    exported = service.export_evidence(blocked, include_traces=True)
    assert exported["result"]["evidence"]["violations"][0]["code"] == "timing.unsupported"
    assert exported["result"]["evidence"]["evidence"]["source_digest_sha256"]


def run_all():
    test_pass_result_preserves_contract_and_evidence_boundary()
    test_unsupported_package_is_blocked_not_passed()
    test_unknown_probe_retains_runner_issue_path()
    test_timed_run_exposes_modeled_provenance_and_blocks_unsupported_paths()
    test_violation_explanation_and_evidence_preserve_the_original_diagnostic()


if __name__ == "__main__":
    run_all()
    print("Circuit runner student contract tests passed")
