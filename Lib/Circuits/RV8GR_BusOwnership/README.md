# RV8GR BusOwnership

This proof isolates the RV8GR bus-driver rules. It is not a new chip; it is a
standalone circuit contract for the real U7, U14, U34, ROM, and RAM paths.

## Normal Ownership

| Phase | Case | IBUS driver | DBUS driver |
|---|---|---|---|
| T0 | fetch control byte | U7 from DBUS | ROM or RAM |
| T1 | fetch operand byte | U7 from DBUS | ROM or RAM |
| T2 | immediate/no data address | U34 from `IRL` | ROM or RAM may be selected, but U7 is off |
| T2 | load/read memory, `SRC=1` | U7 from DBUS | ROM or RAM |
| T2 | store, `STR=1` | U14 from `AC` | U7 from IBUS |

For store, `WR_DIR=1` makes U7 write toward DBUS and also disables ROM output.
RAM output is disabled by `/WE=0` during the write cycle.

## Proof

The circuit proof checks:

- T0 and T1 have exactly one IBUS driver: U7.
- T2 immediate has exactly one IBUS driver: U34.
- T2 memory load has exactly one IBUS driver: U7.
- T2 store has U14 driving IBUS and U7 driving DBUS.
- ROM and RAM selects are complementary from A15.
- Forced unsafe states are detected as conflicts.

Run:

```sh
PYTHONPATH=python python3 -B -m tests.test_lib_circuits
```
