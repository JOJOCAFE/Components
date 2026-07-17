# 22 — `component:board` Profile Contract

Status: C4.1 prototype checkpoint. The local Board now creates and validates
browser-local `components.board-profile@1` records for placements and existing
scalar-edge routes. It is not a Component-language feature, a server-persisted
exchange implementation, or a completed visual editor. Its normalized top-left
coordinates are legacy prototype data; the frozen Board v2 migration is in
[`../board/docs/BOARD_ARCHITECTURE_FREEZE.md`](../board/docs/BOARD_ARCHITECTURE_FREEZE.md).
C4.2 remains gated on that migration plus resolver, resource-binding,
round-trip, and learner interaction evidence.

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

Coordinates and path points are Board-local presentation data. They neither
create an electrical connection nor prove a PCB route. A physical capture is
an evidence reference, not a simulation input and not an automatic physical
signoff claim. Profile `@1` uses bounded `0..100` top-left coordinates only as
a prototype encoding. The planned successor will declare centered Cartesian
world coordinates explicitly; screen and viewport coordinates never enter the
Component parser or resolver.

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

## C4.1 prototype evidence

The dependency-free local Board consumes the resolver's read-only Board view
and saves only presentation data in browser-local storage. Its profile helper
rejects invalid/non-finite/out-of-range `0..100` coordinates, rejects a route
whose resolved edge is not explicitly scalar, preserves topology identity, and
marks mismatched profiles stale rather than retargeting them. Coordinate and
LOGO-pen paths are normalized to the same Board units and have a deterministic
Node proof in `board/profile.test.mjs`.

This is deliberately still narrower than C4.2: Board profile persistence is
local to the prototype, bus-route/member semantics are not defined, and the
required browser accessibility plus first-sight learner trials remain open.
Before C4.2 extends placement/routing, a new profile version, migration
fixtures, world/viewport transform, and transaction operation path are
required.
