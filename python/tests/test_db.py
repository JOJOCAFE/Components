"""DB manifest tests."""

import importlib.util
import json
from pathlib import Path
import re

from chiplib.db import audit_db, component_catalog, component_detail, component_ids, component_summary, db_root, db_status_report, generate_component_artifacts, legacy_catalog_parts, load_all_components, load_component, load_component_package, load_digital_definition, load_digital_package, load_package_definition, student_component_catalog
from chiplib.db import _derived_package_layers
from chiplib.db import _pinout_mismatches
from chiplib.chips import create_chip


ALLOWED_STATUS = {
    "verified",
    "modeled",
    "tested",
    "missing",
    "blocked",
    "unknown",
    "not_applicable",
}
ALLOWED_DIRECTIONS = {"input", "output", "bidirectional", "passive", "power", "nc", "unknown"}
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
GROUPED_PARTS = {
    "InputSource",
    "ClockSource",
    "Switch",
    "Probe",
    "BusProbe",
    "VCC",
    "GND",
    "Pullup",
    "Pulldown",
    "RCParasitic",
    "OutputAssert",
    "DelayNoise",
    "LED",
    "RedLED",
    "BlueLED",
    "YellowLED",
    "Resistor",
    "Capacitor",
    "NPN",
    "PNP",
    "BC549",
    "BC559",
}
GENERATION_SEED_PARTS = {"74HC161", "74HC157", "74HC245", "74HC574", "AT28C256"}


def generation_package_parts() -> set[str]:
    return {
        path.parents[1].name
        for path in db_root().glob("*/*/definition/definition.json")
        if path.parents[2].name in {"74xx", "Memory"}
    }


def generic_package_parts() -> set[str]:
    return {
        path.parents[1].name
        for path in db_root().glob("*/*/definition/definition.json")
        if path.parents[2].name in {"Virtual", "Passive"}
    }


GENERATION_TARGETS = {
    "json",
    "python_simulator",
    "verilog_wrapper",
    "verilog_testbench",
    "kicad_symbol",
    "svg_pinout",
    "documentation",
    "unit_test",
    "interactive_demo",
}

LOCAL_DATASHEET_FILE_OVERRIDES = {
    "62256": "KM62256C.PDF",
    "74HC593": "M54HC593.PDF",
    "74HC922": "MM74C922.PDF",
}


def test_db_seed_entries_are_loadable():
    assert db_root().name == "DB"
    assert SEED_PARTS.issubset(set(component_ids()))
    assert GROUPED_PARTS.issubset(set(component_ids()))
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
    assert {key: counter["pins"][14][key] for key in ("number", "name", "direction")} == {"number": 15, "name": "RCO", "direction": "output"}
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
    assert {key: register["pins"][11][key] for key in ("number", "name", "direction")} == {"number": 12, "name": "8Q", "direction": "output"}

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

    source = load_component("InputSource")
    assert source["group"] == "virtual"
    assert source["kind"] == "virtual"
    assert source["role"] == "stimulus"
    assert source["db_path"] == "DB/Virtual/InputSource/definition/definition.json"
    assert source["pins"] == [{"number": 1, "name": "OUT", "direction": "output"}]
    assert source["simulation"]["service"] == "sim.input_source"

    switch = load_component("Switch")
    assert switch["group"] == "virtual"
    assert switch["kind"] == "virtual"
    assert switch["role"] == "stimulus"
    assert switch["db_path"] == "DB/Virtual/Switch/definition/definition.json"
    assert switch["pins"] == [{"number": 1, "name": "OUT", "direction": "output"}]
    assert switch["simulation"]["service"] == "sim.switch"
    assert switch["simulation"]["default_mode"] == "stable_off"
    assert {mode["name"] for mode in switch["simulation"]["modes"]} == {
        "stable_off",
        "stable_on",
        "one_shot_push_on_release_off",
        "one_shot_on_off",
        "preset_pulse_train",
    }
    assert switch["simulation"]["preset_profiles"][0]["name"] == "100_pulses_10ms_interval"

    rc_parasitic = load_component("RCParasitic")
    assert rc_parasitic["group"] == "virtual"
    assert rc_parasitic["kind"] == "virtual"
    assert rc_parasitic["role"] == "parasitic_timing_estimator"
    assert rc_parasitic["pins"] == [
        {"number": 1, "name": "IN", "direction": "passive"},
        {"number": 2, "name": "OUT", "direction": "passive"},
    ]
    assert rc_parasitic["simulation"]["service"] == "sim.rc_parasitic"
    assert rc_parasitic["claim_boundary"]["status"] == "estimate_only_not_signoff"

    output_assert = load_component("OutputAssert")
    assert output_assert["group"] == "virtual"
    assert output_assert["kind"] == "virtual"
    assert output_assert["role"] == "output_expectation_checker"
    assert output_assert["simulation"]["service"] == "sim.output_assert"
    assert output_assert["simulation"]["fail_policy"] == "raise_assertion"

    delay_noise = load_component("DelayNoise")
    assert delay_noise["group"] == "virtual"
    assert delay_noise["kind"] == "virtual"
    assert delay_noise["role"] == "delay_noise_injector"
    assert delay_noise["pins"] == [
        {"number": 1, "name": "IN", "direction": "input"},
        {"number": 2, "name": "OUT", "direction": "output"},
    ]
    assert delay_noise["simulation"]["service"] == "sim.delay_noise"
    assert delay_noise["simulation"]["deterministic_seed_required"] is True

    led = load_component("LED")
    assert led["group"] == "passive"
    assert led["db_path"] == "DB/Passive/LED/definition/definition.json"
    assert led["pins"][0]["direction"] == "passive"
    assert led["ui"]["symbol"] == "led"

    red_led = load_component("RedLED")
    assert red_led["title"] == "Red light emitting diode"
    assert red_led["ui"]["default_color"] == "red"

    blue_led = load_component("BlueLED")
    assert blue_led["title"] == "Blue light emitting diode"
    assert blue_led["ui"]["default_color"] == "blue"

    yellow_led = load_component("YellowLED")
    assert yellow_led["title"] == "Yellow light emitting diode"
    assert yellow_led["ui"]["default_color"] == "yellow"

    npn = load_component("NPN")
    assert npn["group"] == "discrete"
    assert [pin["name"] for pin in npn["pins"]] == ["C", "B", "E"]

    bc549 = load_component("BC549")
    assert bc549["group"] == "discrete"
    assert bc549["title"] == "BC549 NPN transistor"
    assert bc549["simulation"]["service"] == "sim.transistor.npn"

    bc559 = load_component("BC559")
    assert bc559["group"] == "discrete"
    assert bc559["title"] == "BC559 PNP transistor"
    assert bc559["simulation"]["service"] == "sim.transistor.pnp"


