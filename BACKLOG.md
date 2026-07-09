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
- ⬜ Implement block-UI model import/export against the same normalized design
  model, not a separate UI-only representation.

## Backend/API Hardening

- ✅ Create the first chip-centered `db/` slice with per-chip
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
  `schemas/normalized-netlist.schema.json` as the first plugin boundary.
- ✅ Add grouped DB seed manifests for virtual tools, passive parts, and
  discrete transistors.
- ✅ Move IC DB manifests into grouped folders: 74HC parts under `db/74xx/`
  and memory parts under `db/memory/`.
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
  chips. Coverage now includes `74HC00`, `74HC161`, bidirectional/high-Z
  `74HC245`, high-Z `74HC541`, latch/hold/high-Z `74HC574`, and SRAM
  write/read/high-Z `62256`.
- ✅ Tighten chip status checks so missing-datasheet exclusions such as
  `74HC150` and `74HC260` cannot also appear as verified, modeled, tested, or
  active legacy/DB parts.
- ✅ Add embedded pinout-comment vs DB-manifest pin consistency checks so
  physical pin labels cannot silently drift between Verilog comments and DB
  metadata.

## Deferred UI Work

- Build a visual chip-block editor where users can place DIP chip blocks on
  screen, wire pins/nets, and run either the Python simulator or Verilog
  simulation backend.

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
