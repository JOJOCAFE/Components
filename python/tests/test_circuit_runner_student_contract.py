"""Student-facing contract checks for functional circuit service adapters."""

from pathlib import Path

from chiplib.services import CircuitCommandService


ROOT = Path(__file__).resolve().parents[2]
RING = ROOT / "Lib" / "Circuits" / "RV8GR_RingCounter" / "circuit.json"
UNSUPPORTED = ROOT / "Lib" / "Circuits" / "RV8GR_WholeSystemChipLevelVirtual" / "circuit.json"


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


def run_all():
    test_pass_result_preserves_contract_and_evidence_boundary()
    test_unsupported_package_is_blocked_not_passed()
    test_unknown_probe_retains_runner_issue_path()


if __name__ == "__main__":
    run_all()
    print("Circuit runner student contract tests passed")
