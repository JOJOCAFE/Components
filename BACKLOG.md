# Components Backlog

Future work for the shared component library.

## Schematic JSON Script

- ✅ Define the complete readable JSON schematic script shape for digital logic
  and CPU simulation projects in `SCHEMATIC_JSON_SPEC.md`.
- ✅ Record the core UI goal: JSON and visual block UI must round-trip 1-to-1,
  including probes/displays, so students can edit either side.
- ✅ Record the primary learner audience: students around `10-15` years old,
  with the same tools still usable by older learners up to about `24`.
- ✅ Record backend-first architecture in `PYTHON_BACKEND_ARCHITECTURE.md`: UI,
  JSON, netlist, and Verilog should talk through one Python design model.
- ✅ Record CLI/backend contract: UI, CLI, and direct Python scripts must all
  call the same Python `Design` API using the same JSON schematic file.
- ✅ Implement first-pass parser/normalizer from schematic JSON into Python
  `Design` and simulator `Board`.
- ✅ Implement a scriptable Python `Design` API that UI actions can call
  directly, Blender/Maya style.
- ✅ Implement initial `chiplib.cli` commands for validate, snapshot, run,
  probe, export-json, export-netlist, and first-pass export-verilog.
- ✅ Implement normalized netlist export/import from `Design`.
- ✅ Implement first-pass Verilog/testbench export from `Design` using explicit
  pin-number-to-port maps for supported 74HC parts.
- ✅ Expand Verilog export mappings beyond the initial simple gate whitelist
  for the first common batch: `74HC02`, `74HC08`, `74HC10`, `74HC14`,
  `74HC20`, `74HC30`, `74HC138`, `74HC139`, `74HC244`, `74HC273`,
  `74HC374`, and `74HC377`.
- ✅ Expand Verilog export mappings for the second common batch: `74HC07`,
  `74HC11`, `74HC27`, `74HC42`, `74HC73`, `74HC85`, `74HC154`,
  `74HC155`, `74HC158`, `74HC160`, `74HC162`, `74HC163`, `74HC238`,
  `74HC266`, and `74HC352`.
- ✅ Expand Verilog export mappings for specialized parts and memory bridges:
  `74HC148`, `74HC181`, `74HC593`, `74HC922`, `AS6C62256`, `CY7C199`, and
  `SST39SF010A`.
- ✅ Review and repair the `74HC147` pinout/model export contract; structural
  Verilog export now exposes `/I0` and preserves the unbonded low output bit
  with an internal open placeholder.
- ✅ Add GitHub Actions for Python tests and Verilog smoke tests, plus README
  badges for both workflows.
- ✅ Split chip status into verified, modeled, tested, and missing-datasheet
  categories in `CHIP_STATUS.md`.
- ✅ Implement block-UI model import/export against the same normalized design
  model, not a separate UI-only representation.

## Backend/API Hardening

- ✅ Create the first chip-centered `DB/` slice with per-chip
  manifests for easy test parts: `74HC00`, `74HC04`, and `62256`.
- ✅ Expand the DB seed set with representative sequential, bus, and EEPROM
  parts: `74HC161`, `74HC245`, and `AT28C256`.
- ✅ Expand DB coverage with flip-flop, register, decoder, and flash examples:
  `74HC74`, `74HC574`, `74HC138`, and `SST39SF010A`.
- ✅ Add `DB_MIGRATION_PLAN.md` to define the phased transition from scattered
  legacy chip files to DB-owned chip identity and metadata.
- ✅ Add `python3 -m chiplib.cli db --audit` for DB manifest checks and
  DB-vs-legacy coverage reporting.
- ✅ Add DB-vs-legacy coverage tests for current DB manifests, legacy Verilog
  models, and legacy pinout files.
- ✅ Expand DB manifests to full active legacy model/pinout catalog coverage:
  62 DB parts for 62 legacy model parts.
- ✅ Add `python3 -m chiplib.cli db --status` to compare DB-derived status
  categories against `CHIP_STATUS.md`.
- ✅ Prove DB-backed Verilog export metadata with `74HC00` while preserving
  existing structural Verilog output.
- ✅ Review `74HC147` export gap and repair the model/export contract so the
  verified `/I0` input is represented in structural Verilog.
- ✅ Add `SERVICE_CONTRACT.md` for stable CLI/API service contracts before the
  repo grows too large.
- ✅ Freeze the normalized netlist schema in
  `Schemas/normalized-netlist.schema.json` as the first plugin boundary.
- ✅ Add grouped DB entries for Virtual, Passive, and Discrete components.
  Virtual and Passive now use layered `definition/definition.json` packages;
  Discrete remains compact `component.json`.
- ✅ Move IC DB manifests into grouped folders: 74HC parts under `DB/74xx/`
  and memory parts under `DB/Memory/`.
- ✅ Add DB-backed adapters so schematic JSON can instantiate virtual sources,
  rails, probes, passive parts, and discrete parts without forcing those
  representation-only components through chip behavior factories.
