# Circuit Runner Student Contract

This document defines how a circuit runner must speak to students. The public
functional commands are `circuit-validate`, `circuit-run`, `circuit-step`, and
`circuit-probe`; the local JSON API also exposes `circuit-load`. It also records
the staged contracts for `timed-run`, `explain-violations`, and
`export-evidence` without claiming that those commands are implemented.

The runner is a simulator. Its results describe the loaded circuit model and
the events the runner actually checked. A passing result is not proof that a
physical circuit is correctly wired, electrically safe, fast enough, or ready
to power.

## Status And Scope

This is a required student-facing contract. The implemented functional subset
is public, but it does not support every circuit package.

- The CLI implements `circuit-validate`, `circuit-run`, `circuit-step`, and
  `circuit-probe`.
- The local JSON API implements `circuit-load` and the same four functional
  commands. `circuit-load` supports API workflows that retain a loaded runner;
  each functional command may also receive a package path.
- A command can return `blocked` when its package uses runtime features that
  are not executable yet. Loadability alone is not verification or promotion.
- `explain-violations` is the violation-focused student view of existing
  structured results. Current tools may use `explain-result` until this command
  is implemented.
- `timed-run` and `export-evidence` are required interfaces for future runner
  work. A runner must return `runner.command_not_implemented` instead of
  silently treating either command as `run` or a general file export.

This document does not change chip behavior, timing values, schematic JSON, or
the service contract. When they disagree, chip definitions and the normalized
design remain the source of chip, pin, net, edge, and timing facts.

## Student Command Pattern

Current CLI commands use this form:

```sh
python3 -m chiplib.cli circuit-COMMAND CIRCUIT.json [OPTIONS]
```

Here, `COMMAND` is `validate`, `run`, `step`, or `probe`. API adapters use the
matching `circuit-*` command names; the API alone also exposes `circuit-load`.
The result meaning and evidence boundary must stay the same in later graphical
or AI-facing adapters.

The current functional CLI emits the machine-readable JSON result. A future
interactive adapter may show a short summary such as:

```text
PASS validate: 3 chips, 14 nets, 0 errors, 1 warning.
```

or:

```text
STOP timed-run: 2 timing violations. No physical timing claim was made.
```

Any human-readable view must carry the same meaning as the JSON. A tool must
never show `PASS` when `ok` is false or when a requested check was unsupported.

## Shared Result Rules

Every result must contain:

```json
{
  "contract": "components.circuit_runner.student.v1",
  "command": "validate",
  "ok": true,
  "status": "pass",
  "design": {"id": "student-counter", "source": "counter.json"},
  "summary": "3 chips, 14 nets, 0 errors, 1 warning.",
  "violations": [],
  "warnings": [],
  "evidence_boundary": {
    "proves": ["the listed checks passed in the named simulator"],
    "does_not_prove": ["physical wiring", "electrical safety", "physical timing"]
  },
  "metadata": {
    "engine": "python",
    "engine_version": null,
    "components_version": null,
    "started_at": null,
    "elapsed_ms": 0
  }
}
```

`status` is one of:

| Status | Student meaning |
|---|---|
| `pass` | Every requested and supported check passed. |
| `needs_attention` | The runner found a problem that the student can inspect. |
| `blocked` | The requested check cannot be completed with the available model or evidence. |
| `error` | The request or design could not be read. |

Rules:

- `ok` is true only for `status: pass`.
- Warnings stay visible and never disappear from exported evidence.
- Values use `0`, `1`, `Z`, or `X`. `Z` means no simulated driver. `X` means
  the runner cannot determine one valid logic value.
- Time values include units in text and use integer `*_ns` fields in JSON.
- Active-low names retain `/`, for example `/OE` and `/RST`.
- A reference must never be shortened when that would hide which chip, pin,
  bus line, or net caused the result.

## Exact Location Rules

Every pin-related violation must include all facts known to the runner:

```json
{
  "location": {
    "source_path": "$.connect[4]",
    "chip_ref": "U7",
    "part": "74HC574",
    "pin_number": "11",
    "pin_name": "CP",
    "net": "CPU_CLK"
  }
}
```

For a bus, include `bus`, `bit`, and the resolved `net`. For several drivers,
include every driver in `details.drivers`, each with chip reference, part, pin
number, pin name, driven value, and enable/control state when known. Do not
replace details with messages such as "check your clock chip" or "bus error."

If a fact is unavailable, use `null` and say which source did not provide it.
Never guess a pin name, edge, timing limit, voltage, current, or physical cause.

## Commands

### `validate`

Use before simulation. It reads and normalizes the design, resolves chip and
pin references, checks connection shape, and reports static circuit problems.

```sh
python3 -m chiplib.cli circuit-validate counter.json
```

The result includes chip, bus, net, probe, error, and warning counts. It must
identify floating inputs and output conflicts when those checks are enabled by
the design. It does not advance simulation time or claim that logic behavior
or timing passed.

