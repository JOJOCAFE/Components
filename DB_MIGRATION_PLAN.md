# DB Migration Plan

Goal: make `DB/` the chip identity layer for Components without breaking the
current simulator, Verilog models, exporter, tests, or existing projects.

The migration is gradual. For active IC packages, the replacement path is now
the current path: `definition/definition.json` plus package-local simulation,
netlist, symbol, test, and generated artifact files. Virtual and Passive
components also use `definition/definition.json` packages. Legacy manifest
loading remains only as compatibility for older or not-yet-migrated component
groups.

## Target Shape

The DB is now a grouped component catalog. Active IC, Virtual, and Passive
packages live with their family/class and use a layered package shape.
Not-yet-migrated component manifests live with their component class:

```text
DB/
  74xx/
    74HC245/
      definition/definition.json
      simulation/model.py
      simulation/model.v
      simulation/model.json
      simulation/netlist.json
      symbol/dip.json
      tests/*.json
      generated/artifacts.json
  Memory/
    AT28C256/
      definition/definition.json
      simulation/model.py
      simulation/model.v
      simulation/model.json
      simulation/netlist.json
      symbol/dip.json
      tests/*.json
      generated/artifacts.json
  Virtual/
    InputSource/
      definition/definition.json
    Probe/
      definition/definition.json
  Passive/
    LED/
      definition/definition.json
    Resistor/
      definition/definition.json
  Discrete/
    NPN/
      component.json
```

For active ICs, `definition/definition.json` is the canonical source artifact.
It owns component identity, package and pin facts, source evidence, status,
logic/timing/electrical records, and generator contracts. Package-local
`simulation/`, `tests/`, `symbol/`, and `generated/` layers travel with the
chip and are reproducible from the definition plus generator/test inputs.

Virtual and Passive components use `schema: db.component.definition` inside
`definition/definition.json`; their embedded layers describe component
identity, package, pins, simulation service, and UI metadata. The compact
`component.json` artifact remains only for not-yet-migrated grouped components
such as Discrete. Legacy `chip.json` loading remains supported for older
compatibility paths, but no active IC under `DB/74xx` or `DB/Memory` requires
`chip.json`.

## Current Transitional Shape

Active IC package files now provide local implementation and export references:

```text
DB/74xx/<part>/definition/definition.json
DB/74xx/<part>/simulation/model.py
DB/74xx/<part>/simulation/model.v
DB/74xx/<part>/simulation/model.json
DB/74xx/<part>/simulation/netlist.json
DB/74xx/<part>/symbol/dip.json
DB/74xx/<part>/tests/*.json
DB/74xx/<part>/generated/artifacts.json
```

`load_component(part)` synthesizes compatibility data from
`definition/definition.json` and `simulation/netlist.json`. Project/system
exports copy the chip-local `simulation/model.py` with the package and copy
`python/chiplib/core.py` once as the shared runtime primitive layer.

Migrated Virtual and Passive component packages live under:

```text
DB/Virtual/<component>/definition/definition.json
DB/Passive/<component>/definition/definition.json
```

Not-yet-migrated component manifests live under:

```text
DB/Discrete/<component>/component.json
```

## Migration Rules

1. Add or update DB package data before changing generators or services.
2. Every active IC definition must pass `DB/digital.schema.json`; generic
   component definitions must pass loader validation; legacy component
   manifests must pass their relevant schema.
3. Missing chip properties are allowed only when visible in `status`,
   `missing_properties`, or `missing_files`.
4. Exporters and simulators should consume DB metadata through `chiplib.db`,
   not by scanning old folders directly.
5. A physical file move is allowed only after tests prove the old and new
   lookup paths produce the same behavior.
6. Do not delete legacy compatibility loaders until older/not-yet-migrated
   components and at least one existing project smoke test still pass.
7. Keep manufacturer-backed DIP/PDIP evidence mandatory for physical pinout
   status.
8. Grouped virtual/passive/discrete definitions are allowed before behavior is
   executable, but they must declare `group`, `kind`, `role`, `pins`, `status`,
   and their intended `simulation.service`.
9. Direct flat `DB/<part>/chip.json` lookups are retired in runtime code. New
   code must use the DB loader so layered IC packages, generic component
   packages, and legacy manifests resolve through one path.

## Phases

### Phase 1: DB Seed

Status: complete.

- ✅ Add `DB/chip.schema.json`.
- ✅ Add seed manifests for simple gates and memory.
- ✅ Add `chiplib.db` loader and CLI access.
- ✅ Report missing properties and missing referenced files.
- ✅ Expand representative seed coverage across gates, decoders, registers,
  counters, bus parts, SRAM, EEPROM, and flash.

Exit criteria:

- ✅ `python3 -B -m tests.test_db` validates all DB manifests and layered IC
  definitions.
- ✅ `python3 -m chiplib.cli db` lists the current DB.
- ✅ No DB manifest has hidden missing file references.

### Phase 2: DB Audit

Status: complete.

Add audit tooling that compares DB state against the legacy catalog.

Required checks:

- ✅ DB parts vs `Verilog/74xx/*.v` and `Verilog/Memory/*.v`.
- ✅ DB parts vs embedded 74xx pinout comments and Memory embedded pinout comments.
- ✅ DB part status vs `CHIP_STATUS.md`.
- ✅ Missing-datasheet exclusions cannot also appear in verified, modeled,
  tested, DB, or active legacy model/pinout coverage.
