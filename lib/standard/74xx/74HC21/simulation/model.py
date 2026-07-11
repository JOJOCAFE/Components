"""Local behavior model for 74HC21."""

from __future__ import annotations

from chiplib.core import Chip, Delay, Z, bit, pins_from


class HC21(Chip):
    part = "74HC21"

    def __init__(self, name: str):
        pins = {1: ("1A", "in"), 2: ("1B", "in"), 3: ("NC", "nc"), 4: ("1C", "in"), 5: ("1D", "in"), 6: ("1Y", "out"), 7: ("GND", "power"), 8: ("2Y", "out"), 9: ("2A", "in"), 10: ("2B", "in"), 11: ("NC", "nc"), 12: ("2C", "in"), 13: ("2D", "in"), 14: ("VCC", "power")}
        super().__init__(name, pins_from(pins), Delay(15))

    def update(self) -> None:
        self.output(6, bit(self.read(1)) & bit(self.read(2)) & bit(self.read(4)) & bit(self.read(5)))
        self.output(8, bit(self.read(9)) & bit(self.read(10)) & bit(self.read(12)) & bit(self.read(13)))



def create(name: str = "U") -> HC21:
    return HC21(name)
