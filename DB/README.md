# Components DB

Canonical component database for the shared Components library.

The DB is the source of truth for component identity, pins, package shape,
simulation hooks, export metadata, evidence status, and learner-facing catalog
data. Project-specific reports belong in their project repos, not here.

## Current Shape

The package model is frozen as `v0.1` from `2026-07-09`. Incompatible structure
changes must bump that model version in `DB/index.json`.

Every active component is a package with:

```text
DB/<group>/<part>/definition/definition.json
```

Current package counts:

| Group | Count | Purpose |
|---|---:|---|
| `74xx` | 57 | 74xx / 74HC logic ICs |
| `Memory` | 5 | SRAM, EEPROM, and flash ICs |
| `Virtual` | 12 | simulation-only sources, rails, probes, and stress tools |
| `Passive` | 6 | LED, resistor, capacitor |
| `Discrete` | 4 | NPN/PNP transistor entries |
| Total | 84 | all package definitions |

No active package uses `chip.json`, `component.json`, or `chip.schema.json`.

## Definition Contracts

Active ICs use:

```json
{"schema": "db.component.digital"}
```

That shape is defined by `DB/digital.schema.json` and applies to `74xx` and
`Memory` parts. These packages may also own:

- `simulation/model.py`
- `simulation/model.v`
- `simulation/model.json`
- `simulation/netlist.json`
- `symbol/dip.json`
- `tests/*.json`
- `generated/artifacts.json`

Virtual, Passive, and Discrete packages use:

```json
{"schema": "db.component.definition"}
```

Those definitions carry embedded layers for component identity, package, pins,
simulation, and UI metadata.

`load_component(part)` returns a compatibility catalog view with
`schema: db.component.manifest`; it is synthesized from package definitions and
is not a file format to author by hand.

## What Belongs Here

Keep these in `DB/`:

- reusable component definitions
- datasheet-backed pin, timing, electrical, and behavior metadata
- package-local simulation/export metadata
- generic test contracts and student catalog documentation

Do not keep these in `DB/`:

- project-specific readiness reports
- project build plans
- one-off audit reports
- generated notes that duplicate JSON status

## Validation

Run from the repo root:

```sh
PYTHONPATH=python python3 -B -m tests.test_db
PYTHONPATH=python python3 -B -m tests.test_generated_split_records
```

CLI catalog checks:

```sh
PYTHONPATH=python python3 -m chiplib.cli db --audit
PYTHONPATH=python python3 -m chiplib.cli db --status
PYTHONPATH=python python3 -m chiplib.cli db --student
```

## DB Docs

Human-readable DB docs are intentionally small:

- `COMPONENT_TEST_PROTOCOL.md`: generic chip/circuit verification policy
- `STUDENT_CATALOG.md`: learner-facing catalog fields and examples
- `VIRTUAL_TEST_GENERATOR_CONTRACT.md`: how split records become virtual benches
- `VIRTUAL_TEST_INSTRUMENTS.md`: student-facing virtual instrument guide
