# Components Session Handoff

Last updated: 2026-07-13

> **Current authority.** This section supersedes the older RV8GR checkpoint
> notes below when they disagree. The pushed `main` baseline is `de1438c Add
> Component language text IDE foundation`. The shared worktree also contains
> the next, uncommitted Component-runtime and student-documentation work; do
> not describe it as pushed until its owner commits it. `Language.zip` is
> user-owned and remains untracked/untouched.

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
- Base pushed state: `de1438c Add Component language text IDE foundation`
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
