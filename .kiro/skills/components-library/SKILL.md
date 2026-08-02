# Components Library — Skill Reference

## Project
- Repository: https://github.com/JOJOCAFE/Components
- Path: /home/jo/kiro/Components
- Audience: Students 10–15 years old (usable by older learners up to ~25)

## Mission
- Shared 74HC/memory component library for education
- Visual schematic editor (Components Board) — headless engine + thin clients
- Preserve datasheet truth, real pin behavior, active-low naming, timing limits, tri-state rules, bus ownership

## Architecture (2026-08-02)

```
┌─────────────────────────────────────────────────────────────┐
│            COMPONENTS ENGINE (headless, 969 tests)            │
│  Parser → Executor → Model (source of truth) → JSON state   │
│  Command Registry (OOP groups, aliases, plugins)             │
│  Twin Sync: Visual ↔ Components:circuit ↔ Components:board   │
└────────────────────┬────────────────────────────────────────┘
                     │ JSON state output
    ┌────────────────┼────────────────────────┐
    v                v                v        v
 Browser          CLI (future)    AI/MCP    3D/VR
 (app.html)       (pipe cmds)    (tool)    (future)
```

### Key Principles
- Engine is the single source of truth (no DOM dependency)
- All UI actions = commands (logged, undoable, replayable)
- Three project files are twins: edit one → others auto-update
- Command registry: OOP groups, progressive disclosure (short/dot/tab)
- Plugin architecture: new command libraries `.register()` at runtime

## Three Project Files (Twins)

| File | Owns | Example |
|------|------|---------|
| `Components:circuit` | Electrical truth: devices, nets, connections | `device U1, digital.74HC04;` |
| `Components:board` | Visual layout: placements, routes, labels | `place U1 at (50, 30) rotate 0;` |
| `Components:command` | Command history/log | `[12:01] place U1 at (50, 30)` |

All three use `@page` sections for multi-page projects.

## Board Engine — Complete (Phases 1-5)

| Phase | What | Tests |
|-------|------|------:|
| 1 | Foundation (engine, parser, executor, viewport, config, pages) | 348 |
| 2 | Text Editors (file model, editor state, page sync) | 256 |
| 3 | Tool Plugins (system, select, connect, tray, guide, eraser, label, inspect) | 158 |
| 4 | Print & Export (SVG, PNG meta, title block, fold marks ISO 5457, tiling) | 73 |
| 5 | Integration (presentation mode, command history, twin sync, registry) | 134 |
| **Total** | **13 source modules, 19 test files** | **969** |

## Command Registry (OOP Plugin System)

```js
registry.register(group)        // add command library
registry.execute('file.save')   // dot-notation
registry.execute('save')        // short alias (same result)
registry.complete('file.')      // tab completion
registry.help('file')           // grouped help
```

Built-in groups: `file`, `edit`, `view`, `tool`, `page`, `board`, `circuit`

## Source Modules

```
board/src/model/
  config.js              Paper sizes, grid, export settings
  component.js           Device + connection data model
  board.js               Placement + route + label model
  file.js                Parse/serialize Components:circuit/:board/:command

board/src/view/
  editor.js              DOM-free editor state (cursor, scroll, highlight)
  viewport.js            Coordinate math + render data
  status-bar.js          Tool/cursor/zoom/paper state
  page-tabs.js           Page management
  command-viewport.js    Command CLI + log
  export.js              Print preview, SVG, PNG meta, fold marks, tiling

board/src/controller/
  parser.js              Dual-format text + JSON parser
  executor.js            Stateful executor (undo/redo, pages)
  engine.js              Pluggable composition (middleware, hot-swap)
  tools.js               Plugin system (8 tools, shortcuts, gestures)
  select-tool.js         Select, move, rotate, delete, box-select
  connect-tool.js        Orthogonal wiring, pin-to-pin
  tool-actions.js        Tray, guide, eraser, label, inspect
  sync.js                Page↔editor synchronization
  twin-sync.js           Bidirectional state↔text (MakeCode-style)
  presentation.js        Presentation mode + command history
  command-registry.js    OOP command system (groups, aliases, plugins)
```

