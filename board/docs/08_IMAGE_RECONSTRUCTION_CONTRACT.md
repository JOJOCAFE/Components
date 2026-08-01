# 08 — Image Reconstruction Contract

**Status:** Planned (2026-07-17)
**Purpose:** How Board handles schematic image import safely.

---

## Source to Board

- Resolved devices -> placed with library-backed frames
- Resolved connections -> dashed connection guides (not routes)
- Student draws visual route over guide -> profile-only
- Future auto-router may suggest route for existing edge, never create one

## Image to Source + Board (Guided Reconstruction)

1. Keep source image, create candidate overlay
2. Detect: symbols, labels, pins, wires, junctions, net labels
3. Resolve each part against Components library (show confidence)
4. Present candidate source lines beside highlighted regions
5. Require confirmation for low-confidence items
6. Parse/resolve complete candidate -> only valid result = authority

Unlabelled crossings, blurred pins, unknown packages = **Needs review**.

## Exclusions

- No direct image-to-simulation
- No auto-accept wire crossing as junction
- No guessed bus, power, pin, behavior, or timing
- No breadboard/PCB extraction or safety claim
- No source rewrite without review and Apply

## Delivery Order

1. Code-to-Board placement + connection guides
2. Manual route editing + deterministic reload
3. Pin-to-pin source edit creating new guide
4. Image import overlay with correction + resolver gate
5. Optional auto-routing of resolved scalar edges
6. Buses only after member/ownership contract
