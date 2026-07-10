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

## RV8GR Circuit Candidates

| Circuit | RV8GR source | Status | Proof focus |
|---|---|---|---|
| `RV8GR_RingCounter` | U8 `74HC164` + U24 `74HC04` feedback | Tested | T0/T1/T2 sequence, edge behavior, reset, lower-state recovery |
| `RV8GR_PC16` | U1-U4 `74HC161` | Tested | count/load priority, carry chain, `/PC_LD`, `PC_INC` |
| `RV8GR_AddressMux16` | U15-U16/U29-U30 `74HC157` | Tested | PC vs `{DP,IRL}` address selection, `ADDR_REQ`, and A15 decode |
| `RV8GR_BusOwnership` | U7/U14/U34 plus ROM/RAM bus controls | Tested | T0/T1/T2 IBUS/DBUS drivers and bus-fight detection |
| `RV8GR_InstructionLatch` | U5/U6 `74HC574` | Tested | T0/T1 edge capture and T2 hold |
| `RV8GR_StorePath` | U7/U14/RAM/ROM control | Tested | IBUS to DBUS write direction and memory output disable |
| `RV8GR_DataPageMemory` | U32/U33/RAM/ROM/address mux | Tested | SETDP, RAM read/write, ROM read via DP, and `$7FFF/$8000` boundary |
| `RV8GR_IRQLatch` | U31 `74HC74` + U33 `74HC21` EI decode | Tested | IE set, `/IRQ` release latch, sticky IRQ_FF, no v1.0 vector |
| `RV8GR_RomDbusRead` | ROM + U7 `74HC245` | Tested | DBUS to IBUS read direction and ROM `/OE` safety |
| `RV8GR_AluAccumulator` | U9-U14/U17-U22/U27 | Tested | ALU path timing, AC latch edge, Z flag settle |
| `RV8GR_PageDataRegisters` | U23/U32/U33/U25 | Tested | `PG_CLK` and `DP_Load` edge timing |
| `RV8GR_BranchJumpControl` | U24-U28 control gates | Tested | `/PC_LD`, branch condition, no unintended load |
| `RV8GR_VirtualTestHelpers` | `ClockSource`, `Probe`, `BusProbe` virtual helpers | Tested | clock profiles, phase probes, bus contention observation |
| `RV8GR_FullControlOpcodeSweep` | T2 horizontal-control equation proof | Tested | all opcode/Z cases, reserved mixes, side-effect drift |
| `RV8GR_ResetClockBringup` | `lab01_power_clock` + `tb_rv8gr_chip_level` reset/ring sanity | Tested | reset idle/release, one-hot phase pushes, PC known-state policy, clock profiles |
| `RV8GR_FetchCycleTrace` | `doc/03_instruction_trace.md` + `tb_rv8gr_tasks.v` basic fetch | Tested | T0 control fetch, T1 operand fetch, T2 LI execute, PC motion, bus owners |
| `RV8GR_StoreLoadBranchTrace` | `doc/03_instruction_trace.md` traces 2, 4, and 7 | Tested | SB RAM write, LB RAM read, BEQ PC load, bus owners, PC/AC/RAM state |
| `RV8GR_PageJumpTrace` | `doc/03_instruction_trace.md` traces 5, 6, and 8 | Tested | SETDP, SETPG, J, page-register state, PC page loading |
| `RV8GR_InterruptTrace` | U31 `74HC74`, U33 `74HC21`, IRQ docs | Tested | EI, DI inert behavior, `/IRQ` LOW hold, release latch, sticky IRQ_FF |
| `RV8GR_BootSequenceTrace` | `doc/03_instruction_trace.md` Trace 11 + `doc/06_debug_plan.md` Step 0 | Tested | SETDP `$80`, SETPG `$00`, LI `$00`, J self, 12-clock manual bring-up |
| `RV8GR_Lab13MarkerTrace` | `doc/labs/lab13_full_system.md` Test 1 | Tested | LI/ADDI/SUBI/BEQ path, `$AA` marker, bus owners, final pass state |
| `RV8GR_WholeSystemChipLevelVirtual` | chip bench plan + tested trace packages | Tested | virtual whole-system chip-level gate with R/C and delay-noise stress nets |

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
