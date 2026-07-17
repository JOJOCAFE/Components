# Components Session Handoff

Last updated: 2026-07-17

> **Current authority.** This section supersedes the older RV8GR checkpoint
> notes below when they disagree. This checkpoint includes the first local
> Component Board implementation and its focused verification. `Language.zip`
> is user-owned and remains untracked/untouched.

## Board prototype checkpoint: 2026-07-17

The active next authority for Board work is
`board/docs/COMPONENT_BOARD_PROTOTYPE.md`. It was written after the learner clarified
the required split:

- `component:component` owns checked `device`, `net`, `bus`, and explicit
  `connect U1.1Y -> U2.1A;` source declarations.
- `component:board` owns only presentation: placed positions and route points
  for an **already resolved** scalar edge. A route must never create a circuit
  connection.
- Coordinate paths and LOGO-style pen paths are alternate ways to describe the
  same legacy prototype Board-profile route. The former `0..100`, top-left,
  positive-right/down encoding is superseded for new work by the centered
  world-coordinate Viewport architecture in `board/docs/BOARD_ARCHITECTURE_FREEZE.md`.
- Bus routing is deliberately not implemented/accepted: a bus needs a frozen
  bundle/member route contract before the Board can draw a line that implies
  bit wiring.

The prototype lists Working Box/BOM lifecycle, source-versus-profile
persistence, stale-digest recovery, accessibility/undo expectations, and seven
first acceptance scenarios. `board/docs/COMPONENT_BOARD_WORKFLOW.md` remains the
learner flow; use the prototype for any new command or Board profile behavior.

### Board worktree status at handoff

- The worktree contains uncommitted Board/SVG/API/docs work from this session
  and earlier concurrent Board slices. Preserve it; do not reset or discard
  unrelated changes.
- Focused checks passed **before** the final prototype clarification:

  ```sh
  PYTHONPATH=python python3 -B -c 'from tests.test_component_board_api import test_board_chip_frame_resource_is_available, test_board_example_resolve_run_and_checked_source_edit, test_board_edit_rejects_stale_or_missing_connection_without_mutating_text; test_board_chip_frame_resource_is_available(); test_board_example_resolve_run_and_checked_source_edit(); test_board_edit_rejects_stale_or_missing_connection_without_mutating_text()'
  PYTHONPATH=python python3 -B -c 'from tests.test_functional_pinout_svg_metadata import test_every_74hc_svg_pin_node_has_command_lookup_metadata; test_every_74hc_svg_pin_node_has_command_lookup_metadata()'
  node --check board/app.js
  git diff --check
  ```

- The later coordinate/LOGO pen-command experiment has **not** been accepted
  against the new prototype or given a final interactive-browser verification.
  Do not claim it is complete. Review/adjust it from the prototype first, then
  add deterministic profile round-trip tests and run the focused checks again.

### Exact resume order

1. Run `board/docs/BOARD_FIRST_SIGHT_TRIAL.md` separately with one 13–15-year-old
   learner and one adult beginner. This is the remaining human acceptance
   evidence; do not mark it passed from developer inspection.
2. Add Working Box and atomic BOM preview only after the add-declaration
   service contract and tests are complete.
3. Add a bus-route contract before any visual bus bundle command.
4. Have Fern independently review the browser flow before a broader Board
   implementation is claimed.

### Board profile contract checkpoint: 2026-07-17

The local Board now has a deterministic profile-rule module at
`board/profile.js` with a Node proof at `board/profile.test.mjs`. It accepts
only finite in-bounds Board coordinates (`0..100`), stores scalar-edge routes
only, and uses Board units for both coordinate and LOGO pen paths. A stale
topology digest is not reused or retargeted: the Board reports it and requires
an explicit `discard board profile` before an empty profile can be saved.

Focused checkpoint evidence:

```sh
node --check board/app.js
node board/profile.test.mjs
PYTHONPATH=python python3 -B -m tests.test_component_board_api
PYTHONPATH=python python3 -B -m tests.test_component_language
PYTHONPATH=python python3 -B -m tests.test_functional_pinout_svg_metadata
git diff --check
```

