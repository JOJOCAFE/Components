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

## Build and test guide

- **Build/probe:** Follow Labs 01-03 for SW_CLK, SW_RST, U8, U24, and U1-U4. Probe `CLK`, `/RST`, T0/T1/T2, `PC_INC`, and all PC bits.
- **Isolated manual-clock test:** Hold reset LOW and verify all listed reset values. Release reset without touching clock, then make three clean press/release cycles and check the Student Checks after each release edge.
- **Integration test:** Connect `PC_INC=T0 OR T1` and continue for several complete T0/T1/T2 loops while checking PC increments only from old T0 or T1.
- **Pass:** Reset and release do not advance state; the first three release edges give T0/PC `$0000`, T1/PC `$0001`, and T2/PC `$0002`; phases remain one-hot and PC has no X/Z bit.
- **Stop:** Remove power for heat or a short. Stop on switch bounce causing multiple steps, phase overlap, clock movement during reset release, or unknown PC.
- **Temporary wiring:** Remove LED-only clock loads and Lab 03 always-enable counter ties that are not part of the integrated wiring; keep only the lab-approved buffered clock/reset path.
- **Boundary:** JSON uses clean edges and cannot prove mechanical debounce, supply integrity, or physical reset/clock waveform quality.
