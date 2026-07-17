# Components Program Tasks

Last reconciled: 2026-07-14

This is the active delivery order for the Component language, text IDE,
runtime, Resource Library, and later Board work.  It complements—not
replaces—the RV8GR circuit-runner plan in
`examples/circuits/CIRCUIT_RUNNER_TASK_PLAN.md`.

## Ordering rule

```text
text Component source
  -> AST + resolver + validation
  -> immutable topology
  -> Components Runtime
  -> Resource Library bindings
  -> component:board / visual editor
```

A later stage must consume the previous stage's immutable contract.  It must
not recreate Device truth, infer wiring, or hide a failed validation result.
Passing digital simulation is never physical wiring or timing signoff.

## P0 — Land the text-first foundation

| ID | Work | Owner / review | Acceptance | Status |
|---|---|---|---|---|
| C0.1 | Review and commit the current text Component implementation: `component-parse`, `component-resolve`, `component-validate`, and `component-ide`; preserve `Language.zip` as user-owned input. | Bam / Fern, Noon | `PYTHONPATH=python python3 -B -m tests.test_component_language`; `python3 -B tools/check_language_spec.py`; `git diff --check`. | completed/pushed `de1438c` |
| C0.2 | Reconcile the stale repository-layout literals and generated timing audit reports already identified by Fern before calling CI green. Keep archived evidence visible without defeating the active-layout checker. | Pim + Noon / Fern | `python3 -B tools/verify_repository_layout.py`; `cd python && python3 -B -m tests.test_generated_audit_reports`. | completed 2026-07-13 |
| C0.3 | Refresh `docs/SESSION_HANDOFF.md`, `examples/circuits/BACKLOG.md`, and `docs/TEAM_SKILLS.md` from current evidence after C0.1/C0.2. State that timed commands are public but RingCounter-bound/fail-closed; distinguish BusOwnership functional promotion from modeled timing and physical proof. | Pim + Noon / Fern | handoff names the current commit and exact passing commands; no contradictory timing/promotion wording remains. | completed in current worktree; commit with the runtime/student slice |

## P1 — Golden language pipeline

| ID | Work | Owner / review | Acceptance | Status |
|---|---|---|---|---|
| C1.1 | Add checked on-disk golden artifacts for each supported phase: `.component -> .ast.json -> .resolved.json`. Include one valid leaf digital fixture and stable source spans. | Bam / Bank / Fern | test fails on AST/order/span or resolved-topology drift; fixtures are generated only by the CLI, not edited as source truth. | completed 2026-07-13 |
| C1.2 | Expand parser coverage for the approved v1.1 leaf syntax only: title, both accepted Device spellings, parameters, nets/buses, selectors, probes/watches, displays, and declared bounded tests. Reject unsupported statements with stable diagnostics. | Bam / Bank / Fern | lexer/parser positive and negative fixtures pass; parser reads no DB and creates no topology. | in progress: leaf source contract is covered; generic schema/board/operation and hierarchy stay deferred |
| C1.3 | Complete resolver validation: duplicate symbols; unknown Device/port/pin; explicit bus mapping; signal kind/width; power isolation; Device port direction; output ownership; read-only probes/displays. | Bam / Bank + Ohm / Fern | all negative cases fail nonzero with the documented diagnostic code and source line; no auto-connect or guessed bus bit. | in progress: leaf ownership/alias/power checks pass; typed-port/floating and hierarchy checks require later contracts |
| C1.4 | Publish `components.resolved-component@1` as a checked schema/fixture contract, including library identity/digest, resolved Device facts, typed endpoints, scalar edges, validation result, and provenance. | Bank + Bam / Fern | schema validation and deterministic CLI output pass with `PYTHONHASHSEED=0` and `1`. | completed 2026-07-13 |

## P2 — Components Runtime, no Board

