# Board Profile v2 Contract

Status: **B2.1 frozen**. This is the persisted presentation contract for the
centered Board world. It does not authorize migration, UI adoption, routing
changes, or direct Board mutation; those are B2.2/B2.3 and later operations
sprints.

`components.board-profile@2` describes only how one already-resolved Component
circuit appears. It is digest-locked to that circuit and contains no Component
source, resolved topology, electrical nets, edge creation, runtime values, raw
input events, or viewport/camera state.

```json
{
  "schema": "components.board-profile@2",
  "version": 2,
  "coordinate_space": {
    "id": "world-centered-cartesian@1",
    "origin": "center",
    "x_axis": "right",
    "y_axis": "up",
    "unit": "world"
  },
  "topology_ref": {
    "component_id": "DigitalInverterFixture",
    "schema": "components.resolved-component@1",
    "digest": "sha256:<resolved topology digest>"
  },
  "resource_bindings": [],
  "placements": [],
  "routes": [],
  "labels": [],
  "widgets": [],
  "physical_captures": [],
  "view": {"title": "A NOT gate", "theme": "light"}
}
```

## Coordinate rule

The `coordinate_space` object is mandatory and exact. World origin is centered,
positive x goes right, positive y goes up, and a unit is a non-physical `world`
unit. No bounds are imposed: finite negative and positive coordinates are valid.
Grid and snap are helpers; neither changes this truth.

`view` may retain a title/theme only. Pan, zoom, visible bounds, screen pixels,
or a camera/viewport object are session-local and must not affect a profile
export digest.

## World objects

- A placement names an existing `device-instance`, an `origin`, and one
  discrete `rotation_deg` (`0`, `90`, `180`, or `270`). Bounding-box and pin
  geometry remain definition-derived work for B3.
- A scalar route names a resolved `edge_id` and finite world-point bends. It
  still cannot create an electrical connection. Bus routes remain rejected.
- A label has a stable identifier, finite world `position`, non-empty text,
  and finite `font_size`.

All profile objects remain subject to topology-digest validation when applied.

## Rejections

The validator rejects a missing/wrong coordinate convention, non-finite world
point, stale topology reference, non-discrete rotation, bus route, profile
electrical fields (`source`, `nets`, `edges`, and similar), unknown top-level
fields, and persisted viewport/camera state.

## Compatibility boundary

`@1` is the previous bounded, top-left normalized profile. It remains readable
only through an explicit deterministic `@1 → @2` migration in B2.2; it is not
silently treated as `@2`. The browser continues to use its local compatibility
adapter until that migration is implemented and tested.
