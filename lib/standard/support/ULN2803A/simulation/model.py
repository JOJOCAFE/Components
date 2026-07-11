"""Local functional model for ULN2803A Darlington sink array.

Each output is modeled as open collector: input high drives the paired collector
low, input low releases it to high-Z.
"""

from __future__ import annotations

from chiplib.core import Chip, Delay, Z, bit, pins_from


class ULN2803A(Chip):
    part = "ULN2803A"

    def __init__(self, name: str = "U"):
        pins = {
            1: ("1B", "in"),
            2: ("2B", "in"),
            3: ("3B", "in"),
            4: ("4B", "in"),
            5: ("5B", "in"),
            6: ("6B", "in"),
            7: ("7B", "in"),
            8: ("8B", "in"),
            9: ("GND", "power"),
            10: ("COM", "passive"),
            11: ("8C", "out"),
            12: ("7C", "out"),
            13: ("6C", "out"),
            14: ("5C", "out"),
            15: ("4C", "out"),
            16: ("3C", "out"),
            17: ("2C", "out"),
            18: ("1C", "out"),
        }
        super().__init__(name, pins_from(pins), Delay(1))

    def update(self) -> None:
        for channel in range(1, 9):
            self.output(f"{channel}C", 0 if bit(self.read(f"{channel}B")) else Z)


def create(name: str = "U") -> ULN2803A:
    return ULN2803A(name)
