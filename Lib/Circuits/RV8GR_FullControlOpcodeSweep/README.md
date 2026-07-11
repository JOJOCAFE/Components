# RV8GR FullControlOpcodeSweep

This circuit package lifts the RV8GR Verilog opcode sweep into the reusable
Components circuit library.

It checks pure T2 execution logic for all 256 opcode values with both starting
Z states. The proof intentionally includes reserved control-bit combinations
because RV8GR is hardwired: physical decode gates still do whatever the bits
ask them to do.

The package does not replace the smaller circuit proofs. It connects them:

- bus ownership and store/load safety
- ALU, AC, and Z update equations
- PG, DP, and IE side effects
- branch and jump PC loading
- virtual helper observation for phase and bus conflicts

The important failure mode is drift. If the Verilog bench, docs, or extracted
circuit equations disagree, this package should fail before the full CPU is
treated as ready.

## Build and test guide

- **Chips and I/O:** This is a virtual control-integration package, not a separate breadboard module. It observes T2 controls, AC/Z, PG/DP/IE, PC load, memory controls, and IBUS/DBUS ownership across all opcode bytes.
- **Isolated manual-clock test:** Before the sweep, hand-step one known LI, store, load, branch, jump, SETPG, SETDP, and EI vector in their smaller module guides.
- **Integration test:** Run the command below; it executes all 256 control bytes with both starting Z states and retains reserved combinations.
- **Pass:** Every vector matches the extracted hardwired equations, all required side effects occur only in T2, and no accepted vector has a bus conflict.
- **Stop:** Treat the first mismatch, unknown output, unintended write, or multiple-driver report as a failure; do not alter the expected result to hide it.
- **Temporary wiring:** None belongs to this virtual package. On hardware, remove all isolated-module switches and tie-offs before attempting equivalent integrated traces.
- **Boundary:** A complete opcode sweep is simulation evidence only; reserved combinations are observed, not endorsed as student instructions, and physical timing remains unproven.

```sh
PYTHONPATH=python python3 -B -m tests.test_lib_circuits
```
