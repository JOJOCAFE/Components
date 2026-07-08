"""Assertion-based smoke tests for the reusable chip library."""

from pathlib import Path
import tempfile

from chiplib import (
    Board,
    BusConflictError,
    ImageLoadError,
    StimulusController,
    Z,
    create_chip,
    load_image,
    load_memory,
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


def set_pins(chip, pins, values):
    for pin, value in zip(pins, values):
        chip.set_input(pin, value)


def set_byte(chip, pins, value):
    for i, pin in enumerate(pins):
        chip.set_input(pin, (value >> i) & 1)


def get_byte(chip, pins):
    return sum((1 if chip.read(pin) == 1 else 0) << i for i, pin in enumerate(pins))


def eval_chip(chip):
    chip.update()
    chip.commit()


def set_memory_addr(chip, value):
    for bit_index, pin in MEMORY_ADDR_PINS.items():
        chip.set_input(pin, (value >> bit_index) & 1)


def test_hc00():
    chip = create_chip("74HC00", "U")
    for a, b, y in [(0, 0, 1), (0, 1, 1), (1, 0, 1), (1, 1, 0)]:
        set_pins(chip, [1, 2], [a, b])
        eval_chip(chip)
        assert chip.read("1Y") == y


def test_hc04():
    chip = create_chip("74HC04", "U")
    for a, y in [(0, 1), (1, 0)]:
        chip.set_input("1A", a)
        eval_chip(chip)
        assert chip.read(2) == y


def test_hc21_hc32_hc86():
    and4 = create_chip("74HC21", "U")
    set_pins(and4, [1, 2, 4, 5], [1, 1, 1, 1])
    eval_chip(and4)
    assert and4.read(6) == 1
    and4.set_input(4, 0)
    eval_chip(and4)
    assert and4.read(6) == 0

    or2 = create_chip("74HC32", "U")
    set_pins(or2, [1, 2], [0, 1])
    eval_chip(or2)
    assert or2.read(3) == 1

    xor2 = create_chip("74HC86", "U")
    set_pins(xor2, [1, 2], [1, 1])
    eval_chip(xor2)
    assert xor2.read(3) == 0


def test_hc157():
    chip = create_chip("74HC157", "U")
    set_pins(chip, [15, 1, 2, 3], [0, 0, 1, 0])
    eval_chip(chip)
    assert chip.read(4) == 1
    chip.set_input(1, 1)
    eval_chip(chip)
    assert chip.read(4) == 0
    chip.set_input(15, 1)
    eval_chip(chip)
    assert chip.read(4) == 0


def test_hc283():
    chip = create_chip("74HC283", "U")
    set_byte(chip, [5, 3, 14, 12], 0xF)
    set_byte(chip, [6, 2, 15, 11], 0x1)
    chip.set_input(7, 0)
    eval_chip(chip)
    assert get_byte(chip, [4, 1, 13, 10]) == 0
    assert chip.read(9) == 1


def test_hc688():
    chip = create_chip("74HC688", "U")
    set_byte(chip, [2, 4, 6, 8, 12, 14, 16, 18], 0x42)
    set_byte(chip, [3, 5, 7, 9, 11, 13, 15, 17], 0x42)
    chip.set_input(1, 0)
    eval_chip(chip)
    assert chip.read(19) == 0
    chip.set_input(17, 1)
    eval_chip(chip)
    assert chip.read(19) == 1


def test_hc541_and_hc245_tristate():
    buf = create_chip("74HC541", "U")
    set_byte(buf, [2, 3, 4, 5, 6, 7, 8, 9], 0xA5)
    set_pins(buf, [1, 19], [0, 0])
    eval_chip(buf)
    assert get_byte(buf, [18, 17, 16, 15, 14, 13, 12, 11]) == 0xA5
    buf.set_input(1, 1)
    eval_chip(buf)
    assert buf.read(18) == Z

    trans = create_chip("74HC245", "U")
    set_byte(trans, [2, 3, 4, 5, 6, 7, 8, 9], 0x3C)
    set_pins(trans, [1, 19], [1, 0])
    eval_chip(trans)
    assert get_byte(trans, [18, 17, 16, 15, 14, 13, 12, 11]) == 0x3C


def test_hc574_hc161_hc164_hc74():
    reg = create_chip("74HC574", "U")
    reg.set_input(1, 0)
    set_byte(reg, [2, 3, 4, 5, 6, 7, 8, 9], 0x5A)
    reg.clock_edge()
    reg.commit()
    assert get_byte(reg, [19, 18, 17, 16, 15, 14, 13, 12]) == 0x5A

    ctr = create_chip("74HC161", "U")
    set_pins(ctr, [1, 9, 7, 10], [1, 1, 1, 1])
    ctr.clock_edge()
    ctr.commit()
    assert get_byte(ctr, [14, 13, 12, 11]) == 1
    ctr.set_input(1, 0)
    eval_chip(ctr)
    assert get_byte(ctr, [14, 13, 12, 11]) == 0

    sr = create_chip("74HC164", "U")
    set_pins(sr, [9, 1, 2], [1, 1, 1])
    sr.clock_edge()
    sr.commit()
    assert sr.read(3) == 1
    sr.set_input(9, 0)
    eval_chip(sr)
    assert get_byte(sr, [3, 4, 5, 6, 10, 11, 12, 13]) == 0

    ff = create_chip("74HC74", "U")
    set_pins(ff, [1, 4, 2], [1, 1, 1])
    ff.clock_edge()
    ff.commit()
    assert ff.read(5) == 1
    assert ff.read(6) == 0


def test_memory():
    rom = create_chip("AT28C256", "ROM")
    rom.data[0x1234] = 0xAB
    assert rom.pin_number("A0") == 10
    assert rom.pin_number("I/O7") == 19
    assert rom.pin_number("/WE") == 27
    set_memory_addr(rom, 0x1234)
    set_pins(rom, [20, 22, 27], [0, 0, 1])
    eval_chip(rom)
    assert get_byte(rom, MEMORY_DQ_PINS) == 0xAB
    set_memory_addr(rom, 0x1235)
    set_byte(rom, MEMORY_DQ_PINS, 0x56)
    set_pins(rom, [20, 22, 27], [0, 1, 0])
    eval_chip(rom)
    set_pins(rom, [22, 27], [0, 1])
    eval_chip(rom)
    assert get_byte(rom, MEMORY_DQ_PINS) == 0x56
    rom.set_input(20, 1)
    eval_chip(rom)
    assert rom.read(11) == Z

    ram = create_chip("62256", "RAM")
    assert ram.pin_number("A14") == 1
    assert ram.pin_number("I/O0") == 11
    assert ram.pin_number("/CE") == 20
    set_memory_addr(ram, 0x2345)
    set_byte(ram, MEMORY_DQ_PINS, 0xC3)
    set_pins(ram, [20, 22, 27], [0, 1, 0])
    eval_chip(ram)
    set_pins(ram, [22, 27], [0, 1])
    eval_chip(ram)
    assert get_byte(ram, MEMORY_DQ_PINS) == 0xC3


def test_memory_image_loader():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        bin_path = tmp_path / "program.bin"
        bin_path.write_bytes(bytes([0x30, 0x42, 0x01, 0x02]))
        assert load_image(bin_path) == bytes([0x30, 0x42, 0x01, 0x02])

        hex_path = tmp_path / "program.hex"
        hex_path.write_text("30 42 01 02  # LI 42, HLT\n")
        assert load_image(hex_path) == bytes([0x30, 0x42, 0x01, 0x02])

        ihex_path = tmp_path / "program_ihex.hex"
        ihex_path.write_text(":040010003042010277\n:00000001FF\n")
        ihex = load_image(ihex_path)
        assert ihex[0x10:0x14] == bytes([0x30, 0x42, 0x01, 0x02])

        rom = create_chip("AT28C256", "ROM")
        copied = load_memory(rom, bin_path, offset=0x20, clear=0xFF)
        assert copied == 4
        assert rom.data[0x1F] == 0xFF
        assert rom.data[0x20:0x24] == bytes([0x30, 0x42, 0x01, 0x02])

        ram = create_chip("62256", "RAM")
        load_memory(ram, hex_path)
        assert ram.data[:4] == bytes([0x30, 0x42, 0x01, 0x02])

        too_large = tmp_path / "too_large.bin"
        too_large.write_bytes(bytes(len(ram.data) + 1))
        try:
            load_memory(ram, too_large)
        except ImageLoadError:
            pass
        else:
            raise AssertionError("expected ImageLoadError for oversized image")


def test_board_delay_and_bus_conflict():
    board = Board()
    inv = board.add_chip("U1", create_chip("74HC04", "U1"))
    board.drive(inv, 1, 1)
    board.settle()
    assert inv.read(2) == 0
    assert board.time_ns == 12

    a = board.add_chip("A", create_chip("74HC541", "A"))
    b = board.add_chip("B", create_chip("74HC541", "B"))
    board.connect("BUS0", a, 18)
    board.connect("BUS0", b, 18)
    a.drive_output(18, 1)
    try:
        b.drive_output(18, 0)
    except BusConflictError:
        pass
    else:
        raise AssertionError("expected bus conflict")


def test_stimulus_inputs_and_clocks():
    board = Board()
    nand = board.add_chip("U1", create_chip("74HC00", "U1"))
    reg = board.add_chip("U2", create_chip("74HC574", "U2"))
    stimulus = StimulusController(board)

    assert len(stimulus.inputs) == 64
    assert len(stimulus.clocks) == 8

    stimulus.bind_input(0, nand, "1A", initial=1)
    stimulus.bind_input(1, nand, "1B", initial=1)
    board.settle()
    assert nand.read("1Y") == 0

    stimulus.input(1).set(0)
    board.settle()
    assert nand.read("1Y") == 1

    for i, pin in enumerate([2, 3, 4, 5, 6, 7, 8, 9]):
        stimulus.bind_input(i, reg, pin)
    stimulus.set_inputs(0xA5, width=8)
    reg.set_input("/OE", 0)

    clk0 = stimulus.bind_clock(0, reg, "CLK")
    clk0.trigger(width_ns=50)
    assert get_byte(reg, [19, 18, 17, 16, 15, 14, 13, 12]) == 0xA5

    inv = board.add_chip("U3", create_chip("74HC04", "U3"))
    clk1 = stimulus.bind_clock(1, inv, "1A")
    clk1.configure(period_ns=100, duty=0.5).start()
    start = board.time_ns
    stimulus.run_for(250)
    assert board.time_ns >= start + 250
    assert clk1.next_edge_ns is not None
    assert stimulus.snapshot()["clocks"][1]["period_ns"] == 100


def test_datasheet_clock_edges_and_independent_clock_pins():
    board = Board()
    stimulus = StimulusController(board)

    jk = board.add_chip("JK", create_chip("74HC73", "JK"))
    jk.set_input("1R", 1)
    jk.set_input("1J", 1)
    jk.set_input("1K", 1)
    board.settle()
    assert jk.read("1Q") == 0

    jk_clk = stimulus.bind_clock(0, jk, "1CP", initial=0)
    jk_clk.configure(period_ns=100, duty=0.5).start(start_high=False)
    stimulus.run_for(50)
    assert jk.read("1Q") == 0
    stimulus.run_for(50)
    assert jk.read("1Q") == 1

    dff = board.add_chip("DFF", create_chip("74HC74", "DFF"))
    set_pins(dff, ["/CLR1", "/PR1", "/CLR2", "/PR2"], [1, 1, 1, 1])
    dff.set_input("D1", 1)
    dff.set_input("D2", 0)
    dff.update()
    dff.commit()

    clk1 = stimulus.bind_clock(1, dff, "CLK1", initial=0)
    clk1.trigger(width_ns=10)
    assert dff.read("Q1") == 1
    assert dff.read("Q2") == 0

    dff.set_input("D2", 1)
    clk2 = stimulus.bind_clock(2, dff, "CLK2", initial=0)
    clk2.trigger(width_ns=10)
    assert dff.read("Q2") == 1

    sr = board.add_chip("SR", create_chip("74HC595", "SR"))
    sr.set_input("/SRCLR", 1)
    sr.set_input("/OE", 0)
    sr.set_input("SER", 1)
    srclk = stimulus.bind_clock(3, sr, "SRCLK", initial=0)
    rclk = stimulus.bind_clock(4, sr, "RCLK", initial=0)
    board.settle()
    srclk.trigger(width_ns=10)
    assert sr.read("QA") == 0
    rclk.trigger(width_ns=10)
    assert sr.read("QA") == 1


def test_all_component_parts_instantiate():
    root = Path(__file__).resolve().parents[2]
    parts = sorted(p.stem.upper() for p in (root / "74HC").glob("74hc*.v"))
    parts += sorted(p.stem.upper() for p in (root / "Memory").glob("*.v"))
    assert parts, "no Components parts found"
    for part in parts:
        chip = create_chip(part, "U")
        assert chip.pins, part
        assert chip.delay.rise_ns > 0, part
        assert all(pin.spec.name for pin in chip.pins.values()), part


def test_catalog_behavior_smoke():
    root = Path(__file__).resolve().parents[2]
    parts = sorted(p.stem.upper() for p in (root / "74HC").glob("74hc*.v"))
    parts += sorted(p.stem.upper() for p in (root / "Memory").glob("*.v"))
    for part in parts:
        chip = create_chip(part, "U")
        chip.update()
        chip.commit()
        chip.clock_edge()
        chip.commit()

    nor = create_chip("74HC02", "U")
    set_pins(nor, ["1A", "1B"], [0, 0])
    eval_chip(nor)
    assert nor.read("1Y") == 1
    nor.set_input("1A", 1)
    eval_chip(nor)
    assert nor.read("1Y") == 0

    dec = create_chip("74HC138", "U")
    set_pins(dec, ["G1", "/G2A", "/G2B", "A", "B", "C"], [1, 0, 0, 1, 1, 0])
    eval_chip(dec)
    assert dec.read("/Y3") == 0
    assert dec.read("/Y2") == 1

    tri = create_chip("74HC244", "U")
    set_pins(tri, ["/1OE", "/2OE", "1A1", "2A1"], [0, 1, 1, 1])
    eval_chip(tri)
    assert tri.read("1Y1") == 1
    assert tri.read("2Y1") == Z

    reg = create_chip("74HC273", "U")
    set_pins(reg, ["/CLR", "1D", "2D"], [1, 1, 0])
    reg.clock_edge()
    reg.commit()
    assert reg.read("1Q") == 1
    reg.set_input("/CLR", 0)
    eval_chip(reg)
    assert reg.read("1Q") == 0

    flash = create_chip("SST39SF010A", "U")
    set_pins(flash, ["/CE", "/OE", "/WE"], [0, 1, 0])
    set_byte(flash, [f"DQ{i}" for i in range(8)], 0xA7)
    eval_chip(flash)
    set_pins(flash, ["/OE", "/WE"], [0, 1])
    eval_chip(flash)
    assert get_byte(flash, [f"DQ{i}" for i in range(8)]) == 0xA7


def run_all():
    test_hc00()
    test_hc04()
    test_hc21_hc32_hc86()
    test_hc157()
    test_hc283()
    test_hc688()
    test_hc541_and_hc245_tristate()
    test_hc574_hc161_hc164_hc74()
    test_memory()
    test_memory_image_loader()
    test_board_delay_and_bus_conflict()
    test_stimulus_inputs_and_clocks()
    test_datasheet_clock_edges_and_independent_clock_pins()
    test_all_component_parts_instantiate()
    test_catalog_behavior_smoke()


if __name__ == "__main__":
    run_all()
    print("Components Python chip tests passed")
