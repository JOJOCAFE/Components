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

## Build and test guide

- **Chips/buses:** This trace joins U1-U7, the U9/U22/U27 ALU path, U24/U28 branch control, U34, and ROM1. Watch PC, AC, Z, PG, DP, IRH/IRL, IBUS, and DBUS.
- **Isolated manual-clock test:** Reset and make exactly 15 clean release edges through the listed program. Record the state after clocks 9, 12, and 15.
- **Integration test:** Repeat on the assembled Lab 13 system, first by hand and then only at the lab-approved baseline after manual stepping passes.
- **Pass:** Clock 9 gives `AC=$00, Z=1`; clock 12 gives `PC=$000C`; clock 15 gives `PC=$000E, AC=$AA, Z=0, PG=$00, DP=$80`, with one driver per bus.
- **Stop:** Stop on an unexpected phase, PC, AC, Z, or bus owner. Remove the clock and power immediately if an IC heats or a bus fight is suspected.
- **Temporary wiring:** Before Lab 13, replace all isolated-lab switches and temporary ties with the real control nets listed in the lab's final-connection checklist.
- **Boundary:** The marker trace proves logical integration. Physical 1 MHz/5 MHz claims require the lab timing and oscilloscope evidence.
