# Board Guide Operation Contract

Status: frozen reusable Board interaction contract (2026-07-17).

`board.guide.toggle` is the semantic form of a **Guides**-tool node click. It
is a `component:operation`, not a mouse event and not a circuit edit.

```json
{
  "schema": "components.operation@1",
  "version": 1,
  "id": "board.guide.toggle:pin:U1.1Y",
  "kind": "board.guide.toggle",
  "authority": "board_session",
  "target": {"kind": "device-pin", "endpoint": "U1.1Y"},
  "topology_ref": {
    "component_id": "DigitalInverterFixture",
    "schema": "components.resolved-component@1",
    "digest": "sha256:<resolved-topology-digest>"
  }
}
```

Targets are exactly one resolved `device-instance`, `net`, or `device-pin`.
The operation contains no pointer coordinates, screen coordinates, SVG path,
source patch, electrical edge creation, or persistent profile field.

## Frozen rule

The reusable reducer receives resolved scalar wires and current session-visible
edge IDs.

1. Find all declared scalar edges touching the operation target.
2. If every matching edge is visible, remove all of those IDs.
3. Otherwise, add every matching edge ID.
4. Saved `component:board` routes remain drawn independently; this operation
   only controls temporary dashed guides.

This gives the learner a direct rule: click a node to show its group, click it
again to hide its group, and click another endpoint to toggle a shared edge.
Several node groups may remain visible together.

## Ownership and reuse

The one authority is `board_session`. Applying this operation may update only
the Board client’s transient guide-visibility set. It must not mutate
`component:component`, resolved topology, `component:board`, or the viewport.
It is deliberately outside the persisted Board profile and is not a B4
Transaction Queue row yet. Future mouse, stylus, keyboard, macro, AI, or API
clients reuse this same operation shape and reducer rather than recreating
guide logic from raw input events.
