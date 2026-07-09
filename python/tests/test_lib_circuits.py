"""Library circuit proof checks."""

from __future__ import annotations

import json
from pathlib import Path
import random

from chiplib import create_chip


ROOT = Path(__file__).resolve().parents[2]
RING_COUNTER = ROOT / "Lib" / "Circuits" / "RV8GR_RingCounter"
PC16 = ROOT / "Lib" / "Circuits" / "RV8GR_PC16"
ADDRESS_MUX16 = ROOT / "Lib" / "Circuits" / "RV8GR_AddressMux16"
BUS_OWNERSHIP = ROOT / "Lib" / "Circuits" / "RV8GR_BusOwnership"
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


def phase_t2(phase: str) -> int:
    return 1 if phase == "T2" else 0


def addr_mode_n_for(phase: str, src: int, str_: int) -> int:
    addr_req = int(bool(src or str_))
    return 0 if (addr_req and phase_t2(phase)) else 1


def address_mux16(pc: int, dp: int, irl: int, addr_mode_n: int) -> int:
    if addr_mode_n:
        return pc & 0xFFFF
    return ((dp & 0xFF) << 8) | (irl & 0xFF)


def memory_select_from_a15(a15: int) -> dict[str, int]:
    return {"rom_ce_n": int(bool(a15)), "ram_ce_n": int(not a15)}


def bus_controls(phase: str, src: int, str_: int) -> dict[str, int]:
    t2 = phase_t2(phase)
    addr_n = addr_mode_n_for(phase, src, str_)
    irl_oe_n = 0 if (t2 and addr_n) else 1
    buf_oe_n = 1 - irl_oe_n
    ac_buf_n = 0 if (t2 and str_) else 1
    wr_dir = 1 - ac_buf_n
    return {
        "ADDR_REQ": int(bool(src or str_)),
        "/ADDR_MODE": addr_n,
        "/IRL_OE": irl_oe_n,
        "BUF_OE_N": buf_oe_n,
        "/AC_BUF": ac_buf_n,
        "WR_DIR": wr_dir,
    }


def bus_ownership(phase: str, src: int, str_: int, a15: int, override: dict | None = None) -> dict:
    controls = bus_controls(phase, src, str_)
    controls["A15"] = int(bool(a15))
    controls.update(memory_select_from_a15(controls["A15"]))
    controls["ROM_OE_N"] = controls["WR_DIR"]
    controls["RAM_WE_N"] = controls["/AC_BUF"]

    if override:
        for name, value in override.items():
            control_name = {"ROM_CE_N": "rom_ce_n", "RAM_CE_N": "ram_ce_n"}.get(name, name)
            controls[control_name] = int(value)

    ibus_drivers: list[str] = []
    dbus_drivers: list[str] = []

    if controls["/IRL_OE"] == 0:
        ibus_drivers.append("U34")
    if controls["/AC_BUF"] == 0:
        ibus_drivers.append("U14")
    if controls["BUF_OE_N"] == 0 and controls["WR_DIR"] == 0:
        ibus_drivers.append("U7")
    if controls["BUF_OE_N"] == 0 and controls["WR_DIR"] == 1:
        dbus_drivers.append("U7")

    if controls["rom_ce_n"] == 0 and controls["ROM_OE_N"] == 0:
        dbus_drivers.append("ROM1")
    if controls["ram_ce_n"] == 0 and controls["RAM_WE_N"] == 1:
        dbus_drivers.append("RAM1")

    conflict = len(ibus_drivers) > 1 or len(dbus_drivers) > 1
    conflict = conflict or (controls["rom_ce_n"] == 0 and controls["ram_ce_n"] == 0)
    return {
        "controls": controls,
        "ibus_drivers": ibus_drivers,
        "dbus_drivers": dbus_drivers,
        "conflict": conflict,
    }


def mux157_set_nibble(chip, a_value: int, b_value: int, select: int) -> None:
    chip.set_input(15, 0)
    chip.set_input(1, select)
    for bit, a_pin, b_pin in ((0, 2, 3), (1, 5, 6), (2, 11, 10), (3, 14, 13)):
        chip.set_input(a_pin, (a_value >> bit) & 1)
        chip.set_input(b_pin, (b_value >> bit) & 1)
    chip.update()
    chip.commit()


def mux157_read_nibble(chip) -> int:
    return sum((1 if chip.read(pin) == 1 else 0) << bit for bit, pin in enumerate([4, 7, 9, 12]))


