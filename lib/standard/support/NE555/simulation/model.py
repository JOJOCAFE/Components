"""Local functional model for NE555 timer.

This models the internal latch at logic level: RESET low clears, THRESH high
resets, TRIG low sets. DISCH is open collector: low when the output is low,
high-Z when the timing capacitor is released.
"""

from __future__ import annotations

from chiplib.core import Chip, Delay, Z, bit, pins_from


class NE555(Chip):
    part = "NE555"

    def __init__(self, name: str = "U"):
        pins = {
            1: ("GND", "power"),
            2: ("TRIG", "in"),
            3: ("OUT", "out"),
            4: ("RESET", "in"),
            5: ("CTRL", "passive"),
            6: ("THRESH", "in"),
            7: ("DISCH", "out"),
            8: ("VCC", "power"),
        }
        super().__init__(name, pins_from(pins), Delay(1))
        self._out = 0

    def update(self) -> None:
        if not bit(self.read("RESET")):
            self._out = 0
        elif bit(self.read("THRESH")):
            self._out = 0
        elif not bit(self.read("TRIG")):
            self._out = 1
        self.output("OUT", self._out)
        self.output("DISCH", Z if self._out else 0)


def create(name: str = "U") -> NE555:
    return NE555(name)
