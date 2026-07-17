# Board v2 Sprint Plan — Harness Before Growth

Status: active task plan. **Gate 0 is complete: the reviewed 25-sample
baseline and regression guard are tracked. B1.1/B1.2 are complete as pure,
tested transform/grid kernels. B1.3 now renders through the centered
world/viewport transform, with the existing `@1` top-left profile adapted only
at the UI boundary until Sprint 2 migration. B2.1/B2.2 have frozen and
validated `components.board-profile@2` plus deterministic `@1 → @2` migration;
current next task: B2.3, adopt world points in the persisted Board profile.**
This plan implements
[BOARD_ARCHITECTURE_FREEZE.md](BOARD_ARCHITECTURE_FREEZE.md) in small,
independently reviewable slices. A sprint cannot advance merely because the
screen looks correct: it must pass its machine harness and its stated human
checkpoint.

## Guardrails for every task

- `component:component` remains electrical source of truth.
- Board creates semantic `component:operation` records only; it never mutates
  source, resolved topology, or a saved profile directly.
- `component:board` contains only digest-locked visual world data.
- A screen pixel, viewport transform, grid line, or SVG path never implies an
  electrical connection.
- A passing digital simulation is not physical timing, breadboard, PCB, or
  safety signoff.

## Gate 0 — Benchmark and regression harness first

This gate is required before migrating the editor. It creates a reproducible
measurement baseline and a small fixture corpus, not a performance promise for
all machines.

The detailed Gate 0 evidence rules are in
[BOARD_V2_HARNESS_VERIFICATION_SPEC.md](BOARD_V2_HARNESS_VERIFICATION_SPEC.md).

| ID | Task | Owner / review | Acceptance / checkpoint |
| --- | --- | --- | --- |
| B0.1 | Freeze deterministic Board fixtures: NOT gate, a 4-device chain, and a moderately dense 16-device/32-scalar-edge circuit. Each has source, resolved topology, resource bindings, and expected Board projection. | Bam + Bank / Fern | Fixture IDs/digests are checked; none relies on screen coordinates or hand-drawn SVG endpoints. |
| B0.2 | Add a headless Board v2 harness that runs projection, profile validation/migration, operation-queue dependency checks, and deterministic export without a browser. | Bam / Fern | One command emits JSON results and fails nonzero on a bad digest, forbidden direct mutation, invalid world point, or dependent route before its source edge exists. |
| B0.3 | Add benchmark measurements to that harness: fixture load/resolve/projection time, profile migration time, queue validation/apply time, exported-byte size, and deterministic digest. | Bam / Fern | Results include machine/runtime metadata, fixture digest, iteration count, median and p95. No unmeasured latency target is claimed. |
| B0.4 | Set conservative initial thresholds only after collecting a checked baseline on the development machine; store them beside the harness and distinguish regression thresholds from product targets. | Pim + Bank / Fern | Threshold change requires recorded baseline evidence and Fern review; CI rejects regressions beyond agreed tolerance. |

**Gate 0 exit:** the harness is runnable from a clean checkout, reports a
baseline for all three fixtures, and detects at least one intentional failure
in each of profile, operation dependency, and deterministic-export checks.
It is not closed until B0.4 records and reviews the full 25-sample baseline
and its threshold record.

## Sprint 1 — World and Viewport kernel

| ID | Task | Owner / review | Acceptance / checkpoint |
| --- | --- | --- | --- |
| B1.1 | Implement pure `screen ↔ viewport ↔ world` transforms with centered `(0,0)`, pan, zoom, and world bounds. | Bam / Fern | Round-trip vectors preserve world points within declared tolerance; parser/resolver inputs contain no coordinate fields. |
| B1.2 | Implement adaptive grid/snap in world units. | Bam + Noon / Fern | Grid labels are numeric world values, never A/B/1/2; changing snap does not change unsnapped stored world truth. |
| B1.3 | Replace the prototype renderer's top-left normalized assumption with the transform kernel. | Bam / Fern | Same fixture can pan/zoom without changing exported profile/topology digest; harness verifies this. |

**Sprint 1 checkpoint:** reviewer can pan from negative to positive world
coordinates, zoom around a pointer, and prove that the Component source and
resolved topology did not change.

## Sprint 2 — Board profile v2 and migration

