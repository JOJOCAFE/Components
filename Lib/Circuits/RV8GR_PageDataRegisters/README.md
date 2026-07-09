# RV8GR PageDataRegisters

This circuit keeps the RV8GR page register proof separate from the data page
register proof.

| Register | Chip | Used for | Capture edge |
|---|---|---|---|
| PG | U23 `74HC574` | high byte for jump/load into PC | `PG_CLK` rising |
| DP | U32 `74HC574` | high byte for data memory address | `DP_Load` rising |

For SETPG, `PG_CLK` goes LOW during T2 and then rises at the end of T2. The
rising edge is the latch event. The LOW level is not the latch event.

## Proof

The proof checks:

- SETPG holds at T2 start and captures on the rising edge at T2 end.
- Wrong `MUX_SEL` or `AC_WR` settings do not load PG.
- Jump targets use `{PG,IRL}`.
- SETPG and SETDP normal control paths stay separated.
- Manual push switch, random 100-push, 50 kHz, 1 MHz, 2 MHz, and 5 MHz
  functional profiles are declared and executed.

Run:

```sh
PYTHONPATH=python python3 -B -m tests.test_lib_circuits
```