This closes the deterministic scalar-profile subgate only. It does not claim
server profile persistence, Working Box/BOM, bus-route semantics, Undo/Redo,
browser accessibility parity, a learner trial, timing signoff, or breadboard
safety.

### Browser interaction implementation checkpoint: 2026-07-17

The local Board now has the code-level interaction path for pointer and
keyboard pin selection, checked preview before explicit Apply, typed pin-to-pin
preview, and Cancel/Escape/`cancel route` recovery. The associated machine
checks are `node board/interaction-contract.test.mjs` plus the focused Board
API tests; a temporary localhost HTTP smoke confirmed that the API serves the
module Board client. No browser automation runtime is installed in this
environment, so visual interaction still needs the human trial protocol above.

### Learner circuit direction: 2026-07-17

The requested Board direction is now recorded in
`board/docs/BOARD_LEARNER_CIRCUIT_DIRECTION.md`: MakeCode-like blocks, readable
Component code, and a KiCad-like spatial Board are three views of one
library-backed Component circuit. The next implementation slice after the
human trial is a checked library palette and Working Box, not a freehand
canvas. `components.block_ui` remains a separate normalized-Design
interchange until a checked Component-to-Design bridge is frozen.

The user further clarified the primary goal: Board is the **detailed
bidirectional visual editor** for Component language. It must render text as
a real pin-by-pin circuit and turn visual part/pin edits back into exact
checked Component code. MakeCode/Canva/SketchUp-style ease is the interaction
layer; it never replaces the KiCad-like detailed canvas with rough blocks.

The first visual surface is now explicitly a **student-friendly KiCad-style
schematic for ages 13–15**, not a breadboard interface. Breadboard/physical
layout stays deferred behind a separate evidence and safety contract.

The Board's two-way next contract is now explicit: Component source places all
resolved devices and shows dashed connection guides for a student to route;
an image import stages a reviewable schematic reconstruction and proposed
Component source rather than claiming automatic electrical truth. See
`board/docs/BOARD_IMAGE_RECONSTRUCTION_CONTRACT.md`.

The three-layer language model is now documented explicitly:
`component:component` defines the circuit, `component:board` defines its
resolved visual profile, and planned `component:operation` defines meaningful
replayable Board/source/runtime actions. It follows the Maya/Blender command
idea without persisting every raw mouse move or individual keystroke; see
`Language/23_Component_Operation_Contract.md`.

### Board architecture freeze: 2026-07-17

Board is frozen as a Component-language visual front end: **Screen → Viewport
→ centered World → snap/selection → semantic operation → transaction queue →
validation → update → re-render**. Board does not edit a Component model
directly. The right-top overlay is a multi-row Transaction Queue with Apply
all; Inspect is semantic (Device, Library, Pins, Ports, Timing, Behavior,
References, Connections). The immediate next implementation gate is profile
v2/migration plus the world/viewport/operation path, before broad editor-tool
work. See `board/docs/BOARD_ARCHITECTURE_FREEZE.md`.

### Board v2 sprint and harness gate: 2026-07-17

The current execution authority is `board/docs/BOARD_V2_SPRINT_PLAN.md`. Begin with
Gate 0: deterministic fixtures and a headless benchmark/regression harness.
Do not widen Board tools until it measures and proves projection, profile
migration, queue dependency, deterministic export, and intentional negative
cases. Subsequent checkpoints are World/Viewport, profile v2 migration,
definition-derived geometry, transaction queue, then the learner trial.

Gate 0 is complete: `Language/fixtures/board-v2/` supplies checked
NOT/chain-4/dense-16x32 sources and canonical topology projections; the
headless `tests.test_board_v2_harness` checks their digests, eight negative
cases, deterministic exports across hash seeds, and baseline-mode measurements.
`python/tests/data/board_v2/baselines/05024f5.json` records the five-warmup,
25-sample baseline; the reviewed `thresholds.json` enables the explicit
regression command documented in `board/docs/BOARD_V2_HARNESS_VERIFICATION_SPEC.md`.
The visual-prototype checkpoint now uses the Board-first viewport layout:
narrow tool rail, large schematic area, and the compact code overlay without a
permanent terminal panel. Old v1 local drafts that contained Terminal `run`
commands are deliberately ignored by the new source-storage key; the UI tells
the learner to use **Try inversion** instead of putting `run` in Component
code.

