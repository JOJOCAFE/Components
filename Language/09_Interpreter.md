# 09 — Interpreter

Status: Language Specification v1.0 — frozen design contract.

The interpreter operates on a resolved [Topology](08_Topology_Model.md), never
on raw source or raw AST. It supplies the lifecycle below; a provider may
implement it in Python, Rust, or another host without changing language
meaning.

```text
load -> resolve -> instantiate -> initialize -> schedule -> evaluate
     -> propagate -> settle -> trace/inspect
```

## Required phases

1. **Load** parses source into the AST only.
2. **Resolve** loads schemas, Device Libraries and references, then produces a
   validated immutable Topology.
3. **Instantiate** creates one isolated Device state object per topology
   instance. Library descriptors remain immutable.
4. **Initialize** applies explicit rails, pulls, initial operation inputs, and
   device reset/default state.
5. **Evaluate** calls a device behavior provider when a sensitive net changes.
6. **Propagate** applies the device's scheduled driver changes to nets.
7. **Settle** repeats same-time work under the execution limits in
   [10 Execution Model](10_Execution_Model.md).
8. **Trace** records requested probes and diagnostics without modifying state.

## Determinism and safety

For equal source, libraries, options, and operation sequence, observable
topology values, trace order, and diagnostics must be deterministic. Device
evaluation order must not alter settled results. The interpreter exposes
four-state digital values (`0`, `1`, `Z`, `X`); `X` is a digital unknown, not
an analog-voltage claim.

An interpreter must reject a missing behavior provider for a requested
simulation. It may resolve/view a non-simulatable Device, but cannot invent
behavior. Resource providers are not required for simulation.

Operations are requests against a named resolved Component: inject, step,
run, probe, inspect, validate, and export. They cannot privately mutate a
Device input; every stimulus is an explicit topology driver.
