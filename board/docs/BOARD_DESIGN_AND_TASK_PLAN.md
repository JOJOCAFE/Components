# Board — Design Document & Task Plan

**Status:** Active (2026-08-01) | **Authority:** This is the single source of truth for Board design.

---

## 1. Vision

Components Board is a **student-friendly KiCad-style schematic editor** for ages 13-15. It renders Component language as a real pin-by-pin circuit and turns visual edits back into exact checked Component code.

- Feel: Canva/MakeCode directness + KiCad precision
- Spirit: Macintosh 1984-1991 (maximize workspace, minimize chrome)
- NOT: breadboard, block-only, IDE, CAD chrome

---

## 2. Architecture

### Engine-First Design

The UI is a **thin client**. All logic lives in the server engine. Like Blender/Maya:

```
User action (mouse/keyboard/voice/AI/CLI)
        |
        v
Tool plugin (gesture interpreter)
        |
        v
Command (text string or JSON)
        |
        v
Engine: parse -> validate -> execute -> update model
        |
        +---> Update Component file (circuit.component)
        +---> Update Board file (circuit.board)
        +---> Render viewport
        +---> Log to Command viewport
```

Every action = a command. The command log = undo stack = macro system = collaboration history.

### Pluggable Module Architecture

The engine composes replaceable modules via dependency injection:

```
createEngine({ parser, executor, middleware })
```

| Module | Contract | Replaceable for |
|--------|----------|-----------------|
| **Parser** | `(text) => {type, ...params}` | Different language, voice, AI format, Thai |
| **Executor** | `.execute(op) => {success, message}` | Different model, simulation, SPICE |
| **Middleware** | `{before, after}` hooks | Readonly, permissions, collaboration, logging |

The engine also supports:
- `run(text)` — parse + execute + log (single command)
- `runBatch(commands[])` — scripting/automation
- `setParser(fn)` — hot-swap parser at runtime
- `addMiddleware(mw)` — add guards/hooks at runtime
- `getState()` — JSON output for any client
- `getLog()` — complete command history with timestamps

**Module contract means:** anyone can build their own parser (voice commands,
Thai language, block-based), their own executor (SPICE simulation, breadboard
physics), or their own client (3D viewer, mobile app, CLI) — as long as they
follow the command/state protocol.

### Data Model

| Layer | File | Owns | Never touches |
|-------|------|------|---------------|
| Component | `circuit.component` | Electrical truth: devices, nets, connections | Visual positions |
| Board | `circuit.board` | Visual layout: placements, routes, labels | Electrical identity |
| Config | `board-config.json` | Paper size, grid, export settings | Circuit data |

Both Component and Board files use `@page` sections for multi-page projects.

### Coordinate System

- Unit: **millimetre (mm)**
- Origin: center of paper
- Axes: +x = right, +y = up
- Grid labels show mm values
- Paper boundary visible in viewport
- Content can extend beyond paper (viewport is unbounded)

---

## 3. UI Layout

```
+--------------------------------------------------------------+
| [C] File  Edit  View  Project  Simulate  Window  Help        | <- Menu bar
+------+---------------------------------------+---------------+
|      | CPU | Memory | ALU | Power | [+]      | Component|Board| <- Page tabs
|      |---------------------------------------|---------------|
|Select|                                       |               |
|Tray  |                                       | Source Editor |
|Guide |        V I E W P O R T               | (monospace)   |
|Conn  |                                       |               |
|Erase |         (clean, no widgets)           |---------------|
|Label |                                       | Command       |
|Inspe |                                       | > _           |
|More  |                                       |               |
+------+---------------------------------------+---------------+
| Select | x: 42.5  y: -15.0 mm | [-] 100% [+] [Fit] | A4 L | <- Status bar
+--------------------------------------------------------------+
```

### Three Viewports

| Viewport | Position | Purpose |
|----------|----------|--------|
| **Main viewport** | Center | Schematic canvas — 100% clean, no widgets |
| **Text editors** | Right | Component + Board source files (separate tabs) |
| **Command** | Right-bottom | Universal command bus (log + CLI input) |

### Status Bar

Left: current tool name. Center: cursor position in mm. Right: zoom (-, %, +, Fit) + paper size.

### Page Tabs (on viewport)

- Tabs above viewport = schematic pages within one project
- [+] creates new page (each page has own paper size)
- Switching page scrolls both text editors to matching `@page` section
- One window = one project. New window = new project.

### View Modes