### `run`

Use for functional simulation. It executes the design's default steps or the
steps supplied by the student, settles supported models, checks expectations,
and returns the final snapshot.

```sh
python3 -m chiplib.cli circuit-run counter.json
python3 -m chiplib.cli circuit-run counter.json --op "reset" --op "clock CLK"
```

The result includes executed steps, final `time_ns`, probes, failed
expectations, and model warnings. `run` may use modeled delays, but it must not
describe itself as a complete setup/hold or pulse-width check. Use `timed-run`
for requested timing checks.

### `step`

Use to perform exactly one named operation. The CLI loads the package path for
that invocation. The local API can operate on its currently loaded runner or
accept a package path with the request.

```sh
python3 -m chiplib.cli circuit-step counter.json --op "set D 1"
python3 -m chiplib.cli circuit-step counter.json --op "clock CLK"
python3 -m chiplib.cli circuit-step counter.json --op "settle"
```

The result includes the operation text, action, time before and after, changed
nets, changed chip outputs, and violations produced by that operation. An
unknown operation returns `runner.unsupported_step`; it must not be reported as
a successful no-op. A stateless adapter must say that it reloads the design or
return `runner.stateful_session_required`.

### `probe`

Use to read one named output or all available outputs. Stateful API callers can
probe the currently loaded runner; a CLI invocation loads the supplied package
before reading it.

```sh
python3 -m chiplib.cli circuit-probe counter.json
python3 -m chiplib.cli circuit-probe counter.json --name Q
```

Each sample includes probe name, exact target, value, sample time, and history
when requested. A bus sample preserves bit order and individual unknown or
high-impedance bits. Probing observes the simulation; it does not alter a net
or create physical oscilloscope evidence.

### `timed-run`

Staged and currently unavailable as a public CLI/API command. The examples
below define the intended interface; they are not commands that can be run in
the current release.

Use when the student requests propagation, active-edge, setup, hold, pulse
width, or bus-turnaround checks.

```sh
components-runner timed-run latch.json --scenario capture --until 500ns
components-runner timed-run bus.json --scenario turnaround --trace DBUS
```

The result includes the timing source for every checked limit, observed model
times, required limits, margins, event order, and traces used for the decision.
A limit is checked only when the active part definition and engine implement
that exact timing rule. Timing metadata by itself is not proof that the engine
enforces the parameter.

If any requested rule is not implemented, the command is `blocked`, not
`pass`, and reports `timing.unsupported`. Current chip-level or generic delay
hooks must not be relabeled as complete per-parameter setup, hold, pulse-width,
or enable-to-high-Z verification.

### `explain-violations`

Use to translate an existing runner result into beginner-readable actions. It
does not rerun the circuit or add electronics facts.

```sh
components-runner explain-violations run-result.json
```

For each violation, show in this order:

1. What happened.
2. Exactly where it happened.
3. What the runner expected and observed.
4. A source-backed fix when one exists.
5. What to run again.
6. What remains unproved about physical hardware.

The explanation must retain the original violation code and exact structured
details. It may simplify wording, but it must not simplify away references,
pins, nets, edge names, times, limits, or drivers.

### `export-evidence`

Use to save a reviewable record of one or more completed runner results.

```sh
components-runner export-evidence run-result.json --output evidence.json
components-runner export-evidence timed-result.json --output evidence.json --include-traces
```

The evidence file contains:

- contract and schema versions;
- source design path and a content digest;
- command, options, engine, and Components version;
- full violations and warnings without redaction;
- executed steps and expectation results;
- probe samples and requested traces;
- timing parameter source paths and checked/unsupported status;
- evidence boundary and physical-measurement requirements;
- creation time, while preserving the original run time separately.

Exporting does not upgrade evidence. A functional result remains functional, a
model timing result remains model timing, and planned physical evidence remains
unmeasured. The exporter must not add `hardware_verified`, `safe_to_power`, or
equivalent claims.

## Violation Messages

The first sentence is written for a beginner. Structured details carry the
exact evidence. Text in angle brackets is replaced from the result, never
guessed.

### Bad Pin

Code: `connection.bad_pin`

```text
Pin <pin-number> is not a valid pin for <chip-ref> (<part>).
The connection at <source-path> names <original-endpoint> on net <net>.
Use a pin number and name from the loaded <part> definition.
```

Include `original_endpoint`, valid pin identifiers when available, chip
definition path, and whether the number exists under a different pin name.

### Floating Input

Code: `connection.floating_input`

```text
Input <chip-ref>:<pin-number> <pin-name> on net <net> has no known driver.
The simulated value is <value> at <time-ns> ns.
Connect the intended source or an appropriate defined pull source, then validate again.
```

Include all connected endpoints and pulls. Do not say that a physical input is
HIGH, LOW, safe, damaged, or electrically floating unless physical measurement
evidence says so.

### Bus Fight

Code: `simulation.bus_fight`

