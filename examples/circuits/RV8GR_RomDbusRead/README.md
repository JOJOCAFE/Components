# RV8GR RomDbusRead

This circuit is the ROM fetch/read path:

`ROM -> DBUS -> U7 -> IBUS`

U7 is a real `74HC245`. Its A side is wired to IBUS and its B side is wired to
DBUS. For a read, `DIR=0` and `/OE=0`, so the chip drives B to A: DBUS reaches
IBUS.

## Proof

The proof checks:

- ROM bytes at `$0000`, `$0001`, and `$0006` reach IBUS.
- `A15=1` disables ROM.
- `BUF_OE_N=1` disables U7.
- `WR_DIR=1` disables ROM output before U7 writes IBUS to DBUS.
- A forced bad write state is detected as a DBUS contention risk.

Run:

```sh
PYTHONPATH=python python3 -B -m tests.test_lib_circuits
```

## Build and test guide

- **Build/probe:** Follow Lab 05 for ROM1 and U7. Probe ABUS, `A15`, ROM `/CE` and `/OE`, U7 direction/enable, DBUS, and IBUS.
- **Isolated manual-clock test:** Hold a known address at `$0000`, `$0001`, then `$0006`; enable ROM and U7 for read and compare IBUS with each programmed byte. Disable U7 and then ROM separately.
- **Integration test:** Single-step T0/T1 fetches through the PC and address mux, then test a write-direction row with ROM output disabled.
- **Pass:** Each named ROM byte reaches IBUS in read mode; A15 or buffer disable removes that drive; write direction disables ROM before U7 drives DBUS; no DBUS conflict appears.
- **Stop:** Remove power for heat or suspected contention. Stop if ROM and U7 directions disagree, a disabled output still drives, or data is unknown.
- **Temporary wiring:** Lab 05 permits a ROM shortcut only before RAM is installed. Remove it before Lab 12 and connect the real ROM/RAM control path described there.
- **Boundary:** Modeled bytes and enables do not prove EEPROM programming, voltage levels, access time, or physical bus deadband.
