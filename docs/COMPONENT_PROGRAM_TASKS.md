# Components Program Tasks

Last reconciled: 2026-07-13

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

## P4 — `component:board` and visual editor

| ID | Work | Owner / review | Acceptance | Status |
|---|---|---|---|---|
| C4.1 | Freeze the Board profile only after C1–C3: placement, routing/view metadata, widgets, and physical-capture references. Board consumes resolved topology and Resources; it cannot create behavior. | Bank / Ohm, Noon, Fern | Board schema has no Device-behavior or hidden-net fields; round-trip tests preserve Component identity. | contract completed 2026-07-13; resolver/editor integration waits on C2/C3.2 |
| C4.2 | Build a minimal visual editor over the same text/AST/resolved-topology service. It must round-trip without changing source-owned topology and expose diagnostics in student language. | Bam + Noon / Bank, Fern | source -> editor -> source/topology deterministic round-trip; no edit can bypass validation. | in progress: read-only `component-language-board-view` JSON bridge exists; editable visual client waits on complete runtime/resource flow |

## Parallel RV8GR and physical lanes

- The RV8GR circuit-runner promotion and modeled-timing work remains in
  `examples/circuits/CIRCUIT_RUNNER_TASK_PLAN.md`.  Do not use Component
  language work to infer missing FullControl/whole-system child interfaces.
- Physical RV8GR work remains separate: installed-part evidence, scope
  captures, bus deadband/no-overlap, VCC quality, and voltage/frequency sweeps
  are required before any board-speed claim.

## Next command

Start with **C0.1**.  It is the smallest finished vertical slice and makes the
new text IDE safe to commit before expanding its language or runtime scope.