```text
Net <net> has drivers trying to produce different values at <time-ns> ns.
<driver-list-with-exact-chip-and-pin-details>
Fix the enable or direction rules so only the intended driver owns the net.
```

Include every driver and its value, output-enable pin/state, direction
pin/state, and event that enabled it when known. Use `unknown` for unavailable
control state. Do not estimate physical current or damage.

### Wrong Edge

Code: `timing.wrong_edge`

```text
<chip-ref>:<pin-number> <pin-name> changed on the <observed-edge> edge of net <net>, but the loaded <part> rule requires the <required-edge> edge.
The event occurred at <time-ns> ns and affected <affected-output-list>.
Use the required edge and check that the opposite edge holds state.
```

Include the edge-rule source path, state before/after, and exact affected output
pins and nets.

### Setup Time

Code: `timing.setup_violation`

```text
<data-chip-pin> changed <observed-ns> ns before the active <clock-chip-pin> edge on net <clock-net>.
The loaded <part> model requires at least <required-ns> ns of setup time, so the margin is <margin-ns> ns.
```

Include data event time, clock event time, required limit, comparison condition,
timing source path, operating-condition fields present in that source, and
affected outputs. Do not choose a datasheet min/typ/max value on the student's
behalf.

### Hold Time

Code: `timing.hold_violation`

```text
<data-chip-pin> changed <observed-ns> ns after the active <clock-chip-pin> edge on net <clock-net>.
The loaded <part> model requires at least <required-ns> ns of hold time, so the margin is <margin-ns> ns.
```

Include the same source and event details required for setup time.

### Pulse Width

Code: `timing.pulse_width_violation`

```text
The <level> pulse on net <net> at <chip-ref>:<pin-number> <pin-name> lasted <observed-ns> ns.
The loaded <part> model requires at least <required-ns> ns, so the pulse is <shortfall-ns> ns too short.
```

Include pulse start/end events, whether HIGH or LOW width was checked, timing
source path, and affected state/output pins.

### Non-Convergence

Code: `simulation.non_convergence`

```text
The simulator could not find a stable value after <event-count> events by <time-ns> ns.
The changing loop includes <exact-net-list> and <exact-chip-pin-list>.
Check unintended feedback, missing delay, unknown inputs, and conflicting drivers.
```

Include the configured event/time limit, last values, repeating states when
detected, and the exact dependency loop known to the engine. Do not claim a
physical circuit will oscillate.

### Unsupported Timing

Code: `timing.unsupported`

```text
The runner cannot check <timing-rule> for <chip-ref> (<part>) pin <pin-number> <pin-name> on net <net>.
The loaded definition has <metadata-status>, and the selected engine has <implementation-status>.
This timing check is blocked; it did not pass or fail.
```

Include the requested rule, metadata source path or `null`, engine capability,
and nearest supported check without presenting it as equivalent.

### Physical Measurement Required

Code: `evidence.physical_measurement_required`

```text
Simulation cannot prove <requested-physical-claim> for <exact-chip-pin-net-scope>.
No matching physical measurement record was supplied.
Record the required measurement with the named equipment and conditions before making this hardware claim.
```

Include the requested claim, exact chips/pins/nets, required measurement type,
conditions already specified by the evidence plan, and matching record status.
Do not invent equipment settings or acceptance limits. This violation is
`blocked`, not a simulation failure.

## Multiple Violations

Show all violations. Order them by the earliest useful fix:

1. Parse and bad-reference errors.
2. Bad pins and invalid connections.
3. Floating inputs and bus fights.
4. Non-convergence.
5. Wrong edge and functional expectations.
6. Setup, hold, pulse width, and other timing checks.
7. Unsupported timing and required physical measurements.

Do not hide later violations merely because an earlier one exists. Mark a
later result `not_checked` when the earlier problem prevented that check.

## Evidence Language

Allowed statements are narrow and reproducible:

- "The Python model produced `Q=1` at 120 ns."
- "The requested setup check passed against the loaded 20 ns model limit."
- "No simulated bus fight was detected during the listed steps."

Disallowed statements without matching physical evidence include:

- "The breadboard works."
- "This circuit is safe to power."
- "The chip meets its datasheet timing in hardware."
- "There is no bus fight on the real bus."
- "The clock is clean."

A result may point to a physical capture plan. A plan is not a measurement,
and a file path is not evidence that the measurement was completed.

## Minimum Acceptance Checks

A runner conforms to this contract only when tests prove that it:

- preserves exact chip reference, part, pin number, pin name, bus bit, and net;
- never turns `X`, `Z`, unsupported, blocked, or not-checked into `PASS`;
- lists all bus drivers and timing event times used in a decision;
- distinguishes functional simulation, modeled timing, and physical evidence;
- exports the original violations and evidence boundary unchanged;
- uses the specified codes and beginner messages for every violation class in
  this document;
- refuses hardware claims when matching physical measurements are absent.
