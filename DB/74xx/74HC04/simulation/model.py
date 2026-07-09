"""Local behavior model for 74HC04."""

from __future__ import annotations

from chiplib.core import Chip, Delay, Z, bit, pins_from


class HC04(Chip):
    part = "74HC04"

    def __init__(self, name: str):
        pins = {1: ("1A", "in"), 2: ("1Y", "out"), 3: ("2A", "in"), 4: ("2Y", "out"), 5: ("3A", "in"), 6: ("3Y", "out"), 7: ("GND", "power"), 8: ("4Y", "out"), 9: ("4A", "in"), 10: ("5Y", "out"), 11: ("5A", "in"), 12: ("6Y", "out"), 13: ("6A", "in"), 14: ("VCC", "power")}
        super().__init__(name, pins_from(pins), Delay(12))

    def update(self) -> None:
        for a, y in [(1, 2), (3, 4), (5, 6), (9, 8), (11, 10), (13, 12)]:
            self.output(y, 1 - bit(self.read(a)))



def create(name: str = "U") -> HC04:
    return HC04(name)
