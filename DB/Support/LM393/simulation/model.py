"""Local functional model for LM393 dual comparator.

Outputs are modeled as open-collector: low when asserted, high-Z when released.
"""

from __future__ import annotations

from chiplib.core import Chip, Delay, Z, bit, pins_from


class LM393(Chip):
    part = "LM393"

    def __init__(self, name: str = "U"):
        pins = {
            1: ("OUT1", "out"),
            2: ("IN1-", "in"),
            3: ("IN1+", "in"),
            4: ("GND", "power"),
            5: ("IN2+", "in"),
            6: ("IN2-", "in"),
            7: ("OUT2", "out"),
            8: ("VCC", "power"),
        }
        super().__init__(name, pins_from(pins), Delay(1))

    def update(self) -> None:
        self.output("OUT1", Z if bit(self.read("IN1+")) > bit(self.read("IN1-")) else 0)
        self.output("OUT2", Z if bit(self.read("IN2+")) > bit(self.read("IN2-")) else 0)


def create(name: str = "U") -> LM393:
    return LM393(name)
