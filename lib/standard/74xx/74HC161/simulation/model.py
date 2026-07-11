"""Local behavior model for 74HC161."""

from __future__ import annotations

from chiplib.core import Chip, Delay, bit, pins_from


def byte_from_pins(chip: Chip, pins: list[int]) -> int:
    value = 0
    for index, pin in enumerate(pins):
        value |= bit(chip.read(pin)) << index
    return value


def write_pins(chip: Chip, pins: list[int], value: int) -> None:
    for index, pin in enumerate(pins):
        chip.output(pin, (value >> index) & 1)


class HC161(Chip):
    part = "74HC161"

    def __init__(self, name: str = "U"):
        pins = {
            1: ("/CLR", "in"), 2: ("CLK", "in"), 3: ("A", "in"), 4: ("B", "in"),
            5: ("C", "in"), 6: ("D", "in"), 7: ("ENP", "in"), 8: ("GND", "power"),
            9: ("/LOAD", "in"), 10: ("ENT", "in"), 11: ("QD", "out"), 12: ("QC", "out"),
            13: ("QB", "out"), 14: ("QA", "out"), 15: ("RCO", "out"), 16: ("VCC", "power"),
        }
        super().__init__(name, pins_from(pins), Delay(22))
        self._count = 0

    def clock_edge(self, pin: int | str | None = None) -> None:
        if not bit(self.read(1)):
            self._count = 0
        elif not bit(self.read(9)):
            self._count = byte_from_pins(self, [3, 4, 5, 6])
        elif bit(self.read(7)) and bit(self.read(10)):
            self._count = (self._count + 1) & 0xF
        self.update()

    def update(self) -> None:
        if not bit(self.read(1)):
            self._count = 0
        write_pins(self, [14, 13, 12, 11], self._count)
        self.output(15, 1 if self._count == 0xF and bit(self.read(10)) else 0)


def create(name: str = "U") -> HC161:
    return HC161(name)
