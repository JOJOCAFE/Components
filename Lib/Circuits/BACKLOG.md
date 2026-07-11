# Circuit Library Backlog

Last reconciled: 2026-07-11 at pushed commit `8a0de62`.

## Completed Software Work

- RV8GR chip readiness is project-neutral on the Components side, with all 18
  definition/options entries carrying datasheet-backed timing/electrical data
  sufficient for functional circuit progression.
- `tests.test_generated_split_records` checks definitions and truth, timing,
  tri-state, bus-fight, and propagation records.
- `RV8GR_COVERAGE_INDEX.json` maps every `RV8GR_*` package to its README, JSON
  proof, and executable `tests.test_lib_circuits` coverage. Every indexed
  package is `Tested`.
- Instruction traces cover fetch/LI and SB/LB/BEQ.
- `RV8GR_PageJumpTrace` covers SETDP, SETPG, and J.
- `RV8GR_InterruptTrace` covers EI, DI, IRQ release, and sticky IRQ state.
- `RV8GR_BootSequenceTrace` covers `SETDP $80`, `SETPG $00`, `LI $00`, and
  `J self`; `RV8GR_Lab13MarkerTrace` covers the Lab 13 `$AA` marker program.
- `RV8GR_WholeSystemChipLevelVirtual` covers the full chip-level virtual gate,
  including boot, Lab 13, RAM/page/IRQ/bus traces, R/C and delay/noise stress.
- The reusable virtual physical-system fault checker and
  `chiplib.cli circuit-faults` detect wrong pins, invalid output-output wiring,
  missing edge polarity, and missing delay/deadband declarations.
- The RV8GR whole-system Verilog gate was recorded passing via
  `/home/jo/kiro/RV8/RV8GR/tools/run_all_verilog_tb.sh`.

RV8GR v1.0 has no core CPU-visible IRQ status register. Polling proof must use
RV8-Bus or external `/SLOT` visibility, or remain an LED/bench observation.

## Timing And Physical Evidence

Definition-level timing extraction is complete for the RV8GR set, but physical
timing is not proven. `timing_margins.json` deliberately separates:

1. Functional edge, phase, and bus-ownership proofs.
2. Source/model timing rows, path budgets, and slack calculations.
3. Physical measurements from the installed build.

Remaining physical work:

1. Record actual EEPROM and SRAM markings and selected datasheet speed rows.
2. Single-step the boot sequence and Lab 13 `$AA` program on the real build.
3. Run RAM read/write, page jump, and IRQ latch/continuity checks.
4. Capture clock/reset and destination edges, memory access/float/write timing,
   quantified bus deadband, VCC quality, and no-driver-overlap evidence.
5. Run the 4.5 V, 5.0 V, and 5.5 V sweep at 100 manual ticks, 50 kHz, 1 MHz,
   2 MHz, and 5 MHz if attempted.

Until those records exist, boot/Lab13/whole-system completion means software
coverage only. Hardware 5 MHz readiness and student speed recommendations stay
blocked.

## Waiting Items

- Visual chip-block editor implementation: waiting by user request. Backend
  metadata, `components.block_ui`, and `Docs/VISUAL_MODULE_PLAN.md` are ready.
- MCP adapter: waiting until editor/service command names and state transitions
  settle. It must remain a thin adapter over the existing service contract.
- Additional trace packages: no current gap. Add one only for a newly identified
  CPU behavior not covered by the index or RV8GR whole-system benches.

## Historical Checkpoints

- `8bb462b`: RV8GR virtual fault protocol.
- `49ed732`: reusable circuit fault checker.
- `86341c5`: whole-system virtual gate.
- `152db2c`: exact timing extraction and visual module plan.

The active campaign and acceptance boundary are in
`Lib/Circuits/RV8GR_END_TO_END_TEST_PLAN.md`.