| Mode | Shows | Hides |
|------|-------|-------|
| Edit (default) | Grid, snap, guides, tools | Title block, fold marks |
| Print Preview | Paper, margins, title block, borders | Grid, guides, tools |
| Presentation | Circuit only, white background | All chrome |

---

## 4. Tool Rail (Plugin Architecture)

Each tool is a **plugin** that interprets gestures and generates commands. Tools never touch the model directly.

### Phase 1 Tools

| # | Tool | Key | Behavior |
|---|------|-----|----------|
| 1 | **Select** | V | Click=select, drag=move, R=rotate, Del=delete, box=multi-select |
| 2 | **Project Tray** | L | Browse library, pick to tray, drag from tray to viewport |
| 3 | **Guide** | G | Click node = toggle connection guides |
| 4 | **Connect** | W | Click pin, orthogonal lines (N/S/E/W only), turning points = nodes, click target pin |
| 5 | **Eraser** | E | Click = delete object, Shift+click = delete entire net |
| 6 | **Label** | T | Click blank = create, click label = edit, drag = move |
| 7 | **Inspect** | I | Click = show definition facts (no mutation) |
| 8 | **More** | . | Plugin overflow menu |

### Connect Tool Rules

- Lines are **orthogonal only** (no diagonal)
- Click source pin to start
- Click to place turning points (each becomes a node)
- Click target pin to complete
- Turning-point nodes can be dragged in Select mode
- Command: `connect U1.1Y -> U2.1A via (85, 30) (85, 60)`

### Project Tray

- Library browser (search + categories)
- Pick devices to tray first (shopping cart)
- Drag from tray to viewport to place
- Unplaced items remain visible as reminder
- Command: `place U1, digital.74HC04 at (50, 30) rotate 0`

### Plugin Contract

```json
{
  "id": "select",
  "name": "Select",
  "icon": "arrow",
  "shortcut": "V",
  "commands": ["select", "move", "rotate", "delete"],
  "gestures": {"click": "select", "drag": "move", "escape": "deselect"}
}
```

Rules: one tool active at a time, Escape returns to Select, tools are loadable from plugin directory.

### Phase 2 Tools (after Phase 1 proven)

Probe, Measure, Simulate Step, Power, Bus, Annotate, Breadboard.

---

## 5. Command Viewport (Universal Command Bus)

Every UI action flows through commands. The Command viewport shows live log:

```
> place U1 at (50, 30)
[12:01] place U1, digital.74HC04 at (50.0, 30.0) rotate 0
[12:01] connect U1.1Y -> OUT
[12:02] route U1.1Y -> OUT via (85, 30) (85, 45)
> _
```

### Input Methods (all produce same commands)

| Input | Example |
|-------|---------|
| Mouse/stylus | Drag pin to pin |
| Keyboard/CLI | Type `connect U1.1Y -> OUT` |
| Shortcut | Ctrl+R = `rotate U1 90` |
| Voice | "connect U1 pin 2 to output" |
| AI assist | "wire the clock" |
| Script/macro | Replay saved sequence |

### Command Log = Everything

- Undo/redo stack (reverse any command)
- Macro system (replay a sequence)
- Collaboration record (who did what)
- AI training data (learn patterns)
- Complete action history (explainable)

---

## 6. Paper & Export

### Paper Sizes

| Paper | mm (landscape) |
|-------|----------------|
| A4 (default) | 297 x 210 |
| A3 | 420 x 297 |
| A2 | 594 x 420 |
| A1 | 841 x 594 |
| A0 | 1189 x 841 |

Orientation: landscape (default) or portrait.

### Title Block (bottom-right)

Project, page title, author, date, revision, paper size, scale.
Visible in Print Preview and export only.

### Export Formats

| Format | Type | Use |
|--------|------|-----|
| PDF | Vector, multi-page | Print, share, archive |
| SVG | Vector, single page | Web, Inkscape |
| PNG | Raster (configurable DPI) | Slides, docs |

### Print Features

- Border frame with 50mm tick marks
- Fold marks (ISO 5457: A0/A1/A2 fold to A4)
- Monochrome option (photocopy-safe)
- Multi-page tiling (A0 -> 4x A4 with overlap + alignment marks)
- Scale indicator in title block

### Configuration (`board-config.json`)

