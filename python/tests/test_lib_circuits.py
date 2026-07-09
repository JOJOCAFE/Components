"""Library circuit proof checks."""

from __future__ import annotations

import json
from pathlib import Path
import random

from chiplib import Z, create_chip


ROOT = Path(__file__).resolve().parents[2]
RING_COUNTER = ROOT / "Lib" / "Circuits" / "RV8GR_RingCounter"
PC16 = ROOT / "Lib" / "Circuits" / "RV8GR_PC16"
ADDRESS_MUX16 = ROOT / "Lib" / "Circuits" / "RV8GR_AddressMux16"
BUS_OWNERSHIP = ROOT / "Lib" / "Circuits" / "RV8GR_BusOwnership"
INSTRUCTION_LATCH = ROOT / "Lib" / "Circuits" / "RV8GR_InstructionLatch"
STORE_PATH = ROOT / "Lib" / "Circuits" / "RV8GR_StorePath"
DATA_PAGE_MEMORY = ROOT / "Lib" / "Circuits" / "RV8GR_DataPageMemory"
IRQ_LATCH = ROOT / "Lib" / "Circuits" / "RV8GR_IRQLatch"
ROM_DBUS_READ = ROOT / "Lib" / "Circuits" / "RV8GR_RomDbusRead"
PAGE_DATA_REGISTERS = ROOT / "Lib" / "Circuits" / "RV8GR_PageDataRegisters"
BRANCH_JUMP_CONTROL = ROOT / "Lib" / "Circuits" / "RV8GR_BranchJumpControl"
ALU_ACCUMULATOR = ROOT / "Lib" / "Circuits" / "RV8GR_AluAccumulator"
VIRTUAL_TEST_HELPERS = ROOT / "Lib" / "Circuits" / "RV8GR_VirtualTestHelpers"
FULL_CONTROL_OPCODE_SWEEP = ROOT / "Lib" / "Circuits" / "RV8GR_FullControlOpcodeSweep"
TIMING_MARGINS = ROOT / "Lib" / "Circuits" / "timing_margins.json"
RANDOM_PUSH_SEED = 0x8C16
BYTE_D_PINS = [2, 3, 4, 5, 6, 7, 8, 9]
BYTE_Q_PINS = [19, 18, 17, 16, 15, 14, 13, 12]
HC541_A_PINS = [2, 3, 4, 5, 6, 7, 8, 9]
HC541_Y_PINS = [18, 17, 16, 15, 14, 13, 12, 11]
U7_A_PINS = [2, 3, 4, 5, 6, 7, 8, 9]
U7_B_PINS = [18, 17, 16, 15, 14, 13, 12, 11]
MEMORY_ADDR_PINS = {0: 10, 1: 9, 2: 8, 3: 7, 4: 6, 5: 5, 6: 4, 7: 3, 8: 25, 9: 24, 10: 21, 11: 23, 12: 2, 13: 26, 14: 1}
MEMORY_DQ_PINS = [11, 12, 13, 15, 16, 17, 18, 19]


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


def set_byte(chip, pins: list[int], value: int) -> None:
    for bit, pin in enumerate(pins):
        chip.set_input(pin, (value >> bit) & 1)


def read_byte(chip, pins: list[int]) -> int:
    return sum((1 if chip.read(pin) == 1 else 0) << bit for bit, pin in enumerate(pins))


def set_memory_addr(chip, address: int) -> None:
    for bit, pin in MEMORY_ADDR_PINS.items():
        chip.set_input(pin, (address >> bit) & 1)


def latch_byte(chip, value: int) -> int:
    chip.set_input(1, 0)
    set_byte(chip, BYTE_D_PINS, value)
    chip.clock_edge(11)
    chip.commit()
    return read_byte(chip, BYTE_Q_PINS)


def instruction_latch_step(ir_high: int, irl: int, ibus: int, phase: str) -> tuple[int, int]:
    if phase == "T0":
        return ibus & 0xFF, irl & 0xFF
    if phase == "T1":
        return ir_high & 0xFF, ibus & 0xFF
    return ir_high & 0xFF, irl & 0xFF


def control_bits(value: int) -> dict[str, int]:
    return {
        "ALU_SUB": (value >> 7) & 1,
        "XOR_MODE": (value >> 6) & 1,
        "MUX_SEL": (value >> 5) & 1,
        "AC_WR": (value >> 4) & 1,
        "SRC": (value >> 3) & 1,
        "STR": (value >> 2) & 1,
        "BR": (value >> 1) & 1,
        "JMP": value & 1,
    }


def store_path_controls(phase: str, str_: int, a15: int) -> dict[str, int | bool]:
    ac_buf_n = 0 if (phase_t2(phase) and str_) else 1
    wr_dir = 1 - ac_buf_n
    return {
        "/AC_BUF": ac_buf_n,
        "WR_DIR": wr_dir,
        "RAM_WE_N": ac_buf_n,
        "ROM_OE_N": wr_dir,
        "ROM_CE_N": int(bool(a15)),
        "RAM_CE_N": int(not a15),
        "write": bool(phase_t2(phase) and str_ and a15),
        "rom_page_store_bus_safe": bool(phase_t2(phase) and str_ and not a15 and wr_dir == 1),
    }


def dp_load_signal(phase: str, xor_mode: int, addr_mode_n: int, ac_wr_n: int) -> int:
    return int(bool(phase_t2(phase) and xor_mode and addr_mode_n and ac_wr_n))


def data_address(dp: int, irl: int) -> int:
    return ((dp & 0xFF) << 8) | (irl & 0xFF)


def irq_latch_step(ie: int, irq_ff: int, event: str, rst: int = 1) -> tuple[int, int, str]:
    if rst == 0 or event == "reset":
        return 0, 0, "unchanged"
    if event == "ei_rising":
        ie = 1
    elif event == "irq_low":
        pass
    elif event == "irq_release_rising":
        irq_ff = 1
    elif event in {"di", "100_cpu_ticks"}:
        pass
    else:
        raise AssertionError(event)
    return ie, irq_ff, "unchanged"


def rom_image_bytes(proof: dict) -> dict[int, int]:
    return {int(address, 16): int(value, 16) for address, value in proof["rom_image"].items()}


def rom_dbus_read(address: int, rom_data: dict[int, int], *, wr_dir: int, buf_oe_n: int, force_rom_oe_n: int | None = None) -> dict:
    a15 = (address >> 15) & 1
    rom_ce_n = a15
    rom_oe_n = wr_dir if force_rom_oe_n is None else force_rom_oe_n
    rom_we_n = 1
    u7_direction = "DISABLED"
    if buf_oe_n == 0:
        u7_direction = "IBUS_TO_DBUS" if wr_dir else "DBUS_TO_IBUS"
    rom_drives_dbus = rom_ce_n == 0 and rom_oe_n == 0 and rom_we_n == 1
    u7_writes_dbus = buf_oe_n == 0 and wr_dir == 1
    ibus = rom_data.get(address & 0x7FFF) if rom_drives_dbus and u7_direction == "DBUS_TO_IBUS" else None
    return {
        "rom_ce_n": rom_ce_n,
        "rom_oe_n": rom_oe_n,
        "rom_we_n": rom_we_n,
        "u7_direction": u7_direction,
        "ibus": ibus,
        "conflict": bool(rom_drives_dbus and u7_writes_dbus),
    }


def pg_cond_n(mux_sel: int, ac_wr: int) -> int:
    ac_wr_n = 1 - int(bool(ac_wr))
    return 1 - int(bool(mux_sel and ac_wr_n))


def pg_clk_for_event(event: str, pg_cond_n_value: int) -> int:
    if event == "T2_START":
        t2_n = 0
    elif event == "T2_END":
        t2_n = 1
    else:
        raise AssertionError(event)
    return int(bool(t2_n or pg_cond_n_value))