- ✅ Follow `SERVICE_ARCHITECTURE_TASKS.md` to split chip behavior, simulation,
  CLI, and future API/UI adapters behind the stable internal service
  contracts. Verilog export, simulation, and CLI now have initial internal
  service boundaries, with future external-engine and API/UI contracts
  documented.
- ✅ Finish production-ready CLI commands around the existing `Design` backend:
  `validate`, `snapshot`, `run`, `probe`, `export-json`, `export-netlist`, and
  `export-verilog`.
- ✅ Add canonical JSON contract tests using service-ready example schematics:
  load schematic JSON, validate, snapshot, run, export netlist, and export
  Verilog when supported.
- ✅ Build a full simulation runner from JSON that applies clocks, inputs,
  probes, expectations, and memory images, then returns structured results.
- ✅ Stabilize the Python API boundary for frontends: create/delete chips,
  connect/disconnect endpoints, add buses, set inputs, step clocks, read
  probes, validate, snapshot, and export.
- ✅ Add DB-backed UI/API metadata accessors so frontends can read component
  group, kind, role, status, pins, package, UI hints, simulation service, and
  export capability without scanning implementation folders.
- ✅ Define the frontend snapshot contract for UI/API clients, including chip
  layout, pin states, net values, bus values, warnings/errors, probe history,
  and display state.
- ✅ Repair the `74HC147` Verilog model/export contract so the model exposes
  all source-supported inputs, including `/I0`.
- ✅ Add example JSON circuits as runnable demos and regressions: NAND gate,
  counter, bus transceiver, ROM/RAM read, tiny CPU slice, and other small
  teaching circuits.
- ✅ Add stronger Python-vs-Verilog equivalence tests for selected chips and
  circuits, especially memories, counters, tri-state bus parts, and ALU-like
  chips. Coverage now includes `74HC00`, mux/disable `74HC157`, count
  sequence `74HC161`, bidirectional/high-Z `74HC245`, high-Z `74HC541`,
  latch/hold/high-Z `74HC574`, SRAM write/read/high-Z `62256`, and EEPROM
  write/read/high-Z `AT28C256`.
- ✅ Tighten chip status checks so missing-datasheet exclusions such as
  `74HC150` and `74HC260` cannot also appear as verified, modeled, tested, or
  active legacy/DB parts.
- ✅ Add embedded pinout-comment vs DB-manifest pin consistency checks so
  physical pin labels cannot silently drift between Verilog comments and DB
  metadata.
- ✅ Finish DB-backed Verilog export migration: all 62 active
  `verilog_export=tested` IC parts now own structural export metadata in
  package `simulation/netlist.json` files, and runtime export no longer uses a
  legacy mapping table.

## Deferred UI Work

Priority order before visual UI:

1. ✅ Add student-facing DB catalog views and examples for component status,
   missing properties, pins, and export/simulation capability.
2. ✅ Move active ICs from manifest-only metadata into standalone DB packages
   with `definition/definition.json`, package-local simulation files, split
   test records, symbol metadata, and generated artifacts.
3. ✅ Keep shared family Verilog folders for smoke coverage and comparison,
   while package-local `simulation/model.py` and `simulation/model.v` are the
   active per-chip package files.
4. ✅ Build block-UI import/export against the normalized `Design` model and DB
   component catalog.
5. Build a visual chip-block editor where users can place DIP chip blocks on
   screen, wire pins/nets, and run either the Python simulator or Verilog
   simulation backend.

## RV8GR Circuit Library Proof Plan

Goal: break RV8GR subcircuits out into `Lib/Circuits/` as reusable standalone
circuits with machine-readable wiring, proof vectors, student docs, and Python
tests backed by DB component models.

Done:

- ✅ `RV8GR_RingCounter`: U8 `74HC164` plus U24 `74HC04` feedback. Tests cover
  reset, T0/T1/T2 sequence, no-edge hold, lower-state recovery, component-model
  execution, push-switch, random debounced push, 50 kHz, 1 MHz, 2 MHz, and 5 MHz
  functional profiles.
- ✅ `RV8GR_PC16`: U1-U4 `74HC161` program counter. Tests cover async reset,
  rising-edge count, no-edge hold, `PC_INC`, `/PC_LD`, RCO carry chain,
  load-priority-over-count, component-model execution, push-switch, random
  debounced push, 50 kHz, 1 MHz, 2 MHz, and 5 MHz functional profiles.

Next team tasks:

1. **Bank + Bam: `RV8GR_AddressMux16`**
   - Build from U15-U20/U29/U30 `74HC157`.
   - Prove `/ADDR_MODE=1` selects PC for fetch and `/ADDR_MODE=0` selects
     `{DP,IRL}` for data access.
   - Include the lab warning that real RV8GR uses `ADDR_REQ=SRC OR STR`, not
     raw `T2`.
