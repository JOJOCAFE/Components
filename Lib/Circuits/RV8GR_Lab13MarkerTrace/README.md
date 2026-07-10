# RV8GR Lab 13 Marker Trace

This package proves the Lab 13 full-system pass program through the `$AA`
marker:

```asm
LI   $10
ADDI $05
SUBI $15
BEQ  $0C
LI   $AA
```

After 15 clean manual clock edges, the expected pass state is:

| Signal | Expected |
|---|---|
| `PC` | `$000E` |
| `AC` | `$AA` |
| `Z` | `0` |
| `PG` | `$00` |
| `DP` | `$80` |

Debug checklist:

- ROM byte `$0000` is `$30` for `LI`, and byte `$0001` is `$10`.
- ROM byte `$0004` is `$90` for `SUBI`, and byte `$0005` is `$15`.
- Clock 9 must leave `AC=$00` and `Z=1`.
- Clock 12 must load `PC=$000C`; otherwise the fail path at `$0008` was not
  skipped.
- Clock 15 must leave `AC=$AA` and `Z=0`.
- During T0/T1, U7 is the only `IBUS` driver and ROM1 is the only `DBUS`
  driver.
- During T2 immediate execution, U34 is the only `IBUS` driver.
- This package proves functional order only. Physical speed still needs the
  voltage/frequency and oscilloscope protocol in `timing_margins.json`.
