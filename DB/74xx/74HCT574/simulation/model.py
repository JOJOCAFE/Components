"""Local behavior model for 74HCT574."""

from __future__ import annotations

from chiplib.core import Chip, Delay, Z, bit, pins_from


class HCT574(Chip):
    part = "74HCT574"

    def __init__(self, name: str = "U"):
        pins = {1: ("/OE", "in"), 2: ("1D", "in"), 3: ("2D", "in"), 4: ("3D", "in"), 5: ("4D", "in"), 6: ("5D", "in"), 7: ("6D", "in"), 8: ("7D", "in"), 9: ("8D", "in"), 10: ("GND", "power"), 11: ("CLK", "in"), 12: ("8Q", "out"), 13: ("7Q", "out"), 14: ("6Q", "out"), 15: ("5Q", "out"), 16: ("4Q", "out"), 17: ("3Q", "out"), 18: ("2Q", "out"), 19: ("1Q", "out"), 20: ("VCC", "power")}
        super().__init__(name, pins_from(pins), Delay(15))
        self._state = 0
        self._state_by_block: dict[int, int] = {}

    def _b(self, name: str) -> int:
        return bit(self.read(name))

    def _o(self, name: str, value) -> None:
        if name in self.pin_names:
            self.output(name, value)

    def update(self) -> None:
        p = self.part
        if p in {"74HC03", "74HC132"}:
            for i in range(1, 5):
                val = 1 - (self._b(f"{i}A") & self._b(f"{i}B"))
                self._o(f"{i}Y", Z if p == "74HC03" and val else val)
        elif p == "74HC05":
            for i in range(1, 7):
                val = 1 - self._b(f"{i}A")
                self._o(f"{i}Y", Z if val else 0)
        elif p in {"74HC4049", "74HCT04", "74HCT14"}:
            for i in range(1, 7):
                self._o(f"{i}Y", 1 - self._b(f"{i}A"))
        elif p == "74HC4050":
            for i in range(1, 7):
                self._o(f"{i}Y", self._b(f"{i}A"))
        elif p in {"74HCT245"}:
            if self._b("/OE"):
                for i in range(1, 9): self._o(f"A{i}", Z); self._o(f"B{i}", Z)
            elif self._b("DIR"):
                for i in range(1, 9): self._o(f"A{i}", Z); self._o(f"B{i}", self._b(f"A{i}"))
            else:
                for i in range(1, 9): self._o(f"B{i}", Z); self._o(f"A{i}", self._b(f"B{i}"))
        elif p == "74HCT541":
            enabled = not self._b("/OE1") and not self._b("/OE2")
            for i in range(1, 9): self._o(f"Y{i}", self._b(f"A{i}") if enabled else Z)
        elif p == "74HCT574":
            for i in range(1, 9): self._o(f"{i}Q", Z if self._b("/OE") else ((self._state >> (i-1)) & 1))
        elif p == "74HC4520":
            for block in (1,2):
                if self._b(f"{block}MR"): self._state_by_block[block] = 0
                value = self._state_by_block.get(block, 0)
                for i in range(4): self._o(f"{block}Q{i}", (value >> i) & 1)
        elif p == "74HC4538":
            for block in (1,2):
                q = 0 if self._b(f"/{block}R") == 0 else self._state_by_block.get(block, 0)
                self._state_by_block[block] = q
                self._o(f"{block}Q", q); self._o(f"/{block}Q", 1 - q)

    def clock_edge(self, pin=None) -> None:
        p = self.part
        pin_name = self.pin(pin).name if pin is not None else None
        if p == "74HCT574":
            self._state = sum(self._b(f"{i}D") << (i-1) for i in range(1,9))
        elif p == "74HC4520":
            blocks = [1,2] if pin_name is None else ([int(pin_name[0])] if pin_name[:1] in {"1","2"} else [])
            for block in blocks:
                if self._b(f"{block}MR"): self._state_by_block[block] = 0
                elif self._b(f"{block}E"):
                    self._state_by_block[block] = (self._state_by_block.get(block, 0) + 1) & 0xF
        elif p == "74HC4538":
            blocks = [1,2] if pin_name is None else ([int(pin_name[0])] if pin_name[:1] in {"1","2"} else [])
            for block in blocks:
                if self._b(f"/{block}R"):
                    self._state_by_block[block] = 1
        self.update()


def create(name: str = "U") -> HCT574:
    return HCT574(name)