def test_db_summary_reports_status_and_gaps():
    summary = component_summary()
    assert summary["format"] == "db.summary"
    assert summary["count"] >= 3
    parts = [item["part"] for item in summary["components"]]
    assert SEED_PARTS.issubset(set(parts))
    assert GROUPED_PARTS.issubset(set(parts))
    assert "BC549" in parts
    assert "BC559" in parts
    assert all(item["missing_properties"] == [] for item in summary["components"])
    assert all(item["missing_files"] == [] for item in summary["components"])


def test_db_component_catalog_is_frontend_ready_and_grouped():
    catalog = component_catalog()
    assert catalog["format"] == "components.db.catalog"
    assert catalog["count"] >= 75
    groups = {item["id"]: item for item in catalog["groups"]}
    assert groups["74xx"]["count"] >= 57
    assert groups["memory"]["count"] == 5
    assert groups["virtual"]["count"] >= 8

    hc00 = next(item for item in catalog["components"] if item["part"] == "74HC00")
    assert hc00["group"] == "74xx"
    assert hc00["db_path"] == "DB/74xx/74HC00/definition/definition.json"
    assert hc00["capabilities"]["physical_pinout"] is True
    assert hc00["capabilities"]["verilog_file"] == "DB/74xx/74HC00/simulation/model.v"
    assert hc00["warnings"] == []

    memory = component_catalog(group="memory")
    assert memory["group"] == "memory"
    assert {item["part"] for item in memory["components"]} == {"62256", "AS6C62256", "AT28C256", "CY7C199", "SST39SF010A"}


def test_student_component_catalog_is_learner_facing_and_status_visible():
    catalog = student_component_catalog(group="virtual")
    assert catalog["format"] == "components.db.student_catalog"
    assert catalog["audience"] == "students ages 10-15, still useful for older learners"
    assert catalog["legend"]["ready"].startswith("Good for building")
    probe = next(item for item in catalog["components"] if item["part"] == "Probe")
    assert probe["readiness"] == "usable"
    assert probe["capabilities"]["can_simulate"] is True
    assert probe["capabilities"]["can_export_verilog"] is False
    assert probe["pins"]["preview"] == [{"number": 1, "name": "IN", "direction": "input"}]
    assert probe["warnings"] == []

    hc00 = next(item for item in student_component_catalog(group="74xx")["components"] if item["part"] == "74HC00")
    assert hc00["readiness"] == "ready"
    assert hc00["capabilities"]["can_export_verilog"] is True
    assert hc00["files"]["verilog"] == "DB/74xx/74HC00/simulation/model.v"


def test_virtual_and_passive_components_use_definition_packages():
    assert generic_package_parts() == {
        "InputSource",
        "ClockSource",
        "Switch",
        "Probe",
        "BusProbe",
        "VCC",
        "GND",
        "Pullup",
        "Pulldown",
        "RCParasitic",
        "OutputAssert",
        "DelayNoise",
        "LED",
        "RedLED",
        "BlueLED",
        "YellowLED",
        "Resistor",
        "Capacitor",
    }
    assert not list((db_root() / "Virtual").glob("*/component.json"))
    assert not list((db_root() / "Passive").glob("*/component.json"))

    probe_definition = load_package_definition("Probe")
    assert probe_definition["schema"] == "db.component.definition"
    assert probe_definition["validation"]["ok"] is True, probe_definition["validation"]["errors"]
    assert probe_definition["definition_path"] == "DB/Virtual/Probe/definition/definition.json"
    assert load_digital_definition("Probe", required=False) is None

    probe_package = load_component_package("Probe")
    assert probe_package["format"] == "db.component.package"
    assert probe_package["part"] == "Probe"
    assert probe_package["definition"]["schema"] == "db.component.definition"
    assert probe_package["definition"]["validation"]["ok"] is True
    assert probe_package["manifest"]["db_path"] == "DB/Virtual/Probe/definition/definition.json"
    assert probe_package["layers"]["definition"]["component"]["group"] == "virtual"
    assert probe_package["layers"]["definition"]["pins"]["pins"] == [{"number": 1, "name": "IN", "direction": "input"}]
    assert probe_package["layers"]["simulation"]["service"] == "sim.probe"
    assert probe_package["layers"]["symbol"]["symbol"] == "probe"
    assert probe_package["portable_files"] == []

    led_package = load_component_package("LED")
    assert led_package["definition"]["validation"]["ok"] is True
    assert led_package["manifest"]["db_path"] == "DB/Passive/LED/definition/definition.json"
    assert led_package["layers"]["definition"]["package"]["packages"] == [{"id": "two_terminal", "kind": "two_terminal", "pins": 2}]
    assert led_package["layers"]["symbol"]["default_color"] == "red"

    red_package = load_component_package("RedLED")
    assert red_package["manifest"]["db_path"] == "DB/Passive/RedLED/definition/definition.json"
    assert red_package["layers"]["symbol"]["default_color"] == "red"

    blue_package = load_component_package("BlueLED")
    assert blue_package["manifest"]["db_path"] == "DB/Passive/BlueLED/definition/definition.json"
    assert blue_package["layers"]["symbol"]["default_color"] == "blue"

    yellow_package = load_component_package("YellowLED")
    assert yellow_package["manifest"]["db_path"] == "DB/Passive/YellowLED/definition/definition.json"
    assert yellow_package["layers"]["symbol"]["default_color"] == "yellow"