def page_register_step(start_pg: int, ibus: int, event: str, mux_sel: int, ac_wr: int) -> dict:
    cond_n = pg_cond_n(mux_sel, ac_wr)
    clk = pg_clk_for_event(event, cond_n)
    latch = event == "T2_END" and cond_n == 0
    return {
        "pg_cond_n": cond_n,
        "pg_clk": clk,
        "latch": latch,
        "pg": ibus & 0xFF if latch else start_pg & 0xFF,
    }


def jump_target(pg: int, irl: int) -> int:
    return ((pg & 0xFF) << 8) | (irl & 0xFF)


def branch_jump_control(phase: str, jmp: int, br: int, z_flag: int, alu_sub: int) -> dict[str, int]:
    z_match = int(bool(z_flag ^ alu_sub))
    br_taken = int(bool(br and z_match))
    pc_load_cond = int(bool(jmp or br_taken))
    pc_ld_n = 0 if phase == "T2" and pc_load_cond else 1
    return {
        "z_match": z_match,
        "br_taken": br_taken,
        "pc_load_cond": pc_load_cond,
        "pc_ld_n": pc_ld_n,
    }


def alu_datapath(start_ac: int, ibus: int, alu_sub: int, xor_mode: int, mux_sel: int, ac_wr: int, phase: str) -> dict[str, int]:
    xor_b = start_ac if xor_mode else (0xFF if alu_sub else 0x00)
    xor_out = (ibus ^ xor_b) & 0xFF
    adder_full = start_ac + xor_out + alu_sub
    adder_sum = adder_full & 0xFF
    ac_mux = xor_out if mux_sel else adder_sum
    acc_clk = int(bool(phase == "T2" and ac_wr))
    ac = ac_mux if acc_clk else start_ac & 0xFF
    return {
        "xor_b": xor_b,
        "xor": xor_out,
        "sum": adder_sum,
        "cout": (adder_full >> 8) & 1,
        "acc_clk": acc_clk,
        "ac": ac,
        "z": int(ac == 0),
    }


def alu_opcode_sweep_expected(opcode: int, start_ac: int, ibus: int, init_z: int) -> dict[str, int]:
    result = alu_datapath(
        start_ac,
        ibus,
        (opcode >> 7) & 1,
        (opcode >> 6) & 1,
        (opcode >> 5) & 1,
        (opcode >> 4) & 1,
        "T2",
    )
    return {
        "ac": result["ac"],
        "z": result["z"] if ((opcode >> 4) & 1) else init_z,
    }


def full_control_opcode_expected(opcode: int, init_z: int, constants: dict[str, str]) -> dict[str, int]:
    init_ac = int(constants["init_ac"], 16)
    init_pg = int(constants["init_pg"], 16)
    init_dp = int(constants["init_dp"], 16)
    operand = int(constants["operand"], 16)
    ram_value = int(constants["ram_value"], 16)
    init_pc = int(constants["init_pc"], 16)
    target = int(constants["target"], 16)

    bits = control_bits(opcode)
    ibus = ram_value if bits["SRC"] else operand
    result = alu_datapath(
        init_ac,
        ibus,
        bits["ALU_SUB"],
        bits["XOR_MODE"],
        bits["MUX_SEL"],
        bits["AC_WR"],
        "T2",
    )
    branch = branch_jump_control("T2", bits["JMP"], bits["BR"], init_z, bits["ALU_SUB"])
    return {
        "ibus": ibus,
        "ac": result["ac"],
        "z": result["z"] if bits["AC_WR"] else init_z,
        "pg": ibus if bits["MUX_SEL"] and not bits["AC_WR"] else init_pg,
        "dp": operand if bits["XOR_MODE"] and not (bits["SRC"] or bits["STR"]) and not bits["AC_WR"] else init_dp,
        "ie": 1 if bits["SRC"] and not bits["XOR_MODE"] and not bits["AC_WR"] else 0,
        "pc": target if branch["pc_load_cond"] else init_pc,
        "ram": init_ac if bits["STR"] else ram_value,
        "conflict": bus_ownership("T2", bits["SRC"], bits["STR"], 1)["conflict"],
    }


def z_compare_n(ac: int) -> int:
    return int((ac & 0xFF) != 0)


def required_clock_profile_names() -> set[str]:
    return {"push_switch_single_step", "push_switch_random_100", "50_khz", "1_mhz", "2_mhz", "5_mhz"}


def simulate_clock_profile(profile: dict) -> list[int]:
    ticks = int(profile["expect_ticks"])
    if profile["mode"] == "manual":
        assert profile["ticks"] == ticks
        return [1]
    if profile["mode"] == "manual_random":
        assert profile["ticks"] == ticks
        intervals = random_push_intervals_ms(profile)
        assert len(intervals) == ticks
        return [1 for _interval in intervals]
    if profile["mode"] == "fixed_frequency":
        period_ns = int(round(1_000_000_000 / int(profile["frequency_hz"])))
        assert profile["period_ns"] == period_ns
        return [1] * ticks
    raise AssertionError(profile["mode"])


def phase_probe(t0: int, t1: int, t2: int) -> dict[str, object]:
    active = [name for name, value in (("T0", t0), ("T1", t1), ("T2", t2)) if value]
    if len(active) == 1:
        return {"valid": True, "phase": active[0]}
    return {"valid": False, "fault": "zero_hot" if not active else "multi_hot"}


def bus_probe(drivers: list[str]) -> dict[str, object]:
    active = [driver for driver in drivers if driver]
    return {"drivers": active, "conflict": len(active) > 1}


def switch_sequence(vector: dict) -> dict[str, object]:
    mode = vector["mode"]
    if mode == "stable_off":
        return {"sequence": [0]}
    if mode == "stable_on":
        return {"sequence": [1]}
    if mode == "one_shot_push_on_release_off":
        return {"sequence": [0] + [1] * int(vector["active_ticks"]) + [0]}
    if mode == "one_shot_on_off":
        return {"sequence": [1] * int(vector["active_ticks"]) + [0]}
    if mode == "preset_pulse_train":
        pulses = int(vector["pulses"])
        interval_ms = int(vector["interval_ms"])
        active_ms = int(vector["active_ms"])
        events = []
        for index in range(pulses):
            start_ms = index * interval_ms
            events.append({"time_ms": start_ms, "value": 1})
            events.append({"time_ms": start_ms + active_ms, "value": 0})
        return {
            "events": events,
            "edges": sum(1 for event in events if event["value"] == 1),
            "total_ms": pulses * interval_ms,
        }
    raise AssertionError(mode)


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


def test_rv8gr_instruction_latch_package_shape():
    circuit = load_json(INSTRUCTION_LATCH / "circuit.json")
    proof = load_json(INSTRUCTION_LATCH / "tests" / "instruction_latch.json")

    assert circuit["schema"] == "components.lib.circuit"
    assert circuit["id"] == "rv8gr_instruction_latch"
    assert proof["circuit"] == circuit["id"]
    assert (INSTRUCTION_LATCH / "README.md").exists()

    chips = {chip["ref"]: chip["part"] for chip in circuit["chips"]}
    assert chips == {"U5": "74HC574", "U6": "74HC574"}
    assert list((ROOT / "DB").glob("*/74HC574/definition/definition.json"))
    assert "T0 rising for U5" in circuit["timing"]["trigger_edges"]
    assert "T1 rising for U6" in circuit["timing"]["trigger_edges"]


def test_rv8gr_instruction_latch_vectors_execute():
    proof = load_json(INSTRUCTION_LATCH / "tests" / "instruction_latch.json")

    for vector in proof["vectors"]:
        ir_high, irl = instruction_latch_step(
            int(vector["start_ir_high"], 16),
            int(vector["start_irl"], 16),
            int(vector["ibus"], 16),
            vector["phase"],
        )
        assert ir_high == int(vector["expect_ir_high"], 16), vector
        assert irl == int(vector["expect_irl"], 16), vector


