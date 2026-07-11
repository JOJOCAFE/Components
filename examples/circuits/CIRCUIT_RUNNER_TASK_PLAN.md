# Circuit Runner Implementation Checklist

Owner: Fern (verification)  
Coordinator: Pim  
Scope: backlog logical item 2 and modeled-timing item 3.  
Status values: `pending`, `in-progress`, `blocked`, `completed`.

This is the durable implementation and promotion checklist consolidated from
`docs/CIRCUIT_RUNNER_ARCHITECTURE.md`,
`examples/circuits/CIRCUIT_RUNNER_VERIFICATION_PLAN.md`, and
`docs/CIRCUIT_RUNNER_STUDENT_CONTRACT.md`. A status changes only with the named
acceptance evidence. Static campaign generation cannot promote a package.

## Status Summary

| ID | Milestone | Owner | Status |
|---|---|---|---|
| D0 | Design sprint: architecture, verification, student contract | Bank / Fern / Noon | `completed` |
| 2.1 | Phase 1A: live DB model loader | Bam | `completed` |
| 2.2 | Phase 1B: strict circuit-package compiler | Bam / Bank | `completed` |
| VS1 | RingCounter direct-execution vertical slice | Bam / Mint / Fern | `completed` |
| 2.3 | Functional service, CLI, and API integration | Bam / Noon | `completed` |
| 2.4 | Range, bidirectional, rail, virtual, audit, and hierarchy foundations | Bam / Bank / Fern | `completed` |
| 2.5-2.14 | Remaining logical package promotion and evidence | named below | `in-progress` / `blocked` |
| 3.1 | T1: timing normalization and path selection | Bam / Ohm | `completed` |
| 3.2 | T2: scheduler, checks, and first package timing binding | Bam / Fern | `in-progress` |
| 3.3-3.10 | Remaining timing item 3 implementation and promotion | named below | `pending` |

## Landed Foundation Evidence

- Phase 1A is complete in `python/chiplib/model_loader.py` and
  `python/tests/test_model_loader.py`: active `74xx`, `Memory`, and `Support`
  packages resolve deterministically; factories are cached; created chips carry
  source provenance; missing, duplicate, invalid, and identity-mismatched models
  fail explicitly. The focused module reports 8 passing tests.
- Phase 1B is complete in `python/chiplib/circuit_package.py` and
  `python/tests/test_circuit_package.py`: all 22 current
  `components.lib.circuit` packages parse into typed immutable records, while
  malformed files, duplicate declarations, missing proof/source files, unknown
  pins/references, and undeclared symbolic boundaries produce structured
  errors. The focused module reports 7 passing tests.
- T1 is complete in `python/chiplib/timing.py` and
  `python/tests/test_timing_profile.py`: six four-state transition classes plus
  clock-to-Q normalize to integer picoseconds, conservative selections retain
  exact/generic/path/default/not-applicable provenance, and all 70 active
  digital definitions normalize. This layer is deliberately scheduler
  independent.
- The completed RingCounter vertical slice is concrete in
  `python/chiplib/circuit_runner.py` and `python/tests/test_circuit_runner.py`;
  its focused module reports 10 passing tests through live 74HC164/74HC04 DB
  models and package wiring. It covers edge hold, isolated sessions, shuffled
  declaration order, declared proof execution, and reachable `000` recovery.
  Four other illegal states remain explicitly uninjectable because 74HC164 has
  no public state-load API; the tests report that limit instead of mutating
  private model state.
- Functional student access is complete in `python/chiplib/services.py`,
  `python/chiplib/cli.py`, and `python/chiplib/api.py`. Stateful `validate`,
  `load`, `run`, `step`, and `probe` operations preserve the outer service
  contract and return structured blocked/error results for unsupported work.
- The runner now supports ordered ranges, logic vectors, bidirectional release,
  VCC/GND rails, and named virtual adapters. Seven packages load:
  `RV8GR_AluAccumulator`, `RV8GR_BranchJumpControl`, `RV8GR_IRQLatch`,
  `RV8GR_ResetClockBringup`, `RV8GR_RingCounter`, `RV8GR_RomDbusRead`, and
  `RV8GR_StorePath`. Loadability is not promotion: RingCounter,
  BranchJumpControl, IRQLatch, ResetClockBringup, RomDbusRead, and StorePath
  currently pass their direct package proof gates.
- The package audit executes all 22 declared proof packages through public
  runner entry points. Six blocked loadable packages retain bounded partial
  observations: IRQLatch executes three checks; ResetClockBringup and
  RomDbusRead execute one check each; AluAccumulator reaches a later
  state/write-observation blocker after live checks. Partial
  observations never promote a blocked package.
