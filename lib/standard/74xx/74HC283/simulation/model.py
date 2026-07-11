"""Local behavior model for 74HC283."""

from __future__ import annotations

from chiplib.core import Chip, Delay, Z, bit, pins_from


class HC283(Chip):
    part = "74HC283"

    def __init__(self, name: str):
        pins = {1: ("S2", "out"), 2: ("B2", "in"), 3: ("A2", "in"), 4: ("S1", "out"), 5: ("A1", "in"), 6: ("B1", "in"), 7: ("C0", "in"), 8: ("GND", "power"), 9: ("C4", "out"), 10: ("S4", "out"), 11: ("B4", "in"), 12: ("A4", "in"), 13: ("S3", "out"), 14: ("A3", "in"), 15: ("B3", "in"), 16: ("VCC", "power")}
        super().__init__(name, pins_from(pins), Delay(35))

    def update(self) -> None:
        a = _byte_from_pins(self, [5, 3, 14, 12])
        b = _byte_from_pins(self, [6, 2, 15, 11])
        result = a + b + bit(self.read(7))
        _write_pins(self, [4, 1, 13, 10], result)
        self.output(9, (result >> 4) & 1)


def _byte_from_pins(chip: Chip, pins: list[int]) -> int:
    value = 0
    for index, pin in enumerate(pins):
        value |= bit(chip.read(pin)) << index
    return value


def _write_pins(chip: Chip, pins: list[int], value: int) -> None:
    for index, pin in enumerate(pins):
        chip.output(pin, (value >> index) & 1)



def create(name: str = "U") -> HC283:
    return HC283(name)
