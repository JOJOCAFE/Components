"""Local functional model for LM358 dual op amp.

This is a simple saturated comparator-style model for logic-level learning
circuits. It is not a SPICE op-amp macro-model.
"""

from __future__ import annotations

from chiplib.core import Chip, Delay, bit, pins_from


class LM358(Chip):
    part = "LM358"

    def __init__(self, name: str = "U"):
        pins = {
            1: ("OUT1", "out"),
            2: ("IN1-", "in"),
            3: ("IN1+", "in"),
            4: ("VSS", "power"),
            5: ("IN2+", "in"),
            6: ("IN2-", "in"),
            7: ("OUT2", "out"),
            8: ("VCC", "power"),
        }
        super().__init__(name, pins_from(pins), Delay(1))

    def update(self) -> None:
        self.output("OUT1", 1 if bit(self.read("IN1+")) > bit(self.read("IN1-")) else 0)
        self.output("OUT2", 1 if bit(self.read("IN2+")) > bit(self.read("IN2-")) else 0)


def create(name: str = "U") -> LM358:
    return LM358(name)
