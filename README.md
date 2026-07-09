# Shared Component Library

[![Python tests](https://github.com/JOJOCAFE/Components/actions/workflows/python-tests.yml/badge.svg)](https://github.com/JOJOCAFE/Components/actions/workflows/python-tests.yml)
[![Verilog smoke](https://github.com/JOJOCAFE/Components/actions/workflows/verilog-smoke.yml/badge.svg)](https://github.com/JOJOCAFE/Components/actions/workflows/verilog-smoke.yml)

Reusable component models, DIP pinout notes, and datasheet evidence for RV8, RV8GR, and future `/home/jo/kiro` hardware projects.

This folder is shared project infrastructure. Keep reusable chip models here instead of copying them into one CPU project unless a project needs a frozen local snapshot.

## Layout

- `verilog/74xx/` - behavioral Verilog models for 74HC-family logic chips, with each `74hcxx.v` embedding its pinout notes as comments.
- `verilog/Memory/` - behavioral Verilog models for EEPROM, flash EEPROM, and SRAM parts, with each `.v` embedding its pinout notes as comments.
- `db/` - component DB manifests and schema where chips, virtual tools,
  passives, and discrete parts own status, pins, sources, behavior/export
  references, and visible missing properties.
- `examples/` - service-ready schematic JSON fixtures for CLI/API contracts
  and regression tests.
- `python/` - reusable Python pin-level behavior models, net wiring, tri-state conflict checks, and propagation-delay simulation.
- `schemas/` - machine-readable schemas for exported interchange artifacts,
  including the normalized netlist contract.
- `source/` - manufacturer datasheet PDFs used as local evidence for pinout documentation; see `source/README.md` for the retained evidence list.
- `SCHEMATIC_JSON_SPEC.md` - readable JSON schematic script contract for
  digital simulation, CPU labs, netlist export, Verilog/testbench generation,
  and future UI display.
- `SERVICE_CONTRACT.md` - CLI/API service contract for validation, snapshots,
  simulation runs, probes, exporters, and DB audit/status responses.
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
- `DB_MIGRATION_PLAN.md` - phased plan for making `db/` the chip identity
  layer while legacy model files with embedded pinout comments remain active
  during migration.
- `AGENTS.md` - local JOJOCAFE team ownership map for Components work.
- `TEAM_SKILLS.md` - individual and shared skills for DB, Python, Verilog,
  simulation, verification, and student-facing documentation.

## Verification Rule

Pinout documentation is for physical wiring, so it must be verified from a manufacturer datasheet, not memory or generic web summaries. For DIP builds, the cited source must explicitly support a DIP, PDIP, P-DIP, or equivalent through-hole plastic package for that part.

If a part has no verified DIP/PDIP source, do not keep physical pinout
documentation or a catalog model for it. Add the part only after
manufacturer-backed package and pin evidence is available.

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

Parts without manufacturer-verified DIP evidence, such as the previously
provisional `74HC150` and `74HC260`, are intentionally absent from the active
catalog.

## Naming

- Chip model files use lowercase part names, for example `verilog/74xx/74hc245.v`.
- 74HC Verilog modules use `ttl_74hcxx` names.
- Memory Verilog modules use `mem_<part>` names.
- Pinout files use `<part>-pin.md`, one file per chip.

## Tests

Run from the Components repo root:

```sh
cd python
python3 -B -m tests.test_chips
python3 -B -m tests.test_design
python3 -B -m tests.test_netlist
python3 -B -m tests.test_cli
python3 -B -m tests.test_api
python3 -B -m tests.test_db
python3 -B -m tests.test_contracts
python3 -B -m tests.test_simulation_service
python3 -B -m tests.test_equivalence
cd ..

iverilog -g2012 -Wall -o /tmp/tb_74xx_smoke.vvp verilog/74xx/*.v verilog/74xx/tests/tb_74xx_smoke.v
vvp /tmp/tb_74xx_smoke.vvp

iverilog -g2012 -Wall -o /tmp/tb_memory_smoke.vvp verilog/Memory/*.v verilog/Memory/tests/tb_memory_smoke.v
vvp /tmp/tb_memory_smoke.vvp
```

Expected pass markers:

- `Components Python chip tests passed`
- `Components Python design tests passed`
- `Components Python netlist tests passed`
- `Components Python CLI tests passed`
- `Components API tests passed`
- `Components DB tests passed`
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

## Subfolder Docs

- `verilog/74xx/README.md` - full 74xx logic model list, scan notes, and 74xx source coverage.
- `verilog/Memory/README.md` - memory model list and datasheet sources.
- `db/README.md` - chip-centered DB migration notes and manifest
  layout.
- `python/README.md` - Python chip-library coverage and usage.
- `examples/*.json` - service-ready NAND, counter, bus transceiver, memory
  read, and tiny CPU-slice schematics used by contract tests.
- `CHIP_STATUS.md` - verified/modeled/tested/missing-datasheet status split
  for the active chip library.
- `SCHEMATIC_JSON_SPEC.md` - complete JSON schematic-script shape for digital
  and CPU simulation projects.
- `schemas/normalized-netlist.schema.json` - JSON Schema for
  `Design.to_netlist()` exports consumed by CLI, UI, and HDL tooling.
- `SERVICE_CONTRACT.md` - shared CLI/API request, response, error, versioning,
  and pluggable-service rules.
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
