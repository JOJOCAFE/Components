"""Local behavior model for SST39SF010A."""

from __future__ import annotations

from chiplib.core import Chip, Delay, Z, bit, pins_from


class SST39SF010A(Chip):
    part = "SST39SF010A"

    def __init__(self, name: str):
        pins = {1: ("NC", "nc"), 2: ("A16", "in"), 3: ("A15", "in"), 4: ("A12", "in"), 5: ("A7", "in"), 6: ("A6", "in"), 7: ("A5", "in"), 8: ("A4", "in"), 9: ("A3", "in"), 10: ("A2", "in"), 11: ("A1", "in"), 12: ("A0", "in"), 13: ("DQ0", "bidir"), 14: ("DQ1", "bidir"), 15: ("DQ2", "bidir"), 16: ("VSS", "power"), 17: ("DQ3", "bidir"), 18: ("DQ4", "bidir"), 19: ("DQ5", "bidir"), 20: ("DQ6", "bidir"), 21: ("DQ7", "bidir"), 22: ("/CE", "in"), 23: ("A10", "in"), 24: ("/OE", "in"), 25: ("A11", "in"), 26: ("A9", "in"), 27: ("A8", "in"), 28: ("A13", "in"), 29: ("A14", "in"), 30: ("NC", "nc"), 31: ("/WE", "in"), 32: ("VDD", "power")}
        super().__init__(name, pins_from(pins), Delay(70))

        self.data = bytearray(131072)

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


MEMORY_ADDR_PINS = {0: 12, 1: 11, 2: 10, 3: 9, 4: 8, 5: 7, 6: 6, 7: 5, 8: 27, 9: 26, 10: 23, 11: 25, 12: 4, 13: 28, 14: 29, 15: 3, 16: 2}
MEMORY_DQ_PINS = [13, 14, 15, 17, 18, 19, 20, 21]


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



def create(name: str = "U") -> SST39SF010A:
    return SST39SF010A(name)
