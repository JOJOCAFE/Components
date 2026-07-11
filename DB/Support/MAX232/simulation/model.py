"""Local functional model for MAX232 RS-232 transceiver.

The charge-pump pins are package/passive pins here. Logic behavior is modeled as
inverting TTL-to-RS232 drivers and inverting RS232-to-TTL receivers.
"""

from __future__ import annotations

from chiplib.core import Chip, Delay, bit, pins_from


class MAX232(Chip):
    part = "MAX232"

    def __init__(self, name: str = "U"):
        pins = {
            1: ("C1+", "passive"),
            2: ("V+", "passive"),
            3: ("C1-", "passive"),
            4: ("C2+", "passive"),
            5: ("C2-", "passive"),
            6: ("V-", "passive"),
            7: ("T2OUT", "out"),
            8: ("R2IN", "in"),
            9: ("R2OUT", "out"),
            10: ("T2IN", "in"),
            11: ("T1IN", "in"),
            12: ("R1OUT", "out"),
            13: ("R1IN", "in"),
            14: ("T1OUT", "out"),
            15: ("GND", "power"),
            16: ("VCC", "power"),
        }
        super().__init__(name, pins_from(pins), Delay(1))

    def update(self) -> None:
        self.output("T1OUT", 1 - bit(self.read("T1IN")))
        self.output("T2OUT", 1 - bit(self.read("T2IN")))
        self.output("R1OUT", 1 - bit(self.read("R1IN")))
        self.output("R2OUT", 1 - bit(self.read("R2IN")))


def create(name: str = "U") -> MAX232:
    return MAX232(name)
