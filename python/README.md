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

## Role In Verification

Use this Python library as the preferred behavioral cross-check for TTL CPU
systems such as RV8/RV8GR. It is closer to physical debugging than the Verilog
component files because projects can connect chips by real pin number or pin
name, observe shared nets, catch bus conflicts, and include propagation-delay
metadata in system timing checks.

The Verilog component files remain useful for HDL-level comparison and
FPGA-oriented tests. For normal system behavior checks, run the Python simulator
first and use Verilog only when the question is specifically about HDL
equivalence or an independent second implementation.

## Compatibility Contract

Python is the physical source of truth for chips that it implements:

- pin numbers and names must match the manufacturer-backed DIP pinout file
- active-low controls must use the same polarity as the datasheet
- disabled tri-state outputs must drive `Z`
- bidirectional pins must release the non-driving side
- sequential chips must model asynchronous clear/preset behavior where present
- memory parts must use the real 28-pin DIP address/data/control mapping

Verilog must match the Python behavior for overlapping parts. Verilog modules
may keep vector ports such as `A[7:0]`, `DQ[7:0]`, and `Q[7:0]` for HDL use, but
the behavior must remain compatible with the Python real-pin model.

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
- `AT28C256` and `62256` use the real 28-pin DIP address/data/control pin map.

## Verify

Run from this folder:

```bash
python3 -B -m tests.test_chips
```
