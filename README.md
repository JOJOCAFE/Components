# Shared Component Library

[![Python tests](https://github.com/JOJOCAFE/Components/actions/workflows/python-tests.yml/badge.svg)](https://github.com/JOJOCAFE/Components/actions/workflows/python-tests.yml)
[![Verilog smoke](https://github.com/JOJOCAFE/Components/actions/workflows/verilog-smoke.yml/badge.svg)](https://github.com/JOJOCAFE/Components/actions/workflows/verilog-smoke.yml)

Reusable component models, DIP pinout notes, and datasheet evidence for RV8, RV8GR, and future `/home/jo/kiro` hardware projects.

This folder is shared project infrastructure. Keep reusable chip models here instead of copying them into one CPU project unless a project needs a frozen local snapshot.

## Layout

- `verilog/74xx/` - behavioral Verilog models for 74HC-family logic chips, with each `74hcxx.v` embedding its pinout notes as comments.
- `verilog/memory/` - behavioral Verilog models for EEPROM, flash EEPROM, and SRAM parts, with each `.v` embedding its pinout notes as comments.
- `lib/standard/` - component DB manifests and schema where chips, virtual tools,
  passives, and discrete parts own status, pins, sources, behavior/export
  references, and visible missing properties.
- `examples/circuits/` - service-ready schematic JSON fixtures for CLI/API contracts
  and regression tests.
- `python/` - reusable Python pin-level behavior models, net wiring, tri-state conflict checks, and propagation-delay simulation.
- `schemas/` - machine-readable schemas for exported interchange artifacts,
  including the normalized netlist contract.
- `source/` - manufacturer datasheet PDFs used as local evidence for pinout documentation; see `source/README.md` for the retained evidence list.
- `docs/` - compact documentation index, guides, contracts, status, reports,
  task plans, team skills, and handoff notes.
- `board/` - lightweight local Components workbench: visual Drawing on the
  left, readable Component text upper-right, and bounded Terminal lower-right.
  It is served by the existing local Python API and owns no separate circuit
  model.
- `AGENTS.md` - local JOJOCAFE team ownership map for Components work.

## Verification Rule

Pinout documentation is for physical wiring, so it must be verified from a manufacturer datasheet, not memory or generic web summaries. For DIP builds, the cited source must explicitly support a DIP, PDIP, P-DIP, or equivalent through-hole plastic package for that part.

If a part has no verified DIP/PDIP source, do not keep physical pinout
documentation or a catalog model for it. Add the part only after
manufacturer-backed package and pin evidence is available.

## Chip Package Rule

Active ICs under `lib/standard/74xx/` and `lib/standard/memory/` are standalone packages. The
canonical source is:

```text
lib/standard/<group>/<part>/definition/definition.json
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

The student authoring goal has two compatible views: the legacy normalized
Design/block-UI workflow and the text-first Component Board in `board/`.
The Component Board keeps readable `.component` text as source of topology;
Drawing and Terminal actions request checked source patches or bounded runtime
operations through Python. Neither view is allowed to invent chip behavior,
pins, wires, or simulator state. The same backend remains callable by CLI,
direct Python, API/AI clients, and the local Board.

Primary users are students from roughly primary to secondary school age
(`10-15` years old), with the same tools still usable by older learners up to
about `25`. Keep examples, labels, errors, and UI/API affordances clear enough
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

Run the generated Verilog behavior cross-check whenever a Python model,
Verilog model, netlist export, or truth-table vector changes:

```bash
python3 tools/verilog_behavior_crosscheck.py
```

This compiles package-local `simulation/model.v` files with Icarus and checks
the DB truth vectors against the Verilog behavior. It complements the hand
smoke benches and Python-vs-Verilog representative tests.

Parts without manufacturer-verified DIP evidence are intentionally absent from
the active 74HC/HCT catalog until source evidence is added.

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
python3 -B -m tests.test_block_ui
python3 -B -m tests.test_netlist
python3 -B -m tests.test_cli
python3 -B -m tests.test_api
python3 -B -m tests.test_component_board_api
python3 -B -m tests.test_db
python3 -B -m tests.test_generated_split_records
python3 -B -m tests.test_contracts
python3 -B -m tests.test_simulation_service
python3 -B -m tests.test_equivalence
cd ..

iverilog -g2012 -Wall -o /tmp/tb_74xx_smoke.vvp verilog/74xx/*.v verilog/74xx/tests/tb_74xx_smoke.v
vvp /tmp/tb_74xx_smoke.vvp

iverilog -g2012 -Wall -o /tmp/tb_memory_smoke.vvp verilog/memory/*.v verilog/memory/tests/tb_memory_smoke.v
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
PYTHONPATH=python python3 tools/state_behavior_crosscheck.py
```

## Student CLI/API Start

For the shortest learner-facing path, start with `docs/STUDENT_GUIDE.md`. It shows:

- how to inspect the student component catalog
- how to run `examples/circuits/nand.json`
- how to use `circuit-faults` for RV8GR virtual physical-system checks
- how to call the local stdio or HTTP API

The important boundary is unchanged: virtual checks can catch wiring, bus,
edge, and timing-risk mistakes, but they do not replace physical voltage,
frequency, or oscilloscope evidence.

For students around ages 10-15, use this build-along order:

1. Read `docs/STUDENT_GUIDE.md`.
2. Run `examples/circuits/nand.json` with `validate`, `run`, and `probe`.
3. Use `lib/standard/STUDENT_CATALOG.md` to look up chips before wiring.
4. Use one `examples/circuits/RV8GR_*/README.md` proof card at a time with a teacher
   or mentor.
5. Use the protocol docs only when measuring the real build.

Use `docs/README.md` for the current student/teacher/reference map across the
docs.

## First Component Board

The first local Board is intentionally small and dependency-free. It opens the
NOT-gate Component in a three-pane workspace, keeps a browser-local draft,
and sends every resolve/run/edit request to the existing Python service.

```sh
PYTHONPATH=python python3 -B -m chiplib.api --http --host 127.0.0.1 --port 8765
```

Open <http://127.0.0.1:8765/>. If that port is busy, choose another (for
example `8766`) and open the matching address. See
[`board/README.md`](board/README.md) for the available safe Terminal commands
and focused tests. A passing digital result is still not breadboard wiring,
electrical-safety, or speed signoff.

## Documentation

Start with `docs/README.md`. It groups the moved documentation by audience:
students, teachers, tool builders, maintainers, verification reports, and
handoff/team process.