- `python/chiplib/circuit_hierarchy.py` provides deterministic recursive plans,
  cycle detection, qualified names, and mapping diagnostics. The two current
  composites remain blocked because their package JSON does not provide enough
  authoritative child-port mappings; no same-name wiring is inferred.
- T2 has started in `python/chiplib/events.py` and
  `python/tests/test_event_scheduler.py` with integer-picosecond ordering,
  explicit phases/deltas, inertial cancellation, transport opt-in, convergence
  limits, and canonical snapshots. `python/chiplib/timed_runner.py` adds
  propagation, clock-to-Q, setup/hold/pulse checks, four-state contention,
  deadband, and deterministic traces. `python/chiplib/circuit_timing.py` binds
  that machinery to the live RingCounter package. RingCounter passes automatic
  before/at/after setup, hold, and pulse-width checks; this is not modeled-
  timing promotion for the other campaign gaps.
- The integrated DB worktree command `cd python && python3 -B -m tests.test_db`
  passes and prints `Components DB tests passed`. Its manual runner now includes
  the focused 74HC593 public/layer timing assertion. Propagation and three-state
  rows are exact in both views; clock-to-Q, setup, hold, and minimum-pulse-width
  rows are currently missing publicly and exact in the definition timing layer.
  This records the current split accurately and does not claim full parity.

Current focused commands:

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

## Logical Item 2: Direct Live-Model Execution