def test_rv8gr_instruction_latch_vectors_execute_with_component_models():
    proof = load_json(INSTRUCTION_LATCH / "tests" / "instruction_latch.json")

    for vector in proof["vectors"]:
        u5 = create_chip("74HC574", "U5")
        u6 = create_chip("74HC574", "U6")
        latch_byte(u5, int(vector["start_ir_high"], 16))
        latch_byte(u6, int(vector["start_irl"], 16))
        set_byte(u5, BYTE_D_PINS, int(vector["ibus"], 16))
        set_byte(u6, BYTE_D_PINS, int(vector["ibus"], 16))
        if vector["phase"] == "T0":
            u5.clock_edge(11)
            u5.commit()
        elif vector["phase"] == "T1":
            u6.clock_edge(11)
            u6.commit()
        else:
            u5.update()
            u6.update()
            u5.commit()
            u6.commit()
        assert read_byte(u5, BYTE_Q_PINS) == int(vector["expect_ir_high"], 16), vector
        assert read_byte(u6, BYTE_Q_PINS) == int(vector["expect_irl"], 16), vector


def test_rv8gr_instruction_latch_control_bit_labels():
    proof = load_json(INSTRUCTION_LATCH / "tests" / "instruction_latch.json")
    expected_labels = ["ALU_SUB", "XOR_MODE", "MUX_SEL", "AC_WR", "SRC", "STR", "BR", "JMP"]
    assert list(proof["control_bits"].values()) == expected_labels
    assert control_bits(0x10) == {"ALU_SUB": 0, "XOR_MODE": 0, "MUX_SEL": 0, "AC_WR": 1, "SRC": 0, "STR": 0, "BR": 0, "JMP": 0}
    assert control_bits(0x90)["ALU_SUB"] == 1 and control_bits(0x90)["AC_WR"] == 1
    assert control_bits(0x04)["STR"] == 1


def test_rv8gr_store_path_package_shape():
    circuit = load_json(STORE_PATH / "circuit.json")
    proof = load_json(STORE_PATH / "tests" / "store_path.json")

    assert circuit["schema"] == "components.lib.circuit"
    assert circuit["id"] == "rv8gr_store_path"
    assert proof["circuit"] == circuit["id"]
    assert (STORE_PATH / "README.md").exists()

    chips = {chip["ref"]: chip["part"] for chip in circuit["chips"]}
    assert chips["U14"] == "74HC541"
    assert chips["U7"] == "74HC245"
    assert chips["U26"] == "74HC00"
    assert chips["U28"] == "74HC86"
    assert chips["ROM1"] == "AT28C256"
    assert chips["RAM1"] == "62256"
    for part in set(chips.values()):
        assert list((ROOT / "DB").glob(f"*/*{part}/definition/definition.json")), part


def test_rv8gr_store_path_vectors_execute():
    proof = load_json(STORE_PATH / "tests" / "store_path.json")

    for vector in proof["vectors"]:
        controls = store_path_controls(vector["phase"], vector["str"], vector["a15"])
        assert controls["/AC_BUF"] == vector["expect_ac_buf_n"], vector
        assert controls["WR_DIR"] == vector["expect_wr_dir"], vector
        assert controls["RAM_WE_N"] == vector["expect_ram_we_n"], vector
        assert controls["ROM_OE_N"] == vector["expect_rom_oe_n"], vector
        assert controls["write"] == vector["expect_write"], vector


def test_rv8gr_store_path_ram_write_and_rom_page_safety():
    proof = load_json(STORE_PATH / "tests" / "store_path.json")
    ram = create_chip("62256", "RAM1")
    set_memory_addr(ram, 0x0003)
    set_byte(ram, MEMORY_DQ_PINS, 0xAA)

    ram_store = next(vector for vector in proof["vectors"] if vector["name"] == "t2_store_ram")
    controls = store_path_controls(ram_store["phase"], ram_store["str"], ram_store["a15"])
    set_byte(ram, MEMORY_DQ_PINS, int(ram_store["ac"], 16))
    ram.set_input(20, controls["RAM_CE_N"])
    ram.set_input(22, 0)
    ram.set_input(27, controls["RAM_WE_N"])
    ram.update()
    ram.commit()
    assert ram.data[0x0003] == int(ram_store["ac"], 16)

    rom = create_chip("AT28C256", "ROM1")
    rom.data[0x0003] = 0xC3
    rom_store = next(vector for vector in proof["vectors"] if vector["name"] == "t2_store_rom_page_bus_safe")
    controls = store_path_controls(rom_store["phase"], rom_store["str"], rom_store["a15"])
    set_memory_addr(rom, 0x0003)
    set_byte(rom, MEMORY_DQ_PINS, int(rom_store["ac"], 16))
    rom.set_input(20, controls["ROM_CE_N"])
    rom.set_input(22, controls["ROM_OE_N"])
    rom.set_input(27, 1)
    rom.update()
    rom.commit()
    assert controls["rom_page_store_bus_safe"] is True
    assert rom.data[0x0003] == 0xC3


def test_rv8gr_data_page_memory_package_shape():
    circuit = load_json(DATA_PAGE_MEMORY / "circuit.json")
    proof = load_json(DATA_PAGE_MEMORY / "tests" / "data_page_memory.json")

    assert circuit["schema"] == "components.lib.circuit"
    assert circuit["id"] == "rv8gr_data_page_memory"
    assert proof["circuit"] == circuit["id"]
    assert (DATA_PAGE_MEMORY / "README.md").exists()

    chips = {chip["ref"]: chip["part"] for chip in circuit["chips"]}
    assert chips == {
        "U32": "74HC574",
        "U33": "74HC21",
        "U29": "74HC157",
        "U30": "74HC157",
        "ROM1": "AT28C256",
        "RAM1": "62256",
    }
    for part in set(chips.values()):
        assert list((ROOT / "DB").glob(f"*/*{part}/definition/definition.json")), part


def test_rv8gr_data_page_setdp_vectors_execute():
    proof = load_json(DATA_PAGE_MEMORY / "tests" / "data_page_memory.json")

    for vector in proof["setdp_vectors"]:
        load = dp_load_signal(vector["phase"], vector["xor_mode"], vector["addr_mode_n"], vector["ac_wr_n"])
        dp = int(vector["ibus"], 16) if load else int(vector["start_dp"], 16)
        assert load == vector["expect_dp_load"], vector
        assert dp == int(vector["expect_dp"], 16), vector


def test_rv8gr_data_page_setdp_executes_with_component_models():
    proof = load_json(DATA_PAGE_MEMORY / "tests" / "data_page_memory.json")
    setdp = next(vector for vector in proof["setdp_vectors"] if vector["name"] == "setdp_80")
    u33 = create_chip("74HC21", "U33")
    u32 = create_chip("74HC574", "U32")

    latch_byte(u32, int(setdp["start_dp"], 16))
    set_byte(u32, BYTE_D_PINS, int(setdp["ibus"], 16))
    for pin, value in ((1, phase_t2(setdp["phase"])), (2, setdp["xor_mode"]), (4, setdp["addr_mode_n"]), (5, setdp["ac_wr_n"])):
        u33.set_input(pin, value)
    u33.update()
    u33.commit()
    assert u33.read(6) == setdp["expect_dp_load"]
    if u33.read(6):
        u32.clock_edge(11)
        u32.commit()
    assert read_byte(u32, BYTE_Q_PINS) == int(setdp["expect_dp"], 16)


