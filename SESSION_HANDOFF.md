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
- Added generator-ready `definition/digital.json` seed files for:
  - `74HC161`
  - `74HC157`
  - `74HC245`
  - `74HC574`
  - `AT28C256`
- Added an initial split package for `74HC245`:
  - `definition/`
  - `simulation/`
  - `tests/`
  - `symbol/`
  - `datasheet/`
- Saved current specialist-agent skills in `TEAM_SKILLS.md`:
  - Arendt: specs and schemas
  - Feynman: docs and demos
  - Halley: verification matrix
  - Ohm: datasheet/pin/timing/electrical evidence
  - Leibniz: loaders, generators, CLI/API integration

## Architecture Direction

Use one canonical component definition file per chip:

```text
DB/<group>/<part>/definition/digital.json
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

Layer split:

```text
definition/
simulation/
tests/
symbol/
datasheet/
```

Keep `chip.json` as the current compatibility manifest until the loader can
merge split packages safely.

## Team Task Assignments

- Arendt: spec and schemas for component packages.
- Feynman: generated docs and interactive demos for students.
- Halley: truth table, timing, tri-state, bus-fight, and propagation tests.
- Ohm: datasheet evidence, package evidence, timing, and electrical data.
- Leibniz: loader compatibility, generators, and CLI/API generation command.

## Next Safe Tasks

1. Add schema validation for `db.component.digital` files.
2. Add tests that the five seed `digital.json` files agree with current
   `chip.json` pins/package/module metadata.
3. Add `tests.test_block_ui` to `.github/workflows/python-tests.yml`.
4. Prototype `chiplib` loader support for `definition/digital.json` without
   breaking `load_component(part)`.
5. Start generator prototype for `74HC245`:
   - normalized JSON detail
   - Verilog export metadata
   - SVG pinout data
   - documentation data
   - interactive demo data
6. Keep `TEAM_SKILLS.md`, `COMPONENT_GENERATION_BACKLOG.md`, and this handoff
   synchronized whenever the team roles or seed-chip plan changes.

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
