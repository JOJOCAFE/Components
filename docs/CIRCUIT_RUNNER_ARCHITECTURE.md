# Reusable Net-Level Circuit Runner Architecture

Status: Bank architecture proposal for circuit backlog items 2 and 3.

This document defines one reusable digital circuit runner with two execution
modes: `functional` and `timed`. It is the architecture boundary between the
normalized Components design/netlist, chip behavior models, and the existing
CLI/API/UI services. It does not define a second chip database and does not make
SPICE, electrical, breadboard, or physical-signoff claims.

## Goals

The runner must:

- execute ordinary schematic JSON and normalized `chiplib.netlist` designs;
- use the same compiled graph and chip behavior in both modes;
- resolve pins, nets, buses, rails, pulls, sources, and aliases once;
- model `0`, `1`, `Z`, and `X`, including visible multi-driver contention;
- handle combinational propagation, clocks, asynchronous controls, and
  edge-triggered state without instance-order dependence;
- use package timing metadata when timed mode has an unambiguous supported path;
- report setup, hold, and minimum-pulse-width violations without pretending to
  model analog metastability;
- provide deterministic probes, snapshots, diagnostics, and resource limits;
- remain behind the existing `components.service.v1` service boundary; and
- preserve existing functional behavior while allowing stricter four-state and
  timed semantics to be introduced explicitly.

## Non-Goals And Physical Boundary

This is a net-level digital event simulator. It is not:

- SPICE or an analog solver;
- a transmission-line, impedance, current, thermal, fan-out, or signal-integrity
  model;
- a model of input thresholds, rise/fall slew, ringing, switch bounce, ground
  bounce, supply droop, decoupling, breadboard parasitics, or component damage;
- proof that a physical circuit works at a stated voltage or frequency; or
- proof that typical datasheet timing is safe across process, temperature,
  voltage, loading, wiring, and part substitutions.

`X` means digitally unknown or conflicting, not an analog voltage. Pulls are
weak logical defaults, not resistor/current calculations. Timing checks and
path delays are educational digital checks against selected metadata. Hardware
signoff still requires exact part markings, datasheet corners, scope captures,
voltage/frequency sweeps, bus deadband evidence, and real wiring inspection.

Support parts whose definitions explicitly say they are simplified functional
models, such as logic-level comparator/op-amp models, retain that boundary in
both runner modes.

## Existing Contracts To Preserve

The architecture is based on these live repository contracts:

- `Design` is the canonical, JSON-round-trippable schematic model.
- Schematic references use physical pin form (`U1:1`), bus form (`DATA:0`),
  aliases, groups, and named rails.
- `Design.to_netlist()` emits additive `chiplib.netlist` version 1 with the
  canonical design retained for round-trip compatibility.
- `Chip` models expose pins, `update()`, queued `output()`, `clock_edge_for_pin()`,
  and `clock_edge()`; model state remains owned by each chip instance.
- `SimulationService` owns `validate`, `snapshot`, `run`, `probe`, and
  `frontend-snapshot` responses under `components.service.v1`.
- Existing snapshots expose time, chips, nets, buses, rails, sources, errors,
  probes, displays, expectations, and step logs.
- Existing timing data is heterogeneous. Some packages provide
  `timing.simple.default_delay_ns` plus `timing.timed.paths`; others provide
  `timing.delay.default_ns`, `timing.timing_requirements`,
  `timing.timing_parameters`, or memory-specific `timing.paths` and
  `timing.write` fields.

The runner must consume timing through one normalization adapter. Kernel code
must not contain part names or private paths into package JSON.

`components.lib.circuit` files are descriptive circuit-library proof packages,
not automatically executable schematic JSON. Their `wiring` endpoints may use
dot notation, symbolic pins, ranges, and nested circuit parts. A separate
adapter may compile one only after every endpoint and range expands to concrete
instances and physical pins. Unsupported descriptive references must produce a
compile diagnostic; they must never be guessed.

## Architecture

```text
schematic JSON -----\
Design --------------> Input adapter -> CircuitCompiler -> CompiledCircuit
netlist v1 ----------/                         |                 |
lib circuit adapter (only when fully concrete)-/                 v
                                                     CircuitRunnerSession
chip DB definition -> TimingNormalizer -> TimingProfile          |
chip factory/model ---------------------> ModelAdapter            v
                                              EventKernel -> snapshots/probes
                                                           -> diagnostics
                                                           -> service result
```