def address_mux16_components(pc: int, dp: int, irl: int, addr_mode_n: int) -> int:
    chips = {
        "U15": create_chip("74HC157", "U15"),
        "U16": create_chip("74HC157", "U16"),
        "U29": create_chip("74HC157", "U29"),
        "U30": create_chip("74HC157", "U30"),
    }
    mux157_set_nibble(chips["U15"], irl & 0xF, pc & 0xF, addr_mode_n)
    mux157_set_nibble(chips["U16"], (irl >> 4) & 0xF, (pc >> 4) & 0xF, addr_mode_n)
    mux157_set_nibble(chips["U29"], dp & 0xF, (pc >> 8) & 0xF, addr_mode_n)
    mux157_set_nibble(chips["U30"], (dp >> 4) & 0xF, (pc >> 12) & 0xF, addr_mode_n)
    return (
        mux157_read_nibble(chips["U15"])
        | (mux157_read_nibble(chips["U16"]) << 4)
        | (mux157_read_nibble(chips["U29"]) << 8)
        | (mux157_read_nibble(chips["U30"]) << 12)
    )


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


def test_rv8gr_address_mux16_package_shape():
    circuit = load_json(ADDRESS_MUX16 / "circuit.json")
    proof = load_json(ADDRESS_MUX16 / "tests" / "address_mux16.json")

    assert circuit["schema"] == "components.lib.circuit"
    assert circuit["id"] == "rv8gr_address_mux16"
    assert proof["circuit"] == circuit["id"]
    assert (ADDRESS_MUX16 / "README.md").exists()

    chips = {chip["ref"]: chip["part"] for chip in circuit["chips"]}
    assert chips == {"U15": "74HC157", "U16": "74HC157", "U29": "74HC157", "U30": "74HC157"}
    assert all(ref not in chips for ref in ("U17", "U18", "U19", "U20"))
    assert list((ROOT / "DB").glob("*/74HC157/definition/definition.json"))

    wiring = {item["net"]: item["connections"] for item in circuit["wiring"]}
    assert "U15.1" in wiring["/ADDR_MODE"] and "U30.1" in wiring["/ADDR_MODE"]
    assert circuit["behavior"]["select"].startswith("The physical select net is /ADDR_MODE")
    assert "ADDR_REQ=SRC OR STR" in circuit["behavior"]["warning"]


def test_rv8gr_address_mux16_vectors_execute():
    proof = load_json(ADDRESS_MUX16 / "tests" / "address_mux16.json")

    for vector in proof["vectors"]:
        pc = int(vector["pc"], 16)
        dp = int(vector["dp"], 16)
        irl = int(vector["irl"], 16)
        addr_n = addr_mode_n_for(vector["phase"], vector["src"], vector["str"])
        assert addr_n == vector["expect_addr_mode_n"], vector
        assert address_mux16(pc, dp, irl, addr_n) == int(vector["expect_abus"], 16), vector


def test_rv8gr_address_mux16_vectors_execute_with_component_models():
    proof = load_json(ADDRESS_MUX16 / "tests" / "address_mux16.json")

    for vector in proof["vectors"]:
        pc = int(vector["pc"], 16)
        dp = int(vector["dp"], 16)
        irl = int(vector["irl"], 16)
        addr_n = addr_mode_n_for(vector["phase"], vector["src"], vector["str"])
        assert address_mux16_components(pc, dp, irl, addr_n) == int(vector["expect_abus"], 16), vector


def test_rv8gr_address_mux16_raw_t2_does_not_select_data_address():
    proof = load_json(ADDRESS_MUX16 / "tests" / "address_mux16.json")
    immediate = next(vector for vector in proof["vectors"] if vector["name"] == "t2_no_addr_req_selects_pc_for_immediate")

    assert immediate["phase"] == "T2"
    assert immediate["src"] == 0 and immediate["str"] == 0
    addr_n = addr_mode_n_for(immediate["phase"], immediate["src"], immediate["str"])
    assert addr_n == 1
    assert address_mux16(
        int(immediate["pc"], 16),
        int(immediate["dp"], 16),
        int(immediate["irl"], 16),
        addr_n,
    ) == int(immediate["pc"], 16)


