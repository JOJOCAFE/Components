# 15 — Interpreter Implementation Guide

Status: Language Specification v1.0 — implementation guidance.

Implement the runtime as separable stages:

```text
AST -> resolver -> typed immutable topology -> session instantiation
    -> event kernel -> trace/diagnostics
```

Keep compilation immutable and reusable; put signal values, queued events,
Device state, clocks, operation sources, histories, and diagnostics in an
isolated execution session. Resolve every endpoint to concrete Device ports
before starting the event loop. Use explicit drivers for test injection and
operations—never private mutation of an input.

The event kernel follows [10 Execution Model](10_Execution_Model.md): atomic
same-time changes, deterministic four-state resolution, delta settlement,
edge-triggered state commits, and bounded execution. Device adapters own only
their declared behavior and schedule outputs through the kernel. Resource
adapters are optional observers/rendering inputs and cannot modify simulation.

Required test layers: Device unit behavior; resolver/topology fixtures; net
resolution and contention; clock/edge/delay traces; deterministic replay;
operation integration; and compatibility tests against current Components DB,
Python models, and generated Verilog where an equivalence contract exists.
Do not implement Board/UI in this phase. Do not claim physical PCB timing from
the digital event result.
