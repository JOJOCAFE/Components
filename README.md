# Shared Component Library

[![Python tests](https://github.com/JOJOCAFE/Components/actions/workflows/python-tests.yml/badge.svg)](https://github.com/JOJOCAFE/Components/actions/workflows/python-tests.yml)
[![Verilog smoke](https://github.com/JOJOCAFE/Components/actions/workflows/verilog-smoke.yml/badge.svg)](https://github.com/JOJOCAFE/Components/actions/workflows/verilog-smoke.yml)

Reusable component models, DIP pinout notes, and datasheet evidence for RV8, RV8GR, and future `/home/jo/kiro` hardware projects.

This folder is shared project infrastructure. Keep reusable chip models here instead of copying them into one CPU project unless a project needs a frozen local snapshot.

## Layout

- `Verilog/74xx/` - behavioral Verilog models for 74HC-family logic chips, with each `74hcxx.v` embedding its pinout notes as comments.
- `Verilog/Memory/` - behavioral Verilog models for EEPROM, flash EEPROM, and SRAM parts, with each `.v` embedding its pinout notes as comments.
- `DB/` - component DB manifests and schema where chips, virtual tools,
  passives, and discrete parts own status, pins, sources, behavior/export
  references, and visible missing properties.
- `Examples/` - service-ready schematic JSON fixtures for CLI/API contracts
  and regression tests.
- `python/` - reusable Python pin-level behavior models, net wiring, tri-state conflict checks, and propagation-delay simulation.
- `Schemas/` - machine-readable schemas for exported interchange artifacts,
  including the normalized netlist contract.
- `Source/` - manufacturer datasheet PDFs used as local evidence for pinout documentation; see `Source/README.md` for the retained evidence list.
- `STUDENT_GUIDE.md` - beginner-first guide for using Components from the CLI
  and local API before the visual editor exists.
- `SCHEMATIC_JSON_SPEC.md` - readable JSON schematic script contract for
  digital simulation, CPU labs, netlist export, Verilog/testbench generation,
  and future UI display.
- `SERVICE_CONTRACT.md` - CLI/API service contract for validation, snapshots,
  simulation runs, probes, exporters, and DB audit/status responses.
- `BLOCK_UI_CONTRACT.md` - drawable block import/export contract that
  round-trips through the same normalized `Design` model as schematic JSON.
- `PYTHON_BACKEND_ARCHITECTURE.md` - backend-first architecture where JSON,
  UI blocks, CLI commands, Python scripts, netlists, and Verilog all talk
  through one Python design model.
- `CHIP_STATUS.md` - chip status split by datasheet verification, models,
  test coverage, netlist export support, and missing-datasheet exclusions.
- `SERVICE_ARCHITECTURE_TASKS.md` - task plan for splitting behavior,
  simulation, exporters, CLI, and future API/UI work behind stable internal
  service contracts.
- `EXTERNAL_ENGINE_ADAPTER_PLAN.md` - contract plan for future Rust, C, or C++
  simulation engines that plug into the same normalized JSON service boundary.
- `FRONTEND_SNAPSHOT_CONTRACT.md` - UI/API snapshot shape for drawing chips,
  nets, buses, probes, displays, errors, and warnings without scraping backend
  internals.
- `DB_MIGRATION_PLAN.md` - historical migration plan for making `DB/` the chip
  identity layer; active ICs now use layered DB packages under the frozen
  `v0.1` chip model.
- `DB_COMPONENT_PACKAGE_SPEC.md` - layered component package structure for
  definition, simulation, verification, and symbol data, with datasheet
  evidence embedded in the definition file.
- `GENERATION_PIPELINE.md` - one-file `definition/definition.json` flow for
  generating JSON, simulator adapters, Verilog wrappers, KiCad symbols, SVG
  pinouts, docs, unit tests, and interactive demos.
- `COMPONENT_GENERATION_BACKLOG.md` - package generation backlog covering seed,
  RV8GR Batch 2, and active catalog package status.
- `AGENTS.md` - local JOJOCAFE team ownership map for Components work.
- `TEAM_SKILLS.md` - individual and shared skills for DB, Python, Verilog,
  simulation, verification, and student-facing documentation.

## Verification Rule

Pinout documentation is for physical wiring, so it must be verified from a manufacturer datasheet, not memory or generic web summaries. For DIP builds, the cited source must explicitly support a DIP, PDIP, P-DIP, or equivalent through-hole plastic package for that part.

If a part has no verified DIP/PDIP source, do not keep physical pinout
documentation or a catalog model for it. Add the part only after
manufacturer-backed package and pin evidence is available.

## Chip Package Rule

Active ICs under `DB/74xx/` and `DB/Memory/` are standalone packages. The
canonical source is:

```text
DB/<group>/<part>/definition/definition.json
```

That file owns chip identity, package, pins, logic, timing, generation targets,
verification requirements, datasheet evidence, and embedded definition layers.
The old IC-level `chip.json` files are no longer required; compatibility data
is synthesized from `definition/definition.json` and `simulation/netlist.json`.

Each IC package carries the layers needed to travel as a standalone chip:

```text
definition/definition.json
simulation/model.py
simulation/model.v
simulation/model.json
simulation/netlist.json
tests/truth_table.json
tests/timing.json
tests/tri_state.json
tests/bus_fight.json
tests/propagation.json
symbol/dip.json
generated/artifacts.json
```

Project, circuit, and system exports must copy the chip-local
`simulation/model.py` with the chip. Python exports must also copy
`python/chiplib/core.py`; one shared copy is enough for a multi-chip exported
project.

## Test Record Rule

Every active IC truth-table record must declare `edge_criteria`. Clocked chips
state rising/falling trigger behavior and prove non-trigger-edge or no-edge
hold behavior. Level-sensitive logic states `trigger_edge: none`. Memory parts
state their write/read control window and high-Z behavior.

Seed chips and RV8GR-used chips must not use `basic_function` or intent-only
truth vectors. They need concrete per-chip `inputs` and `expect` records.
Important required checks include:

- async control priority for clocked chips
- enable/hold behavior around clock edges
- tri-state/high-Z behavior
- executable bus-fight/no-conflict cases for bus-driving chips
- memory write protection: `/CE=1` and `/WE=1` prevent writes
- propagation/timing metadata matching definition records
- Python-vs-Verilog equivalence coverage when Verilog exists

## System Cross-Check Rule

Use `python/` as the first-line behavioral cross-check for TTL CPU systems. The
Python models are pin-number/pin-name addressable, support net wiring and
tri-state conflict checks, and carry propagation-delay metadata for timing
analysis.

The long-term simulator goal is a student-friendly block UI whose design state
round-trips 1-to-1 with `SCHEMATIC_JSON_SPEC.md`: JSON can become editable
blocks, and blocks can become the same logical JSON, including probes and
display blocks. The UI should behave like Blender or Maya: a front-end that
calls Python backend commands and renders the returned design/simulation state.
The same backend must also be callable by CLI and by direct Python scripts, all
using the same JSON schematic file.

Primary users are students from roughly primary to secondary school age
(`10-15` years old), with the same tools still usable by older learners up to
about `24`. Keep examples, labels, errors, and UI/API affordances clear enough
for beginners while preserving real pin-level behavior and datasheet accuracy.

Use the Verilog files when a project needs HDL-level comparison, FPGA-oriented
tests, or a second independent implementation. Do not prefer Verilog over the
Python simulator for RV8/RV8GR system behavior checks unless the task is
specifically about Verilog or RTL equivalence.

## Python/Verilog Compatibility Rule

The Python models are the physical behavior contract. For every chip implemented
in Python, the model must use the real DIP pin numbers and names from the
manufacturer-backed pinout file and must model the real control behavior:
active-low enables, tri-state outputs, bidirectional pins, asynchronous clears,
and memory read/write controls.

The Verilog models must match that Python behavior for every overlapping part.
Verilog modules may expose HDL-friendly vector ports instead of individual DIP
pins, but their logic, direction controls, high-Z behavior, and write/read
semantics must stay compatible with the Python model.

`Design.to_netlist()` exports the normalized bridge format used by CLI, future
block UI work, and HDL generation. `Design.to_verilog()` lowers that netlist to
structural Verilog only for parts with explicit pin-number-to-port mappings; it
reports unsupported parts instead of guessing from names.
`Design.from_kicad_netlist()` can import KiCad generic netlists for compatibility
smoke tests against existing projects such as RV8GR-V2.
`Design.to_block_ui()` and `Design.from_block_ui()` bridge a future visual
chip-block editor to the same schematic JSON contract. The block-UI format only
adds drawable blocks, wires, and layout metadata; chip identity, pins, probes,
tests, and behavior still come from `Design` and the DB catalog.

Parts without manufacturer-verified DIP evidence, such as the previously
provisional `74HC150` and `74HC260`, are intentionally absent from the active
catalog.

## Naming

- Chip model files use lowercase part names, for example `Verilog/74xx/74hc245.v`.
- 74HC Verilog modules use `ttl_74hcxx` names.
- Memory Verilog modules use `mem_<part>` names.
- Pinout files use `<part>-pin.md`, one file per chip.

## Tests

Run from the Components repo root:

```sh
cd python
python3 -B -m tests.test_chips
python3 -B -m tests.test_design
python3 -B -m tests.test_block_ui
python3 -B -m tests.test_netlist
python3 -B -m tests.test_cli
python3 -B -m tests.test_api
python3 -B -m tests.test_db
python3 -B -m tests.test_generated_split_records
python3 -B -m tests.test_contracts
python3 -B -m tests.test_simulation_service
python3 -B -m tests.test_equivalence
cd ..

iverilog -g2012 -Wall -o /tmp/tb_74xx_smoke.vvp Verilog/74xx/*.v Verilog/74xx/tests/tb_74xx_smoke.v
vvp /tmp/tb_74xx_smoke.vvp

iverilog -g2012 -Wall -o /tmp/tb_memory_smoke.vvp Verilog/Memory/*.v Verilog/Memory/tests/tb_memory_smoke.v
vvp /tmp/tb_memory_smoke.vvp
```

Expected pass markers:

- `Components Python chip tests passed`
- `Components Python design tests passed`
- `Components block UI tests passed`
- `Components Python netlist tests passed`
- `Components Python CLI tests passed`
- `Components API tests passed`
- `Components DB tests passed`
- `Components generated split-record tests passed`
- `Components contract tests passed`
- `Components simulation service tests passed`
- `Components equivalence tests passed`
- `74xx SMOKE TEST PASSED`
- `MEMORY SMOKE TEST PASSED`

DB audit:

```sh
cd python
python3 -m chiplib.cli db --audit
python3 -m chiplib.cli db --status
cd ..
```

## Student CLI/API Start

For the shortest learner-facing path, start with `STUDENT_GUIDE.md`. It shows:

- how to inspect the student component catalog
- how to run `Examples/nand.json`
- how to use `circuit-faults` for RV8GR virtual physical-system checks
- how to call the local stdio or HTTP API

The important boundary is unchanged: virtual checks can catch wiring, bus,
edge, and timing-risk mistakes, but they do not replace physical voltage,
frequency, or oscilloscope evidence.

## Subfolder Docs

- `STUDENT_GUIDE.md` - student-first CLI/API guide with safe virtual-vs-hardware
  boundaries.
- `Verilog/74xx/README.md` - full 74xx logic model list, scan notes, and 74xx source coverage.
- `Verilog/Memory/README.md` - memory model list and datasheet sources.
- `DB/README.md` - chip-centered DB package layout and migration notes.
- `python/README.md` - Python chip-library coverage and usage.
- `Examples/*.json` - service-ready NAND, counter, bus transceiver, memory
  read, and tiny CPU-slice schematics used by contract tests.
- `CHIP_STATUS.md` - verified/modeled/tested/missing-datasheet status split
  for the active chip library.
- `SCHEMATIC_JSON_SPEC.md` - complete JSON schematic-script shape for digital
  and CPU simulation projects.
- `Schemas/normalized-netlist.schema.json` - JSON Schema for
  `Design.to_netlist()` exports consumed by CLI, UI, and HDL tooling.
- `SERVICE_CONTRACT.md` - shared CLI/API request, response, error, versioning,
  and pluggable-service rules.
- `DB_COMPONENT_PACKAGE_SPEC.md` and `GENERATION_PIPELINE.md` - current DB
  package layer where one `definition/definition.json` drives generated JSON,
  simulator adapters, Verilog wrappers, KiCad symbols, SVG pinouts,
  documentation, unit tests, and interactive demos.
- `BLOCK_UI_CONTRACT.md` - block editor import/export shape for drawable
  chips, buses, rails, wires, and layout metadata over the normalized `Design`
  model.
- `PYTHON_BACKEND_ARCHITECTURE.md` - Python command/API model for the future
  block UI, CLI tool, Python script use, netlist exporter, and Verilog/testbench
  exporter.
- `SERVICE_ARCHITECTURE_TASKS.md` - service-boundary task plan for keeping the
  component library modular before it grows too large.
- `DB_MIGRATION_PLAN.md` - DB migration plan for moving chip facts under
  per-chip ownership without breaking existing tools.
- `BACKLOG.md` - deferred future work, including the visual chip-block UI idea.
- `AGENTS.md` - compact team directory and ownership map for this repo.
- `TEAM_SKILLS.md` - detailed team skill map and Components quality gates.
