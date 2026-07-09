# Components Team Skills

This file records the active skill map for the Components repo. It is the local
team contract for chip DB work, Python behavior, Verilog models/export,
simulation services, and student-facing documentation.

## Shared Team Skills

- Student-first engineering for ages 10-15, with enough accuracy and depth for
  learners up to about 24.
- Manufacturer-backed DIP/PDIP evidence discipline for physical pinout claims.
- Chip-centered DB design: one component identity, visible missing properties,
  grouped families, and stable references to behavior/export files.
- Python/Verilog equivalence discipline: real pin behavior, active-low controls,
  tri-state buses, bidirectional memory pins, delays, and reset/clock behavior.
- CLI/API service thinking: every frontend should call stable backend services
  instead of duplicating component behavior.
- Regression habit: every DB migration, exporter move, model repair, or status
  change needs focused tests plus smoke coverage.
- Beginner-readable failure messages and examples: errors must point to the
  chip, pin, net, source, or missing property that the learner can fix.
- Layered component generation: one canonical `definition/definition.json` should
  drive normalized JSON, Python simulator adapters, Verilog wrappers/export,
  KiCad symbols, SVG pinouts, documentation, unit tests, and interactive demos.
- Package separation discipline: definition, simulation, schematic/symbol,
  verification, generation, datasheet evidence, and project use must stay as
  separate layers even when one file can generate outputs.
- One-file definition discipline: component/package/pins/power/logic/timing/
  electrical definition sublayers live inside `definition/definition.json` as
  `definition_layers`; datasheet sources live inside the same file as
  `datasheet.sources`; split definition and datasheet files are compatibility
  fallback only.
- Standalone package discipline: chip-local `simulation/model.py`,
  `simulation/model.v`, `simulation/model.json`, `simulation/netlist.json`,
  `symbol/dip.json`, `tests/*.json`, and `generated/artifacts.json` travel
  with the chip folder; exported projects copy shared `python/chiplib/core.py`
  once as the runtime primitive layer.
- Verification-record discipline: active IC truth records must declare
  `edge_criteria`; clocked chips prove active-edge behavior and no-edge hold,
  tri-state/bus chips prove high-Z and bus-fight/no-conflict behavior, and
  memory chips prove write protection plus read/write control windows.
- Circuit-library proof discipline: RV8GR-derived circuits in `Lib/Circuits/`
  must include machine-readable wiring, proof vectors, Python tests, and
  student docs. Clocked circuits must prove reset, active-edge advance,
  no-edge hold, load/count priority when relevant, and recovery from invalid or
  lower states. Bus circuits must prove one active driver per phase, high-Z
  release, and no ROM/RAM/IBUS/DBUS contention.
- Clock-profile discipline: every reusable RV8GR circuit proof should keep the
  push-switch profile, random debounced push profile up to 500 ms for 100
  ticks, and 50 kHz, 1 MHz, 2 MHz, and 5 MHz functional profiles. The 5 MHz
  result is functional simulation until hardware signal-integrity and timing
  margin evidence are added.

## Active Specialist Agents

These are the current Codex specialist agents used for Components delegation.
They complement the original JOJOCAFE role names below.

| Agent | Main skills | Current Components ownership |
|---|---|---|
| Arendt | Specification, schema discipline, task framing, consistency checks | Owns component package specs, `definition.json` schema design, required/optional field rules, and missing-data representation. |
| Feynman | Teaching, explanation, demo design, student-facing simplification | Owns generated docs, interactive demos, beginner-readable examples, and age 10-15 clarity. |
| Halley | Verification, audit coverage, test matrix design | Owns truth table, timing, tri-state, bus-fight, propagation, equivalence, and CI verification planning. |
| Ohm | Hardware truth, datasheets, pin/package/electrical evidence | Owns package evidence, pin truth, timing/electrical extraction, active-low naming, and breadboard realism. |
| Leibniz | Tooling, loaders, generators, API/CLI integration | Owns definition-backed loaders, generator prototypes, legacy `chip.json` compatibility, and CLI/API generation commands. |

Shared specialist rule:

- No generated artifact is authoritative by itself. The source is
  `definition/definition.json` plus datasheet evidence; generated Python,
  Verilog, KiCad, SVG, docs, tests, and demos must be reproducible from that
  layer.

Current seed-batch milestone:

- `74HC161`, `74HC157`, `74HC245`, `74HC574`, and `AT28C256` now have
  generator-ready `definition/definition.json`, local `simulation/model.py`,
  `simulation/model.v`, `simulation/netlist.json`, `simulation/model.json`,
  `symbol/dip.json`, split test records, generated artifact reports, and first
  timing/electrical extraction records.