There is one `CircuitRunner` implementation. Mode is a policy selected when a
session is created, not a separate simulator:

- `functional`: all supported propagation delays are zero simulation time;
  delta cycles still preserve causality and sequential phases.
- `timed`: output transitions are scheduled using a normalized selected path;
  timing checks are enabled when required metadata and pin-role mappings exist.

Both modes use the same four-state resolver, edge detector, sequential commit
algorithm, event ordering, probe recorder, diagnostics, and limits.

### Core Interfaces

The following Python-shaped interfaces are normative architecture, not a demand
for these exact class locations in the first implementation.

```python
Logic4 = Literal[0, 1, "Z", "X"]
RunnerMode = Literal["functional", "timed"]

@dataclass(frozen=True)
class RunnerOptions:
    mode: RunnerMode = "functional"
    timing_corner: str = "typ"
    vcc: str | None = None              # e.g. "vcc_4_5_v"
    device_variant: str | None = None
    unknown_timing: str = "warn_default"  # error | warn_default | zero
    contention: str = "diagnose"          # diagnose | fail
    violation_effect: str = "diagnose"    # diagnose | drive_x
    max_delta_cycles: int = 1000
    max_events: int = 100000
    max_time_ns: int | None = None
    max_same_time_events: int = 10000

class CircuitCompiler:
    def compile(self, design_or_netlist, options: RunnerOptions) -> "CompiledCircuit": ...

class CircuitRunner:
    def create_session(self, circuit: "CompiledCircuit", options: RunnerOptions) -> "RunnerSession": ...

class RunnerSession:
    def apply(self, assignments: Mapping[str, Logic4]) -> "RunDelta": ...
    def settle(self) -> "RunDelta": ...
    def advance(self, duration_ns: int) -> "RunDelta": ...
    def run_until(self, time_ns: int) -> "RunDelta": ...
    def step(self, command: str) -> "RunDelta": ...
    def snapshot(self, *, include_history: bool = False) -> dict: ...
    def probe(self, set_name: str = "default") -> dict: ...
```

### Compiled Circuit

`CompiledCircuit` is immutable and reusable across sessions. It contains:

- stable integer IDs for instances, pins, nets, drivers, receivers, and probes;
- canonical endpoint lookup tables;
- one net per electrically connected set of endpoints;
- pin direction, active-low display name, and physical pin number;
- driver-to-net and net-to-sensitive-instance adjacency;
- rails, pulls, external sources, clocks, and initial values;
- model factories or immutable model descriptors, never live model state;
- normalized timing profiles and pin/path mappings;
- compiled expectations and probe targets where possible; and
- source locations for all compile/runtime diagnostics.

No current signal value belongs in `CompiledCircuit`. Each `RunnerSession` owns
model state, driver state, net state, event queue, timestamps, histories, and
diagnostics so tests and API clients cannot leak state into each other.

## Endpoint And Net Resolution

Resolution is a compile-time operation with these steps:

1. Normalize list/map forms of chips, buses, probes, and input sets through
   `Design`; retain unknown additive metadata for round trips.
2. Build instance records and load each part through the existing Components DB
   and chip factory. Missing or ambiguous parts are compile errors.
3. Expand aliases recursively with cycle detection. Expand groups only where a
   command accepts multiple endpoints; a group is not itself an electrical net.
4. Resolve chip pins by physical number first. A symbolic pin name is accepted
   only when the package has one exact match. Preserve active-low names for
   display but use stable physical pin identity internally.
5. Resolve bus references to canonical `bus:<name>[<index>]`; reject negative,
   out-of-range, or undeclared widths.
6. Treat each connection rule as an undirected electrical equivalence relation.
   `->` and `<->` remain readability/intent metadata; they do not create a
   one-way electrical link.
7. Union connected endpoints, aliases, and explicit net/bus tags into one net.
   Choose a deterministic canonical name: explicit bus line, then explicit net
   or alias, then generated `net:<index>`. Preserve all source names as aliases.
8. Attach rails and external input/clock sources as drivers, pulls as weak
   defaults, chip output/bidirectional pins as drivers, and input/power pins as
   receivers. A bidirectional pin may be both.
