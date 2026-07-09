# Components Session Handoff

Date: 2026-07-09
Last updated: 2026-07-09, session save

## Current State

- Repo: `/home/jo/kiro/Components`
- Branch: `main`
- Status at handoff: clean, `main...origin/main`
- Latest commit: `aa81704 Add generator-ready component definitions`
- Latest pushed commit before this save: `e4dfeff Add Components session handoff`

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
```

Seed packages no longer need `chip.json`; compatibility catalog/API data is
synthesized from `definition/definition.json` and `simulation/netlist.json`.
Legacy `chip.json` remains supported for older components.

## Team Task Assignments

- Arendt: spec and schemas for component packages.
- Feynman: generated docs and interactive demos for students.
- Halley: truth table, timing, tri-state, bus-fight, and propagation tests.
- Ohm: datasheet evidence, package evidence, timing, and electrical data.
- Leibniz: loader compatibility, generators, and CLI/API generation command.

## Next Safe Tasks

1. Expand generated documentation and interactive demo wording beyond the
   initial structured data.
2. Grow generated split-record execution from Python-only checks toward
   generated Verilog testbenches.
3. Keep Verilog smoke compiling all 74xx and memory models.
4. Keep `TEAM_SKILLS.md`, `COMPONENT_GENERATION_BACKLOG.md`, and this handoff
   synchronized whenever the team roles or seed-chip plan changes.

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

## Verification Already Run Recently

- `python3 -B -m tests.test_block_ui`
- `python3 -B -m tests.test_cli`
- `python3 -B -m tests.test_api`
- `python3 -B -m tests.test_design`
- `python3 -B -m tests.test_contracts`
- `python3 -B -m tests.test_simulation_service`
- `python3 -B -m tests.test_db`
- `python3 -B -m tests.test_chips`
- `python3 -B -m tests.test_netlist`
- `python3 -B -m tests.test_equivalence`
- `python3 -m chiplib.cli db --audit`
- `python3 -m chiplib.cli db --status`
- 74xx Verilog smoke
- Memory Verilog smoke

Note: rerun the focused tests after any new schema/loader/generator edits.