def test_virtual_test_instruments_map_to_real_virtual_components():
    instruments = json.loads((db_root().parent / "DB" / "VIRTUAL_TEST_INSTRUMENTS.json").read_text(encoding="utf-8"))
    virtual_index = json.loads((db_root() / "Virtual" / "index.json").read_text(encoding="utf-8"))
    virtual_parts = set(virtual_index["components"])

    assert instruments["schema"] == "components.virtual_test_instruments"
    assert "do not replace datasheet evidence" in instruments["claim_boundary"]
    assert "Use virtual instruments to learn" in instruments["student_rule"]

    mapped = {item["part"] for item in instruments["instruments"]}
    assert mapped <= virtual_parts
    assert {"ClockSource", "Switch", "Probe", "BusProbe", "RCParasitic", "OutputAssert", "DelayNoise"} <= mapped

    for item in instruments["instruments"]:
        definition = load_component(item["part"])
        assert definition["group"] == "virtual", item
        assert item["instrument_role"], item
        assert item["student_name"], item
        assert item["protocol_gates"], item
        assert item["use_for"], item
        assert item["not_for"], item


def test_virtual_test_generator_contract_maps_split_records_to_instruments():
    contract = json.loads((db_root().parent / "DB" / "VIRTUAL_TEST_GENERATOR_CONTRACT.json").read_text(encoding="utf-8"))
    instruments = json.loads((db_root().parent / "DB" / "VIRTUAL_TEST_INSTRUMENTS.json").read_text(encoding="utf-8"))
    instrument_parts = {item["part"] for item in instruments["instruments"]}

    assert contract["schema"] == "components.virtual_test_generator_contract"
    assert contract["input_records"] == ["truth_table", "timing", "tri_state", "bus_fight", "propagation"]
    assert {level["level"] for level in contract["bench_levels"]} == {"chip", "circuit", "system"}

    for level in contract["bench_levels"]:
        assert set(level["required_instruments"]) <= instrument_parts, level
        assert set(level["optional_instruments"]) <= instrument_parts, level

    mapping = {item["record"]: item for item in contract["record_mapping"]}
    assert set(mapping) == set(contract["input_records"])
    assert "OutputAssert" in mapping["truth_table"]["virtual_instruments"]
    assert "BusProbe" in mapping["bus_fight"]["virtual_instruments"]
    assert {"RCParasitic", "DelayNoise", "OutputAssert"} <= set(mapping["propagation"]["virtual_instruments"])
    assert contract["delay_noise_policy"]["seed_required"] is True
    assert "DelayNoise shows what could go wrong" in contract["delay_noise_policy"]["student_note"]


def test_rv8gr_multi_level_protocol_and_report_are_current():
    root = db_root().parent
    protocol = (root / "DB" / "RV8GR_MULTI_LEVEL_TEST_PROTOCOL.md").read_text(encoding="utf-8")
    report = (root / "DB" / "RV8GR_TEST_REPORT.md").read_text(encoding="utf-8")
    readiness = json.loads((root / "DB" / "RV8GR_CHIP_LEVEL_READINESS.json").read_text(encoding="utf-8"))
    coverage = json.loads((root / "Lib" / "Circuits" / "RV8GR_COVERAGE_INDEX.json").read_text(encoding="utf-8"))

    assert "Level 1: Chip-Level Behavior Gate" in protocol
    assert "Level 2: Circuit-Level Gate" in protocol
    assert "Level 3: System-Level Gate" in protocol
    assert "Level 4: Physical Build Signoff Gate" in protocol
    assert "Virtual Physical-System Fault Gate" in protocol
    assert "Do not write \"hardware ready\" unless Level 4 passes." in protocol
    assert "DelayNoise" in protocol and "OutputAssert" in protocol
    assert "Wrong physical pin number" in protocol
    assert "Output-to-output wiring" in protocol
    assert "rising/falling edge" in protocol
    assert "positive disable-to-enable deadband" in protocol

    assert len(readiness["parts"]) == 18
    assert len(coverage["packages"]) == 22
    assert all(item["status"] == "Tested" for item in coverage["packages"])

    assert "| RV8GR required chips | 18 |" in report
    assert "| RV8GR circuit packages | 22 |" in report
    assert "| Physical hardware signoff | BLOCKED |" in report
    assert "Components virtual/model testing is ready" in report
    assert "Physical hardware is not signed off yet." in report
    assert "Virtual Physical-System Fault Coverage" in report
    assert "wrong physical pin number" in report
    assert "output-to-output wiring" in report
    assert "rising/falling edge behavior" in report
    assert "propagation delay, R/C delay, or delay noise" in report


