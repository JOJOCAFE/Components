# DB Component Package Spec

This document defines the next DB shape for a component as a layered digital
definition package. Seed packages use `definition/definition.json` directly;
legacy `chip.json` manifests remain supported for older components while tools
migrate.

## Layers

```text
Datasheet
  -> Definition
  -> Simulation
  -> Verification
  -> Schematic / Symbol
  -> Generation
  -> Project
```

Repository package layout:

```text
DB/74xx/74HC245/
  definition/
    definition.json
  simulation/
    model.json
    model.py
    model.v
    netlist.json
  tests/
    truth_table.json
    timing.json
    tri_state.json
    bus_fight.json
    propagation.json
  symbol/
    dip.json
```

During the generator seed phase, `definition/definition.json` is the canonical
umbrella file for a digital component. It keeps identity, package, pins, logic,
timing, generation targets, verification intent, and datasheet evidence in one
schema-validated file. Definition sublayers such as component metadata,
package, pins, power, logic, timing, and electrical facts live under
`definition_layers` inside that file. Datasheet source records live in the
top-level `datasheet.sources` section of the same file. Legacy split definition
or datasheet files may still be loaded as a compatibility fallback, but they
are not required physical source files for generator seed packages.

## Layer Ownership

- `definition/definition.json` owns chip identity, package, pins, power, logic,
  timing, propagation, tri-state, direction, voltage, current, electrical facts,
  and datasheet source evidence.
- `simulation/` points to executable Python/Verilog behavior and records which
  definition features the simulator implements.
- `simulation/model.py` is the portable Python behavior source. Project,
  system, and chip-add/export tools should copy it with the chip instead of
  linking back to the DB package path.
- Python exports that copy `simulation/model.py` must also copy
  `python/chiplib/core.py`, because the local models use the shared `Chip`,
  `Delay`, logic, and pin primitives from that runtime file.
- Single-chip exports, circuits, and larger systems should include one shared
  copy of `chiplib/core.py` per exported project, not one duplicate per chip.
- `tests/` owns machine-readable verification intent. Test files can be turned
  into Python, Verilog, CLI, or UI checks.
- `symbol/` owns schematic and visual block hints. It must not define behavior.

## Rules

- The datasheet is the evidence source.
- Definition files describe the part; they do not run code.
- Simulation consumes definitions and may add implementation details.
- Verification checks definition, simulation, generated netlists, and exports.
- Visualization consumes definition plus simulator snapshots.
- CLI/API exposes all layers without inventing chip behavior.

## Required Test Types

Each active IC package should eventually include:

- `truth_table.json`: functional vectors or state rules.
- `timing.json`: setup, hold, pulse width, and timing-mode checks where known.
- `tri_state.json`: high-Z and enable behavior checks.
- `bus_fight.json`: conflict checks for bidirectional or bus-driving parts.
- `propagation.json`: propagation-delay expectations and metadata checks.

Not every part has every behavior. If a test type is not applicable, the test
file should say `applicable: false` with a short reason. Missing information
should be visible, not hidden.

## First Reference Part

`DB/74xx/74HC245/` is the first reference package because it exercises:

- bidirectional A/B buses
- `DIR` direction control
- active-low `/OE`
- tri-state outputs
- bus-fight risk
- propagation delay
- physical DIP pin mapping
