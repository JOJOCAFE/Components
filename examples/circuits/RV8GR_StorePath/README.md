# RV8GR StorePath

This circuit proves the store path used by `SB`.

Normal store flow:

`AC -> U14 -> IBUS -> U7 -> DBUS -> RAM`

The key control is `/AC_BUF`:

- `/AC_BUF = NAND(T2, STR)`
- `/AC_BUF=0` enables U14 and pulls RAM `/WE` low.
- `WR_DIR = NOT(/AC_BUF)`
- `WR_DIR=1` makes U7 write from IBUS to DBUS and disables ROM output.

## Proof

The circuit proof checks:

- T0 and T1 do not assert store controls.
- T2 with `STR=0` does not assert store controls.
- T2 with `STR=1` enables U14, U7 write direction, ROM output disable, and RAM
  `/WE` low.
- RAM stores write only when A15 selects RAM space.
- Store to a ROM page remains bus-safe because ROM output is disabled.

Run:

```sh
PYTHONPATH=python python3 -B -m tests.test_lib_circuits
```

## Build and test guide

- **Build/probe:** Use Labs 08, 10, and 12 for U14, U7, U26, U28, ROM1, and RAM1. Probe T2, STR, A15, `/AC_BUF`, `WR_DIR`, ROM output enable, RAM `/WE`, IBUS, and DBUS.
- **Isolated manual-clock test:** Set `AC=$AA` and a RAM-space address. Check T0, T1, and T2/STR=0 first; then assert the T2 store row once and read RAM back after the write ends.
- **Integration test:** Execute `SB $03` with `DP=$80`, then `LB $03`, while monitoring both buses and memory enables.
- **Pass:** Only T2/STR=1 enables U14, sets U7 toward DBUS, disables ROM, and pulls RAM `/WE` LOW; RAM `$8003` reads back `$AA`. A ROM-page store remains conflict-free and does not write ROM.
- **Stop:** Stop before clocking if ROM output is enabled during write, two devices own a bus, or RAM `/WE` is LOW at the wrong address/phase. Remove power for heat.
- **Temporary wiring:** Remove direct AC-to-bus tests, manual U7 direction/enable wires, and manual RAM write controls before integration.
- **Boundary:** Simulation proves control ordering and modeled storage. Hardware needs scope proof of ROM disable, bus deadband, and RAM address/data setup around `/WE`.
