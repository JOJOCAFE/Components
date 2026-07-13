# 22 — `component:board` Profile Contract

Status: deferred contract for C4.1.  A Board profile is intentionally not an
implemented language feature or visual editor.  It can be frozen for exchange
only after the C1 resolved-component and C3 Resource-binding contracts are
available to consume.

## Boundary

A Board is a presentation and physical-capture view of exactly one locked,
validated Resolved Component.

```text
Resolved Component + Resource bindings -> Board profile -> visual/physical clients
```

The Board cannot parse Component source into a different machine, create a
Device, create a net, select a Device model, alter pin truth, or supply Device
behavior/timing.  It consumes resolved IDs, scalar-edge IDs, declared
probes/displays, and locked Resource views.  A Board profile is therefore
discardable without changing Component resolution or runtime behavior.

## Canonical interchange shape

`schemas/board-profile.schema.json` defines `components.board-profile@1`.
It contains:

- `topology_ref`: Component ID, resolved-topology schema, and immutable digest;
- `resource_bindings`: references to C3 binding IDs only;
- `placements`: display positions for existing resolved instance/boundary/
  probe/display IDs;
- `routes`: visual paths associated with existing scalar-edge IDs only;
- `widgets`: read-only views associated with existing Probe or Display IDs;
- `physical_captures`: evidence references with scope and status; and
- optional Board title/view metadata.

Coordinates and path points are Board-local presentation data.  They neither
create an electrical connection nor prove a PCB route.  A physical capture is
an evidence reference, not a simulation input and not an automatic physical
signoff claim.

## Hard exclusions

The profile must reject Device definitions, Device parameters, behavior,
timing, pins/ports, Device instances, nets, buses, hidden connections,
drivers, values, clocks, operations, executable callbacks, or arbitrary
runtime state.  A widget is read-only in this contract.  Future controls must
be explicit Runtime Operations and retain their own authority checks.

## Identity and round trip

`topology_ref` is mandatory and identifies the same Component/Topology used by
all Board references.  A Board importer/exporter may reorder presentation
records canonically, but must preserve that reference unchanged.  It must fail
rather than retarget an ID when a Component revision changes its topology
digest.

## Deferred implementation gate

The fixtures in
[`fixtures/component-presentation-contract/`](fixtures/component-presentation-contract/)
prove the closed ownership boundary only.  They do not authorize C4.2.  A
visual editor can begin only when it uses the C1 resolver and C3 bindings,
round-trips source-owned topology unchanged, and exposes resolver diagnostics
instead of silently repairing a Board view.
