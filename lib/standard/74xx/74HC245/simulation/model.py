"""Local behavior model for 74HC245."""

from __future__ import annotations

from chiplib.core import Chip, Delay, Z, bit, pins_from


class HC245(Chip):
    part = "74HC245"

    def __init__(self, name: str = "U"):
        pins = {1: ("DIR", "in"), 19: ("/OE", "in"), 10: ("GND", "power"), 20: ("VCC", "power")}
        for index in range(8):
            pins[2 + index] = (f"A{index + 1}", "bidir")
            pins[18 - index] = (f"B{index + 1}", "bidir")
        super().__init__(name, pins_from(pins), Delay(12))

    def update(self) -> None:
        if bit(self.read(19)):
            for index in range(8):
                self.output(2 + index, Z)
                self.output(18 - index, Z)
            return
        a_to_b = bit(self.read(1)) == 1
        for index in range(8):
            a_pin = 2 + index
            b_pin = 18 - index
            if a_to_b:
                self.output(a_pin, Z)
                self.output(b_pin, self.read(a_pin))
            else:
                self.output(b_pin, Z)
                self.output(a_pin, self.read(b_pin))


def create(name: str = "U") -> HC245:
    return HC245(name)
