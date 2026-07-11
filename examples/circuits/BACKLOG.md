# Circuit Library Backlog

Last reconciled: 2026-07-11 against the current worktree; last pushed baseline
was commit `8a0de62`.

## Active Circuit Runner Work

The durable implementation checklist for logical item 2 and modeled-timing item
3 is `examples/circuits/CIRCUIT_RUNNER_TASK_PLAN.md`. Fern owns promotion gates; Pim
coordinates implementation across specialists.

Current state:

- `completed`: design sprint; Phase 1A (`2.1`, live DB model loading); Phase 1B
  (`2.2`, strict typed circuit-package compilation); and T1 (`3.1`,
  scheduler-independent timing normalization/path selection).
- `completed`: RingCounter direct execution (`VS1`), functional stateful
  service/CLI/API commands (`2.3`), and the range/vector, bidirectional, rail,
  named-virtual, fail-closed audit, and hierarchy foundations (`2.4`).
- `completed`: T2 (`3.2`) for the RingCounter package gate. Automatic setup,
  hold, pulse-width, propagation, clock-to-Q, Z-transition, and deadband checks
  pass the before/at/after threshold contract. Other package timing batches
  remain pending.
- `pending` or `blocked`: later package promotion batches, timed CLI/API, and
  the remaining CI equivalence/hash-seed promotion lanes. The campaign report
  and its deterministic freshness gate are active.

Current focused verification commands are:

```sh
cd python
python3 -B -m tests.test_model_loader
python3 -B -m tests.test_circuit_package
python3 -B -m tests.test_timing_profile
python3 -B -m tests.test_circuit_runner
python3 -B -m tests.test_circuit_runner_packages
python3 -B -m tests.test_circuit_runner_student_contract
python3 -B -m tests.test_event_scheduler
python3 -B -m tests.test_timed_runner
python3 -B -m tests.test_circuit_timing
python3 -B -m tests.test_circuit_hierarchy
python3 -B -m tests.test_virtual_runtime
python3 -B -m tests.test_simulation_service
python3 -B -m tests.test_cli
python3 -B -m tests.test_api
python3 -B -m tests.test_db
```

The first two focused modules report 8 and 7 passing tests respectively, the
timing command covers all six transition classes and all 70 active digital
definitions, and the runner reports 10 passing focused tests. Service, CLI,
API, virtual-runtime, hierarchy, package-audit, scheduler, timed-runner, and
RingCounter timing-binding modules use standard-library commands. T2 remains
in progress because package-level timing is bound only to RingCounter. The
integrated DB worktree command passes with `Components DB tests passed`, and its
manual runner includes the focused 74HC593 public/layer timing assertion. That assertion
currently verifies exact propagation and three-state rows in both views while
recording clock-to-Q, setup, hold, and minimum-pulse-width rows as `missing` in
the public timing view and `exact` in the definition timing layer; it does not
claim full public/layer parity or T2 completion.

Logical item 2 requires direct live-model execution for the 13 campaign gaps.
Timing item 3 requires deterministic modeled-timing execution for the 12 timing
gaps. Package order, owners, dependencies, exact files, and acceptance tests are
in the task plan; campaign generation alone cannot promote either item.

Current promotion boundary:

- Eight packages are loadable by the functional runner:
  `RV8GR_AluAccumulator`, `RV8GR_BranchJumpControl`, `RV8GR_IRQLatch`,
  `RV8GR_ResetClockBringup`, `RV8GR_RingCounter`, `RV8GR_RomDbusRead`, and
  `RV8GR_StorePath`, and `RV8GR_VirtualTestHelpers`.
- `RV8GR_RingCounter`, `RV8GR_BranchJumpControl`, `RV8GR_IRQLatch`,
  `RV8GR_ResetClockBringup`, `RV8GR_RomDbusRead`, `RV8GR_StorePath`, and
  `RV8GR_VirtualTestHelpers` are
  directly promoted;
  BranchJumpControl passes all nine declared vectors after the package gained
  its required `/JUMP` inversion. Loadability is not proof completion. The
  public proof audit executes all 22 packages fail-closed. AluAccumulator
  reaches a later state/write-observation blocker after live checks.
  Partial observations remain blocked evidence and cannot count as promotion.
- Batches A-G all have current structured public-runner results. D-F are now
  explicitly blocked by unresolved outputs, width/port contracts, or
  non-executable composition rather than left as generic pending work.
