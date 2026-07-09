"""Library circuit proof checks."""

from __future__ import annotations

import json
from pathlib import Path
import random

from chiplib import create_chip


ROOT = Path(__file__).resolve().parents[2]
RING_COUNTER = ROOT / "Lib" / "Circuits" / "RV8GR_RingCounter"
PC16 = ROOT / "Lib" / "Circuits" / "RV8GR_PC16"
RANDOM_PUSH_SEED = 0x8C16


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def random_push_intervals_ms(profile: dict) -> list[int]:
    rng = random.Random(profile["seed"])
    return [rng.randint(0, profile["max_interval_ms"]) for _ in range(profile["ticks"])]


def ring_outputs(state: int) -> dict[str, int]:
    return {
        "T0": state & 1,
        "T1": (state >> 1) & 1,
        "T2": (state >> 2) & 1,
    }


def ring_clock(state: int) -> int:
    q0 = state & 1
    q1 = (state >> 1) & 1
    serial = int((not q0) and (not q1))
    return ((state << 1) & 0xFE) | serial


def pc16_step(state: int, *, rst: int = 1, pc_ld: int = 1, pc_inc: int = 1, pg: int = 0, irl: int = 0, clock: bool = True) -> int:
    if rst == 0:
        return 0
    if not clock:
        return state & 0xFFFF
    if pc_ld == 0:
        return ((pg & 0xFF) << 8) | (irl & 0xFF)
    if pc_inc:
        return (state + 1) & 0xFFFF
    return state & 0xFFFF


def set_nibble(chip, value: int) -> None:
    for bit, pin in enumerate([3, 4, 5, 6]):
        chip.set_input(pin, (value >> bit) & 1)


def read_nibble(chip) -> int:
    return sum((1 if chip.read(pin) == 1 else 0) << bit for bit, pin in enumerate([14, 13, 12, 11]))


class PC16Components:
    def __init__(self) -> None:
        self.chips = [create_chip("74HC161", f"U{index}") for index in range(1, 5)]
        self.pg = 0
        self.irl = 0
        self.rst = 1
        self.pc_ld = 1
        self.pc_inc = 1
        self.apply_inputs()

    def apply_inputs(self) -> None:
        load_values = [self.irl & 0xF, (self.irl >> 4) & 0xF, self.pg & 0xF, (self.pg >> 4) & 0xF]
        for index, chip in enumerate(self.chips):
            chip.set_input(1, self.rst)
            chip.set_input(9, self.pc_ld)
            chip.set_input(7, self.pc_inc)
            set_nibble(chip, load_values[index])
        ent = self.pc_inc
        for chip in self.chips:
            chip.set_input(10, ent)
            chip.update()
            chip.commit()
            ent = chip.read(15)

    def set_controls(self, *, rst: int = 1, pc_ld: int = 1, pc_inc: int = 1, pg: int = 0, irl: int = 0) -> None:
        self.rst = rst
        self.pc_ld = pc_ld
        self.pc_inc = pc_inc
        self.pg = pg
        self.irl = irl
        self.apply_inputs()

    def clock(self) -> None:
        self.apply_inputs()
        for chip in self.chips:
            chip.clock_edge()
        for chip in self.chips:
            chip.commit()
        self.apply_inputs()

    def read_pc(self) -> int:
        return sum(read_nibble(chip) << (4 * index) for index, chip in enumerate(self.chips))


def test_rv8gr_ring_counter_package_shape():
    circuit = load_json(RING_COUNTER / "circuit.json")
    proof = load_json(RING_COUNTER / "tests" / "ring_counter.json")

    assert circuit["schema"] == "components.lib.circuit"
    assert circuit["id"] == "rv8gr_ring_counter"
    assert proof["circuit"] == circuit["id"]
    assert (RING_COUNTER / "README.md").exists()

    chip_parts = {chip["part"] for chip in circuit["chips"]}
    assert chip_parts == {"74HC164", "74HC04"}
    for part in chip_parts:
        assert list((ROOT / "DB").glob(f"*/*{part}/definition/definition.json")), part

    outputs = {port["name"] for port in circuit["ports"] if port["direction"] == "output"}
    assert {"T0", "T1", "T2"} <= outputs
    assert circuit["behavior"]["serial_input"] == "NOT(T0) AND NOT(T1)"


def test_rv8gr_ring_counter_sequence_and_reset():
    proof = load_json(RING_COUNTER / "tests" / "ring_counter.json")
    state = 0
    assert ring_outputs(state) == proof["reset"]["expect"]

    for vector in proof["sequence_after_reset"]:
        state = ring_clock(state)
        outputs = ring_outputs(state)
        assert outputs == vector["expect"], vector
        assert sum(outputs.values()) == 1, vector


