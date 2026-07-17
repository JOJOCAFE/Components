# Board Schematic Toolset

Status: proposed tool inventory for the 13–15-year-old, KiCad-style Board.
This is a schematic editor, not a breadboard interface. It takes precision
from KiCad and directness from Tinkercad, while every meaningful action maps to
`component:component`, `component:board`, or `component:operation`.

## Tool rail: start small, grow safely

The first visual prototype keeps only **Select**, **Place device**,
**Connect**, and **Inspect**. The following tools are the full schematic
editor target, grouped so an early student is not presented with a CAD wall.

| Tool | Student action | Component mapping | Initial status |
| --- | --- | --- | --- |
| Select | Click, box-select, Escape to leave a tool. | `board.select`; session-only. | Prototype now. |
| Pan / Zoom / Fit | Move around a large grid; pinch/wheel; fit circuit. | `board.pan`, `board.zoom`; view only. | Prototype now. |
| Grid / Snap | Toggle visible grid and snap to pins/guide points. | `board.set-grid`; presentation only. | Prototype now. |
| Place device | Pick a library part, place its real symbol/package. | preview/apply `component.add-device`, then `board.place`. | Next. |
| Move / Drag / Rotate | Reposition or rotate a placed symbol. | `board.move` / `board.rotate`; profile only. | Next. |
| Connect / Wire | Start at an exact pin, preview `connect`, Apply, then draw a route over its guide. | `component.connect.preview/apply`, then `board.route`. | Prototype now / deepen next. |
| Wire posture | Choose 90°, 45°, or free-angle visual route bends. | `board.set-wire-posture`, `board.route`; profile only. | Next. |
| Edit route | Drag a bend, add/slice/delete a segment. | `board.route`; profile only. | Next. |
| Text label | Add one/multiple visible note lines and adjust size (no font/color choice yet). | `board.label`; SVG Board-profile text only. | Prototype now. |
| Net label | Name a declared net and attach its label visibly. | preview/apply `component.add-net`; Board stores label position. | Next. |
| Junction | Explicitly confirm an intended wire meeting. | checked source/net membership operation; never infer crossing. | After net contract. |
| No-connect | Mark an intentionally unused resolved pin. | later checked Component declaration plus Board marker. | Deferred: language syntax first. |
| Power / ground | Place a declared power/ground net symbol. | checked named-net/source operation; no physical power claim. | Deferred: power policy first. |
| Inspect / Properties | Select a part, pin, net, or route to see source, real pin facts, and diagnostics. | `board.inspect`; no mutation. | Prototype now. |
| Highlight net | Show all resolved edges for one selected net. | `board.highlight-net`; view only. | Next. |
| Undo / Redo | Reverse one safe semantic action. | `component.undo` or `board.undo` through operation inverse. | Next. |
| Run / Step / Watch | Run a declared test, single bounded step, or read a probe. | `runtime.run-test`, `runtime.step`, `runtime.probe`. | Small **Try** action now; expand later. |

## Essential interaction rules

1. **Wires do not connect by visual crossing.** A source connection or an
   explicit reviewed junction is required. This preserves real circuit truth.
2. **Pins and guides snap.** The canvas may look simple, but placing and
   routing snaps to resolved pins, edge endpoints, and the schematic grid.
3. **A route is not a connection.** Connecting changes Component source after
   preview/Apply; routing describes only its Board path.
4. **Every tool has a text/operation equivalent.** Gesture, shortcut, and
   operation history invoke the same checked intent.
5. **The tool stays active until Escape/cancel.** This follows KiCad’s clear
   mode model while the current mode is always visibly named for students.

## Student-first presentation

Borrow the useful beginner pattern from Tinkercad: a small named palette,
starter circuits, direct placement, and one clear **Try** action. Keep the
actual canvas schematic-grade: no breadboard, arbitrary coloured blocks, or
hidden “smart wiring.” Contextual hints appear next to the selected tool, not
as a permanent tutorial wall.

## Source inspiration

- KiCad Schematic Editor: symbol placement; wire drawing from pins; 90°/45°/
  free wire posture; move versus drag; grid/snap; labels; junctions; explicit
  no-connect flags; net highlight; and cancel-to-selection behavior.
- Tinkercad Circuits: direct components palette, starter circuits, edit/remix
  path, and one visible simulation action.

The Board adopts these interaction ideas, not their data models. Component
source, the resolved library facts, Board profile, and the operation contract
remain the authority boundaries.
