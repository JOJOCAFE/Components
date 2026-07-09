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