def test_memory_components_use_definition_packages():
    memory_parts = {"62256", "AS6C62256", "AT28C256", "CY7C199", "SST39SF010A"}
    assert memory_parts.issubset(set(component_ids()))
    assert not list((db_root() / "Memory").glob("*/chip.json"))
    assert {path.parents[1].name for path in (db_root() / "Memory").glob("*/definition/definition.json")} == memory_parts

    for part in memory_parts:
        definition = load_digital_definition(part)
        assert definition["schema"] == "db.component.digital"
        assert definition["validation"]["ok"] is True, (part, definition["validation"]["errors"])

        package = load_component_package(part)
        assert package["format"] == "db.component.package"
        assert package["definition"]["schema"] == "db.component.digital"
        assert package["manifest"]["db_path"] == f"DB/Memory/{part}/definition/definition.json"
        assert package["layers"]["definition"]["component"]["family"] == "Memory"
        assert package["layers"]["simulation"]["model"]["schema"] == "db.component.simulation"


def test_db_component_detail_exposes_pins_and_capabilities():
    detail = component_detail("AT28C256")
    assert detail["format"] == "components.db.component"
    assert detail["part"] == "AT28C256"
    assert detail["group"] == "memory"
    assert detail["db_path"] == "DB/Memory/AT28C256/definition/definition.json"
    assert {key: detail["pins"][0][key] for key in ("number", "name", "direction")} == {"number": 1, "name": "A14", "direction": "input"}
    assert detail["capabilities"]["verilog_model"] is True
    assert detail["capabilities"]["verilog_file"] == "DB/Memory/AT28C256/simulation/model.v"
    assert detail["digital_definition"]["path"] == "DB/Memory/AT28C256/definition/definition.json"
    assert set(detail["digital_definition"]["generation_targets"]) == GENERATION_TARGETS


def test_generation_seed_digital_definitions_are_valid_and_generator_ready():
    for part in generation_package_parts():
        definition = load_digital_definition(part)
        assert definition["schema"] == "db.component.digital"
        assert definition["part"] == part
        assert definition["validation"]["ok"] is True, definition["validation"]["errors"]
        assert set(definition["generation"]["targets"]) == GENERATION_TARGETS
        assert len(definition["pins"]) == definition["package"]["pins"]
        assert definition["generation"]["python"]["factory"] == "create"
        assert definition["generation"]["verilog"]["file"].endswith("/simulation/model.v")


def test_digital_definition_schema_contract_is_strict_enough_for_generation():
    schema = json.loads((db_root() / "digital.schema.json").read_text(encoding="utf-8"))
    assert schema["properties"]["schema"]["const"] == "db.component.digital"
    assert "timing" in schema["required"]
    assert "package_evidence" in schema["properties"]["datasheet"]["properties"]["sources"]["items"]["required"]
    assert {"required": ["url"]} in schema["properties"]["datasheet"]["properties"]["sources"]["items"]["anyOf"]
    assert {"required": ["file"]} in schema["properties"]["datasheet"]["properties"]["sources"]["items"]["anyOf"]
    assert set(schema["$defs"]["generationTarget"]["enum"]) == GENERATION_TARGETS
    assert {"truth_table", "timing", "tri_state", "bus_fight", "propagation"} == set(schema["$defs"]["testType"]["enum"])

    pin_schema = schema["properties"]["pins"]["items"]["properties"]
    assert pin_schema["direction"]["$ref"] == "#/$defs/pinDirection"
    assert set(schema["$defs"]["pinDirection"]["enum"]) == ALLOWED_DIRECTIONS
    assert pin_schema["rail"]["enum"] == ["VCC", "VDD", "GND", "VSS"]


def test_generation_seed_digital_definitions_match_chip_manifests():
    for part in generation_package_parts():
        definition = load_digital_definition(part)
        manifest = load_component(part)
        package = load_digital_package(part)
        simulation = package["layers"]["simulation"]["model"]

        assert definition["validation"]["ok"] is True, definition["validation"]["errors"]
        assert definition["metadata"]["title"] == manifest["title"]
        assert definition["metadata"]["family"] == manifest["family"]
        assert definition["metadata"]["group"] == manifest["group"]
        assert definition["package"]["kind"] == manifest["package"]["kind"]
        assert definition["package"]["pins"] == manifest["package"]["pins"]
        assert definition["status"] == manifest["status"]

        digital_pins = {pin["number"]: pin for pin in definition["pins"]}
        manifest_pins = {pin["number"]: pin for pin in manifest["pins"]}
        assert set(digital_pins) == set(manifest_pins)
        for number, manifest_pin in manifest_pins.items():
            digital_pin = digital_pins[number]
            assert digital_pin["name"] == manifest_pin["name"]
            assert digital_pin["direction"] == manifest_pin["direction"]
            if "active_low" in manifest_pin:
                assert digital_pin["active_low"] == manifest_pin["active_low"]

        assert definition["generation"]["python"]["factory"] == simulation["python"]["factory"]
        assert definition["generation"]["python"]["file"] == simulation["python"]["file"]
        assert definition["generation"]["verilog"]["module"] == simulation["verilog"]["module"]
        assert definition["generation"]["verilog"]["file"] == simulation["verilog"]["file"]
        assert definition["generation"]["verilog"]["netlist"] == simulation["netlist_generation"]["source"]

        export = manifest["verilog"]["export"]
        export_pins = set(export["output_pins"])
        for port in export["ports"]:
            export_pins.update(port["pins"])
            if "internal" in str(port.get("note", "")).lower() and "placeholder" in str(port.get("note", "")).lower():
                export_pins.difference_update(pin for pin in port.get("pins", []) if pin == 0)
        export_pins.discard(0)
        assert export_pins.issubset(set(digital_pins))


