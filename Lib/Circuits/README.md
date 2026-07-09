# Circuit Library

This folder breaks reusable RV8GR subcircuits out of the full CPU so each block
can be documented, simulated, and proven on its own.

Use the RV8GR `doc/build_plan/` stages and `doc/labs/` files as extraction
helpers. The build plan gives module order and stop conditions; the labs give
student-facing wiring checks. The circuit packages still record electrical
truth when lab wording is simplified.

## RV8GR Circuit Candidates

| Circuit | RV8GR source | Status | Proof focus |
|---|---|---|---|
| `RV8GR_RingCounter` | U8 `74HC164` + U24 `74HC04` feedback | Started | T0/T1/T2 sequence, edge behavior, reset, lower-state recovery |
| `RV8GR_PC16` | U1-U4 `74HC161` | Started | count/load priority, carry chain, `/PC_LD`, `PC_INC` |
| `RV8GR_AddressMux16` | U15-U20/U29/U30 `74HC157` | Next | PC vs `{DP,IRL}` address selection and A15 decode |
| `RV8GR_RomDbusRead` | ROM + U7 `74HC245` | Next | DBUS to IBUS read direction and ROM `/OE` safety |
| `RV8GR_InstructionLatch` | U5/U6 `74HC574` | Next | T0/T1 edge capture and hold |
| `RV8GR_AluAccumulator` | U9-U14/U21/U22/U27/U28 | Next | ALU path timing, AC latch edge, Z flag settle |
| `RV8GR_StorePath` | U7/U14/RAM/ROM control | Next | IBUS to DBUS write direction and no bus fight |
| `RV8GR_PageDataRegisters` | U23/U32/U33/U25 | Next | `PG_CLK` and `DP_Load` edge timing |
| `RV8GR_BranchJumpControl` | U24-U28 control gates | Next | `/PC_LD`, branch condition, no unintended load |
| `RV8GR_IRQLatch` | U31 `74HC74` | Next | `/IRQ` release edge, IE latch, reset clear |

Each circuit package should include:

- `circuit.json`: chips, ports, wiring, timing contract, and source links.
- `tests/*.json`: proof vectors or timing/bus checks.
- `README.md`: student-readable explanation and debug checklist.
- Python tests under `python/tests/` that fail loudly when the proof breaks.

## Next Tests From RV8GR Debug Plan

1. `RV8GR_AddressMux16`: prove `/ADDR_MODE=1` selects PC for fetch and
   `/ADDR_MODE=0` selects `{DP,IRL}` for data access. Include the lab warning
   that real RV8GR uses `ADDR_REQ=SRC OR STR`, not raw `T2`.
2. `RV8GR_BusOwnership`: prove the phase table from `06_debug_plan.md`: T0/T1
   use U7 DBUS-to-IBUS, T2 immediate uses U34, T2 store uses U14 plus U7
   write direction. This is the main bus-race proof.
3. `RV8GR_InstructionLatch`: prove U5 captures control only on T0, U6 captures
   operand only on T1, and both hold through T2.
4. `RV8GR_StorePath`: prove `STR=1` at T2 makes U7 enabled, `WR_DIR=1`, ROM
   `/OE=HIGH`, and RAM `/WE=LOW` only when selected.
5. `RV8GR_DataPageMemory`: prove SETDP, RAM/ROM boundary `$7FFF/$8000`, RAM
   write/readback, ROM read via DP, and ROM/RAM chip-select exclusivity.
6. `RV8GR_ClockProfiles`: keep push-switch, random debounced push, 50 kHz,
   1 MHz, 2 MHz, and 5 MHz profiles on every circuit. Mark 5 MHz as functional
   simulation until timing-margin and hardware signal-integrity proof exist.
7. `RV8GR_IRQLatch`: prove `/IRQ` low-then-release latches IRQ_FF, reset clears
   it, and v1.0 does not force PC or auto-vector.
