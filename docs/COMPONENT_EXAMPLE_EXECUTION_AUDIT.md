# Component Example Execution Audit

Date: 2026-07-13.  This is an executable status snapshot, separate from the
Language coverage audit.  It records what was actually tested one source at a
time without promoting a package merely because its topology is expressible.

## Commands

Five root legacy topology examples were individually validated with:

```bash
PYTHONPATH=python python3 -B -m chiplib.cli validate <example>.json
```

All five passed: `nand`, `counter`, `bus_transceiver`, `memory_read`, and
`tiny_cpu_slice`.

Every package `examples/circuits/RV8GR_*/circuit.json` was individually loaded
and live-audited through `chiplib.circuit_proofs.audit_all_packages()`.  The
full 118-check regression also passed:

```bash
PYTHONPATH=python python3 -B -m tests.test_lib_circuits
```

## Per-package live-audit result

| Package | Result | Reason when not promoted |
|---|---|---|
| RV8GR_AluAccumulator | promoted | — |
| RV8GR_BranchJumpControl | promoted | — |
| RV8GR_BusOwnership | promoted | — |
| RV8GR_IRQLatch | promoted | — |
| RV8GR_ResetClockBringup | promoted | — |
| RV8GR_RingCounter | promoted | — |
| RV8GR_RomDbusRead | promoted | — |
| RV8GR_StorePath | promoted | — |
| RV8GR_AddressMux16 | blocked | unresolved output mapping |
| RV8GR_DataPageMemory | blocked | unresolved output mapping |
| RV8GR_FetchCycleTrace | blocked | unresolved output mapping |
| RV8GR_InstructionLatch | blocked | unresolved output mapping |
| RV8GR_PageDataRegisters | blocked | unresolved output mapping |
| RV8GR_InterruptEnable | blocked | proof adapter not implemented |
| RV8GR_InterruptTrace | blocked | unsupported port direction |
| RV8GR_PC16 | blocked | ambiguous symbolic width |
| RV8GR_BootSequenceTrace | blocked | composite not executable |
| RV8GR_FullControlOpcodeSweep | blocked | composite/boundary transforms not executable |
| RV8GR_Lab13MarkerTrace | blocked | composite and range/output issues |
| RV8GR_PageJumpTrace | blocked | composite not executable |
| RV8GR_StoreLoadBranchTrace | blocked | composite and ambiguous range width |
| RV8GR_WholeSystemChipLevelVirtual | blocked | composite children and unresolved outputs |
| RV8GR_VirtualTestHelpers | promoted | — |

## Meaning

This is not a product failure: the blocked entries have structural JSON,
proof-file, and regression coverage, but they do not yet have an independent
live `CircuitRunner` proof adapter.  The Component System Profile therefore
keeps their graph/interface model in `component:component` while deferring
execution and composite orchestration to later resolver/Operation work.

Do not turn `blocked` into `promoted` without a source-backed child interface,
an executable proof adapter, and a shell-failing test.