def test_generation_seed_digital_packages_load_split_tests():
    for part in generation_package_parts():
        package = load_digital_package(part)
        definition = package["definition"]
        assert package["format"] == "db.component.package"
        assert package["part"] == part
        assert definition["part"] == part
        assert definition["validation"]["ok"] is True, definition["validation"]["errors"]
        assert definition["package"]["pins"] == len(definition["pins"])

        tests = package["layers"]["tests"]
        for test_type in ("truth_table", "timing", "tri_state", "bus_fight", "propagation"):
            test_data = tests[test_type]
            assert test_data is not None, (part, test_type)
            assert test_data["schema"] == f"db.component.test.{test_type}"
            assert test_data["version"] == 1
            assert test_data["part"] == part
            assert isinstance(test_data["applicable"], bool)

        for test_type in definition["verification"]["tests"]:
            assert tests[test_type]["applicable"] is True, (part, test_type)


def test_generation_seed_packages_have_required_layers():
    required_definition_layers = ("component", "package", "pins", "power", "logic", "timing", "electrical")
    for part in generation_package_parts():
        package = load_digital_package(part)
        definition = package["layers"]["definition"]
        digital = package["definition"]
        simulation = package["layers"]["simulation"]
        assert package["definition"]["validation"]["ok"] is True, part
        assert isinstance(digital.get("definition_layers"), dict), part
        for layer_name in required_definition_layers:
            assert definition[layer_name] is not None, (part, layer_name)
            if layer_name in digital["definition_layers"]:
                assert definition[layer_name] == digital["definition_layers"][layer_name], (part, layer_name)
            assert definition[layer_name]["part"] == part, (part, layer_name)
        assert simulation["model"] is not None, part
        assert simulation["netlist"] is not None, part
        assert package["layers"]["symbol"]["dip"] is not None, part
        assert package["layers"]["datasheet"]["sources"] is not None, part
        assert package["layers"]["symbol"]["dip"]["schema"] == "db.component.symbol.dip"
        assert simulation["model"]["schema"] == "db.component.simulation"
        assert simulation["model"]["python"]["factory"] == "create"
        assert simulation["model"]["python"]["file"].endswith("/simulation/model.py")
        assert simulation["model"]["verilog"]["file"].endswith("/simulation/model.v")
        assert simulation["model"]["netlist_generation"]["source"].endswith("/simulation/netlist.json")
        assert simulation["netlist"]["schema"] == "db.component.simulation.netlist"
        assert simulation["netlist"]["simulation"]["python"] == simulation["model"]["python"]["file"]
        assert simulation["netlist"]["simulation"]["verilog"] == simulation["model"]["verilog"]["file"]
        assert simulation["netlist"]["verilog"]["module"] == package["manifest"]["verilog"]["module"]
        assert simulation["netlist"]["verilog"]["export"] == package["manifest"]["verilog"]["export"]
        portable = package["portable_files"]
        assert {item["kind"] for item in portable} == {"python_model", "python_runtime", "verilog_model", "netlist"}
        assert any(item["runtime"] == "python" and item["copy_as"] == "model.py" for item in portable)
        assert any(
            item["kind"] == "python_runtime"
            and item["copy_as"] == "chiplib/core.py"
            and item["shared"] is True
            and item["copy_once"] is True
            for item in portable
        )
        assert simulation["model"]["python"]["file"] in {item["source"] for item in portable}


def test_physical_digital_definitions_omit_exact_duplicate_layers():
    duplicates: list[tuple[str, str]] = []
    for part in generation_package_parts():
        definition = load_digital_definition(part)
        derived = _derived_package_layers(definition, load_component(part))
        layers = definition.get("definition_layers", {})
        for layer_name, layer in layers.items():
            if layer == derived.get(layer_name):
                duplicates.append((part, layer_name))

    assert duplicates == []


def test_python_chip_factory_delay_matches_public_timing_default():
    mismatches: list[tuple[str, int, int]] = []
    for part in generation_package_parts():
        definition = load_digital_definition(part)
        timing = definition.get("timing", {})
        expected = None
        if isinstance(timing.get("simple"), dict):
            expected = timing["simple"].get("default_delay_ns")
        elif isinstance(timing.get("paths"), dict):
            expected = timing["paths"].get("address_to_data_valid_ns")
        elif isinstance(timing.get("delay_ns"), int):
            expected = timing["delay_ns"]
        if not isinstance(expected, int):
            continue

        chip = create_chip(part, "U")
        actual = chip.delay.rise_ns
        if actual != expected:
            mismatches.append((part, actual, expected))

    assert mismatches == []


