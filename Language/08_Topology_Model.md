# 08 — Topology Model

Status: Language Specification v1.0 — frozen design contract.

Topology is the resolved, executable graph made from a valid AST.  The
interpreter never executes AST syntax directly.  It executes this graph.

## Inputs and output

The resolver consumes the nodes in [03 AST Model](03_AST_Model.md), resolves
names using [04 Name Resolution](04_Name_Resolution.md), checks the types in
[07 Type System](07_Type_System.md), and emits an immutable `Topology`:

```text
AST + libraries + parameters -> validated Topology -> runtime session
```

`Topology` contains stable IDs and source spans for `ComponentInstance`,
`PortEndpoint`, `Net`, `Bus`, `Driver`, `Receiver`, `Clock`, and `Probe`.
It contains model descriptors, not live device state.

## Graph rules

- A Component instantiates Devices from a Device Library; it does not copy
  device behavior into its source.
- A connection resolves to an undirected electrical net. Arrow spelling may
  communicate intent, but does not make an electrical connection one-way.
- A bus is an ordered collection of typed nets. A slice and a concatenation
  expand to concrete lines before execution.
- Each endpoint has one resolved type and direction. Multiple output-capable
  endpoints may share a net only when runtime drive rules permit it.
- Rails, pulls, operations, clocks, and enabled outputs become explicit
  drivers; inputs and probes become receivers/observers.
- No implicit same-name connection, implicit power rail, or inferred bus bit
  is permitted.

Topology construction rejects duplicate drivers that are structurally
impossible, width/type mismatches, unknown ports, unresolved library symbols,
and cyclic aliases. Runtime detects enable-dependent contention.

## Ownership boundary

Topology references Device behavior and Resource presentation by stable IDs.
Resource data may add a view or physical presentation mapping, but cannot
alter port direction, electrical behavior, timing, or net connectivity.
Board/UI is intentionally not part of topology v1.0.
