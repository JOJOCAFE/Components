# RV8GR VirtualTestHelpers

This package defines reusable virtual helpers for RV8GR circuit proofs.

The helpers are not replacement CPU logic. They are test instruments:

- `ClockSource` supplies manual, random-push, and fixed-frequency profiles.
- `Probe` records T0/T1/T2 phase signals and catches invalid phase states.
- `BusProbe` records which named device drives IBUS or DBUS and catches bus fights.

Use these helpers when the test needs clearer observation than ad hoc Python
code. Keep real state changes in real DB chip models whenever a real chip model
exists.

5 MHz remains functional simulation only until physical timing and
signal-integrity evidence exists.