| ID | Work and exact files | Owner | Depends on | Acceptance | Status |
|---|---|---|---|---|---|
| 2.1 Phase 1A | Load executable chip models directly from active DB packages in `python/chiplib/model_loader.py`; export the loader through `python/chiplib/__init__.py`; cover deterministic group resolution, cached factories, provenance, and explicit rejection paths in `python/tests/test_model_loader.py`. | Bam | D0 | `cd python && python3 -B -m tests.test_model_loader`; 8 tests pass and every created chip is tied to one validated live DB definition/model path. | `completed` |
| 2.2 Phase 1B | Compile `components.lib.circuit` JSON into strict runtime-independent typed records in `python/chiplib/circuit_package.py`; cover all current packages and structured endpoint/reference/file errors in `python/tests/test_circuit_package.py`. | Bam / Bank | 2.1 | `cd python && python3 -B -m tests.test_circuit_package`; 7 tests pass, including all 22 packages, numeric ranges, symbolic boundaries, and collected stable issue codes. | `completed` |
| VS1 RingCounter vertical slice | Join the landed package compiler and live DB model loader to execute `examples/circuits/RV8GR_RingCounter/circuit.json` directly with 74HC164/74HC04 models. Add the functional kernel/session needed for net union, `0/1/Z/X`, convergence, deterministic clock capture/commit, asynchronous `/CLR`, and package proof-vector execution. | Bam / Mint; Fern gate | 2.1, 2.2 | Focused direct-execution tests prove clear `000`, T0/T1/T2 sequencing, non-rising-edge hold, reachable illegal-state recovery, isolated sessions, shuffled-order determinism, and declared package proof execution. States requiring a nonexistent public model state-load API are reported explicitly. | `completed` |
| 2.3 | Integrate functional mode through `python/chiplib/services.py`, `python/chiplib/cli.py`, and `python/chiplib/api.py`; add/extend `python/tests/test_simulation_service.py`, `python/tests/test_cli.py`, `python/tests/test_api.py`, and `python/tests/test_circuit_runner_student_contract.py`. Preserve `components.service.v1`; expose additive metadata, exact locations, diagnostics, snapshots, probes, and nonzero failures. | Bam / Noon | 2.1, 2.2 | Named standard-library modules pass; stateful circuit commands never report pass for unsupported work and capability discovery exposes the additive commands. | `completed` |
| 2.4 | Implement concrete package execution foundations: ordered ranges/vectors, bidirectional release, rails, named virtual adapters, fail-closed package audits, and deterministic hierarchy planning. Reject ambiguous widths, generic virtual parts, and absent child mappings instead of guessing. | Bam / Bank / Fern | 2.1-2.3 | Standard-library runner, package-audit, virtual-runtime, and hierarchy modules pass. Seven packages are loadable; every non-promoted package returns a structured blocker. | `completed` |
| 2.5 Batch A | Promote `RV8GR_VirtualTestHelpers` through `python/tests/test_circuit_runner_packages.py` and its package proof JSON. | Fern (gate), Bam | 2.4 | Shared direct batch gate below; helper, stimulus, probe, clock, delay/noise, and diagnostics pass. | `blocked`: public runner reports unresolved output and unsupported port-direction contracts |
| 2.6 Batch B | Promote `RV8GR_BranchJumpControl` and `RV8GR_StorePath`. | Fern (gate), Bam | 2.5 | Shared direct batch gate; exhaustive active-low decode, priority, hold, and store vectors pass. | `completed`: BranchJumpControl passes 9/9 live vectors and StorePath passes its five declared public-runner vectors. |
| 2.7 Batch C | Promote `RV8GR_ResetClockBringup`, `RV8GR_BusOwnership`, and `RV8GR_FullControlOpcodeSweep`. | Fern (gate), Bam / Mint | 2.6, 2.2 | Shared direct batch gate; reset/ring state, all 512 opcode/Z cases, high-Z, contention, and deadband checks pass. | `in-progress`: ResetClockBringup is promoted through its complete reset and six-push sequence; BusOwnership has ambiguous symbolic width; FullControlOpcodeSweep remains composite-blocked |
| 2.8 Batch D | Promote `RV8GR_FetchCycleTrace`. | Fern (gate), Bam / Mint | 2.7 | Shared direct batch gate; T0/T1/T2, ROM/DBUS/IBUS handoff, latch edge, and PC trace match the package and Verilog boundaries. | `blocked`: public runner reports unresolved outputs |
| 2.9 Batch E | Promote `RV8GR_StoreLoadBranchTrace`, `RV8GR_PageJumpTrace`, and `RV8GR_InterruptTrace`. | Fern (gate), Bam / Mint | 2.8 | Shared direct batch gate; independent SB/LB/BEQ, page/jump, and IRQ intermediate traces pass. | `blocked`: current audits report ambiguous range width, unresolved outputs, unsupported port direction, or non-executable composition |
| 2.10 Batch F | Promote `RV8GR_BootSequenceTrace` and `RV8GR_Lab13MarkerTrace`. | Fern (gate), Bam / Mint | 2.9 | Shared direct batch gate; exact instruction-boundary state, bounded termination, isolation, and reversed-order traces pass. | `blocked`: current audits report ambiguous range width, unresolved outputs, or non-executable composition |
| 2.11 Batch G | Promote `RV8GR_WholeSystemChipLevelVirtual`. | Fern (gate), Bam / Mint | 2.10 | Shared direct batch gate; boot, Lab 13, RAM/page/IRQ/bus stress and lower-package checkpoints pass within event limits. | `blocked`: package JSON lacks authoritative mappings for required child ports and abstract parts lack executable contracts |
| 2.12 | Apply the shared batch gate in `python/tests/test_circuit_runner_packages.py`: red contract, bind, all proof vectors, controlled negative, oracle/equivalence, isolation, bounded execution, and fresh-process determinism. | Fern | 2.5-2.11 incrementally | Every promoted package passes; no skip, xfail, warning-only result, flaky rerun, or final-state-only comparison counts. | `in-progress`: all 22 packages are audited fail-closed; partial observations and exact A-G blocker sets are gated, while deeper negatives/equivalence remain tied to future promotions |
| 2.13 | Add required direct, equivalence, determinism, and focused negative lanes to `.github/workflows/python-tests.yml`; retain existing suites. | Fern | 2.5-2.6 before fast lane; later batches as promoted | CI fails nonzero with package/time/net/value/driver context and compares byte-identical normalized traces under `PYTHONHASHSEED=0` and `1`. | `in-progress`: `circuit-campaign-promotion` runs the fresh report, package-proof audit, timing binding, and campaign determinism gates. Hash-seed determinism and promoted-package equivalence lanes remain required. |
| 2.14 | Reconcile `examples/circuits/RV8GR_COVERAGE_INDEX.json`, `tools/circuit_campaign_report.py`, `examples/circuits/RV8GR_CIRCUIT_TEST_CAMPAIGN.json`, and `.md`; extend `python/tests/test_lib_circuit_campaign.py`. | Fern / Pim | 2.5-2.13 | `python3 tools/circuit_campaign_report.py && cd python && python3 -B -m tests.test_lib_circuit_campaign`; all 13 packages have executable evidence and no `no_direct_live_component_model_test` basis. | `in-progress`: artifacts are execution-derived and deterministic; final acceptance waits on remaining genuine promotions |

## Timing Item 3: Deterministic Modeled Timing

