"""Local behavior model for 74HC86."""

from __future__ import annotations

from chiplib.core import Chip, Delay, Z, bit, pins_from


class HC86(Chip):
    part = "74HC86"

    def __init__(self, name: str):
        pins = {1: ("1A", "in"), 2: ("1B", "in"), 3: ("1Y", "out"), 4: ("2A", "in"), 5: ("2B", "in"), 6: ("2Y", "out"), 7: ("GND", "power"), 8: ("3Y", "out"), 9: ("3A", "in"), 10: ("3B", "in"), 11: ("4Y", "out"), 12: ("4A", "in"), 13: ("4B", "in"), 14: ("VCC", "power")}
        super().__init__(name, pins_from(pins), Delay(15))

    def update(self) -> None:
        for a, b, y in [(1, 2, 3), (4, 5, 6), (9, 10, 8), (12, 13, 11)]:
            self.output(y, bit(self.read(a)) ^ bit(self.read(b)))



def create(name: str = "U") -> HC86:
    return HC86(name)