9. Validate direction hazards but do not reject a legitimate shared bus merely
   because multiple output-capable pins are connected. Runtime enable state
   determines contention.

Power and `nc` pins remain visible in snapshots. Unless a chip model explicitly
declares sensitivity to them, they do not trigger functional evaluation. An
external stimulus drives a net through a named source; it must not mutate an
input pin privately, because every receiver on that net must observe the same
resolved value.

Normalized netlist v1 currently embeds output values from a materialized board.
Those values are observational export fields, not authoritative initial state.
Compilation derives initial drivers from rails, pulls, explicit sources,
inputs, clocks, and model reset/default state.

## Four-State Net Semantics

Every strong driver has one value in `{0, 1, Z, X}`. `Z` means no drive. Rails,
external sources, and enabled chip outputs are strong. Pulls apply only when no
strong driver contributes `0`, `1`, or `X`.

Strong-driver resolution:

| Active strong values | Net result | Diagnostic |
|---|---|---|
| none | pull result or `Z` | none |
| only `0` | `0` | none |
| only `1` | `1` | none |
| only `Z` | pull result or `Z` | none |
| any `X` | `X` | unknown driver provenance |
| both `0` and `1` | `X` | `simulation.bus_contention` |

Pull resolution when no strong driver exists:

- one or more agreeing pulls resolve to that value;
- opposing pulls resolve to `X` and emit `simulation.pull_conflict`;
- no pull resolves to `Z`.

Contention is state, not an exception that aborts resolution. The diagnostic
records net, time, delta, all active drivers, their values, and source endpoints.
It is emitted once per contiguous contention episode and closed when contention
ends. `contention=fail` makes the run result unsuccessful after the kernel has
recorded the stable `X` state; `diagnose` permits continued debugging.

Models must progressively become four-state aware. Until a model declares
native four-state support, `ModelAdapter` applies conservative coercion:

- `0` and `1` pass through;
- `Z` or `X` on a logic input is presented as unknown;
- if the legacy model cannot accept unknown, outputs dependent on that unknown
  become `X`, rather than coercing it silently to `0`;
- output values are normalized to `{0,1,Z,X}`.

This adapter must be tested per model family. It must not infer an output when
the dependency set is unknown.

## Event Queue And Determinism

The kernel uses a priority queue ordered by:

```text
(time_ns, delta, phase, stable_sequence)
```

`time_ns` is integer nanoseconds for current compatibility. `delta` orders
zero-time causality. `phase` enforces the processing phases below.
`stable_sequence` is a monotonic insertion sequence used only as a final tie
breaker; behavior must not depend on dictionary or chip insertion order.

Event kinds include:

- external/clock driver update;
- chip output-driver update;
- net resolve;
- model evaluate request;
- edge capture;
- sequential state commit;
- timing hold-check deadline;
- probe sample; and
- stop/checkpoint marker.

Events carry IDs and serializable payloads, not arbitrary callbacks. This makes
queue inspection, cancellation, diagnostics, replay, and snapshots deterministic.

### Same-Time Processing Phases

For each `(time_ns, delta)`, process atomically:

1. **Apply drivers:** apply all due external, clock, and chip-output changes.
2. **Resolve nets:** resolve every dirty net once from the complete driver set.
3. **Detect transitions:** compare old/new resolved values and record transition
   provenance. Only `0 -> 1` is rising and `1 -> 0` is falling. Transitions
   involving `X` or `Z` are unknown transitions, not clock edges.
4. **Check timing:** close pulse widths, check setup at recognized active edges,
   open hold windows, and process expired hold windows.
5. **Capture sequential intent:** all edge-triggered instances sample the same
   pre-commit resolved-net snapshot and produce proposed next state/output.
6. **Evaluate combinational/asynchronous behavior:** sensitive instances read
   the same resolved snapshot and propose driver changes.
7. **Commit model state:** commit all captured internal next states together.
   No sequential instance sees another instance's newly committed state at the
   same edge.
8. **Schedule outputs:** convert proposed driver changes into immediate next
   delta events in functional mode or future-time events in timed mode.
9. **Sample automatic probes:** record nets changed in this phase and any
   requested checkpoint sample.