- `RV8GR_FullControlOpcodeSweep` and
  `RV8GR_WholeSystemChipLevelVirtual` remain blocked by absent authoritative
  child-port mappings. Same-name connections are not inferred.
- RingCounter is the only package with promoted live package-level modeled
  timing. Its nine before/at/after setup, hold, and pulse-width checks execute
  through `CircuitTimingBinding`; all later timing batches remain pending or
  blocked.
- `.github/workflows/python-tests.yml` has a dedicated
  `circuit-campaign-promotion` job. It fails closed on stale execution-derived
  artifacts and runs the package-proof audit, timing binding, and campaign
  determinism gates; it does not yet replace the required equivalence and
  hash-seed lanes.

These are software gates. `physical_status` remains unchanged until the real
RV8GR build completes `physical_capture_plan.json` and
`RV8GR_END_TO_END_TEST_PLAN.md` measurements.

## Completed Software Work

- RV8GR chip readiness is project-neutral on the Components side, with all 18
  definition/options entries carrying datasheet-backed timing/electrical data
  sufficient for functional circuit progression.
- `tests.test_generated_split_records` checks definitions and truth, timing,
  tri-state, bus-fight, and propagation records.
- `RV8GR_COVERAGE_INDEX.json` maps every `RV8GR_*` package to its README, JSON
  proof, and executable `tests.test_lib_circuits` coverage. Every indexed
  package is `Tested`.
- Instruction traces cover fetch/LI and SB/LB/BEQ.
- `RV8GR_PageJumpTrace` covers SETDP, SETPG, and J.
- `RV8GR_InterruptTrace` covers EI, DI, IRQ release, and sticky IRQ state.
- `RV8GR_BootSequenceTrace` covers `SETDP $80`, `SETPG $00`, `LI $00`, and
  `J self`; `RV8GR_Lab13MarkerTrace` covers the Lab 13 `$AA` marker program.
- `RV8GR_WholeSystemChipLevelVirtual` covers the full chip-level virtual gate,
  including boot, Lab 13, RAM/page/IRQ/bus traces, R/C and delay/noise stress.
- The reusable virtual physical-system fault checker and
  `chiplib.cli circuit-faults` detect wrong pins, invalid output-output wiring,
  missing edge polarity, and missing delay/deadband declarations.
- The RV8GR whole-system Verilog gate was recorded passing via
  `/home/jo/kiro/RV8/RV8GR/tools/run_all_verilog_tb.sh`.

RV8GR v1.0 has no core CPU-visible IRQ status register. Polling proof must use
RV8-Bus or external `/SLOT` visibility, or remain an LED/bench observation.

## Timing And Physical Evidence

Definition-level timing extraction is complete for the RV8GR set, but physical
timing is not proven. `timing_margins.json` deliberately separates:

1. Functional edge, phase, and bus-ownership proofs.
2. source/model timing rows, path budgets, and slack calculations.
3. Physical measurements from the installed build.

Remaining physical work:

1. Record actual EEPROM and SRAM markings and selected datasheet speed rows.
2. Single-step the boot sequence and Lab 13 `$AA` program on the real build.
3. Run RAM read/write, page jump, and IRQ latch/continuity checks.
4. Capture clock/reset and destination edges, memory access/float/write timing,
   quantified bus deadband, VCC quality, and no-driver-overlap evidence.
5. Run the 4.5 V, 5.0 V, and 5.5 V sweep at 100 manual ticks, 50 kHz, 1 MHz,
   2 MHz, and 5 MHz if attempted.

Until those records exist, boot/Lab13/whole-system completion means software
coverage only. Hardware 5 MHz readiness and student speed recommendations stay
blocked.

## Waiting Items

- Visual chip-block editor implementation: waiting by user request. Backend
  metadata, `components.block_ui`, and `docs/VISUAL_MODULE_PLAN.md` are ready.
- MCP adapter: waiting until editor/service command names and state transitions
  settle. It must remain a thin adapter over the existing service contract.
- Additional trace packages: no current gap. Add one only for a newly identified
  CPU behavior not covered by the index or RV8GR whole-system benches.

## Historical Checkpoints

- `8bb462b`: RV8GR virtual fault protocol.
- `49ed732`: reusable circuit fault checker.
- `86341c5`: whole-system virtual gate.
- `152db2c`: exact timing extraction and visual module plan.

The active campaign and acceptance boundary are in
`examples/circuits/RV8GR_END_TO_END_TEST_PLAN.md`.