B1.1 is complete in `board/viewport.js` with a Node proof at
`board/viewport.test.mjs`: centered world origin, screen/world round trips,
content-following pan, anchor-preserving zoom, and visible world bounds. The
same module now selects readable 1/2/5 adaptive world grids and snaps a world
point without altering Component source. B1.3 is also complete: the browser
projects devices, nets, routes, labels, and pen previews through this viewport;
wheel zoom is pointer-anchored and Shift/middle drag pans the view. Those view
actions only change local viewport state. The persisted `@1` normalized profile
is explicitly adapted at the UI boundary until B2 migration; it is not renamed
or presented as world-coordinate truth. The next task is B2.1: specify the
persisted `components.board-profile@2` world-coordinate contract.

B2.1 is complete in `board/profile-v2.js`, its Node contract proof, and
`board/docs/BOARD_PROFILE_V2_CONTRACT.md`. The new profile requires exact
centered Cartesian metadata, finite unbounded world points, digest-locked
topology references, and only discrete initial rotation. It rejects electrical
fields and session-local viewport/camera persistence. B2.2 is next: a
deterministic explicit `@1 → @2` migration with fixtures; the browser must not
silently reinterpret an old profile as world data.

B2.2 is complete in `board/profile-v2.js` and the aligned headless harness:
it maps bounded v1 top-left points by `(x - 50) × 6`, `(50 - y) × 6`, validates
the source digest before conversion, returns a copied source profile as
migration evidence, and exports validated v2 output deterministically across
hash seeds. The existing 25-sample regression baseline predates this intentional
canonical-export change and must be refreshed after B2.3 browser adoption; do
not use it to claim a current v2 performance threshold. B2.3 is next.

B2.3 implementation is now in the Board client: its local profile key is
`components.board.not-gate.profile.v2`; old `@1` storage migrates explicitly,
then is removed. Devices/nets use world `origin`, routes and labels use world
points, and mouse/stylus input converts directly from the viewport to a finite
world point. The viewport is never stored in the profile. No browser runtime is
available in this environment, so do not mark B2.3 passed until a human observes
old-profile migration, negative/positive placement, a label/route drag, and
pan/zoom with an unchanged exported profile. Its machine benchmark side is
refreshed and Fern-reviewed at `659a67a`: the tracked baseline has five
unmeasured warm-ups, 25 retained samples, recorded seed-0/seed-1 digest
evidence, and the enforced regression guard in
`python/tests/data/board_v2/thresholds.json`. Before starting B3, retain the
remaining human migration observation rather than treating the benchmark as a
browser substitute.

Board chip artwork now uses generated no-pin 74HC DIP frames in
`board/assets/74hc-chip-frames-no-pins/`: long printed lead stubs are replaced
with compact connection dots while readable labels remain. The Board overlays
definition-owned hit areas on those dots and targets its routes/guides there.
The underlying definition still owns port names, physical pin evidence, and
validation.

### Vector canvas slice: 2026-07-17

The local Board now renders existing chip-frame resources as SVG, resolved
connection guides/routes as SVG paths, and Board-only labels as SVG text. A
label supports one or multiple lines and a `1.5..8` Board-unit size; font and
colour choices remain intentionally deferred. Labels and visual routes are
stored in the digest-locked profile and do not change Component wiring. The
current connection-guide path can be dragged into a routed path; it does not
invent an electrical edge.

### Board guide-operation checkpoint: 2026-07-17

The guide rule is frozen and reusable. `board/guide-operation.js` emits and
reduces a session-only `components.operation@1` record with kind
`board.guide.toggle`; its contract and reuse boundary are in
`board/docs/BOARD_GUIDE_OPERATION_CONTRACT.md`. With **Guides** selected,
clicking any device, net, or precise pin/node dot toggles all matching declared
scalar edges for that focus: if all are shown they hide, otherwise they show.
Several node groups may remain shown. Clicking another endpoint can therefore
hide or show a shared edge individually. Every visible Board object has a
resolved border node/dot; a guide click never selects, inspects, routes,
persists, or changes `component:component` topology.

