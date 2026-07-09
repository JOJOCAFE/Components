# Components Session Handoff

Date: 2026-07-09
Last updated: 2026-07-09, after RV8GR complete-set and v0.1 DB checkpoint

## Current State

- Repo: `/home/jo/kiro/Components`
- Branch: `main`
- Status at handoff: DB/package migration checkpoint verified and committed
  locally; push remains the next repository hygiene step if not already done.
- Latest pushed commit: `fcaf1f4 Harden IC package verification records`

## Completed This Session

- Added block-UI import/export in the normalized `Design` model.
- Added CLI/API support for `export-block-ui` and `import-block-ui`.
- Added `BLOCK_UI_CONTRACT.md`.
- Verified and pushed commit `561c3b1 Add block UI import export contract`.
- Audited requested parts: `74HC161`, `74HC157`, `74HC245`, `74HC574`,
  `AT28C256`.
- Expanded memory verification:
  - memory smoke now instantiates all memory modules directly
  - direct Python-vs-Verilog equivalence now covers `62256`, `AS6C62256`,
    `CY7C199`, `AT28C256`, and `SST39SF010A`
- Fixed `74HC688` DB/Python pin mapping so comparator output is pin 11, not
  pin 19.
- Updated IC manifests so DB `python_behavior` status reflects simulatable
  catalog-backed parts.
- Added component-generation direction:
  - `DB_COMPONENT_PACKAGE_SPEC.md`
  - `GENERATION_PIPELINE.md`
  - `COMPONENT_GENERATION_BACKLOG.md`
- Added generator-ready `definition/definition.json` seed files for:
  - `74HC161`
  - `74HC157`
  - `74HC245`
  - `74HC574`
  - `AT28C256`
- Added an initial layered package for `74HC245`:
  - `definition/definition.json`
  - `simulation/`
  - `tests/`
  - `symbol/`
- Saved current specialist-agent skills in `TEAM_SKILLS.md`:
  - Arendt: specs and schemas
  - Feynman: docs and demos
  - Halley: verification matrix
  - Ohm: datasheet/pin/timing/electrical evidence
  - Leibniz: loaders, generators, CLI/API integration

## Architecture Direction

Use one canonical component definition file per chip:

```text
DB/<group>/<part>/definition/definition.json
```

That one file should drive:

```text
JSON component detail
  -> Python simulator
  -> Verilog wrapper/export
  -> KiCad symbol
  -> SVG pinout
  -> documentation
  -> unit tests
  -> interactive demo
```

Package layers:

```text
definition/
simulation/
tests/
symbol/
generated/
```

Seed packages no longer need `chip.json`; compatibility catalog/API data is
synthesized from `definition/definition.json` and `simulation/netlist.json`.
Legacy `chip.json` remains supported for older components.

Truth records now require `edge_criteria`. Clocked chips must identify rising
or falling trigger behavior and prove non-trigger/no-edge hold behavior. Level
logic uses `trigger_edge: none`; memory chips identify write/read control
windows and high-Z/write-protection behavior.

## Team Task Assignments

- Arendt: spec and schemas for component packages.
- Feynman: generated docs and interactive demos for students.
- Halley: truth table, timing, tri-state, bus-fight, and propagation tests.
- Ohm: datasheet evidence, package evidence, timing, and electrical data.
- Leibniz: loader compatibility, generators, and CLI/API generation command.

## Next Safe Tasks

1. Grow generated Verilog bench emission beyond the first simple supported
   truth-table shape.
2. Build student-readable generated docs and interactive demo data from
   `definition/definition.json`, starting with the seed and RV8GR complete set.
3. Extend the RV8GR complete-set gate to the rest of the migrated IC catalog.
4. Deepen datasheet-backed timing/electrical extraction for rest-of-catalog
   parts beyond the seed/RV8GR set.
5. Keep Verilog smoke compiling family-level and package-local Verilog models.
6. Keep `TEAM_SKILLS.md`, `COMPONENT_GENERATION_BACKLOG.md`, and this handoff
   synchronized whenever the team roles or package/test contracts change.

## Current Complete-Set Test State

