# Component Generation Backlog

Goal: make one canonical component definition file able to generate or drive:

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

The first seed batch is:

- `74HC161`
- `74HC157`
- `74HC245`
- `74HC574`
- `AT28C256`

## Current Direction

Each chip gets one generator-ready source file:

```text
DB/<group>/<part>/definition/definition.json
```

Other package folders hold non-definition layers:

```text
simulation/
tests/
symbol/
```

Definition sublayers are embedded in `definition/definition.json` under
`definition_layers`, and datasheet sources are embedded under
`datasheet.sources`. Legacy split definition or datasheet files are
compatibility fallback inputs, not required seed-package source files.
Packages no longer need `chip.json` or `component.json`; `load_component(part)`
synthesizes the catalog manifest from `definition/definition.json` and package
metadata. Runtime compatibility paths still exist for external older data, but
the active DB tree is package-definition only.

## Pim's Comments

- Keep `definition.json` as the canonical source for generators. Do not make
  generators scrape Verilog comments, Python classes, or Markdown.
- Keep datasheet evidence visible. If timing or electrical data is not
  extracted yet, mark it as missing or `datasheet-required`.
- Migration proceeded seed batch first, then RV8GR Batch 2, then the rest of
  the active IC catalog. Keep future package changes gated by tests and
  generated artifacts.
- For students, the generated docs and demos matter as much as simulator
  correctness. The same definition should explain the chip and run it.
- The DB package must separate definition, simulation, schematic/symbol,
  verification, and generation. UI must consume these layers, not own them.

## Team Tasks

### 1. Arendt - Specification And Schema

Status: done for `db.component.digital` seed schema; split-file schemas remain
future work.

Owns:

- `DB_COMPONENT_PACKAGE_SPEC.md`
- `GENERATION_PIPELINE.md`
- future schemas under `Schemas/`

Tasks:

- Define schemas for `db.component.digital`, `db.component.pins`,
  `db.component.logic`, `db.component.timing`, and generated test files.
- Define required vs optional fields for beginners and advanced hardware users.
- Define how missing datasheet timing/electrical values are represented.
- Add schema validation tests for the seed batch.

Acceptance:

- `python3 -B -m tests.test_db` validates every seed `definition.json`.
- Missing timing/electrical values are visible, not silently absent.

Done:

- `DB/digital.schema.json` defines the current umbrella
  `db.component.digital` seed schema.
- `python/chiplib/db.py` validates seed definitions and checks synthesized
  compatibility data against definition, simulation, and generation metadata.
- `python/tests/test_db.py` covers schema shape and seed definition agreement.
- `.github/workflows/python-tests.yml` already runs `tests.test_db` and
  `tests.test_block_ui`.

### 2. Feynman - Learning Docs And Interactive Demos

Status: generated artifact files written; prose/demo polish remains.

Owns:

- generated documentation shape
- interactive demo requirements
- student-facing wording

Tasks:

- Define generated Markdown sections from `definition.json`.
- Define a simple interactive demo contract for each seed chip.
- Keep language clear for ages `10-15`, while preserving correct pin names.
- Start with `74HC245` and `74HC161` examples.

Acceptance:

- Each seed part has enough metadata to generate a beginner-readable page.
- Demo definitions say which inputs can be toggled and which outputs/probes are
  shown.

Done:

- `generate_component_artifacts(part)` emits documentation and interactive demo
  data from `definition/definition.json`.
- `74HC245` exposes initial generated docs sections and demo controls/probes.
- Each seed package now has `generated/artifacts.json` written from the CLI
  generator path.

### 3. Halley - Verification Matrix

Status: generated split-record Python checks wired; first generated Verilog
bench artifact exists; the full active IC catalog now has seed-style package
layers, explicit truth vectors, edge criteria, generated artifacts, and
executable regression gates.

Owns:

- truth table tests
- timing tests
- tri-state tests
- bus-fight tests
- propagation tests

Tasks:

- Map each seed chip to required test types.
- Add machine-readable test files where useful.
- Ensure GitHub Actions runs the Python and Verilog verification every commit.
- Expand direct Python-vs-Verilog equivalence for seed parts first.

Acceptance:

- Seed batch has explicit test coverage records.
- `python3 -B -m tests.test_equivalence` covers all memory seed parts and the
  first 74xx seed parts.
- Verilog smoke instantiates every memory module directly.
- Every active IC truth-table record declares `edge_criteria`.
- Active IC truth records do not use `basic_function` placeholders or
  intent-only vectors.
