# RV8GR AddressMux16

This circuit selects the 16-bit memory address used by RV8GR.

Four `74HC157` multiplexers do the work:

| Bits | Chip | `/ADDR_MODE=1` | `/ADDR_MODE=0` |
|---|---|---|---|
| `ABUS0..3` | U15 | `PC0..3` | `IRL0..3` |
| `ABUS4..7` | U16 | `PC4..7` | `IRL4..7` |
| `ABUS8..11` | U29 | `PC8..11` | `DP0..3` |
| `ABUS12..15` | U30 | `PC12..15` | `DP4..7` |

The important signal is `/ADDR_MODE`, not raw `T2`.

- `/ADDR_MODE=1` selects the program counter for fetch.
- `/ADDR_MODE=0` selects the data address `{DP,IRL}`.
- RV8GR makes `/ADDR_MODE` from `ADDR_REQ=SRC OR STR` and `T2`.

That means T0 and T1 always fetch from PC. T2 changes to `{DP,IRL}` only for
instructions that actually request a memory data address.

## Proof

The circuit proof checks:

- T0/T1 select PC even if `SRC` or `STR` is already latched.
- T2 with no address request still selects PC, so immediate instructions do
  not accidentally read `{DP,IRL}`.
- T2 with `SRC=1` or `STR=1` selects `{DP,IRL}`.
- `ABUS15` gives complementary ROM/RAM chip selects.
- The same vectors execute through live `74HC157` component models.

Run:

```sh
PYTHONPATH=python python3 -B -m tests.test_lib_circuits
```