| ID | Task | Owner / review | Acceptance / checkpoint |
| --- | --- | --- | --- |
| B2.1 | Specify and validate `components.board-profile@2` with explicit centered Cartesian coordinate-space metadata. | Bank + Bam / Fern | Schema excludes electrical model fields and rejects missing/incorrect coordinate convention. |
| B2.2 | Implement deterministic `@1 → @2` migration with source profile retained as input evidence. | Bam / Fern | Fixture migration is stable across runs; invalid/stale `@1` rejects without retargeting. |
| B2.3 | Move placements, route bends, and labels to finite world points; keep viewport view state optional/session-local. | Bam / Fern | Exports are world-coordinate-only for visual objects; changing viewport state changes no Board profile digest. |

**Sprint 2 checkpoint:** every Gate 0 fixture round-trips through v2 and a
stale topology refuses to attach an old visual route to a new edge.

## Sprint 3 — Definition-derived placement geometry

| ID | Task | Owner / review | Acceptance / checkpoint |
| --- | --- | --- | --- |
| B3.1 | Define a placement transform: instance ID, world origin, discrete rotation, and definition-derived bounding box. | Bank + Bam / Ohm, Fern | No pin direction, number, or timing is duplicated in Board profile/SVG data. |
| B3.2 | Compute pin anchors from the transform and resource/definition geometry. | Bam + Ohm / Fern | Rotation vectors for all four orientations map anchors deterministically; missing geometry has a clear fallback/error. |
| B3.3 | Add semantic inspector projection for Device, Library, Pins, Ports, Timing, Behavior, References, Connections. | Bam + Noon / Ohm, Fern | Inspector reads resolved/definition facts only and exposes limitations rather than filling gaps with generic graphics properties. |

**Sprint 3 checkpoint:** one 74HC04 can be placed and rotated around world
origin; every displayed anchor maps back to a definition-owned pin.

## Sprint 4 — Semantic operations and Transaction Queue

| ID | Task | Owner / review | Acceptance / checkpoint |
| --- | --- | --- | --- |
| B4.1 | Implement versioned operation records and a Board operation generator for place, move, label, connect preview/apply, route, inspect, pan, and zoom. | Bam + Bank / Fern | No raw mouse move/keystroke becomes a durable operation; every row declares exactly one target authority. |
| B4.2 | Implement queue ordering/dependency states: Pending, Waiting, Applied, Rejected, Discarded. | Bam / Fern | `connect` applies/resolves before a dependent route; rejection blocks dependents and preserves all targets. |
| B4.3 | Replace direct prototype mutation paths with a service apply/re-render path. | Bam / Fern | A test fails if Board UI can update source/topology/profile without an operation result. |
| B4.4 | Render connection-preview labels in the viewport and expose queue details accessibly. | Bam + Noon / Fern | A learner can read `connect U1.1Y → OUT` beside the guide and see the same exact text in the queue. |

**Sprint 4 checkpoint:** queue a connect, route, and label; Apply all; observe
source resolve first, visual route second, then reload with the same digest.

## Sprint 5 — Integration and learner proof

| ID | Task | Owner / review | Acceptance / checkpoint |
| --- | --- | --- | --- |
| B5.1 | Run the full Gate 0 harness plus existing Board/API/language regressions in one documented command. | Fern + Bam | All fixtures, negative cases, deterministic exports, and current focused regressions pass. |
| B5.2 | Conduct the first-sight trial with one 13–15-year-old and one adult beginner using the NOT-gate scenario. | Noon + Pim / Fern | Record completion, confusion points, recovery, and whether the queue/guide wording was understood; do not replace this with developer opinion. |
| B5.3 | Freeze the observed baseline and unresolved issues in handoff/task docs. | Pim / Fern | Remaining risks are explicit; no claim of auto-routing, bus routing, physical safety, or performance beyond recorded evidence. |

**Sprint 5 exit:** Board v2 is ready to widen its toolset only when the
machine harness and both human trials pass. Otherwise, return to the specific
failed sprint task; do not add features around the failure.

## Harness command contract

The exact command path will be added in Gate B0.2. It must be executable in
this repository without a GUI and follow this shape:

```sh
PYTHONPATH=python python3 -B -m tests.test_board_v2_harness
```

The B0.4 regression command adds `BOARD_V2_HARNESS_ITERATIONS=25` and
`BOARD_V2_HARNESS_ENFORCE_THRESHOLDS=1`; the short test command deliberately
does not enforce timing thresholds.

The output must name the fixture, source revision, topology digest, Board
profile version, operation IDs, measurements, pass/fail state, and a specific
failure reason. Browser visuals complement this harness; they do not replace
it.

## Not in this sprint

Auto-routing, bus-route semantics, freehand electrical wires, breadboard/PCB
views, generic drawing properties, arbitrary fonts/colors, physical timing
claims, and image-to-circuit auto-acceptance remain out of scope.