- Active IC `chip.json` files are removed; `load_component(part)` synthesizes
  compatibility data from `definition/definition.json` and
  `simulation/netlist.json`.
- Project/system exports must use package `portable_files` and copy the local
  `simulation/model.py` with each chip so standalone projects do not link back
  to the DB package folder for behavior.
- Whenever `simulation/model.py` is copied, `python/chiplib/core.py` must be
  copied too as the runtime primitive layer.
- For circuit/system exports, copy `chiplib/core.py` once and share it across
  all local chip models in that exported project.
- `load_digital_package(part)` and `generate_component_artifacts(part)` are the
  current loader/generator entry points. Definition sublayers are read from
  `definition_layers` first; `load_component(part)` remains the compatibility
  manifest path.
- `python/tests/test_chips.py` now executes selected split test records against
  live Python chip models; broader generated Python/Verilog test generation is
  the next verification step.
- `python/tests/test_generated_split_records.py` is the current generated-check
  harness for seed records and Verilog smoke workflow scope.
- Next seed-chip hardening targets are full counter/load/RCO behavior for
  `74HC161`, select and enable propagation for `74HC157`, repeated DIR and
  `/OE` bus-conflict coverage for `74HC245`, capture/hold/output-disable
  coverage for `74HC574`, and write-cycle/read-after-write/protection coverage
  for `AT28C256`.

Current RV8GR circuit-library milestone:

- `RV8GR_RingCounter` is the seed circuit proof for U8 `74HC164` plus U24
  `74HC04` feedback. It proves reset, T0/T1/T2 sequence, no-edge hold,
  lower-state recovery, component-model execution, push-switch operation,
  random debounced pushes, and 50 kHz through 5 MHz functional profiles.
- `RV8GR_PC16` is the seed counter-chain proof for U1-U4 `74HC161`. It proves
  async reset, rising-edge count, no-edge hold, `PC_INC`, `/PC_LD`, RCO carry,
  load priority, component-model execution, push-switch operation, random
  debounced pushes, and 50 kHz through 5 MHz functional profiles.
- `RV8GR_AddressMux16` proves PC vs `{DP,IRL}` address selection,
  `ADDR_REQ=SRC OR STR` gating, no raw-`T2` data-address selection, A15
  ROM/RAM decode, and live `74HC157` component-model execution.
- `RV8GR_BusOwnership` proves T0/T1 fetch, T2 immediate, T2 memory load, T2
  store, memory output disable during store, ROM/RAM select exclusivity, and
  forced unsafe bus-fight detection.
- `RV8GR_InstructionLatch` proves U5 T0 capture, U6 T1 capture, T2 hold,
  direct-control bit labels, and live `74HC574` component-model execution.
- `RV8GR_StorePath` proves no-store holdoff, T2 store controls, RAM write,
  ROM output disable, RAM output disable, and ROM-page store bus safety.
- `RV8GR_DataPageMemory` proves SETDP decode, U32 load behavior,
  `$7FFF/$8000` boundary selection, RAM write/readback, ROM read via DP, and
  ROM/RAM select exclusivity.
- `RV8GR_IRQLatch` proves reset clear, EI rising-edge IE set, `/IRQ` release
  latching, sticky IRQ_FF, DI inert behavior, no PC change, no v1.0 vector,
  and live `74HC74` component-model execution.
- `RV8GR_RomDbusRead` proves ROM bytes crossing DBUS to IBUS through live
  `AT28C256` and `74HC245` models, A15 ROM disable, U7 disable, write-direction
  ROM output disable, and forced ROM-vs-U7 DBUS contention detection.
- `RV8GR_PageDataRegisters` proves U23 positive-edge SETPG capture,
  T2-start hold while `PG_CLK` is LOW, `{PG,IRL}` jump targets, SETPG/SETDP
  separation, invalid overlap visibility, live `74HC574` execution, and clock
  profiles.
- `RV8GR_BranchJumpControl` proves `/PC_LD` phase gating, JMP, BEQ, BNE,
  no-load hold cases, JMP+BR overlap, and the Verilog opcode-sweep equation
  for all 256 opcodes with both Z states.
- `RV8GR_AluAccumulator` proves LI/ADDI/SUBI/XORI datapath equations,
  accumulator edge capture, no-capture hold cases, U14 store-buffer high-Z and
  drive behavior, U22 zero compare, Z toggle behavior, live `74HC283` and
  `74HC574` execution, model-delay propagation checks, and opcode-sweep ALU
  samples.
- `74HC688` pin truth is corrected in Components: pin 19 is `Y` output and
  pins 11-18 are A4/B4 through A7/B7. RV8GR U22 wiring/docs need a follow-up
  audit in the RV8GR repo.
