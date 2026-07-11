# Components Session Handoff

Date: 2026-07-09
Last updated: 2026-07-11, after the full 74HC/HCT source/model/export pass and
Support IC Python-model pass

## Current State

- Repo: `/home/jo/kiro/Components`
- Branch: `main`
- Status at this handoff: staged checkpoint prepared for commit/push.
- Previous pushed commit before this handoff: `8de6f7c Compact DB package docs
  and retire legacy manifests`
- Latest pushed RV8GR virtual-check commits:
  - `8bb462b Add RV8GR virtual fault protocol`
  - `49ed732 Add circuit virtual fault checker`
  - `b8719bc Update circuit backlog checkpoint status`

## Latest Save: 2026-07-11 Full 74HC/HCT And Support IC Verification Pass

Completed in this checkpoint:

- Expanded and normalized the active 74HC/HCT DB set with package-local
  `definition/definition.json`, Python models, Verilog models, netlists, split
  tests, generated artifacts, source PDFs, and regenerated status/report files.
- Removed the non-standard/deprecated parts requested for removal from active
  source and DB scope: `74HC42`, `74HC73`, `74HC112`, and `74HC181`.
- Added Verilog pinout comments as the standing style for generated/local HDL
  chip files, so pin number/name truth is visible near the model body.
- Added passive crystal and oscillator packages for 1 MHz, 2 MHz, 5 MHz, and
  10 MHz.
- Added Support group IC packages for `LM358`, `LM393`, `MAX232`, `NE555`, and
  `ULN2803A` with source-backed pinouts and local Python functional models.
- Support IC boundary is explicit: these are logic-level learning models for
  Components behavior tests, not SPICE analog signoff models.
- `load_component_package()` now includes generic package-local Python models in
  `files` and `portable_files`; `create_chip()` now resolves `DB/Support`
  models.
- Python behavior crosscheck now includes `Support`, so the support-chip models
  are checked with pin maps, truth vectors, and model-delay metadata.

Verification for this checkpoint:

- `PYTHONPATH=python python3 -B python/tests/test_chips.py`
- `PYTHONPATH=python python3 -B python/tests/test_db.py`
- `PYTHONPATH=python python3 tools/python_behavior_crosscheck.py`
  - 75 models checked
  - 0 failures
  - 0 warnings
- `PYTHONPATH=python python3 -B -m chiplib.cli db --audit`
  - `ok: true`
  - no errors/warnings
- `git diff --cached --check`

Notes for next resume:

- `.venv` was intentionally removed from the worktree cleanup; system Python did
  not have `pytest`, so the focused checks above used the repo's direct test
  runners and CLI/crosscheck scripts.
- The support-chip Python models are intentionally simplified. Deep analog
  validation belongs to a future SPICE/external-model lane, not the current
  digital behavior gate.

## Latest Save: 2026-07-11 DB Cleanup And Package Contract

Completed in this checkpoint:

- Components DB is package-definition only:
  - active ICs use `schema: db.component.digital`
  - Virtual, Passive, and Discrete use `schema: db.component.definition`
  - `load_component(part)` returns a synthesized `db.component.manifest`
    catalog view for callers that still need flat component cards
- Retired active-tree legacy artifacts:
  - `DB/chip.schema.json`
  - all `DB/**/chip.json`
  - all `DB/**/component.json`
- Migrated Discrete entries to package definitions:
  - `DB/Discrete/NPN/definition/definition.json`
  - `DB/Discrete/PNP/definition/definition.json`
  - `DB/Discrete/BC549/definition/definition.json`
  - `DB/Discrete/BC559/definition/definition.json`
- Removed RV8GR-specific Markdown/JSON artifacts from `DB/`; valued RV8GR
  protocol/readiness/bench artifacts were moved to `/home/jo/kiro/RV8/RV8GR/doc/`.
- Compacted DB docs:
  - `DB/README.md`
  - `DB/COMPONENT_TEST_PROTOCOL.md`
  - `DB/STUDENT_CATALOG.md`
- Kept virtual-test information at DB root because it is DB-level information,
  not a Virtual device package:
  - `DB/VIRTUAL_TEST_INSTRUMENTS.json`
  - `DB/VIRTUAL_TEST_GENERATOR_CONTRACT.json`
  - matching `.md` guides