If phase 8 schedules zero-delay changes, increment `delta` and repeat at the
same `time_ns`. Advance physical simulation time only when no same-time work
remains.

### Clock And Sequential Model Contract

Clock behavior is driven by resolved net transitions, never by a stimulus
helper directly calling whichever chips it knows about. Therefore an inverted,
gated, delayed, or shared clock is handled like any other net.

Each compiled model declares:

- clock pin(s) and accepted edge (`rising`, `falling`, or `both`);
- asynchronous controls and their priority;
- data/control pins sampled at an edge;
- state capture and commit operations; and
- outputs affected by state, asynchronous controls, or output enables.

The compatibility adapter may call existing `clock_edge_for_pin()` and
`clock_edge()` methods, but it must stage all affected instances against one
read snapshot and defer externally visible output application through the
kernel. Long term, chip models should expose explicit `evaluate(snapshot)`,
`capture(edge, snapshot)`, and `commit(token)` operations. The runner must not
call every chip's `clock_edge()` for an unrelated clock.

Asynchronous controls are evaluated after net resolution and before ordinary
edge capture according to model-declared priority. If an asynchronous control
asserts at the same timestamp as a clock edge, that priority decides the
captured state and is included in the trace.

## Functional Mode

Functional mode answers logical and sequencing questions without elapsed
propagation time:

- all output changes use zero delay and propagate through delta cycles;
- clocks still use their configured period/high/low simulation time;
- setup/hold and pulse-width checks are disabled by default because zero-delay
  combinational propagation is not a physical timing claim;
- contention, `X`, `Z`, edge polarity, sequential commit, convergence limits,
  probes, and diagnostics remain active; and
- `time_ns` advances for explicit `run`, pulse, and clock stimulus only.

This mode is the compatibility target for existing `Design.run()` behavior.
Existing tests expecting a package's generic delay in timestamps require a
temporary `legacy_delay` compatibility policy, not a second runner. New callers
must choose `functional` or `timed` explicitly once that option is exposed.

## Timed Mode

Timed mode uses the same logical evaluation, but each proposed driver transition
is associated with a timing cause:

```python
@dataclass(frozen=True)
class TransitionCause:
    changed_inputs: tuple[PinId, ...]
    output: PinId
    old: Logic4
    new: Logic4
    condition_tags: frozenset[str]
```

The model adapter must report the input/control changes that caused an output
proposal. Timing selection must not guess from all package paths.

### Timing Normalization

`TimingNormalizer` converts current package shapes into:

```python
@dataclass(frozen=True)
class TimingProfile:
    default_delay_ns: int | None
    paths: tuple[TimingArc, ...]
    constraints: tuple[TimingConstraint, ...]
    evidence: tuple[TimingEvidence, ...]

@dataclass(frozen=True)
class TimingArc:
    source_pins: frozenset[PinId | PinRole]
    destination_pins: frozenset[PinId | PinRole]
    transition: str       # rise, fall, enable, disable, any
    condition: str | None
    values_ns: Mapping[str, int | None]
    status: str           # exact, conservative, inferred, unavailable
    source_field: str
```

Normalization supports, without kernel special cases:

- `timing.simple.default_delay_ns` and `timing.timed.paths`;
- `timing.delay.default_ns` and datasheet typical values;
- normalized `timing.timing_parameters` (`tPLH`, `tPHL`, `tPZH`, `tPZL`,
  `tPHZ`, `tPLZ`, clock-to-Q, setup, hold, and minimum pulse width);
- memory `timing.paths` and `timing.write`; and
- selected variant and voltage condition keys.

Tests under `tests/timing.json` verify metadata but are not runtime timing input.
Runtime values come from the canonical package definition.

### Path Selection

For each proposed output change:

1. Filter arcs whose destination contains the output pin/role.
2. Filter by actual changed source pins and satisfied condition tags.
3. Match transition class:
   `0->1` uses rise, `1->0` uses fall, `Z->0/1` uses enable,
   `0/1->Z` uses disable, and an `X` transition uses the conservative maximum
   of matching arcs.
4. Select the requested variant, voltage, and corner. `typ`, `max_25c`,
   `max_sn74`, and other available keys remain explicit; no interpolation is
   performed.
