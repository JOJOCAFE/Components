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
