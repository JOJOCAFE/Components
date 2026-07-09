"""Local behavior model for 74HC157."""

from __future__ import annotations

from chiplib.core import Chip, Delay, bit, pins_from


class HC157(Chip):
    part = "74HC157"

    def __init__(self, name: str = "U"):
        pins = {
            1: ("SEL", "in"), 2: ("1A", "in"), 3: ("1B", "in"), 4: ("1Y", "out"),
            5: ("2A", "in"), 6: ("2B", "in"), 7: ("2Y", "out"), 8: ("GND", "power"),
            9: ("3Y", "out"), 10: ("3B", "in"), 11: ("3A", "in"), 12: ("4Y", "out"),
            13: ("4B", "in"), 14: ("4A", "in"), 15: ("/E", "in"), 16: ("VCC", "power"),
        }
        super().__init__(name, pins_from(pins), Delay(18))

    def update(self) -> None:
        if bit(self.read(15)):
            for y_pin in (4, 7, 9, 12):
                self.output(y_pin, 0)
            return
        select_b = bit(self.read(1))
        for a_pin, b_pin, y_pin in ((2, 3, 4), (5, 6, 7), (11, 10, 9), (14, 13, 12)):
            self.output(y_pin, bit(self.read(b_pin if select_b else a_pin)))


def create(name: str = "U") -> HC157:
    return HC157(name)