5. If several independent changed inputs match, use the maximum matching delay
   unless the package declares a more specific conditional arc.
6. If no exact arc matches, apply `unknown_timing`: fail, warn and use the
   package default, or use zero. Every fallback records part, instance, output,
   requested condition, selected value, status, and source field.

Enable and disable arcs must remain distinct. For example, 74HC245 data
propagation, `/OE` to enabled output, and `/OE` to high-Z are different paths;
AT28C256 address/CE/OE data-valid paths and CE/OE-to-float are different paths.

The first implementation uses transport scheduling: every model-proposed
transition is delivered after its selected delay. A later additive arc option
may request inertial cancellation for gates, but timed mode must report the
policy. Silent cancellation of short pulses is forbidden.

### Setup, Hold, And Pulse Width

Constraints are checked only when a package maps metadata to concrete clock,
data/control, and asynchronous pins.

- **Setup:** at an active edge at `T`, find the last resolved transition of each
  constrained input. Violation when `T - last_change < setup_ns`.
- **Hold:** at an active edge, open a window through `T + hold_ns`. Any resolved
  constrained-input transition inside `(T, T + hold_ns)` is a violation. A
  transition exactly at the end satisfies the requirement.
- **Pulse width:** on each recognized `0<->1` transition of a constrained clock
  or asynchronous control, measure time since the opposite edge. Violation when
  width is less than the selected minimum.
- **Unknown edge:** `X/Z` transitions do not satisfy a clock edge or close a
  valid pulse. Emit an unknown-clock diagnostic when the net is clock-sensitive.

Each violation records constraint type, instance, pins, edge time, observed
margin/width, required value, selected condition/corner, evidence source, and
the affected state/output set.

Default `violation_effect=diagnose` preserves deterministic logical execution
and marks the run unsuccessful only if the caller's policy says violations are
errors. Optional `drive_x` sets only affected captured state/output to `X` after
the edge. It does not simulate metastability duration or analog recovery.

## Convergence, Oscillation, And Resource Limits

The runner must distinguish three failures:

- `simulation.no_convergence`: same-time delta cycles exceed
  `max_delta_cycles`;
- `simulation.oscillation`: a repeated same-time state signature is detected;
- `simulation.resource_limit`: event, same-time event, time, or history limits
  are exceeded.

After every delta, hash the dirty-net values plus affected model state and
pending same-time event kinds. A repeated signature before quiescence proves a
digital zero-delay cycle. The diagnostic includes cycle length, involved nets,
instances, and recent transitions. Functional combinational loops commonly hit
this rule. In timed mode, a real delayed oscillator may continue across time;
it is bounded by requested run time and `max_events`, not called a convergence
failure merely because it oscillates.

On a limit, stop at a coherent phase boundary, retain the last state, pending
event count, and diagnostic trace, and return `ok: false`. Never hang or discard
all debugging state.

## Probes, Histories, And Snapshots

Probes observe resolved nets, not private input-pin copies. A pin probe reports
the net value when connected and the pin's own driver value separately when the
pin can drive. Bus probes are ordered collections of line-net probes.

Three sampling forms are supported:

- automatic transition history for subscribed probe nets;
- explicit `probe`/checkpoint samples, including unchanged values; and
- a current snapshot at any coherent phase boundary.

Each transition sample contains:

```json
{
  "time_ns": 25,
  "delta": 2,
  "value": "X",
  "previous": 1,
  "edge": "unknown",
  "cause": "driver_change",
  "drivers": ["U7:18=1", "ROM1:11=0"]
}
```

Snapshots are additive to the current shape and should include:

- `mode`, `time_ns`, `delta`, `quiescent`, and selected timing policy;
- instances and model-visible state where safely serializable;
- pins with sampled value, driver value, direction, and canonical net;
- nets with resolved value, pulls, and all drivers including `Z`;
- buses, rails, sources, clocks, pending-event summary, probes, and displays;
- active and historical contention episodes;
- timing selections/fallbacks and timing violations; and
- structured diagnostics with stable codes and source locations.

History limits use deterministic oldest-first truncation and report truncation.
Probe reads must not advance time or trigger evaluation.

## API And CLI Boundary

`SimulationService` remains the stable owner. CLI, HTTP, UI, and a future MCP
adapter are thin request/response adapters and must not call kernel internals or
reimplement parsing, timing, or resolution.

