# Board Guide Operation Contract

Status: **release candidate for the reusable Guides interaction feature**
(2026-07-18). This does not make Board v2 itself a release candidate or pause
its active sprint plan.

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

## Release-candidate boundary and production reminder

The release candidate is limited to this Guides feature:
`board.guide.toggle`, its `board_session` ownership, and the reusable reducer
in `board/guide-operation.js`. Future production clients must reuse this
operation/reducer contract, not implement parallel raw-click guide behavior.

Before promoting **Guides** to a production/release build, Fern must rerun
`node board/guide-operation.test.mjs` independently and review the integrated
client flow. It must still prove that guide clicks leave Component source,
resolved topology, saved Board profiles, routing, selection, and inspection
unchanged. Broader Board work remains governed by
`BOARD_V2_SPRINT_PLAN.md`; its browser and learner-trial gates are separate.

**Pim reminder:** when future work returns to Guides, surface this release
candidate and its reuse boundary before approving a different client, durable
guide state, queue integration, collaboration, or production-release claim.
