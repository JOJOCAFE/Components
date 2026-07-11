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

## Build and test guide

- **Chips/buses:** This trace joins ROM, U7, U5, U6, U34, PC, and AC behavior. Probe T0/T1/T2, PC, IRH, IRL, AC, IBUS, and DBUS.
- **Isolated manual-clock test:** Load `30 42` at ROM `$0000-$0001`, reset, and make exactly three clean release edges, checking the five Student Checks above.
- **Integration test:** Repeat with the integrated ring counter and address path; verify ROM-to-DBUS-to-U7-to-IBUS in T0/T1 and U34-to-IBUS in T2.
- **Pass:** Edge 1 gives `IRH=$30, PC=$0001`; edge 2 gives `IRL=$42, PC=$0002`; edge 3 gives `AC=$42, PC=$0002`, with one owner per bus.
- **Stop:** Stop on skipped/duplicate phases, unknown PC or instruction bytes, wrong bus owner, or any conflict.
- **Temporary wiring:** Remove manual IR clocks, direct IBUS data switches, and fixed address ties before integration.
- **Boundary:** The trace proves functional ordering, not switch debounce or physical setup/hold margin.
