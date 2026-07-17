# Board Canvas Prototype Scope

Status: first visual/interaction prototype. This is deliberately smaller than
the complete Board direction: prove the one large schematic viewport and the
three Component layers before adding library browsers, full routing, image
recognition, buses, or physical-layout views.

## Screen

```text
+----------+--------------------------------------+------------------+
| tools    |                                      | Component code   |
| Select   |                                      | generated/edited |
| Place    |       large clear schematic viewport +------------------+
| Connect  |       mouse + stylus first           | instruction /    |
| Inspect  |                                      | transaction queue|
+----------+--------------------------------------+------------------+
```

- **Center:** the dominant clean KiCad-style viewport. It maps screen input
  through pan/zoom to centered Cartesian world coordinates; its grid is snap,
  never spreadsheet coordinates.
- **Left:** five labelled tools: Select, Place device, Connect, Label, Inspect.
- **Right top:** a compact transaction queue showing generated Component code
  and Board actions, with multiple pending rows and **Apply all**.
- **No right bottom panel** in this prototype.

No need to place every library device or finish every editor command in this
version. The prototype must make the canvas feel spacious, precise, and safe
for a 13–15-year-old student.

`BOARD_SCHEMATIC_TOOLSET.md` records the fuller tool rail. The prototype keeps
the rail intentionally small; grid/snap, pan/zoom, and Escape/cancel behavior
support those four tools without occupying extra permanent buttons.

## Minimal actions and layer results

| Student action | `component:operation` | Resulting layer |
| --- | --- | --- |
| Pick **Place device**, click canvas | `board.place-preview` then `board.place` | `component:board` position; if new, show a pending source declaration. |
| Drag pin to pin, release | `component.connect.preview` | Proposed `component:component` `connect` line; no circuit change yet. |
| Press **Apply** | `component.connect.apply` | Source resolves, Board refreshes, then dashed route guide appears. |
| Draw over a dashed guide, finish | `board.route` | `component:board` route points only. |
| Choose Label, click, type one/more lines, set size | `board.label` | SVG Board-profile label only. |
| Click **Inspect** then a pin/part | `board.inspect` | Right panel explains library pin/part facts; no mutation. |
| Press Escape | `board.cancel` | Transient guide/preview disappears; source/profile unchanged. |

Every queued or accepted operation appears in the upper-right queue and carries
the source revision or topology digest required by its target. The queue makes Board use
teachably scriptable without exposing arbitrary Python or recording every raw
pointer move.

## Prototype acceptance scene

Start with one supplied `74HC04` instance and `IN`/`OUT` nets. A student can:

1. see the empty spacious canvas and the real package/pin anchors;
2. select **Connect**, draw from `U1.1Y` to `OUT`, and read the generated
   Component source proposal;
3. apply it, see its dashed guide, then draw a clean visual route over it;
4. read the operation log showing the source operation and Board route as
   distinct actions; and
5. cancel a mistaken attempt without creating a hidden wire.

## Explicitly later

- full part catalogue/Working Box/BOM;
- auto-routing, bus routing, image reconstruction, waveform/timeline, and
  full undo/redo history;
- breadboard or PCB/physical-layout views; and
- broad simulation controls beyond one bounded test/probe explanation.
