# 01 — Learner Circuit Direction

**Status:** Product direction (frozen 2026-07-17)
**Purpose:** What Board is, who it's for, and the product commitment.

---

## What Board Is

Board is the **detailed, bidirectional visual editor** for Component language.
It renders Component source as a real pin-by-pin circuit and turns visual
part/pin/wire edits back into exact checked Component code.

- Feel: Canva/MakeCode directness + KiCad pin-level precision
- First audience: students about **13-15 years old**
- First surface: **KiCad-style schematic** (not breadboard)

## Primary Commitment

Both directions are first-class and deterministic:

```
Component source -> parse/resolve -> complete visual circuit
visual edit -> exact source patch preview -> parse/resolve -> refreshed circuit
```

Every meaningful Board gesture has a `Components:command` command equivalent
(like Maya/Blender action history) - explainable, replayable, safely undoable.

## What Students See

- Logical symbols/package frames with pin names and numbers
- Nets, explicit wires, probes, and diagnostics
- No breadboard, no block-only representation
- Select, inspect, and connect individual pins (not vague blocks)
- Logical port names (`U1.1Y`) and physical selectors (`U1.@2`) always visible

## Three Synchronized Views

| View | Feeling | Changes | Never owns |
|------|---------|---------|------------|
| Blocks | MakeCode-like assistance | Checked Component edit intent | Pins, behavior, timing |
| Code | Exact readable source | Component source through parse/resolve | Hidden AST |
| Circuit Board | KiCad-like detailed canvas | Source-edit proposal + profile placement/route | Electrical truth from art |

## Connection Guides

When source declares an edge, Board draws a dashed **connection guide**
between exact endpoints. This tells the student where to draw a clean route.
The guide is NOT a second electrical connection. After routing, only the Board
profile changes.

## First Acceptance Scene

A learner selects NOT gate (74HC04), sees real package/pins and new code,
places U1, connects IN -> U1.1A -> OUT through checked previews, presses
**Try inversion**, and says: "0 becomes 1 because this NOT gate flips the
input." Board also states this is a digital-model result, not breadboard proof.

## Explicitly Not (Now)

- Breadboard/PCB layout (later, separate evidence contract)
- Auto-routing, bus expansion, conflict repair
- Plugin/updater/timeline/waveform/3D prerequisite for NOT-gate route
- Block UI import without frozen Component-to-Design bridge