Use rising/falling/control edge criteria as the default for every new chip test.
Seed chips and the RV8GR Batch 2 complete set now have explicit machine-readable
truth records, timing/propagation metadata, tri-state/bus-fight records or
not-applicable reasons, generated artifacts, and executable Python coverage.

The RV8GR complete set is hard-gated in
`python/tests/test_generated_split_records.py`: every listed part must have the
seed-package layer files, non-placeholder truth vectors, declared edge criteria,
and split test records. Current deepened cases include counter load/count,
transceiver high-Z and repeated direction reversal, register re-enable capture,
and memory cross-address persistence.

When adding future checks, keep the package standalone: test files should call
the chip-local `simulation/model.py`, not a shared model folder.

## Completed Since Last Handoff

- Added schema validation for `db.component.digital` files.
- Added tests that the five seed `definition.json` files agree with current
  `chip.json` pins/package/module metadata.
- Confirmed `tests.test_block_ui` is already present in
  `.github/workflows/python-tests.yml`.
- Added `load_digital_package(part)` for `definition/definition.json` package
  layers without changing `load_component(part)`.
- Added `generate_component_artifacts(part)` and CLI/API access for structured
  generator output.
- Added split test files for the seed batch.
- Extracted first `74HC245` timing/electrical facts from the TI datasheet.
- Wrote seed generated artifact reports under each package's `generated/`
  folder.
- Added executable Python checks that read seed split test records and exercise
  the live chip models.
- Extracted first timing/electrical facts for `74HC161`, `74HC157`,
  `74HC574`, and `AT28C256`.
- Added `tests.test_generated_split_records` to execute seed split records and
  guard Verilog smoke workflow scope.
- Verified 74xx and memory Verilog smoke locally.
- Added `simulation/model.json`, local `simulation/model.py`,
  `simulation/model.v`, `simulation/netlist.json`, and `symbol/dip.json`
  package layers for all five seed chips.
- Added `portable_files` metadata and export required-file coverage so projects
  copy local `simulation/model.py` with each seed chip for standalone use.
- `portable_files` also requires `python/chiplib/core.py` whenever a local
  Python `model.py` is exported.
- Circuit/system exports should copy `chiplib/core.py` once and share it across
  all copied chip models.
- Seed chip `status` is now copied into `definition/definition.json`; active
  Verilog export mapping is read from `simulation/netlist.json` with
  `chip.json` kept as a compatibility fallback.
- Removed seed `chip.json` files after migrating their remaining status/export
  data into `definition/definition.json` and `simulation/netlist.json`.
- Merged seed chip definition sublayers into the single canonical
  `definition/definition.json` file and removed redundant split definition JSON
  files.
- Merged seed chip datasheet source records into `definition/definition.json`
  and removed redundant `datasheet/` folders.
- Recorded Batch 2 as the full RV8GR chip migration, using
  `/home/jo/kiro/RV8/RV8GR/README.md` and `doc/12_netlist.md` as the source of
  truth for the 34 logic packages plus ROM/RAM.
- Migrated the remaining RV8GR Batch 2 parts to standalone packages:
  `74HC00`, `74HC04`, `74HC21`, `74HC32`, `74HC74`, `74HC86`, `74HC164`,
  `74HC283`, `74HC541`, `74HC688`, `62256`, `AS6C62256`, and `SST39SF010A`.
- Each Batch 2 package now has `definition/definition.json`,
  `simulation/model.py`, `simulation/model.v`, `simulation/model.json`,
  `simulation/netlist.json`, `symbol/dip.json`, split test records, and
  generated artifacts.
- Legacy `chip.json` files were removed for those Batch 2 parts; compatibility
  now synthesizes catalog/API data from each `definition/definition.json` plus
  `simulation/netlist.json`.
- Migrated the rest of the active IC catalog after RV8GR Batch 2. All 62 IC
  parts under `DB/74xx` and `DB/Memory` now have standalone package folders
  with `definition/definition.json`, local `simulation/model.py`, local
  `simulation/model.v`, `simulation/model.json`, `simulation/netlist.json`,
  `symbol/dip.json`, split test records, and generated artifacts.