Focused proof:

```bash
node board/guide-operation.test.mjs
node board/interaction-contract.test.mjs
node board/profile-v2.test.mjs
PYTHONPATH=python python3 -B -m tests.test_component_board_api
```

This is not a transaction queue or a persisted `component:operation` log.
Bank must freeze that later authority before collaboration, replay, macro, or
profile-persistence work. B3 also remains blocked by the separate human
old-profile migration/pan/zoom observation described above.

## Functional-pinout SVG handoff: 2026-07-14

Board artwork is being redrawn as clean SVG from the cropped datasource PNGs
in `board/assets/74hc-functional-pinouts/`; the package definition remains
the pin-truth authority. The accepted internal-symbol references are
`74hc04-internal.svg`, `74hc05-internal.svg`, `74hc08-internal.svg`, and
`74hc14-internal.svg`. The reviewed combined outputs are
`74hc04-functional.svg`, `74hc05-functional.svg`, `74hc08-functional.svg`,
and `74hc14-functional.svg`; the definition-backed Fritzing-style outside
frames use the corresponding un-suffixed filenames. Together they establish
the shared DIP header, inside-name/outside-number label spacing, direct
gate/bubble/cord contact, and source-specific internal marks. For special
symbols, check a manufacturer datasheet as well as the cropped source before
drawing a new part.

`74hc21.png` is cropped and `74hc21.svg` exists only as an **unaccepted
draft**. Do not use it as a template. Resume by inspecting its PNG at high
magnification and tracing its two four-input AND symbols and each stepped cord
one route at a time; the previous attempt did not faithfully match the source.

### Functional-pinout resume point: 2026-07-14

- Reviewed combined drawings: `74hc00-functional.svg`, `74hc02-functional.svg`,
  `74hc03-functional.svg`, `74hc04-functional.svg`, `74hc05-functional.svg`,
  `74hc08-functional.svg`, and `74hc14-functional.svg`.
- `74hc08-functional.svg` is the latest accepted source-match reference: its
  right AND gates mirror the left-side placement, and 4A/3A take the clear
  turn lane between the inside pin name and lower gate edge.
- For each next chip: enlarge its cropped PNG before editing, trace cord turns
  rather than inferring them, preserve definition pin mapping/connectors, then
  run a connector/symbol count check and `git diff --check`.
- The 74HC00/02/03 drawings are functional references but should receive a
  final visual source comparison before they are treated as finished examples.

## Current student-first Board/desktop checkpoint: 2026-07-14

This student-first checkpoint contains Resource/Board contracts, the local
Board implementation, source-edit API, Component-language ownership checks,
fixtures, tests, documentation, and team working rules.

The next Component client is a lightweight, offline-first three-pane
workbench: **Drawing** is left, readable **Component text** is upper-right,
and a small bounded **Terminal** is lower-right. Panes can resize, collapse,
detach, or go full-screen. The default UI is pointer/stylus-first and
contextual, not a ribbon/menu-heavy professional CAD application.

- One readable `.component` source remains the electrical/topology authority.
  Drawing and Terminal *source edits* send revision-checked intents and return
  visible source patches; bounded runtime commands return trace/results and do
  not rewrite source.
- The first route is a NOT gate. A 10–15-year-old learner and an adult
  beginner must understand `IN -> U1 -> OUT`, run one example, make one safe
  change, and recover from an invalid connection without a reference guide.
- `docs/COMPONENT_FIRST_SIGHT_DESIGN.md` owns this usability promise;
  `docs/COMPONENT_LEARNING_LENS.md` defines the selected-object explanation:
  what it is, what it does here, real name, safe action, and outcome. Resource
  views can offer teaching/2D/3D detail but never change Device truth.
