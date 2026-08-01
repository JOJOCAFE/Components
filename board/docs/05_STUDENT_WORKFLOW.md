# 05 — Student Workflow

**Status:** Specification (2026-07-17)
**Purpose:** How a 13-15-year-old student uses Board step by step.

---

## Goal

Open one Component, understand parts, connect pins, see source change,
run one test, recover from one mistake. First route: IN -> U1 (74HC04) -> OUT.

## One Authority, Three Surfaces

```
Learner action (Drawing / Text / Terminal)
        |
checked source-edit intent or bounded runtime request
        |
Component parser + resolver / runtime service
        |
accepted source patch + refreshed topology
OR visible diagnostic with no change
```

## Before Starting

Board shows: title ("This is a NOT gate..."), Drawing left, text upper-right,
Terminal lower-right, IN/U1/OUT visible, one action: **Try inversion**,
boundary statement about digital-model result.

## A: Inspect a Chip

1. Select U1 -> Learning Lens explains what it does
2. DIP-frame SVG from definition
3. Pin anchors from resolved facts (number, port, direction)
4. Selecting anchor highlights source endpoint

## B: Connect with Mouse

1. Wire tool, press source pin (U1.1Y)
2. Dashed temporary route to pointer (not saved)
3. Release on compatible endpoint (OUT)
4. Board builds: `connect U1.1Y -> OUT;`
5. Pure preview (source unchanged)
6. Show line + Apply / Cancel
7. Apply -> source updated, Board redraws
8. Cancel/Escape -> nothing changed

## C: Connect by Typing

`connect U1.1Y to OUT` or `connect U1.@2 to OUT` (physical pin).
Same preview/Apply route.

## D: Recover from Mistake

1. Red/dashed route, labelled "Not connected"
2. Explanation: what, why, one next action
3. Source/topology/profile unchanged

## E: Run and Understand

1. **Try inversion** or `run inversion`
2. Result: test, values, reason
3. Boundary: digital-model only

## Working Box

- Add part: preview `device` declaration -> Apply
- Add from BOM: batch preview, atomic accept/reject
- Pick and place: one at a time, profile-only

## Delivery Order

1. Add one library part
2. Add batch from BOM
3. Place one part
4. Inspect chip/pins
5. Preview connection
6. Apply or cancel
7. Recover from error
8. Run one test
9. Complete trial without guide
