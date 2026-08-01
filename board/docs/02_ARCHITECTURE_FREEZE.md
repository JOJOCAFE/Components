# 02 — Architecture Freeze

**Status:** Frozen (2026-07-17)
**Purpose:** Technical data flow from pointer to rendered circuit.

---

## Frozen Flow

```
pointer / stylus / keyboard
        |
screen coordinate (device pixels)
        |
viewport transform (pan, zoom, visible bounds)
        |
world coordinate (x, y)
        |
snap, hit-test, selection
        |
semantic Operation Generator
        |
Transaction Queue
        |
validation / resolver / bounded runtime
        |
Component and/or Board-profile update
        |
re-rendered viewport
```

Parser and resolver know electrical identifiers, never coordinates.

## Coordinate Spaces

| Space | Owner | Purpose | Never used for |
|-------|-------|---------|----------------|
| Screen | client input/rendering | pixel pointer, SVG/DOM | persisted data |
| Viewport | Board client/session | pan, zoom, visible rect | electrical identity |
| World | `component:board` | origins, route bends, labels | implied wiring |

World: Cartesian (x,y), (0,0) = center of paper, +x = right, +y = up.
Unit = **millimetre (mm)**. Grid labels show mm values.

## Canvas Paper Size

Default A4 landscape (297×210 mm). Configurable: A3, A2, A1, A0.
Paper boundary visible in viewport. Content beyond paper is allowed
(viewport unbounded) but export/print clips to paper.

Configuration stored in `board-config.json` (JSON, shared by render/export/print):

```json
{
  "schema": "components.board-config@1",
  "paper": {"size": "A4", "width_mm": 297, "height_mm": 210, "orientation": "landscape",
            "margin_mm": {"top": 10, "bottom": 10, "left": 10, "right": 10}},
  "grid": {"major_mm": 10, "minor_mm": 2.5, "snap_mm": 1.25, "border_tick_mm": 50},
  "title_block": {"show": true, "project": "", "page_title": "", "author": "", "revision": "1.0"},
  "export": {"dpi": 300, "format": "pdf", "monochrome": false, "include_title_block": true},
  "print": {"scale": "1:1", "tile_to": "A4", "overlap_mm": 15}
}
```

View modes: Edit (grid+tools), Print Preview (paper+title block+borders),
Presentation (circuit only, white). Export: PDF/SVG/PNG. Fold marks for
large paper (A0/A1/A2 → ISO 5457 fold to A4).

## Device Geometry

```json
{
  "instance_id": "U1",
  "origin": {"x": 0, "y": 0},
  "rotation_deg": 0,
  "bounding_box": {"min_x": -70, "min_y": -45, "max_x": 70, "max_y": 45}
}
```

Pin anchors = definition geometry x placement transform.
SVG never invents a pin. Rotation: discrete (0/90/180/270).

## Transaction Queue

No direct model-mutation path:

```
Board action -> operation -> checked queue -> service apply -> re-render
```

Application order:
1. Source operations against expected revision
2. Parse and resolve topology
3. Refresh topology digest
4. Dependent Board-profile operations (only if edge/device exists)
5. Bounded runtime operations under own contract

Failed row blocks dependents and changes nothing.

## Inspect

Semantic inspector: Device, Library, Pins, Ports, Timing, Behavior,
References, Connections. Reads resolved facts only.

## Implementation Gate

Before extending tools, all must work:
1. World/screen transform + center-origin pan/zoom
2. Versioned profile migration with fixtures
3. Definition-derived geometry + pin anchors
4. Operation generator + dependency-aware queue
5. Source-first validation + digest-locked profile
