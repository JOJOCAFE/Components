# RV8GR Test Report

Date: 2026-07-10

Scope: Components-side RV8GR chip, circuit, virtual instrument, and system-test
readiness.

## Summary

| Level | Status | Evidence |
|---|---|---|
| Source/definition gate | PASS | `tests.test_db` passed |
| Chip-level behavior gate | PASS | `tests.test_generated_split_records` passed |
| Circuit-level package gate | PASS | `tests.test_lib_circuits` passed |
| Block UI/tooling gate | PASS | `tests.test_block_ui` passed |
| RV8GR whole-system Verilog gate | PASS from recorded checkpoint | `Lib/Circuits/RV8GR_END_TO_END_TEST_PLAN.md` records `run_all_verilog_tb.sh` pass |
| Physical hardware signoff | BLOCKED | voltage/frequency/scope evidence still missing |

## Current Counts

| Item | Count | Status |
|---|---:|---|
| RV8GR required chips | 18 | all listed in `DB/RV8GR_CHIP_LEVEL_READINESS.json` |
| Chip split-record sets | 18 | all have truth/timing/tri-state/bus-fight/propagation records |
| RV8GR circuit packages | 22 | all indexed in `Lib/Circuits/RV8GR_COVERAGE_INDEX.json` |
| Indexed packages marked `Tested` | 22 | README/index/package/test checks pass |

## Commands Run

```sh
PYTHONPATH=python python3 -B -m tests.test_db
PYTHONPATH=python python3 -B -m tests.test_lib_circuits
PYTHONPATH=python python3 -B -m tests.test_generated_split_records
PYTHONPATH=python python3 -B -m tests.test_block_ui
```

Results:

- `Components DB tests passed`
- `Components library circuit tests passed`
- `Components generated split-record tests passed`
- `Components block UI tests passed`

## Chip-Level Result

All RV8GR chips are functionally ready for circuit-level tests:

- `74HC00`
- `74HC04`
- `74HC21`
- `74HC32`
- `74HC74`
- `74HC86`
- `74HC157`
- `74HC161`
- `74HC164`
- `74HC245`
- `74HC283`
- `74HC541`
- `74HC574`
- `74HC688`
- `62256`
- `AS6C62256`
- `AT28C256`
- `SST39SF010A`

Chip-level virtual bench generation is defined by
`DB/VIRTUAL_TEST_GENERATOR_CONTRACT.json`.

## Virtual Instruments

Available student-friendly virtual test instruments:

- `InputSource`
- `ClockSource`
- `Switch`
- `Probe`
- `BusProbe`
- `OutputAssert`
- `RCParasitic`
- `DelayNoise`
- `VCC`
- `GND`
- `Pullup`
- `Pulldown`

`OutputAssert` is the pass/fail checker for expected outputs. `DelayNoise`
injects deterministic delay, jitter, or glitch stress between chips. These are
virtual stress tools, not physical signoff.

## Circuit/System Result

Circuit package coverage is passing for the 22 indexed RV8GR circuit packages,
including:

- bring-up and clock/reset packages
- bus ownership and memory path packages
- ALU/accumulator/page/control packages
- trace packages for fetch, store/load/branch, page/jump, interrupt, and boot
  sequence
- Lab 13 full-system `$AA` marker trace
- whole-system chip-level virtual gate with R/C and delay-noise stress nets
- virtual test helper package with R/C and delay/noise instruments

System-level recorded RV8GR bench checkpoint is pass in
`Lib/Circuits/RV8GR_END_TO_END_TEST_PLAN.md`.

## Physical Evidence Still Required

Hardware speed/signoff is blocked until all are captured:

- actual EEPROM/SRAM part markings
- 4.5 V, 5.0 V, and 5.5 V sweep
- 100 manual push-switch ticks
- 50 kHz, 1 MHz, 2 MHz, and 5 MHz runs
- VCC and far-IC supply captures
- clock/reset edge quality
- memory output-disable/output-float deadband
- bus turn-off before turn-on deadband
- representative R/C calibration at real driver and destination pins

## Current Decision

Components virtual/model testing is ready to support RV8GR circuit and system
work. Physical hardware is not signed off yet.
