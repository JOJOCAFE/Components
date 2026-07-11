"""Local behavior model for AS6C62256."""

from __future__ import annotations

from chiplib.core import Chip, Delay, Z, bit, pins_from


class AS6C62256(Chip):
    part = "AS6C62256"

    def __init__(self, name: str):
        pins = {1: ("A14", "in"), 2: ("A12", "in"), 3: ("A7", "in"), 4: ("A6", "in"), 5: ("A5", "in"), 6: ("A4", "in"), 7: ("A3", "in"), 8: ("A2", "in"), 9: ("A1", "in"), 10: ("A0", "in"), 11: ("I/O0", "bidir"), 12: ("I/O1", "bidir"), 13: ("I/O2", "bidir"), 14: ("GND", "power"), 15: ("I/O3", "bidir"), 16: ("I/O4", "bidir"), 17: ("I/O5", "bidir"), 18: ("I/O6", "bidir"), 19: ("I/O7", "bidir"), 20: ("/CE", "in"), 21: ("A10", "in"), 22: ("/OE", "in"), 23: ("A11", "in"), 24: ("A9", "in"), 25: ("A8", "in"), 26: ("A13", "in"), 27: ("/WE", "in"), 28: ("VCC", "power")}
        super().__init__(name, pins_from(pins), Delay(55))

        self.data = bytearray(32768)

    def update(self) -> None:
        selected = not bit(self.read("/CE"))
        address = _memory_address(self)
        if selected and not bit(self.read("/WE")):
            self.data[address] = _byte_from_pins(self, MEMORY_DQ_PINS)
        read_enabled = selected and bit(self.read("/WE")) and not bit(self.read("/OE"))
        if read_enabled:
            _write_pins(self, MEMORY_DQ_PINS, self.data[address])
        else:
            for pin in MEMORY_DQ_PINS:
                self.output(pin, Z)


MEMORY_ADDR_PINS = {0: 10, 1: 9, 2: 8, 3: 7, 4: 6, 5: 5, 6: 4, 7: 3, 8: 25, 9: 24, 10: 21, 11: 23, 12: 2, 13: 26, 14: 1}
MEMORY_DQ_PINS = [11, 12, 13, 15, 16, 17, 18, 19]


def _memory_address(chip: Chip) -> int:
    value = 0
    for index, pin in MEMORY_ADDR_PINS.items():
        value |= bit(chip.read(pin)) << index
    return value


def _byte_from_pins(chip: Chip, pins: list[int]) -> int:
    value = 0
    for index, pin in enumerate(pins):
        value |= bit(chip.read(pin)) << index
    return value


def _write_pins(chip: Chip, pins: list[int], value: int) -> None:
    for index, pin in enumerate(pins):
        chip.output(pin, (value >> index) & 1)



def create(name: str = "U") -> AS6C62256:
    return AS6C62256(name)