Verification for this checkpoint:

- `PYTHONPATH=python python3 -B -m tests.test_db`
- `PYTHONPATH=python python3 -B -m tests.test_generated_split_records`
- `PYTHONPATH=python python3 -B -m tests.test_lib_circuits`
- `PYTHONPATH=python python3 -B -m tests.test_cli`
- `PYTHONPATH=python python3 -B -m tests.test_api`
- `PYTHONPATH=python python3 -B -m tests.test_block_ui`
- `git diff --check`

Current remaining lanes:

1. Continue non-RV8GR datasheet timing/electrical extraction for active ICs
   that still rely on simulator-default timing rows.
2. Keep virtual-test contracts at DB root unless they become real component
   packages with their own `definition/definition.json`.
3. Push both repos together when RV8GR doc artifacts and Components DB cleanup
   are reviewed together.

## Latest Save: 2026-07-10 Student Readability And RV8GR Count Audit

Completed in this checkpoint:

- Added `STUDENT_READABILITY_AUDIT.md` to map each document to student,
  teacher, tool-builder, or maintainer use.
- Updated root `README.md`, `STUDENT_GUIDE.md`, and
  `Lib/Circuits/README.md` with the beginner route and student stop
  conditions.
- Updated `TEAM_SKILLS.md` shared and per-member skills for:
  - student readability ownership
  - RV8GR physical package vs part-definition count vocabulary
  - current board-instance audit responsibility
  - physical-signoff boundary around timing, bus deadband, and real scope
    evidence

RV8GR count result checked from live files:

- RV8GR board source:
  `/home/jo/kiro/RV8/RV8GR/Kicad/gen_kicad.py`
- Physical board packages: 36 (`U1`-`U34`, `ROM1`, `RAM1`)
- Board-used part types: 16
- Components RV8GR-ready definition/options set: 18, because RAM and ROM
  alternatives are tracked separately in readiness docs.
- All 16 board-used part types currently have:
  `definition/definition.json`, local Python model, local Verilog model,
  simulation JSON, netlist JSON, DIP symbol, generated artifacts, and
  truth/timing/tri-state/bus-fight/propagation split records.

Verification run for this checkpoint:

```sh
PYTHONPATH=python python3 -B -m tests.test_db
PYTHONPATH=python python3 -B -m tests.test_generated_split_records
PYTHONPATH=python python3 -B -m tests.test_lib_circuits
PYTHONPATH=python python3 -B -m tests.test_chips
PYTHONPATH=python python3 -B -m chiplib.cli db --audit
PYTHONPATH=python python3 -B -m chiplib.cli db --status
git diff --check
```

Observed pass results:

- `Components DB tests passed`
- `Components generated split-record tests passed`
- `Components library circuit tests passed`
- `Components Python chip tests passed`
- `chiplib.cli db --audit`: `ok: true`, no warnings
- `chiplib.cli db --status`: `ok: true`, no warnings
- `git diff --check`: clean

Important boundary:

- Components virtual/model checks are ready for RV8GR circuit and system work.
- Physical hardware speed/signoff remains blocked until real voltage,
  frequency, bus-deadband, clock/reset edge, memory float/write timing, and
  oscilloscope evidence are recorded.

Next lanes after this push:

1. Add generated student chip cards from `definition/definition.json`.
2. Add a short student command card for common CLI/API wiring actions.
3. Build the first visual chip-block editor screen on `components.block_ui`.
4. Add MCP adapter only after editor/service command names settle.
5. Continue physical RV8GR evidence collection before any hardware-ready claim.

## Latest Save: 2026-07-10 Student Guide And Handoff

Completed since the previous checker handoff:

- Added `STUDENT_GUIDE.md` as the beginner-first Components guide for CLI and
  local API use before the visual editor exists.
- Linked `STUDENT_GUIDE.md` from root `README.md` and `python/README.md`.
- Cleaned `SERVICE_CONTRACT.md` so documented CLI examples match the current
  CLI behavior: JSON output by default, no fake `--json` option.
- Added `circuit-faults` to the service contract and kept the RV8GR
  virtual-vs-hardware boundary explicit.
- Saved a persistent future-task note to review chip JSON/component definition
  output for student-friendliness and document the system wiring commands used
  in Components.