def test_rv8gr_data_page_memory_vectors_execute():
    proof = load_json(DATA_PAGE_MEMORY / "tests" / "data_page_memory.json")
    ram = create_chip("62256", "RAM1")
    rom = create_chip("AT28C256", "ROM1")

    for vector in proof["memory_vectors"]:
        dp = int(vector["dp"], 16)
        irl = int(vector["irl"], 16)
        address = data_address(dp, irl)
        select = memory_select_from_a15((address >> 15) & 1)
        if "expect_address" in vector:
            assert address == int(vector["expect_address"], 16), vector
            assert select["rom_ce_n"] == vector["expect_rom_ce_n"], vector
            assert select["ram_ce_n"] == vector["expect_ram_ce_n"], vector
            assert select["rom_ce_n"] != select["ram_ce_n"], vector
        if "write" in vector:
            set_memory_addr(ram, address & 0x7FFF)
            set_byte(ram, MEMORY_DQ_PINS, int(vector["write"], 16))
            ram.set_input(20, select["ram_ce_n"])
            ram.set_input(22, 0)
            ram.set_input(27, 0)
            ram.update()
            ram.commit()
            ram.set_input(27, 1)
            ram.update()
            ram.commit()
            assert read_byte(ram, MEMORY_DQ_PINS) == int(vector["expect_read"], 16), vector
        if "rom_value" in vector:
            rom.data[address & 0x7FFF] = int(vector["rom_value"], 16)
            set_memory_addr(rom, address & 0x7FFF)
            rom.set_input(20, select["rom_ce_n"])
            rom.set_input(22, 0)
            rom.set_input(27, 1)
            rom.update()
            rom.commit()
            assert read_byte(rom, MEMORY_DQ_PINS) == int(vector["expect_read"], 16), vector


def test_rv8gr_clock_profiles_exist_on_edge_sensitive_new_circuits():
    for tests_path in [
        INSTRUCTION_LATCH / "tests" / "instruction_latch.json",
        DATA_PAGE_MEMORY / "tests" / "data_page_memory.json",
        IRQ_LATCH / "tests" / "irq_latch.json",
    ]:
        profiles = load_json(tests_path)["clock_profiles"]
        names = {profile["name"] for profile in profiles}
        assert required_clock_profile_names() <= names, tests_path
        random_profile = next(profile for profile in profiles if profile["name"] == "push_switch_random_100")
        assert random_profile["seed"] == RANDOM_PUSH_SEED
        intervals = random_push_intervals_ms(random_profile)
        assert len(intervals) == 100
        assert all(0 <= interval <= 500 for interval in intervals)
        assert len(set(intervals)) > 1
        five_mhz = next(profile for profile in profiles if profile["name"] == "5_mhz")
        assert "Functional simulation only" in five_mhz["note"]


def test_rv8gr_instruction_latch_clock_profiles_capture_once_per_edge():
    profile = next(item for item in load_json(INSTRUCTION_LATCH / "tests" / "instruction_latch.json")["clock_profiles"] if item["name"] == "push_switch_random_100")
    intervals = random_push_intervals_ms(profile)
    ir_high = 0
    irl = 0
    for index, _interval in enumerate(intervals):
        phase = "T0" if index % 2 == 0 else "T1"
        value = (index + 1) & 0xFF
        ir_high, irl = instruction_latch_step(ir_high, irl, value, phase)
        if phase == "T0":
            assert ir_high == value
        else:
            assert irl == value


def test_rv8gr_data_page_clock_profiles_load_once_per_edge():
    profile = next(item for item in load_json(DATA_PAGE_MEMORY / "tests" / "data_page_memory.json")["clock_profiles"] if item["name"] == "push_switch_random_100")
    intervals = random_push_intervals_ms(profile)
    dp = 0
    for expected, _interval in enumerate(intervals, start=1):
        value = expected & 0xFF
        load = dp_load_signal("T2", 1, 1, 1)
        if load:
            dp = value
        assert dp == value


def test_rv8gr_irq_latch_package_shape():
    circuit = load_json(IRQ_LATCH / "circuit.json")
    proof = load_json(IRQ_LATCH / "tests" / "irq_latch.json")

    assert circuit["schema"] == "components.lib.circuit"
    assert circuit["id"] == "rv8gr_irq_latch"
    assert proof["circuit"] == circuit["id"]
    assert (IRQ_LATCH / "README.md").exists()

    chips = {chip["ref"]: chip["part"] for chip in circuit["chips"]}
    assert chips == {"U31": "74HC74", "U33": "74HC21"}
    for part in set(chips.values()):
        assert list((ROOT / "DB").glob(f"*/*{part}/definition/definition.json")), part
    absent_ports = {port["name"] for port in circuit["ports"] if port["direction"] == "absent"}
    assert {"PC_FORCE", "IRQ_ACK"} <= absent_ports


def test_rv8gr_irq_latch_vectors_execute():
    proof = load_json(IRQ_LATCH / "tests" / "irq_latch.json")

    for vector in proof["vectors"]:
        ie, irq_ff, pc = irq_latch_step(vector["start_ie"], vector["start_irq_ff"], vector["event"], vector["rst"])
        assert ie == vector["expect_ie"], vector
        assert irq_ff == vector["expect_irq_ff"], vector
        assert pc == vector["expect_pc"], vector


def test_rv8gr_irq_latch_vectors_execute_with_component_model():
    proof = load_json(IRQ_LATCH / "tests" / "irq_latch.json")

    for vector in proof["vectors"]:
        u31 = create_chip("74HC74", "U31")
        # Initialize both FFs through their real clock inputs with D=1, then reset as needed.
        u31.set_input(1, 1)
        u31.set_input(4, 1)
        u31.set_input(10, 1)
        u31.set_input(13, 1)
        u31.set_input(2, vector["start_ie"])
        u31.clock_edge(3)
        u31.set_input(12, vector["start_irq_ff"])
        u31.clock_edge(11)
        u31.commit()

        u31.set_input(1, vector["rst"])
        u31.set_input(13, vector["rst"])
        if vector["event"] == "reset":
            u31.update()
        elif vector["event"] == "ei_rising":
            u31.set_input(2, 1)
            u31.clock_edge(3)
        elif vector["event"] == "irq_low":
            u31.set_input(12, 1)
            u31.set_input(11, 0)
            u31.update()
        elif vector["event"] == "irq_release_rising":
            u31.set_input(12, 1)
            u31.clock_edge(11)
        elif vector["event"] in {"di", "100_cpu_ticks"}:
            u31.update()
        else:
            raise AssertionError(vector)
        u31.commit()

        assert u31.read(5) == vector["expect_ie"], vector
        assert u31.read(9) == vector["expect_irq_ff"], vector


def test_rv8gr_irq_latch_random_release_profile_latches_and_stays_sticky():
    profile = next(item for item in load_json(IRQ_LATCH / "tests" / "irq_latch.json")["clock_profiles"] if item["name"] == "push_switch_random_100")
    intervals = random_push_intervals_ms(profile)
    ie = 1
    irq_ff = 0
    for _interval in intervals:
        ie, irq_ff, _pc = irq_latch_step(ie, irq_ff, "irq_low", 1)
        assert irq_ff == 0
        ie, irq_ff, _pc = irq_latch_step(ie, irq_ff, "irq_release_rising", 1)
        assert ie == 1 and irq_ff == 1
        ie, irq_ff, _pc = irq_latch_step(ie, irq_ff, "100_cpu_ticks", 1)
        assert irq_ff == 1
        ie, irq_ff, _pc = irq_latch_step(ie, irq_ff, "reset", 0)
        assert ie == 0 and irq_ff == 0
        ie = 1


def test_rv8gr_rom_dbus_read_package_shape():
    circuit = load_json(ROM_DBUS_READ / "circuit.json")
    proof = load_json(ROM_DBUS_READ / "tests" / "rom_dbus_read.json")

    assert circuit["schema"] == "components.lib.circuit"
    assert circuit["id"] == "rv8gr_rom_dbus_read"
    assert proof["circuit"] == circuit["id"]
    assert (ROM_DBUS_READ / "README.md").exists()

    chips = {chip["ref"]: chip["part"] for chip in circuit["chips"]}
    assert chips == {"ROM1": "AT28C256", "U7": "74HC245"}
    for part in set(chips.values()):
        assert list((ROOT / "DB").glob(f"*/*{part}/definition/definition.json")), part
    assert "DBUS_TO_IBUS" in circuit["behavior"]["u7_read"]


