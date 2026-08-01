# 06 — Profile v2 Contract

**Status:** Frozen (B2.1, 2026-07-17)
**Purpose:** Persisted presentation contract for centered Board world.

---

## Schema

```json
{
  "schema": "components.board-profile@2",
  "version": 2,
  "coordinate_space": {
    "id": "world-centered-cartesian@1",
    "origin": "center", "x_axis": "right", "y_axis": "up", "unit": "mm"
  },
  "topology_ref": {"component_id": "...", "digest": "sha256:..."},
  "placements": [],
  "routes": [],
  "labels": [],
  "view": {"title": "...", "theme": "light"}
}
```

## Rules

- `coordinate_space` mandatory and exact
- Origin = center of paper, +x = right, +y = up, unit = **millimetre (mm)**
- No bounds (finite negative/positive valid — content can extend beyond paper)
- `view` retains title/theme only (no pan/zoom/camera)
- Viewport state is session-local, never in digest

## World Objects

- **Placement**: device/net, origin, rotation_deg (0/90/180/270)
- **Route**: resolved edge_id + finite world-point bends (no connection creation)
- **Label**: stable ID, finite position, non-empty text, finite font_size

All subject to topology-digest validation.

## Rejections

Missing coordinate convention, non-finite point, stale topology, non-discrete
rotation, bus route, electrical fields, persisted viewport state.

## Migration from @1

`world_x = (v1_x - 50) * 6`, `world_y = (50 - v1_y) * 6`

Deep-copied source profile as evidence. Digest validated before conversion.
Never silently treats @1 as @2.