- Windows, Linux, and iOS are product targets. Windows/Linux use the current
  local Python service adapter; iOS must retain the same JSON contract through
  a tested iOS-compatible adapter before release. Android/iPad refinement is
  later. Launch, interaction, memory, package size, autosave, and crash
  recovery are release gates, not polish.
- Auto-update and plugins are contracts only: signed/compatible/recoverable
  updates; optional capability-limited plugins; no startup dependency and no
  hidden electrical authority.

### Working method now required

`docs/TEAM_SKILLS.md` and every role guide now use the adapted 9arm-style
engineering loop: **intent -> trace -> verify -> report**. New work must name
the smallest learner outcome, trace the real path to source/runtime and the
visible result, prove success/failure/ownership/performance cases, and retain
compact evidence. Defects require reproduce -> trace -> falsify -> breadcrumb
ledger before a proposed fix.

### Resume this lane

1. Start C3.5.1 with a one-window NOT-gate proof, no plugins and no network.
2. First implement/test the `component-edit` source-patch and bounded Terminal
   request contracts against the existing Python service; do not build a hidden
   canvas model.
3. Add the small Rust/Tauri + Preact shell only around that proved path, then
   measure startup, pointer response, autosave/recovery, and memory on modest
   student hardware.
4. Run the first-sight learner test before adding timeline/waveform, 3D,
   multiwindow, updater endpoint, or plugin host.

### First implementation now present

`board/` now contains a dependency-free local web workbench served from the
existing `chiplib.api --http` process. It loads the real NOT-gate fixture,
shows Drawing/Text/Terminal, resolves text through the existing service,
stores a local browser draft, runs the declared `inversion` test, and supports
bounded `run`, `drive`, `watch`, `connect`, and `disconnect` commands.

`python/chiplib/component_edit.py` owns the first revision-checked source
patches for connect/disconnect. It parses/resolves the candidate text before
returning it; invalid or stale edits leave source unchanged. Focused proof:

```sh
PYTHONPATH=python python3 -B -m tests.test_component_board_api
PYTHONPATH=python python3 -B -m tests.test_api
node --check board/app.js
```

This is a local browser proof, not yet a Rust/Tauri package, an iOS adapter,
measured performance session, or a completed learner test.

## Current Component Text Route

- A human writes one readable `component:component` source. Components turns
  it into AST, resolved topology, and result JSON for CLI/API/AI or a later
  visual Board client. JSON is interchange, not a second source students must
  edit.
- The pushed foundation provides `component-parse`, `component-resolve`,
  `component-validate`, and `component-ide`, plus AST/resolved golden fixtures.
  The current shared worktree adds `component-student` and a bounded
  `component-run` leaf digital-model path with declared beginner actions.
- Start a 10–15-year-old learner with
  `docs/COMPONENT_BUILD_NOT_GATE.md`. The learner view shows parts, explicit
  wire count, observations, and named tests before showing full JSON.
- A Component result is a digital-model result only. It does not create a
  `component:board`, select physical placement/routing, bind Resources, prove
  electrical safety, or sign off timing/speed on a breadboard.
- The next implementation boundaries remain: broaden only the frozen leaf
  parser/resolver contract, finish deterministic runtime traces and CLI/API
  probe/export contracts, add text Resource inspection/binding, then let the
  Board/editor consume—not alter—the resolved topology.

## Resume Checks For This Lane

```sh
git status --short --branch
PYTHONPATH=python python3 -B -m tests.test_component_language
PYTHONPATH=python python3 -B -m chiplib.cli component-student \
  Language/fixtures/component-v1.1/digital_inverter.component
PYTHONPATH=python python3 -B -m chiplib.cli component-run \
  Language/fixtures/component-v1.1/digital_inverter.component --test inversion
python3 -B tools/check_language_spec.py
git diff --check
```

## Current State

- Repo: `/home/jo/kiro/Components`
- Branch: `main`
- Base pushed state: `5409405 Extend Component runtime and JSON bridge`
- The sections below preserve the prior compact-definition and RV8GR evidence
  context. Consult the Current Component Text Route above for active language
  and student-tool status.

