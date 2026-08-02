# 09 — V2 Sprint Plan

**Status:** ⚠️ SUPERSEDED — This Python-based sprint plan (B1.x-B5.x) has been replaced by the Node.js engine-first Board implementation (Phase 1-5, all complete). Kept for historical reference.

**Original Purpose:** Gate 0 through Sprint 5, small reviewable slices.

---

## Progress

- Gate 0: DONE (harness, baselines, thresholds, negative cases)
- Sprint 1 (B1.1-B1.3): DONE (viewport kernel, grid, renderer)
- Sprint 2 (B2.1-B2.2): DONE (profile v2 contract, migration)
- Sprint 2 (B2.3): CODE DONE, needs browser observation
- Sprint 3-5: Not started (superseded by Node.js Phase 3-5, which are complete)

## Guardrails

- `Components:circuit` = electrical source of truth
- Board creates semantic operations only, never mutates directly
- `Components:board` = digest-locked visual world data only
- Screen pixel / SVG path never implies electrical connection
- Passing simulation is not physical signoff

## Sprint 3 — Definition-derived Geometry

| ID | Task | Owner | Accept |
|----|------|-------|--------|
| B3.1 | Placement transform: ID, origin, rotation, bbox | Bank+Bam / Fern | No pin/timing in profile |
| B3.2 | Pin anchor computation from transform | Bam+Ohm / Fern | All 4 rotations deterministic |
| B3.3 | Semantic inspector projection | Bam+Noon / Fern | Reads resolved facts only |

Exit: 74HC04 placed, rotated, every anchor maps to definition pin.

## Sprint 4 — Operations and Queue

| ID | Task | Owner | Accept |
|----|------|-------|--------|
| B4.1 | Versioned operation records | Bam+Bank / Fern | No raw mouse -> durable |
| B4.2 | Queue states (Pending/Waiting/Applied/Rejected) | Bam / Fern | Connect before route |
| B4.3 | Service apply path (no direct mutation) | Bam / Fern | Test fails without operation |
| B4.4 | Queue visibility + labels | Bam+Noon / Fern | Learner can read queue |

Exit: queue connect+route+label, Apply all, reload with same digest.

## Sprint 5 — Integration and Trial

| ID | Task | Owner | Accept |
|----|------|-------|--------|
| B5.1 | Full regression in one command | Fern+Bam | Zero failures |
| B5.2 | First-sight trial (13-15 + adult) | Noon+Pim / Fern | Both complete without guide |
| B5.3 | Freeze baseline and issues | Pim / Fern | Risks explicit |

Exit: machine harness + both human trials pass. Then widen toolset.

## Not in This Sprint

Auto-routing, bus semantics, freehand wires, breadboard/PCB, generic drawing
properties, arbitrary fonts/colors, physical timing claims.