def test_rv8gr_rom_dbus_read_vectors_execute():
    proof = load_json(ROM_DBUS_READ / "tests" / "rom_dbus_read.json")
    rom_data = rom_image_bytes(proof)

    for vector in proof["vectors"]:
        result = rom_dbus_read(int(vector["address"], 16), rom_data, wr_dir=vector["wr_dir"], buf_oe_n=vector["buf_oe_n"])
        assert result["rom_ce_n"] == vector["expect_rom_ce_n"], vector
        assert result["rom_oe_n"] == vector["expect_rom_oe_n"], vector
        assert result["u7_direction"] == vector["expect_u7_direction"], vector
        expect_ibus = None if vector["expect_ibus"] is None else int(vector["expect_ibus"], 16)
        assert result["ibus"] == expect_ibus, vector
        assert result["conflict"] == vector["expect_conflict"], vector

    for vector in proof["bus_safety"]:
        result = rom_dbus_read(
            int(vector["address"], 16),
            rom_data,
            wr_dir=vector["wr_dir"],
            buf_oe_n=vector["buf_oe_n"],
            force_rom_oe_n=vector["force_rom_oe_n"],
        )
        assert result["conflict"] == vector["expect_conflict"], vector


def test_rv8gr_rom_dbus_read_executes_with_component_models():
    proof = load_json(ROM_DBUS_READ / "tests" / "rom_dbus_read.json")
    rom_data = rom_image_bytes(proof)

    for address, value in rom_data.items():
        rom = create_chip("AT28C256", "ROM1")
        u7 = create_chip("74HC245", "U7")
        rom.data[address & 0x7FFF] = value
        set_memory_addr(rom, address & 0x7FFF)
        rom.set_input(20, (address >> 15) & 1)
        rom.set_input(22, 0)
        rom.set_input(27, 1)
        rom.update()
        rom.commit()

        set_byte(u7, U7_B_PINS, read_byte(rom, MEMORY_DQ_PINS))
        u7.set_input(1, 0)
        u7.set_input(19, 0)
        u7.update()
        u7.commit()
        assert read_byte(u7, U7_A_PINS) == value, hex(address)


def test_rv8gr_page_data_registers_package_shape():
    circuit = load_json(PAGE_DATA_REGISTERS / "circuit.json")
    proof = load_json(PAGE_DATA_REGISTERS / "tests" / "page_data_registers.json")

    assert circuit["schema"] == "components.lib.circuit"
    assert circuit["id"] == "rv8gr_page_data_registers"
    assert proof["circuit"] == circuit["id"]
    assert (PAGE_DATA_REGISTERS / "README.md").exists()

    chips = {chip["ref"]: chip["part"] for chip in circuit["chips"]}
    assert chips == {"U23": "74HC574", "U25": "74HC32", "U27": "74HC00", "U32": "74HC574", "U33": "74HC21"}
    for part in set(chips.values()):
        assert list((ROOT / "DB").glob(f"*/*{part}/definition/definition.json")), part
    assert "PG_CLK rising edge" in circuit["timing"]["trigger_edges"][0]


def test_rv8gr_page_register_setpg_edge_vectors_execute():
    proof = load_json(PAGE_DATA_REGISTERS / "tests" / "page_data_registers.json")

    for vector in proof["setpg_vectors"]:
        result = page_register_step(
            int(vector["start_pg"], 16),
            int(vector["ibus"], 16),
            vector["event"],
            vector["mux_sel"],
            vector["ac_wr"],
        )
        assert result["pg_cond_n"] == vector["expect_pg_cond_n"], vector
        assert result["pg_clk"] == vector["expect_pg_clk"], vector
        assert result["latch"] == vector["expect_latch"], vector
        assert result["pg"] == int(vector["expect_pg"], 16), vector


def test_rv8gr_page_register_setpg_executes_with_component_model():
    proof = load_json(PAGE_DATA_REGISTERS / "tests" / "page_data_registers.json")
    for vector in proof["setpg_vectors"]:
        u23 = create_chip("74HC574", "U23")
        latch_byte(u23, int(vector["start_pg"], 16))
        set_byte(u23, BYTE_D_PINS, int(vector["ibus"], 16))
        if vector["expect_latch"]:
            u23.clock_edge(11)
        else:
            u23.update()
        u23.commit()
        assert read_byte(u23, BYTE_Q_PINS) == int(vector["expect_pg"], 16), vector


def test_rv8gr_page_data_register_jump_targets_and_separation():
    proof = load_json(PAGE_DATA_REGISTERS / "tests" / "page_data_registers.json")

    for vector in proof["jump_targets"]:
        assert jump_target(int(vector["pg"], 16), int(vector["irl"], 16)) == int(vector["expect_pc_load"], 16), vector

    for vector in proof["separation_vectors"]:
        pg_latch = page_register_step(0, 0x5A, "T2_END", vector["mux_sel"], 0 if vector["ac_wr_n"] else 1)["latch"]
        dp_load = dp_load_signal(vector["phase"], vector["xor_mode"], vector["addr_mode_n"], vector["ac_wr_n"])
        assert pg_latch == vector["expect_pg_latch"], vector
        assert dp_load == vector["expect_dp_load"], vector


def test_rv8gr_branch_jump_control_package_shape():
    circuit = load_json(BRANCH_JUMP_CONTROL / "circuit.json")
    proof = load_json(BRANCH_JUMP_CONTROL / "tests" / "branch_jump_control.json")

    assert circuit["schema"] == "components.lib.circuit"
    assert circuit["id"] == "rv8gr_branch_jump_control"
    assert proof["circuit"] == circuit["id"]
    assert (BRANCH_JUMP_CONTROL / "README.md").exists()

    chips = {chip["ref"]: chip["part"] for chip in circuit["chips"]}
    assert chips == {"U28": "74HC86", "U27": "74HC00", "U26": "74HC00"}
    for part in set(chips.values()):
        assert list((ROOT / "DB").glob(f"*/*{part}/definition/definition.json")), part
    assert circuit["behavior"]["pc_load_cond"] == "PC_LOAD_COND=JMP OR BR_TAKEN."


def test_rv8gr_branch_jump_vectors_execute():
    proof = load_json(BRANCH_JUMP_CONTROL / "tests" / "branch_jump_control.json")

    for vector in proof["vectors"]:
        result = branch_jump_control(vector["phase"], vector["jmp"], vector["br"], vector["z_flag"], vector["alu_sub"])
        assert result["z_match"] == vector["expect_z_match"], vector
        assert result["br_taken"] == vector["expect_br_taken"], vector
        assert result["pc_load_cond"] == vector["expect_pc_load_cond"], vector
        assert result["pc_ld_n"] == vector["expect_pc_ld_n"], vector


def test_rv8gr_branch_jump_opcode_sweep_matches_verilog_bench_equation():
    target = jump_target(0x12, 0x5A)
    assert target == 0x125A
    for opcode in range(256):
        for z_flag in (0, 1):
            result = branch_jump_control("T2", opcode & 1, (opcode >> 1) & 1, z_flag, (opcode >> 7) & 1)
            expect_pc_load = int(bool((opcode & 1) or (((opcode >> 1) & 1) and (z_flag ^ ((opcode >> 7) & 1)))))
            assert result["pc_load_cond"] == expect_pc_load, (opcode, z_flag)
            next_pc = target if result["pc_ld_n"] == 0 else 0x0011
            if opcode == 0x01:
                assert next_pc == target