Verified for the student-guide checkpoint:

```sh
PYTHONPATH=python python3 -B -m chiplib.cli validate Examples/nand.json
PYTHONPATH=python python3 -B -m chiplib.cli run Examples/nand.json
PYTHONPATH=python python3 -B -m chiplib.cli circuit-faults Lib/Circuits/RV8GR_WholeSystemChipLevelVirtual/circuit.json
PYTHONPATH=python python3 -B -m chiplib.api --stdio
PYTHONPATH=python python3 -B -m tests.test_cli
PYTHONPATH=python python3 -B -m tests.test_api
PYTHONPATH=python python3 -B -m tests.test_contracts
git diff --check
```

Current remaining lanes:

1. Build the first visual chip-block editor screen on top of
   `components.block_ui`.
2. Add an MCP adapter after editor/service names settle.
3. Collect physical RV8GR evidence before any hardware-ready claim.
4. Continue broader non-RV8GR component catalog hardening.
5. Later: review chip JSON/component definition output for student clarity and
   document system wiring commands used in Components.

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
- Saved current Components team skills in `TEAM_SKILLS.md`:
  - Pim: coordination and task routing
  - Bank: architecture, schemas, and service boundaries
  - Fern: verification matrix and release confidence
  - Mint: RTL models, export contracts, and HDL benches
  - Ohm: datasheet, pin, timing, and electrical evidence
  - Bam: Python behavior, circuit simulation, CLI/API workflows
  - Noon: student docs, examples, and lab wording

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

- Pim: coordinate backlog, handoff, commits, and cross-file consistency.
- Bank: spec and schemas for component packages and circuit-checker contracts.
- Fern: truth table, timing, tri-state, bus-fight, propagation, and virtual
  physical-system fault tests.
- Mint: Verilog models, export contracts, and edge/timing RTL alignment.
- Ohm: datasheet evidence, package evidence, timing, and electrical data.
- Bam: loader compatibility, generators, CLI/API commands, and Python checker
  implementation.
- Noon: generated docs, interactive demos, and student-readable fix methods.

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

## 2026-07-10 RV8GR Virtual Physical-System Fault Checker

Protocol checkpoint pushed:

- `8bb462b Add RV8GR virtual fault protocol`

Completed checker work ready for commit/push:

- Added `python/chiplib/virtual_faults.py`.
- Added `python3 -m chiplib.cli circuit-faults <circuit.json>`.
- Checker reads `components.lib.circuit` JSON and reports the four required
  virtual physical-system fault classes:
  - wrong pin number/name or active-low marker
  - output-output wiring without explicit bus/enable proof
  - missing positive/negative or rising/falling edge statement for
    edge-sensitive chips
  - shared bus or stress-net timing without R/C, DelayNoise, setup/hold, float,
    or deadband coverage
- Added regression coverage in `python/tests/test_lib_circuits.py` for good
  RV8GR packages and deliberately bad mini-circuits.
- Added CLI coverage in `python/tests/test_cli.py`; bad circuit reports exit
  status `2`.

Team ownership:

- Bank owns checker architecture and circuit JSON contract boundaries.
- Bam owns Python/CLI implementation.
- Fern owns failing gates and CI confidence.
- Ohm owns pin truth, active-low markers, and timing/deadband interpretation.
- Mint owns edge/RTL alignment.
- Noon owns student-readable fault and fix wording.
- Pim keeps this handoff, backlog, tests, commit, and push aligned.

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
- RV8GR complete-set readiness and virtual bench artifacts were moved out of
  `DB/` and into the RV8GR repo; Components DB stays project-neutral.
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
- Migrated `DB/Virtual`, `DB/Passive`, and `DB/Discrete` from compact
  `component.json` manifests to generic `definition/definition.json` packages
  with embedded component/package/pins/simulation/UI definition layers.
  `load_component()` now returns the synthesized `db.component.manifest` view,
  while `load_component_package()` and CLI/API `component-package` support
  digital IC and generic component packages.
- Added `BC549` and `BC559` discrete component entries, red/blue/yellow LED
  passive packages, and explicit group migration-status notes.