## Browser Client (app.html)

Thin client — renders engine state, captures input:
- Tool rail (8 tools, keyboard shortcuts V/L/G/W/E/T/I/.)
- SVG viewport (click select, drag move, connect wires)
- Tabbed editors (Components:circuit | Components:board) — real textareas, editable
- IDLE-style terminal (>>> prompt, tab completion, help)
- File menu (New/Open/Save/Save As/Download/Recent) — Ctrl+N/O/S
- Resizable panels (h/v splitters), collapsible (Ctrl+B)
- Page tabs with sync
- Auto-save to localStorage

## Quality Gates

```bash
# All 969 Board engine tests (headless, no DOM)
cd board && for f in test/*.test.js; do node "$f"; done

# Serve app
cd board && python3 -m http.server 8080
# http://localhost:8080/app.html

# Python chiplib tests
PYTHONPATH=python python3 -B -m pytest tests/ -q

# Crosschecks
python3 tools/pinout_crosscheck.py
python3 tools/timing_crosscheck.py
```

## Team (7-person model)

| Name | Role | Scope |
|------|------|-------|
| Pim | Coordinator | Route tasks, commits, pushes |
| Bank | Architect | Schema, boundaries, contracts |
| Fern | Verifier | Regression, proofs, audit |
| Mint | RTL Coder | Verilog models, HDL export |
| Ohm | HW Coder | Pinout truth, DIP evidence |
| Bam | SW Coder | Python chiplib, Board engine, CLI |
| Noon | Docs Writer | Student guides, labs, cleanup |

## Repo Layout
```
Components/
├── board/                 Board engine + browser client (969 tests)
│   ├── src/model/         Data models (config, component, board, file)
│   ├── src/view/          View state (editor, viewport, export)
│   ├── src/controller/    Logic (parser, executor, engine, tools, sync, registry)
│   ├── test/              19 test files
│   ├── app.html           Interactive browser client
│   └── docs/              11 numbered design docs
├── lib/standard/          Chip definitions (74xx, memory, passive, etc.)
├── python/chiplib/        Python behavior models
├── python/tests/          Python test suite
├── verilog/74xx/          Verilog structural models
├── verilog/memory/        Memory chip Verilog
├── source/                Manufacturer datasheet PDFs
├── examples/circuits/     RV8GR and standalone circuit examples
├── Language/              Component language spec (23+ docs)
├── tools/                 Crosscheck and audit scripts
├── schemas/               JSON schemas
├── docs/                  Team docs, session handoff, design plans
└── .kiro/skills/          This skill file
```

## Non-Negotiable Rules
1. No specialist verifies only their own work — Fern reviews what ships
2. DB, Python, Verilog, pinout evidence, and docs must not drift apart
3. Engine is headless — zero DOM dependency in source modules
4. All UI actions = commands (logged, undoable, twin-synced)
5. Pinouts require manufacturer datasheet + DIP package proof
6. Student clarity is a hard requirement, not a polish pass
7. Command registry is extensible — new features = new groups, not core changes

## Datasheet Policy
- Manufacturer PDFs only (DIP/PDIP package proof required)
- AllDatasheet as locator only, not authority
- Keep cited PDFs in `source/`, remove failed downloads

## Current Status (2026-08-02)
- Board engine: feature-complete, 969 tests, 0 failures
- Browser client: interactive (drag, connect, edit, file menu, terminal)
- Architecture: headless engine + thin client (proven by 969 headless tests)
- Remaining: human first-sight trial (needs real students), zoom/pan, pin visualization

## TODO
- First-sight trial with 13-15 y/o students
- Zoom + pan in viewport
- Pin visualization on devices
- CLI client (headless pipe mode)
- MCP tool adapter (AI integration)
