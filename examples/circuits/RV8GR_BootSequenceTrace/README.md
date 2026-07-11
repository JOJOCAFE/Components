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

## Build and test guide

- **Chips and buses:** This trace joins U1-U4, U9/U14, U23, U32-U34, ROM1, and virtual clock/bus monitors. Watch `PC`, `DP`, `PG`, `AC`, `Z`, `IBUS`, and `DBUS`.
- **Isolated manual-clock test:** Reset, load the four listed instructions at their stated ROM addresses, and make exactly 12 clean release edges. Record state after each T2.
- **Integration test:** Run the same ROM through the assembled CPU and confirm U7 owns IBUS during T0/T1 and U34 owns it during immediate T2.
- **Pass:** After edge 12, `PC=$0006`, `DP=$80`, `PG=$00`, `AC=$00`, and `Z=1`, with no bus conflict.
- **Stop:** Stop on any extra step per button release, unknown state, wrong ROM byte, phase overlap, or more than one bus driver. Remove power for heat or suspected contention.
- **Temporary wiring:** Before this trace, remove isolated lab switches and tie-offs from module inputs; all controls must come from the integrated instruction and phase paths.
- **Boundary:** This proves sequence and ownership in simulation/manual stepping only. It does not prove physical voltage, clock rate, or timing margin.
