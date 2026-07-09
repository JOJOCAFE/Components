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
| `RV8GR_AddressMux16` | U15-U16/U29-U30 `74HC157` | Started | PC vs `{DP,IRL}` address selection, `ADDR_REQ`, and A15 decode |
| `RV8GR_BusOwnership` | U7/U14/U34 plus ROM/RAM bus controls | Started | T0/T1/T2 IBUS/DBUS drivers and bus-fight detection |
| `RV8GR_InstructionLatch` | U5/U6 `74HC574` | Started | T0/T1 edge capture and T2 hold |
| `RV8GR_StorePath` | U7/U14/RAM/ROM control | Started | IBUS to DBUS write direction and memory output disable |
| `RV8GR_DataPageMemory` | U32/U33/RAM/ROM/address mux | Started | SETDP, RAM read/write, ROM read via DP, and `$7FFF/$8000` boundary |
| `RV8GR_IRQLatch` | U31 `74HC74` + U33 `74HC21` EI decode | Started | IE set, `/IRQ` release latch, sticky IRQ_FF, no v1.0 vector |
| `RV8GR_RomDbusRead` | ROM + U7 `74HC245` | Started | DBUS to IBUS read direction and ROM `/OE` safety |
| `RV8GR_AluAccumulator` | U9-U14/U17-U22/U27 | Started | ALU path timing, AC latch edge, Z flag settle |
| `RV8GR_PageDataRegisters` | U23/U32/U33/U25 | Started | `PG_CLK` and `DP_Load` edge timing |
| `RV8GR_BranchJumpControl` | U24-U28 control gates | Started | `/PC_LD`, branch condition, no unintended load |
| `RV8GR_VirtualTestHelpers` | `ClockSource`, `Probe`, `BusProbe` virtual helpers | Started | clock profiles, phase probes, bus contention observation |

Each circuit package should include:

- `circuit.json`: chips, ports, wiring, timing contract, and source links.
- `tests/*.json`: proof vectors or timing/bus checks.
- `README.md`: student-readable explanation and debug checklist.
- Python tests under `python/tests/` that fail loudly when the proof breaks.

## Next Tests From RV8GR Debug Plan

1. `RV8GR_FullControlOpcodeSweep`: extract more of the Verilog opcode-sweep
   expectations into standalone circuit proofs, especially illegal/reserved
   control mixes.
2. `RV8GR_ClockProfiles`: keep push-switch, random debounced push, 50 kHz,
   1 MHz, 2 MHz, and 5 MHz profiles on every edge-sensitive circuit. Mark
   5 MHz as functional simulation until timing-margin and hardware
   signal-integrity proof exist.
