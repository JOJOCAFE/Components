# RV8GR PC16

This circuit is the RV8GR 16-bit program counter. It uses four cascaded
`74HC161` synchronous 4-bit counters.

The lab version first ties count enables high so students can prove the carry
chain. The integrated RV8GR circuit uses `PC_INC` for counting and `/PC_LD` for
parallel jumps/branches.

## Counter Blocks

| Nibble | Chip | Outputs | Load input |
|---|---|---|---|
| PC[3:0] | U1 | `PC0..PC3` | `IRL0..IRL3` |
| PC[7:4] | U2 | `PC4..PC7` | `IRL4..IRL7` |
| PC[11:8] | U3 | `PC8..PC11` | `PG0..PG3` |
| PC[15:12] | U4 | `PC12..PC15` | `PG4..PG7` |

## Proof

The circuit proof checks:

- `/RST=0` asynchronously clears the PC to `$0000`.
- With `/PC_LD=1` and `PC_INC=1`, rising clocks count upward.
- Without a rising clock, the PC holds.
- With `PC_INC=0`, rising clocks hold.
- Carry ripples through U1->U2->U3->U4 at nibble boundaries.
- With `/PC_LD=0`, the PC loads `{PG,IRL}` on the next rising clock.
- Parallel load wins over count when `/PC_LD=0` and `PC_INC=1`.

Run:

```sh
PYTHONPATH=python python3 -B -m tests.test_lib_circuits
```

## Build and test guide

- **Build/probe:** Build U1-U4 from Lab 03. Probe `CLK`, `/RST`, `/PC_LD`, `PC_INC`, PC nibble boundaries, and the 16 PC outputs.
- **Isolated manual-clock test:** Clear to `$0000`; with `/PC_LD=1` and count enabled, hand-clock through `$000F->$0010` and `$00FF->$0100`. Then set `{PG,IRL}`, pull `/PC_LD=0`, and clock once.
- **Integration test:** Replace always-enabled lab counting with `PC_INC=T0 OR T1`, connect branch/jump `/PC_LD`, and single-step fetch plus a jump.
- **Pass:** Reset gives `$0000`; count advances only on enabled rising edges; carry reaches each nibble; load produces `{PG,IRL}` and wins over count.
- **Stop:** Stop on an unknown PC bit, count while disabled, missed/double count, or wrong parallel-load value.
- **Temporary wiring:** Remove the Lab 03 ENP/ENT tie-high test arrangement where the integrated `PC_INC` cascade replaces it, and remove direct load switches before connection.
- **Boundary:** Functional count/load simulation does not prove breadboard carry-chain or clock margin at speed.
