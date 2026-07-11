"""Local behavior model for 74HC74."""

from __future__ import annotations

from chiplib.core import Chip, Delay, Z, bit, pins_from


class HC74(Chip):
    part = "74HC74"

    def __init__(self, name: str):
        pins = {1: ("/1CLR", "in"), 2: ("1D", "in"), 3: ("1CLK", "in"), 4: ("/1PRE", "in"), 5: ("1Q", "out"), 6: ("/1Q", "out"), 7: ("GND", "power"), 8: ("/2Q", "out"), 9: ("2Q", "out"), 10: ("/2PRE", "in"), 11: ("2CLK", "in"), 12: ("2D", "in"), 13: ("/2CLR", "in"), 14: ("VCC", "power")}
        super().__init__(name, pins_from(pins), Delay(20))

        self._q = [0, 0]

    def clock_edge(self, pin: int | str | None = None) -> None:
        blocks = [0, 1]
        if pin is not None:
            number = self.pin_number(pin)
            blocks = [0] if number == 3 else ([1] if number == 11 else [])
        for block in blocks:
            if block == 0:
                if not bit(self.read(1)):
                    self._q[0] = 0
                elif not bit(self.read(4)):
                    self._q[0] = 1
                else:
                    self._q[0] = bit(self.read(2))
            else:
                if not bit(self.read(13)):
                    self._q[1] = 0
                elif not bit(self.read(10)):
                    self._q[1] = 1
                else:
                    self._q[1] = bit(self.read(12))
        self.update()

    def update(self) -> None:
        if not bit(self.read(1)):
            self._q[0] = 0
        elif not bit(self.read(4)):
            self._q[0] = 1
        if not bit(self.read(13)):
            self._q[1] = 0
        elif not bit(self.read(10)):
            self._q[1] = 1
        self.output(5, self._q[0])
        self.output(6, 1 - self._q[0])
        self.output(9, self._q[1])
        self.output(8, 1 - self._q[1])



def create(name: str = "U") -> HC74:
    return HC74(name)