def test_rv8gr_new_control_clock_profiles_exist_and_are_functional():
    for tests_path in [
        PAGE_DATA_REGISTERS / "tests" / "page_data_registers.json",
        BRANCH_JUMP_CONTROL / "tests" / "branch_jump_control.json",
    ]:
        profiles = load_json(tests_path)["clock_profiles"]
        names = {profile["name"] for profile in profiles}
        assert required_clock_profile_names() <= names, tests_path
        random_profile = next(profile for profile in profiles if profile["name"] == "push_switch_random_100")
        assert random_profile["seed"] == RANDOM_PUSH_SEED
        intervals = random_push_intervals_ms(random_profile)
        assert len(intervals) == 100
        assert all(0 <= interval <= 500 for interval in intervals)
        assert len(set(intervals)) > 1
        assert "Functional simulation only" in next(profile for profile in profiles if profile["name"] == "5_mhz")["note"]

    pg = 0
    pg_profile = next(item for item in load_json(PAGE_DATA_REGISTERS / "tests" / "page_data_registers.json")["clock_profiles"] if item["name"] == "push_switch_random_100")
    for expected, _interval in enumerate(random_push_intervals_ms(pg_profile), start=1):
        pg = page_register_step(pg, expected, "T2_END", 1, 0)["pg"]
        assert pg == (expected & 0xFF)

    branch_profile = next(item for item in load_json(BRANCH_JUMP_CONTROL / "tests" / "branch_jump_control.json")["clock_profiles"] if item["name"] == "push_switch_random_100")
    for index, _interval in enumerate(random_push_intervals_ms(branch_profile)):
        z_flag = index & 1
        result = branch_jump_control("T2", 0, 1, z_flag, 0)
        assert result["pc_ld_n"] == (0 if z_flag else 1)


def test_rv8gr_alu_accumulator_package_shape():
    circuit = load_json(ALU_ACCUMULATOR / "circuit.json")
    proof = load_json(ALU_ACCUMULATOR / "tests" / "alu_accumulator.json")

    assert circuit["schema"] == "components.lib.circuit"
    assert circuit["id"] == "rv8gr_alu_accumulator"
    assert proof["circuit"] == circuit["id"]
    assert (ALU_ACCUMULATOR / "README.md").exists()

    chips = {chip["ref"]: chip["part"] for chip in circuit["chips"]}
    assert chips == {
        "U9": "74HC574",
        "U10": "74HC283",
        "U11": "74HC283",
        "U12": "74HC86",
        "U13": "74HC86",
        "U14": "74HC541",
        "U17": "74HC157",
        "U18": "74HC157",
        "U19": "74HC157",
        "U20": "74HC157",
        "U21": "74HC74",
        "U22": "74HC688",
        "U27": "74HC00",
    }
    for part in set(chips.values()):
        assert list((ROOT / "DB").glob(f"*/*{part}/definition/definition.json")), part
    assert "ClockProfileMonitor" in circuit["timing"]["virtual_test_helpers"]


def test_rv8gr_alu_accumulator_vectors_execute():
    proof = load_json(ALU_ACCUMULATOR / "tests" / "alu_accumulator.json")

    for vector in proof["vectors"]:
        result = alu_datapath(
            int(vector["start_ac"], 16),
            int(vector["ibus"], 16),
            vector["alu_sub"],
            vector["xor_mode"],
            vector["mux_sel"],
            vector["ac_wr"],
            vector["phase"],
        )
        assert result["xor_b"] == int(vector["expect_xor_b"], 16), vector
        assert result["xor"] == int(vector["expect_xor"], 16), vector
        assert result["sum"] == int(vector["expect_sum"], 16), vector
        assert result["cout"] == vector["expect_cout"], vector
        assert result["ac"] == int(vector["expect_ac"], 16), vector
        assert result["z"] == vector["expect_z"], vector


def test_rv8gr_alu_adder_vectors_execute_with_component_models():
    proof = load_json(ALU_ACCUMULATOR / "tests" / "alu_accumulator.json")

    for vector in proof["vectors"]:
        low = create_chip("74HC283", "U10")
        high = create_chip("74HC283", "U11")
        result = alu_datapath(
            int(vector["start_ac"], 16),
            int(vector["ibus"], 16),
            vector["alu_sub"],
            vector["xor_mode"],
            vector["mux_sel"],
            vector["ac_wr"],
            vector["phase"],
        )

        def set_283(chip, a_nibble: int, b_nibble: int, cin: int) -> None:
            for bit, pin in enumerate([5, 3, 14, 12]):
                chip.set_input(pin, (a_nibble >> bit) & 1)
            for bit, pin in enumerate([6, 2, 15, 11]):
                chip.set_input(pin, (b_nibble >> bit) & 1)
            chip.set_input(7, cin)
            chip.update()
            chip.commit()

        set_283(low, int(vector["start_ac"], 16) & 0xF, result["xor"] & 0xF, vector["alu_sub"])
        set_283(high, int(vector["start_ac"], 16) >> 4, result["xor"] >> 4, low.read(9))

        low_sum = sum(low.read(pin) << bit for bit, pin in enumerate([4, 1, 13, 10]))
        high_sum = sum(high.read(pin) << bit for bit, pin in enumerate([4, 1, 13, 10]))
        assert low_sum | (high_sum << 4) == result["sum"], vector
        assert high.read(9) == result["cout"], vector


def test_rv8gr_alu_accumulator_capture_executes_with_component_model():
    proof = load_json(ALU_ACCUMULATOR / "tests" / "alu_accumulator.json")

    for vector in proof["vectors"]:
        u9 = create_chip("74HC574", "U9")
        latch_byte(u9, int(vector["start_ac"], 16))
        result = alu_datapath(
            int(vector["start_ac"], 16),
            int(vector["ibus"], 16),
            vector["alu_sub"],
            vector["xor_mode"],
            vector["mux_sel"],
            vector["ac_wr"],
            vector["phase"],
        )
        set_byte(u9, BYTE_D_PINS, result["sum"] if vector["mux_sel"] == 0 else result["xor"])
        if result["acc_clk"]:
            u9.clock_edge(11)
        else:
            u9.update()
        u9.commit()
        assert read_byte(u9, BYTE_Q_PINS) == int(vector["expect_ac"], 16), vector


def test_rv8gr_alu_ac_buffer_and_z_vectors_execute_with_component_models():
    proof = load_json(ALU_ACCUMULATOR / "tests" / "alu_accumulator.json")

    for vector in proof["buffer_vectors"]:
        u14 = create_chip("74HC541", "U14")
        set_byte(u14, HC541_A_PINS, int(vector["ac"], 16))
        u14.set_input(1, vector["ac_buf_n"])
        u14.set_input(19, vector["ac_buf_n"])
        u14.update()
        u14.commit()
        if vector["expect_ibus"] is None:
            assert all(u14.read(pin) == Z for pin in HC541_Y_PINS), vector
        else:
            assert read_byte(u14, HC541_Y_PINS) == int(vector["expect_ibus"], 16), vector

    for vector in proof["z_vectors"]:
        if "sequence" in vector:
            assert [int(z_compare_n(int(value, 16)) == 0) for value in vector["sequence"]] == vector["expect_z_sequence"], vector
            continue
        comp = create_chip("74HC688", "U22")
        ac = int(vector["ac"], 16)
        comp.set_input(1, 0)
        for bit, pin in enumerate([2, 4, 6, 8, 11, 13, 15, 17]):
            comp.set_input(pin, (ac >> bit) & 1)
        for pin in [3, 5, 7, 9, 12, 14, 16, 18]:
            comp.set_input(pin, 0)
        comp.update()
        comp.commit()
        assert z_compare_n(ac) == vector["expect_compare_n"], vector
        assert comp.read(19) == vector["expect_compare_n"], vector
        assert int(comp.read(19) == 0) == vector["expect_z"], vector


