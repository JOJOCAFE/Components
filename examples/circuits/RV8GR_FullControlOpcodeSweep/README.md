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

## Explicit hierarchy boundary

The parent now declares every port of `BUS`, `ALU`, `PGDP`, `PC`, and `VT`.
The eight control signals use explicit selectors from the latched U5 control
byte: `IRH[7]` through `IRH[0]` map to `ALU_SUB`, `XOR_MODE`, `MUX_SEL`,
`AC_WR`, `SRC`, `STR`, `BR`, and `JMP`. Shared AC, Z, page/data-page, IRL,
IBUS, and DBUS boundaries are named explicitly. No same-name connection is
inferred by the hierarchy runtime.

`VT` is observation-only. Its current scalar BusProbe ports are deliberately
isolated from the eight-bit physical buses until it receives an explicit
eight-bit probe contract; it cannot drive CPU control or state.

This makes the hierarchy constructible on one Board, but it is **not yet a
live 512-case promotion**. The source-owned operation harness can exercise a
real `/PC_LD` control strobe and the U33/U31 IE state edge. It drives only
`/RST`, `PC_INC`, IRH, IRL, and T2; it deliberately refuses to inject IBUS,
DBUS, AC, Z, PG, DP, IE, or PC. Those are shared bus or state-output
boundaries, so a fixed test source there would hide a real driver conflict.

At the current checkpoint, a live T2 phase correctly fails loud: the powered
flattened model reports U34 and U7 simultaneously driving IBUS. This is a
real composition blocker, not a reason to add a test-only bus driver or mark
the 512-case sweep as live. The harness records that exact category before
any promotion decision.

Before a 512-case live promotion, provide source-backed initializers for
AC/Z, PG/DP, and PC, plus phase-owned ROM/RAM/IBUS/DBUS driver operations.
The existing 512 opcode × Z equation test remains independent proof evidence,
not a substitute for those stateful live vectors or physical timing evidence.

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
