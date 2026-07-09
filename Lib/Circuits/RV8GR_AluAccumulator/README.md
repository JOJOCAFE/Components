# RV8GR AluAccumulator

This circuit is the RV8GR arithmetic and accumulator block.

```text
XOR_B   = XOR_MODE ? AC : {8{ALU_SUB}}
XOR_Y   = IBUS XOR XOR_B
SUM     = AC + XOR_Y + ALU_SUB
AC_D    = MUX_SEL ? XOR_Y : SUM
ACC_CLK = T2 AND AC_WR
```

U9 captures `AC_D` on the rising edge of `ACC_CLK`. AC feedback does not make a
combinational loop because U9 is a register: the old AC value feeds the ALU,
then the new value is captured on the clock edge.

## Proof

The proof checks:

- `LI`, `ADDI`, `SUBI`, and `XORI` datapath results.
- SUB borrow/carry behavior.
- AC holds during T0/T1 or when `AC_WR=0`.
- U14 drives AC onto IBUS only when `/AC_BUF=0`.
- U22 `Y`/U21 Z flag behavior for zero, nonzero, and toggling values. `Y` is
  LOW when AC equals zero.
- Manual push switch, random 100-push, 50 kHz, 1 MHz, 2 MHz, and 5 MHz
  functional profiles.

Run:

```sh
PYTHONPATH=python python3 -B -m tests.test_lib_circuits
```
