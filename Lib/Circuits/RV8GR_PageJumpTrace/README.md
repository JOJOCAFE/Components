# RV8GR Page/Jump Trace

This package checks three RV8GR execute traces that are easy to mix up:

- `SETDP #0x80`: the operand becomes `DP`, so later data memory uses page `0x80`.
- `SETPG #0x12`: the operand becomes `PG`, so later jumps use page `0x12`.
- `J $5A`: the PC loads `{PG, IRL}`, so with `PG=0x12` and `IRL=0x5A`, PC becomes `0x125A`.

The proof keeps `SETDP`, `SETPG`, and `J` separate. `J` uses the page register
that was already latched before the jump; it does not secretly load `PG` from
the jump operand.

## Student Checks

1. During `SETDP`, check that `DP` changes and `PG` does not.
2. During `SETPG`, check that `PG` changes at the page-register clock edge and
   `DP` does not.
3. During `J`, check that `PC` becomes `{PG, IRL}`.
4. Confirm that U34 is the only IBUS driver for all three rows.
5. Treat this as functional simulation. Hardware timing still needs the shared
   timing-margin evidence.

Run:

```sh
PYTHONPATH=python python3 -B -m tests.test_lib_circuits
```