Additive service options under `components.service.v1`:

```json
{
  "options": {
    "mode": "functional",
    "timing": {
      "corner": "typ",
      "vcc": "vcc_4_5_v",
      "device_variant": null,
      "unknown_timing": "warn_default"
    },
    "limits": {
      "max_delta_cycles": 1000,
      "max_events": 100000,
      "max_time_ns": null
    },
    "policies": {
      "contention": "diagnose",
      "violation_effect": "diagnose"
    }
  }
}
```

`validate`, `snapshot`, `run`, `probe`, and `frontend-snapshot` keep their
existing top-level response shapes. Add `metadata.engine = "python-net"`,
`metadata.mode`, timing selection, event counts, and diagnostics additively.
Existing clients still gate on `ok` and ignore unknown fields.

CLI direction:

```sh
python3 -m chiplib.cli run design.json --mode functional
python3 -m chiplib.cli run design.json --mode timed --vcc vcc_4_5_v --corner typ
python3 -m chiplib.cli probe design.json --mode timed --set logic
python3 -m chiplib.cli snapshot design.json --mode functional
```

The CLI parses arguments and files, constructs the shared service request, and
prints the service response. File path resolution remains in the Design/service
adapter. The kernel accepts already loaded/validated data and performs no file
I/O.

Stable diagnostic codes should include:

- `compile.invalid_endpoint`, `compile.ambiguous_pin`,
  `compile.unsupported_circuit_reference`, `compile.missing_part`;
- `simulation.bus_contention`, `simulation.pull_conflict`,
  `simulation.unknown_clock`, `simulation.oscillation`,
  `simulation.no_convergence`, `simulation.resource_limit`;
- `timing.path_missing`, `timing.condition_missing`,
  `timing.setup_violation`, `timing.hold_violation`, and
  `timing.pulse_width_violation`.

## Data Flow

One run follows this sequence:

1. Service loads schematic/design/netlist according to existing input
   precedence and calls `Design` normalization where required.
2. Compiler resolves concrete endpoints and electrical nets, validates package
   references, creates model descriptors, and normalizes timing metadata.
3. Runner creates an isolated session, model instances, driver table, net table,
   probe subscriptions, and empty event queue.
4. Initialization schedules rails, sources, initial clocks/inputs, model
   defaults, and asynchronous controls at `(0,0)`; the kernel settles.
5. Step executor translates existing `apply`, `settle`, `run`, `clock`, `probe`,
   and `expect` commands into session operations.
6. Kernel runs through deterministic phases until the requested stop condition,
   quiescence, or a resource/error policy stops it.
7. Probe and expectation layers read coherent resolved state.
8. Service maps session results into the existing response contract and exposes
   diagnostics without losing the final snapshot.

## Staged Implementation

### Stage 1: Compile And Functional Kernel

- Add immutable compiled IDs/graph and strict endpoint/net resolution.
- Adapt existing `Design` and `chiplib.netlist` v1 inputs.
- Implement four-state drivers, pulls, contention episodes, dirty-net
  propagation, delta cycles, deterministic ordering, and resource limits.
- Adapt current `Chip.update()` models and preserve current Design step syntax.
- Route probes and snapshots through resolved nets.
- Add focused tests for alias/net union, buses, rails, pulls, `Z`, `X`,
  contention, convergence, and deterministic ordering.

Acceptance: current functional Design/service/netlist tests remain green except
for intentionally versioned assertion updates to contention and timestamps;
new tests prove identical results across shuffled instance/connection order.

### Stage 2: Sequential Phases And Clock Nets

- Replace direct stimulus-to-chip edge calls with transition-derived edge
  subscriptions.
- Add capture/commit staging and asynchronous-control priority.
- Adapt representative 74HC161/164/574/595 and memory write models.
- Add simultaneous-register, gated/inverted-clock, clear-vs-clock, unknown-clock,
  and opposite-edge-hold tests.

Acceptance: sequential results are independent of instance order and all
clocked models declare their edge and sampled pins or are reported unsupported.

### Stage 3: Timing Normalization And Timed Mode