| ID | Work and exact files | Owner | Depends on | Acceptance | Status |
|---|---|---|---|---|---|
| 3.1 T1 | Normalize DB timing independently of scheduling in `python/chiplib/timing.py`; cover transition classification, exact integer-picosecond conversion, conservative path/default selection, visible provenance/fallbacks, and all active digital definitions in `python/tests/test_timing_profile.py`. Read canonical package definitions through the DB; never copy part timing into runner code. | Bam / Ohm | 2.1, D0 | Run the focused `test_timing_profile` command above; all six logic transitions, clock-to-Q, representative 74HC245/74HC574/74HC161/62256/AT28C256 selections, fallback visibility, and all 70 active definitions pass. | `completed` |
| 3.2 T2 | Add deterministic timed event scheduling and checks after the scheduler-independent T1 layer; introduce focused scheduler tests. Cover clock-to-Q, memory access, setup, hold, pulse width, recovery, unknown edge, deadband, coherent failure snapshots, and `diagnose`/`drive_x`. | Bam / Fern | VS1, 3.1 | Tests pass one tick before, at, and after each threshold; X and Z remain distinct; overlap fails even for equal driven values; resource exhaustion and missing paths block rather than warn-pass. | `completed` for the RingCounter package gate; broader package bindings are tracked in 3.4-3.9 |
| 3.3 | Expose timed mode and student result contract through `python/chiplib/services.py`, `python/chiplib/cli.py`, and `python/chiplib/api.py`; extend service/CLI/API tests and `python/tests/test_circuit_runner_student_contract.py`. | Bam / Noon | 2.3, 3.2 | `timed-run`, `explain-violations`, and `export-evidence` return the contract fields or `runner.command_not_implemented`; requested unsupported timing returns `blocked`; exported evidence preserves violations, provenance, and physical boundary. | `completed`: timed commands expose explicit RingCounter binding evidence and preserve `blocked` for unsupported package timing. |
| 3.4 Batch B | Promote timing anchors `RV8GR_IRQLatch` and `RV8GR_RomDbusRead`; retain existing timing passes for BranchJumpControl/StorePath and timing N/A for helpers. | Fern (gate), Bam / Ohm | 3.2, 3.3; direct promotion | Shared timing gate below; IRQ release and ROM valid/disable windows pass. | `pending` |
| 3.5 Batch C | Promote timed ResetClockBringup, BusOwnership, and FullControlOpcodeSweep. | Fern (gate), Bam / Mint / Ohm | 3.4, direct 2.7 | Shared timing gate; edge ordering, X/Z, deadband, and overlap thresholds pass. | `pending` |
| 3.6 Batch D | Promote timed FetchCycleTrace. | Fern (gate), Bam / Mint / Ohm | 3.5, direct 2.8 | Shared timing gate; fetch event sequence and output-valid/high-Z windows pass. | `pending` |
| 3.7 Batch E | Promote timed StoreLoadBranchTrace, PageJumpTrace, and InterruptTrace. | Fern (gate), Bam / Mint / Ohm | 3.6, direct 2.9 | Shared timing gate; memory turnaround, page edge, and IRQ pulse constraints pass. | `pending` |
| 3.8 Batch F | Promote timed BootSequenceTrace and Lab13MarkerTrace. | Fern (gate), Bam / Mint / Ohm | 3.7, direct 2.10 | Shared timing gate; bounded deterministic instruction traces pass. | `pending` |
| 3.9 Batch G | Promote timed WholeSystemChipLevelVirtual. | Fern (gate), Bam / Mint / Ohm | 3.8, direct 2.11 | Shared timing gate; all lower checkpoints and critical event perturbation negatives pass. | `pending` |
| 3.10 | Apply the shared timing gate in `python/tests/test_circuit_runner_packages.py`; add required timing lane to `.github/workflows/python-tests.yml`; reconcile campaign files and `python/tests/test_lib_circuit_campaign.py`. | Fern / Pim | 3.4-3.9 | All 12 gaps pass event order, edge/window, X/Z, deadband, threshold negatives, equivalence, limits, and hash-seed determinism with timing provenance; CI has no warning-pass mode; campaign has no timing gap and uses only `modeled_timing_pass` wording. | `pending` |

## Physical Boundary

Completion of items 2 or 3 proves software behavior only. It must not change
`physical_status` or claim safe wiring, voltage/frequency readiness, or hardware
timing. Physical acceptance remains in
`examples/circuits/physical_capture_plan.json` and
`examples/circuits/RV8GR_END_TO_END_TEST_PLAN.md`: installed part markings,
clock/reset scope captures, EEPROM/SRAM access-float-write timing, quantified bus
deadband/no-overlap, VCC quality, wiring inspection, and 4.5/5.0/5.5 V frequency
sweeps must be measured on the real build.

## Pim Handoff Rule

Pim updates this file only from named test/CI evidence. Fern reviews every
promotion. DB definitions, Python behavior, Verilog equivalence, package proof
JSON, student diagnostics, campaign output, and CI must move together; a design
document, generated report, manual trace inspection, skip, or rerun is not
completion evidence.