## Active Verified Worktree

- `docs/Component/` now exposes one active Markdown source:
  `Component_Model.md`.  The original imported design bundle is preserved
  unchanged under `docs/Component/old_references/`; Language fixtures link to
  the active model instead of a second document copy.
- Compact Device authoring is active for the digital, memory, passive, and
  virtual pilots.  The legacy migration adapters prove lossless resolution for
  eight RV8GR digital records and three SRAM records; the audit reports seven
  compact-ready, eleven bridge-ready, and zero blocked RV8GR definitions.
- The complete Components quality gate passed: Python chip/design/UI/netlist/
  CLI/API/database/contracts/simulation/equivalence/circuit suites, database audit/status,
  six source/behavior crosschecks, 74xx and memory Verilog smoke benches,
  migration gates, and Component-language fixtures.  Direct package-file
  crosschecks now resolve compact sources through the same DB boundary.

- Last pushed Components checkpoint: `01d7ea1 Promote virtual test helper
  circuit` on `main`; the worktree was clean after push.
- Last pushed RV8 compatibility checkpoint: `7d2dac5 Support migrated
  Components layout` on `team-setup`. With
  `COMPONENTS_ROOT=/home/jo/kiro/Components`, the RV8GR chip-level bring-up,
  full, dual-compare, and 16-part/36-package Components verification gates
  pass.
- `RV8GR_VirtualTestHelpers` is directly promoted. Its public runner proof
  executes clock, phase, bus, switch, R/C, delay/noise, and output-assert
  vectors. `RV8GR_BusOwnership` is also directly promoted: seven live phase
  vectors plus five explicitly labelled forced-control conflict checks bind
  U24/U25/U26/U28, U7/U14/U34, ROM, and RAM from canonical RV8GR evidence.
- Do not infer FullControl child-port mappings from prose equations. Source
  them from canonical RV8GR RTL/wiring evidence, then bind
  database/Python/verilog/tests/docs together. BusOwnership functional promotion does
  not prove package-level timing or physical hardware timing.
- Repository layout migrated on 2026-07-12: packages live in
  `lib/standard/`; circuit examples and proof assets live in
  `examples/circuits/`; documentation, schemas, source evidence, and Verilog
  live in `docs/`, `schemas/`, `source/`, and `verilog/` respectively.
  `tools/verify_repository_layout.py` and its CI/test gate reject stale
  legacy-root references.
- The lower-case layout migration was staged, committed, and pushed as
  `cb2a514`; Git rename detection was verified before the commit.
- The uncommitted circuit-runner implementation is verified by the complete
  Python workflow-equivalent suite, state-behavior cross-check, campaign
  drift gate, and `git diff --check`.
- `RV8GR_StorePath` is now directly promoted: five public live-runner vectors
  verify accumulator-buffer control, direction, RAM `/WE`, ROM `/OE`, and
  RAM address-zero writeback.
- Timed student access is available through `timed-run`,
  `explain-violations`, and `export-evidence` in the service, CLI, and API.
  It is fail-closed: only the explicitly bound RingCounter timing scenario
  runs; unsupported package timing returns `blocked`.
- CI includes a separate `circuit-campaign-promotion` job that verifies
  generated campaign artifacts, the direct package gate, the timing-binding
  gate, and campaign determinism.
- FullControl now has explicit source-backed composition contracts for ordered
  address concatenation, `/ADDR_MODE` export, PC16, and InterruptEnable; it
  flattens to 39 live leaves with child power rails preserved.  The isolated
  PC16 proof passes reset, `0x1234` parallel load, and `0x1235` increment.
  FullControl remains unpromoted: a powered live T2 run detects a real U34/U7
  IBUS contention, and IE requires an explicit U31 clock event rather than
  inferred combinational-edge behavior.  BusOwnership modeled timing and all
  physical RV8GR evidence remain separate and open.
