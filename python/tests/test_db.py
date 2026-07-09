"""DB manifest tests."""

import json

from chiplib.db import component_ids, component_summary, db_root, load_all_components, load_component


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

    hc00 = load_component("74HC00")
    assert hc00["part"] == "74HC00"
    assert hc00["package"]["pins"] == 14
    assert hc00["verilog"]["module"] == "ttl_74hc00"
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

    counter = load_component("74HC161")
    assert counter["pins"][0]["name"] == "/CLR"
    assert counter["pins"][14] == {"number": 15, "name": "RCO", "direction": "output"}

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


def run_all():
    test_db_seed_entries_are_loadable()
    test_db_summary_reports_status_and_gaps()
    test_db_manifests_match_schema_contract()


if __name__ == "__main__":
    run_all()
    print("Components DB tests passed")
