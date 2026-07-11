"""Local behavior model for 74HC541."""

from __future__ import annotations

from chiplib.core import Chip, Delay, Z, bit, pins_from


class HC541(Chip):
    part = "74HC541"

    def __init__(self, name: str):
        pins = {1: ("/OE1", "in"), 2: ("A1", "in"), 3: ("A2", "in"), 4: ("A3", "in"), 5: ("A4", "in"), 6: ("A5", "in"), 7: ("A6", "in"), 8: ("A7", "in"), 9: ("A8", "in"), 10: ("GND", "power"), 11: ("Y8", "out"), 12: ("Y7", "out"), 13: ("Y6", "out"), 14: ("Y5", "out"), 15: ("Y4", "out"), 16: ("Y3", "out"), 17: ("Y2", "out"), 18: ("Y1", "out"), 19: ("/OE2", "in"), 20: ("VCC", "power")}
        super().__init__(name, pins_from(pins), Delay(12))

    def update(self) -> None:
        enabled = not bit(self.read(1)) and not bit(self.read(19))
        for index in range(8):
            self.output(18 - index, bit(self.read(2 + index)) if enabled else Z)



def create(name: str = "U") -> HC541:
    return HC541(name)
