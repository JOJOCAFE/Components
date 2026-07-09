# Components Backlog

Future work for the shared component library.

## Schematic JSON Script

- ✅ Define the complete readable JSON schematic script shape for digital logic
  and CPU simulation projects in `SCHEMATIC_JSON_SPEC.md`.
- ✅ Record the core UI goal: JSON and visual block UI must round-trip 1-to-1,
  including probes/displays, so students can edit either side.
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
- ⬜ Continue full-catalog Verilog export mappings for remaining muxes,
  decoders, counters, transceivers, ALU/control parts, and memory chips.
- ⬜ Implement block-UI model import/export against the same normalized design
  model, not a separate UI-only representation.

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
