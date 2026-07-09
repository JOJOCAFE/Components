"""Local behavior model for 74HC164."""

from __future__ import annotations

from chiplib.core import Chip, Delay, Z, bit, pins_from


class HC164(Chip):
    part = "74HC164"

    def __init__(self, name: str):
        pins = {1: ("A", "in"), 2: ("B", "in"), 3: ("QA", "out"), 4: ("QB", "out"), 5: ("QC", "out"), 6: ("QD", "out"), 7: ("GND", "power"), 8: ("CLK", "in"), 9: ("/CLR", "in"), 10: ("QE", "out"), 11: ("QF", "out"), 12: ("QG", "out"), 13: ("QH", "out"), 14: ("VCC", "power")}
        super().__init__(name, pins_from(pins), Delay(20))

        self._sr = [0] * 8
        self._q_pins = [3, 4, 5, 6, 10, 11, 12, 13]

    def clock_edge(self, pin: int | str | None = None) -> None:
        if not bit(self.read(9)):
            self._sr = [0] * 8
        else:
            self._sr = [bit(self.read(1)) & bit(self.read(2))] + self._sr[:7]
        self.update()

    def update(self) -> None:
        if not bit(self.read(9)):
            self._sr = [0] * 8
        for index, pin in enumerate(self._q_pins):
            self.output(pin, self._sr[index])



def create(name: str = "U") -> HC164:
    return HC164(name)
