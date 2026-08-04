# Components Board — thin client for the Components engine

Board is a **thin client** of the Components core engine. It owns no circuit
model, no chip behavior, and no electrical truth. It sends commands, reads
state, and renders SVG.

```
Components Engine (python/chiplib/)
  owns: Device Library, parse, resolve, simulate, validate, export
    │
    ▼  component:operation / JSON state
    │
Board (this directory)
  owns: viewport rendering, interaction, drag/place, visual editing
  reads: engine state → SVG
  writes: commands → engine
```

This is the smallest real Board client: Drawing is on the left, readable
Component text is upper-right, and a short bounded Terminal is lower-right.
It has no npm dependencies, no plugin host, no network requirement after
startup, and no hidden canvas circuit model.

## Engine Interface Boundary

Board communicates with the Components engine exclusively through
`src/engine-interface.js`. This is the **only** import path for circuit state
and mutations. Board never parses device/connect syntax, never generates
circuit source, and never holds its own topology model.

```
Board code ──► engine-interface.js ──► adapter (mock or real)
                (reads state, submits operations)
```

### File classification

| File | Status | Role |
|------|--------|------|
| `src/engine-interface.js` | **Permanent** | Contract — Board's only engine import |
| `src/engine-interface.md` | **Permanent** | Contract specification |
| `src/engine-mock.js` | **TEMPORARY** | Local adapter wrapping component.js/file.js |

The mock exists so Board development can proceed without the real Python
Components engine adapter. It fulfils the same contract and will be replaced.

### Phase B swap (what happens when the real engine is ready)

1. Write a new adapter (e.g. `engine-http.js` or `engine-wasm.js`) that
   implements `{ getState, submit, submitBatch }`.
2. Pass it to `createEngineInterface(adapter)` instead of the mock.
3. Delete `engine-mock.js` (and its `component.js`/`file.js` imports).
4. **Zero Board code changes** — executor, tools, tray, tests all keep working.

The contract is version-locked: `components.component-operation@1`. Both
sides must agree on that format string before operations are exchanged.

## Quick Start

```sh
cd board && python3 -m http.server 8080
# Open: http://localhost:8080/app.html
```

## Engine Architecture

Board's internal engine is also headless (no DOM). The browser is just one
possible renderer:

```
Board Engine (headless, 1122 tests, no DOM) → JSON state → Any client
  ├── Browser (app.html)  — thin SVG renderer
  ├── CLI (future)        — terminal commands
  ├── AI / MCP (future)   — agent adapter
  └── REST API (future)   — JSON over HTTP
```

This is the **Board-local** engine for layout state. The **Components core
engine** (python/chiplib/) owns circuit resolution and simulation separately.

## Modules

| Module | Purpose | Tests |
|--------|---------|------:|
| `src/engine-interface.js` | **THE** engine boundary — Board's only import for circuit state/ops | — |
| `src/engine-mock.js` | ⚠️ TEMPORARY mock adapter (wraps component.js locally) | — |
| `src/model/config.js` | Paper, grid, export config | 29 |
| `src/model/component.js` | Device + connection model (used by mock only) | — |
| `src/model/board.js` | Placement + route + label model | — |
| `src/model/file.js` | Parse/serialize Components:circuit/board/command | 133 |
| `src/model/library.js` | Catalog loader, search, filter, browse groups | 36 |
| `src/model/catalog-loader.js` | Auto-fetch definitions from lib/standard at startup | 22 |
| `src/controller/parser.js` | Command text → structured objects | 87 |
| `src/controller/executor.js` | Apply commands to models (undo/redo), delegates to engine | 98 |
| `src/controller/engine.js` | Pluggable engine (middleware, batch) | 21 |
| `src/controller/tools.js` | Tool plugin system (8 tools) | 53 |
| `src/controller/select-tool.js` | Select, move, rotate, delete, box-select | 30 |
| `src/controller/connect-tool.js` | Orthogonal wiring, pin-to-pin, toOperations() | 37 |
| `src/controller/tool-actions.js` | Tray, guide, eraser, label, inspect | 38 |
| `src/controller/device-tray.js` | Project tray: add/remove/pickup/place/bom, toOperation() | 62 |
| `src/controller/drag-place.js` | Drag-to-place: drag from tray/library onto viewport | 33 |
| `src/controller/sync.js` | Page↔editor synchronization | 35 |
| `src/controller/twin-sync.js` | ⚠️ DEPRECATED — bidirectional state↔text sync | 32 |
| `src/controller/presentation.js` | Presentation mode + command history | 62 |
| `src/controller/command-registry.js` | OOP command system | 40 |
| `src/view/editor.js` | DOM-free editor state | 88 |
| `src/view/viewport.js` | Coordinate transforms, zoom, grid | 37 |
| `src/view/export.js` | Print preview, SVG, PNG meta, fold marks | 73 |
| `src/view/status-bar.js` | Status bar state | 22 |
| `src/view/page-tabs.js` | Page tab state | 22 |

**Total: 1260 tests, 24 test files, 0 failures**

## Device Library + Project Tray

Parts flow from the core engine's Device Library into the Board through the
tray system:

```
lib/standard/ (core — Device Library, owns chip truth)
    │  fetch definition.json at startup
    ▼
catalog-loader → Library model (search, filter, browse)
    │  student picks parts
    ▼
Project Tray (add, quantity, ref designators)
    │  place command
    ▼
Board viewport (SVG rendering from board/assets/)
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