- Extra clock-profile tests now cover `RV8GR_InstructionLatch`,
  `RV8GR_DataPageMemory`, `RV8GR_IRQLatch`, `RV8GR_PageDataRegisters`, and
  `RV8GR_BranchJumpControl`, and `RV8GR_AluAccumulator` with push-switch,
  random debounced push up to 500 ms for 100 ticks, 50 kHz, 1 MHz, 2 MHz, and
  5 MHz functional profiles.
- Virtual helper policy: use virtual clock sources, phase probes, bus monitors,
  or contention detectors when they make tests clearer, but do not replace real
  chip behavior with virtual behavior when the DB has a real model.
- Next circuit/test lane must follow the same quality level:
  `RV8GR_FullControlOpcodeSweep` and virtual test helpers.

## Pim - Coordinator

Core skills:

- Turn broad requests into numbered tasks the user can choose from.
- Route work to Bank, Fern, Mint, Ohm, Bam, and Noon by risk area.
- Keep `BACKLOG.md`, `DB_MIGRATION_PLAN.md`, and status docs aligned with the
  real repo state.
- Watch for cross-file drift between DB manifests, Python models, Verilog
  models, exporter mappings, CLI/API contracts, and docs.
- Surface concerns directly when a task risks confusing students or hiding
  technical debt.

Components focus:

- Treat the DB as the product center.
- Keep the next task list short, concrete, and executable.
- Make sure completed work ends with tests, task docs, and a push when asked.
- Preserve the active specialist assignments in this file and route new work
  through `COMPONENT_GENERATION_BACKLOG.md`.
- For RV8GR circuit work, route the build order from `BACKLOG.md`, keep
  `Lib/Circuits/README.md`, circuit READMEs, tests, and pushed commits aligned,
  and make sure timing, synchronous edge, and bus-race concerns stay visible.

## Bank - Architect

Core skills:

- Define repo structure before implementation grows too large.
- Decide when a behavior belongs in DB metadata, Python code, Verilog code, or
  a future service boundary.
- Review grouped component layout for 74xx, memory, virtual, passive, and
  discrete components.
- Protect stable contracts: schematic JSON, normalized netlist, DB schema,
  service responses, and exporter behavior.
- Separate baseline beginner paths from optional advanced engines or features.

Components focus:

- Approves DB migration phases and service architecture.
- Challenges duplication or hidden coupling between DB, Python, and Verilog.
- Keeps C/C++/Rust plugin ideas behind stable adapter contracts until the
  Python/DB path is proven.
- Owns the long-term architecture of the definition/simulation/schematic/
  verification/generation layer split.
- Owns the boundary between DB component packages and reusable circuit-library
  packages so circuits prove behavior without becoming hidden chip-model forks.
- Defines RV8GR circuit decomposition order and confirms address, bus, memory,
  and control subcircuits are reusable outside the full CPU context.

## Fern - Verifier

Core skills:

- Find status contradictions, missing test coverage, and undocumented behavior
  changes.
- Build focused regression tests for DB audit/status, netlist export, CLI/API
  contracts, and Python-vs-Verilog behavior.
- Review edge cases: active-low names, high-Z states, bus conflicts,
  bidirectional pins, memory write/read timing, and clocked parts.
- Require shell-failing tests, not just printed pass messages.
- File defects with evidence and an owner.

Components focus:

- Owns the final confidence pass before push.
- Treats `python3 -m chiplib.cli db --audit` and `db --status` as quality gates.
- Expands equivalence tests before more exporter metadata is migrated.
- Turns `tests/*.json` component package files into executable regression
  checks.
- Requires every active IC truth-table test to state edge criteria explicitly:
  rising, falling, level/no-edge, or control-window behavior.
- Owns RV8GR circuit proof completeness: edge-trigger checks, no-edge hold,
  random push-switch clocks, functional frequency profiles, bus-driver
  exclusivity, memory write/read windows, and failure cases for unsafe control
  combinations.
- Reviews every `Lib/Circuits/` proof before it is treated as evidence for the
  full RV8GR timing, synchronous, or bus-race concerns.

## Mint - RTL Coder

Core skills:

- Write and repair readable Verilog models for 74xx and memory parts.
- Keep HDL modules behavior-compatible with Python chip models even when ports
  are HDL-friendly vectors rather than DIP pins.
- Maintain structural export contracts and smoke benches.
- Model tri-state outputs, bidirectional DQ buses, active-low controls, and
  clock/reset behavior clearly.
- Avoid clever HDL that students cannot inspect.

Components focus:

- Owns `Verilog/74xx/`, `Verilog/Memory/`, and Verilog smoke tests.
- Reviews DB-owned `verilog.export` mappings for correct port direction and
  pin order.
- Adds focused benches when a chip becomes export-supported.
- Helps ensure Verilog wrappers can be generated from `definition/definition.json`
  without losing readable HDL.
