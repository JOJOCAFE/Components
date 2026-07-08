# Components Python Library

Reusable Python behavior models for the JOJOCAFE component library.

This package models chips by real DIP pin number and pin name so projects can
wire instances like physical parts:

```python
from chiplib import Board, create_chip

board = Board()
u1 = board.add_chip("U1", create_chip("74HC00", "U1"))
board.drive(u1, 1, 1)
board.drive(u1, "1B", 0)
board.settle()
assert u1.read("1Y") == 1
```

## Current Coverage

RV8GR-V2 starter set:

- `74HC00`, `74HC04`, `74HC21`, `74HC32`, `74HC74`, `74HC86`
- `74HC157`, `74HC161`, `74HC164`, `74HC245`, `74HC283`
- `74HC541`, `74HC574`, `74HC688`
- `AT28C256`, `62256`

## Timing

Each chip carries propagation delay metadata in nanoseconds. The event scheduler
uses per-chip rise/fall defaults for output changes. These are simulation
defaults, not a replacement for board-level timing closure; real timing depends
on manufacturer, VCC, temperature, and load.

## Design Notes

- Pin numbers are the source of truth.
- Pin names are aliases for readability.
- Tri-state outputs can drive `Z`.
- Nets resolve `0`, `1`, `Z`, and `X`.
- Conflicting active drivers raise `BusConflictError`.
- `74HC245` follows the real datasheet direction convention: `DIR=1` means
  A-to-B, `DIR=0` means B-to-A.

## Verify

Run from this folder:

```bash
python3 -m tests.test_chips
```
