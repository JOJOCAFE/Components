# RV8GR Store/Load/Branch Trace

This package checks three RV8GR execute traces from
`doc/03_instruction_trace.md`:

- `SB $03`: AC drives through U14 and U7, then RAM at `0x8003` stores `0xAA`.
- `LB $03`: RAM at `0x8003` drives through U7, then AC becomes `0xAA`.
- `BEQ $20`: when `Z=1`, PC loads `0x0020`.

The proof watches the buses before it accepts the result. A vector only passes
when IBUS and DBUS each have a single owner. That matters because two chips
driving the same bus can hide a wiring bug even when the expected byte appears.

## Student Checks

1. Set `DP=0x80`, `PG=0x00`, and `IRL=0x03` for the memory traces.
2. For `SB`, start with `AC=0xAA`; expect `RAM[0x8003]=0xAA`.
3. For `LB`, start with `RAM[0x8003]=0xAA`; expect `AC=0xAA`.
4. For `BEQ`, set `IRL=0x20`; with `Z=1`, expect `PC=0x0020`.
5. Check that each row lists one IBUS driver and one DBUS driver at most.

Run:

```sh
PYTHONPATH=python python3 -B -m tests.test_lib_circuits
```
