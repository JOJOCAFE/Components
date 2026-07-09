# DB Migration Plan

Goal: make `db/` the chip identity layer for Components without breaking the
current simulator, Verilog models, exporter, tests, or existing projects.

The migration is gradual. Existing implementation files stay active until DB
loaders and tests prove the replacement path is equivalent.

## Target Shape

Each chip has one DB folder:

```text
db/
  74HC245/
    chip.json
    pinout.md          # later, after migration
    model.v            # later, after migration
    behavior.py        # optional later
    tests.json         # optional later
```

The first stable artifact is `chip.json`. It owns the chip's identity,
verified status, package, pins, source evidence, and references to active
legacy files.

## Current Transitional Shape

During migration, `chip.json` may point to legacy files:

```text
74HC/74hc245-pin.md
74HC/74hc245.v
Memory/at28c256-pin.md
Memory/at28c256.v
python/chiplib/chips.py
python/chiplib/catalog.py
python/chiplib/netlist.py
```

This keeps the current implementation working while the DB becomes complete.

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

## Phases

### Phase 1: DB Seed

Status: started.

- ✅ Add `db/chip.schema.json`.
- ✅ Add seed manifests for simple gates and memory.
- ✅ Add `chiplib.db` loader and CLI access.
- ✅ Report missing properties and missing referenced files.
- ✅ Expand representative seed coverage across gates, decoders, registers,
  counters, bus parts, SRAM, EEPROM, and flash.

Exit criteria:

- `python3 -B -m tests.test_db` validates all DB manifests.
- `python3 -m chiplib.cli db` lists the current DB.
- No DB manifest has hidden missing file references.

### Phase 2: DB Audit

Status: started.

Add audit tooling that compares DB state against the legacy catalog.

Required checks:

- ✅ DB parts vs `74HC/*.v` and `Memory/*.v`.
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

Move read-only metadata consumers to the DB first.

Candidates:

- chip status reporting
- CLI `db` summary
- frontend pin metadata
- docs generation
- exporter capability report

Do not move behavior execution yet.

Exit criteria:

- `CHIP_STATUS.md` can be generated or checked from DB data.
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

- ✅ `74HC00` has DB-owned Verilog export metadata.
- ✅ `Design.to_verilog()` uses DB metadata for `74HC00` and falls back to the
  legacy mapping table for the rest.
- ✅ `74HC147` has DB-owned blocked export status explaining that the current
  Verilog module cannot represent the source-supported `/I0` input.

### Phase 5: DB-Backed Pinout Files

Move pinout docs from legacy folders into chip folders only after references
are DB-backed.

Example future move:

```text
74HC/74hc245-pin.md -> db/74HC245/pinout.md
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
74HC/74hc245.v -> db/74HC245/model.v
Memory/at28c256.v -> db/AT28C256/model.v
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
- Do not delete `74HC/`, `Memory/`, or `python/chiplib/catalog.py` while any
  loader still depends on them.
- Do not let exporters or UI parse raw chip files independently from DB
  metadata.

## Recommended Next Tasks

1. Add `db --audit`.
2. Add more representative DB manifests.
3. Add a DB-vs-legacy coverage test.
4. Generate or check `CHIP_STATUS.md` from DB data.
5. Move Verilog export metadata for one simple chip to prove the pattern.
