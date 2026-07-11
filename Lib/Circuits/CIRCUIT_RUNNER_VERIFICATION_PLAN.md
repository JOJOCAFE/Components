# Circuit Runner Verification Plan

Owner: Fern (verification)
Scope: backlog item 2, direct live-model circuit execution, and backlog item 3,
direct modeled-timing execution. This plan specifies tests and promotion gates;
it does not authorize runtime implementation or physical signoff claims.

## Verification Boundary

The committed campaign records 13 packages with
`direct_live_model_status: not_directly_executed` and 12 packages with
`modeled_timing_status: not_directly_executed`. Package-shape checks, static
equations, and hand-computed vectors are useful oracles, but they are not a
substitute for executing the composed circuit through live component models.

This plan promotes only software evidence. Datasheet timing is an input to a
model; deterministic model timing is not measured board timing. Voltage sweep,
installed chip markings, clock/reset scope captures, memory float/write timing,
bus deadband, signal integrity, and maximum-frequency claims remain exclusively
in `physical_capture_plan.json` and the physical stage of
`RV8GR_END_TO_END_TEST_PLAN.md`.

## Fail-Loudly Contract

Every runner test must fail with a nonzero test result and identify the package,
vector or trace step, simulation time, net, expected value, observed value, and
active drivers. The runner must never convert an unknown component, unresolved
net, bus conflict, missing timing path, event-limit exhaustion, or non-convergent
delta cycle into a pass, a default logic level, or a warning-only result.

Each package advances through these stages:

1. **Red contract:** add a test that proves the current no-direct status cannot
   be reported as pass. Confirm the test fails for the intended missing runner
   capability, not because of malformed fixtures or imports.
2. **Load and bind:** require every component type, instance, pin, net, active-low
   control, initial state, and stimulus endpoint to resolve. Unknown or duplicate
   bindings fail before time zero.
3. **Functional execution:** replay the committed JSON vectors through live
   models. Compare every declared observation at every declared step; no package
   may be promoted from a smoke-only run.
4. **Negative execution:** inject one controlled fault at a time and prove the
   runner rejects it with the expected diagnostic class.
5. **Equivalence:** compare runner observations with the existing package oracle
   and, where an RV8GR Verilog bench covers the same boundary, compare a canonical
   normalized trace against that bench.
6. **Timed execution:** for the 12 timing-applicable packages, execute the same
   stimulus under explicit timing data and assert event order, edge polarity,
   output-valid windows, high-Z intervals, and setup/hold or deadband constraints.
7. **Determinism:** repeat in fresh processes and under at least two hash seeds;
   byte-identical normalized traces and identical diagnostics are required.
8. **Promotion:** update campaign status only after all gates for that package and
   all prerequisite batches pass in CI. A test skip, expected failure, warning,
   flaky rerun, or manually inspected trace is not a pass.

## Package Batches

The order follows dependency depth first and risk second. A batch cannot enter
promotion CI until all earlier prerequisite batches are green.

| Batch | Packages | Gap | Dependency and risk basis |
|---|---|---|---|
| A - runner substrate | `RV8GR_VirtualTestHelpers` | direct only; timing N/A | Proves stimulus, probe, clock-profile, delay/noise helper, and diagnostic plumbing before CPU composition. Highest fan-out, no physical package claim. |
| B - primitive controls and timing anchors | `RV8GR_BranchJumpControl`, `RV8GR_StorePath` (direct); `RV8GR_IRQLatch`, `RV8GR_RomDbusRead` (timing) | first pair direct only; second pair timing only | Small boundaries with one gate already passing. Establishes active-low decode, select priority, store enable, asynchronous latch timing, and ROM/bus enable-disable timing before traces depend on them. |
| C - state and bus hazards | `RV8GR_ResetClockBringup`, `RV8GR_BusOwnership`, `RV8GR_FullControlOpcodeSweep` | direct and timing | Depends on A-B and primitive chip models. Highest semantic risk: reset state, edge ordering, reserved control combinations, high-Z, multi-driver rejection, and deadband. |
| D - fetch composition | `RV8GR_FetchCycleTrace` | direct and timing | Depends on C plus already-direct `RingCounter`, `PC16`, `AddressMux16`, `RomDbusRead`, and `InstructionLatch`. First complete clocked trace. |
| E - instruction-path traces | `RV8GR_StoreLoadBranchTrace`, `RV8GR_PageJumpTrace`, `RV8GR_InterruptTrace` | direct and timing | Depend on D, B, and existing direct ALU/register/memory/IRQ models. Split failures by store/load bus risk, page/program control risk, and asynchronous IRQ edge risk. |
| F - program traces | `RV8GR_BootSequenceTrace`, `RV8GR_Lab13MarkerTrace` | direct and timing | Depend on D and E. Longer deterministic traces expose state leakage, termination errors, and incorrect repeated-cycle scheduling. |
| G - whole system | `RV8GR_WholeSystemChipLevelVirtual` | direct and timing | Depends on A-F. Highest fan-in and runtime risk; promoted only after every lower package is green. |