- The full active 74xx/memory catalog has the same required package/test layers
  as the seed chips.

Done:

- The seed batch has machine-readable `tests/truth_table.json`,
  `tests/timing.json`, `tests/tri_state.json`, `tests/bus_fight.json`, and
  `tests/propagation.json` records where applicable.
- `python/tests/test_chips.py` reads seed split test records and exercises the
  corresponding Python chip models.
- `python/tests/test_generated_split_records.py` executes seed truth-table
  records through generated dispatch checks, validates timing/tri-state/bus
  records, and guards Verilog smoke workflow scope.
- `.github/workflows/python-tests.yml` runs `tests.test_generated_split_records`.
- `tests.test_generated_split_records` now enforces `edge_criteria` on all IC
  truth records.
- Seed checks cover enable/hold behavior, async priority, executable
  bus-fight/no-conflict cases, Python-vs-Verilog coverage guards, memory write
  protection, and propagation/timing metadata.
- RV8GR-used chips now have explicit per-chip truth vectors for logic, clocked
  controls, bus parts, and ROM/RAM options.
- The remaining active 74xx/memory truth placeholders were replaced with
  explicit executable records. Generic fresh-chip pin-vector records now replay
  through the Python model for each catalog chip, and `CY7C199` has
  SRAM-family write/read/high-Z vectors.
- `python/tests/test_generated_split_records.py` now enforces the RV8GR
  complete-set gate: package files, non-placeholder truth vectors, declared
  edge criteria, split test records, and executable truth coverage.
- `python/tests/test_generated_split_records.py` now also gates the active IC
  placeholder inventory to an empty set.
- RV8GR complete-set readiness artifacts have been moved out of `DB/` and into
  the RV8GR repo so Components DB stays project-neutral.

### 4. Ohm - Electrical, Timing, And Datasheet Evidence

Status: first seed-batch extraction done.

Owns:

- datasheet evidence
- package evidence
- timing/electrical extraction

Tasks:

- Fill missing `package_evidence` fields in verified manifests.
- Extract first timing/electrical facts for `74HC245`.
- Mark unknown electrical values as `datasheet-required`.
- Review active-low naming mismatches in embedded pinout comments.

Acceptance:

- DB audit catches missing package evidence.
- `74HC245` has traceable source evidence for package, logic, and timing.

Done:

- `74HC245` timing records include first TI datasheet switching values.
- `74HC245` electrical records include first operating-voltage, input-threshold,
  output-drive, supply-current, and input-capacitance facts.
- `74HC161`, `74HC157`, `74HC574`, and `AT28C256` now have first
  timing/electrical extraction files with datasheet evidence.

### 5. Leibniz - Generators And Loader Compatibility

Status: loader and generator path active for layered IC packages; generic
Virtual/Passive definition packages are also supported.

Owns:

- generation code
- loader compatibility
- CLI/API output

Tasks:

- Add a loader that can read `definition/definition.json`.
- Keep `load_component(part)` compatible with callers that need a flat catalog
  view while sourcing active data from package definitions.
- Prototype generators for:
  - normalized JSON detail
  - Python simulator adapter report
  - Verilog wrapper/export metadata
  - KiCad symbol JSON
  - SVG pinout JSON
  - documentation data
  - unit test vectors
  - interactive demo data
- Add CLI command proposal, likely `python3 -m chiplib.cli db PART --generate`.

Acceptance:

- Seed, RV8GR Batch 2, active IC, Virtual, Passive, and Discrete packages load
  through the current DB API from `definition/definition.json`.
- Package definitions emit generator-ready artifact reports from one file.

Done:

- `load_digital_package(part)` loads definition sublayers from
  `definition/definition.json`, with legacy split-file and derived fallback layers
  preserved for compatibility.
- `generate_component_artifacts(part)` emits structured outputs for the seed
  generation targets.
- CLI/API expose `--package`, `--generate`, `component-package`, and
  `component-generate`.
- All five seed packages now include physical `simulation/model.json`,
  `simulation/model.py`, `simulation/model.v`, `simulation/netlist.json`, and
  `symbol/dip.json` layers.
- All five seed packages now expose `portable_files` metadata so project/system
  exports know to copy local `simulation/model.py` with each chip.
- `portable_files` also lists `python/chiplib/core.py`, which must travel with
  local Python chip models as the shared runtime primitive layer.
