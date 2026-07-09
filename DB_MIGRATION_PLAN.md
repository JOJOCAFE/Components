# DB Migration Plan

Goal: make `db/` the chip identity layer for Components without breaking the
current simulator, Verilog models, exporter, tests, or existing projects.

The migration is gradual. Existing implementation files stay active until DB
loaders and tests prove the replacement path is equivalent.

## Target Shape

The DB is becoming a grouped component catalog. Existing flat chip folders stay
active during migration, while new component classes can already live in group
folders:

```text
db/
  74xx/
    74HC245/
      chip.json
  memory/
    AT28C256/
      chip.json
  virtual/
    InputSource/
      component.json
    Probe/
      component.json
  passive/
    LED/
      component.json
    Resistor/
      component.json
  discrete/
    NPN/
      component.json
```

Future IC folders may own implementation files directly:

```text
db/
  74xx/74HC245/
    chip.json
    pinout.md          # later, after migration
    model.v            # later, after migration
    behavior.py        # optional later
    tests.json         # optional later
```

The first stable artifact is the manifest: `chip.json` for ICs and
`component.json` for grouped virtual/passive/discrete components. It owns the
component identity, group, kind, role, package/pins, source evidence, status,
and references to active legacy files when any exist.

## Current Transitional Shape

During migration, `chip.json` may point to legacy files:

```text
verilog/74xx/74hc245-pin.md
verilog/74xx/74hc245.v
verilog/Memory/at28c256-pin.md
verilog/Memory/at28c256.v
python/chiplib/chips.py
python/chiplib/catalog.py
python/chiplib/netlist.py
```

This keeps the current implementation working while the DB becomes complete.
New grouped component manifests may live under:

```text
db/virtual/<component>/component.json
db/passive/<component>/component.json
db/discrete/<component>/component.json
```

## Migration Rules

1. Add DB entries before moving files.
2. Every DB entry must pass `db/chip.schema.json`.
3. Missing chip properties are allowed only when visible in `status`,
   `missing_properties`, or `missing_files`.
4. Exporters and simulators should consume DB metadata through `chiplib.db`,
   not by scanning old folders directly.
5. A physical file move is allowed only after tests prove the old and new
   lookup paths produce the same behavior.
6. Do not delete legacy files until all current tests and at least one existing
   project smoke test still pass.
7. Keep manufacturer-backed DIP/PDIP evidence mandatory for physical pinout
   status.
8. Grouped virtual/passive/discrete manifests are allowed before behavior is
   executable, but they must declare `group`, `kind`, `role`, `pins`, `status`,
   and their intended `simulation.service`.
9. Do not move existing flat IC DB folders into `db/74xx/` or `db/memory/`
   until the grouped lookup path has contract tests and no downstream code
   assumes `db/<part>/chip.json`.

## Phases

### Phase 1: DB Seed

Status: complete.

- ✅ Add `db/chip.schema.json`.
- ✅ Add seed manifests for simple gates and memory.
- ✅ Add `chiplib.db` loader and CLI access.
- ✅ Report missing properties and missing referenced files.
- ✅ Expand representative seed coverage across gates, decoders, registers,
  counters, bus parts, SRAM, EEPROM, and flash.

Exit criteria:

- ✅ `python3 -B -m tests.test_db` validates all DB manifests.
- ✅ `python3 -m chiplib.cli db` lists the current DB.
- ✅ No DB manifest has hidden missing file references.

### Phase 2: DB Audit

Status: complete.

Add audit tooling that compares DB state against the legacy catalog.

Required checks:

- ✅ DB parts vs `verilog/74xx/*.v` and `verilog/Memory/*.v`.
- ✅ DB parts vs `*-pin.md` files.
- ✅ DB part status vs `CHIP_STATUS.md`.
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

Status: started.

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
- ✅ DB loader can read both flat IC manifests and grouped
  `component.json` manifests.
- ✅ Seed grouped manifests exist for virtual, passive, and discrete schematic
  components.
- UI/API-facing chip metadata comes from DB manifests.

### Phase 4: DB-Backed Export Metadata

Status: started.

Move Verilog export mappings out of the large shared mapping table and into
DB-owned export metadata.

Target:

```text
db/<part>/chip.json
  verilog:
    module
    file
    export:
      kind
      ports
      output_pins
      parameters
```

Rules:

- The generic exporter stays central.
- Chip-specific pin-to-port mapping becomes DB-owned.
- Unsupported chips report clear missing export metadata.

Exit criteria:

- Existing `Design.to_verilog()` tests pass.
- DB can explain why a chip is or is not exportable.

Current proof point:

- ✅ `74HC00`, `74HC04`, `74HC161`, `74HC245`, and `74HC147` have DB-owned
  Verilog export metadata.
- ✅ `Design.to_verilog()` uses DB metadata when present and falls back to the
  legacy mapping table for the rest.
- ✅ `74HC147` has an explicit DB-owned `/I0` export contract and keeps the
  unbonded low output bit as an internal open placeholder.

### Phase 5: DB-Backed Pinout Files

Move pinout docs from legacy folders into chip folders only after references
are DB-backed.

Example future move:

```text
verilog/74xx/74hc245-pin.md -> db/74HC245/pinout.md
```

Temporary compatibility options:

- Keep a legacy stub that points to the DB file.
- Add loader fallback for both old and new paths.

Exit criteria:

- Pinout readers use DB paths.
- Existing docs/tests still pass.

### Phase 6: Optional DB-Owned Models

Only after metadata and export paths are stable, consider moving model files:

```text
verilog/74xx/74hc245.v -> db/74HC245/model.v
verilog/Memory/at28c256.v -> db/AT28C256/model.v
```

This is optional. It may be better to keep implementation models in family
folders and let DB manifests own references. The decision should be based on
which layout stays easiest for simulation, HDL tools, and student browsing.

Exit criteria:

- Verilog smoke tests pass.
- Python behavior tests pass.
- Existing projects can still locate component models.

## Do Not Do Yet

- Do not split chip behavior into Rust/C/C++ until the DB and service
  contracts are stable.
- Do not make every backend piece a separate process.
- Do not delete `verilog/74xx/`, `verilog/Memory/`, or `python/chiplib/catalog.py` while any
  loader still depends on them.
- Do not let exporters or UI parse raw chip files independently from DB
  metadata.

## Recommended Next Tasks

1. Finish DB-backed UI/API metadata accessors so frontends can read component
   group, kind, role, status, pins, package, evidence, UI hints, simulation
   service, and export capability without scanning implementation folders.
2. Continue Phase 4 by moving more safe `Design.to_verilog()` pin-to-port
   mappings into `db/<part>/chip.json` export metadata.
3. Add a generated/check mode for `CHIP_STATUS.md` so documentation drift is
   caught in tests or CI instead of only through manual review.
4. Add virtual/passive/discrete behavior adapters so schematic JSON can
   instantiate DB-backed InputSource, Probe, LED, Resistor, Capacitor, and
   transistor components.
5. Start Phase 5 with one low-risk pinout migration proof, keeping a legacy
   compatibility path until tests prove DB pinout loading is stable.
6. Defer DB-owned model moves until service interfaces and contract tests are
   in place.