- ✅ Embedded Verilog pinout comments match DB manifest pin names and numbers
  for referenced model files.
- ✅ DB legacy paths exist.
- ✅ Pin count equals package pin count.
- ✅ Power pins are present.
- ✅ Active-low pin names and `active_low` flags are consistent.
- ✅ Verilog module names exist in referenced model files.
- ✅ Export status agrees with known `Design.to_verilog()` mappings.

Exit criteria:

- ✅ `python3 -m chiplib.cli db --audit` or equivalent exists.
- ✅ Audit returns structured JSON and a nonzero exit code on hard failures.
- ✅ Audit checks DB status against `CHIP_STATUS.md`.

### Phase 3: DB-Backed Metadata

Status: complete.

Move read-only metadata consumers to the DB first.

Candidates:

- chip status reporting
- CLI `db` summary
- frontend pin metadata
- docs generation
- exporter capability report

Do not move behavior execution yet.

Exit criteria:

- ✅ `CHIP_STATUS.md` can be checked from DB data with
  `python3 -m chiplib.cli db --status`.
- ✅ DB loader can read layered IC packages, generic Virtual/Passive packages,
  and grouped `component.json` manifests for not-yet-migrated components.
- ✅ Seed grouped records exist for virtual, passive, and discrete schematic
  components.
- ✅ UI/API-facing chip metadata comes from DB manifests.

### Phase 4: DB-Backed Export Metadata

Status: complete.

Move Verilog export mappings out of the large shared mapping table and into
DB-owned package export metadata.

Target:

```text
DB/74xx/<part>/simulation/netlist.json
DB/Memory/<part>/simulation/netlist.json
  verilog.module
  verilog.file
  verilog.export
  portable_files
```

Rules:

- The generic exporter stays central.
- Chip-specific pin-to-port mapping becomes DB-owned.
- Unsupported chips report clear missing export metadata.

Exit criteria:

- Existing `Design.to_verilog()` tests pass.
- DB can explain why a chip is or is not exportable.
- Runtime export uses DB metadata only, with no legacy `VERILOG_MAPPINGS`
  fallback table.

Current proof point:

- ✅ All 62 active `verilog_export=tested` IC packages have DB-owned Verilog
  export metadata.
- ✅ `Design.to_verilog()` uses DB metadata through `chiplib.db.load_component`
  and has no legacy mapping-table fallback.
- ✅ `74HC147` has an explicit DB-owned `/I0` export contract and keeps the
  unbonded low output bit as an internal open placeholder.
- ✅ Memory exports can declare DB-owned input fallbacks such as unconnected
  `/WE` defaulting to `1'b1`.

### Phase 5: Optional DB-Backed Pinout Documentation

Status: deferred.

Move pinout docs from legacy Verilog comments into chip folders only after
references are DB-backed.

Example future move:

```text
Verilog/74xx/74hc245.v embedded comments -> DB/74xx/74HC245/pinout.md
```

Temporary compatibility options:

- Keep a legacy stub that points to the DB file.
- Add loader fallback for both old and new paths.

Exit criteria if chosen:

- Pinout readers use DB paths.
- Existing docs/tests still pass.
- Student catalog pages are clearer with per-component DB pinout files than
  with manifest-backed pin metadata plus linked implementation references.

### Phase 6: Package-Local IC Models

Status: complete for active IC packages.

Active IC packages now own package-local model files:

```text
DB/74xx/74HC245/simulation/model.py
DB/74xx/74HC245/simulation/model.v
DB/Memory/AT28C256/simulation/model.py
DB/Memory/AT28C256/simulation/model.v
```

The shared `Verilog/74xx/` and `Verilog/Memory/` trees remain useful for
family-level smoke coverage and comparison, but exported projects should use
the package-local `simulation/model.py` and copy `python/chiplib/core.py` once
as the shared runtime primitive layer. Legacy Python catalog helpers stay only
as loader/runtime compatibility, not as the source of active IC package facts.

Exit criteria:

- Verilog smoke tests pass for shared family models and package-local
  `simulation/model.v` files.
- Python behavior tests pass using package-local `simulation/model.py` files.
- Existing projects can still locate component models through DB metadata and
  `portable_files`.
- Student browsing sees one component package instead of needing to assemble
  facts from multiple legacy locations.

## Do Not Do Yet

- Do not split chip behavior into Rust/C/C++ until the DB and service
  contracts are stable.
- Do not make every backend piece a separate process.
- Do not delete `Verilog/74xx/`, `Verilog/Memory/`, or
  `python/chiplib/catalog.py` while smoke tests, legacy compatibility, or
  comparison checks still depend on them.
- Do not let exporters or UI parse raw chip files independently from DB
  metadata.

## Recommended Next Tasks

1. Reconcile stale docs so every entry point describes active IC packages as
   `definition/definition.json` plus package-local simulation, netlist, symbol,
   tests, and generated artifacts.
2. Make the student-facing catalog path obvious: status, missing properties,
   package readiness, and unsupported exports should be visible before a
   learner opens a raw definition file.
3. Expand generated Verilog bench emission beyond the first simple truth-table
   shape, especially for edge-sensitive, tri-state, bidirectional, and memory
   control-window parts.
4. Resolve remaining `datasheet-required` package evidence placeholders, then
   deepen timing/electrical extraction for the rest of the active IC catalog.
5. Leave the full visual chip-block editor until after generated docs, demos,
   and normalized import/export contracts are comfortable for student-facing
   use.