def test_rv8gr_ring_counter_ignores_non_rising_edges():
    state = ring_clock(0)
    before = ring_outputs(state)
    # Falling/no-edge behavior is a hold for this circuit model.
    after = ring_outputs(state)
    assert after == before


def test_rv8gr_ring_counter_illegal_lower_states_recover():
    proof = load_json(RING_COUNTER / "tests" / "ring_counter.json")
    recovery = proof["illegal_lower_state_recovery"]
    normal = {tuple(item[name] for name in ("T0", "T1", "T2")) for item in recovery["normal_states"]}

    for illegal in recovery["states"]:
        state = illegal["T0"] | (illegal["T1"] << 1) | (illegal["T2"] << 2)
        reached = False
        for _ in range(recovery["max_clocks"]):
            state = ring_clock(state)
            outputs = ring_outputs(state)
            if tuple(outputs[name] for name in ("T0", "T1", "T2")) in normal:
                reached = True
                break
        assert reached, illegal


def test_rv8gr_ring_counter_sequence_executes_with_component_models():
    proof = load_json(RING_COUNTER / "tests" / "ring_counter.json")
    shift = create_chip("74HC164", "U8")
    inv = create_chip("74HC04", "U24")

    def apply_feedback() -> None:
        inv.set_input(1, shift.read(3))
        inv.set_input(3, shift.read(4))
        inv.update()
        inv.commit()
        shift.set_input(1, inv.read(2))
        shift.set_input(2, inv.read(4))

    shift.set_input(9, 0)
    shift.update()
    shift.commit()
    assert {name: shift.read(pin) for name, pin in {"T0": 3, "T1": 4, "T2": 5}.items()} == proof["reset"]["expect"]

    shift.set_input(9, 1)
    for vector in proof["sequence_after_reset"]:
        apply_feedback()
        shift.clock_edge(8)
        shift.commit()
        assert {name: shift.read(pin) for name, pin in {"T0": 3, "T1": 4, "T2": 5}.items()} == vector["expect"]


def test_rv8gr_pc16_package_shape():
    circuit = load_json(PC16 / "circuit.json")
    proof = load_json(PC16 / "tests" / "pc16.json")

    assert circuit["schema"] == "components.lib.circuit"
    assert circuit["id"] == "rv8gr_pc16"
    assert proof["circuit"] == circuit["id"]
    assert (PC16 / "README.md").exists()

    chips = {chip["ref"]: chip["part"] for chip in circuit["chips"]}
    assert chips == {"U1": "74HC161", "U2": "74HC161", "U3": "74HC161", "U4": "74HC161"}
    assert list((ROOT / "DB").glob("*/74HC161/definition/definition.json"))

    wiring = {item["net"]: item["connections"] for item in circuit["wiring"]}
    assert "U1.15" in wiring["RCO0"] and "U2.10" in wiring["RCO0"]
    assert "U2.15" in wiring["RCO1"] and "U3.10" in wiring["RCO1"]
    assert "U3.15" in wiring["RCO2"] and "U4.10" in wiring["RCO2"]
    assert circuit["behavior"]["priority"] == ["/RST", "/PC_LD", "count when PC_INC=1", "hold"]


def test_rv8gr_pc16_vectors_execute():
    proof = load_json(PC16 / "tests" / "pc16.json")
    assert pc16_step(0xBEEF, rst=0) == int(proof["reset"]["expect"]["PC"], 16)

    for vector in proof["vectors"]:
        result = pc16_step(
            int(vector["start"], 16),
            pc_inc=vector["pc_inc"],
            pc_ld=vector["pc_ld"],
            pg=int(vector.get("pg", "0x00"), 16),
            irl=int(vector.get("irl", "0x00"), 16),
            clock=vector["clock"],
        )
        assert result == int(vector["expect"], 16), vector


def test_rv8gr_pc16_vectors_execute_with_component_models():
    proof = load_json(PC16 / "tests" / "pc16.json")
    circuit = PC16Components()
    circuit.set_controls(rst=0)
    assert circuit.read_pc() == int(proof["reset"]["expect"]["PC"], 16)

    for vector in proof["vectors"]:
        circuit = PC16Components()
        circuit.set_controls(rst=0)
        circuit.set_controls(rst=1, pc_ld=0, pg=(int(vector["start"], 16) >> 8), irl=int(vector["start"], 16) & 0xFF)
        circuit.clock()
        circuit.set_controls(
            rst=1,
            pc_ld=vector["pc_ld"],
            pc_inc=vector["pc_inc"],
            pg=int(vector.get("pg", "0x00"), 16),
            irl=int(vector.get("irl", "0x00"), 16),
        )
        if vector["clock"]:
            circuit.clock()
        else:
            circuit.apply_inputs()
        assert circuit.read_pc() == int(vector["expect"], 16), vector