def test_rv8gr_alu_opcode_sweep_samples_match_verilog_equation():
    proof = load_json(ALU_ACCUMULATOR / "tests" / "alu_accumulator.json")
    sample = next(vector for vector in proof["source_vectors"] if vector["name"] == "opcode_sweep_formula_sample")
    expected = alu_opcode_sweep_expected(int(sample["opcode"], 16), int(sample["start_ac"], 16), int(sample["ibus"], 16), 0)
    assert expected["ac"] == int(sample["expect_ac"], 16)
    assert expected["z"] == sample["expect_z"]

    for opcode in range(256):
        for init_z in (0, 1):
            expected = alu_opcode_sweep_expected(opcode, 0xA5, 0x5A, init_z)
            direct = alu_datapath(0xA5, 0x5A, (opcode >> 7) & 1, (opcode >> 6) & 1, (opcode >> 5) & 1, (opcode >> 4) & 1, "T2")
            assert expected["ac"] == (direct["ac"] if ((opcode >> 4) & 1) else 0xA5), opcode


def test_rv8gr_alu_clock_profiles_capture_once_per_push():
    profiles = load_json(ALU_ACCUMULATOR / "tests" / "alu_accumulator.json")["clock_profiles"]
    names = {profile["name"] for profile in profiles}
    assert required_clock_profile_names() <= names
    random_profile = next(profile for profile in profiles if profile["name"] == "push_switch_random_100")
    assert random_profile["seed"] == RANDOM_PUSH_SEED
    intervals = random_push_intervals_ms(random_profile)
    assert len(intervals) == 100
    assert all(0 <= interval <= 500 for interval in intervals)
    assert len(set(intervals)) > 1
    assert "Functional simulation only" in next(profile for profile in profiles if profile["name"] == "5_mhz")["note"]

    ac = 0
    for expected, _interval in enumerate(intervals, start=1):
        result = alu_datapath(ac, 1, 0, 0, 0, 1, "T2")
        ac = result["ac"]
        assert ac == expected & 0xFF


def test_rv8gr_alu_propagation_delay_checks_are_explicit():
    proof = load_json(ALU_ACCUMULATOR / "tests" / "alu_accumulator.json")
    model_delays = {
        "74HC157": 18,
        "74HC86": 15,
        "74HC283": 35,
        "74HC574": 20,
        "74HC688": 30,
        "74HC74": 20,
        "74HC541": 12,
    }
    for check in proof["propagation_checks"]:
        delay = sum(model_delays[part] for part in check["parts"])
        assert delay == check["expect_delay_ns"], check
        assert delay <= check["limit_ns"], check


def test_rv8gr_virtual_test_helpers_package_shape():
    circuit = load_json(VIRTUAL_TEST_HELPERS / "circuit.json")
    proof = load_json(VIRTUAL_TEST_HELPERS / "tests" / "virtual_test_helpers.json")

    assert circuit["schema"] == "components.lib.circuit"
    assert circuit["id"] == "rv8gr_virtual_test_helpers"
    assert proof["circuit"] == circuit["id"]
    assert (VIRTUAL_TEST_HELPERS / "README.md").exists()

    chips = {chip["ref"]: chip["part"] for chip in circuit["chips"]}
    assert chips == {
        "VCLK": "ClockSource",
        "SW1": "Switch",
        "PH0": "Probe",
        "PH1": "Probe",
        "PH2": "Probe",
        "IBUSMON": "BusProbe",
        "DBUSMON": "BusProbe",
    }
    for part in proof["virtual_parts_required"]:
        assert (ROOT / "DB" / "Virtual" / part / "definition" / "definition.json").exists(), part


def test_rv8gr_virtual_clock_profiles_execute():
    proof = load_json(VIRTUAL_TEST_HELPERS / "tests" / "virtual_test_helpers.json")
    profiles = {profile["name"]: profile for profile in proof["clock_profiles"]}
    assert required_clock_profile_names() <= set(profiles)
    assert profiles["push_switch_random_100"]["seed"] == RANDOM_PUSH_SEED
    assert "Functional simulation only" in profiles["5_mhz"]["note"]

    for profile in profiles.values():
        ticks = simulate_clock_profile(profile)
        assert len(ticks) == profile["expect_ticks"], profile
        assert all(tick == 1 for tick in ticks), profile


def test_rv8gr_virtual_phase_probe_detects_invalid_phases():
    proof = load_json(VIRTUAL_TEST_HELPERS / "tests" / "virtual_test_helpers.json")
    for vector in proof["phase_vectors"]:
        result = phase_probe(vector["T0"], vector["T1"], vector["T2"])
        assert result["valid"] is vector["expect_valid"], vector
        if vector["expect_valid"]:
            assert result["phase"] == vector["expect_phase"], vector
        else:
            assert result["fault"] == vector["expect_fault"], vector


def test_rv8gr_virtual_bus_probe_detects_contention():
    proof = load_json(VIRTUAL_TEST_HELPERS / "tests" / "virtual_test_helpers.json")
    for vector in proof["bus_vectors"]:
        result = bus_probe(vector["drivers"])
        assert result["drivers"] == vector["drivers"], vector
        assert result["conflict"] is vector["expect_conflict"], vector


def test_rv8gr_virtual_switch_profiles_execute():
    proof = load_json(VIRTUAL_TEST_HELPERS / "tests" / "virtual_test_helpers.json")
    for vector in proof["switch_vectors"]:
        result = switch_sequence(vector)
        if "expect_sequence" in vector:
            assert result["sequence"] == vector["expect_sequence"], vector
        else:
            switch_def = load_json(ROOT / "DB" / "Virtual" / "Switch" / "definition" / "definition.json")
            presets = {preset["name"]: preset for preset in switch_def["simulation"]["preset_profiles"]}
            preset = presets["100_pulses_10ms_interval"]
            assert vector["pulses"] == preset["pulses"], vector
            assert vector["interval_ms"] == preset["interval_ms"], vector
            assert vector["active_ms"] == preset["active_ms"], vector
            assert result["edges"] == vector["expect_edges"], vector
            assert result["total_ms"] == vector["expect_total_ms"], vector
            assert len(result["events"]) == vector["pulses"] * 2, vector
            for index in range(vector["pulses"]):
                start = index * vector["interval_ms"]
                assert result["events"][index * 2] == {"time_ms": start, "value": preset["active_state"]}, vector
                assert result["events"][index * 2 + 1] == {"time_ms": start + vector["active_ms"], "value": preset["idle_state"]}, vector


def test_rv8gr_full_control_opcode_sweep_package_shape():
    circuit = load_json(FULL_CONTROL_OPCODE_SWEEP / "circuit.json")
    proof = load_json(FULL_CONTROL_OPCODE_SWEEP / "tests" / "full_control_opcode_sweep.json")

    assert circuit["schema"] == "components.lib.circuit"
    assert circuit["id"] == "rv8gr_full_control_opcode_sweep"
    assert proof["circuit"] == circuit["id"]
    assert (FULL_CONTROL_OPCODE_SWEEP / "README.md").exists()

    refs = {chip["ref"] for chip in circuit["chips"]}
    assert {"CTRL", "BUS", "ALU", "PGDP", "PC", "VT"} <= refs
    assert "tb_rv8gr_opcode_sweep.v" in " ".join(circuit["source_project"]["paths"])
    assert "reserved opcode mix" in " ".join(circuit["timing"]["unsafe_states"])


def test_rv8gr_full_control_opcode_sweep_all_512_cases_match_verilog_equation():
    proof = load_json(FULL_CONTROL_OPCODE_SWEEP / "tests" / "full_control_opcode_sweep.json")
    constants = proof["constants"]
    cases = 0

    for opcode in range(proof["sweep"]["opcode_count"]):
        for init_z in proof["sweep"]["initial_z_states"]:
            expected = full_control_opcode_expected(opcode, init_z, constants)
            bits = control_bits(opcode)
            assert expected["ac"] == (expected["ibus"] if opcode == 0x30 else expected["ac"])
            assert expected["z"] in (0, 1), (opcode, init_z)
            assert expected["pg"] in range(256), (opcode, init_z)
            assert expected["dp"] in range(256), (opcode, init_z)
            assert expected["pc"] in range(0x10000), (opcode, init_z)
            assert expected["ram"] == (int(constants["init_ac"], 16) if bits["STR"] else int(constants["ram_value"], 16)), (opcode, init_z)
            assert expected["conflict"] is False, (opcode, init_z)
            cases += 1

    assert cases == proof["sweep"]["expect_cases"]


