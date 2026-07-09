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
DB/<group>/<part>/definition/digital.json
```

Split folders can still hold derived or detailed views:

```text
definition/
simulation/
tests/
symbol/
datasheet/
```

`chip.json` stays as the current compatibility manifest until the loader can
merge split component packages safely.

## Pim's Comments

- Keep `digital.json` as the canonical source for generators. Do not make
  generators scrape Verilog comments, Python classes, or Markdown.
- Keep datasheet evidence visible. If timing or electrical data is not
  extracted yet, mark it as missing or `datasheet-required`.
- Do not migrate all chips at once. Finish the seed batch, build tests and
  generators, then expand family by family.
- For students, the generated docs and demos matter as much as simulator
  correctness. The same definition should explain the chip and run it.
- The DB package must separate definition, simulation, schematic/symbol,
  verification, and generation. UI must consume these layers, not own them.

## Team Tasks

### 1. Arendt - Specification And Schema

Status: next.

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

- `python3 -B -m tests.test_db` validates every seed `digital.json`.
- Missing timing/electrical values are visible, not silently absent.

### 2. Feynman - Learning Docs And Interactive Demos

Status: next.

Owns:

- generated documentation shape
- interactive demo requirements
- student-facing wording

Tasks:

- Define generated Markdown sections from `digital.json`.
- Define a simple interactive demo contract for each seed chip.
- Keep language clear for ages `10-15`, while preserving correct pin names.
- Start with `74HC245` and `74HC161` examples.

Acceptance:

- Each seed part has enough metadata to generate a beginner-readable page.
- Demo definitions say which inputs can be toggled and which outputs/probes are
  shown.

### 3. Halley - Verification Matrix

Status: in progress.

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

### 4. Ohm - Electrical, Timing, And Datasheet Evidence

Status: next.

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

### 5. Leibniz - Generators And Loader Compatibility

Status: next.

Owns:

- generation code
- loader compatibility
- CLI/API output

Tasks:

- Add a loader that can read `definition/digital.json`.
- Keep `load_component(part)` backward-compatible with `chip.json`.
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

- The seed batch can be loaded through the current DB API.
- At least `74HC245` can produce generator-ready outputs from one file.

## Seed Batch Checklist

### 74HC161

- ✅ `definition/digital.json`
- ⬜ split test files
- ⬜ generated doc data
- ⬜ generated symbol data
- ⬜ timing/electrical evidence extraction

### 74HC157

- ✅ `definition/digital.json`
- ⬜ split test files
- ⬜ generated doc data
- ⬜ generated symbol data
- ⬜ timing/electrical evidence extraction

### 74HC245

- ✅ `definition/digital.json`
- ✅ initial split `definition/`, `simulation/`, `tests/`, `symbol/`,
  `datasheet/` package
- ⬜ generator prototype
- ⬜ generated KiCad symbol
- ⬜ generated SVG pinout
- ⬜ generated documentation
- ⬜ generated interactive demo

### 74HC574

- ✅ `definition/digital.json`
- ⬜ split test files
- ⬜ generated doc data
- ⬜ generated symbol data
- ⬜ timing/electrical evidence extraction

### AT28C256

- ✅ `definition/digital.json`
- ⬜ split test files
- ⬜ generated doc data
- ⬜ generated symbol data
- ⬜ timing/electrical evidence extraction

## GitHub Actions

Existing workflows already run on every push and pull request:

- `.github/workflows/python-tests.yml`
- `.github/workflows/verilog-smoke.yml`

Next CI tasks:

- Add `tests.test_block_ui` to the Python workflow.
- Add schema/package validation for seed `digital.json` files.
- Keep Verilog smoke compiling all 74xx and memory models.
- Keep memory smoke instantiating each memory module directly.
