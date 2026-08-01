# 04 — Schematic Toolset

**Status:** Phase 1 defined (2026-08-01)
**Purpose:** Tool rail — plugin-based, implement in phases.

---

## Phase 1 Tools (implement first)

| # | Tool | Key | Action |
|---|------|-----|--------|
| 1 | Select | V | Click select, drag move, R rotate, Del delete, box multi-select |
| 2 | Project Tray | L | Browse library, pick to tray, drag from tray to viewport to place |
| 3 | Guide | G | Click node → toggle connection guides (prototype behavior) |
| 4 | Connect | W | Click pin → orthogonal line → turning points → click target pin |
| 5 | Eraser | E | Click → delete device/line/label/node. Shift+click → delete entire net |
| 6 | Label | T | Click blank → create text, click label → edit, drag → move |
| 7 | Inspect | I | Click → show facts, pins, connections (no mutation) |
| 8 | More | . | Plugin overflow menu |

## Connect Tool Rules

- Lines are **orthogonal only** (N/S/E/W, no diagonal)
- Click source pin to start
- Click to place turning points (each becomes a node)
- Each segment strictly horizontal or vertical
- Click target pin to complete
- Turning-point nodes can be dragged in Select mode
- Escape / right-click to cancel

## Project Tray

- Library browser panel (search + categories)
- Pick devices to tray first (like shopping cart)
- Shows reference (U1, U2) + part name
- Drag from tray to viewport to place
- Unplaced items remain visible as reminder

## Eraser Tool

- Click device → remove from source + profile
- Click wire segment → remove that segment
- Click connection → remove from source
- Click label → remove from profile
- Shift+click → delete entire net
- All deletions generate commands, all undoable

## Phase 2 Tools (after Phase 1 proven)

| Tool | Purpose | Gate |
|------|---------|------|
| Probe | Watch live values | Runtime engine ready |
| Measure | Distance in mm | Basic editing works |
| Sim Step | Advance clock | Runtime engine ready |
| Power | VCC/GND symbols | Power net contract |
| Bus | Bundle between ports | Bus contract frozen |
| Annotate | Comments on schematic | Nice-to-have |
| Breadboard | Physical layout view | Breadboard contract |

## Interaction Rules

1. Lines orthogonal only (no diagonal) — turning points are explicit nodes
2. Only one tool active at a time
3. Escape always returns to Select
4. Every tool action generates a command in Command viewport
5. Tool never touches model — only generates commands
6. Tools are plugins (can add/remove/customize)

