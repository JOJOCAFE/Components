# RV8GR End-To-End Test Campaign

Purpose: drive RV8GR testing from chip definitions and chip-level proofs to
standalone circuit proofs, whole-system simulation, and then physical build
signoff. This file is the Components-side campaign tracker; RV8GR source
benches and lab docs remain the authority for the full CPU implementation.

## Current Verification Checkpoint

Recorded whole-system gate:

```sh
/home/jo/kiro/RV8/RV8GR/tools/run_all_verilog_tb.sh
```

Result: pass. Components package coverage is also complete at pushed commit
`8a0de62`; this recorded result is software evidence, not physical signoff.

Covered RV8GR benches:

- `tb_rv8gr_asm`: assembler program halts at PC `$0084`, AC `$00`, Z `1`.
- `tb_rv8gr_full`: full CPU behavioral bench passed 127 cycles.
- `tb_rv8gr_irq`: polling IRQ, DI inert behavior, no vector, no PC save passed.
- `tb_rv8gr_opcode_sweep`: 512 opcode/Z cases passed.
- `tb_rv8gr_setdp`: SETDP, 5KB RAM page write/read, ROM read via DP `$00`,
  and default RAM page checks passed.
- `tb_rv8gr_tasks`: reset and fetch task checks passed.
- `tb_rv8gr_chip_level`: chip-level bring-up passed.
- `tb_rv8gr_chip_full`: chip-level full passed 124 cycles.

Components-side gates also passed recently:

- `PYTHONPATH=python python3 -B -m tests.test_lib_circuits`
- `PYTHONPATH=python python3 -B -m tests.test_block_ui`
- `PYTHONPATH=python python3 -B -m tests.test_db`
- `PYTHONPATH=python python3 -B -m chiplib.cli db --audit`

## Testing Ladder

### Working Rule - Real Build And Source Of Truth

This campaign supports a real RV8GR build, not only simulation. During the
physical build:

1. Test one module at a time before connecting the next module.
2. Record every observed failure with the module, signal, expected value,
   observed value, suspected cause, and fix.
3. If the fix changes main RV8GR wiring, RTL, KiCad, simulator behavior, or
   lab instructions, update `/home/jo/kiro/RV8/RV8GR` in the same work item.
4. Then update the matching Components circuit package so the reusable proof
   stays aligned.
5. Re-run the smallest relevant Components test and the smallest relevant
   RV8GR whole-system or lab test.

Do not let Components become a fork of the CPU. Components proves reusable
circuits; `/home/jo/kiro/RV8/RV8GR` remains the main CPU project.

### Stage 0 - Chip Definition And Chip-Level Gate

Goal: all RV8GR chips are checked at chip level before circuit-level timing
tests depend on them.

Required artifacts:

- `RV8GR/doc/rv8gr_chip_level_readiness.json`
- `RV8GR/doc/rv8gr_virtual_bench_plan.json`
- each chip's `definition/definition.json`
- each chip's `tests/truth_table.json`
- each chip's `tests/timing.json`
- each chip's `tests/tri_state.json`
- each chip's `tests/bus_fight.json`
- each chip's `tests/propagation.json`

Required gate:

```sh
PYTHONPATH=python python3 -B -m tests.test_generated_split_records
PYTHONPATH=python python3 -B -m tests.test_db
```

Policy:

1. Functional circuit tests may run once chip truth, timing, tri-state,
   bus-fight, and propagation split records pass.
2. Physical timing claims are blocked for any circuit path using a chip whose
   readiness entry still says `definition_timing_status: model_derived` or
   `definition_electrical_status: needs_extraction`.
3. Datasheet extraction or bench measurement must happen before speed claims.
4. If a chip definition changes from a datasheet row, update the matching
   split records and any affected RV8GR circuit package in the same work item.

Current readiness is visible in `RV8GR/doc/rv8gr_chip_level_readiness.json`.
The complete RV8GR definition/options set now has datasheet-backed
timing/electrical records sufficient for functional progression. Physical
timing remains blocked because definition evidence does not identify the
installed parts or measure the assembled system.

### Stage 1 - Circuit Package Integrity

