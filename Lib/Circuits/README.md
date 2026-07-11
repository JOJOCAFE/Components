# Circuit Library

This folder breaks reusable RV8GR subcircuits out of the full CPU so each block
can be documented, simulated, and proven on its own.

Use the RV8GR `doc/build_plan/` stages and `doc/labs/` files as extraction
helpers. The build plan gives module order and stop conditions; the labs give
student-facing wiring checks. The circuit packages still record electrical
truth when lab wording is simplified.

For students around ages 10-15, treat each `RV8GR_*` README as a proof card,
not as a complete standalone lesson. A teacher or mentor should pair it with
the matching RV8GR lab/build step, point to the real chips and pins, and check
the pass state before the next module is connected.

Student stop conditions:

- a chip gets hot or supply current is unexpected
- a virtual check reports a bus conflict
- a clocked part changes on the wrong edge
- a shared bus has no clear owner
- a fast-clock test is attempted before manual-clock behavior is clean

## Circuit Runner

The reusable functional runner is public through the
`python3 -m chiplib.cli circuit-validate`, `circuit-run`, `circuit-step`, and
`circuit-probe` commands. The local JSON API also provides `circuit-load` and
matching functional commands. Support is package-dependent: unsupported
ranges, parts, composition, or other runtime features must produce a structured
blocked result rather than a pass.

This is not a blanket promotion of the circuit library. Broader direct package
execution is staged, and `timed-run` is not currently a public command.
Package-level modeled timing remains staged or blocked until the requested
constraints are executed and proven. No simulated result is physical evidence.

- [`CIRCUIT_RUNNER_ARCHITECTURE.md`](../../Docs/CIRCUIT_RUNNER_ARCHITECTURE.md)
  - net, timing, execution, and future interface architecture.
- [`CIRCUIT_RUNNER_STUDENT_CONTRACT.md`](../../Docs/CIRCUIT_RUNNER_STUDENT_CONTRACT.md)
  - current functional commands, staged commands, results, and error language.
- [`CIRCUIT_RUNNER_TASK_PLAN.md`](CIRCUIT_RUNNER_TASK_PLAN.md) - staged
  implementation checklist and current status.
- [`CIRCUIT_RUNNER_VERIFICATION_PLAN.md`](CIRCUIT_RUNNER_VERIFICATION_PLAN.md)
  - package batches, negative tests, CI lanes, and promotion gates.

## RV8GR Circuit Test Campaign Reports

The generated campaign has two matching views in this directory:

- [`RV8GR_CIRCUIT_TEST_CAMPAIGN.md`](RV8GR_CIRCUIT_TEST_CAMPAIGN.md): the
  beginner-readable summary.
- [`RV8GR_CIRCUIT_TEST_CAMPAIGN.json`](RV8GR_CIRCUIT_TEST_CAMPAIGN.json): the
  machine-readable evidence and status data behind that summary.

Report presence is not a blanket pass. Read each result together with the
coverage index and executable package tests below.

Read each campaign result as a stack of separate checks:

- **Logical pass:** the expected inputs produce the expected outputs or state.
  This checks the circuit idea, not every chip model or real wire.
- **Part-model smoke/direct model:** smoke means the package can exercise its
  available DB chip models without a basic failure; direct means a test checks
  the model's behavior itself. A smoke pass is useful but weaker than a direct
  behavior test.
- **Composed/static checks:** composed checks run connected circuit behavior;
  static checks inspect wiring, package shape, vectors, or equations without
  proving that every connected chip changed state correctly.
- **Modeled timing:** delays and setup/hold rules pass using values represented
  by the simulator. This is a virtual timing result, not a measured board speed.
- **Physical measurement required:** the remaining proof needs the built board,
  installed chip markings, and instruments such as a meter or oscilloscope.
  No virtual pass can replace this step.

## RV8GR Coverage Status