def test_rv8gr_pc16_phase_gating_matches_t0_t1_only():
    pc = 0
    phases = [
        {"T0": 1, "T1": 0, "T2": 0},
        {"T0": 0, "T1": 1, "T2": 0},
        {"T0": 0, "T1": 0, "T2": 1},
    ]
    expected = [1, 2, 2]
    for phase, expect in zip(phases, expected):
        pc_inc = int(bool(phase["T0"] or phase["T1"]))
        pc = pc16_step(pc, pc_inc=pc_inc, pc_ld=1, clock=True)
        assert pc == expect, phase


def test_rv8gr_pc16_clock_profiles_are_functionally_stable():
    profiles = load_json(PC16 / "tests" / "pc16.json")["clock_profiles"]
    for profile in profiles:
        circuit = PC16Components()
        circuit.set_controls(rst=0)
        circuit.set_controls(rst=1, pc_ld=1, pc_inc=1)
        steps = 12 if profile["name"] == "push_switch_single_step" else 256
        for expected in range(1, steps + 1):
            circuit.clock()
            assert circuit.read_pc() == expected, profile


def test_rv8gr_pc16_random_push_switch_profile_counts_one_per_press():
    profile = next(item for item in load_json(PC16 / "tests" / "pc16.json")["clock_profiles"] if item["name"] == "push_switch_random_100")
    assert profile["seed"] == RANDOM_PUSH_SEED
    intervals = random_push_intervals_ms(profile)
    assert len(intervals) == 100
    assert all(0 <= interval <= 500 for interval in intervals)
    assert len(set(intervals)) > 1

    circuit = PC16Components()
    circuit.set_controls(rst=0)
    circuit.set_controls(rst=1, pc_ld=1, pc_inc=1)
    for expected, _interval_ms in enumerate(intervals, start=1):
        circuit.clock()
        assert circuit.read_pc() == expected, profile


def test_rv8gr_ring_counter_clock_profiles_are_functionally_stable():
    profiles = load_json(RING_COUNTER / "tests" / "ring_counter.json")["clock_profiles"]
    expected_sequence = [
        {"T0": 1, "T1": 0, "T2": 0},
        {"T0": 0, "T1": 1, "T2": 0},
        {"T0": 0, "T1": 0, "T2": 1},
    ]
    for profile in profiles:
        state = 0
        steps = 12 if profile["name"] == "push_switch_single_step" else 300
        for index in range(steps):
            state = ring_clock(state)
            assert ring_outputs(state) == expected_sequence[index % 3], profile


def test_rv8gr_ring_counter_random_push_switch_profile_advances_one_phase_per_press():
    profile = next(item for item in load_json(RING_COUNTER / "tests" / "ring_counter.json")["clock_profiles"] if item["name"] == "push_switch_random_100")
    assert profile["seed"] == RANDOM_PUSH_SEED
    intervals = random_push_intervals_ms(profile)
    assert len(intervals) == 100
    assert all(0 <= interval <= 500 for interval in intervals)
    assert len(set(intervals)) > 1

    expected_sequence = [
        {"T0": 1, "T1": 0, "T2": 0},
        {"T0": 0, "T1": 1, "T2": 0},
        {"T0": 0, "T1": 0, "T2": 1},
    ]
    state = 0
    for index, _interval_ms in enumerate(intervals):
        state = ring_clock(state)
        assert ring_outputs(state) == expected_sequence[index % 3], profile


def test_all_started_circuit_packages_have_tests():
    for circuit_path in sorted((ROOT / "Lib" / "Circuits").glob("RV8GR_*/circuit.json")):
        circuit = load_json(circuit_path)
        assert circuit["schema"] == "components.lib.circuit"
        tests = circuit.get("verification", {}).get("tests", [])
        assert tests, circuit_path
        for test in tests:
            assert (circuit_path.parent / test).exists(), (circuit_path, test)


def run_all():
    test_rv8gr_ring_counter_package_shape()
    test_rv8gr_ring_counter_sequence_and_reset()
    test_rv8gr_ring_counter_ignores_non_rising_edges()
    test_rv8gr_ring_counter_illegal_lower_states_recover()
    test_rv8gr_ring_counter_sequence_executes_with_component_models()
    test_rv8gr_pc16_package_shape()
    test_rv8gr_pc16_vectors_execute()
    test_rv8gr_pc16_vectors_execute_with_component_models()
    test_rv8gr_pc16_phase_gating_matches_t0_t1_only()
    test_rv8gr_pc16_clock_profiles_are_functionally_stable()
    test_rv8gr_pc16_random_push_switch_profile_counts_one_per_press()
    test_rv8gr_ring_counter_clock_profiles_are_functionally_stable()
    test_rv8gr_ring_counter_random_push_switch_profile_advances_one_phase_per_press()
    test_all_started_circuit_packages_have_tests()


if __name__ == "__main__":
    run_all()
    print("Components library circuit tests passed")
