# Components DB

Component database for the shared Components library.

## Chip Model Freeze

The chip model is frozen at `v0.1` on `2026-07-09`.

That freeze covers the current DB package shape, schema names, and loader
contracts for active IC, Virtual, Passive, and Discrete component metadata.
Future incompatible structure changes must bump the model version and update
the documented date together.

The current structure is grouped by component family. Active ICs, Virtual
components, and Passive components are layered packages. Discrete components
still use compact `component.json` manifests:

```text
DB/
  74xx/
    74HC00/
      definition/definition.json
      simulation/model.py
      simulation/model.v
      simulation/model.json
      simulation/netlist.json
      symbol/dip.json
      tests/*.json
      generated/artifacts.json
  Memory/
    62256/
      definition/definition.json
      simulation/model.py
      simulation/model.v
      simulation/model.json
      simulation/netlist.json
      symbol/dip.json
      tests/*.json
      generated/artifacts.json
  Virtual/
    InputSource/
      definition/definition.json
    Probe/
      definition/definition.json
  Passive/
    LED/
      definition/definition.json
    Resistor/
      definition/definition.json
  Discrete/
    NPN/
      component.json
    PNP/
      component.json
    BC549/
      component.json
    BC559/
      component.json
```

Each active IC owns one canonical source file,
`definition/definition.json`, plus package-local layer folders:

- `simulation/`: local Python and Verilog behavior, model metadata, and
  netlist/export metadata
- `tests/`: truth table, timing, tri-state, bus-fight, and propagation records
- `symbol/`: DIP/schematic visual metadata
- `generated/`: reproducible artifact reports from the generator path

The IC definition shape is defined by `digital.schema.json`. Virtual and
Passive packages use `schema: db.component.definition` with embedded
definition layers for component identity, package, pins, simulation, and UI
metadata. Legacy `chip.schema.json`, `chip.json`, and `component.json` loading
remain compatibility paths for older data, not the active IC, Virtual, or
Passive package source. The DB can represent:

- `74xx`: 74xx/74HC logic ICs
- `memory`: SRAM, EEPROM, and flash ICs
- `virtual`: simulation-only inputs, clocks, rails, pulls, and probes
- `passive`: LED, resistor, capacitor
- `discrete`: generic NPN/PNP transistors and specific BC549/BC559 entries

Missing properties are allowed, but they must be visible through package
status, `missing_properties`, `missing_files`, generated records, or loader
reports. A grouped IC, Virtual, or Passive folder is valid when
`definition/definition.json` is readable and identifies the part. A grouped
Discrete folder is valid when `component.json` is readable and identifies the
component.

Active IC implementation files are package-local. The shared family Verilog
trees remain for smoke coverage and comparison:

- `Verilog/74xx/`
- `Verilog/Memory/`

The DB is the component identity layer. Simulators, exporters, CLI tools, and
future UI/API code should ask the DB what properties a component has instead of
scattering component facts across unrelated files.

The original seed set intentionally covered simple gates, a sequential counter,
a bidirectional bus transceiver, SRAM, and EEPROM:

- `74HC00`
- `74HC04`
- `74HC161`
- `74HC245`
- `62256`
- `AT28C256`

The next useful set adds flip-flop, register, decoder, and flash coverage:

- `74HC74`
- `74HC574`
- `74HC138`
- `SST39SF010A`

The DB now has one layered package for every active IC model and pinout entry:
62 DB IC parts for 62 modeled IC parts. Virtual and Passive schematic
components are also layered packages; Discrete schematic components remain
compact manifests.

All 62 active IC parts with `verilog_export=tested` now own their structural
Verilog export metadata in package `simulation/netlist.json` files.
`Design.to_verilog()` reads those export blocks through `chiplib.db`; there is
no separate runtime mapping table to keep in sync.

Grouped schematic components currently cover:

- `InputSource`
- `ClockSource`
- `Probe`
- `BusProbe`
- `VCC`
- `GND`
- `Pullup`
- `Pulldown`
- `LED`
- `Resistor`
- `Capacitor`
- `NPN`
- `PNP`
- `BC549`
- `BC559`

Audit the DB against the active legacy catalog:

```sh
cd ../python
python3 -m chiplib.cli db --audit
python3 -m chiplib.cli db --status
```

Use the learner-facing catalog view for student UI/API work:

```sh
python3 -m chiplib.cli db --student
python3 -m chiplib.cli db --student --group virtual
```

See `STUDENT_CATALOG.md` for the CLI, Python, and frontend API contract.