```json
{
  "schema": "components.board-config@1",
  "paper": {
    "size": "A4",
    "width_mm": 297,
    "height_mm": 210,
    "orientation": "landscape",
    "margin_mm": {"top": 10, "bottom": 10, "left": 10, "right": 10}
  },
  "grid": {
    "major_mm": 10,
    "minor_mm": 2.5,
    "snap_mm": 1.25,
    "border_tick_mm": 50
  },
  "title_block": {
    "show": true,
    "project": "",
    "page_title": "",
    "author": "",
    "revision": "1.0"
  },
  "export": {
    "dpi": 300,
    "format": "pdf",
    "monochrome": false,
    "include_title_block": true,
    "include_fold_marks": false
  },
  "print": {
    "scale": "1:1",
    "tile_to": "A4",
    "overlap_mm": 15
  }
}
```

Same JSON drives viewport, export, and print. No config menu (no Microsoft style) -- edit JSON directly or through Command.

---

## 7. File Structure Example

### circuit.component
```
@page CPU
device U1, digital.74HC04;
device U2, digital.74HC161;
connect U1.1Y -> U2.CLK;

@page Memory
device U3, memory.62256;
connect U2.QA -> U3.A0;
```

### circuit.board
```
@page CPU
paper A4 landscape;
place U1 at (50, 30) rotate 0;
place U2 at (120, 30) rotate 0;
route U1.1Y -> U2.CLK via (85, 30) (85, 45) (120, 45);

@page Memory
paper A3 landscape;
place U3 at (80, 50) rotate 0;
```

### Synchronization

- Switch page tab -> viewport shows page + editors scroll to `@page`
- Click device in viewport -> highlights line in Component editor
- Click placement in viewport -> highlights line in Board editor
- Edit Component text -> viewport refreshes (parse/resolve)
- Edit Board text -> viewport refreshes (reload profile)

---

## 8. Design Rules

1. A route is NOT a connection (route = visual, connect = electrical)
2. Lines are orthogonal only (no diagonal)
3. Wires don't connect by visual crossing (explicit connection required)
4. World coordinates are in millimetres
5. Every UI action = a command in the Command viewport
6. Tools never touch the model -- only generate commands
7. Engine is the authority, UI is a thin client
8. One window = one project, tabs = pages
9. No config menu -- JSON config edited directly or via Command
10. Student clarity is a hard requirement
11. Commands accept both human text and JSON (same result either way)
12. Parser, executor, and middleware are pluggable modules (replaceable at runtime)
13. Engine state output is JSON-serializable (any client can render it)
14. No rate limiting -- engine must run at full speed for AI/automation (~100K cmd/sec)
15. Hard page cap: max 100 pages per project (prevents infinite loops)
16. Memory guard: block new pages at 70% of 512MB RSS (prevents system crash)
17. Each page has isolated models -- switching pages shows only that page's content

---

## 9. Task Plan

### Phase 1: Foundation (engine + config + viewport)

| # | Task | Layer | Status | Verify |
|---|------|-------|--------|--------|
| 1.1 | `board-config.json` schema + JSON read/write module | Model | ✅ DONE (29 tests) | Schema validates, load/save round-trips |
| 1.2 | Command parser: text + JSON dual-format into operations | Controller | ✅ DONE (87 tests) | All command types parse, both formats same output |
| 1.3 | Executor: apply commands to Component + Board models | Model+Controller | ✅ DONE (98 tests) | Model updates, rejects invalid, undo/redo works |
| 1.4 | Pluggable engine: compose parser + executor + middleware | Controller | ✅ DONE (21 tests) | Hot-swap parser, middleware blocks/notifies, batch |
| 1.5 | Command viewport: log commands, accept CLI input, send to engine | View | ⬜ TODO | Type command → engine executes → log shows result |
| 1.6 | Viewport renderer: read Board model + config, render SVG/canvas | View | ⬜ TODO | Paper boundary, grid in mm, devices render |
| 1.7 | Status bar: tool name, cursor mm position, zoom controls, paper size | View | ⬜ TODO | Updates live on pointer move and zoom |
| 1.8 | Page tabs: create/switch/rename pages, each with own config | Controller+View | ⬜ TODO | New page works, switch updates viewport + editors |

**Phase 1 progress: 4/8 tasks done, 235 tests passing.**

Implementation order for remaining tasks: 1.5 → 1.6 → 1.7 → 1.8

