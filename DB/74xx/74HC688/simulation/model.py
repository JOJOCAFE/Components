"""Local behavior model for 74HC688."""

from __future__ import annotations

from chiplib.core import Chip, Delay, Z, bit, pins_from


class HC688(Chip):
    part = "74HC688"

    def __init__(self, name: str):
        pins = {1: ("/E", "in"), 2: ("A0", "in"), 3: ("B0", "in"), 4: ("A1", "in"), 5: ("B1", "in"), 6: ("A2", "in"), 7: ("B2", "in"), 8: ("A3", "in"), 9: ("B3", "in"), 10: ("GND", "power"), 11: ("A4", "in"), 12: ("B4", "in"), 13: ("A5", "in"), 14: ("B5", "in"), 15: ("A6", "in"), 16: ("B6", "in"), 17: ("A7", "in"), 18: ("B7", "in"), 19: ("Y", "out"), 20: ("VCC", "power")}
        super().__init__(name, pins_from(pins), Delay(30))

    def update(self) -> None:
        if bit(self.read(1)):
            self.output(19, 1)
            return
        p_value = _byte_from_pins(self, [2, 4, 6, 8, 11, 13, 15, 17])
        q_value = _byte_from_pins(self, [3, 5, 7, 9, 12, 14, 16, 18])
        self.output(19, 0 if p_value == q_value else 1)


def _byte_from_pins(chip: Chip, pins: list[int]) -> int:
    value = 0
    for index, pin in enumerate(pins):
        value |= bit(chip.read(pin)) << index
    return value



def create(name: str = "U") -> HC688:
    return HC688(name)
