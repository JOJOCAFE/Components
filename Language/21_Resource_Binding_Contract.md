# 21 — Resource Binding Contract

Status: proposal for C3.1.  This contract adds presentation bindings to a
validated Resolved Component.  It does not add parser syntax, runtime
behavior, coordinates, routing, or Board state.

## Purpose and ownership

A Resource binding answers only **how an already resolved object is named or
shown**.  It may select a library Resource view, a student-facing label, a
display kind, or an optional package/physical-presentation reference.  It
does not answer what a Device is or how a Component is electrically connected.

```text
Resolved Component + Resource Library -> Resource bindings -> presentation client
```

The binding is an additive presentation record.  Omitting every binding leaves
the Resolved Component, its Topology, and a future Runtime Session identical.
This is the Component-level application of the package ownership rule in
[`../docs/DEFINITION_OWNERSHIP_V0_1.md`](../docs/DEFINITION_OWNERSHIP_V0_1.md).

## Canonical interchange shape

`schemas/resource-binding.schema.json` defines
`components.resource-binding@1`.  A binding record contains:

- one stable binding ID;
- a `target` that references an existing resolved Device instance, Probe, or
  Display by ID;
- a locked Resource definition identity and one of its declared views; and
- optional display-only label, symbol, display-kind, and package text.

Targets are references, never embedded Device records.  A resolver or future
presentation client must reject a missing target, missing Resource view, or a
Resource that does not map the target's resolved Device identity.

## Hard exclusions

Resource bindings must reject fields or equivalent aliases for:

- Device pins, ports, direction, polarity, behavior, model, timing,
  electrical limits, evidence, or test status;
- nets, buses, edges, connections, power rails, drivers, or topology;
- runtime values, events, clocks, operations, callbacks, or state mutation;
- Board coordinates, routing, widgets, or Board-local precedence.

A display kind is a rendering request, not an executable widget.  A future
interactive control must submit a bounded Operation through the Runtime API;
it cannot mutate a Device or net through a Resource.

## Resolution and reproducibility

Bindings resolve after a Component topology is validated.  The resolver locks
the Resource identity and view alongside the Component's Device-library locks,
but does not copy Resource data into Device definitions or executable topology.
Changing a label or selected view may change presentation output only; it must
not change the resolved-topology digest, runtime trace identity, or validation
result.

## Acceptance boundary

The valid and negative examples in
[`fixtures/component-presentation-contract/`](fixtures/component-presentation-contract/)
are checked by:

```bash
python3 -B tools/check_component_presentation_contracts.py
```

They are contract fixtures only.  No Resource binding CLI, visual editor, or
runtime implementation is claimed by this document.