Count check: A-G contain all 13 no-direct packages. The timing set contains ten
of those packages plus timing-only `RV8GR_IRQLatch` and `RV8GR_RomDbusRead`, for
exactly 12 no-direct-timing packages. `RV8GR_BranchJumpControl` and
`RV8GR_StorePath` already pass modeled timing; `RV8GR_VirtualTestHelpers` is
timing N/A.

## Batch Gates And Negative Tests

### Batch A - Runner Substrate

Required positives: deterministic stimulus ordering, probe sampling before/after
an edge, bounded delay/noise injection, explicit high-Z representation, and a
stable normalized trace schema.

Required negatives: unknown helper type, missing endpoint, invalid clock period,
negative delay, duplicate timestamp with undefined ordering, event queue overflow,
and an unseeded random/noise request. Each must fail before producing a pass
record. Promotion requires diagnostics to name the bad helper and field.

### Batch B - Primitive Composed Controls

Required positives: exhaust committed truth vectors, assert active-low polarity,
decode priority, mutually exclusive actions, hold/no-write cases, IRQ latch
assert/release timing, and ROM-to-DBUS propagation plus enable/disable windows.

Required negatives: invert `/PC_LD` or write polarity, assert incompatible store
sources, omit a required select, swap a bound pin, introduce an unsupported logic
value, release IRQ on the wrong modeled edge, make ROM data valid late, or retain
ROM drive after its disable limit. The runner must detect oracle mismatch,
structural invalidity, or a timing-window violation. Promotion requires direct
traces to match the existing logical oracle for every vector; existing passing
direct or timing status must remain unchanged while its missing counterpart is
promoted.

### Batch C - State And Bus Hazards

Required positives: reset from every reachable ring state; T0/T1/T2 progression;
all 512 opcode/Z cases; single-owner and no-owner high-Z windows on IBUS/DBUS;
and explicit control transition timestamps.

Required negatives: wrong clock edge, omitted reset, illegal ring state,
simultaneous bus drivers, zero deadband where a positive deadband is declared,
reserved-opcode control overlap, delta-cycle oscillation, and driver release
after replacement-driver enable. Bus fights must fail at the first conflicting
timestamp and list all drivers.

Promotion requires exhaustive control coverage, lower-state recovery, no hidden
default driver, and deterministic event ordering at coincident control changes.

### Batch D - Fetch Composition

Required positives: reset through T0/T1/T2 fetch, ROM address selection, DBUS to
IBUS handoff, instruction-latch edge capture, PC increment, and post-fetch hold.

Required negatives: ROM output late, DBUS transceiver enabled early, instruction
latch triggered on the wrong edge, PC increment duplicated or omitted, and ROM/U7
overlap. Promotion requires cycle-by-cycle agreement with the package oracle and
the matching RV8GR fetch/chip-level Verilog trace at the shared signals.

### Batch E - Instruction-Path Traces

Required positives: SB/LB/BEQ taken and not taken; SETDP/SETPG/J; EI/DI; `/IRQ`
assertion and release; sticky IRQ state; memory read/write turnaround; and page
register edge capture.

Required negatives: RAM write outside its legal phase, stale read data, missing
memory float interval, branch polarity error, page clock on wrong edge, IRQ pulse
shorter than the declared modeled acceptance window, DI changing unrelated state,
and a fabricated CPU-visible IRQ polling path. Promotion requires independent
trace equivalence per package so one passing end state cannot mask an intermediate
timing or bus error.

### Batch F - Program Traces

Required positives: exact boot and Lab 13 instruction streams, expected state at
every instruction boundary, explicit halt/pass termination, and a bounded maximum
cycle count.

Required negatives: one-bit ROM mutation, unexpected opcode, off-by-one PC,
incorrect page state, missing marker write, nonterminating self-loop before the
declared terminal state, and retained state from a prior run. Promotion requires
fresh-process execution and identical traces when package order is reversed.

### Batch G - Whole System

Required positives: compose all live models; replay boot, Lab 13, RAM/page/IRQ,
and bus stress scenarios; preserve package-level checkpoints; and report total
events and bounded completion time.

Required negatives: remove one required component, alias two nets, reverse one
active-low control, inject a bus overlap, perturb a critical event by one model
tick, exceed the event budget, and mutate a lower-package expected checkpoint.
Promotion requires every injected fault to be detected and attributed; a final
state match cannot override an intermediate package failure.

## Equivalence Checks

Equivalence is checked at explicit observation boundaries, not by comparing only
final states:

- **JSON oracle versus runner:** every committed vector or trace step maps to a
  normalized `(time, phase, signal, value, drivers)` observation.
- **Direct package versus composed package:** lower-package checkpoints embedded
  in traces must equal the standalone direct-run trace for the same stimulus.
- **Python versus Verilog:** use shared architectural signals and cycle/phase
  labels for fetch, opcode sweep, store/load/branch, page/jump, IRQ, boot, Lab 13,
  and whole-system benches. Normalize X/Z explicitly; never coerce them to 0/1.
