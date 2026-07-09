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