- Five active digital Device sources (`74HC00`, `74HC161`, `74HC157`,
  `74HC245`, `74HC574`) use compact authoring plus generated resolved output.
  Resistor, ClockSource, and AT28C256 are also active typed compact Devices
  for passive, virtual, and memory classes.  `74HC00`, `74HC157`, `74HC161`,
  `74HC245`, and `74HC574` have presentation-only Resource maps.  See
  `docs/DEFINITION_OWNERSHIP_V0_1.md` before migrating another package.
- The lossless migration proof now covers all eleven still-legacy RV8GR-ready
  records: eight digital chips through
  `tools/check_rv8gr_legacy_compact_equivalence.py` and the `62256`,
  `AS6C62256`, `CY7C199` SRAM trio through
  `tools/check_rv8gr_legacy_memory_compact_equivalence.py`.  No legacy source
  has been rewritten yet; compact authoring review and package regressions are
  the next safe migration step.
- The FullControl operation gate runs the external RV8GR behavioral 512-opcode
  suite, chip-level bring-up/full, and dual RTL comparison, then checks all
  512 scheduled `/PC_LD` rows and 256 source-owned reset-Z T2 controls with
  settled U34/U7 ownership.  Live IE remains correctly blocked until the
  flattened runner can schedule the source-backed U33-to-U31 clock edge.

## Completed RV8GR Software Coverage

- All packages in `examples/circuits/RV8GR_COVERAGE_INDEX.json` are `Tested` and
  are cross-checked against package directories, READMEs, JSON proof vectors,
  and `python/tests/test_lib_circuits.py`.
- Boot coverage is complete in `RV8GR_BootSequenceTrace`: `SETDP $80`,
  `SETPG $00`, `LI $00`, and `J self`.
- Lab 13 coverage is complete in `RV8GR_Lab13MarkerTrace`, including the `$AA`
  marker and final pass state.
- Whole-system virtual coverage is complete in
  `RV8GR_WholeSystemChipLevelVirtual`, including boot, Lab 13, RAM/page/IRQ/bus
  traces, R/C stress, delay/noise stress, and virtual fault checks.
- The RV8GR behavioral and chip-level Verilog gate was recorded passing via
  `/home/jo/kiro/RV8/RV8GR/tools/run_all_verilog_tb.sh`.
- The same full external gate now also requires negative mutation kills for
  reset release, U34/U7 ownership, ROM `/WE` protection, U7 store direction,
  and output-enable ordering.  This closes the bounded RV8GR software lane;
  only physical measurement/readiness work remains on that lane.

## Evidence Boundary

- Functional timing is proven in executable Components vectors and RV8GR
  benches: edge order, no-edge holds, phase sequencing, and bus ownership.
- source/model timing is recorded in `examples/circuits/timing_margins.json`:
  datasheet rows, setup/hold and propagation budgets, candidate paths, and
  computed slack. Positive model slack is not a physical speed claim.
- Physical timing is not proven. Hardware signoff still requires installed
  EEPROM/SRAM markings, voltage/frequency sweeps, clock/reset and destination
  edge captures, memory read/float/write timing, quantified bus deadband, VCC
  quality, and proof of no driver overlap.
- Therefore boot, Lab 13, and whole-system tasks are complete as software
  coverage only. Their physical build runs remain pending, and 5 MHz plus any
  student build-speed recommendation remain blocked.

## Waiting By Scope

1. Visual chip-block editor implementation is waiting by user request. The
   backend contract and `docs/VISUAL_MODULE_PLAN.md` are ready.
2. MCP adapter implementation is waiting until visual editor and service
   command names settle; MCP must remain a thin adapter over existing services.
3. Physical RV8GR evidence collection belongs to the real build and cannot be
   closed by Components software tests.

## Resume Checks

```sh
git status --short --branch
PYTHONPATH=python python3 -B -m tests.test_lib_circuits
PYTHONPATH=python python3 -B -m tests.test_generated_split_records
PYTHONPATH=python python3 -B -m tests.test_db
PYTHONPATH=python python3 -B -m chiplib.cli db --audit
git diff --check
```

Current coordination detail is maintained in
`examples/circuits/RV8GR_END_TO_END_TEST_PLAN.md` and
`examples/circuits/BACKLOG.md`; older implementation history remains available in
Git history.
