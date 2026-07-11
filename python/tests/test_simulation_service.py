"""Focused tests for the internal simulation service boundary."""

from __future__ import annotations

import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from time import sleep

from chiplib import SimulationService
from chiplib.services import CircuitCommandService, CircuitSessionRegistry
from chiplib.design import Design


ROOT = Path(__file__).resolve().parents[2]
CIRCUIT = ROOT / "Lib" / "Circuits" / "RV8GR_RingCounter" / "circuit.json"


def load_example(name: str = "nand") -> Design:
    return Design.from_dict(json.loads((ROOT / "Examples" / f"{name}.json").read_text(encoding="utf-8")))


def assert_service_response(response: dict, command: str) -> None:
    assert response["contract"] == "components.service.v1"
    assert response["command"] == command
    assert "ok" in response
    assert "warnings" in response
    assert response["metadata"]["engine"] == "python"
    assert "elapsed_ms" in response["metadata"]


def test_simulation_service_validate_wraps_design_validation():
    service = SimulationService()
    response = service.validate(load_example())

    assert_service_response(response, "validate")
    assert response["ok"] is True
    assert response["result"]["valid"] is True
    assert response["result"]["design_id"] == "nand"
    assert response["result"]["summary"]["chips"] == 1
    assert response["result"]["errors"] == []
    assert response["warnings"] == []


def test_simulation_service_validate_reports_structured_errors():
    service = SimulationService()
    design = Design.from_dict({"name": "bad", "buses": {"BROKEN": {"width": 0}}})
    response = service.validate(design)

    assert_service_response(response, "validate")
    assert response["ok"] is False
    assert response["result"]["valid"] is False
    assert response["errors"] == [{"type": "bus_width_invalid", "bus": "BROKEN", "width": 0}]
    assert response["error"]["code"] == "validation.failed"


def test_simulation_service_snapshot_returns_existing_design_payload():
    service = SimulationService()
    design = load_example()
    design.to_board()
    response = service.snapshot(design)

    assert_service_response(response, "snapshot")
    assert response["ok"] is True
    assert response["result"]["design"]["name"] == "nand"
    assert response["result"]["board"]["chips"][0]["ref"] == "U1"
    assert response["result"]["validate"]["ok"] is True


def test_simulation_service_run_wraps_existing_run_payload_and_warnings():
    service = SimulationService()
    response = service.run(load_example(), ["settle", "unknown command"])

    assert_service_response(response, "run")
    assert response["ok"] is True
    assert response["result"]["ok"] is True
    assert response["result"]["log"][0]["action"] == "settle"
    assert response["warnings"] == [{"step": "unknown command", "warning": "step not implemented"}]


def test_simulation_service_run_reports_failed_expectations_as_errors():
    service = SimulationService()
    design = Design.from_dict({
        "name": "failed-expect",
        "chips": {"U1": {"part": "74HC00"}},
        "aliases": {"A": "U1:1", "B": "U1:2", "Y": "U1:3"},
        "connect": ["VCC -> U1:14", "GND -> U1:7"],
        "inputs": {"both_high": ["A = 1", "B = 1"]},
        "expect": {"wrong": ["Y = 1"]},
        "steps": ["apply both_high", "expect wrong"],
    })
    response = service.run(design)

    assert_service_response(response, "run")
    assert response["ok"] is False
    assert response["errors"][0]["type"] == "expectation_failed"
    assert response["error"]["code"] == "simulation.failed"


def test_simulation_service_probe_samples_named_probe_set_after_steps():
    service = SimulationService()
    response = service.probe(load_example(), set_name="logic", steps=["apply power_on", "settle"])

    assert_service_response(response, "probe")
    assert response["ok"] is True
    assert response["result"]["set"] == "logic"
    assert response["result"]["samples"] == [
        {
            "name": "nand_y",
            "target": "U1.1Y",
            "target_kind": "pin",
            "value": 0,
            "history": [
                {"time_ns": 12, "value": 0},
                {"time_ns": 12, "value": 0},
            ],
        }
    ]


def test_simulation_service_probe_reports_missing_set():
    service = SimulationService()
    response = service.probe(load_example(), set_name="missing")

    assert_service_response(response, "probe")
    assert response["ok"] is False
    assert response["result"]["available_sets"] == ["default", "logic"]
    assert response["errors"] == [{"type": "probe_set_missing", "set": "missing"}]


def test_simulation_service_frontend_snapshot_contract():
    service = SimulationService()
    response = service.frontend_snapshot(load_example())

    assert_service_response(response, "frontend-snapshot")
    assert response["ok"] is True
    result = response["result"]
    assert result["format"] == "components.frontend.snapshot"
    assert result["version"] == 1
    assert result["design"]["name"] == "nand"
    assert result["chips"][0]["ref"] == "U1"
    assert result["probes"]["sets"][1]["name"] == "logic"
    assert result["validation"]["ok"] is True
    assert result["errors"] == []


def test_circuit_command_service_keeps_state_and_fails_loudly():
    service = CircuitCommandService()
    validated = service.validate(CIRCUIT)
    assert validated["contract"] == "components.service.v1"
    assert validated["result"]["contract"] == "components.circuit_runner.student.v1"
    assert validated["ok"] is True
    assert service.step("clock CLK")["ok"] is True
    assert service.probe("T0")["result"]["samples"][0]["name"] == "T0"
    failed = service.step("invent magic")
    assert failed["ok"] is False
    assert failed["error"]["code"] == "runner.unsupported_step"


def test_circuit_session_registry_serializes_each_session():
    registry = CircuitSessionRegistry()
    assert registry.execute("same-session", lambda service: service.load(CIRCUIT))["ok"] is True
    active = 0
    peak = 0

    def guarded(_service):
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        sleep(0.01)
        active -= 1
        return {"ok": True}

    def overlap(_index: int):
        return registry.execute("same-session", guarded)

    with ThreadPoolExecutor(max_workers=4) as pool:
        responses = list(pool.map(overlap, range(4)))
    assert all(response["ok"] for response in responses)
    assert peak == 1


def run_all():
    test_simulation_service_validate_wraps_design_validation()
    test_simulation_service_validate_reports_structured_errors()
    test_simulation_service_snapshot_returns_existing_design_payload()
    test_simulation_service_run_wraps_existing_run_payload_and_warnings()
    test_simulation_service_run_reports_failed_expectations_as_errors()
    test_simulation_service_probe_samples_named_probe_set_after_steps()
    test_simulation_service_probe_reports_missing_set()
    test_simulation_service_frontend_snapshot_contract()
    test_circuit_command_service_keeps_state_and_fails_loudly()
    test_circuit_session_registry_serializes_each_session()


if __name__ == "__main__":
    run_all()
    print("Components simulation service tests passed")
