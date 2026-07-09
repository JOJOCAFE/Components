# Component Generation Pipeline

Goal: one component definition file can drive every generated artifact.

```text
definition/definition.json
  -> normalized JSON component detail
  -> Python simulator adapter
  -> Verilog wrapper/export metadata
  -> Verilog testbench metadata / generated benches
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

`generated/artifacts.json` is reproducible output. It is not a second source of
truth. Regenerate it after changing `definition/definition.json`, split test
records, symbol metadata, or generator code.

## Required Generation Targets

Each seed `definition.json` must declare:

- `json`: normalized component JSON/API detail
- `python_simulator`: Python behavior model or adapter
- `verilog_wrapper`: Verilog module/export wrapper
- `verilog_testbench`: Verilog testbench metadata or generated bench text
- `kicad_symbol`: KiCad symbol generation
- `svg_pinout`: SVG pinout drawing
- `documentation`: Markdown/student docs
- `unit_test`: Python/Verilog test generation
- `interactive_demo`: block UI or simulator demo

Generated documentation stays machine-readable, but it should also include
student-facing prose fields derived from the same `definition.json` facts:
`overview`, `key_points`, `pin_summary`, `bus_explanations`,
`control_explanations`, and `timing_note`. Generated interactive demos keep
their structured `controls`, `probes`, and `default_steps`, and add readable
`title`, `intro`, labels, guided steps, and short student questions for UI use.

## Edge Criteria Rule

Every `tests/truth_table.json` record must declare `edge_criteria`.

- Clocked chips must state the triggering edge, such as `rising` or `falling`,
  and include or point to checks that prove the non-trigger edge holds state.
- Level-sensitive and combinational chips must explicitly state
  `trigger_edge: none`.
- Memory parts must state their write/read control edge or level window and
  include disabled/high-Z checks.
- New chips cannot rely on `basic_function` placeholders when they are used by
  RV8GR or another system-level package.

## Verification Generation Rules

Generated tests start from the split records in `tests/`:

- `truth_table.json`: per-chip functional vectors, edge criteria, enable/hold
  behavior, async-control priority, and memory write protection.
- `timing.json`: clock/control mode records and datasheet/model timing facts.
- `tri_state.json`: high-Z behavior for disabled outputs or bidirectional pins.
- `bus_fight.json`: board-level conflict/no-conflict cases for shared buses.
- `propagation.json`: delay expectations that must match definition metadata.

For seed chips and RV8GR-used parts:

- truth records must be executable against Python models
- bus-fight records must be executable through `Board.errors()`
- direct Python-vs-Verilog equivalence must exist when a Verilog model exists
- timing and propagation records must be non-placeholder metadata
- memory records must prove `/CE=1` and `/WE=1` prevent writes

The split-record regression entry point is:

```sh
PYTHONPATH=python python3 -B -m tests.test_generated_split_records
```

The current generated Verilog testbench artifact records Icarus compile
metadata for every seed package and emits a simple generated bench where the
split-record shape is already supported.

## First Seed Parts

The first generator-ready chips are:

- `74HC161`
- `74HC157`
- `74HC245`
- `74HC574`
- `AT28C256`

These cover counters, multiplexers, bidirectional bus transceivers, tri-state
registers, and EEPROM memory.

## RV8GR Batch 2 Direction

The RV8GR-used chip set now follows the seed-package verification shape. See
`DB/RV8GR_BATCH2_VERIFICATION_AUDIT.md` for the current per-chip truth coverage
and the edge-criteria policy. The same standard should be applied to the rest
of the migrated IC catalog before a part is called fully verified.
