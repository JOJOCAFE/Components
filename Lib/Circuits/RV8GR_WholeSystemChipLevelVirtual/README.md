# RV8GR Whole-System Chip-Level Virtual Test

This package is the virtual full-system gate while the physical RV8GR build is
still pending.

It checks that the already-tested chip-level and circuit-level proofs are
present together:

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
