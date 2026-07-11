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

## Build and test guide

- **Build/probe:** Use Labs 11-12 for U23, U25, U27, U32, and U33. Probe IBUS, `PG_CLK`, `DP_Load`, PG, DP, IRL, and `PC_LOAD`.
- **Isolated manual-clock test:** Present a known IBUS byte. For SETPG, observe PG hold while `PG_CLK` is LOW and capture on its rising edge at T2 end. Separately execute SETDP and confirm only DP changes.
- **Integration test:** Execute `SETPG $12`, `J $5A`, and `SETDP $80`; then use DP for a RAM access.
- **Pass:** PG becomes `$12`, jump load is `$125A`, DP becomes `$80`, and no instruction changes the other register.
- **Stop:** Stop on a level-sensitive capture, wrong-register change, unknown PG/DP, or PC load assembled from the wrong bytes.
- **Temporary wiring:** Remove manual IBUS/control switches and any direct register clocks before reconnecting U34, T2 decode, and instruction controls.
- **Boundary:** Frequency profiles are functional simulation; physical proof needs the `PG_CLK`/`DP_Load` edge and data setup measured at the registers.
