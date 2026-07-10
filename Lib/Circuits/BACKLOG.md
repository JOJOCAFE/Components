# Circuit Library Backlog

## RV8GR Chip-Level Gate

- Done: `DB/RV8GR_CHIP_LEVEL_READINESS.json` now records all 18 RV8GR chips,
  their role, datasheet timing/electrical status, chip-level gate, physical
  timing allowance, and next datasheet action.
- Done: `DB/RV8GR_CHIP_LEVEL_TEST_PLAN.md` defines the required order:
  datasheet definition evidence, chip-level split records, circuit packages,
  whole-system benches, then physical build measurements.
- Done: `python/tests/test_generated_split_records.py` now checks the
  readiness matrix against actual definitions and the five split-record files.
- Done: all 18 RV8GR chips now have datasheet-backed timing/electrical
  readiness for circuit functional progression.

Current blocked-for-physical-timing chips:

- none at definition level

Priority order:

1. Record the installed SRAM marking: Samsung `KM62256C`, Alliance
   `AS6C62256-55`, or another compatible 62256.
2. Run the physical voltage/frequency sweep at 4.5 V, 5.0 V, and 5.5 V using
   100 push-switch ticks, 50 kHz, 1 MHz, 2 MHz, and 5 MHz before any hardware
   speed claim.

## RV8GR Trace Packages

- Done: `RV8GR_StoreLoadBranchTrace` packages the SB, LB, and BEQ rows from
  `doc/03_instruction_trace.md` with machine-readable vectors for state and bus
  ownership.
- Done: `RV8GR_PageJumpTrace` packages SETDP, SETPG, and J so page-register
  state and PC page loading are checked together.
- Done: `RV8GR_InterruptTrace` packages EI, DI, and IRQ release so
  interrupt-enable state and sticky IRQ latch behavior are checked against
  fetch/execute rows.
- Done: `RV8GR_Lab13MarkerTrace` packages the Lab 13 full-system marker
  program through `AC=$AA`, including the taken `BEQ $0C`, fail-path skip,
  bus ownership, and final pass state.
- Waiting: add more trace packages after the chip-level datasheet gate above
  has been advanced. Do not start circuit timing signoff from trace packages
  while chip definitions still have timing/electrical gaps.

Note: RV8GR v1.0 has no core CPU-visible IRQ status register. A polling-loop
proof must use RV8-Bus or external `/SLOT` visibility, or stay as an LED/bench
observation. Do not invent a fake core status-register path.

### RV8GR_InterruptTrace Team Tasks

1. **Pim - scope and routing**
   - Keep this task limited to EI, DI, `/IRQ` assertion/release, IE, IRQ_FF,
     PC unchanged, and v1.0 polling-only behavior.
   - Do not reopen commit packaging, visual editor implementation, MCP, or
     broader interrupt-vector design in this lane.
   - Acceptance: backlog, circuit package, tests, and README all name the same
     boundaries.

2. **Bank - circuit package shape**
   - Create `Lib/Circuits/RV8GR_InterruptTrace/` using the existing trace
     package pattern.
   - Source from `RV8GR_IRQLatch`, `RV8GR_FullControlOpcodeSweep`, and current
     instruction trace docs.
   - Acceptance: `circuit.json` declares chips, ports, absent v1.0 paths,
     timing boundaries, and verification files.

3. **Fern - executable proof**
   - Add machine-readable vectors for reset, EI, DI inert behavior, `/IRQ` LOW
     hold, `/IRQ` release latch, sticky IRQ_FF, and PC unchanged.
   - Add `python/tests/test_lib_circuits.py` coverage that executes the vectors
     against existing helper behavior and rejects vector/ack/auto-clear drift.
   - Acceptance: `PYTHONPATH=python python3 -B -m tests.test_lib_circuits`
     fails if IE, IRQ_FF, PC, or absent-path behavior changes.

4. **Mint - RTL/equation alignment**
   - Compare the trace vectors with the existing full-control opcode sweep
     assumptions for EI decode.
   - Keep DI documented as inert unless the current RTL/docs prove otherwise.
   - Acceptance: trace vectors do not contradict
     `RV8GR_FullControlOpcodeSweep/tests/full_control_opcode_sweep.json`.

5. **Ohm - edge and pin truth**
   - Reuse `RV8GR_IRQLatch` pin truth for U31 `74HC74` and U33 `74HC21`.
   - Keep `/IRQ` latch behavior tied to rising release, not LOW assertion.
   - Acceptance: README and test vectors state the active-low input and
     release-edge behavior in beginner-readable words.

6. **Bam - package/test tooling**
   - Add the new package files without changing shared simulator behavior.
   - Add focused helpers only if existing `irq_latch_step()` is not enough.
   - Acceptance: JSON files parse, all started circuit packages still have
     tests, and no DB/package audit behavior changes.

7. **Noon - student explanation**
   - Write a short README explaining EI, DI, `/IRQ` LOW, `/IRQ` release, sticky
     IRQ_FF, and polling-only v1.0 behavior.
   - Acceptance: a 10-15 year old can tell why pressing IRQ LOW is different
     from releasing it HIGH, and why the CPU does not auto-jump.

Status: complete. Package files live under
`Lib/Circuits/RV8GR_InterruptTrace/`; executable checks live in
`python/tests/test_lib_circuits.py`.

## Physical Evidence

- Done: `timing_margins.json` now separates source-backed candidate timing from
  required bench evidence and blocks hardware-speed claims until all required
  measurements pass.
- Next: fill actual EEPROM/SRAM markings, memory output-float deadband,
  clock-phase deadband, and supply/edge quality captures.

## End-To-End Test Campaign

- Active campaign tracker:
  `Lib/Circuits/RV8GR_END_TO_END_TEST_PLAN.md`.
- Done: RV8GR whole-system Verilog gate passed via
  `/home/jo/kiro/RV8/RV8GR/tools/run_all_verilog_tb.sh`.
- Next Components tasks:
  1. Done: add `RV8GR_COVERAGE_INDEX.json` plus a package/readme
     coverage-index check so `Lib/Circuits/README.md` cannot drift from actual
     `RV8GR_*` package directories.
  2. Done: add `RV8GR_BootSequenceTrace` for `SETDP $80`, `SETPG $00`,
     `LI $00`, and `J self`.
  3. Done: add `RV8GR_Lab13MarkerTrace` for the Lab 13 `$AA` pass program.
- Next RV8GR hardware tasks:
  1. Single-step the boot sequence on the physical build.
  2. Single-step Lab 13 full-system marker program.
  3. Run RAM read/write and page jump marker programs.
  4. Capture timing and bus deadband evidence before any speed claim.

## Visual Editor

- Done: block-UI export now exposes backend editor metadata for palette,
  commands, validation gates, and MCP-ready tool mapping.
- Next: build the first visual chip-block editor screen against
  `components.block_ui` instead of creating a second circuit format.

## Waiting Items

- Commit current checkpoint: waiting by user request.
- Visual chip-block editor implementation: waiting by user request.
- MCP adapter implementation: waiting until service/editor names settle.