- Circuit/system exports de-duplicate that runtime: one copied
  `chiplib/core.py` is shared by all exported chip `model.py` files.
- Seed `status` now lives in `definition/definition.json`, and active Verilog
  export mapping is read from `simulation/netlist.json` before the legacy
  `chip.json` fallback.
- Seed `chip.json` files have been removed; seed catalog/API compatibility is
  synthesized from `definition/definition.json` plus `simulation/netlist.json`.
- All five seed packages now keep component/package/pins/power/logic/timing/
  electrical definition sublayers inside the single `definition/definition.json`
  source file.
- All five seed packages now keep datasheet source records inside
  `definition/definition.json`.

## Seed Batch Checklist

### 74HC161

- ✅ `definition/definition.json`
- ✅ merged `definition_layers` source
- ✅ split test files
- ✅ generated doc data
- ✅ generated symbol data
- ✅ generated artifact report
- ✅ timing/electrical evidence extraction
- ✅ edge criteria, ENP/ENT hold, no-rising-edge hold, count resume, and
  `/CLR` priority truth tests

### 74HC157

- ✅ `definition/definition.json`
- ✅ merged `definition_layers` source
- ✅ split test files
- ✅ generated doc data
- ✅ generated symbol data
- ✅ generated artifact report
- ✅ timing/electrical evidence extraction
- ✅ level-sensitive edge criteria and Python-vs-Verilog coverage guard

### 74HC245

- ✅ `definition/definition.json`
- ✅ merged `definition_layers` source
- ✅ initial `simulation/`, `tests/`, `symbol/` package
- ✅ generator prototype
- ✅ generated KiCad symbol data
- ✅ generated SVG pinout data
- ✅ generated documentation data
- ✅ generated interactive demo data
- ✅ generated artifact report
- ✅ timing/electrical evidence extraction
- ✅ DIR both directions, `/OE=1` high-Z, reverse patterns, and executable
  bus-fight/no-conflict checks

### 74HC574

- ✅ `definition/definition.json`
- ✅ merged `definition_layers` source
- ✅ split test files
- ✅ generated doc data
- ✅ generated symbol data
- ✅ generated artifact report
- ✅ timing/electrical evidence extraction
- ✅ rising-edge latch, no-clock hold, output-disable capture, re-enable, and
  bus-conflict/high-Z checks

### AT28C256

- ✅ `definition/definition.json`
- ✅ merged `definition_layers` source
- ✅ split test files
- ✅ generated doc data
- ✅ generated symbol data
- ✅ generated artifact report
- ✅ timing/electrical evidence extraction
- ✅ write/read, `/CE=1` write-protect, `/WE=1` write-protect, output-disable
  high-Z, and control-window edge criteria

## Batch 2 - RV8GR Chip Migration

Status: complete by the seed-package record gate for the RV8GR BOM chip set.
Package migration, explicit truth vectors, edge criteria, split test records,
and executable coverage are done for all RV8GR Batch 2 parts. Deeper
datasheet-backed timing/electrical extraction remains future work for
rest-of-catalog parts beyond the seed/RV8GR checkpoint.

Source of truth:

- `/home/jo/kiro/RV8/RV8GR/README.md` BOM: 34 logic packages plus ROM and RAM.
- `/home/jo/kiro/RV8/RV8GR/doc/12_netlist.md`: U1-U34, ROM, and RAM package
  list from the wiring source.

Target parts:

- Logic: `74HC161`, `74HC574`, `74HC245`, `74HC164`, `74HC283`, `74HC86`,
  `74HC541`, `74HC157`, `74HC74`, `74HC688`, `74HC04`, `74HC32`, `74HC00`,
  and `74HC21`.
- Memory: `AT28C256` or `SST39SF010A` for ROM, and `62256` or `AS6C62256`
  for RAM.

Migration phases:

1. Done from seed batch: `74HC161`, `74HC574`, `74HC245`, `74HC157`, and
   `AT28C256`.
2. Done RV8GR logic chips: `74HC00`, `74HC04`, `74HC21`, `74HC32`, `74HC74`,
   `74HC86`, `74HC164`, `74HC283`, `74HC541`, and `74HC688`.
3. Done RV8GR memory chips/options: `62256`, `AS6C62256`, and
   `SST39SF010A`.

Done:

- Added full package folders for the 13 Batch 2 parts, with
  `definition/definition.json`, local `simulation/model.py`, local
  `simulation/model.v`, `simulation/netlist.json`, `simulation/model.json`,
  `symbol/dip.json`, split test records, and generated artifacts.