def test_generation_seed_simulation_sources_are_local_and_importable():
    for part in generation_package_parts():
        package = load_digital_package(part)
        model = package["layers"]["simulation"]["model"]
        for file_key in ("simulation_model_py", "simulation_model_v", "simulation_netlist"):
            assert file_key in package["files"], (part, file_key)
            assert Path(package["files"][file_key]).parts[-2] == "simulation", (part, file_key)

        model_path = db_root().parent / model["python"]["file"]
        spec = importlib.util.spec_from_file_location(f"local_{part.lower()}_model", model_path)
        assert spec is not None and spec.loader is not None, part
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        chip = module.create("U1")
        assert chip.part == part
        assert chip.name == "U1"


def test_generation_seed_definitions_are_one_file_sources():
    for part in generation_package_parts():
        package = load_digital_package(part)
        definition_dir = db_root() / package["files"]["definition"]
        json_files = sorted(path.name for path in definition_dir.parent.glob("*.json"))
        assert json_files == ["definition.json"], (part, json_files)
        assert not any(name.startswith("legacy_") for name in package["files"]), part


def test_74hc245_split_tests_and_evidence_are_loaded():
    package = load_digital_package("74HC245")
    tests = package["layers"]["tests"]
    assert {item["name"] for item in tests["truth_table"]["vectors"]} == {
        "dir_high_a_to_b",
        "dir_high_a_to_b_reverse_pattern",
        "dir_low_b_to_a",
        "dir_low_b_to_a_reverse_pattern",
        "disabled_oe_high_releases_a_and_b",
        "disabled_oe_high_reverse_releases_a_and_b",
        "reenabled_a_to_b_after_high_z",
        "direction_reversal_back_to_b_to_a",
    }
    assert {item["name"] for item in tests["tri_state"]["checks"]} >= {"disabled_releases_a", "disabled_releases_b"}
    assert {item["name"] for item in tests["bus_fight"]["checks"]} == {
        "external_b_driver_conflicts_with_a_to_b",
        "external_a_driver_conflicts_with_b_to_a",
        "oe_high_prevents_conflict_with_external_drivers",
    }
    assert {item["control"] for item in tests["timing"]["checks"] if "control" in item} == {"DIR", "/OE"}
    assert {item["parameter"] for item in tests["timing"]["checks"] if "parameter" in item} == {
        "tpd",
        "ten",
        "tdis",
        "tt",
    }
    assert {item["path"] for item in tests["propagation"]["checks"]} == {
        "A_to_B",
        "B_to_A",
        "OE_to_output_enable",
        "OE_to_high_Z",
        "transition_time",
    }
    assert {item["expect_default_delay_ns"] for item in tests["propagation"]["checks"]} == {12}
    assert next(
        item for item in tests["propagation"]["checks"] if item["path"] == "OE_to_high_Z"
    )["expect_typ_ns"]["vcc_6_v"] == 21

    timing = package["layers"]["definition"]["timing"]
    assert timing["delay"]["simple"]["default_delay_ns"] == 12
    assert timing["delay"]["timed"]["paths"]["A_to_B"]["ranges_ns"]["vcc_4_5_v"] == {
        "min_ns": None,
        "typ_ns": 15,
        "max_ns_25c": 21,
        "max_ns_sn54": 32,
        "max_ns_sn74": 26,
    }
    assert timing["delay"]["timed"]["paths"]["OE_to_output_enable"]["ranges_ns"]["vcc_6_v"]["typ_ns"] == 20
    assert timing["delay"]["timed"]["paths"]["OE_to_high_Z"]["ranges_ns"]["vcc_6_v"]["max_ns_25c"] == 34
    assert timing["delay"]["timed"]["paths"]["transition_time"]["ranges_ns"]["vcc_4_5_v"]["max_ns_sn74"] == 15
    assert timing["delay"]["datasheet_typical_ns"]["tpd_a_b_to_b_a"]["vcc_4_5_v"] == 15
    assert timing["delay"]["datasheet_typical_ns"]["tdis_oe_to_a_b"]["vcc_6_v"] == 21
    electrical = package["layers"]["definition"]["electrical"]
    assert electrical["voltage"]["vcc"] == {"min_v": 2.0, "typ_v": 5.0, "max_v": 6.0, "status": "extracted"}
    assert electrical["current"]["output_drive"]["vcc_4_5_v"] == {"ioh_ma": -6, "iol_ma": 6}
    assert electrical["loading"]["input_capacitance"]["max_pf"] == 10