| ID | Work | Owner / review | Acceptance | Status |
|---|---|---|---|---|
| C2.1 | Compile a validated Resolved Component into the existing event-kernel boundary without changing circuit-package behavior. Create isolated Device/Net instances and explicit operation drivers. | Bam / Bank / Fern | a leaf Component inverter and counter run through the kernel; raw AST never reaches runtime. | in progress: inverter instantiation, rails, explicit drive, and probe pass; counter/clock coverage remains |
| C2.2 | Implement declared-test execution only through bounded Operations: set, pulse, wait, settle, assert, probe. Retain deterministic `(time, delta)` trace and execution limits. | Bam / Fern + Mint | event/edge/no-edge, Z/X, timeout, and deterministic replay fixtures pass; nonzero on test failure. | in progress: beginner actions execute; deterministic trace/replay and broader clock coverage remain |
| C2.3 | Expose `component-run`, `component-probe`, and trace export through CLI/API after C2.1/C2.2. Errors must name Component, Device, port/net, time, and suggested next action. | Bam + Noon / Fern | CLI/API contract tests pass; output says digital-model result and never physical signoff. | in progress: CLI and additive `component-language-*` API commands pass; trace export remains |

## P3 — Resource Library before visual editing

| ID | Work | Owner / review | Acceptance | Status |
|---|---|---|---|---|
| C3.1 | Define a Resource binding contract for labels, symbols, display kinds, and optional physical/package presentation. Resource data remains presentation-only and cannot change Device pins, behavior, timing, or Component topology. | Bank + Noon / Ohm, Fern | schema and negative ownership tests prove Resource cannot alter electrical truth. | completed 2026-07-13 |
| C3.2 | Add text commands to inspect and bind Resources to a resolved Component, with readable student output. Do not add coordinates, routing, or Board state. | Bam + Noon / Fern | resource CLI tests prove stable bindings and clear missing-resource diagnostics. | completed in current worktree |
| C3.3 | Define versioned Resource Definitions for readable text, optional 2D, optional 3D, and other presentation assets. Keep Resource Definitions presentation-only; a missing asset must fall back to text. | Bank + Noon / Ohm, Fern | schema fixtures prove a resource cannot alter Device truth or topology and can be selected by a binding. | completed 2026-07-13 (contract/fixtures; no renderer yet) |
| C3.4 | Freeze the Learning Lens contract: beginner explanation, real technical name, source/trace links, safe contextual actions, and text fallback for every visible resolved target. | Noon + Bank / Bam, Fern | NOT-gate lens fixture proves the lens consumes locked facts only and cannot mutate topology/runtime directly. | completed 2026-07-14 (design contract; no renderer yet) |

## P3.5 — Desktop foundations before a visual client

| ID | Work | Owner / review | Acceptance | Status |
|---|---|---|---|---|
| C3.5.1 | Build the lightweight three-pane foundation: Drawing, readable Component text, and bounded Terminal over one Rust/Tauri + small Preact/TypeScript session. Use the desktop Python adapter, preserve a portable JSON service boundary for iOS, and keep source authoritative while Drawing emits checked source patches. | Bank + Bam / Noon, Fern | First pass the intent/trace/verification gate; then NOT-gate no-network/no-plugin launch proves text -> Drawing sync, legal/illegal Drawing connection handling, one bounded Terminal trace, atomic autosave/recovery, recorded startup/interaction baseline, and a first-sight test with a 13–15-year-old plus an adult beginner; no pane has alternate electrical state. | in progress: dependency-free local `board/` workbench, API-served assets, resolver/runtime, draft recovery, and checked connect/disconnect source patches pass focused tests; Tauri wrapper, measured UI session, and learner test remain |
| C3.5.1a | Build the NOT-gate first-sight route inside the three-pane shell: title/meaning, visible `IN -> U1 -> OUT`, one suggested action, result sentence, selection-to-source highlight, and error recovery. | Bam + Noon / Bank, Fern | unprepared 13–15-year-old and adult-beginner test each complete the five-minute Learning Lens path without a guide. | queued with C3.5.1 |
| C3.5.2 | Define signed auto-update compatibility, channel, safe-restart, recovery, and rollback contracts before enabling an update endpoint. | Bank + Bam / Fern, Noon | tampered/incompatible manifest fixtures are rejected; update preserves drafts and waits for runtime idle. | contract completed 2026-07-13; implementation deferred |
| C3.5.3 | Define the versioned plugin manifest, capability policy, integrity checks, safe mode, and no-plugin core operation before accepting third-party code. | Bank + Bam / Fern, Noon | plugin contract proves no hidden topology/model mutation and rejects incompatible/tampered plugins. | contract completed 2026-07-13; host implementation deferred |