- **Definition versus execution:** pin numbers/names, active-low markers, edge
  polarity, tri-state enable rules, and timing-path identifiers used by a run must
  match the loaded definition. Any missing path blocks timed promotion.

Where Verilog has no identical internal signal, record that boundary as
`not_comparable` with a reason and retain JSON/direct-package equivalence. It must
not be silently counted as a Verilog pass.

## Deterministic Timing Checks

The timed lane uses integer simulation ticks with one declared conversion to
nanoseconds. Floating-point wall time and host scheduling must not affect results.

For every timing-applicable package:

1. Require an explicit timing profile and record the source path and selected
   value in the trace header.
2. Define same-timestamp ordering for stimulus, model evaluation, net resolution,
   edge capture, and observation. Assert that ordering with a focused test.
3. Check minimum/maximum event timestamps, not only eventual values; verify
   propagation, enable, disable, setup, hold, and recovery paths when applicable.
4. Represent high-Z and unknown distinctly. Assert break-before-make intervals
   and reject overlapping enabled drivers even when they drive the same value.
5. Bound delta cycles, total events, and simulated duration. Exceeding a bound is
   a failure with the last stable event, never a timeout-only CI message.
6. Run each canonical trace three times in fresh processes with `PYTHONHASHSEED=0`
   and `PYTHONHASHSEED=1`; normalized trace digests must match across all runs.
7. Test boundary values at one tick before, exactly at, and one tick after each
   declared setup/hold/deadband threshold.

Timing assertions prove only the selected model and profile. They must use terms
such as `modeled_timing_pass`, never `hardware_timing_pass`.

## CI Lanes

| Lane | Trigger | Required work | Failure policy |
|---|---|---|---|
| `circuit-contract` | Every PR touching circuit JSON, definitions, runner, or tests | Schema/binding checks, campaign count check, red-contract guard, package shape and source integrity | Required; no skips for promoted packages |
| `circuit-direct-fast` | Every relevant PR | Batches A-B and previously promoted direct packages, functional plus negative tests | Required; first mismatch prints focused trace context |
| `circuit-direct-stateful` | Every relevant PR | Batches C-E, exhaustive opcode vectors and state isolation | Required; split by package for attribution |
| `circuit-direct-system` | Every relevant PR after G exists | Batches F-G with event/cycle limits | Required; artifact normalized traces only on failure |
| `circuit-timing` | Every relevant PR | All promoted timing packages, threshold tests, X/Z and bus-deadband checks | Required; missing timing paths fail, no warning mode |
| `circuit-determinism` | Every relevant PR | Fresh-process/hash-seed matrix and trace digest comparison | Required; rerun success does not clear failure |
| `circuit-equivalence` | Every relevant PR | JSON-runner, standalone-composed, and available Python-Verilog trace comparisons | Required at declared comparable boundaries |
| `circuit-negative` | Nightly and before promotion; focused subset on PR | Fault-injection mutation matrix for current and promoted batch | Any undetected mutation blocks promotion |
| `rv8gr-external` | Nightly/release or RV8GR source change | Existing RV8GR Verilog runner and cross-repo trace comparison | Software integration gate; not physical signoff |

CI must publish package/status summaries generated from actual test results.
Static campaign generation cannot turn `not_directly_executed` into `pass`.

## Package Promotion Gates

A package may change `direct_live_model_status` to `pass` only when:

- its load/bind, functional, negative, equivalence, isolation, and determinism
  tests pass in the required CI lanes;
- all committed vectors execute through live models with no skipped observations;
- failures are nonzero and contain package/time/net/driver context;
- prerequisite batches are already promoted; and
- the campaign evidence points to named executable tests, not only static files.

A timing-applicable package may change `modeled_timing_status` to `pass` only when:

- direct live-model promotion is already complete;
- all used timing paths resolve to explicit definition/model data;
- edge, event-order, threshold, X/Z, high-Z, deadband, and bounded-execution tests
  pass deterministically;
- equivalent shared trace boundaries agree; and
- wording and status remain explicitly model-only.

`RV8GR_VirtualTestHelpers` may reach direct pass but must retain timing
`not_applicable`; helper self-tests do not create an independent package timing
claim.

## Backlog Acceptance Criteria

Backlog item 2 is complete only when all 13 listed packages have direct live
execution, all package promotion gates pass, the negative mutation suite proves
fail-loud behavior, CI requires the direct/equivalence/determinism lanes, and the
campaign contains no `no_direct_live_component_model_test` basis for them.

Backlog item 3 is complete only when all 12 listed timing-gap packages pass the
deterministic timed lane, every timing assertion identifies its selected model
path, threshold and bus-hazard negatives are detected, CI requires the timing
lane, and the campaign contains no `modeled_timing_status:
not_directly_executed` for them.

Neither item changes `physical_status`. Physical acceptance remains blocked
until the separate measurement plan is executed on the installed RV8GR build.