def test_component_generation_artifacts_cover_declared_targets():
    for part in generation_package_parts():
        generated = generate_component_artifacts(part)
        assert generated["format"] == "db.component.generated"
        assert generated["part"] == part
        assert generated["source"].endswith("definition/definition.json")
        assert any(item["runtime"] == "python" and item["copy_as"] == "model.py" for item in generated["portable_files"])
        assert any(
            item["kind"] == "python_runtime"
            and item["source"] == "python/chiplib/core.py"
            and item["copy_once"] is True
            for item in generated["portable_files"]
        )
        assert set(generated["artifacts"]) == GENERATION_TARGETS
        for artifact in generated["artifacts"].values():
            assert artifact["part"] == part
        assert generated["artifacts"]["python_simulator"]["portable"] is True
        assert generated["artifacts"]["python_simulator"]["copy_with_chip"]

    hc245 = generate_component_artifacts("74HC245")
    assert hc245["artifacts"]["json"]["buses"]["A"]["pins_lsb_first"] == [2, 3, 4, 5, 6, 7, 8, 9]
    assert hc245["artifacts"]["verilog_wrapper"]["module"] == "ttl_74hc245"
    assert hc245["artifacts"]["svg_pinout"]["shape"] == "dip"
    assert hc245["artifacts"]["documentation"]["sections"] == ["overview", "pins", "controls", "truth_table", "timing", "try_it"]
    assert hc245["artifacts"]["documentation"]["overview"] == "74HC245 is a 20-pin DIP part for bus transceiver."
    assert "Connect power before testing signal pins." in hc245["artifacts"]["documentation"]["key_points"]
    assert hc245["artifacts"]["documentation"]["control_explanations"][1]["hint"] == "This is active low, so 0 turns the control on."
    assert hc245["artifacts"]["documentation"]["bus_explanations"][0]["explanation"] == "A is an 8-bit signal group. Bit 0 is pin 2 and the highest bit is pin 9."
    assert (
        hc245["artifacts"]["documentation"]["timing_note"]
        == "Default simulator delay is 12 ns; timed mode uses path-specific datasheet delays."
    )
    assert hc245["artifacts"]["interactive_demo"]["probes"] == ["A", "B"]
    assert hc245["artifacts"]["interactive_demo"]["title"] == "Try 74HC245 in the simulator"
    assert hc245["artifacts"]["interactive_demo"]["guided_steps"] == [
        "Set each control to the value you want to test.",
        "Run one settle step so the simulated signals can update.",
        "Read the probes and compare them with the truth table.",
    ]
    assert hc245["artifacts"]["interactive_demo"]["probe_labels"][0]["hint"] == "Read all 8 bits together."


def test_generated_artifact_files_exist_for_seed_batch():
    for part in generation_package_parts():
        definition_path = db_root().parent / load_digital_definition(part)["definition_path"]
        path = definition_path.parents[1] / "generated" / "artifacts.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["format"] == "db.component.generated"
        assert data["part"] == part
        assert set(data["artifacts"]) == GENERATION_TARGETS


def test_remaining_seed_timing_and_electrical_evidence_is_extracted():
    checks = {
        "74HC161": {
            "timing": ("clock_to_q", "vcc_4_5_v", 25),
            "drive": {"ioh_ma": -4, "iol_ma": 4},
        },
        "74HC157": {
            "timing": ("data_to_y", "vcc_4_5_v", 13),
            "drive": {"ioh_ma": -6, "iol_ma": 6},
        },
        "74HC574": {
            "timing": ("clock_to_q", "vcc_4_5_v", 28),
            "drive": {"ioh_ma": -6, "iol_ma": 6},
        },
        "AT28C256": {
            "timing": ("tacc_address_to_output", "at28c256_15", 150),
            "vcc": {"min_v": 4.5, "typ_v": 5.0, "max_v": 5.5, "status": "extracted"},
        },
    }
    for part, expected in checks.items():
        package = load_digital_package(part)
        timing = package["layers"]["definition"]["timing"]
        electrical = package["layers"]["definition"]["electrical"]
        assert timing is not None, part
        assert electrical is not None, part
        timing_name, key, value = expected["timing"]
        if part == "AT28C256":
            assert timing["delay"]["datasheet_read_ns"][timing_name][key] == value
            definition = load_digital_definition("AT28C256")
            top_timing = definition["timing"]
            assert top_timing == {
                "variant": "AT28C256-15",
                "paths": {
                    "address_to_data_valid_ns": 150,
                    "ce_to_data_valid_ns": 150,
                    "oe_to_data_valid_ns": 70,
                    "ce_or_oe_to_high_z_ns": 50,
                },
                "write": {
                    "pulse_min_ns": 100,
                    "data_setup_min_ns": 50,
                    "address_hold_min_ns": 50,
                },
            }
            layer_delay = timing["delay"]
            assert layer_delay["selected_variant"] == "at28c256_15"
            assert "do_not_assume_70ns" in layer_delay["variant_policy"]["unselected_variant_policy"]
            write_detail = layer_delay["datasheet_write_ns"]
            assert write_detail["latch_edge"] == "/WE rising"
            assert write_detail["write_cycle_us"] == 10000
            assert write_detail["write_cycle_updates_default"] == 1
            assert "high-Z" in write_detail["busy_behavior"]
            assert electrical["voltage"]["vcc"] == expected["vcc"]
            assert electrical["loading"]["input_capacitance"]["max_pf"] == 6
        else:
            assert timing["delay"]["datasheet_typical_ns"][timing_name][key] == value
            assert electrical["current"]["output_drive"]["vcc_4_5_v"] == expected["drive"]
            assert electrical["loading"]["input_capacitance"]["max_pf"] == 10
        assert "url" in timing["evidence"]
        assert "url" in electrical["evidence"]


def test_db_manifests_match_schema_contract():
    schema = json.loads((db_root() / "chip.schema.json").read_text(encoding="utf-8"))
    assert schema["properties"]["schema"]["const"] == "db.chip"
    assert "passive" in schema["properties"]["pins"]["items"]["properties"]["direction"]["enum"]
    digital_schema = json.loads((db_root() / "digital.schema.json").read_text(encoding="utf-8"))
    assert set(digital_schema["properties"]["definition_layers"]["required"]) == {
        "component",
        "package",
        "pins",
        "power",
        "logic",
        "timing",
        "electrical",
    }

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


def test_ic_manifests_with_python_behavior_paths_are_marked_simulatable():
    for manifest in load_all_components():
        if manifest.get("kind") != "ic" and manifest.get("group") not in {"74xx", "memory"}:
            continue
        if not manifest.get("legacy_paths", {}).get("python_behavior"):
            continue
        assert manifest["status"]["python_behavior"] in {"modeled", "tested"}, manifest["part"]
        detail = component_detail(manifest["part"])
        assert detail["capabilities"]["python_behavior"] is True, manifest["part"]