2. **Fern + Mint: `RV8GR_BusOwnership`**
   - Prove the phase table from `06_debug_plan.md`: T0/T1 use U7
     DBUS-to-IBUS, T2 immediate uses U34, T2 store uses U14 plus U7 write
     direction.
   - This is the main bus-race/bus-fight proof.
3. **Mint + Fern: `RV8GR_InstructionLatch`**
   - Build from U5/U6 `74HC574`.
   - Prove U5 captures only on T0, U6 captures only on T1, and both hold
     through T2.
4. **Ohm + Fern: `RV8GR_StorePath`**
   - Prove `STR=1` at T2 makes U7 enabled, `WR_DIR=1`, ROM `/OE=HIGH`, and RAM
     `/WE=LOW` only when selected.
   - Include current-draw/bus-fight notes for physical debug.
5. **Bam + Ohm + Fern: `RV8GR_DataPageMemory`**
   - Prove SETDP, RAM write/readback, ROM read via DP, `$7FFF/$8000` boundary,
     and ROM/RAM chip-select exclusivity.
6. **Mint + Fern: Clock profiles**
   - Keep push-switch, random debounced push up to 500 ms for 100 ticks,
     50 kHz, 1 MHz, 2 MHz, and 5 MHz profiles on every circuit.
   - Mark 5 MHz as functional simulation until timing-margin and hardware
     signal-integrity proof exist.
7. **Noon + Fern: `RV8GR_IRQLatch`**
   - Prove `/IRQ` low-then-release latches IRQ_FF, reset clears it, and v1.0
     does not force PC or auto-vector.

Pim coordinates this plan and keeps `Lib/Circuits/README.md`, `BACKLOG.md`,
tests, and pushed commits aligned.

## Component Generation Pipeline

- ✅ Define the direction that one canonical component definition file can
  generate or drive JSON component detail, Python simulator adapters, Verilog
  wrappers, KiCad symbols, SVG pinouts, documentation, unit tests, and
  interactive demos.
- ✅ Start the seed batch with generator-ready `definition/definition.json` files
  for `74HC161`, `74HC157`, `74HC245`, `74HC574`, and `AT28C256`.
- ✅ Add layered packages for all active ICs with
  `definition/definition.json`, `simulation/`, `tests/`, `symbol/`, and
  `generated/` layers.
- ✅ Add schemas and DB validation tests for the new `db.component.digital`
  package files.
- ✅ Add a loader that can read `definition/definition.json` while preserving
  legacy `chip.json` compatibility.
- ✅ Prototype generation from one file for `74HC245`: normalized JSON,
  Python simulator report, Verilog wrapper/export metadata, KiCad symbol,
  SVG pinout, documentation data, unit test vectors, and interactive demo data.
- ✅ Expand split test files for the seed batch: truth table, timing,
  tri-state, bus-fight, and propagation where applicable.
- ✅ Add GitHub Actions coverage for package/schema validation once the schemas
  land.

## Backend Bus, Probe, And Test Logic

- ✅ Add bus/tag wiring before probe logic: schematics can place any number of
  `Bus` objects, and each bus groups named net tags up to 128 lines, such as
  `bus:b1[0]` through `bus:b1[127]`.
- ✅ Any number of chip pins can plug into the same tag to share a connection;
  one physical pin is guarded against being silently attached to multiple tags.
- ✅ Add pull-up and pull-down defaults for nets, bus tags, or individual chip
  pins so schematics can define normal states with weak VCC/ground behavior.
- ✅ Add first-class power rails and manual logic sources for visible
  schematic/UI drivers.
- ✅ Add `Board.snapshot()` and structured `Board.errors()` so UI/API display
  can read board state without scraping simulator internals.
- ✅ Add any number of named stimulus input sets, each with up to 64 channels.
- ✅ Add reusable probe sets for simulator tests and future UI inspection.
- ✅ Any number of probe sets can attach up to 64 channels each to chip pins,
  named nets, or bus tags, sample logic values over simulated time, and expose
  serializable state for web or Python frontends.
- ✅ Assertion/test helpers can check expected `0`, `1`, `Z`, `X`,
  rising/falling transitions, pulse counts, and stable timing windows against
  the Python simulator.
- Keep probe logic backend-only and independent from the future visual editor.

Notes:

- This is intentionally deferred.
- Current priority remains the backend component library: Python chip behavior,
  pin-number/name access, propagation delay, memory models, and Python/Verilog
  compatibility.
- The UI should consume the backend library instead of duplicating chip
  behavior.
- The backend must stay frontend-agnostic. It should be usable from a JavaScript
  web UI through an API/service wrapper, or directly from a Python-native UI,
  without changing chip behavior code.
- Future UI work should treat the backend as a simulator service: create chips,
  expose pin metadata, create buses, attach pins to tags, step/settle clocks,
  probe pins/nets/bus tags, and return serializable state for drawing.
