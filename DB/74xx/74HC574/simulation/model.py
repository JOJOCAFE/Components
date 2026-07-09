"""Local behavior model for 74HC574."""

from __future__ import annotations

from chiplib.core import Chip, Delay, Z, bit, pins_from


class HC574(Chip):
    part = "74HC574"

    def __init__(self, name: str = "U"):
        pins = {1: ("/OE", "in"), 11: ("CLK", "in"), 10: ("GND", "power"), 20: ("VCC", "power")}
        for index in range(8):
            pins[2 + index] = (f"D{index + 1}", "in")
            pins[19 - index] = (f"Q{index + 1}", "out")
        super().__init__(name, pins_from(pins), Delay(20))
        self._reg = [0] * 8

    def clock_edge(self, pin: int | str | None = None) -> None:
        self._reg = [bit(self.read(2 + index)) for index in range(8)]
        self.update()

    def update(self) -> None:
        enabled = not bit(self.read(1))
        for index in range(8):
            self.output(19 - index, self._reg[index] if enabled else Z)


def create(name: str = "U") -> HC574:
    return HC574(name)
