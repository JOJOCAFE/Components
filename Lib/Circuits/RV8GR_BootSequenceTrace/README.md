# RV8GR Boot Sequence Trace

This package proves the first four instructions used for safe physical
bring-up:

```asm
SETDP $80
SETPG $00
LI $00
J $06
```

After reset, `DP`, `PG`, `AC`, and `Z` may be unknown. The first three
instructions make them known. The fourth instruction loops at `$0006`, so a
student can single-step the board and see that the CPU is stable.

Expected result after 12 clean manual clock edges:

| Signal | Expected |
|---|---|
| `PC` | `$0006` |
| `DP` | `$80` |
| `PG` | `$00` |
| `AC` | `$00` |
| `Z` | `1` |

Debug checklist:

- ROM byte `$0000` is `$40` for `SETDP`.
- ROM byte `$0001` is `$80`.
- ROM byte `$0002` is `$20` for `SETPG`.
- ROM byte `$0004` is `$30` for `LI`.
- ROM byte `$0006` is `$01` and byte `$0007` is `$06` for `J $06`.
- During each T2 immediate step, U34 is the only `IBUS` driver.
- This package proves functional order only. Physical speed still needs the
  voltage/frequency and oscilloscope protocol.
