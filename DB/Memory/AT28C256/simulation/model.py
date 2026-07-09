"""Local behavior model for AT28C256."""

from __future__ import annotations

from chiplib.core import Chip, Delay, Z, bit, pins_from

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


def memory_28_pin_defs(data_direction: str) -> dict[int, tuple[str, str]]:
    pins = {
        14: ("GND", "power"),
        20: ("/CE", "in"),
        22: ("/OE", "in"),
        27: ("/WE", "in"),
        28: ("VCC", "power"),
    }
    for bit_index, pin in MEMORY_ADDR_PINS.items():
        pins[pin] = (f"A{bit_index}", "in")
    for bit_index, pin in enumerate(MEMORY_DQ_PINS):
        pins[pin] = (f"I/O{bit_index}", data_direction)
    return pins


def memory_address(chip: Chip) -> int:
    value = 0
    for bit_index, pin in MEMORY_ADDR_PINS.items():
        value |= bit(chip.read(pin)) << bit_index
    return value


def byte_from_pins(chip: Chip, pins: list[int]) -> int:
    value = 0
    for index, pin in enumerate(pins):
        value |= bit(chip.read(pin)) << index
    return value


def write_pins(chip: Chip, pins: list[int], value: int) -> None:
    for index, pin in enumerate(pins):
        chip.output(pin, (value >> index) & 1)


class AT28C256(Chip):
    part = "AT28C256"

    def __init__(self, name: str = "U"):
        super().__init__(name, pins_from(memory_28_pin_defs("bidir")), Delay(70))
        self.data = bytearray(32768)

    def update(self) -> None:
        selected = not bit(self.read("/CE"))
        if selected and bit(self.read("/OE")) and not bit(self.read("/WE")):
            self.data[memory_address(self)] = byte_from_pins(self, MEMORY_DQ_PINS)
        read_enabled = selected and not bit(self.read("/OE")) and bit(self.read("/WE"))
        if not read_enabled:
            for pin in MEMORY_DQ_PINS:
                self.output(pin, Z)
            return
        write_pins(self, MEMORY_DQ_PINS, self.data[memory_address(self)])


def create(name: str = "U") -> AT28C256:
    return AT28C256(name)
