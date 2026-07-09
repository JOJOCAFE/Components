"""Generated checks from component split test records."""

from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from chiplib.db import generate_component_artifacts
from chiplib import Board, BusConflictError, Z, create_chip


ROOT = Path(__file__).resolve().parents[2]
SEED_TEST_ROOTS = {
    "74HC161": ROOT / "DB" / "74xx" / "74HC161" / "tests",
    "74HC157": ROOT / "DB" / "74xx" / "74HC157" / "tests",
    "74HC245": ROOT / "DB" / "74xx" / "74HC245" / "tests",
    "74HC574": ROOT / "DB" / "74xx" / "74HC574" / "tests",
    "AT28C256": ROOT / "DB" / "Memory" / "AT28C256" / "tests",
}
TARGETED_TRUTH_TEST_ROOTS = {
    "74HC21": ROOT / "DB" / "74xx" / "74HC21" / "tests",
    "74HC74": ROOT / "DB" / "74xx" / "74HC74" / "tests",
    "74HC86": ROOT / "DB" / "74xx" / "74HC86" / "tests",
    "74HC161": ROOT / "DB" / "74xx" / "74HC161" / "tests",
    "74HC164": ROOT / "DB" / "74xx" / "74HC164" / "tests",
    "74HC245": ROOT / "DB" / "74xx" / "74HC245" / "tests",
    "74HC283": ROOT / "DB" / "74xx" / "74HC283" / "tests",
    "74HC541": ROOT / "DB" / "74xx" / "74HC541" / "tests",
    "74HC574": ROOT / "DB" / "74xx" / "74HC574" / "tests",
    "74HC688": ROOT / "DB" / "74xx" / "74HC688" / "tests",
    "62256": ROOT / "DB" / "Memory" / "62256" / "tests",
    "AS6C62256": ROOT / "DB" / "Memory" / "AS6C62256" / "tests",
    "AT28C256": ROOT / "DB" / "Memory" / "AT28C256" / "tests",
    "SST39SF010A": ROOT / "DB" / "Memory" / "SST39SF010A" / "tests",
}
BATCH2_TEST_ROOTS = {
    "74HC00": ROOT / "DB" / "74xx" / "74HC00" / "tests",
    "74HC04": ROOT / "DB" / "74xx" / "74HC04" / "tests",
    "74HC21": ROOT / "DB" / "74xx" / "74HC21" / "tests",
    "74HC32": ROOT / "DB" / "74xx" / "74HC32" / "tests",
    "74HC74": ROOT / "DB" / "74xx" / "74HC74" / "tests",
    "74HC86": ROOT / "DB" / "74xx" / "74HC86" / "tests",
    "74HC157": ROOT / "DB" / "74xx" / "74HC157" / "tests",
    "74HC161": ROOT / "DB" / "74xx" / "74HC161" / "tests",
    "74HC164": ROOT / "DB" / "74xx" / "74HC164" / "tests",
    "74HC245": ROOT / "DB" / "74xx" / "74HC245" / "tests",
    "74HC283": ROOT / "DB" / "74xx" / "74HC283" / "tests",
    "74HC541": ROOT / "DB" / "74xx" / "74HC541" / "tests",
    "74HC574": ROOT / "DB" / "74xx" / "74HC574" / "tests",
    "74HC688": ROOT / "DB" / "74xx" / "74HC688" / "tests",
    "62256": ROOT / "DB" / "Memory" / "62256" / "tests",
    "AS6C62256": ROOT / "DB" / "Memory" / "AS6C62256" / "tests",
    "AT28C256": ROOT / "DB" / "Memory" / "AT28C256" / "tests",
    "SST39SF010A": ROOT / "DB" / "Memory" / "SST39SF010A" / "tests",
}
TASK3_REPRESENTATIVE_PARTS = ("74HC00", "74HC04", "74HC32")
RV8GR_EXECUTED_PARTS = set(TASK3_REPRESENTATIVE_PARTS) | set(TARGETED_TRUTH_TEST_ROOTS) | {"74HC157"}
RV8GR_REQUIRED_PACKAGE_FILES = (
    "definition/definition.json",
    "simulation/model.py",
    "simulation/model.v",
    "simulation/model.json",
    "simulation/netlist.json",
    "symbol/dip.json",
    "generated/artifacts.json",
    "tests/truth_table.json",
    "tests/timing.json",
    "tests/tri_state.json",
    "tests/bus_fight.json",
    "tests/propagation.json",
)
MEMORY_ADDR_PINS = {
    0: 10,
    1: 9,
    2: 8,
    3: 7,
    4: 6,
    5: 5,
    6: 4,
    7: 3,
    8: 25,
    9: 24,
    10: 21,
    11: 23,
    12: 2,
    13: 26,
    14: 1,
}
MEMORY_DQ_PINS = [11, 12, 13, 15, 16, 17, 18, 19]


def load_record(part: str, test_type: str):
    return json.loads((SEED_TEST_ROOTS[part] / f"{test_type}.json").read_text(encoding="utf-8"))


def load_batch2_record(part: str, test_type: str):
    return json.loads((BATCH2_TEST_ROOTS[part] / f"{test_type}.json").read_text(encoding="utf-8"))


