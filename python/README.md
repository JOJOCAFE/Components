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

Bus tags are the preferred way to describe multi-line CPU wiring. A schematic
can place any number of bus objects (`b0`, `b1`, `b2`, and so on), and each bus
can have up to 128 indexed lines such as `bus:b1[0]` through `bus:b1[127]`.
Any number of chip pins can plug into the same tag to share that connection;
conflict detection still catches multiple active output drivers.

Pull-up and pull-down helpers define normal/default logic states for floating
nets, bus tags, or individual chip pins. They behave like weak resistor pulls:
an active chip output overrides the pull, while conflicting pull directions on
the same net are rejected.

Power rails, manual logic sources, and stimulus input sets are first-class
backend objects. Rails can drive schematic tags such as `VCC`, `GND`, or a bus
line. Logic sources model visible switches, jumpers, or UI-controlled inputs.
Stimulus can create any number of named 64-channel input sets. `Board.snapshot()`
returns serializable chip, pin, net, bus, rail, source, pull, and error state
for UI or API display.

`Design` is the scriptable schematic model above `Board`. It can load the
readable schematic JSON shape, normalize aliases/endpoints, build a simulator
`Board`, import a KiCad generic netlist, export a normalized netlist, create
first-pass structural Verilog for supported parts, and expose stimulus/probe
controllers and snapshots for CLI or UI use.

Probe sets are available for backend tests and future UI inspection. A board
can have many probe sets, and each set has up to 64 probe channels. Each
channel can attach to a chip pin, named net, or bus tag, record logic samples
over simulated time, serialize its history, and assert expected values,
transitions, pulse counts, and stable timing windows.

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

The Python package can instantiate every current Verilog component in
`Components/Verilog/74xx` and `Components/Verilog/Memory` through `create_chip(part, name)`.

Coverage includes:

- all 57 current `Verilog/74xx/*.v` parts
- all 5 current `Verilog/Memory/*.v` parts
- the RV8GR-V2 starter set as hand-written models
- the remaining Components parts as catalog models loaded from embedded or
  embedded pinout docs

Parts without manufacturer-verified HC-family DIP evidence are intentionally
absent from the Python catalog.

## Component DB

`Components/DB` is the chip-centered DB layer. Each active IC folder owns a
canonical `definition/definition.json` file plus package-local
`simulation/`, `tests/`, `symbol/`, and `generated/` layers. Virtual and
Passive components also use `definition/definition.json`, with embedded
definition layers for component identity, package, pins, simulation service,
and UI metadata. IC definitions own status, pins, source evidence,
logic/timing/electrical facts, generator contracts, and visible
missing-property reports. Package-local `simulation/netlist.json` owns
structural Verilog export metadata.

The original DB seed covered representative gates, sequential parts, bus parts,
decoders, SRAM, EEPROM, and flash: `74HC00`, `74HC04`, `74HC74`, `74HC138`,
`74HC161`, `74HC245`, `74HC574`, `62256`, `AT28C256`, and `SST39SF010A`.
All active ICs, Virtual components, and Passive components now use the layered
package shape. Legacy `chip.json` and compact `component.json` loading remain
as compatibility for older or not-yet-migrated paths, not as the active IC,
Virtual, or Passive source.

CLI/API access:

```bash
python3 -m chiplib.cli db
python3 -m chiplib.cli db 74HC00
python3 -m chiplib.cli db --catalog
python3 -m chiplib.cli db --catalog --group virtual
python3 -m chiplib.cli db --student
python3 -m chiplib.cli db --student --group virtual
python3 -m chiplib.cli db 74HC00 --detail
python3 -m chiplib.cli db 74HC00 --package
python3 -m chiplib.cli db 74HC00 --generate
python3 -m chiplib.cli db --audit
python3 -m chiplib.cli db --status
```

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
- `Bus` groups named net tags up to 128 lines, for example `bus:b1[0]`.
- Schematics can create any number of buses, such as `b0`, `b1`, `b2`.
- A physical pin can belong to one net/tag; many pins can share one tag.
- Pull-up and pull-down helpers provide weak default logic for nets, bus tags,
  or pins before any active output drives the connection.
- Power rails and manual logic sources provide visible schematic drivers for
  UI-controlled state.
- `StimulusController` manages any number of named input sets; each input set
  has up to 64 channels.
- `Board.snapshot()` exposes serializable chips, pins, nets, buses, rails,
  sources, pulls, and structured errors for frontend/API use.
- `Design` is the shared backend model for JSON files, Python scripts, CLI
  commands, and future block UI actions.
- `Design.to_netlist()` is the bridge format for future UI, netlist, and HDL
  tools. `Design.to_verilog()` starts from that netlist and only maps parts
  with explicit pin-number-to-port rules.
- `Design.from_kicad_netlist()` can smoke-test existing KiCad netlists such as
  RV8GR-V2 against the same backend.
- Conflicting active drivers raise `BusConflictError`.
- `74HC245` follows the real datasheet direction convention: `DIR=1` means
  A-to-B, `DIR=0` means B-to-A.
- `AT28C256` and `62256` use the real 28-pin DIP address/data/control pin map.
- `AS6C62256`, `CY7C199`, and `SST39SF010A` are available as memory catalog
  models.
- `SST39SF010A` uses a simplified flash write model aligned with Verilog:
  write occurs on the falling edge of `/WE` while `/CE=0` and `/OE=1`.
- `ProbeController` manages many probe sets; each set has up to 64 channels
  attached to pins, nets, or bus tags for assertions and frontend/API state.

## Verify

Run from this folder:

```bash
python3 -B -m tests.test_chips
python3 -B -m tests.test_design
python3 -B -m tests.test_netlist
python3 -B -m tests.test_cli
python3 -B -m tests.test_db
```

## Future Use Guide

See `USAGE.md` for the practical API guide: imports, chip creation, pin access,
board/net wiring, tri-state behavior, propagation delays, memory usage,
`.bin`/`.hex` loading into ROM/RAM before simulation, verification commands,
external input/clock stimulus channels, and rules for keeping Python and
Verilog compatible.