- No IC `chip.json` files remain under `DB/74xx` or `DB/Memory`; legacy
  `chip.json` support remains in the loader for older/non-IC components.
- Added `tools/migrate_ic_packages.py` so this package migration shape can be
  repeated or audited. Catalog chips get local behavior code embedded in their
  own `simulation/model.py`, with only `chiplib.core` shared at export time.
- Added generated `verilog_testbench` artifact metadata and first emitted
  generated bench support for a simple seed truth-table shape.
- Added student-readable generated documentation/demo fields from package facts.
- Added `edge_criteria` to every active IC `tests/truth_table.json`.
- Replaced RV8GR-used `basic_function` placeholders and intent-only records
  with per-chip truth vectors.
- Seed and RV8GR verification now covers rising/no-edge behavior, enable/hold,
  async priority, bus-fight/no-conflict cases, memory write protection,
  propagation/timing metadata, and Python-vs-Verilog coverage guards.
- Added `DB/RV8GR_BATCH2_VERIFICATION_AUDIT.md`.
- `.github/workflows/verilog-smoke.yml` now also compiles package-local
  `DB/74xx` and `DB/Memory` `simulation/model.v` files.
- Updated docs for chip definition and verification contracts:
  `README.md`, `DB_COMPONENT_PACKAGE_SPEC.md`, `GENERATION_PIPELINE.md`,
  `COMPONENT_GENERATION_BACKLOG.md`, and this handoff now describe
  `definition/definition.json`, package-local simulation files, generated
  artifacts, and required test records.
- Reconciled stale migration/service docs after Pim team wake-up:
  `DB_MIGRATION_PLAN.md`, `DB/README.md`, `python/README.md`, `BACKLOG.md`,
  `SERVICE_ARCHITECTURE_TASKS.md`, `TEAM_SKILLS.md`, and `README.md` now
  describe active ICs as layered DB packages instead of current
  `chip.json`/family-model manifests. Remaining `chip.json` references are
  legacy compatibility notes.
- Updated `TEAM_SKILLS.md` broad health gates to include `test_block_ui`,
  `test_generated_split_records`, `db --audit`, and `db --status`.
- Migrated `DB/Virtual` and `DB/Passive` from compact `component.json`
  manifests to generic `definition/definition.json` packages with embedded
  component/package/pins/simulation/UI definition layers. `load_component()`
  still returns the compatibility manifest shape, while `load_component_package()`
  and CLI/API `component-package` now support both digital IC packages and
  generic Virtual/Passive packages. `DB/Discrete` remains on compact
  `component.json`.
- Added `BC549` and `BC559` discrete component entries, red/blue/yellow LED
  passive packages, and explicit group migration-status notes.
- Froze the DB chip model as `v0.1` on `2026-07-09` in `DB/index.json`,
  `DB/chip.schema.json`, `DB/digital.schema.json`, and `DB/README.md`.
- Promoted RV8GR Batch 2 from migrated records to a complete seed-style set:
  every RV8GR part is hard-gated for package layers, non-placeholder truth
  vectors, declared edge criteria, split test records, and executable truth
  coverage in `python/tests/test_generated_split_records.py`.

## Verification Already Run Recently

- `python3 -B -m tests.test_block_ui`
- `python3 -B -m tests.test_cli`
- `python3 -B -m tests.test_api`
- `python3 -B -m tests.test_design`
- `python3 -B -m tests.test_contracts`
- `python3 -B -m tests.test_simulation_service`
- `python3 -B -m tests.test_db`
- `python3 -B -m tests.test_generated_split_records`
- `python3 -B -m tests.test_chips`
- `python3 -B -m tests.test_netlist`
- `python3 -B -m tests.test_equivalence`
- `python3 -m chiplib.cli db --audit`
- `python3 -m chiplib.cli db --status`
- 74xx Verilog smoke
- Memory Verilog smoke

Focused doc-save verification run:

- `PYTHONPATH=python python3 -B -m tests.test_db`
- `PYTHONPATH=python python3 -B -m tests.test_generated_split_records`
- `git diff --check`

Note: rerun the focused tests after any new schema/loader/generator edits.