Goal: every reusable RV8GR circuit package has:

- `circuit.json`
- `README.md`
- `tests/*.json`
- executable coverage in `python/tests/test_lib_circuits.py`
- source links to RV8GR docs, labs, RTL, or prior circuit packages

Current status: complete. `RV8GR_COVERAGE_INDEX.json` lists every
`Lib/Circuits/RV8GR_*` package as `Tested`; executable checks require each
package directory, README, JSON proof file, and Python test prefix, and prevent
the circuit README, index, and package tree from drifting.

### Stage 2 - Module Proofs

Goal: each physical module can be tested alone before the next module depends
on it.

Covered modules:

- clock/reset/ring counter
- program counter
- address mux and ROM/RAM select
- bus ownership
- ROM to DBUS to IBUS read path
- instruction latch
- ALU, accumulator, Z flag, and AC store buffer
- store path
- data-page memory path
- page/program registers
- branch/jump control
- IRQ latch
- virtual test helpers

No open package-integrity gap is currently recorded. New packages must enter
the same index/README/vector/Python gate.

### Stage 3 - Trace Proofs

Goal: instruction-level traces connect modules into CPU-visible behavior.

Covered traces:

- fetch cycle and LI execution
- SB, LB, BEQ
- SETDP, SETPG, J
- EI, DI, `/IRQ` assertion/release, sticky IRQ_FF
- full T2 opcode-control sweep for all 512 opcode/Z cases
- boot sequence: `SETDP $80`, `SETPG $00`, `LI $00`, and `J self`
- Lab 13 `$AA` marker program through final pass state

Current status: complete for the identified trace set. Treat IRQ polling
carefully: RV8GR v1.0 has no core CPU-visible IRQ status register. Any polling
proof must use RV8-Bus or external slot visibility, not a fake core path.

### Stage 4 - Whole-System Simulation

Goal: every full-system bench stays runnable and agrees with the package-level
proofs.

Required gate:

```sh
/home/jo/kiro/RV8/RV8GR/tools/run_all_verilog_tb.sh
```

Required pass lines:

- `=== ASSEMBLER TEST PASSED ===`
- `=== ALL TESTS PASSED ===`
- `ALL IRQ POLLING TESTS PASSED`
- `=== OPCODE SWEEP PASSED: 512 cases`
- `=== SETDP TEST PASSED ===`
- `ALL TASK TESTS PASSED`
- `RV8GR chip-level bring-up PASS`
- `RV8GR chip-level full PASS`

Current status: complete. `RV8GR_WholeSystemChipLevelVirtual` records the
Components-side whole-system proof scope, while RV8GR retains ownership of the
behavioral and chip-level Verilog runners. Do not duplicate RV8GR testbench
logic here; keep both RTL levels in the required gate.

### Stage 5 - Physical Build Signoff

Goal: hardware is accepted only after both logic behavior and physical evidence
pass.

Required evidence before a speed claim:

- installed EEPROM and SRAM markings
- selected datasheet timing rows
- memory output-float deadband
- clock-phase deadband
- VCC and edge-quality scope captures
- no bus-driver overlap during read/write turnarounds

Current status: `timing_margins.json` blocks hardware 5 MHz readiness and
student build speed recommendations until evidence is present.

Recommended physical order:

1. Single-step boot sequence: `SETDP $80`, `SETPG $00`, `LI $00`, `J self`.
2. Lab 13 full-system `$AA` marker program at manual clock.
3. RAM read/write marker program.
4. Page jump marker program.
5. IRQ latch LED test and RV8-Bus signal continuity.
6. 1 Hz or low-speed clock.
7. 1 MHz sustained run.
8. 2 MHz sustained run if wiring quality is good.
9. 5 MHz only after timing-margin and signal-integrity evidence pass.

## Bug And Change Record Shape

Every real-build bug should be recorded with this shape in the RV8GR project
docs, then mirrored here only when it affects a reusable circuit package:

```text
Date:
Build stage:
Module/circuit:
Signal(s):
Expected:
Observed:
Root cause:
Fix in RV8GR:
Fix in Components:
Verification rerun:
Remaining risk:
```

