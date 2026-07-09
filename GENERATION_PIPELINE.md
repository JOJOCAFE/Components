# Component Generation Pipeline

Goal: one component definition file can drive every generated artifact.

```text
definition/digital.json
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
DB/<group>/<part>/definition/digital.json
```

The split package folders remain useful:

```text
definition/   source facts and generated definition views
simulation/   behavior model adapters
tests/        truth table, timing, tri-state, bus-fight, propagation checks
symbol/       schematic and SVG symbol metadata
datasheet/    evidence
```

But generators should be able to start from `definition/digital.json` alone.

## Required Generation Targets

Each seed `digital.json` must declare:

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
