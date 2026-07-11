"""Tests for frontend editing service and local JSON API adapter."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from chiplib.api import handle_request
from chiplib.services import CircuitSessionRegistry, FrontendDesignService


CIRCUIT = Path(__file__).resolve().parents[2] / "examples" / "circuits" / "RV8GR_RingCounter" / "circuit.json"


def test_frontend_design_service_edits_and_exports_design():
    service = FrontendDesignService()
    service.create_design("api-small")
    service.create_chip("U1", "74HC00", label="NAND")
    service.add_bus("DATA", 2)
    service.connect("DATA:0 -> U1:1")
    service.connect("DATA:1 -> U1:2")
    service.connect("VCC -> U1:14")
    service.connect("GND -> U1:7")
    service.set_inputs("power_on", {"DATA:0": 1, "DATA:1": 1})

    run = service.run(["apply power_on", "settle"])
    assert run["ok"] is True
    snapshot = service.frontend_snapshot()["result"]
    assert snapshot["format"] == "components.frontend.snapshot"
    assert snapshot["chips"][0]["ref"] == "U1"
    assert snapshot["buses"][0]["name"] == "DATA"

    exported = service.export_json()["result"]
    assert exported["chips"]["U1"]["part"] == "74HC00"
    assert exported["inputs"]["power_on"] == ["DATA:0 = 1", "DATA:1 = 1"]

    block_ui = service.export_block_ui()["result"]
    assert block_ui["format"] == "components.block_ui"
    assert {block["id"] for block in block_ui["blocks"]} >= {"U1", "DATA", "VCC", "GND"}

    service.disconnect("DATA:1 -> U1:2")
    assert "DATA:1 -> U1:2" not in service.export_json()["result"]["connect"]
    service.delete_chip("U1")
    assert service.export_json()["result"]["chips"] == {}


def test_json_api_adapter_dispatches_stateful_frontend_commands():
    service = FrontendDesignService()

    created = handle_request({"command": "create-design", "options": {"name": "api-session"}}, service)
    assert created["ok"] is True

    chip = handle_request({"command": "create-chip", "options": {"ref": "U1", "part": "74HC04"}}, service)
    assert chip["ok"] is True

    connected = handle_request({"command": "connect", "options": {"rule": "A -> U1:1"}}, service)
    assert connected["ok"] is True

    exported = handle_request({"command": "export-json"}, service)
    assert exported["result"]["name"] == "api-session"
    assert exported["result"]["chips"]["U1"]["part"] == "74HC04"
    assert exported["result"]["connect"] == ["A -> U1:1"]

    block_ui = handle_request({"command": "export-block-ui"}, service)
    assert block_ui["ok"] is True
    assert block_ui["result"]["format"] == "components.block_ui"

    imported = handle_request({"command": "import-block-ui", "input": {"block_ui": block_ui["result"]}}, service)
    assert imported["ok"] is True
    imported_json = handle_request({"command": "export-json"}, service)
    assert imported_json["result"]["chips"]["U1"]["part"] == "74HC04"
    assert imported_json["result"]["connect"] == ["A -> U1:1"]

    unknown = handle_request({"command": "missing-command"}, service)
    assert unknown["ok"] is False
    assert unknown["error"]["code"] == "api.unknown_command"


def test_json_api_adapter_explain_result_wraps_structured_summary():
    service = FrontendDesignService()
    response = {
        "contract": "components.service.v1",
        "command": "run",
        "ok": False,
        "result": {
            "ok": False,
            "expectations": {
                "passed": [],
                "failed": [
                    {
                        "name": "nand_both_high",
                        "errors": [{"type": "expectation_failed", "detail": "Y was 1"}],
                    }
                ],
            },
        },
        "warnings": [],
    }

    explained = handle_request({"command": "explain-result", "input": {"response": response}}, service)
    assert explained["ok"] is True
    result = explained["result"]
    assert result["format"] == "components.explain_result"
    assert result["source_command"] == "run"
    assert result["ok"] is False
    assert result["issues"][0]["code"] == "nand_both_high"
    assert result["issues"][0]["field_refs"]["name"] == "nand_both_high"
    assert result["stop_before_hardware_warnings"][0]["reason"] == "run did not report ok=true."


def test_json_api_adapter_exposes_component_metadata_without_design():
    service = FrontendDesignService()

    headless = handle_request({"command": "headless-capabilities"}, service)
    assert headless["ok"] is True
    assert headless["result"]["format"] == "components.headless.capabilities"
    assert "student-component-catalog" in headless["result"]["core_commands"]["catalog"]
    assert "explain-result" in headless["result"]["core_commands"]["simulation"]
    assert "circuit-step" in headless["result"]["core_commands"]["circuit_simulation"]
    assert "Do not invent pinouts, active-low markers, chip behavior, timing, or procurement facts." in headless["result"]["student_guardrails"]

    builder = handle_request({"command": "project-builder", "options": {"part": "74HC00"}}, service)
    assert builder["ok"] is True
    assert builder["result"]["format"] == "components.ai.project_builder_workflow"
    assert builder["result"]["selected_part"]["part"] == "74HC00"
    assert builder["result"]["starter_schematic"]["chips"]["U1"]["part"] == "74HC00"
    assert builder["result"]["starter_schematic"]["expect"]["nand_both_high"] == ["Y = 0"]
    assert [step["step"] for step in builder["result"]["workflow"][:3]] == ["discover", "inspect", "draft"]

    catalog = handle_request({"command": "component-catalog", "options": {"group": "memory"}}, service)
    assert catalog["ok"] is True
    assert catalog["result"]["format"] == "components.db.catalog"
    assert catalog["result"]["group"] == "memory"
    assert {item["part"] for item in catalog["result"]["components"]} == {"62256", "AS6C62256", "AT28C256", "CY7C199", "SST39SF010A"}

    student_catalog = handle_request({"command": "student-component-catalog", "options": {"group": "virtual"}}, service)
    assert student_catalog["ok"] is True
    assert student_catalog["result"]["format"] == "components.db.student_catalog"
    probe = next(item for item in student_catalog["result"]["components"] if item["part"] == "Probe")
    assert probe["readiness"] == "usable"
    assert probe["capabilities"]["can_simulate"] is True

    detail = handle_request({"command": "component-detail", "options": {"part": "74HC00"}}, service)
    assert detail["ok"] is True
    assert detail["result"]["format"] == "components.db.component"
    assert detail["result"]["db_path"] == "lib/standard/74xx/74HC00/definition/definition.json"
    assert detail["result"]["capabilities"]["physical_pinout"] is True

    digital = handle_request({"command": "component-digital", "options": {"part": "74HC245"}}, service)
    assert digital["ok"] is True
    assert digital["result"]["schema"] == "db.component.digital"
    assert digital["result"]["validation"]["ok"] is True
    assert "interactive_demo" in digital["result"]["generation"]["targets"]

    package = handle_request({"command": "component-package", "options": {"part": "74HC245"}}, service)
    assert package["ok"] is True
    assert package["result"]["format"] == "db.component.package"
    assert package["result"]["layers"]["tests"]["tri_state"]["applicable"] is True

    virtual_package = handle_request({"command": "component-package", "options": {"part": "Probe"}}, service)
    assert virtual_package["ok"] is True
    assert virtual_package["result"]["format"] == "db.component.package"
    assert virtual_package["result"]["definition"]["schema"] == "db.component.definition"
    assert virtual_package["result"]["layers"]["simulation"]["service"] == "sim.probe"

    generated = handle_request({"command": "component-generate", "options": {"part": "74HC245"}}, service)
    assert generated["ok"] is True
    assert generated["result"]["format"] == "db.component.generated"
    assert generated["result"]["artifacts"]["interactive_demo"]["probes"] == ["A", "B"]


def test_json_api_adapter_runs_stateful_circuit_session():
    service = FrontendDesignService()
    loaded = handle_request({"command": "circuit-load", "input": {"path": str(CIRCUIT)}}, service)
    assert loaded["ok"] is True
    assert handle_request({"command": "circuit-step", "input": {"operation": "clock CLK"}}, service)["ok"] is True
    probe = handle_request({"command": "circuit-probe", "input": {"name": "T0"}}, service)
    assert probe["result"]["samples"][0]["name"] == "T0"
    failed = handle_request({"command": "circuit-step", "input": {"operation": "guess"}}, service)
    assert failed["ok"] is False
    assert failed["error"]["code"] == "runner.unsupported_step"


def test_json_api_adapter_exposes_timed_run_and_evidence_contracts():
    service = FrontendDesignService()
    response = handle_request({
        "command": "timed-run",
        "input": {"path": str(CIRCUIT), "operations": ["reset", "release /CLR", "clock CLK"]},
    }, service)
    assert response["ok"] is True
    assert response["result"]["timing"]["modeled_only"] is True
    explained = handle_request({"command": "explain-violations", "input": {"response": response}}, service)
    assert explained["ok"] is True
    exported = handle_request({"command": "export-evidence", "input": {"response": response, "include_traces": True}}, service)
    assert exported["ok"] is True
    assert exported["result"]["evidence"]["timing"]["trace"]
    blocked = handle_request({"command": "timed-run", "input": {"path": str(CIRCUIT), "operations": ["set /CLR 0"]}}, service)
    assert blocked["result"]["status"] == "blocked"
    assert blocked["error"]["code"] == "timing.unsupported"


def test_http_mode_requires_explicit_circuit_session_id():
    response = handle_request(
        {"command": "circuit-load", "input": {"path": str(CIRCUIT)}},
        FrontendDesignService(),
        circuit_sessions=CircuitSessionRegistry(),
        require_circuit_session=True,
    )
    assert response["ok"] is False
    assert response["error"]["code"] == "api.session_id_required"


def test_http_circuit_sessions_are_isolated_under_concurrency():
    sessions = CircuitSessionRegistry()
    service = FrontendDesignService()

    def request(session_id: str, command: str, **input_data):
        return handle_request(
            {"command": command, "session_id": session_id, "input": input_data},
            service,
            circuit_sessions=sessions,
            require_circuit_session=True,
        )

    loaded = request("student-a", "circuit-load", path=str(CIRCUIT))
    assert loaded["ok"] is True
    assert loaded["session_id"] == "student-a"

    with ThreadPoolExecutor(max_workers=2) as pool:
        probe_a, missing = list(pool.map(
            lambda sid: request(sid, "circuit-probe", name="T0"),
            ("student-a", "student-b"),
        ))
    assert probe_a["ok"] is True
    assert probe_a["session_id"] == "student-a"
    assert missing["ok"] is False
    assert missing["session_id"] == "student-b"
    assert "no circuit loaded" in missing["error"]["message"]

    loaded_b = request("student-b", "circuit-load", path=str(CIRCUIT))
    assert loaded_b["ok"] is True
    identities = {
        sid: sessions.execute(sid, lambda selected: {"service_id": id(selected)})["service_id"]
        for sid in ("student-a", "student-b")
    }
    assert identities["student-a"] != identities["student-b"]


def run_all():
    test_frontend_design_service_edits_and_exports_design()
    test_json_api_adapter_dispatches_stateful_frontend_commands()
    test_json_api_adapter_explain_result_wraps_structured_summary()
    test_json_api_adapter_exposes_component_metadata_without_design()
    test_json_api_adapter_runs_stateful_circuit_session()
    test_json_api_adapter_exposes_timed_run_and_evidence_contracts()
    test_http_mode_requires_explicit_circuit_session_id()
    test_http_circuit_sessions_are_isolated_under_concurrency()


if __name__ == "__main__":
    run_all()
    print("Components API tests passed")
