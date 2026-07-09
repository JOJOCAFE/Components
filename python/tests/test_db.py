"""DB manifest tests."""

import json

from chiplib.db import audit_db, component_ids, component_summary, db_root, db_status_report, legacy_catalog_parts, load_all_components, load_component


ALLOWED_STATUS = {
    "verified",
    "modeled",
    "tested",
    "missing",
    "blocked",
    "unknown",
    "not_applicable",
}
ALLOWED_DIRECTIONS = {"input", "output", "bidirectional", "power", "nc", "unknown"}
SEED_PARTS = {
    "62256",
    "74HC00",
    "74HC04",
    "74HC74",
    "74HC138",
    "74HC161",
    "74HC245",
    "74HC574",
    "AT28C256",
    "SST39SF010A",
}


def test_db_seed_entries_are_loadable():
    assert db_root().name == "db"
    assert SEED_PARTS.issubset(set(component_ids()))
    assert "74HC147" in component_ids()

    hc00 = load_component("74HC00")
    assert hc00["part"] == "74HC00"
    assert hc00["package"]["pins"] == 14
    assert hc00["verilog"]["module"] == "ttl_74hc00"
    assert hc00["verilog"]["export"]["ports"] == [
        {"name": "A", "pins": [1, 4, 9, 12], "direction": "input"},
        {"name": "B", "pins": [2, 5, 10, 13], "direction": "input"},
        {"name": "Y", "pins": [3, 6, 8, 11], "direction": "output"},
    ]
    assert hc00["verilog"]["export"]["output_pins"] == [3, 6, 8, 11]
    assert hc00["verilog"]["export"]["delay_ns"] == {"U26": 8, "*": 1}
    assert hc00["missing_properties"] == []
    assert hc00["missing_files"] == []
    assert hc00["pins"][0] == {"number": 1, "name": "1A", "direction": "input"}

    ram = load_component("62256")
    assert ram["family"] == "Memory"
    assert ram["pins"][10]["direction"] == "bidirectional"
    assert ram["pins"][19]["active_low"] is True

    transceiver = load_component("74HC245")
    assert transceiver["package"]["pins"] == 20
    assert transceiver["pins"][1]["direction"] == "bidirectional"
    assert transceiver["pins"][18]["active_low"] is True
    assert transceiver["verilog"]["export"]["ports"] == [
        {"name": "OE_bar", "pins": [19], "direction": "input"},
        {"name": "DIR", "pins": [1], "direction": "input"},
        {"name": "A", "pins": [2, 3, 4, 5, 6, 7, 8, 9], "direction": "output"},
        {"name": "B", "pins": [18, 17, 16, 15, 14, 13, 12, 11], "direction": "output"},
    ]

    counter = load_component("74HC161")
    assert counter["pins"][0]["name"] == "/CLR"
    assert counter["pins"][14] == {"number": 15, "name": "RCO", "direction": "output"}
    assert counter["verilog"]["export"]["ports"] == [
        {"name": "Clear_bar", "pins": [1], "direction": "input"},
        {"name": "Load_bar", "pins": [9], "direction": "input"},
        {"name": "ENT", "pins": [10], "direction": "input"},
        {"name": "ENP", "pins": [7], "direction": "input"},
        {"name": "D", "pins": [3, 4, 5, 6], "direction": "input"},
        {"name": "Clk", "pins": [2], "direction": "input"},
        {"name": "RCO", "pins": [15], "direction": "output"},
        {"name": "Q", "pins": [14, 13, 12, 11], "direction": "output"},
    ]

    inverter = load_component("74HC04")
    assert inverter["verilog"]["export"]["ports"] == [
        {"name": "A", "pins": [1, 3, 5, 9, 11, 13], "direction": "input"},
        {"name": "Y", "pins": [2, 4, 6, 8, 10, 12], "direction": "output"},
    ]

    eeprom = load_component("AT28C256")
    assert eeprom["family"] == "Memory"
    assert eeprom["verilog"]["module"] == "mem_at28c256"

    dff = load_component("74HC74")
    assert dff["package"]["pins"] == 14
    assert dff["pins"][0]["name"] == "/1CLR"
    assert dff["pins"][5]["active_low"] is True

    register = load_component("74HC574")
    assert register["verilog"]["module"] == "ttl_74hc574"
    assert register["pins"][0]["active_low"] is True
    assert register["pins"][11] == {"number": 12, "name": "8Q", "direction": "output"}

    decoder = load_component("74HC138")
    assert decoder["verilog"]["module"] == "ttl_74hc138"
    assert decoder["pins"][3]["name"] == "/G2A"
    assert decoder["pins"][14]["active_low"] is True

    encoder = load_component("74HC147")
    assert encoder["status"]["verilog_export"] == "tested"
    assert encoder["verilog"]["export"]["ports"][0] == {"name": "I0_bar", "pins": [9], "direction": "input"}
    assert encoder["pins"][8] == {"number": 9, "name": "/I0", "direction": "input", "active_low": True}
    assert encoder["pins"][14] == {"number": 15, "name": "NC", "direction": "nc"}

    flash = load_component("SST39SF010A")
    assert flash["family"] == "Memory"
    assert flash["package"]["pins"] == 32
    assert flash["pins"][0]["direction"] == "nc"
    assert flash["verilog"]["module"] == "mem_sst39sf010a"