- Removed legacy `chip.json` files for the migrated Batch 2 parts.
- Expanded package contract tests so all migrated seed and RV8GR Batch 2 chips
  must load from `definition/definition.json` and expose package-local
  simulation/export files.
- Added `tools/migrate_ic_packages.py` as a repeatable migration helper for
  this package shape.
- Migrated the rest of the active IC catalog after Batch 2. All 62 IC parts
  under `DB/74xx` and `DB/Memory` now use package folders with
  `definition/definition.json`; no IC `chip.json` files remain.
- Generalized the migration helper as `tools/migrate_ic_packages.py`; catalog
  chips get package-local `simulation/model.py` files with local behavior logic
  and only `chiplib.core` as the shared runtime dependency.
- Expanded package tests to discover all `definition/definition.json` IC
  packages dynamically instead of maintaining a manual migrated-part list.
- Replaced RV8GR-used `basic_function` placeholders with chip-specific truth
  vectors for the full RV8GR Batch 2 set.
- Deepened representative RV8GR records for counter load/count, bus
  transceiver high-Z and repeated direction reversal, register re-enable
  capture, and memory cross-address persistence.
- Added `edge_criteria` to every active IC truth-table record.
- Added a hard RV8GR complete-set test gate in
  `python/tests/test_generated_split_records.py`.
- Added a structural all-active IC package gate for the 62 active 74xx/memory
  package folders.
- Added generated `verilog_testbench` artifact metadata and emitted generated
  bench support for `74HC157`, `74HC00`, `74HC04`, `74HC32`, and `74HC86`.
- Added CI/workflow guard to compile package-local `simulation/model.v` files.
- Replaced the remaining active-catalog truth-placeholder inventory with
  explicit pin-vector or SRAM-family truth records, regenerated each affected
  `generated/artifacts.json`, and made the placeholder inventory gate empty.
- Added structural Verilog export pinout comments from `Design.to_verilog()`
  so exported circuit wrappers carry a physical pin table beside each chip
  instance.
- Proved all 62 active ICs export to structural Verilog and compile with
  `iverilog`; `AS6C62256` and `CY7C199` now include the base 62256 Verilog
  dependency in `required_files`.

Acceptance for each migrated Batch 2 chip:

- ✅ `definition/definition.json` is the canonical package definition.
- ✅ No seed-style `chip.json` remains after status/export/datasheet data are
  migrated.
- ✅ `simulation/model.py`, `simulation/model.v`, `simulation/netlist.json`, and
  `simulation/model.json` live inside the chip package.
- ✅ `symbol/dip.json`, split test records, and generated artifacts are present.
- ✅ `portable_files` includes the local `simulation/model.py`; Python models
  also require shared `python/chiplib/core.py`, copied once for chip/circuit/
  system exports.
- ✅ Focused Python DB/generation tests and Verilog smoke/equivalence checks pass.
- ✅ Active IC truth records are explicit and executable through
  `tests.test_generated_split_records`.
- ✅ All 62 active 74xx/memory packages are now checked as a complete
  seed-style set for package layers, generated artifacts, truth coverage, and
  structural Verilog export dependencies.

## GitHub Actions

Existing workflows already run on every push and pull request:

- `.github/workflows/python-tests.yml`
- `.github/workflows/verilog-smoke.yml`

Next CI tasks:

- Keep Verilog smoke compiling all 74xx and memory models.
- Keep memory smoke instantiating each memory module directly.
- Full active IC catalog hardening complete: all 62 physical
  `generated/artifacts.json` files were refreshed from the current generator,
  and `tests.test_generated_split_records` now has a strict no-drift gate that
  compares each checked-in generated artifact file with
  `generate_component_artifacts(part)`.
- Full active IC structural export smoke complete: one-chip wrappers for all
  62 active parts export with embedded pinout comments and compile against the
  package-local Verilog files listed by `required_files`.
- Grow generated Verilog bench emission to decoder, tri-state, sequential,
  arithmetic, and memory-specific shapes after their truth records are explicit.
- Extend executable edge/enable/bus/memory checks beyond the generic
  fresh-chip truth vectors where individual chips need deeper seed-style
  behavioral scenarios.
- Extract datasheet-backed timing/electrical fields for the non-RV8GR active
  ICs that still carry `model-derived` timing and `datasheet-required`
  electrical placeholders.