Coverage is layered. `C` means an executable Python test directly covers that
layer, `-` means not covered, and `P/NM` means physical work is planned but no
board measurement exists. Structural or vector coverage never implies a live
component-model, composed-system, or physical pass. Evidence references are in
`RV8GR_COVERAGE_INDEX.json`; every physical row points to
`physical_capture_plan.json`.

| Circuit | Structural | Vector/equation | Live model | Composed/system | Physical |
|---|---:|---:|---:|---:|---:|
| `RV8GR_RingCounter` | C | C | C | - | P/NM |
| `RV8GR_PC16` | C | C | C | - | P/NM |
| `RV8GR_AddressMux16` | C | C | C | - | P/NM |
| `RV8GR_BusOwnership` | C | C | - | - | P/NM |
| `RV8GR_InstructionLatch` | C | C | C | - | P/NM |
| `RV8GR_StorePath` | C | C | - | - | P/NM |
| `RV8GR_DataPageMemory` | C | C | C | - | P/NM |
| `RV8GR_IRQLatch` | C | C | C | - | P/NM |
| `RV8GR_RomDbusRead` | C | C | C | - | P/NM |
| `RV8GR_AluAccumulator` | C | C | C | - | P/NM |
| `RV8GR_PageDataRegisters` | C | C | C | - | P/NM |
| `RV8GR_BranchJumpControl` | C | C | - | - | P/NM |
| `RV8GR_VirtualTestHelpers` | C | C | - | - | P/NM |
| `RV8GR_FullControlOpcodeSweep` | C | C | - | - | P/NM |
| `RV8GR_ResetClockBringup` | C | C | - | - | P/NM |
| `RV8GR_FetchCycleTrace` | C | C | - | C | P/NM |
| `RV8GR_StoreLoadBranchTrace` | C | C | - | C | P/NM |
| `RV8GR_PageJumpTrace` | C | C | - | C | P/NM |
| `RV8GR_InterruptTrace` | C | C | - | C | P/NM |
| `RV8GR_BootSequenceTrace` | C | C | - | C | P/NM |
| `RV8GR_Lab13MarkerTrace` | C | C | - | C | P/NM |
| `RV8GR_WholeSystemChipLevelVirtual` | C | C | - | C | P/NM |

Each circuit package should include:

- `circuit.json`: chips, ports, wiring, timing contract, and source links.
- `tests/*.json`: proof vectors or timing/bus checks.
- `README.md`: student-readable explanation and debug checklist.
- Python tests under `python/tests/` that fail loudly when the proof breaks.
- `timing_margins.json`: shared RV8GR timing-margin data for propagation
  paths, 50 kHz/1/2/5 MHz periods, setup/hold notes, bus-race risks, and the
  current functional-only 5 MHz boundary.
- `BACKLOG.md`: short list of next trace/circuit packages and proof gaps.
- `RV8GR_COVERAGE_INDEX.json`: machine-readable index tying README rows to
  package folders, proof vectors, and Python regression coverage.
- `RV8GR_END_TO_END_TEST_PLAN.md`: campaign tracker from package proofs to
  whole-system Verilog and physical build signoff.

## Next Tests From RV8GR Debug Plan

1. `RV8GR_ClockProfiles`: keep push-switch, random debounced push, 50 kHz,
   1 MHz, 2 MHz, and 5 MHz profiles on every edge-sensitive circuit. Mark
   5 MHz as functional simulation until timing-margin and hardware
   signal-integrity proof exist.
2. `RV8GR_TimingMargins`: keep `timing_margins.json` consumed by tests so
   model-delay slack, setup/hold requirements, source-backed physical
   assumptions, and bus-race notes stay visible without promoting 5 MHz to
   physically proven.
3. `RV8GR_PhysicalEvidence`: add selected memory speed grade, output-disable
   timing, clock-phase deadband, and measured wiring/signal-integrity evidence
   before any hardware-speed claim.
