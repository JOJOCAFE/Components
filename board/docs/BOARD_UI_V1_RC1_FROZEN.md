# Components Board UI v1.0 RC1 — Frozen Specification

**Status:** 🟢 Frozen (Release Candidate 1)  
**Date:** 2026-07-27  
**Authority:** This document is the visual contract for all Board UI work.

---

## Design Principles

1. Human First
2. Read Before Learning
3. Maximum Circuit Area
4. Minimal UI
5. Zero Visual Noise
6. Macintosh Spirit, not Macintosh Clone
7. Circuit First, UI Second

---

## Layout

```
+--------------------------------------------------------------+
| Logo  File Edit View Project Simulate Window Help      Clock |
+--------------------------------------------------------------+
| Page Tabs                                                    |
+--------------------------------------------------------------+
|      |                               | Component | Board     |
|      |                               |-----------------------|
|      |                               |                       |
|Tool  |                               |                       |
|Rail  |        Viewport               |   Component Source    |
|      |                               |                       |
|      |                               |                       |
|      |                               |                       |
|      |                               |                       |
+--------------------------------------------------------------+
| Command                                                      |
|--------------------------------------------------------------|
| >                                                            |
+--------------------------------------------------------------+
```

---

## Left Rail (Frozen)

1. Select
2. Library
3. Wire
4. Guide
5. Label
6. Inspect
7. Probe
8. More

**Explicitly excluded:**
- No Eraser
- No Bus Tool
- No Node Tool
- No Rectangle
- No Circle
- No Pan Tool
- No Rotate Tool
- No Mirror Tool

---

## Logo (Frozen)

```
Hexagon → C → Green Dot
```

- Monochrome icon
- Green accent only
- No "Components" word
- Same visual weight as original Macintosh Apple logo
- The logo is the only colored element in the chrome

---

## Top Menu (Frozen)

```
File  Edit  View  Project  Simulate  Window  Help
```

---

## Project Model

- Single Project only (v1)
- Tabs represent **Pages**, NOT Projects
- Example pages: `CPU`, `Memory`, `ALU`, `Front Panel`, `Power`
- Multi-project: future/later

---

## Right Panel

Tabs: `Component` | `Board`

- Component tab → component source editor
- Board tab → board source editor

---

## Bottom Panel

- Title: `Command`
- NOT `component:command` in the UI
- The command language itself is `component:command`
- The UI title is simply **Command**

---

## Scrollbars (Frozen)

- Classic scrollbar style (from previous version)
- Same scrollbar design for: Component editor, Board editor, Command panel
- No modern overlay scrollbar

---

## Viewport

- Priority #1 — everything sacrifices space for the viewport
- Zoom controls only (bottom-right): `+`, `-`, `Fit`
- No permanent pan control
- No floating toolbar
- No extra widgets

---

## Pan/Zoom

- Two-finger gesture
- Mouse wheel
- Space + drag

---

## Color (Frozen)

- Mostly grayscale
- One accent only: **Green** (logo dot, `#007C3D`)
- Simulation colors appear only during simulation
- Never in idle UI

---

## Typography

- UI: Sans-serif
- Source: Monospace

---

## Overall Style

- Minimal
- Calm
- Professional
- Educational
- No gradients
- No glossy buttons
- No Microsoft ribbon
- No IDE feeling
- No CAD feeling

---

## Design Inspiration

Rather than resembling KiCad, Eagle, EasyEDA, or Visual Studio, this UI
intentionally follows the philosophy of early creative tools:

- Macintosh System Software (1984–1991)
- MacPaint
- MacDraw
- HyperCard

Those applications maximized the workspace, minimized interface chrome, and
made the tool disappear so the user's work became the focus. That is exactly
the experience Components should provide.

---

## Rationale

This RC1 is strong enough to be the face of Components for years because it
does not follow Flat UI or Material Design fashion. It follows the principle of
"timeless interface" — aligned with the project goal of learning and reading
circuits rather than flashy UI.
