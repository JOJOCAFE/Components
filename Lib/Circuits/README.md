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