def test_db_summary_reports_status_and_gaps():
    summary = component_summary()
    assert summary["format"] == "db.summary"
    assert summary["count"] >= 3
    parts = [item["part"] for item in summary["components"]]
    assert SEED_PARTS.issubset(set(parts))
    assert all(item["missing_properties"] == [] for item in summary["components"])
    assert all(item["missing_files"] == [] for item in summary["components"])


def test_db_manifests_match_schema_contract():
    schema = json.loads((db_root() / "chip.schema.json").read_text(encoding="utf-8"))
    assert schema["properties"]["schema"]["const"] == "db.chip"

    for manifest in load_all_components():
        for key in schema["required"]:
            assert key in manifest, (manifest.get("part"), key)
        assert manifest["schema"] == "db.chip"
        assert isinstance(manifest["version"], int)
        assert manifest["version"] >= 1
        assert manifest["package"]["pins"] == len(manifest["pins"])
        assert set(manifest["status"]).issuperset(set(schema["properties"]["status"]["required"]))
        assert set(manifest["status"].values()).issubset(ALLOWED_STATUS)
        for pin in manifest["pins"]:
            assert {"number", "name", "direction"}.issubset(pin)
            assert isinstance(pin["number"], int)
            assert pin["number"] >= 1
            assert pin["direction"] in ALLOWED_DIRECTIONS


def test_db_audit_reports_partial_legacy_coverage_without_hard_errors():
    audit = audit_db()
    assert audit["format"] == "db.audit"
    assert audit["ok"] is True
    assert audit["errors"] == []
    assert SEED_PARTS.issubset(set(audit["coverage"]["db_parts"]))
    assert "74HC147" in audit["coverage"]["db_parts"]
    assert SEED_PARTS.issubset(set(audit["coverage"]["legacy_model_parts"]))
    assert "74HC147" not in audit["coverage"]["legacy_parts_missing_db"]
    assert any(item["code"] == "chip_status_parts_missing_db" for item in audit["warnings"])
    assert audit["chip_status"]["format"] == "db.status"
    assert audit["chip_status"]["ok"] is True


def test_db_legacy_coverage_lists_models_and_pinouts():
    legacy = legacy_catalog_parts()
    assert "74HC00" in legacy["verilog_models"]
    assert "74HC00" in legacy["pinouts"]
    assert "AT28C256" in legacy["verilog_models"]
    assert "SST39SF010A" in legacy["pinouts"]
    assert set(component_ids()).issubset(set(legacy["verilog_models"]))
    assert set(component_ids()).issubset(set(legacy["pinouts"]))


def test_db_status_report_checks_chip_status_snapshot():
    report = db_status_report()
    tested_seed_parts = SEED_PARTS - {"74HC147"}
    assert report["format"] == "db.status"
    assert report["ok"] is True
    assert report["errors"] == []
    assert SEED_PARTS.issubset(set(report["generated"]["verified"]))
    assert SEED_PARTS.issubset(set(report["generated"]["modeled"]))
    assert tested_seed_parts.issubset(set(report["generated"]["tested"]))
    assert SEED_PARTS.issubset(set(report["chip_status"]["verified"]))
    assert SEED_PARTS.issubset(set(report["chip_status"]["modeled"]))
    assert tested_seed_parts.issubset(set(report["chip_status"]["tested"]))
    assert any(item["code"] == "chip_status_parts_missing_db" for item in report["warnings"])


def run_all():
    test_db_seed_entries_are_loadable()
    test_db_summary_reports_status_and_gaps()
    test_db_manifests_match_schema_contract()
    test_db_audit_reports_partial_legacy_coverage_without_hard_errors()
    test_db_legacy_coverage_lists_models_and_pinouts()
    test_db_status_report_checks_chip_status_snapshot()


if __name__ == "__main__":
    run_all()
    print("Components DB tests passed")
