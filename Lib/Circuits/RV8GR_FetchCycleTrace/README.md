# RV8GR Fetch Cycle Trace

This package turns the RV8GR golden trace into a standalone Components circuit
proof. It checks the first fetch/execute rhythm before the whole CPU is needed.

The important rule is simple:

- `T0`: fetch the control byte, latch `IRH`, increment PC.
- `T1`: fetch the operand byte, latch `IRL`, increment PC.
- `T2`: execute the instruction. For `LI $42`, AC becomes `0x42` and PC holds.

The trace also records which device drives each bus. During `T0` and `T1`,
ROM drives DBUS and U7 bridges DBUS to IBUS. During immediate `T2`, U34 drives
the operand onto IBUS. The proof rejects multiple active bus drivers.

## Student Checks

1. Put `0x30 0x42` at ROM addresses `0x0000` and `0x0001`.
2. After reset, pulse clock once: `IRH=0x30`, `PC=0x0001`.
3. Pulse again: `IRL=0x42`, `PC=0x0002`.
4. Pulse again: `AC=0x42`, `PC` still equals `0x0002`.
5. Confirm only one named driver owns IBUS and DBUS in every phase.

Run:

```sh
PYTHONPATH=python python3 -B -m tests.test_lib_circuits
```
