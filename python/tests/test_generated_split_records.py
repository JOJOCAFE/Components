"""Generated checks from component split test records."""

from __future__ import annotations

import json
from pathlib import Path
import re

from chiplib import Z, create_chip


ROOT = Path(__file__).resolve().parents[2]
SEED_TEST_ROOTS = {
    "74HC161": ROOT / "DB" / "74xx" / "74HC161" / "tests",
    "74HC157": ROOT / "DB" / "74xx" / "74HC157" / "tests",
    "74HC245": ROOT / "DB" / "74xx" / "74HC245" / "tests",
    "74HC574": ROOT / "DB" / "74xx" / "74HC574" / "tests",
    "AT28C256": ROOT / "DB" / "Memory" / "AT28C256" / "tests",
}
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


def test_verilog_smoke_workflow_keeps_broad_compile_scope():
    workflow = (ROOT / ".github" / "workflows" / "verilog-smoke.yml").read_text(encoding="utf-8")
    assert "Verilog/74xx/*.v Verilog/74xx/tests/tb_74xx_smoke.v" in workflow
    assert "Verilog/Memory/*.v Verilog/Memory/tests/tb_memory_smoke.v" in workflow

    memory_tb = (ROOT / "Verilog" / "Memory" / "tests" / "tb_memory_smoke.v").read_text(encoding="utf-8")
    for path in sorted((ROOT / "Verilog" / "Memory").glob("*.v")):
        match = re.search(r"\bmodule\s+(mem_\w+)", path.read_text(encoding="utf-8"))
        assert match is not None, path
        assert re.search(rf"\b{re.escape(match.group(1))}\s+\w+", memory_tb), match.group(1)


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
    names = {item["name"] for item in record["vectors"]}
    chip = create_chip("74HC161", "U")
    set_byte(chip, [3, 4, 5, 6], 0xC)
    for pin, value in [(1, 1), (9, 0), (7, 1), (10, 1)]:
        chip.set_input(pin, value)
    chip.clock_edge()
    chip.commit()
    assert get_byte(chip, [14, 13, 12, 11]) == 0xC

    chip.set_input(9, 1)
    chip.clock_edge()
    chip.commit()
    assert get_byte(chip, [14, 13, 12, 11]) == 0xD

    chip.set_input(7, 0)
    chip.clock_edge()
    chip.commit()
    assert get_byte(chip, [14, 13, 12, 11]) == 0xD

    chip.set_input(1, 0)
    eval_chip(chip)
    assert get_byte(chip, [14, 13, 12, 11]) == 0
    return names


def _execute_74hc245_truth(record) -> set[str]:
    vectors = {item["name"]: item for item in record["vectors"]}
    chip = create_chip("74HC245", "U")
    set_byte(chip, [2, 3, 4, 5, 6, 7, 8, 9], int(vectors["a_to_b"]["inputs"]["A"], 16))
    chip.set_input(1, vectors["a_to_b"]["inputs"]["DIR"])
    chip.set_input(19, vectors["a_to_b"]["inputs"]["/OE"])
    eval_chip(chip)
    assert get_byte(chip, [18, 17, 16, 15, 14, 13, 12, 11]) == int(vectors["a_to_b"]["expect"]["B"], 16)

    chip = create_chip("74HC245", "U")
    set_byte(chip, [18, 17, 16, 15, 14, 13, 12, 11], int(vectors["b_to_a"]["inputs"]["B"], 16))
    chip.set_input(1, vectors["b_to_a"]["inputs"]["DIR"])
    chip.set_input(19, vectors["b_to_a"]["inputs"]["/OE"])
    eval_chip(chip)
    assert get_byte(chip, [2, 3, 4, 5, 6, 7, 8, 9]) == int(vectors["b_to_a"]["expect"]["A"], 16)

    chip.set_input(19, vectors["disabled"]["inputs"]["/OE"])
    eval_chip(chip)
    assert chip.read(2) == Z
    assert chip.read(18) == Z
    return set(vectors)


def _execute_74hc574_truth(record) -> set[str]:
    names = {item["name"] for item in record["vectors"]}
    chip = create_chip("74HC574", "U")
    chip.set_input(1, 0)
    set_byte(chip, [2, 3, 4, 5, 6, 7, 8, 9], 0xA5)
    chip.clock_edge()
    chip.commit()
    assert get_byte(chip, [19, 18, 17, 16, 15, 14, 13, 12]) == 0xA5
    set_byte(chip, [2, 3, 4, 5, 6, 7, 8, 9], 0)
    eval_chip(chip)
    assert get_byte(chip, [19, 18, 17, 16, 15, 14, 13, 12]) == 0xA5
    chip.set_input(1, 1)
    eval_chip(chip)
    assert chip.read(19) == Z
    return names


def _execute_at28c256_truth(record) -> set[str]:
    names = {item["name"] for item in record["vectors"]}
    chip = create_chip("AT28C256", "ROM")
    set_memory_addr(chip, 0x2A)
    set_byte(chip, MEMORY_DQ_PINS, 0xC6)
    for pin, value in [(20, 0), (22, 1), (27, 0)]:
        chip.set_input(pin, value)
    eval_chip(chip)
    chip.set_input(22, 0)
    chip.set_input(27, 1)
    eval_chip(chip)
    assert get_byte(chip, MEMORY_DQ_PINS) == 0xC6
    chip.set_input(22, 1)
    eval_chip(chip)
    assert chip.read(11) == Z
    chip.set_input(20, 1)
    eval_chip(chip)
    assert chip.read(11) == Z
    return names


def run_all():
    test_seed_truth_table_records_execute_against_python_models()
    test_seed_timing_and_propagation_records_match_definition_metadata()
    test_seed_tristate_and_bus_fight_records_are_explicit()
    test_verilog_smoke_workflow_keeps_broad_compile_scope()


if __name__ == "__main__":
    run_all()
    print("Components generated split-record tests passed")
