# DB Component Package Spec

This document defines the next DB shape for a component as a layered digital
definition package. `chip.json` remains as the compatibility manifest while
tools migrate to the split files.

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
  chip.json
  definition/
    component.json
    package.json
    pins.json
    power.json
    logic.json
    timing.json
    electrical.json
  simulation/
    model.json
  tests/
    truth_table.json
    timing.json
    tri_state.json
    bus_fight.json
    propagation.json
  symbol/
    dip.json
  datasheet/
    sources.json
```

## Layer Ownership

- `definition/` owns chip identity, package, pins, power, logic, timing,
  propagation, tri-state, direction, voltage, current, and electrical facts.
- `simulation/` points to executable Python/Verilog behavior and records which
  definition features the simulator implements.
- `tests/` owns machine-readable verification intent. Test files can be turned
  into Python, Verilog, CLI, or UI checks.
- `symbol/` owns schematic and visual block hints. It must not define behavior.
- `datasheet/` owns source evidence and package evidence.

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
