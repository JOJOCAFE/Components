# Components Session Handoff

Last updated: 2026-07-11

## Current State

- Repo: `/home/jo/kiro/Components`
- Branch: `main`
- Base pushed state: `8a0de62 Refine 74HC593 timing evidence`
- This handoff describes the verified follow-up checkpoint for the NE555
  contract fix, generated-report drift gate, and coordination-doc refresh.

## Active Verified Worktree

- Repository layout migrated on 2026-07-12: packages live in
  `lib/standard/`; circuit examples and proof assets live in
  `examples/circuits/`; documentation, schemas, source evidence, and Verilog
  live in `docs/`, `schemas/`, `source/`, and `verilog/` respectively.
  `tools/verify_repository_layout.py` and its CI/test gate reject stale
  legacy-root references.
- The lower-case moved roots are intentionally unstaged. Git therefore shows
  the old tracked roots as deletions and the new roots as untracked until the
  migration is staged; do not use that display as evidence that files are gone.
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
- BusOwnership and FullControl remain blocked by missing concrete boundary
  width/control contracts. Physical RV8GR evidence remains separate and open.

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