- Froze the DB chip model as `v0.1` on `2026-07-09` in `DB/index.json`,
  `DB/digital.schema.json` and `DB/README.md`; `DB/chip.schema.json` is now
  retired.
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

## 2026-07-10 Pim Team Session Save

Current repo state:

- Branch: `main`
- Latest pushed commit: `ee4c418 Add RV8GR traces and chip truth batches`
- Working tree was clean immediately after the push before this handoff/skills
  documentation update.

Work completed in the latest pushed commit:

- Task 2, RV8GR trace packages:
  - Added `Lib/Circuits/RV8GR_StoreLoadBranchTrace/`.
  - Covered SB, LB, and BEQ rows from
    `/home/jo/kiro/RV8/RV8GR/doc/03_instruction_trace.md`.
  - Tests recompute expected ABUS, IBUS, DBUS, PC, AC, Z, RAM state, U7
    direction, and bus-owner/no-contention policy.
- Task 4, chip-specific truth vectors and active-catalog completion:
  - Replaced the remaining active 74xx/memory `basic_function` truth
    placeholders with explicit executable records.
  - Added generic fresh-chip pin-vector execution coverage for the catalog
    records that do not yet need deeper hand-authored control-edge scenarios.
  - Added SRAM-family write/read/high-Z truth coverage for `CY7C199`.
  - Regenerated affected `generated/artifacts.json` files and made the
    placeholder inventory gate empty in `python/tests/test_generated_split_records.py`.
- Structural Verilog export hardening:
  - `Design.to_verilog()` now emits embedded pinout documentation comments
    beside each chip instance, matching the package-local model style.
  - One-chip structural wrappers for all 62 active `DB/74xx` and `DB/Memory`
    parts export with pinout comments and compile with `iverilog`.
  - Fixed `AS6C62256` and `CY7C199` required-file metadata so their exports
    include `DB/Memory/62256/simulation/model.v`, which provides `mem_62256`.
- Task 5, datasheet timing/electrical extraction:
  - Filled source-backed timing/electrical fields for `74HC138`, `74HC139`, and
    `74HC151`.
  - Source-named TI datasheet switching/electrical values are kept separate from
    the simulator default delay so 5 MHz and propagation claims remain
    conservative.
- Updated `BACKLOG.md`, `Lib/Circuits/README.md`, and added
  `Lib/Circuits/BACKLOG.md`.

Verification run for that commit:

- `PYTHONPATH=python python3 -B -m tests.test_lib_circuits`
- `PYTHONPATH=python python3 -B -m tests.test_generated_split_records`
- `PYTHONPATH=python python3 -B -m tests.test_db`
- `python3 -m py_compile python/tests/test_lib_circuits.py python/tests/test_generated_split_records.py`
- JSON parser check over the edited truth/circuit/definition files
- Active IC placeholder inventory is now gated to an empty set by
  `tests.test_generated_split_records`.
- Full 62-part structural Verilog export/compile smoke passed and wrote
  generated wrappers under `/tmp/components-all-chip-verilog-export`.
- `git diff --check`

Team/skill updates from this handoff:

- `TEAM_SKILLS.md` now records the Store/Load/Branch trace proof, the task-4
  placeholder-removal discipline, and the task-5 datasheet extraction discipline.
- Fern owns the placeholder inventory gate: truth records, required vectors,
  generated artifacts, and executable Python-model coverage must move together.
- Ohm owns source-named timing/electrical extraction and the separation between
  datasheet maxima and simulator defaults.
- Bam owns trace-package executable helpers that recompute state and bus
  ownership from reusable circuit logic.
- Noon owns source-row-grounded trace docs that do not hide bus contention risk.

Recommended next tasks:

1. Commit the current Components checkpoint after reviewing the large dirty
   worktree: datasheets, pin/model fixes, AT28C256 timing/write behavior,
   active-catalog truth vectors, structural export pinout comments, and
   SRAM-wrapper Verilog dependencies.
2. Continue task-5 datasheet extraction for the next decoder/mux batch, keeping
   timing/electrical source names inside `definition/definition.json`.
3. Add real bench-evidence fields for selected memory markings, SRAM
   output-disable/read timing, DBUS deadband, and 5 MHz signal-integrity proof.
4. Start the visual chip-block editor lane against `components.block_ui` when
   the user wants UI implementation.
