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

All active IC packages under `DB/74xx/` and `DB/Memory/` now use this package
shape. IC `chip.json` files are no longer required for those packages; loader
compatibility is synthesized from `definition/definition.json` plus
`simulation/netlist.json`. Legacy `chip.json` support remains only for older or
non-IC components.

## Definition Contract

`definition/definition.json` is the only canonical chip definition file for a
package. It must contain:

- `schema`, `version`, and `part`.
- `metadata`: title, group, family, role, and status-facing identity.
- `package`: physical package kind and pin count.
- `pins`: real package pin numbers, names, directions, active-low flags, and
  functions.
- `logic`: machine-readable behavior summary used by generators and docs.
- `timing`: model delay plus extracted timing facts when available.
- `generation`: required generator targets and local file paths.
- `verification`: required test types and required vector names.
- `datasheet.sources`: manufacturer/source evidence used for package, pins,
  logic, timing, and electrical claims.
- `evidence`: compact status flags derived from the package evidence, including
  `dip_pinout_verified`, `manufacturer`, and `datasheet_status`.
- `logic_family_model`: canonical shared logic behavior model for compatible
  orderable variants, such as `74HC161`.
- `variants`: manufacturer/orderable package numbers that use the same logic
  family model, each with `part` and `manufacturer`.
- `procurement`: conservative buying guidance for student/tooling catalogs:
  `recommended_for_new_design`, `availability_class`, `stock_basis`, and
  `last_checked`. These fields are catalog hints, not live distributor
  inventory.
- `definition_layers`: embedded sublayers only when they carry information not
  already derivable from the top-level fields. Loaders expose a complete
  layer-specific view by deriving component/package/pins/power/logic/timing
  records from the top-level definition when those records are omitted.

Do not move behavior code, generated prose, or UI-only state into
`definition.json`. It describes source facts and generator contracts; it does
not execute behavior.

## Layer Ownership

- `definition/definition.json` owns chip identity, package, pins, power, logic,
  timing, propagation, tri-state, direction, voltage, current, electrical facts,
  datasheet source evidence, and procurement hints.
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
- `generated/` owns reproducible artifact reports from
  `generate_component_artifacts(part)`. Regenerate these files after changing
  definitions, tests, symbols, or generator logic.

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

### Truth Table Contract

`tests/truth_table.json` is the primary executable behavior record. For active
ICs it must not use a generic `basic_function` placeholder. System-used chips,
such as RV8GR parts, must have per-chip vectors with concrete `inputs` and
`expect` fields.

Every truth table record must include `edge_criteria`:

```json
{
  "clocking": "edge_sensitive",
  "trigger_edge": "rising",
  "non_trigger_edge": "falling_or_no_rising_edge_holds_state",
  "notes": "Truth tests must prove state changes only on the triggering rising edge and holds without that edge."
}
```

Allowed clocking modes:

- `edge_sensitive`: clocked state changes. The record must state `rising` or
  `falling` and include vectors or linked checks proving the non-trigger edge
  holds state.
- `level_sensitive`: combinational or level-controlled logic. Use
  `trigger_edge: none`.
- `control_edge_or_level_sensitive`: memory read/write or similar control
  windows. Use `trigger_edge: WE_control` when write-enable behavior is the
  relevant transition.

Clocked seed and RV8GR chips must include negative edge/hold coverage. Examples:

- `74HC161`: ENP/ENT hold, no-rising-edge hold, count resumes on rising edge,
  `/CLR` priority over load/count.
- `74HC574`: no-clock hold, clock while `/OE=1` captures internally, re-enable
  exposes the captured value.
- `74HC164` and `74HC74`: explicit clocked behavior and asynchronous controls.

### Timing Parameter Contract

Datasheet timing records should use canonical polarity-specific names when the
source provides them:

- `tPLH` and `tPHL` for input/output propagation delay.
- `tPZH` and `tPZL` for output enable from high-Z.
- `tPHZ` and `tPLZ` for output disable to high-Z.
- `clock_to_q_high` and `clock_to_q_low` for clock-to-Q polarity.
- `setup`, `hold`, and `minimum_pulse_width` for clock, reset, write, or
  control timing windows.

Generic fields such as `tpd`, `enable`, `disable`, `clock_to_q`, and memory
high-Z timing are allowed only as source-backed intermediate data or simulator
defaults. `Docs/TIMING_PARAMETER_AUDIT.md` tracks which active physical ICs
still need normalized polarity-specific timing.

Executable models must keep a timing hook even before every datasheet path is
normalized. Python models should drive outputs through `Chip.output()` so
`Board.settle()` can schedule chip-level delay, and Verilog models should keep
`DELAY_RISE`/`DELAY_FALL` or equivalent `assign #(...)` parameters. The audit
in `Docs/TIMING_SIMULATION_AUDIT.md` tracks whether each active physical model
has this timing path.

### Bus Fight And High-Z Contract

`bus_fight.json` must be present for bidirectional or bus-driving chips. If a
chip can drive a shared bus, tests should cover both:

- conflict when the chip and an external driver drive opposite values
- no conflict when the chip output is disabled/high-Z

The Python regression suite must execute representative bus-fight records
through `Board.errors()`; JSON records alone are not enough for seed or RV8GR
bus parts.

### Memory Write Protection Contract

Memory truth records must prove:

- write then read at one or more addresses
- `/CE=1` prevents writes
- `/WE=1` prevents writes
- `/OE=1` or disabled chip states release DQ to high-Z
- write-mode DQ high-Z behavior is explicit

The seed records for `62256` and `AT28C256` are the reference shape.

### Python/Verilog Equivalence Contract

Seed and system-used chips should have direct Python-vs-Verilog equivalence
coverage whenever a Verilog model exists. The split-record tests guard that the
seed chips have matching equivalence tests, and generated Verilog testbench
metadata is emitted as a package artifact.

## First Reference Part

`DB/74xx/74HC245/` is the first reference package because it exercises:

- bidirectional A/B buses
- `DIR` direction control
- active-low `/OE`
- tri-state outputs
- bus-fight risk
- propagation delay
- physical DIP pin mapping
