# RV8GR AluAccumulator

This circuit is the RV8GR arithmetic and accumulator block.

```text
XOR_B   = XOR_MODE ? AC : {8{ALU_SUB}}
XOR_Y   = IBUS XOR XOR_B
SUM     = AC + XOR_Y + ALU_SUB
AC_D    = MUX_SEL ? XOR_Y : SUM
ACC_CLK = NAND(T2, AC_WR)
```

U9 captures `AC_D` on the rising edge of `ACC_CLK`. Because U27 makes this
clock with NAND, an AC write starts with `T2=1, AC_WR=1` (ACC_CLK LOW), then
captures on the `T2` high-to-low transition when ACC_CLK rises. AC feedback
does not make a combinational loop because U9 is a register: the old AC value
feeds the ALU, then the new value is captured on the clock edge.

## Proof

The proof checks:

- `LI`, `ADDI`, `SUBI`, and `XORI` datapath results.
- SUB borrow/carry behavior.
- AC holds during T0/T1 or when `AC_WR=0`.
- U14 drives AC onto IBUS only when `/AC_BUF=0`.
- U22 `Y`/U21 Z flag behavior for zero-to-nonzero, nonzero-to-zero, repeated
  zero, no-edge hold, and non-AC-write hold. `Y` is LOW when AC equals zero.
- Manual push switch, random 100-push, 50 kHz, 1 MHz, 2 MHz, and 5 MHz
  functional profiles.

## Public simulation initialization

Independent vectors may initialize AC through the public runner API:

```python
runner.initialize_state("AC", 0x42)
```

This is not output forcing or a private-model write. The declared runtime
contract drives the public `IBUS0..IBUS7` and LI controls, takes `T2` high,
then returns it LOW and requires the real U27 `ACC_CLK` net to rise before U9
and U21 receive the edge.

The live proof executes the eight datapath vectors plus five explicit Z-settle
vectors. U21 uses an explicit, package-only 20 ns post-`ACC_CLK` model sample,
because the canonical `rv8gr_chip_level.v` instantiates U21 with
`SAMPLE_DELAY(20)`. This keeps the generic 74HC74 model unchanged and makes
Z follow the newly captured AC value in the same ordering as the chip-level
RTL.

This is a simulation contract only. It does **not** create a second physical
clock edge, establish a 20 ns PCB settling time, or prove any clock frequency.

Run:

```sh
PYTHONPATH=python python3 -B -m tests.test_lib_circuits
```

## Build and test guide

- **Build/probe:** Follow Labs 07-09 for U9-U14, U17-U22, and U27. Probe `IBUS`, `XOR_Y`, `SUM`, `ACC_CLK`, `AC`, `/AC_BUF`, and `Z_flag`; use lab pinouts, not this summary, for wiring.
- **Isolated manual-clock test:** Hold T2 low while setting the controls and IBUS. Raise T2 once with `AC_WR=1`, then lower it. Check LI, ADDI, SUBI, and XORI one vector at a time; repeat with `AC_WR=0` to prove hold.
- **Integration test:** Single-step instructions through T0/T1/T2, then execute a store and confirm U14 drives IBUS only while `/AC_BUF=0`.
- **Pass:** In modeled simulation, AC matches every expected byte, changes only on the rising `ACC_CLK` edge, and after the explicit 20 ns RTL sample phase Z is 1 exactly when captured AC is zero. AC is the sole IBUS driver during store.
- **Stop:** Cut power for a hot IC or multiple IBUS drivers. Stop clocking for an unexpected AC edge, unstable feedback, or an unknown bus value.
- **Temporary wiring:** Remove manual IBUS, control-switch, and direct clock ties from Labs 07-09 before reconnecting IR control, T2, and the shared bus.
- **Boundary:** Manual and fixed-frequency profiles are functional simulation. Physical frequency claims require scope evidence for `ACC_CLK`, data setup/hold, and bus deadband.
