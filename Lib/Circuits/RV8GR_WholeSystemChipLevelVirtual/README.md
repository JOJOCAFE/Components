# RV8GR Whole-System Chip-Level Virtual Test

This package is the virtual whole-system evidence gate while the physical RV8GR
build is still pending. It collects lower-level proofs; it is not a second,
pin-by-pin whole-board simulator.

It checks that the chip-level and circuit-level evidence is present together:

- all 18 RV8GR chips in the virtual bench plan
- boot sequence
- Lab 13 `$AA` marker
- RAM store/load/branch
- page jump
- IRQ latch boundary
- bus ownership

It also lists the critical nets that should be stressed with `RCParasitic` and
`DelayNoise` before the real build:

- `CLK`
- `/RST`
- `IBUS[0]`
- `DBUS[0]`
- `RAM_/OE`
- `RAM_/WE`
- `ROM_/OE`

Required AI error traps:

- wrong physical pin number, pin name, direction, or active-low marker
- output-to-output wiring unless bus enable conditions prove only one active
  driver
- wrong positive/negative or rising/falling edge behavior
- propagation delay, R/C delay, or delay noise that removes bus deadband or
  setup/hold margin

Fix method rule: fix the chip definition, bus ownership, edge phase, or timing
margin. Do not change expected results just to make a bad virtual circuit pass.

Pass means the virtual whole-system package is coherent. It does not mean the
hardware is signed off. Physical signoff still needs voltage, frequency, and
scope evidence.

## Whole-system test guide

- **Purpose/chips:** `CHIP_BENCH` tracks the 18 definition/options in the virtual
  bench plan and references BOOT, LAB13, STORE_LOAD_BRANCH, PAGE_JUMP, IRQ, and
  BUS proofs. It is not the physical 36-package board count.
- **Inputs/outputs and buses:** The package declares `CLK`, `/RST`, ABUS, PC,
  AC, Z, PG, DP, ROM/RAM controls, and both shared buses. The RC/noise entries
  identify virtual stress targets; this gate does not claim measured signal
  quality.
- **Part-model proof:** Direct circuit packages exercise the live Python models
  from `DB`. This proves the selected IC behavior at model pins for those test
  vectors.
- **Wired/composed proof:** Trace and composite packages inherit named
  lower-level evidence and enforce wiring metadata, endpoint resolution,
  coverage, and ownership rules. They do not execute every board package and
  wire as one whole-board model.
- **Pass:** All six commands below pass. This means the declared evidence,
  source paths, endpoints, model dispositions, and static circuit-fault checks
  agree.
- **Stop:** Stop at the first wrong pin metadata report, edge mismatch, unknown
  state, unintended write, bus conflict, or lost timing margin. Fix the source
  definition or circuit; never edit expected results around a defect.
- **Temporary wiring:** Before comparing with hardware, remove every
  isolated-lab switch, direct clock, shortcut, and tie-off called out by Labs
  03-14; keep only the final Lab 13/14 connections.
- **Boundary:** Physical status is planned, not measured. Signoff still requires
  chip-marking evidence, voltage sweeps, clock/reset scope captures, bus
  deadband, memory float/write timing, and frequency evidence from the real
  board.

## Enforced circuit commands

```sh
# Legacy circuit package and functional-vector gate
PYTHONPATH=python python3 -B -m tests.test_lib_circuits

# Source-reference gate
PYTHONPATH=python python3 -B -m tests.test_lib_circuit_sources

# Evidence-layer coverage gate
PYTHONPATH=python python3 -B -m tests.test_lib_circuit_coverage

# Wiring-endpoint gate
PYTHONPATH=python python3 -B -m tests.test_lib_circuit_endpoints

# Live DB part-model and composite-disposition gate
PYTHONPATH=python python3 -B -m tests.test_lib_circuit_models

# Static circuit fault report for this package
PYTHONPATH=python python3 -B -m chiplib.cli circuit-faults Lib/Circuits/RV8GR_WholeSystemChipLevelVirtual/circuit.json
```