def test_rv8gr_full_control_named_vectors_and_reserved_mixes_are_visible():
    proof = load_json(FULL_CONTROL_OPCODE_SWEEP / "tests" / "full_control_opcode_sweep.json")
    constants = proof["constants"]

    for vector in proof["named_vectors"]:
        expected = full_control_opcode_expected(int(vector["opcode"], 16), vector["init_z"], constants)
        assert expected["ac"] == int(vector["expect_ac"], 16), vector
        assert expected["z"] == vector["expect_z"], vector
        assert expected["pg"] == int(vector["expect_pg"], 16), vector
        assert expected["dp"] == int(vector["expect_dp"], 16), vector
        assert expected["ie"] == vector["expect_ie"], vector
        assert expected["pc"] == int(vector["expect_pc"], 16), vector
        assert expected["ram"] == int(vector["expect_ram"], 16), vector

    rules = " ".join(proof["reserved_mix_rules"])
    assert "loads PG" in rules
    assert "loads DP" in rules
    assert "sets IE" in rules
    assert "writes AC to RAM" in rules


def test_rv8gr_timing_margin_artifact_checks_slack_and_5mhz_boundary():
    timing = load_json(TIMING_MARGINS)
    assert timing["schema"] == "components.lib.circuit.timing_margins"
    assert timing["status"]["physical_5mhz_timing"] == "not_proven"
    assert timing["status"]["physical_signal_integrity"] == "not_proven"
    assert "functional simulation only" in timing["status"]["boundary_rule"]
    profiles = {profile["name"]: profile for profile in timing["clock_profiles"]}
    assert set(profiles) == {"50_khz", "1_mhz", "2_mhz", "5_mhz"}
    assert profiles["5_mhz"]["physical_status"] == "functional_simulation_only"

    circuit_paths = {
        path.parent.name
        for path in (ROOT / "Lib" / "Circuits").glob("RV8GR_*/circuit.json")
    }
    part_sources = {entry["part"]: entry for entry in timing["part_timing_sources"]}
    assert {"74HC574", "74HC161", "AT28C256", "62256"} <= set(part_sources)
    for entry in part_sources.values():
        assert (ROOT / entry["source"]).exists(), entry

    for path in timing["propagation_paths"]:
        assert path["circuit"] in circuit_paths, path
        total = path["total_budget_ns"]
        assert total == path["model_delay_ns"] + path["required_setup_ns"], path
        assert set(path["slack_ns"]) == set(profiles), path
        for name, profile in profiles.items():
            assert path["slack_ns"][name] == profile["period_ns"] - total, path
        if path["id"] == "alu_result_to_accumulator_setup":
            assert path["slack_ns"]["5_mhz"] == 59

    risks = {note["id"] for note in timing["bus_race_notes"]}
    assert {"rom_to_u7_turnaround", "ram_read_to_ram_write_turnaround", "ibus_multiple_driver_guard"} <= risks
    for note in timing["bus_race_notes"]:
        assert set(note["circuits"]) <= circuit_paths, note
        assert note["current_evidence"], note
        assert note["still_needed"], note


def test_rv8gr_timing_setup_hold_requirements_cover_edge_sensitive_paths():
    timing = load_json(TIMING_MARGINS)
    propagation_circuits = {path["circuit"] for path in timing["propagation_paths"]}
    requirements = {item["destination"]: item for item in timing["setup_hold_requirements"]}

    hc574 = requirements["74HC574 edge registers"]
    assert hc574["setup_before_clock_ns"] == 20
    assert hc574["hold_after_clock_ns"] == 5
    assert set(hc574["used_by_circuits"]) <= propagation_circuits

    counter = requirements["74HC161 program counter"]
    assert counter["setup_before_clock_ns"]["enp_ent"] == 34
    assert counter["hold_after_clock_ns"] == 0
    assert set(counter["used_by_circuits"]) <= propagation_circuits

    eeprom = requirements["AT28C256 EEPROM write"]
    assert eeprom["address_hold_ns"] == 50
    assert eeprom["data_setup_ns"] == 50
    assert eeprom["data_hold_ns"] == 0
    assert set(eeprom["used_by_circuits"]) <= propagation_circuits

    summary = " ".join(timing["student_summary"])
    assert "Setup means data is ready before a clock edge" in summary
    assert "bus race means two chips might briefly try to drive the same wire" in summary


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
    test_rv8gr_instruction_latch_package_shape()
    test_rv8gr_instruction_latch_vectors_execute()
    test_rv8gr_instruction_latch_vectors_execute_with_component_models()
    test_rv8gr_instruction_latch_control_bit_labels()
    test_rv8gr_store_path_package_shape()
    test_rv8gr_store_path_vectors_execute()
    test_rv8gr_store_path_ram_write_and_rom_page_safety()
    test_rv8gr_data_page_memory_package_shape()
    test_rv8gr_data_page_setdp_vectors_execute()
    test_rv8gr_data_page_setdp_executes_with_component_models()
    test_rv8gr_data_page_memory_vectors_execute()
    test_rv8gr_clock_profiles_exist_on_edge_sensitive_new_circuits()
    test_rv8gr_instruction_latch_clock_profiles_capture_once_per_edge()
    test_rv8gr_data_page_clock_profiles_load_once_per_edge()
    test_rv8gr_irq_latch_package_shape()
    test_rv8gr_irq_latch_vectors_execute()
    test_rv8gr_irq_latch_vectors_execute_with_component_model()
    test_rv8gr_irq_latch_random_release_profile_latches_and_stays_sticky()
    test_rv8gr_rom_dbus_read_package_shape()
    test_rv8gr_rom_dbus_read_vectors_execute()
    test_rv8gr_rom_dbus_read_executes_with_component_models()
    test_rv8gr_page_data_registers_package_shape()
    test_rv8gr_page_register_setpg_edge_vectors_execute()
    test_rv8gr_page_register_setpg_executes_with_component_model()
    test_rv8gr_page_data_register_jump_targets_and_separation()
    test_rv8gr_branch_jump_control_package_shape()
    test_rv8gr_branch_jump_vectors_execute()
    test_rv8gr_branch_jump_opcode_sweep_matches_verilog_bench_equation()
    test_rv8gr_new_control_clock_profiles_exist_and_are_functional()
    test_rv8gr_alu_accumulator_package_shape()
    test_rv8gr_alu_accumulator_vectors_execute()
    test_rv8gr_alu_adder_vectors_execute_with_component_models()
    test_rv8gr_alu_accumulator_capture_executes_with_component_model()
    test_rv8gr_alu_ac_buffer_and_z_vectors_execute_with_component_models()
    test_rv8gr_alu_opcode_sweep_samples_match_verilog_equation()
    test_rv8gr_alu_clock_profiles_capture_once_per_push()
    test_rv8gr_alu_propagation_delay_checks_are_explicit()
    test_rv8gr_virtual_test_helpers_package_shape()
    test_rv8gr_virtual_clock_profiles_execute()
    test_rv8gr_virtual_phase_probe_detects_invalid_phases()
    test_rv8gr_virtual_bus_probe_detects_contention()
    test_rv8gr_virtual_switch_profiles_execute()
    test_rv8gr_full_control_opcode_sweep_package_shape()
    test_rv8gr_full_control_opcode_sweep_all_512_cases_match_verilog_equation()
    test_rv8gr_full_control_named_vectors_and_reserved_mixes_are_visible()
    test_rv8gr_timing_margin_artifact_checks_slack_and_5mhz_boundary()
    test_rv8gr_timing_setup_hold_requirements_cover_edge_sensitive_paths()
    test_all_started_circuit_packages_have_tests()


if __name__ == "__main__":
    run_all()
    print("Components library circuit tests passed")
