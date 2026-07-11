# RV8GR Test Protocol

Purpose: define the test protocol used for RV8GR chip, circuit, system, and
physical breadboard timing work in Components.

Parent protocol: `lib/standard/COMPONENT_TEST_PROTOCOL.md`.

## Test Order

1. Chip definition source gate
   - Every RV8GR chip must have a local or stable datasheet source.
   - Pinout, package, logic, active-low controls, timing, and electrical rows
     must be represented in `definition/definition.json`.
   - Chip definitions describe behavior at the IC pins only. They do not include
     breadboard wire capacitance, contact resistance, probe loading, or layout
     crosstalk.

2. Chip-level split-record gate
   - Required records for every RV8GR chip:
     `truth_table.json`, `timing.json`, `tri_state.json`, `bus_fight.json`,
     and `propagation.json`.
   - Required test:
     `PYTHONPATH=python python3 -B -m tests.test_generated_split_records`
   - Pass means the Python behavior, generated records, and definition
     readiness agree for all 18 RV8GR chips.

3. Circuit package gate
   - Required records for every `examples/circuits/RV8GR_*` package:
     `circuit.json`, `README.md`, and at least one `tests/*.json` proof.
   - Required test:
     `PYTHONPATH=python python3 -B -m tests.test_lib_circuits`
   - Pass means circuit-level functional vectors, timing-margin metadata,
     bus-ownership policy, and package inventory checks agree.

4. Whole-system simulation gate
   - Required RV8GR command:
     `/home/jo/kiro/RV8/RV8GR/tools/run_all_verilog_tb.sh`
   - Required pass markers are recorded in
     `examples/circuits/RV8GR_END_TO_END_TEST_PLAN.md`.
   - Pass means the RV8GR behavioral and chip-level Verilog benches still agree
     with the reusable Components proofs.

5. Physical breadboard gate
   - Physical speed claims are blocked until bench evidence is recorded.
   - Required voltage points: `4.5 V`, `5.0 V`, `5.5 V`.
   - Required clock profiles:
     100 manual push-switch ticks, `50 kHz`, `1 MHz`, `2 MHz`, and `5 MHz`.
   - `5 MHz` remains functional simulation only until scope evidence proves
     timing margin, bus deadband, and signal quality on the real build.

## Physical Measurement Protocol

For every module before connecting the next module:

1. Record installed chip markings, especially EEPROM and SRAM speed grades.
2. Run 100 clean manual push-switch ticks and check one edge per push.
3. Run `50 kHz`, `1 MHz`, `2 MHz`, and `5 MHz` profiles only after the manual
   test is clean.
4. Repeat at `4.5 V`, `5.0 V`, and `5.5 V`.
5. Scope representative driver and destination pins, not only LEDs.
6. Record failures with expected, observed, root cause, fix, and rerun command.

Required scope/probe points:

- `CLK`, `/RST`, `T0`, `T1`, `T2`
- `ROM /OE`, `RAM /OE` or `/CE`, `RAM /WE`
- `U7 /OE`, `U7 DIR`, `WR_DIR`
- representative `DBUS`, `IBUS`, and `ABUS` bits
- `ACC_CLK`, `PG_CLK`, `DP_Load`, `/PC_LD`, `EI_decode`, `/IRQ`
- VCC at power entry and at a far IC

## Breadboard RC Protocol

Breadboard wires and contacts add resistance and capacitance between chip pins.
We can simulate this as an estimate, but it is not a physical proof.

Use the virtual `RCParasitic` component for repeatable circuit-level estimates.
It belongs in test/circuit artifacts, not inside real chip definitions.

RC estimate rule:

```text
tau_ns = source_resistance_ohm * total_capacitance_pf / 1000
```

Before measurement, treat `2.2 * tau` as a conservative 10%-to-90% settling
estimate. Do not use this estimate to claim hardware speed readiness.

Required RC estimate inputs:

- source/output resistance
- wire and breadboard capacitance
- all destination chip input capacitance
- probe capacitance
- pull-up or pull-down resistance for reset, clock, and RC debounce nets

Required calibration nets:

- `CLK`
- `/RST`
- `DBUS[0]`
- `IBUS[0]`
- `/OE` or `/WE` memory control

Physical pass condition:

- scoped destination edges are monotonic enough for 74HC inputs
- threshold-crossing delay is recorded at the destination input
- bus-driver deadband is greater than selected memory output-float plus buffer
  enable/disable skew
- no two active output drivers overlap on `DBUS` or `IBUS`

## Current Gates

- Chip-definition readiness: complete for all 18 RV8GR chips.
- Circuit functional proofs: covered by `tests.test_lib_circuits`.
- Physical timing/signoff: not proven until the voltage/frequency/RC bench
  evidence is recorded in the real build notes.