def test_db_audit_reports_partial_legacy_coverage_without_hard_errors():
    audit = audit_db()
    assert audit["format"] == "db.audit"
    assert audit["ok"] is True
    assert audit["errors"] == []
    assert SEED_PARTS.issubset(set(audit["coverage"]["db_parts"]))
    assert "74HC147" in audit["coverage"]["db_parts"]
    assert "LED" not in audit["coverage"]["db_parts"]
    assert SEED_PARTS.issubset(set(audit["coverage"]["legacy_model_parts"]))
    assert "74HC147" not in audit["coverage"]["legacy_parts_missing_db"]
    assert audit["chip_status"]["format"] == "db.status"
    assert audit["chip_status"]["ok"] is True


def test_db_legacy_coverage_lists_models_and_pinouts():
    legacy = legacy_catalog_parts()
    assert "74HC00" in legacy["verilog_models"]
    assert "74HC00" in legacy["pinouts"]
    assert "AT28C256" in legacy["verilog_models"]
    assert "SST39SF010A" in legacy["pinouts"]
    legacy_backed = set(component_ids()) - GROUPED_PARTS
    assert legacy_backed.issubset(set(legacy["verilog_models"]))
    assert legacy_backed.issubset(set(legacy["pinouts"]))


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
    assert {"74HC150", "74HC260"}.issubset(set(report["chip_status"]["missing_datasheet"]))
    assert "74HC150" not in report["chip_status"]["tested"]
    assert "74HC260" not in report["chip_status"]["tested"]
    assert not any(item["code"] == "chip_status_parts_missing_db" and item.get("category") == "missing_datasheet" for item in report["warnings"])


def test_embedded_pinout_matches_grouped_db_manifest_pins():
    assert _pinout_mismatches(load_component("74HC00")) == []
    assert _pinout_mismatches(load_component("74HC147")) == []

    broken = load_component("74HC00")
    broken["pins"][0]["name"] = "BROKEN"
    issues = _pinout_mismatches(broken)
    assert issues == [{
        "code": "pinout_name_mismatch",
        "message": "pin 1 embedded pinout='1A' DB='BROKEN'",
    }]


def test_physical_chip_definitions_have_local_source_datasheets():
    root = db_root().parent
    source_dir = root / "Source"
    source_pdfs = sorted(path for path in source_dir.iterdir() if path.is_file() and path.suffix.lower() == ".pdf")
    missing: list[str] = []

    for part in generation_package_parts():
        definition = load_digital_definition(part)
        sources = definition.get("datasheet", {}).get("sources", [])
        local_files: list[Path] = []
        for source in sources:
            if not isinstance(source, dict):
                continue
            file_name = source.get("file")
            if isinstance(file_name, str):
                local_files.append(root / file_name)
            for key in ("url", "source", "source_note"):
                value = str(source.get(key, ""))
                match = re.search(r"(?:Components/)?(Source/[^\s`]+\.pdf|Source/[^\s`]+\.PDF)", value)
                if match:
                    local_files.append(root / match.group(1))

        override = LOCAL_DATASHEET_FILE_OVERRIDES.get(part)
        if override:
            local_files.append(source_dir / override)

        exact_part = re.compile(rf"(^|[^A-Za-z0-9]){re.escape(part)}([^A-Za-z0-9]|$)", re.IGNORECASE)
        local_files.extend(path for path in source_pdfs if exact_part.search(path.stem))

        if not any(path.exists() for path in local_files):
            missing.append(part)

    assert missing == []


def run_all():
    test_db_seed_entries_are_loadable()
    test_db_summary_reports_status_and_gaps()
    test_db_component_catalog_is_frontend_ready_and_grouped()
    test_student_component_catalog_is_learner_facing_and_status_visible()
    test_virtual_and_passive_components_use_definition_packages()
    test_virtual_test_instruments_map_to_real_virtual_components()
    test_virtual_test_generator_contract_maps_split_records_to_instruments()
    test_rv8gr_multi_level_protocol_and_report_are_current()
    test_memory_components_use_definition_packages()
    test_db_component_detail_exposes_pins_and_capabilities()
    test_generation_seed_digital_definitions_are_valid_and_generator_ready()
    test_digital_definition_schema_contract_is_strict_enough_for_generation()
    test_generation_seed_digital_definitions_match_chip_manifests()
    test_generation_seed_digital_packages_load_split_tests()
    test_generation_seed_packages_have_required_layers()
    test_physical_digital_definitions_omit_exact_duplicate_layers()
    test_python_chip_factory_delay_matches_public_timing_default()
    test_74hc245_split_tests_and_evidence_are_loaded()
    test_component_generation_artifacts_cover_declared_targets()
    test_generated_artifact_files_exist_for_seed_batch()
    test_remaining_seed_timing_and_electrical_evidence_is_extracted()
    test_db_manifests_match_schema_contract()
    test_ic_manifests_with_python_behavior_paths_are_marked_simulatable()
    test_db_audit_reports_partial_legacy_coverage_without_hard_errors()
    test_db_legacy_coverage_lists_models_and_pinouts()
    test_db_status_report_checks_chip_status_snapshot()
    test_embedded_pinout_matches_grouped_db_manifest_pins()
    test_physical_chip_definitions_have_local_source_datasheets()


if __name__ == "__main__":
    run_all()
    print("Components DB tests passed")
