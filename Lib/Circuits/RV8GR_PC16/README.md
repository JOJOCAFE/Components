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
