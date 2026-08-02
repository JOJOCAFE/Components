# 03 — UI Specification (Frozen RC1)

**Status:** Frozen (2026-07-27)
**Purpose:** Visual contract for all Board UI work.

---

## Design Principles

1. Human First
2. Read Before Learning
3. Maximum Circuit Area
4. Minimal UI
5. Zero Visual Noise
6. Macintosh Spirit, not Macintosh Clone
7. Circuit First, UI Second

## Layout

```
+--------------------------------------------------------------+
| [C] File  Edit  View  Project  Simulate  Window  Help        |
+------+---------------------------------------+---------------+
|      | CPU | Memory | ALU | Power | [+]      | Component|Board|
|      |---------------------------------------|---------------|
| Tool |                                       | Source Editor |
| Rail |        V I E W P O R T               |               |
|      |         (clean, no widgets)           |               |
|      |                                       |---------------|
|      |                                       | Command       |
|      |                                       | > _           |
+------+---------------------------------------+---------------+
| Select | x: 42.5  y: -15.0 mm | [-] 100% [+] [Fit] | A4 L |
+--------------------------------------------------------------+
```

## Tool Rail (8 tools — plugin-based)

1. Select (V)  2. Project Tray (L)  3. Guide (G)  4. Connect (W)
5. Eraser (E)  6. Label (T)  7. Inspect (I)  8. More (.)

Tools are plugins. Only one active at a time. Escape → Select.
Connect lines are orthogonal only (N/S/E/W, no diagonal).
Every tool action generates a command in the Command viewport.

## Page Tabs (on viewport, not global)

- Tabs above viewport = pages within one project
- [+] on rightmost creates new page
- Each page has own paper size and Board profile
- Pages share one project source
- Window = separate project (File -> New Window)

## Status Bar

Left: tool name. Center: cursor position in mm. Right: zoom (-, %, +, Fit) + paper size.
No zoom controls in viewport. Keyboard Ctrl+=/- and wheel/pinch still work.

## Logo

Hexagon + C + Green Dot. Monochrome, no text. Same weight as Mac Apple logo.

## Top Menu

File  Edit  View  Project  Simulate  Window  Help

## Project Model

- v1: Single Project only
- Tabs = Pages (CPU, Memory, ALU, Front Panel, Power)

## Right Panel — Two Separate Files

Tabs: `Component` | `Board` — each connected to a **separate file**.

- Component tab → `Components:circuit` (electrical: devices, nets, connections)
- Board tab → `Components:board` (visual: placements, routes, labels)

Both files have `@page` sections. Switching viewport page tab scrolls both
editors to the matching `@page` position. Click device in viewport → highlights
line in Component. Click placement → highlights line in Board.

## Bottom: Command Viewport (Universal Command Bus)

Like Blender's console or Maya's Script Editor — every Board action flows
through commands. The Command viewport shows the live command log:

- Every mouse click, drag, shortcut → generates a command → logged here
- User can type commands directly (CLI mode)
- Voice and AI assistant also produce commands
- The log = undo stack = macro system = collaboration history

All inputs (mouse, keyboard, voice, AI, script) produce the same command
format. The UI is a thin client; the engine processes commands and renders
results back to the viewport.

UI title: **Command**. Language is `component:command`.

## Viewport

Priority #1 — 100% clean, no floating widgets or overlays.
Pan: two-finger / wheel / Space+drag. Zoom: status bar controls or Ctrl+=/-.
Grid labels: millimetres (mm). Paper boundary visible (default A4 landscape).
Zoom controls are in the status bar, NOT in the viewport.

## Color

Grayscale + one accent: Green (#007C3D) for logo dot only.
Simulation colors only during simulation.

## Typography

UI: Sans-serif. Source: Monospace.

## Style

Minimal, calm, professional, educational.
No gradients, glossy, ribbon, IDE feeling, CAD feeling.

## Inspiration

Macintosh System Software 1984-91, MacPaint, MacDraw, HyperCard.
Maximize workspace, minimize chrome, make tool disappear.
