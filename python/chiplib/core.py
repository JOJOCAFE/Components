"""Pin, net, and event primitives for reusable chip simulation."""

from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import count
from typing import Callable

Z = "Z"
X = "X"
Logic = int | str


class BusConflictError(RuntimeError):
    """Raised when two enabled outputs drive a net to different logic levels."""


@dataclass(frozen=True)
class Delay:
    rise_ns: int
    fall_ns: int | None = None

    def for_change(self, old: Logic, new: Logic) -> int:
        if old == new:
            return 0
        if new == 1:
            return self.rise_ns
        if new == 0:
            return self.fall_ns if self.fall_ns is not None else self.rise_ns
        return max(self.rise_ns, self.fall_ns or self.rise_ns)


@dataclass(frozen=True)
class PinSpec:
    number: int
    name: str
    direction: str
    active_low: bool = False


class Pin:
    def __init__(self, chip: "Chip", spec: PinSpec):
        self.chip = chip
        self.spec = spec
        self.value: Logic = Z if spec.direction in ("out", "bidir") else 0
        self.net: Net | None = None

    @property
    def number(self) -> int:
        return self.spec.number

    @property
    def name(self) -> str:
        return self.spec.name

    @property
    def direction(self) -> str:
        return self.spec.direction

    def drive(self, value: Logic) -> None:
        self.value = normalize_logic(value)
        if self.net:
            self.net.resolve()

    def sample(self) -> Logic:
        return self.net.value if self.net else self.value


class Net:
    def __init__(self, name: str):
        self.name = name
        self.pins: list[Pin] = []
        self.value: Logic = Z

    def connect(self, pin: Pin) -> None:
        if pin not in self.pins:
            self.pins.append(pin)
            pin.net = self
        self.resolve()

    def resolve(self) -> Logic:
        drivers = [
            pin for pin in self.pins
            if pin.direction in ("out", "bidir") and pin.value != Z
        ]
        driven_values = {pin.value for pin in drivers}
        if len(driven_values) > 1:
            detail = ", ".join(f"{p.chip.name}.{p.number}:{p.value}" for p in drivers)
            raise BusConflictError(f"{self.name} has conflicting drivers: {detail}")
        self.value = drivers[0].value if drivers else Z
        for pin in self.pins:
            if pin.direction in ("in", "power", "nc"):
                pin.value = self.value
        return self.value


class Chip:
    part = "GENERIC"

    def __init__(self, name: str, pin_specs: list[PinSpec], delay: Delay | int = 10):
        self.name = name
        self.delay = delay if isinstance(delay, Delay) else Delay(delay)
        self.pins = {spec.number: Pin(self, spec) for spec in pin_specs}
        self.pin_names = {spec.name: spec.number for spec in pin_specs}
        self._pending: list[tuple[int, Logic]] = []

    def pin_number(self, pin: int | str) -> int:
        if isinstance(pin, int):
            return pin
        if pin in self.pin_names:
            return self.pin_names[pin]
        raise KeyError(f"{self.name} has no pin {pin!r}")

    def pin(self, pin: int | str) -> Pin:
        return self.pins[self.pin_number(pin)]

    def read(self, pin: int | str) -> Logic:
        return self.pin(pin).sample()

    def set_input(self, pin: int | str, value: Logic) -> None:
        p = self.pin(pin)
        p.value = normalize_logic(value)
        if p.net:
            p.net.resolve()

    def drive_output(self, pin: int | str, value: Logic) -> None:
        self.pin(pin).drive(value)

    def output(self, pin: int | str, value: Logic) -> None:
        number = self.pin_number(pin)
        new_value = normalize_logic(value)
        if self.pins[number].value != new_value:
            self._pending.append((number, new_value))

    def commit(self) -> None:
        pending = self._pending
        self._pending = []
        for pin, value in pending:
            self.drive_output(pin, value)

    def update(self) -> None:
        pass

    def clock_edge(self) -> None:
        pass


class Board:
    def __init__(self):
        self.time_ns = 0
        self.chips: dict[str, Chip] = {}
        self.nets: dict[str, Net] = {}
        self._events: list[tuple[int, int, Callable[[], None]]] = []
        self._counter = count()

    def add_chip(self, ref: str, chip: Chip) -> Chip:
        self.chips[ref] = chip
        return chip

    def net(self, name: str) -> Net:
        if name not in self.nets:
            self.nets[name] = Net(name)
        return self.nets[name]

    def connect(self, net_name: str, chip: Chip, pin: int | str) -> None:
        self.net(net_name).connect(chip.pin(pin))

    def drive(self, chip: Chip, pin: int | str, value: Logic) -> None:
        chip.set_input(pin, value)

    def schedule(self, delay_ns: int, callback: Callable[[], None]) -> None:
        heappush(self._events, (self.time_ns + delay_ns, next(self._counter), callback))

    def evaluate(self) -> None:
        for chip in self.chips.values():
            chip.update()
            for pin, value in chip._pending:
                delay = chip.delay.for_change(chip.pins[pin].value, value)
                self.schedule(delay, lambda c=chip, p=pin, v=value: c.drive_output(p, v))
            chip._pending = []

    def settle(self, max_events: int = 10000) -> None:
        self.evaluate()
        events = 0
        while self._events:
            when, _, callback = heappop(self._events)
            self.time_ns = when
            callback()
            while self._events and self._events[0][0] == when:
                _, _, same_time_callback = heappop(self._events)
                same_time_callback()
            self.evaluate()
            events += 1
            if events > max_events:
                raise RuntimeError("event queue did not settle")

    def clock_edge(self) -> None:
        for chip in self.chips.values():
            chip.clock_edge()
        self.settle()


def normalize_logic(value: Logic) -> Logic:
    if value in (0, 1, Z, X):
        return value
    if value is True:
        return 1
    if value is False:
        return 0
    raise ValueError(f"invalid logic value {value!r}")


def bit(value: Logic) -> int:
    return 1 if value == 1 else 0


def pins_from(defs: dict[int, tuple[str, str]]) -> list[PinSpec]:
    return [
        PinSpec(number, name, direction, name.startswith("/"))
        for number, (name, direction) in sorted(defs.items())
    ]