Examples of changes that must update RV8GR first:

- KiCad net or chip pin correction.
- Wiring guide correction.
- RTL or chip-level generated Verilog correction.
- Lab/debug-plan correction.
- Main simulator behavior correction.

Examples that can remain Components-only:

- Additional reusable proof vectors.
- Student wording in a Components package README.
- Timing-margin bookkeeping that does not change main RV8GR wiring or behavior.

## Timing Test Boundary

We can test three different timing layers:

1. Functional timing: edge order, no-edge holds, phase sequencing, and bus
   ownership. This is covered by Components circuit tests and RV8GR benches.
2. Model/source timing: propagation budgets, setup/hold windows, speed-grade
   candidates, and slack arithmetic. This is covered by `timing_margins.json`.
3. Physical timing: measured edge quality, memory output-float deadband,
   selected chip markings, VCC stability, and bus overlap. This cannot be
   completed by software alone; it needs scope or bench evidence from the real
   build.

Therefore, software can prove readiness for a physical test, but it cannot
declare the hardware physically timed until the physical evidence is recorded.

## Primary Timing Hazards

During real build and whole-system testing, prioritize these four hazards over
cosmetic cleanup:

1. Timing margin
   - Software check: `timing_margins.json` slack must stay non-negative for
     model paths at the claimed profile.
   - Hardware check: selected EEPROM/SRAM markings and measured/sourced memory
     timing must match the timing row being claimed.
   - Stop condition: no high-speed claim if selected chip speed or measured
     margin is unknown.

2. Bus racing
   - Software check: every vector has at most one IBUS driver and one DBUS
     driver; forced conflicts must be detected.
   - Hardware check: scope `/OE`, `DIR`, `/WE`, and representative bus bits
     through read/write turnarounds.
   - Stop condition: any overlap between two active bus drivers blocks
     full-system signoff.

3. Edge-trigger polarity
   - Software check: positive-edge registers, active-low controls, release
     edges, no-edge holds, and reset priority are explicit in vectors.
   - Hardware check: single-step and scope `CLK`, `/RST`, `ACC_CLK`, `PG_CLK`,
     `DP_Load`, `EI_decode`, and `/IRQ`.
   - Stop condition: any register captures on the wrong edge or any active-low
     control is inverted.

4. Propagation delay
   - Software check: named propagation paths must include source, through
     chips, destination, model delay, setup/hold requirement, total budget, and
     slack.
   - Hardware check: critical destination inputs settle before the active clock
     edge, especially AC, Z, `/PC_LD`, PG, DP, ROM/RAM read data, and store
     data before `/WE`.
   - Stop condition: any critical path is still moving when the destination
     latch samples it.

When a real-build failure appears in any of these four areas, update the main
RV8GR circuit/docs first if the CPU wiring or behavior is affected, then update
the matching Components proof.

## Team Ownership

- Pim: keep this campaign, backlog, and session handoff aligned.
- Bank: keep package boundaries and RV8/RV8GR source links clean.
- Fern: own pass/fail gates, full-system regression strategy, and coverage
  closure.
- Mint: own Verilog bench compatibility and behavioral vs chip-level RTL
  agreement.
- Ohm: own physical timing, pin truth, bus contention, and speed evidence.
- Bam: own Python circuit proof helpers, CLI/API test runners, and JSON vector
  execution.
- Noon: keep the student-facing README and lab wording accurate and readable.

## Definition Of Done

RV8GR is "properly tested" in this repo when:

1. Every RV8GR chip has explicit chip-level readiness, all five split-record
   files, and visible datasheet or measurement status for timing/electrical
   evidence.
2. Every circuit package listed in `Lib/Circuits/README.md` exists, has tests,
   and is covered by `tests.test_lib_circuits`.
3. Every major instruction trace in `doc/03_instruction_trace.md` has either a
   package-level proof or is explicitly covered by a whole-system bench.
4. The RV8GR Verilog whole-system gate passes.
5. Physical build notes do not claim speed beyond measured/source-backed
   evidence.
6. The next unproven item is visible in `Lib/Circuits/BACKLOG.md`.