## P4 — `component:board` and visual editor

| ID | Work | Owner / review | Acceptance | Status |
|---|---|---|---|---|
| C4.1 | Freeze the Board profile only after C1–C3: placement, routing/view metadata, widgets, and physical-capture references. Board consumes resolved topology and Resources; it cannot create behavior. | Bank / Ohm, Noon, Fern | Board schema has no Device-behavior or hidden-net fields; round-trip tests preserve Component identity. | contract completed 2026-07-13; resolver/editor integration waits on C2/C3.2 |
| C4.1a | Migrate the exploratory normalized Board profile to the frozen world-coordinate Viewport architecture: centered Cartesian world points, screen/viewport transform, definition-derived placement geometry, semantic operation generator, and dependency-aware transaction queue. | Bam + Bank / Fern, Noon | profile-v2/migration fixtures preserve topology identity; Board never writes a model directly; source-first transaction proof rejects stale/dependent Board work; pan/zoom has no parser effect. | next mandatory gate; sprint breakdown and harness-first benchmark in `board/docs/BOARD_V2_SPRINT_PLAN.md` |
| C4.2 | Extend the minimal Drawing pane into a detailed bidirectional Component editor: Component text renders a complete KiCad-like pin/edge circuit with dashed guides for each existing connection; visual part/pin edits preview exact Component patches; beginner blocks/palette are assistance beside—not instead of—the detailed canvas. | Bam + Noon / Bank, Fern | text -> placed devices plus guides and visual edit -> checked text patch are deterministic in both directions; every library-backed visible part exposes definition-owned pins and named edges; routes alter only the Board profile; palette parts use real library identity/pins/model; no visual edit bypasses validation or mutates Device truth. | queued after C3.5.1; direction frozen in `board/docs/BOARD_LEARNER_CIRCUIT_DIRECTION.md` |
| C4.2a | Add guided KiCad-style schematic-image reconstruction: detection overlay, candidate library mapping, proposed Component source, review/correction, and Board-profile capture. | Bam + Bank / Ohm, Fern, Noon | unknown part/pin/crossing/bus mapping stays visibly unresolved; only reviewed candidate code that parse/resolves can be applied; image import cannot create a hidden connection or simulation claim. | planned after C4.2; contract in `board/docs/BOARD_IMAGE_RECONSTRUCTION_CONTRACT.md` |
| C4.2b | Implement the versioned `component:operation` command/replay layer across Board source edits, Board-profile actions, bounded runtime actions, and guided image reconstruction. | Bam + Bank / Fern, Noon | each meaningful gesture/shortcut exposes one checked command equivalent; revision/digest mismatch fails; source/profile/runtime boundaries stay separate; safe undo/redo replays recorded inverses. | planned with C4.2; contract in `Language/23_Component_Operation_Contract.md` |
| C4.2c | Add the staged schematic toolset: select/pan/zoom/grid/snap, library placement, move/drag/rotate, connect/route, labels, explicit junction/no-connect policy, inspect, net highlight, undo/redo, and bounded run/step/watch. | Bam + Noon / Bank, Ohm, Fern | every enabled tool has a clear student label, text/operation equivalent, authority target, cancel path, and positive/negative proof; visual crossings never become hidden connections. | planned after Canvas Prototype; tool inventory in `board/docs/BOARD_SCHEMATIC_TOOLSET.md` |
| C4.3 | Add optional Board plugins only after C4.2: first a sandboxed Resource/trace viewer, then any integration under the plugin policy. | Bam / Bank, Fern, Noon | disabled/safe-mode client remains fully usable; plugin receives only declared JSON capabilities. | deferred |

## Parallel RV8GR and physical lanes

- The RV8GR circuit-runner promotion and modeled-timing work remains in
  `examples/circuits/CIRCUIT_RUNNER_TASK_PLAN.md`.  Do not use Component
  language work to infer missing FullControl/whole-system child interfaces.
- Physical RV8GR work remains separate: installed-part evidence, scope
  captures, bus deadband/no-overlap, VCC quality, and voltage/frequency sweeps
  are required before any board-speed claim.

## Next command

Start with **C3.5.1**. Build the smallest no-plugin three-pane session for a
NOT gate: Drawing, readable text, and bounded Terminal commands. Do not
enable the updater or a plugin host yet.