- Owns clocked-circuit proof benches for RV8GR subcircuits, especially
  ring-counter, instruction-latch, program-counter, and any later Verilog
  wrappers for circuit-level export.
- Keeps circuit timing assumptions explicit: functional simulator profiles are
  not the same as propagation-delay or hardware margin proof.

## Ohm - HW Coder

Core skills:

- Verify real DIP/PDIP pinouts from manufacturer datasheets.
- Keep embedded Verilog pinout comments and DB manifest pins in sync.
- Catch physical wiring mistakes: swapped pins, missing power pins, misleading
  active-low labels, and package evidence gaps.
- Translate chip data into wiring-real descriptions a student can use on a
  breadboard.
- Reject provisional chips that lack source-backed physical evidence.

Components focus:

- Owns pinout truth for DB manifests and model comments.
- Treats missing-datasheet chips as explicit exclusions, not partial parts.
- Helps Noon convert physical facts into beginner-safe labels.
- Owns package evidence, electrical placeholders, and extracted timing values
  inside `definition/definition.json`.
- Owns breadboard realism for RV8GR circuits: DIP pin references, power and
  decoupling notes, active-low labels, bus-fight/current-risk debug clues, and
  physical warnings for push-switch clocking and MHz clock wiring.
- Checks that extracted RV8GR circuits still match the real chip packages and
  wiring paths used by the CPU, not just the simplified simulator nets.

## Bam - SW Coder

Core skills:

- Implement Python chip behavior, board simulation, schematic JSON handling,
  CLI commands, and API-ready services.
- Keep tools scriptable from CLI, tests, and future frontends.
- Make errors structured and useful: chip id, part, pin, net, service, and
  suggested fix when possible.
- Preserve one backend design model for JSON, UI, netlist, simulation, and
  Verilog export.
- Add abstractions only when they reduce real duplication or stabilize a
  service boundary.

Components focus:

- Owns `python/chiplib/`, tests, schema-facing code, and service adapters.
- Moves exporter metadata into DB only when equivalence and netlist tests prove
  the behavior.
- Keeps frontend-facing responses serializable and stable.
- Owns loader compatibility for legacy `chip.json` while active IC packages are
  definition-backed.
- Owns `Lib/Circuits/` Python execution paths, reusable test helpers, generated
  clock profiles, random push-switch tests, and component-model integration for
  RV8GR circuit proofs.
- Keeps circuit proof data serializable so later CLI/API/UI tools can load and
  explain the same circuit behavior without duplicating simulation logic.

## Noon - Docs Writer

Core skills:

- Explain real electronics accurately for young learners.
- Turn DB/status/service changes into docs that answer "what can I use, what is
  missing, and how do I test it?"
- Keep examples small, inspectable, and connected to visible circuit behavior.
- Flag wording that hides risk, such as "supported" when only a partial model
  exists.
- Convert expert terms into labels and notes that preserve the real signal
  names.

Components focus:

- Owns README clarity, student labels, example descriptions, and future labs.
- Keeps the primary customer visible in planning docs.
- Works with Ohm and Bam so UI/API metadata is both physically true and easy to
  display.
- Owns generated documentation and interactive demo wording from
  `definition/definition.json`.
- Owns RV8GR circuit READMEs and lab wording: explain the circuit purpose,
  signals, expected tick-by-tick behavior, and what each proof means for
  students without overselling functional simulation as hardware timing proof.
- Keeps debug-plan and lab notes connected to student-facing circuit examples,
  especially for clock push switches, memory boundaries, and bus ownership.

## Natural Pairings

- Bank + Ohm: architecture and physical truth.
- Mint + Fern: HDL speed and verification rigor.
- Bam + Noon: usable tools and student understanding.
- Bank + Bam: reusable circuit boundary and executable circuit model.
- Fern + Ohm: bus-race, timing-risk, and physical debug evidence.
- Mint + Bam: circuit-level proof benches shared by Python and future HDL.
- Pim + everyone: routing, task order, and delivery discipline.

## Current Quality Gates

Run these before claiming broad Components health:

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
python3 -B -m tests.test_lib_circuits
python3 -m py_compile chiplib/*.py tests/*.py
python3 -m chiplib.cli db --audit
python3 -m chiplib.cli db --status
cd ..

iverilog -g2012 -Wall -o /tmp/tb_74xx_smoke.vvp Verilog/74xx/*.v Verilog/74xx/tests/tb_74xx_smoke.v
vvp /tmp/tb_74xx_smoke.vvp

iverilog -g2012 -Wall -o /tmp/tb_memory_smoke.vvp Verilog/Memory/*.v Verilog/Memory/tests/tb_memory_smoke.v
vvp /tmp/tb_memory_smoke.vvp
```
