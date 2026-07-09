# RV8GR Reset Clock Bring-up

This circuit is the first standalone RV8GR bring-up package. It joins the
Lab 01 push-button clock and reset nets with the ring counter and PC reset/count
sanity checks from the chip-level bench.

The clock button is normally high. Pressing it pulls `CLK` low; releasing it
creates the rising edge. One clean release edge must mean one CPU step. If a
real switch bounces, the circuit may step more than once, so the proof vectors
describe clean logical edges instead of pretending the RC network is perfect.

## Reset State

`/RST` is active low. While it is low:

| Signal | Expected |
|---|---|
| `T0` | `0` |
| `T1` | `0` |
| `T2` | `0` |
| `PC` | `0x0000` |

Releasing reset does not count as a clock edge. The first clean rising edge
enters `T0`; the PC is still `0x0000` because `PC_INC` was low before that
edge. Later edges repeat `T0 -> T1 -> T2`, and the PC increments on edges that
start from old `T0` or old `T1`.

## Student Checks

1. Hold reset low and confirm the phase LEDs are off and PC is zero.
2. Release reset without pressing the clock; nothing should advance.
3. Press and release the clock once; `T0` should be the only active phase.
4. Press and release again; `T1` should be the only active phase and PC becomes
   `0x0001`.
5. Press and release again; `T2` should be the only active phase and PC becomes
   `0x0002`.

The PC monitor has a strict policy: no PC bit may be `X`, `Z`, or unknown during
reset idle, reset release, or the post-clock bring-up checks. That mirrors the
chip-level Verilog sanity bench.

Run:

```sh
PYTHONPATH=python python3 -B -m tests.test_lib_circuits
```
