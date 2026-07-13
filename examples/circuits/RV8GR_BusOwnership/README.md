# RV8GR BusOwnership

This proof isolates the RV8GR bus-driver rules. It is not a new chip; it is a
standalone circuit contract for the real U7, U14, U34, ROM, and RAM paths.

The executable package uses the canonical per-bit wiring: `U7 A1..A8` are
`IBUS0..IBUS7`, `U7 B1..B8` are `DBUS0..DBUS7`; `U14` and `U34` output pins
`Y1..Y8` connect to `IBUS0..IBUS7`. U24, U25, U26, and U28 are included so
the runner exercises the real `/IRL_OE`, `BUF_OE_N`, `/AC_BUF`, and `WR_DIR`
control chain instead of accepting a same-name or symbolic bus binding.

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
- Forced unsafe states are detected as conflicts. These are fault-injection
  rows: they bypass the normal interlock and are not reachable normal phases.

Run:

```sh
PYTHONPATH=python python3 -B -m tests.test_lib_circuits
```

## Build and test guide

- **Chips/buses:** Observe U7, U14, U34, ROM, and RAM on `IBUS` and `DBUS`. A logic probe shows value; the circuit `BusProbe` also identifies the modeled driver.
- **Isolated manual-clock test:** Step one T0 fetch, T1 fetch, immediate T2, load T2, and store T2. Pause in each phase and record enabled outputs before continuing.
- **Integration test:** Run the fetch, store/load, and Lab 13 marker traces with both bus monitors enabled.
- **Pass:** Ownership matches the Normal Ownership table and no bus has more than one active driver. A floating bus with every output disabled is Hi-Z, not a data pass.
- **Stop:** Remove power immediately for heat or suspected output-to-output drive. Stop on any conflict report, unknown driven value, or overlapping ROM/RAM output enables.
- **Temporary wiring:** Remove LED-only bus shortcuts, direct bus drive switches, and the pre-RAM ROM shortcut described in Lab 05 before integration.
- **Boundary:** Simulation detects modeled enables and conflicts. Physical signoff needs current/heat checks and scope evidence for deadband between drivers.
