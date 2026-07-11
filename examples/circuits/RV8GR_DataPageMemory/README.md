# RV8GR DataPageMemory

This circuit proves the data-page memory path.

`SETDP` loads U32 with the high address byte used later by `LB` and `SB`.

`DP_Load = T2 AND XOR_MODE AND /ADDR_MODE AND /AC_WR`

When `/ADDR_MODE=0`, the address mux selects:

`ABUS = {DP, IRL}`

Then A15 chooses memory:

- `$0000-$7FFF`: ROM selected
- `$8000-$FFFF`: RAM selected

## Proof

The circuit proof checks:

- SETDP loads U32 only when the U33 decode is true.
- `$7FFF` selects ROM and `$8000` selects RAM.
- RAM write/readback works through `{DP,IRL}`.
- ROM can be read as data when `DP<$80`.
- ROM and RAM chip selects are never both active.

Run:

```sh
PYTHONPATH=python python3 -B -m tests.test_lib_circuits
```

## Build and test guide

- **Build/probe:** Use Lab 12 for U32, U33, the address mux, ROM, and RAM wiring. Probe `DP`, `IRL`, `ABUS`, `A15`, ROM/RAM selects, RAM `/OE`, RAM `/WE`, and DBUS.
- **Isolated manual-clock test:** Execute `SETDP $80`, then stop the clock. Manually test `SB $03` with `AC=$AA`, followed by `LB $03`.
- **Integration test:** Run the Lab 12 ROM/RAM boundary checks at pages `$7F` and `$80`, then the full-system RAM program.
- **Pass:** DP captures `$80`; `RAM[$8003]=$AA`; LB returns `$AA`; `$7FFF` selects ROM and `$8000` selects RAM, with no simultaneous selects.
- **Stop:** Stop before writing if address, `/WE`, or bus ownership is wrong. Remove power for heat or contention.
- **Temporary wiring:** Lab 12 temporarily ties unused U33 inputs HIGH. Remove those VCC ties when Lab 14 connects the real `EI_decode` inputs, exactly as the lab directs.
- **Boundary:** Modeled read/write and decode are not physical memory timing signoff. Verify `/OE`, `/WE`, address stability, and readback on the board.