Files completed:
```
board/src/model/config.js          ← 1.1 (paper sizes, validation, CRUD)
board/src/model/component.js       ← 1.3 (devices, connections)
board/src/model/board.js           ← 1.3 (placements, routes, labels)
board/src/controller/parser.js     ← 1.2 (text + JSON dual parser)
board/src/controller/executor.js   ← 1.3 (stateful, undo/redo, pages)
board/src/controller/engine.js     ← 1.4 (pluggable composition)
board/board-config.json            ← 1.1 (default config)
board/test/config.test.js          ← 29 tests
board/test/parser.test.js          ← 87 tests
board/test/executor.test.js        ← 98 tests
board/test/engine.test.js          ← 21 tests
```

### Phase 2: Text Editors (Component + Board)

| # | Task | Verify |
|---|------|--------|
| 2.1 | Component editor: load/save circuit.component, syntax highlight | File loads, edits trigger viewport refresh |
| 2.2 | Board editor: load/save circuit.board, syntax highlight | File loads, edits trigger viewport refresh |
| 2.3 | Page sync: switch tab scrolls both editors to `@page` section | Click tab -> editors jump to right position |
| 2.4 | Viewport-to-editor highlight: click device -> highlight source line | Click U1 in viewport -> Component highlights `device U1` |

### Phase 3: Tool Plugins

| # | Task | Verify |
|---|------|--------|
| 3.1 | Plugin system: register/activate/deactivate tools, bind shortcuts | Tool loads, shortcut activates, Escape -> Select |
| 3.2 | Select tool: click select, drag move, R rotate, Del delete, box select | All gestures generate correct commands |
| 3.3 | Project Tray: library browser, pick to tray, drag to place | Device appears in tray, drag places on viewport |
| 3.4 | Guide tool: click node toggles connection guides | Guides show/hide per existing prototype behavior |
| 3.5 | Connect tool: orthogonal lines, turning points, pin-to-pin | Line draws N/S/E/W only, completes connection |
| 3.6 | Eraser tool: click delete, shift+click delete net | Object removed, command logged, undoable |
| 3.7 | Label tool: create, edit, move text labels | Label appears, editable, draggable |
| 3.8 | Inspect tool: click shows definition facts | Panel shows pin info, no mutation |

### Phase 4: Print & Export

| # | Task | Verify |
|---|------|--------|
| 4.1 | Print Preview mode: paper + margins + title block + border ticks | Matches config, no grid/tools visible |
| 4.2 | PDF export: vector, clips to paper, includes title block | Clean PDF at correct mm dimensions |
| 4.3 | SVG export: single page vector output | Valid SVG, correct coordinates |
| 4.4 | PNG export: raster at configured DPI | Correct resolution, transparent option works |
| 4.5 | Fold marks + multi-page tiling for large paper | A0 tiles to 4x A4 with overlap marks |
| 4.6 | Monochrome option | Grayscale output, photocopy-safe |

### Phase 5: Integration & Human Trial

| # | Task | Verify |
|---|------|--------|
| 5.1 | Full regression: all machine tests pass in one command | Zero failures |
| 5.2 | Presentation mode: clean white, circuit only | No chrome visible |
| 5.3 | Undo/redo from command log | Reverse any action, replay works |
| 5.4 | First-sight trial: 13-15 y/o + adult beginner | Both complete NOT-gate without guide |
| 5.5 | Freeze baseline and document remaining issues | No false claims |

### Phase 6: Security & Multi-Agent (after v1.0)

| # | Task | Verify |
|---|------|--------|
| 6.1 | Authentication protocol: identify who/what is sending commands (human/AI/app/bot) | Token-based auth, engine rejects unsigned commands |
| 6.2 | Permission levels: read-only viewer, editor, admin, engine-to-engine | Role check before execute, unauthorized commands blocked |
| 6.3 | Agent identity: each connected client/AI has an ID in command log | Log shows who executed each command |
| 6.4 | Session management: connect/disconnect, token expiry, re-auth | Stale sessions rejected, no zombie connections |
| 6.5 | Command signing: verify command origin (prevent injection from untrusted source) | Unsigned/tampered commands rejected |
| 6.6 | Multi-agent coordination: lock pages/objects when being edited | Conflict detection, reject conflicting edits |
| 6.7 | Audit trail: who did what, when, from where (exportable) | Full history with agent identity, exportable JSON |

---

## 10. Success Criteria

Board v1.0 is complete when:

1. A 13-15 year old can place a NOT gate, wire it, try it, recover from error -- without a guide
2. An adult beginner can do the same
3. All machine tests pass
4. Every Board edit produces a command in Command viewport
5. Every command can be typed manually with same result
6. Export produces correct PDF/SVG/PNG at configured paper size
7. No physical/timing/safety claims are made
