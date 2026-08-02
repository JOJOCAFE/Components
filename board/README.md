# Components Board — first local workbench

This is the smallest real Board client: Drawing is on the left, readable
Component text is upper-right, and a short bounded Terminal is lower-right.
It has no npm dependencies, no plugin host, no network requirement after
startup, and no hidden canvas circuit model.

## Quick Start

```sh
cd board && python3 -m http.server 8080
# Open: http://localhost:8080/app.html
```

## Engine Architecture

```
Engine (headless, 1067 tests, no DOM) → JSON state → Any client
  ├── Browser (app.html) — thin SVG renderer
  ├── CLI (future)
  ├── AI / MCP tool (future)
  └── REST API (future)
```

## Modules

| Module | Purpose | Tests |
|--------|---------|------:|
| `src/model/config.js` | Paper, grid, export config | 29 |
| `src/model/component.js` | Device + connection model | — |
| `src/model/board.js` | Placement + route + label model | — |
| `src/model/file.js` | Parse/serialize Components:circuit/board/command | 133 |
| `src/model/library.js` | Catalog loader, search, filter, browse groups | 36 |
| `src/controller/parser.js` | Command text → structured objects | 87 |
| `src/controller/executor.js` | Apply commands to models (undo/redo) | 98 |
| `src/controller/engine.js` | Pluggable engine (middleware, batch) | 21 |
| `src/controller/tools.js` | Tool plugin system (8 tools) | 53 |
| `src/controller/select-tool.js` | Select, move, rotate, delete, box-select | 30 |
| `src/controller/connect-tool.js` | Orthogonal wiring, pin-to-pin | 37 |
| `src/controller/tool-actions.js` | Tray, guide, eraser, label, inspect | 38 |
| `src/controller/device-tray.js` | Project tray: add/remove/pickup/place/bom | 62 |
| `src/controller/sync.js` | Page↔editor synchronization | 35 |
| `src/controller/twin-sync.js` | Bidirectional state↔text sync | 32 |
| `src/controller/presentation.js` | Presentation mode + command history | 62 |
| `src/controller/command-registry.js` | OOP command system | 40 |
| `src/view/editor.js` | DOM-free editor state | 88 |
| `src/view/viewport.js` | Coordinate transforms, zoom, grid | 37 |
| `src/view/export.js` | Print preview, SVG, PNG meta, fold marks | 73 |
| `src/view/status-bar.js` | Status bar state | 22 |
| `src/view/page-tabs.js` | Page tab state | 22 |

**Total: 1067 tests, 21 test files, 0 failures**

## Device Library + Project Tray

The tray system lets students pick parts from the library and place them on
the board:

```
Library (lib/standard/)  →  Project Tray  →  Board viewport
   (core engine)              (core engine)       (client SVG)
```

- **Library**: tree-style catalog loaded from `lib/standard/` definitions
- **Tray**: add/remove/pickup/place/bom — tracks quantity and placement refs
- **BOM**: load a JSON bill-of-materials → tray resolves parts from library
- **Auto-ref**: U1/R1/C1/D1/Y1/Q1/X1 based on part group/role
- **Auto-position**: finds next free grid cell if no position specified
- **SVG rendering**: 61 chip frame SVGs loaded from `assets/`, with generic
  DIP fallback for parts without artwork

### Terminal commands

```
tray.add 74HC04          — add 1× 74HC04 to project tray
tray.remove 74HC04       — remove from tray
tray.place 74HC04        — place at auto-position
tray.bom [{"part":"74HC04","qty":4}]  — load BOM JSON
tray.export              — export tray as BOM JSON
tray                     — open tray panel
```

## Boundary

- **Core** (`lib/standard/`): definition truth — pins, logic, timing, behavior
- **Client** (`board/assets/`): presentation only — SVG chip frames, gate art

The client reads definitions to know *what* to draw, then maps to asset SVGs
for *how* to draw it. If no asset exists, a generic DIP frame is drawn from
pin count. The engine works headless without any assets.

Interaction proof currently covers pointer and keyboard pin selection, exact
source-edit preview before Apply, Cancel/Escape/`cancel route` recovery, and
typed pin-to-pin commands using that same preview. The machine checks are in
`board/interaction-contract.test.mjs`; the final first-sight acceptance trial
still requires a real 10–15-year-old learner and adult beginner.

Unrouted connections are quiet by default. A normal click on a chip or net is
reserved for its definition/inspection. Choose **Guides** in the left rail,
then left-click a device, net, or precise connection dot to toggle its related
routing guides. The choices accumulate: click three nodes and their guide
groups stay visible together, which lets a learner arrange related paths as a
future bus. While Guides is active, node clicks only toggle guides; they do
not select, inspect, or create a connection. Click a node again to hide only
its connected guide group. When one pin is already visible and its device is
clicked, the device reveals its remaining guides; clicking that device again
removes every guide connected to it. Clicking another endpoint toggles that
edge one by one. A saved Board route remains
visible because it is the learner's drawing, not a temporary guide.
The semantic operation and future-reuse boundary are frozen in
[`docs/07_GUIDE_OPERATION_CONTRACT.md`](docs/07_GUIDE_OPERATION_CONTRACT.md).

The current canvas keeps visual artifacts vector-first: reviewed chip frames
are SVG resources, connection guides/routes are SVG paths, and Board labels
are SVG text. Choose **Label**, then click anywhere in the viewport and type
immediately at that point. Double-click a saved label to edit text directly on
the label itself; click elsewhere to save it, or press Escape to cancel.
Thai, English, and other standard Unicode text are kept as one label object.
Select and left-drag a completed label to move it. Right-click any
viewport object to replace the browser menu with its Board properties; a label
uses a compact properties popup for `1.5..8` size, a 16-colour palette with an
editable hex-code field, bold, italic, and underline. Double-click the label
itself to edit its text; selecting it exposes a resize handle. One label has
one style and color—mixed runs and font-family choice are intentionally
deferred. Labels and routes save only in the digest-locked Board profile; they
do not alter Component source or pin truth.

Mode rule: in **Label** mode, one click on an existing label edits its text and
one click elsewhere finishes the active edit. In **Select** mode, the pointer
tool selects/grabs a label for moving or its corner handle for resizing;
double-click edits its text. Right-click always opens Board properties.

The SVG chip frames are deliberately presentation-only. The Board serves the
no-pin frames through `resources/74hc-chip-frames-no-pins/` when a matching
local frame exists. The older functional-pinout frames remain review assets,
not Board artwork. The resolved Component and package definition remain the
only source for ports, logic, timing, and wiring.

Every visible Board object is connectable at a border node: a 74HC frame uses
its definition-aligned DIP dots; a net such as `Clock` or `OUT`, and a device
without a chip SVG, uses a bordered frame with resolved endpoint dots. These
are the targets for routes and for the **Guides** on/off switch; none creates
an electrical connection by itself.
