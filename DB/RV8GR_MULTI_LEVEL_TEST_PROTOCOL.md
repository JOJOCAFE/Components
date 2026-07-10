# RV8GR Multi-Level Test Protocol

Purpose: define one test protocol from chip definition to circuit package to
whole-system proof and physical build signoff.

This protocol uses the Components virtual instruments as the student-friendly
test bench. Virtual tests can prove model behavior and stress assumptions.
Physical hardware still needs real voltage, timing, and oscilloscope evidence.

## Level 0: Source And Definition Gate

Required evidence for every real chip:

- local or stable manufacturer datasheet reference
- package and pinout
- active-low names and bus directions
- behavior equation or truth table
- timing/electrical rows when present in the datasheet
- explicit missing-property status when any row is not available

Pass command:

```sh
PYTHONPATH=python python3 -B -m tests.test_db
```

Virtual instruments: `InputSource`, `Probe`, `OutputAssert`.

## Level 1: Chip-Level Behavior Gate

Required split records for every RV8GR chip:

- `truth_table.json`
- `timing.json`
- `tri_state.json`
- `bus_fight.json`
- `propagation.json`

Pass command:

```sh
PYTHONPATH=python python3 -B -m tests.test_generated_split_records
```

Virtual instrument mapping:

| Split record | Virtual instruments | Pass rule |
|---|---|---|
| `truth_table` | `InputSource`, `Probe`, `OutputAssert` | every output equals the expected value |
| `timing` | `ClockSource`, `Switch`, `Probe`, `OutputAssert` | edge/no-edge/setup/hold behavior matches the record |
| `tri_state` | `InputSource`, `BusProbe`, `OutputAssert` | disabled output is high-Z when required |
| `bus_fight` | `BusProbe`, `OutputAssert` | safe vectors are conflict-free and forced conflicts are reported |
| `propagation` | `ClockSource`, `Probe`, `RCParasitic`, `DelayNoise`, `OutputAssert` | output still passes after declared timing and selected stress |

Pass condition: all 18 RV8GR chips have all split records and the generated
record tests pass. This is a functional/model gate, not physical timing
signoff.

## Level 2: Circuit-Level Gate

Each `Lib/Circuits/RV8GR_*` package must include:

- `circuit.json`
- `README.md`
- at least one `tests/*.json` proof file
- package entry in `Lib/Circuits/RV8GR_COVERAGE_INDEX.json`
- executable coverage in `python/tests/test_lib_circuits.py`

Pass command:

```sh
PYTHONPATH=python python3 -B -m tests.test_lib_circuits
```

Virtual instruments: `ClockSource`, `Switch`, `Probe`, `BusProbe`,
`OutputAssert`, `RCParasitic`, and `DelayNoise`.

Pass condition: all indexed circuit packages are tested, all proof vectors
execute, bus conflicts are caught, and physical timing claims remain blocked
unless bench evidence exists.

## Level 3: System-Level Gate

Components-side pass commands:

```sh
PYTHONPATH=python python3 -B -m tests.test_lib_circuits
PYTHONPATH=python python3 -B -m tests.test_db
PYTHONPATH=python python3 -B -m tests.test_generated_split_records
```

RV8GR-side whole-system command:

```sh
/home/jo/kiro/RV8/RV8GR/tools/run_all_verilog_tb.sh
```

Required RV8GR pass markers:

- `=== ASSEMBLER TEST PASSED ===`
- `=== ALL TESTS PASSED ===`
- `ALL IRQ POLLING TESTS PASSED`
- `=== OPCODE SWEEP PASSED: 512 cases`
- `=== SETDP TEST PASSED ===`
- `ALL TASK TESTS PASSED`
- `RV8GR chip-level bring-up PASS`
- `RV8GR chip-level full PASS`

Pass condition: Components proofs and RV8GR benches agree on instruction
behavior, bus ownership, reset/boot behavior, page/data behavior, and IRQ v1.0
boundaries.

## Virtual Physical-System Fault Gate

Every chip-level, circuit-level, and whole-system virtual test must include
traps for the common AI mistakes that can look plausible in text but fail on a
real breadboard.

| Fault class | Required virtual test | Fix method |
|---|---|---|
| Wrong physical pin number or pin name | Compare every circuit pin reference against DB pin number, pin name, direction, active-low marker, and local pinout evidence before simulation starts. | Fix the chip definition or source-backed pin map first; do not move circuit wires to hide a bad definition. |
| Output-to-output wiring with no valid bus condition | Allow direct output-to-input wiring. Allow multiple outputs only on a named bus when enable conditions prove at most one driver is active; force a conflict vector with `BusProbe`. | Add tri-state control, buffer/transceiver direction, or output-enable sequencing so the old driver is high-Z before the new driver turns on. |
| Wrong positive/negative or rising/falling edge | For every edge-triggered part, prove the declared trigger edge captures and the opposite edge holds; reset/load priority must be explicit. | Move the signal to the correct clock phase or add an intentional inverter. Keep expected behavior tied to the datasheet edge. |
| Propagation delay or R/C delay creates bus overlap or early sampling | Use `RCParasitic` and `DelayNoise` on `CLK`, `/RST`, `IBUS`, `DBUS`, `/OE`, and `/WE`; assert positive disable-to-enable deadband and destination setup/hold margin. | Add phase separation, delay the new enable, disable the old driver earlier, shorten or buffer the net, or lower the clock until measured margin is positive. |

Pass condition: a virtual physical-system test must fail loudly for wrong pin
truth, meaningless output-output wiring, bad edge polarity, and negative delay
deadband. The report must name the fix method instead of changing the expected
result to match the bug.

## Level 4: Physical Build Signoff Gate

Required physical voltage points:

- 4.5 V
- 5.0 V
- 5.5 V

Required clock profiles:

- 100 manual push-switch ticks
- 50 kHz
- 1 MHz
- 2 MHz
- 5 MHz

Required physical evidence:

- installed EEPROM and SRAM markings
- selected datasheet timing rows
- VCC at power entry and far IC
- clock/reset edge quality
- memory output-float deadband
- bus turn-off before turn-on deadband
- representative driver-pin and destination-pin scope captures
- breadboard R/C calibration for `CLK`, `/RST`, `IBUS`, `DBUS`, and memory
  control nets

Pass condition: the real build passes the voltage/frequency sweep without bus
fights, bad edge triggers, timing-window failures, or supply/edge-quality
violations.

## Report Rule

Every test report must separate:

- passed virtual/model evidence
- passed whole-system simulation evidence
- blocked physical evidence
- next required physical capture

Do not write "hardware ready" unless Level 4 passes.