def load_targeted_record(part: str, test_type: str):
    return json.loads((TARGETED_TRUTH_TEST_ROOTS[part] / f"{test_type}.json").read_text(encoding="utf-8"))


def load_definition(part: str):
    group = "Memory" if part in {"62256", "AS6C62256", "AT28C256", "SST39SF010A"} else "74xx"
    path = ROOT / "DB" / group / part / "definition" / "definition.json"
    return json.loads(path.read_text(encoding="utf-8"))


def set_byte(chip, pins, value: int) -> None:
    for bit, pin in enumerate(pins):
        chip.set_input(pin, (value >> bit) & 1)


def get_byte(chip, pins) -> int:
    return sum((1 if chip.read(pin) == 1 else 0) << bit for bit, pin in enumerate(pins))


def eval_chip(chip) -> None:
    chip.update()
    chip.commit()


def set_memory_addr(chip, value: int) -> None:
    for bit, pin in MEMORY_ADDR_PINS.items():
        chip.set_input(pin, (value >> bit) & 1)


def test_seed_truth_table_records_execute_against_python_models():
    for part, executor in {
        "74HC157": _execute_74hc157_truth,
        "74HC161": _execute_74hc161_truth,
        "74HC245": _execute_74hc245_truth,
        "74HC574": _execute_74hc574_truth,
        "AT28C256": _execute_at28c256_truth,
    }.items():
        record = load_record(part, "truth_table")
        assert record["applicable"] is True
        executed = executor(record)
        expected = {item["name"] for item in record["vectors"]}
        assert executed == expected, part


def test_seed_timing_and_propagation_records_match_definition_metadata():
    expected_delays = {
        "74HC157": {18},
        "74HC161": {22},
        "74HC245": {12},
        "74HC574": {20},
        "AT28C256": {70},
    }
    for part, delays in expected_delays.items():
        timing = load_record(part, "timing")
        propagation = load_record(part, "propagation")
        assert timing["part"] == part
        assert propagation["part"] == part
        if propagation["applicable"]:
            assert {item["expect_delay_ns"] for item in propagation["checks"]} == delays


def test_seed_tristate_and_bus_fight_records_are_explicit():
    for part in SEED_TEST_ROOTS:
        tri_state = load_record(part, "tri_state")
        bus_fight = load_record(part, "bus_fight")
        assert tri_state["part"] == part
        assert bus_fight["part"] == part
        assert isinstance(tri_state["applicable"], bool)
        assert isinstance(bus_fight["applicable"], bool)
        if not tri_state["applicable"]:
            assert tri_state["reason"]
        if not bus_fight["applicable"]:
            assert bus_fight["reason"]