- Normalize all current timing shapes into `TimingProfile`.
- Implement path/corner/voltage/variant selection and visible fallback policy.
- Schedule rise, fall, enable, disable, memory access, and clock-to-Q arcs.
- Add timing provenance to snapshots and service metadata.
- Use 74HC245, 74HC574, 74HC161, and AT28C256 as acceptance fixtures because
  together they cover bidirectional tri-state, sequential output enable,
  clock-to-Q/setup/hold/pulse width, and asynchronous memory paths.

Acceptance: each fixture selects the expected path at `vcc_4_5_v`, distinguishes
enable from disable, and reports every fallback.

### Stage 4: Timing Constraints And Diagnostics

- Implement setup, hold, pulse-width, and unknown-edge checks.
- Add `diagnose` and `drive_x` violation policies.
- Add contention/timing episode reporting, trace windows, and history limits.
- Expand service/CLI tests for structured codes and coherent failure snapshots.

Acceptance: boundary tests cover just-before, exactly-at, and just-after each
constraint; no violation claims analog metastability or physical signoff.

### Stage 5: Circuit Library Adapter

- Define an explicit adapter for executable `components.lib.circuit` packages.
- Require concrete pin maps for symbolic/ranged ports and nested circuit parts.
- Compile only packages whose dependencies recursively provide executable
  manifests; retain descriptive proof-only packages as non-executable.
- Cross-check adapted circuits against existing package proof vectors.

Acceptance: no dot/range endpoint is guessed, and a rejected package identifies
the exact unresolved reference and required mapping.

## Compatibility Constraints

1. `Design.to_dict()` and block-UI round trips must retain all current fields and
   unknown additive metadata.
2. `chiplib.netlist` version 1 remains accepted. Additive runner metadata is
   allowed; changing meanings of required fields requires netlist version 2.
3. `components.service.v1` top-level response fields and commands remain stable.
   New mode/options/result fields are additive.
4. Existing CLI commands continue to work without requiring an HTTP server or a
   second database.
5. Chip package behavior remains loaded through the existing chip factory and
   canonical package definition. No timing values are copied into runner code.
6. Active-low labels, physical pin numbers, tri-state behavior, edge polarity,
   and timing evidence remain visible in diagnostics and snapshots.
7. A model that lacks four-state, sequential, or timed capabilities is marked
   with a structured capability/fallback diagnostic; the runner must not claim
   unsupported accuracy.
8. Functional and timed modes may differ only in propagation time and enabled
   timing checks, not in net topology, logical truth, edge polarity, sequential
   phase ordering, or contention resolution.
9. Exported Verilog remains a separate engine/verification path. Matching the
   Python runner does not replace Python-vs-Verilog equivalence tests.
10. Descriptive circuit-library metadata and physical evidence records remain
    intact. Successful digital execution must not rewrite their completion or
    hardware-readiness status.

## Required Test Matrix

The implementation should add tests at four boundaries:

| Boundary | Required coverage |
|---|---|
| Compiler | aliases, cycles, symbolic/physical pins, bus bounds, net union, rails, pulls, invalid/ranged library endpoints |
| Kernel | truth tables, `Z`, `X`, contention episodes, same-time ordering, delta convergence, oscillation, limits |
| Sequential | rising/falling edges, simultaneous capture/commit, async priority, gated clock, unknown edge, state hold |
| Timed | rise/fall, enable/disable, clock-to-Q, memory paths, corner selection, fallback, setup/hold/pulse boundaries |
| Observability | transition and explicit samples, bus order, coherent snapshots, pending events, diagnostics, truncation |
| Service/CLI | default compatibility, explicit modes, options, structured failures, final snapshot on failure |

Every kernel test that uses multiple instances should be rerun with shuffled
instance and connection order. Timed tests must assert selected timing source
and condition, not only the final timestamp.

## Architectural Decisions

- One runner and one compiled graph serve both modes.
- Nets resolve four-state values; contention resolves to `X` and is diagnosed.
- Clocks are ordinary resolved nets with edge subscriptions.
- Sequential capture and commit are globally phased at each edge time.
- Timed paths are selected from normalized canonical definition metadata with
  explicit conditions and fallbacks.
- Timing violations are digital diagnostics, not analog simulation.
- The service is the public boundary; the kernel is file-I/O-free and private.
- Physical readiness remains outside this runner.
