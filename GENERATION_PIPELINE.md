# Component Generation Pipeline

Goal: one component definition file can drive every generated artifact.

```text
definition/definition.json
  -> normalized JSON component detail
  -> Python simulator adapter
  -> Verilog wrapper/export metadata
  -> KiCad symbol
  -> SVG pinout
  -> documentation
  -> unit tests
  -> interactive demo
```

## Canonical Source

For each chip, the canonical generator input is:

```text
DB/<group>/<part>/definition/definition.json
```

The split package folders remain useful:

```text
definition/   source facts and generated definition views
simulation/   local behavior source, Verilog model, and netlist metadata
tests/        truth table, timing, tri-state, bus-fight, propagation checks
symbol/       schematic and SVG symbol metadata
```

Datasheet source evidence is embedded in `definition/definition.json` under
`datasheet.sources`, so generators can start from that one file alone.

When a chip is copied into a project or system, copy its local
`simulation/model.py` with it. The exported package metadata lists this under
`portable_files` so standalone projects do not need to import behavior from the
DB package folder. Also copy `python/chiplib/core.py`; the local models depend
on that runtime support file for `Chip`, `Delay`, logic, and pin primitives.
For a circuit or system export with many chips, copy `chiplib/core.py` once and
share it across the copied chip models.

## Required Generation Targets

Each seed `definition.json` must declare:

- `json`: normalized component JSON/API detail
- `python_simulator`: Python behavior model or adapter
- `verilog_wrapper`: Verilog module/export wrapper
- `kicad_symbol`: KiCad symbol generation
- `svg_pinout`: SVG pinout drawing
- `documentation`: Markdown/student docs
- `unit_test`: Python/Verilog test generation
- `interactive_demo`: block UI or simulator demo

## First Seed Parts

The first generator-ready chips are:

- `74HC161`
- `74HC157`
- `74HC245`
- `74HC574`
- `AT28C256`

These cover counters, multiplexers, bidirectional bus transceivers, tri-state
registers, and EEPROM memory.