def test_all_truth_records_declare_edge_criteria():
    allowed_clocking = {
        "level_sensitive",
        "edge_sensitive",
        "control_edge_or_level_sensitive",
    }
    for path in sorted((ROOT / "DB").glob("*/*/tests/truth_table.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        criteria = record.get("edge_criteria")
        assert isinstance(criteria, dict), path
        assert criteria.get("clocking") in allowed_clocking, path
        assert criteria.get("trigger_edge") in {"none", "rising", "falling", "WE_control"}, path
        assert isinstance(criteria.get("non_trigger_edge"), str) and criteria["non_trigger_edge"], path
        assert isinstance(criteria.get("notes"), str) and criteria["notes"], path


def test_task3_representative_batch2_truth_records_execute_against_python_models():
    executors = {
        "74HC00": _execute_74hc00_truth,
        "74HC04": _execute_74hc04_truth,
        "74HC32": _execute_74hc32_truth,
    }
    for part, executor in executors.items():
        record = load_batch2_record(part, "truth_table")
        assert record["applicable"] is True
        assert all(item["name"] != "basic_function" for item in record["vectors"])
        assert all("inputs" in item and "expect" in item for item in record["vectors"])
        executed = executor(record)
        assert executed == {item["name"] for item in record["vectors"]}, part


def test_targeted_truth_records_are_explicit_and_execute_against_python_models():
    executors = {
        "74HC21": _execute_74hc21_truth,
        "74HC74": _execute_74hc74_truth,
        "74HC86": _execute_74hc86_truth,
        "74HC161": _execute_74hc161_truth,
        "74HC164": _execute_74hc164_truth,
        "74HC245": _execute_74hc245_truth,
        "74HC283": _execute_74hc283_truth,
        "74HC541": _execute_74hc541_truth,
        "74HC574": _execute_74hc574_truth,
        "74HC688": _execute_74hc688_truth,
        "62256": _execute_62256_truth,
        "AS6C62256": _execute_as6c62256_truth,
        "AT28C256": _execute_at28c256_truth,
        "SST39SF010A": _execute_sst39sf010a_truth,
    }
    for part, executor in executors.items():
        record = load_targeted_record(part, "truth_table")
        assert record["applicable"] is True
        assert all(item.get("name") != "basic_function" for item in record["vectors"])
        assert all("intent" not in item for item in record["vectors"])
        assert all("inputs" in item and "expect" in item for item in record["vectors"])
        executed = executor(record)
        assert executed == {item["name"] for item in record["vectors"]}, part


def test_74hc245_direction_high_z_and_bus_fight_records_are_explicit():
    truth = load_targeted_record("74HC245", "truth_table")
    names = {item["name"] for item in truth["vectors"]}
    assert {
        "dir_high_a_to_b",
        "dir_low_b_to_a",
        "disabled_oe_high_releases_a_and_b",
        "disabled_oe_high_reverse_releases_a_and_b",
    }.issubset(names)

    bus_fight = load_targeted_record("74HC245", "bus_fight")
    checks = {item["name"]: item for item in bus_fight["checks"]}
    assert checks["external_b_driver_conflicts_with_a_to_b"]["expect"]["board_error"] == "bus_conflict"
    assert checks["external_a_driver_conflicts_with_b_to_a"]["expect"]["board_error"] == "bus_conflict"
    assert checks["oe_high_prevents_conflict_with_external_drivers"]["expect"] == {
        "board_error": "none",
        "A": "Z",
        "B": "Z",
    }


def test_seed_enable_hold_and_write_protection_vectors_are_present():
    expected = {
        "74HC161": {
            "hold_when_enp_low",
            "hold_when_ent_low",
            "no_rising_edge_holds_even_when_enabled",
            "count_resumes_on_next_rising_edge",
            "clear_priority_over_load_and_count",
            "load_then_count_from_7",
            "count_after_load_7",
        },
        "74HC245": {
            "disabled_oe_high_releases_a_and_b",
            "disabled_oe_high_reverse_releases_a_and_b",
            "reenabled_a_to_b_after_high_z",
            "direction_reversal_back_to_b_to_a",
        },
        "74HC574": {
            "hold_after_d_change",
            "clock_while_outputs_disabled_captures_5a",
            "reenabled_outputs_last_latched_value",
            "reenabled_rising_edge_latch_c3",
        },
        "62256": {
            "ce_high_prevents_write",
            "ce_high_read_keeps_previous_data",
            "we_high_prevents_write",
            "we_high_read_keeps_previous_data",
        },
        "AT28C256": {
            "ce_high_prevents_write",
            "ce_high_read_keeps_previous_data",
            "we_high_prevents_write",
            "we_high_read_keeps_previous_data",
        },
    }
    for part, names in expected.items():
        record = load_targeted_record(part, "truth_table")
        assert names.issubset({item["name"] for item in record["vectors"]}), part


def test_seed_split_records_have_python_verilog_equivalence_coverage():
    source = (ROOT / "python" / "tests" / "test_equivalence.py").read_text(encoding="utf-8")
    expected_tests = {
        "74HC161": "test_74hc161_python_matches_verilog_count_sequence",
        "74HC157": "test_74hc157_python_matches_verilog_select_and_disable",
        "74HC245": "test_74hc245_python_matches_verilog_a_to_b_and_high_z",
        "74HC574": "test_74hc574_python_matches_verilog_latch_hold_and_high_z",
        "62256": "test_62256_python_matches_verilog_write_read_and_high_z",
        "AT28C256": "test_at28c256_python_matches_verilog_write_read_and_high_z",
    }
    for part, test_name in expected_tests.items():
        assert f"def {test_name}(" in source, part


def test_seed_timing_and_propagation_records_are_not_placeholders():
    expected_delay = {
        "74HC161": 22,
        "74HC157": 18,
        "74HC245": 12,
        "74HC574": 20,
        "62256": 70,
        "AT28C256": 70,
    }
    for part, delay in expected_delay.items():
        root = TARGETED_TRUTH_TEST_ROOTS[part] if part in TARGETED_TRUTH_TEST_ROOTS else SEED_TEST_ROOTS[part]
        timing = json.loads((root / "timing.json").read_text(encoding="utf-8"))
        propagation = json.loads((root / "propagation.json").read_text(encoding="utf-8"))
        assert timing["applicable"] is True, part
        assert propagation["applicable"] is True, part
        assert timing["checks"], part
        assert propagation["checks"], part
        truth = json.loads((root / "truth_table.json").read_text(encoding="utf-8"))
        if truth["edge_criteria"]["trigger_edge"] == "rising":
            assert any(item.get("edge") == "rising" for item in timing["checks"]), part
        else:
            assert any(
                item.get("control") or item.get("type") == "memory_access" or item.get("expect_delay_ns") == delay
                for item in timing["checks"]
            ), part
        assert any(item.get("expect_delay_ns") == delay for item in propagation["checks"]), part


def test_seed_bus_fight_records_execute_against_board_errors():
    _assert_74hc245_bus_fight_records()
    _assert_seed_unidirectional_outputs_conflict_when_externally_driven()
    _assert_memory_dq_bus_conflicts_and_high_z("62256")
    _assert_memory_dq_bus_conflicts_and_high_z("AT28C256")


def test_task3_representative_batch2_records_have_datasheet_electrical_extraction():
    expected = {
        "74HC00": {"path": "A_or_B_to_Y", "typical_ns": 9, "max_ns_25c": 18, "max_ns_minus40_to_85c": 23},
        "74HC04": {"path": "A_to_Y", "typical_ns": 9, "max_ns_25c": 19, "max_ns_minus40_to_85c": 24},
        "74HC32": {"path": "A_or_B_to_Y", "typical_ns": 10, "max_ns_25c": 20, "max_ns_minus40_to_85c": 25},
    }
    for part, values in expected.items():
        definition = load_definition(part)
        timing = definition["definition_layers"]["timing"]["delay"]
        electrical = definition["definition_layers"]["electrical"]
        assert timing["status"] == "datasheet-backed"
        assert timing["conditions"]["path"] == values["path"]
        assert timing["datasheet_typical_ns"]["4.5"] == values["typical_ns"]
        assert timing["datasheet_max_ns_25c"]["4.5"] == values["max_ns_25c"]
        assert timing["datasheet_max_ns_minus40_to_85c"]["4.5"] == values["max_ns_minus40_to_85c"]
        assert electrical["recommended_operating"]["vcc_v"] == {"min": 2, "nom": 5, "max": 6}
        assert electrical["static_characteristics"]["icc_max_ua"]["6.0"] == 20
        assert electrical["static_characteristics"]["ci_max_pf"]["2.0_to_6.0"] == 10
        assert "timing" in definition["datasheet"]["sources"][0]["used_for"]
        assert "electrical" in definition["datasheet"]["sources"][0]["used_for"]


def test_rv8gr_complete_set_has_seed_package_layers_and_executable_truth_coverage():
    assert RV8GR_EXECUTED_PARTS == set(BATCH2_TEST_ROOTS)
    for part, tests_root in BATCH2_TEST_ROOTS.items():
        package_root = tests_root.parent
        for relative_path in RV8GR_REQUIRED_PACKAGE_FILES:
            assert (package_root / relative_path).exists(), (part, relative_path)

        truth = json.loads((tests_root / "truth_table.json").read_text(encoding="utf-8"))
        assert truth["applicable"] is True, part
        assert truth["vectors"], part
        assert all(
            item.get("name") != "basic_function" and "inputs" in item and "expect" in item
            for item in truth["vectors"]
        ), part

        for test_type in ("timing", "tri_state", "bus_fight", "propagation"):
            record = json.loads((tests_root / f"{test_type}.json").read_text(encoding="utf-8"))
            assert record["part"] == part
            assert isinstance(record["applicable"], bool), (part, test_type)
            if record["applicable"]:
                assert record.get("checks"), (part, test_type)
            else:
                assert record.get("reason"), (part, test_type)


def test_rv8gr_audit_report_declares_complete_set():
    audit = (ROOT / "DB" / "RV8GR_BATCH2_VERIFICATION_AUDIT.md").read_text(encoding="utf-8")
    assert "RV8GR complete set" in audit
    assert "All RV8GR Batch 2 parts now meet the seed-package record gate." in audit
    for part in BATCH2_TEST_ROOTS:
        assert f"`{part}`" in audit


def test_verilog_smoke_workflow_keeps_broad_compile_scope():
    workflow = (ROOT / ".github" / "workflows" / "verilog-smoke.yml").read_text(encoding="utf-8")
    assert "Verilog/74xx/*.v Verilog/74xx/tests/tb_74xx_smoke.v" in workflow
    assert "Verilog/Memory/*.v Verilog/Memory/tests/tb_memory_smoke.v" in workflow
    assert "find DB/74xx DB/Memory -path '*/simulation/model.v'" in workflow
    assert "/tmp/db_package_models.vvp" in workflow

    package_models = sorted((ROOT / "DB").glob("*/**/simulation/model.v"))
    assert len(package_models) >= 62
    for path in package_models:
        text = path.read_text(encoding="utf-8")
        assert re.search(r"\bmodule\s+(ttl|mem)_\w+", text), path

    memory_tb = (ROOT / "Verilog" / "Memory" / "tests" / "tb_memory_smoke.v").read_text(encoding="utf-8")
    for path in sorted((ROOT / "Verilog" / "Memory").glob("*.v")):
        match = re.search(r"\bmodule\s+(mem_\w+)", path.read_text(encoding="utf-8"))
        assert match is not None, path
        assert re.search(rf"\b{re.escape(match.group(1))}\s+\w+", memory_tb), match.group(1)


def test_split_records_generate_verilog_testbench_metadata():
    for part in SEED_TEST_ROOTS:
        truth = load_record(part, "truth_table")
        artifact = generate_component_artifacts(part)["artifacts"]["verilog_testbench"]
        assert artifact["schema"] == "db.component.generated.verilog_testbench"
        assert artifact["part"] == part
        assert artifact["module"]
        assert artifact["bench_module"] == f"tb_generated_{part.lower()}"
        assert artifact["compile"]["tool"] == "iverilog"
        assert artifact["compile"]["standard"] == "g2012"
        assert artifact["compile"]["sources"] == [f"DB/{'Memory' if part == 'AT28C256' else '74xx'}/{part}/simulation/model.v"]

        truth_metadata = artifact["split_records"]["truth_table"]
        assert truth_metadata["present"] is True
        assert truth_metadata["applicable"] is truth["applicable"]
        assert truth_metadata["vectors"] == [item["name"] for item in truth["vectors"]]

        emitted = artifact["emitted"]
        if part == "74HC157":
            assert emitted["supported"] is True
            assert emitted["kind"] == "simple_truth_table"
            assert "module tb_generated_74hc157;" in emitted["text"]
            assert "ttl_74hc157 dut" in emitted["text"]
            for vector in truth_metadata["vectors"]:
                assert f"\"{vector}\"" in emitted["text"]
        else:
            assert emitted["supported"] is False
            assert emitted["reason"]


def test_generated_74hc157_verilog_testbench_compiles_when_iverilog_is_available():
    if shutil.which("iverilog") is None:
        return

    artifact = generate_component_artifacts("74HC157")["artifacts"]["verilog_testbench"]
    assert artifact["emitted"]["supported"] is True
    with tempfile.TemporaryDirectory() as tmpdir:
        bench = Path(tmpdir) / "tb_generated_74hc157.v"
        output = Path(tmpdir) / "tb_generated_74hc157.vvp"
        bench.write_text(artifact["emitted"]["text"], encoding="utf-8")
        subprocess.run(
            [
                "iverilog",
                "-g2012",
                "-Wall",
                "-o",
                str(output),
                *artifact["compile"]["sources"],
                str(bench),
            ],
            cwd=ROOT,
            check=True,
        )
        if shutil.which("vvp") is not None:
            subprocess.run(["vvp", str(output)], cwd=ROOT, check=True)


def _execute_74hc157_truth(record) -> set[str]:
    vectors = {item["name"]: item for item in record["vectors"]}
    chip = create_chip("74HC157", "U")
    set_byte(chip, [2, 5, 11, 14], 0xA)
    set_byte(chip, [3, 6, 10, 13], 0x5)

    chip.set_input(15, 0)
    chip.set_input(1, vectors["select_a"]["inputs"]["A/B"])
    eval_chip(chip)
    assert get_byte(chip, [4, 7, 9, 12]) == 0xA

    chip.set_input(1, vectors["select_b"]["inputs"]["A/B"])
    eval_chip(chip)
    assert get_byte(chip, [4, 7, 9, 12]) == 0x5

    chip.set_input(15, vectors["disabled_low"]["inputs"]["/G"])
    eval_chip(chip)
    assert get_byte(chip, [4, 7, 9, 12]) == vectors["disabled_low"]["expect"]["Y"]
    return set(vectors)


def _execute_74hc161_truth(record) -> set[str]:
    vectors = {item["name"]: item for item in record["vectors"]}
    chip = create_chip("74HC161", "U")
    for vector in record["vectors"]:
        _apply_74hc161_inputs(chip, vector.get("inputs", {}))
        if vector.get("clock"):
            chip.clock_edge()
            chip.commit()
        else:
            eval_chip(chip)
        _assert_bus_expect(chip, [14, 13, 12, 11], vector["expect"]["Q"], vector["name"])
        assert chip.read(15) == vector["expect"]["RCO"], vector["name"]
    return set(vectors)


def _execute_74hc21_truth(record) -> set[str]:
    names = {item["name"] for item in record["vectors"]}
    for vector in record["vectors"]:
        chip = create_chip("74HC21", "U")
        gate = int(vector.get("gate", 1))
        pins = (1, 2, 4, 5, 6) if gate == 1 else (9, 10, 12, 13, 8)
        for key, pin in zip(("A", "B", "C", "D"), pins[:4]):
            chip.set_input(pin, vector["inputs"][key])
        eval_chip(chip)
        assert chip.read(pins[4]) == vector["expect"]["Y"], vector["name"]
    return names


def _execute_74hc74_truth(record) -> set[str]:
    names = {item["name"] for item in record["vectors"]}
    for vector in record["vectors"]:
        chip = create_chip("74HC74", "U")
        section = int(vector.get("section", 1))
        if section == 1:
            pins = {"/CLR": 1, "D": 2, "CLK": 3, "/PR": 4, "Q": 5, "/Q": 6}
        else:
            pins = {"/CLR": 13, "D": 12, "CLK": 11, "/PR": 10, "Q": 9, "/Q": 8}
        for name in ("/CLR", "D", "/PR"):
            chip.set_input(pins[name], vector["inputs"][name])
        if vector.get("clock"):
            chip.clock_edge(pins["CLK"])
            chip.commit()
        else:
            eval_chip(chip)
        assert chip.read(pins["Q"]) == vector["expect"]["Q"], vector["name"]
        assert chip.read(pins["/Q"]) == vector["expect"]["/Q"], vector["name"]
    return names


def _execute_74hc86_truth(record) -> set[str]:
    names = {item["name"] for item in record["vectors"]}
    chip = create_chip("74HC86", "U")
    for vector in record["vectors"]:
        chip.set_input(1, vector["inputs"]["A"])
        chip.set_input(2, vector["inputs"]["B"])
        eval_chip(chip)
        assert chip.read(3) == vector["expect"]["Y"], vector["name"]
    return names


def _execute_74hc164_truth(record) -> set[str]:
    vectors = {item["name"]: item for item in record["vectors"]}
    chip = create_chip("74HC164", "U")
    q_pins = [3, 4, 5, 6, 10, 11, 12, 13]
    for vector in record["vectors"]:
        inputs = vector["inputs"]
        for name, pin in (("/CLR", 9), ("A", 1), ("B", 2)):
            if name in inputs:
                chip.set_input(pin, inputs[name])
        if vector.get("clock"):
            chip.clock_edge(8)
            chip.commit()
        else:
            eval_chip(chip)
        assert get_byte(chip, q_pins) == int(vector["expect"]["Q"], 16), vector["name"]
    return set(vectors)


def _execute_74hc245_truth(record) -> set[str]:
    names = {item["name"] for item in record["vectors"]}
    for vector in record["vectors"]:
        chip = create_chip("74HC245", "U")
        inputs = vector.get("inputs", {})
        if "A" in inputs:
            set_byte(chip, [2, 3, 4, 5, 6, 7, 8, 9], int(inputs["A"], 16))
        if "B" in inputs:
            set_byte(chip, [18, 17, 16, 15, 14, 13, 12, 11], int(inputs["B"], 16))
        chip.set_input(1, inputs["DIR"])
        chip.set_input(19, inputs["/OE"])
        eval_chip(chip)
        expect = vector["expect"]
        if expect.get("A") == "Z":
            _assert_all_z(chip, [2, 3, 4, 5, 6, 7, 8, 9], vector["name"])
        elif "A" in expect:
            assert get_byte(chip, [2, 3, 4, 5, 6, 7, 8, 9]) == int(expect["A"], 16), vector["name"]
        if expect.get("B") == "Z":
            _assert_all_z(chip, [18, 17, 16, 15, 14, 13, 12, 11], vector["name"])
        elif "B" in expect:
            assert get_byte(chip, [18, 17, 16, 15, 14, 13, 12, 11]) == int(expect["B"], 16), vector["name"]
    return names


def _execute_74hc283_truth(record) -> set[str]:
    names = {item["name"] for item in record["vectors"]}
    chip = create_chip("74HC283", "U")
    for vector in record["vectors"]:
        set_byte(chip, [5, 3, 14, 12], int(vector["inputs"]["A"], 16))
        set_byte(chip, [6, 2, 15, 11], int(vector["inputs"]["B"], 16))
        chip.set_input(7, vector["inputs"]["Cin"])
        eval_chip(chip)
        assert get_byte(chip, [4, 1, 13, 10]) == int(vector["expect"]["S"], 16), vector["name"]
        assert chip.read(9) == vector["expect"]["Cout"], vector["name"]
    return names


def _execute_74hc541_truth(record) -> set[str]:
    names = {item["name"] for item in record["vectors"]}
    chip = create_chip("74HC541", "U")
    a_pins = [2, 3, 4, 5, 6, 7, 8, 9]
    y_pins = [18, 17, 16, 15, 14, 13, 12, 11]
    for vector in record["vectors"]:
        inputs = vector["inputs"]
        chip.set_input(1, inputs["/OE1"])
        chip.set_input(19, inputs["/OE2"])
        set_byte(chip, a_pins, int(inputs["A"], 16))
        eval_chip(chip)
        if vector["expect"]["Y"] == "Z":
            _assert_all_z(chip, y_pins, vector["name"])
        else:
            assert get_byte(chip, y_pins) == int(vector["expect"]["Y"], 16), vector["name"]
    return names


def _execute_74hc574_truth(record) -> set[str]:
    vectors = {item["name"]: item for item in record["vectors"]}
    chip = create_chip("74HC574", "U")
    for vector in record["vectors"]:
        inputs = vector.get("inputs", {})
        if "/OE" in inputs:
            chip.set_input(1, inputs["/OE"])
        if "D" in inputs:
            set_byte(chip, [2, 3, 4, 5, 6, 7, 8, 9], int(inputs["D"], 16))
        if vector.get("clock"):
            chip.clock_edge()
            chip.commit()
        else:
            eval_chip(chip)
        q_pins = [19, 18, 17, 16, 15, 14, 13, 12]
        if vector["expect"]["Q"] == "Z":
            _assert_all_z(chip, q_pins, vector["name"])
        else:
            assert get_byte(chip, q_pins) == int(vector["expect"]["Q"], 16), vector["name"]
    return set(vectors)


def _execute_74hc688_truth(record) -> set[str]:
    names = {item["name"] for item in record["vectors"]}
    chip = create_chip("74HC688", "U")
    p_pins = [2, 4, 6, 8, 19, 17, 15, 13]
    q_pins = [3, 5, 7, 9, 18, 16, 14, 12]
    for vector in record["vectors"]:
        chip.set_input(1, vector["inputs"]["/OE"])
        set_byte(chip, p_pins, int(vector["inputs"]["P"], 16))
        set_byte(chip, q_pins, int(vector["inputs"]["Q"], 16))
        eval_chip(chip)
        assert chip.read(11) == vector["expect"]["/P=Q"], vector["name"]
    return names


def _execute_at28c256_truth(record) -> set[str]:
    chip = create_chip("AT28C256", "ROM")
    return _execute_memory_truth(chip, record)


def _execute_62256_truth(record) -> set[str]:
    chip = create_chip("62256", "RAM")
    return _execute_memory_truth(chip, record)


def _execute_as6c62256_truth(record) -> set[str]:
    chip = create_chip("AS6C62256", "RAM")
    return _execute_memory_truth(chip, record)


def _execute_sst39sf010a_truth(record) -> set[str]:
    chip = create_chip("SST39SF010A", "FLASH")
    return _execute_memory_truth(chip, record)


def _execute_memory_truth(chip, record) -> set[str]:
    names = {item["name"] for item in record["vectors"]}
    for vector in record["vectors"]:
        inputs = vector.get("inputs", {})
        if "A" in inputs:
            _set_memory_addr_by_name(chip, int(inputs["A"], 16))
        for name in ("/CE", "/OE", "/WE"):
            if name in inputs:
                chip.set_input(name, inputs[name])
        if "DQ" in inputs:
            _set_memory_dq_by_name(chip, int(inputs["DQ"], 16))
        eval_chip(chip)
        expect = vector["expect"]
        if expect.get("DQ") == "Z":
            _assert_memory_dq_z(chip, vector["name"])
        elif "DQ" in expect:
            assert _get_memory_dq_by_name(chip) == int(expect["DQ"], 16), vector["name"]
    return names


def _assert_74hc245_bus_fight_records() -> None:
    record = load_targeted_record("74HC245", "bus_fight")
    checks = {item["name"]: item for item in record["checks"]}

    assert _board_has_driver_conflict(_configured_74hc245_board("a_to_b_conflict")), checks
    assert _board_has_driver_conflict(_configured_74hc245_board("b_to_a_conflict")), checks

    board = _configured_74hc245_board("disabled_no_conflict")
    assert board.errors() == []
    chip = board.chips["U1"]
    _assert_all_drive_z(chip, [2, 3, 4, 5, 6, 7, 8, 9], "74HC245 disabled A high-Z")
    _assert_all_drive_z(chip, [18, 17, 16, 15, 14, 13, 12, 11], "74HC245 disabled B high-Z")


def _configured_74hc245_board(mode: str) -> Board:
    board = Board()
    chip = board.add_chip("U1", create_chip("74HC245", "U1"))
    a_pins = [2, 3, 4, 5, 6, 7, 8, 9]
    b_pins = [18, 17, 16, 15, 14, 13, 12, 11]
    for index, (a_pin, b_pin) in enumerate(zip(a_pins, b_pins)):
        board.attach(f"bus:A[{index}]", chip, a_pin)
        board.attach(f"bus:B[{index}]", chip, b_pin)
    if mode == "a_to_b_conflict":
        set_byte(chip, a_pins, 0x00)
        chip.set_input(1, 1)
        chip.set_input(19, 0)
        eval_chip(chip)
        _attach_byte_sources(board, "bus:B", 0xFF)
    elif mode == "b_to_a_conflict":
        set_byte(chip, b_pins, 0x00)
        chip.set_input(1, 0)
        chip.set_input(19, 0)
        eval_chip(chip)
        _attach_byte_sources(board, "bus:A", 0xFF)
    elif mode == "disabled_no_conflict":
        set_byte(chip, a_pins, 0x00)
        set_byte(chip, b_pins, 0xFF)
        chip.set_input(1, 1)
        chip.set_input(19, 1)
        eval_chip(chip)
        _attach_byte_sources(board, "bus:A", 0x00)
        _attach_byte_sources(board, "bus:B", 0xFF)
    else:
        raise AssertionError(f"unknown 74HC245 bus mode {mode}")
    return board


def _assert_seed_unidirectional_outputs_conflict_when_externally_driven() -> None:
    reg = create_chip("74HC574", "U1")
    board = Board()
    board.add_chip("U1", reg)
    q_pins = [19, 18, 17, 16, 15, 14, 13, 12]
    for index, pin in enumerate(q_pins):
        board.attach(f"bus:Q[{index}]", reg, pin)
    reg.set_input(1, 0)
    set_byte(reg, [2, 3, 4, 5, 6, 7, 8, 9], 0x00)
    reg.clock_edge()
    reg.commit()
    _attach_byte_sources(board, "bus:Q", 0xFF)
    assert _board_has_driver_conflict(board)

    disabled = create_chip("74HC574", "U2")
    disabled_board = Board()
    disabled_board.add_chip("U2", disabled)
    for index, pin in enumerate(q_pins):
        disabled_board.attach(f"bus:QZ[{index}]", disabled, pin)
    disabled.set_input(1, 1)
    set_byte(disabled, [2, 3, 4, 5, 6, 7, 8, 9], 0x00)
    disabled.clock_edge()
    disabled.commit()
    _attach_byte_sources(disabled_board, "bus:QZ", 0xFF)
    assert disabled_board.errors() == []


def _assert_memory_dq_bus_conflicts_and_high_z(part: str) -> None:
    chip = create_chip(part, "MEM")
    board = Board()
    board.add_chip("MEM", chip)
    prefix = _memory_dq_prefix(chip)
    for bit_index in range(8):
        board.attach(f"bus:DQ[{bit_index}]", chip, f"{prefix}{bit_index}")

    _set_memory_addr_by_name(chip, 0x0123)
    for name, value in (("/CE", 0), ("/WE", 0), ("/OE", 1)):
        chip.set_input(name, value)
    _set_memory_dq_by_name(chip, 0x00)
    eval_chip(chip)
    for name, value in (("/WE", 1), ("/OE", 0)):
        chip.set_input(name, value)
    eval_chip(chip)
    _attach_byte_sources(board, "bus:DQ", 0xFF)
    assert _board_has_driver_conflict(board), part

    high_z_chip = create_chip(part, "MEMZ")
    high_z_board = Board()
    high_z_board.add_chip("MEMZ", high_z_chip)
    prefix = _memory_dq_prefix(high_z_chip)
    for bit_index in range(8):
        high_z_board.attach(f"bus:DQZ[{bit_index}]", high_z_chip, f"{prefix}{bit_index}")
    _set_memory_addr_by_name(high_z_chip, 0x0123)
    for name, value in (("/CE", 1), ("/WE", 1), ("/OE", 0)):
        high_z_chip.set_input(name, value)
    eval_chip(high_z_chip)
    _attach_byte_sources(high_z_board, "bus:DQZ", 0xFF)
    assert high_z_board.errors() == [], part


def _attach_byte_sources(board: Board, bus_name: str, value: int) -> None:
    for bit_index in range(8):
        try:
            board.logic_source(f"{bus_name}:external:{bit_index}", f"{bus_name}[{bit_index}]", (value >> bit_index) & 1)
        except BusConflictError:
            pass


def _board_has_driver_conflict(board: Board) -> bool:
    return any(error["type"] == "driver_conflict" for error in board.errors())


def _memory_addr_width(chip) -> int:
    return 17 if getattr(chip, "part", "") == "SST39SF010A" else 15


def _memory_dq_prefix(chip) -> str:
    return "DQ" if getattr(chip, "part", "") == "SST39SF010A" else "I/O"


def _set_memory_addr_by_name(chip, value: int) -> None:
    for bit_index in range(_memory_addr_width(chip)):
        chip.set_input(f"A{bit_index}", (value >> bit_index) & 1)


def _set_memory_dq_by_name(chip, value: int) -> None:
    prefix = _memory_dq_prefix(chip)
    for bit_index in range(8):
        chip.set_input(f"{prefix}{bit_index}", (value >> bit_index) & 1)


def _get_memory_dq_by_name(chip) -> int:
    prefix = _memory_dq_prefix(chip)
    return sum((1 if chip.read(f"{prefix}{bit_index}") == 1 else 0) << bit_index for bit_index in range(8))


def _assert_memory_dq_z(chip, name: str) -> None:
    prefix = _memory_dq_prefix(chip)
    for bit_index in range(8):
        assert chip.read(f"{prefix}{bit_index}") == Z, name


def _apply_74hc161_inputs(chip, inputs: dict) -> None:
    pin_map = {"/CLR": 1, "/LD": 9, "ENP": 7, "ENT": 10}
    for name, pin in pin_map.items():
        if name in inputs:
            chip.set_input(pin, inputs[name])
    if "D" in inputs:
        set_byte(chip, [3, 4, 5, 6], int(inputs["D"], 16))


def _assert_bus_expect(chip, pins, expected, name: str) -> None:
    if expected == "Z":
        _assert_all_z(chip, pins, name)
    else:
        assert get_byte(chip, pins) == int(expected, 16), name


def _assert_all_z(chip, pins, name: str) -> None:
    for pin in pins:
        assert chip.read(pin) == Z, name


def _assert_all_drive_z(chip, pins, name: str) -> None:
    for pin in pins:
        assert chip.pin(pin).value == Z, name


def _execute_74hc00_truth(record) -> set[str]:
    vectors = {item["name"]: item for item in record["vectors"]}
    chip = create_chip("74HC00", "U")
    for item in vectors.values():
        chip.set_input(1, item["inputs"]["A"])
        chip.set_input(2, item["inputs"]["B"])
        eval_chip(chip)
        assert chip.read(3) == item["expect"]["Y"]
    return set(vectors)


def _execute_74hc04_truth(record) -> set[str]:
    vectors = {item["name"]: item for item in record["vectors"]}
    chip = create_chip("74HC04", "U")
    for item in vectors.values():
        chip.set_input(1, item["inputs"]["A"])
        eval_chip(chip)
        assert chip.read(2) == item["expect"]["Y"]
    return set(vectors)


def _execute_74hc32_truth(record) -> set[str]:
    vectors = {item["name"]: item for item in record["vectors"]}
    chip = create_chip("74HC32", "U")
    for item in vectors.values():
        chip.set_input(1, item["inputs"]["A"])
        chip.set_input(2, item["inputs"]["B"])
        eval_chip(chip)
        assert chip.read(3) == item["expect"]["Y"]
    return set(vectors)


def run_all():
    test_seed_truth_table_records_execute_against_python_models()
    test_seed_timing_and_propagation_records_match_definition_metadata()
    test_seed_tristate_and_bus_fight_records_are_explicit()
    test_all_truth_records_declare_edge_criteria()
    test_task3_representative_batch2_truth_records_execute_against_python_models()
    test_targeted_truth_records_are_explicit_and_execute_against_python_models()
    test_74hc245_direction_high_z_and_bus_fight_records_are_explicit()
    test_seed_enable_hold_and_write_protection_vectors_are_present()
    test_seed_split_records_have_python_verilog_equivalence_coverage()
    test_seed_timing_and_propagation_records_are_not_placeholders()
    test_seed_bus_fight_records_execute_against_board_errors()
    test_task3_representative_batch2_records_have_datasheet_electrical_extraction()
    test_rv8gr_complete_set_has_seed_package_layers_and_executable_truth_coverage()
    test_rv8gr_audit_report_declares_complete_set()
    test_verilog_smoke_workflow_keeps_broad_compile_scope()
    test_split_records_generate_verilog_testbench_metadata()
    test_generated_74hc157_verilog_testbench_compiles_when_iverilog_is_available()


if __name__ == "__main__":
    run_all()
    print("Components generated split-record tests passed")
