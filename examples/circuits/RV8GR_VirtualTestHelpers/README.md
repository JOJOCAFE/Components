# RV8GR VirtualTestHelpers

This package defines reusable virtual helpers for RV8GR circuit proofs.

The helpers are not replacement CPU logic. They are test instruments:

- `ClockSource` supplies manual, random-push, and fixed-frequency profiles.
- `Switch` supplies stable on/off, one-shot push/release, one-shot on/off, and
  preset pulse-train stimulus.
- `Probe` records T0/T1/T2 phase signals and catches invalid phase states.
- `BusProbe` records which named device drives IBUS or DBUS and catches bus fights.

Use these helpers when the test needs clearer observation than ad hoc Python
code. Keep real state changes in real DB chip models whenever a real chip model
exists.

5 MHz remains functional simulation only until physical timing and
signal-integrity evidence exists.

For repeated push-switch tests, use the `100_pulses_10ms_interval` switch
profile when a deterministic preset sequence is clearer than random push timing.

## Student test-instrument guide

- **Purpose/chips:** `ClockSource`, `Switch`, `Probe`, `BusProbe`, `RCParasitic`, `DelayNoise`, and `OutputAssert` are virtual instruments, not replacement RV8GR logic chips.
- **Inputs/outputs:** VCLK drives `CLK`; probes observe T0/T1/T2; bus probes observe IBUS/DBUS value and driver; RC/noise helpers transform only their named test paths; assertions compare `EXPECT_IN` with a stated result.
- **Isolated manual-clock test:** Select the manual profile, make one edge at a time, and verify the phase probes record one T0, one T1, then one T2. Disable all bus drivers once to recognize Hi-Z, then deliberately run only the provided unsafe vector to confirm conflict detection.
- **Integration test:** Attach helpers without replacing real chip state, run `100_pulses_10ms_interval`, then the declared fixed-frequency profiles.
- **Pass:** Requested edges are counted exactly, phases remain valid, buses report no conflict in normal vectors, and every output assertion matches.
- **Stop:** Stop on an unexpected edge count, invalid phase, conflict, or assertion failure. Do not weaken an expected value to obtain a pass.
- **Temporary wiring:** Remove test-only virtual sources before claiming the real integrated control path is tested; probes may remain because they do not implement CPU state.
- **Boundary:** RC and noise values are estimates. Even a 5 MHz virtual pass requires physical voltage, waveform, and timing evidence.

```sh
PYTHONPATH=python python3 -B -m tests.test_lib_circuits
```
