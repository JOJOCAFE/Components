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