def test_rv8gr_address_mux16_a15_decode_is_complementary():
    proof = load_json(ADDRESS_MUX16 / "tests" / "address_mux16.json")

    for vector in proof["memory_select_vectors"]:
        abus = int(vector["abus"], 16)
        a15 = (abus >> 15) & 1
        select = memory_select_from_a15(a15)
        assert a15 == vector["a15"], vector
        assert select["rom_ce_n"] == vector["rom_ce_n"], vector
        assert select["ram_ce_n"] == vector["ram_ce_n"], vector
        assert select["rom_ce_n"] != select["ram_ce_n"], vector


def test_rv8gr_bus_ownership_package_shape():
    circuit = load_json(BUS_OWNERSHIP / "circuit.json")
    proof = load_json(BUS_OWNERSHIP / "tests" / "bus_ownership.json")

    assert circuit["schema"] == "components.lib.circuit"
    assert circuit["id"] == "rv8gr_bus_ownership"
    assert proof["circuit"] == circuit["id"]
    assert (BUS_OWNERSHIP / "README.md").exists()

    chips = {chip["ref"]: chip["part"] for chip in circuit["chips"]}
    assert chips == {
        "U7": "74HC245",
        "U14": "74HC541",
        "U34": "74HC541",
        "ROM1": "AT28C256",
        "RAM1": "62256",
    }
    for part in {"74HC245", "74HC541", "AT28C256", "62256"}:
        assert list((ROOT / "DB").glob(f"*/*{part}/definition/definition.json")), part

    assert "U34 and U14 both enabled on IBUS" in circuit["timing"]["unsafe_states"]
    assert circuit["behavior"]["addr_req"] == "ADDR_REQ=SRC OR STR."


def test_rv8gr_bus_ownership_phase_vectors_are_conflict_free():
    proof = load_json(BUS_OWNERSHIP / "tests" / "bus_ownership.json")

    for vector in proof["vectors"]:
        ownership = bus_ownership(vector["phase"], vector["src"], vector["str"], vector["a15"])
        assert ownership["ibus_drivers"] == vector["expect_ibus_drivers"], vector
        assert ownership["dbus_drivers"] == vector["expect_dbus_drivers"], vector
        assert ownership["conflict"] == vector["expect_conflict"], vector

        controls = ownership["controls"]
        if vector["u7_direction"] == "DBUS_TO_IBUS":
            assert controls["BUF_OE_N"] == 0 and controls["WR_DIR"] == 0, vector
        elif vector["u7_direction"] == "IBUS_TO_DBUS":
            assert controls["BUF_OE_N"] == 0 and controls["WR_DIR"] == 1, vector
        elif vector["u7_direction"] == "DISABLED":
            assert controls["BUF_OE_N"] == 1, vector
        else:
            raise AssertionError(vector)


def test_rv8gr_bus_ownership_store_disables_memory_outputs():
    proof = load_json(BUS_OWNERSHIP / "tests" / "bus_ownership.json")
    store_vectors = [vector for vector in proof["vectors"] if vector["str"] == 1]

    assert store_vectors
    for vector in store_vectors:
        ownership = bus_ownership(vector["phase"], vector["src"], vector["str"], vector["a15"])
        controls = ownership["controls"]
        assert controls["/AC_BUF"] == 0, vector
        assert controls["WR_DIR"] == 1, vector
        assert controls["ROM_OE_N"] == 1, vector
        assert controls["RAM_WE_N"] == 0, vector
        assert "U7" in ownership["dbus_drivers"], vector
        assert "ROM1" not in ownership["dbus_drivers"], vector
        assert "RAM1" not in ownership["dbus_drivers"], vector


def test_rv8gr_bus_ownership_detects_forced_conflicts():
    proof = load_json(BUS_OWNERSHIP / "tests" / "bus_ownership.json")

    for vector in proof["unsafe_control_vectors"]:
        ownership = bus_ownership("T2", 0, 0, 0, vector["override"])
        assert ownership["conflict"] == vector["expect_conflict"], vector


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
    test_rv8gr_address_mux16_package_shape()
    test_rv8gr_address_mux16_vectors_execute()
    test_rv8gr_address_mux16_vectors_execute_with_component_models()
    test_rv8gr_address_mux16_raw_t2_does_not_select_data_address()
    test_rv8gr_address_mux16_a15_decode_is_complementary()
    test_rv8gr_bus_ownership_package_shape()
    test_rv8gr_bus_ownership_phase_vectors_are_conflict_free()
    test_rv8gr_bus_ownership_store_disables_memory_outputs()
    test_rv8gr_bus_ownership_detects_forced_conflicts()
    test_all_started_circuit_packages_have_tests()


if __name__ == "__main__":
    run_all()
    print("Components library circuit tests passed")
