# Board Architecture Freeze — Viewport, World, and Operations

Status: **frozen for the next Board implementation slice** (2026-07-17).

Components Board is a visual front end for the Component language. It is not a
freehand drawing program and it does not directly mutate the circuit model.
The word **Viewport** is used deliberately: the schematic world exists
independently of the visible window into it.

This freeze supersedes the early prototype's normalized `0..100`, top-left
coordinate system. That implementation remains useful as a narrow interaction
experiment, but it must not be extended into the full editor. Migrate it before
adding broader placement, routing, or transaction features.

## Frozen flow

```text
pointer / stylus / keyboard
        ↓
screen coordinate (device pixels)
        ↓
viewport transform (pan, zoom, visible bounds)
        ↓
world coordinate (x, y)
        ↓
snap, hit-test, selection
        ↓
semantic Operation Generator
        ↓
Transaction Queue
        ↓
validation / resolver / bounded runtime
        ↓
Component and/or Board-profile update
        ↓
re-rendered viewport
```

The parser and resolver know electrical identifiers, never viewport or screen
coordinates. Grid marks are a placement aid, not the coordinate system.

## Coordinate spaces

| Space | Owner | Purpose | Never used for |
| --- | --- | --- | --- |
| Screen | client input/rendering | pixel pointer location and SVG/DOM layout | persisted circuit or Board data |
| Viewport | Board client/session | pan, zoom, visible rectangle, world-to-screen transform | electrical identity or parser input |
| World | `component:board` | persistent part origins, route bends, labels | implied electrical wiring |

World coordinates are Cartesian `(x, y)`: `(0,0)` is the initial viewport
center, positive `x` is right, and positive `y` is up. The unit is initially
named **world unit**, not millimetres; physical units require a later,
evidence-backed package/layout contract. Grid labels adapt to zoom, for example
`100`, `200`, `300`, rather than spreadsheet-style `A/B/1/2` labels.

## Device geometry

Every placed device has a definition-derived visual transform:

```json
{
  "instance_id": "U1",
  "origin": {"x": 0, "y": 0},
  "rotation_deg": 0,
  "bounding_box": {"min_x": -70, "min_y": -45, "max_x": 70, "max_y": 45}
}
```

Pin anchors are calculated by applying that transform to definition/resource
geometry. SVG artwork may draw the frame but never invents a pin, direction,
or electrical endpoint. Rotation is discrete initially (`0`, `90`, `180`,
`270`) unless a later schematic-symbol contract safely widens it.

## Operations and the transaction queue

The Board may propose and display operations; it has no direct model-mutation
path:

```text
Board action → semantic operation → checked queue → service apply → re-render
```

The upper-right panel is therefore a **Transaction Queue**, not merely a code
viewer. It can contain several pending operations and offers **Apply all** or
an explicit discard. Each row shows its authority, target, dependency, exact
Component text when applicable, and diagnostics.

```text
Pending  component.connect.apply  connect U1.1Y -> OUT;
Waiting  board.route              edge:U1.1Y->OUT via (...)
Pending  board.label              "Clock input" at (120,80)
                                        [Apply all] [Discard]
```

One operation still has exactly one authority target. A transaction may contain
dependent operations, but application is ordered and checked:

1. apply source operations against the expected source revision;
2. parse and resolve the resulting topology;
3. refresh its topology digest;
4. apply dependent Board-profile operations only when their referenced edge or
   device exists in that digest; and
5. apply bounded runtime operations only under their own runtime contract.

A failed row changes neither its target nor later dependent rows. This keeps
undo/redo, action recording, collaboration, headless use, and AI assistance on
the same reviewable command path.

## Connection guide and inspection

Dragging from one pin to another creates a source-operation preview, not a
wire. The temporary blue/dashed guide carries an in-viewport label such as
`connect U1.1Y → OUT`, so the learner can understand it without looking away.
After source validation, the same named scalar edge may receive a separate
visual route operation.

**Inspect** opens a semantic inspector, not generic drawing properties. Its
first sections are:

```text
Device · Library · Pins · Ports · Timing · Behavior · References · Connections
```

It reads resolved Component and definition facts. Width, fill, arbitrary color,
and other generic graphics controls are outside this milestone.

## Planned Board profile migration

The shipped prototype currently implements `components.board-profile@1` with
bounded, top-left normalized coordinates. Board v2 will introduce a new
versioned profile only after its schema and migration fixtures exist. Its
placement, route, and label points use world coordinates and it identifies the
coordinate convention explicitly, for example:

```json
"coordinate_space": {
  "id": "world-centered-cartesian@1",
  "origin": "center",
  "x_axis": "right",
  "y_axis": "up",
  "unit": "world"
}
```

The viewport transform is client/session state by default. It may be saved as
optional view metadata for convenience, but does not affect the meaning of the
world data or the resolved circuit.

## Implementation gate

Before extending Board tools, implement and prove all of these together:

1. world/screen transform and center-origin pan/zoom;
2. versioned profile migration/fixtures from the prototype profile;
3. definition-derived origin, rotation, bounding-box, and pin-anchor handling;
4. operation generator and dependency-aware transaction queue; and
5. source-first validation followed by digest-locked Board-profile application.

Do not add auto-routing, bus-route semantics, breadboard/PCB claims, freehand
electrical wires, or direct Board-to-model edits during this migration.
