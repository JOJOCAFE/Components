# 24 — Stimulus Model

Status: proposal.  Additive v1.1 profile extension for `component:component`.
Does not modify frozen v1.0 documents `00`–`15`, the Component Language Model
v1.1 core (`17`), Runtime Model (`18`), or Operation Protocol (`16`).

## Purpose

The Component Language Model v1.1 defines topology (`device`, `net`, `connect`)
and observation (`probe`, `display`, `test`).  What it lacks is a way to
declare **how the circuit receives its input signals** — the stimulus that
drives it during simulation, interactive exploration, and acceptance testing.

Without stimulus declarations, a Component is a wired-but-inert graph.
Stimulus turns it into a runnable machine.

```text
component:component source
  ├── Topology:  device, net, bus, connect
  ├── Observation: probe, display
  ├── Stimulus:  input, clock, channel, step   ← THIS DOCUMENT
  └── Test:      test { arrange/settle/assert }
```

Stimulus is **not** arbitrary imperative scripting.  It is a bounded,
declarative description of signal sources.  A runtime session uses the
stimulus declarations to construct initial drivers, periodic generators, and
interactive injection points.  A test block may reference named stimuli.

## Stimulus declarations

### Input presets

```component
input <preset-id> {
  set <endpoint> = <value>;
  ...
}
```

A named input preset declares a fixed configuration of signal values to be
applied simultaneously.  It does not describe time or sequence — only which
endpoints are driven to which values at the moment the preset is applied.

Values are signal-domain literals: `0`, `1`, `Z` (high-impedance), or integer
literals for buses (decimal, `0b` binary, `0x` hex).

```component
input power_on {
  set a = 1;
  set b = 1;
}

input count_mode {
  set clear_n = 1;
  set load_n = 1;
  set enp = 1;
  set ent = 1;
  set d = 0;
}
```

### Clock generators

```component
clock <clock-id>, <endpoint>, { <parameters> };
```

A clock declaration names a periodic signal source bound to a specific
endpoint.  Parameters:

| Parameter | Required | Description |
|-----------|----------|-------------|
| `period_ns` | yes | Period in nanoseconds |
| `initial` | no | Starting level (default `0`) |
| `duty` | no | Duty cycle 0.0–1.0 (default `0.5`) |
| `phase_ns` | no | Phase offset from time zero (default `0`) |

```component
clock main, clk, { "period_ns": 100 };
clock fast, clk, { "period_ns": 20, "initial": 0, "duty": 0.5 };
```

A clock generator does not override topology connections.  It drives the named
endpoint as a source.  If a clock is bound to an endpoint that already has a
device output driving it, that is a contention error (caught by the resolver).

### Interactive channels

```component
channel <channel-id>, <endpoint>, { <parameters> };
```

A channel is an interactive injection point — the equivalent of a front-panel
switch, button, or potentiometer.  A channel differs from an `input` preset:
it persists across time and can be toggled during an interactive session.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `kind` | no | `switch` (default), `button`, `slider` |
| `initial` | no | Initial value (default `0`) |
| `label` | no | Human-readable label for UI |

```component
channel sw_a, a, { "kind": "switch", "initial": 1, "label": "Switch A" };
channel sw_b, b, { "kind": "switch", "initial": 1, "label": "Switch B" };
```

Channels are declared stimulus sources.  They provide a stable identity for
Board/UI bindings, CLI injection, and test scripts without granting a UI
direct access to topology internals.

### Step sequences

```component
step <step-id> {
  <action>;
  ...
}
```

A step sequence declares a bounded, repeatable runtime procedure.  Actions:

| Action | Meaning |
|--------|---------|
| `apply <preset-id>;` | Drive all values from a named input preset |
| `settle;` | Wait for combinational propagation to quiescence |
| `pulse <endpoint>;` | Drive `0→1→0` (or `1→0→1` if initial=1) one cycle |
| `clock <clock-id> <count>;` | Run the named clock for N complete cycles |
| `wait <time>;` | Advance simulation time (e.g., `wait 50ns;`) |
| `set <endpoint> = <value>;` | Drive a single signal |
| `probe;` | Sample all declared probes at current time |
| `assert <observation> == <expected>;` | Check one observation value |

```component
step run_and_probe {
  apply count_mode;
  settle;
  clock main 4;
  probe;
}
```

Step sequences are deterministic and bounded.  A runtime session refuses to
execute an unbounded step.  Steps may be referenced from `test` blocks:

```component
test counter_reaches_four {
  run run_and_probe;
  assert count == 4;
}
```

## Clock profiles (optional, for timing sweep)

```component
clock_profile <profile-id> {
  clock <clock-id>, { <parameters> };
  ...
}
```

A clock profile groups alternative clock configurations for frequency sweep or
timing margin testing.  Only one profile is active during a session.

```component
clock_profile slow {
  clock main, clk, { "period_ns": 20000 };
}

clock_profile target_5mhz {
  clock main, clk, { "period_ns": 200 };
}
```

Profiles do not change topology or stimulus structure — only clock timing
parameters.  A test or step may specify which profile to use:

```component
test works_at_5mhz {
  use clock_profile target_5mhz;
  run run_and_probe;
  assert count == 4;
}
```

## Relationship to existing declarations

| Existing | Stimulus equivalent |
|----------|---------------------|
| `test { arrange { set ... } }` | Inline stimulus within test — still valid, unchanged |
| `device Clock, virtual.ClockSource` | Becomes optional; `clock` declaration is preferred for explicit period |
| `device SW, virtual.Switch` | Becomes optional; `channel` declaration is preferred for explicit kind/initial |

Virtual devices (`virtual.ClockSource`, `virtual.Switch`, `virtual.Probe`)
remain valid as explicit device instances.  The stimulus declarations are a
shorthand that avoids requiring topology wiring for test infrastructure.
When both exist, the explicit device takes precedence and the stimulus
declaration acts as its configuration.

## Resolver contract

After topology resolution succeeds:

1. Validate that every stimulus endpoint (`input`, `clock`, `channel`, `step`)
   resolves to a declared net, bus member, or device port.
2. Check direction: stimulus endpoints must be valid driver targets (inputs to
   the circuit or undriven nets).  Driving an active device output is an error.
3. Check for contention between stimuli: two clocks on the same endpoint is an
   error; a clock and a channel on the same endpoint is an error.
4. Validate step sequences: all referenced presets, clocks, and probes exist.
5. Bind clock generators, channel drivers, and presets into the resolved
   topology as explicit source records with provenance.

## AST extensions

```text
InputPresetNode      { name, assignments: [{endpoint, value}] }
ClockDeclNode        { name, endpoint, parameters }
ChannelDeclNode      { name, endpoint, parameters }
StepSequenceNode     { name, actions: StepActionNode[] }
ClockProfileNode     { name, overrides: ClockDeclNode[] }
StepActionNode       { kind: apply|settle|pulse|clock|wait|set|probe|assert, ... }
```

## Examples mapping

The existing JSON circuit features map cleanly:

| JSON feature | component:component |
|---|---|
| `"inputs": { "power_on": [...] }` | `input power_on { ... }` |
| `"clocks": { "main": {...} }` | `clock main, clk, { ... };` |
| `"input_sets": { "front_panel": { "channels": [...] } }` | `channel sw_a, a, { ... };` |
| `"steps": ["apply ...", "settle", ...]` | `step run { apply ...; settle; ... }` |
| `"clock_profiles": [...]` | `clock_profile slow { ... }` |

## Memory image loading

```component
memory <instance-id> {
  load <path>;
}
```

A memory declaration binds content to an SRAM or ROM device instance.  The
path is relative to the Component source file.  Multiple address ranges may
also be declared inline:

```component
memory U_ROM {
  load "programs/boot.bin";
}

memory U_RAM {
  0x0000 = [0x00, 0x00, 0x00, 0x00];
  0x0010 = [0xFF, 0x42];
}
```

Memory content is immutable stimulus.  It represents the initial state visible
to the circuit when the session starts.  A runtime session may not alter
ROM content; RAM content may change as the circuit writes it.

## Reset declarations

```component
reset <reset-id> {
  <action>*
  expect <observation> == <expected>;
}
```

A reset declaration describes a bounded initialization sequence and its
expected outcome.  It is the defined "known-good starting point" for all
subsequent tests and steps.

```component
reset power_on {
  set clear_n = 0;
  settle;
  set clear_n = 1;
  settle;
  expect phase_t0 == 0;
  expect phase_t1 == 0;
  expect phase_t2 == 0;
}
```

A test or step may reference a reset:

```component
test sequence_after_reset {
  reset power_on;
  pulse clk; settle;
  assert phase_t0 == 1;
}
```

## Derived signals (control equations)

```component
derive <signal-id> = <expression>;
```

A derived signal is a named combinational function of existing nets.  It does
not create a physical connection or device.  It is a read-only observation
that computes its value from the topology at every simulation coordinate.

```component
derive wr_dir = t2 & opcode[1];
derive buf_oe_safe = buf_oe | str;
derive serial_in = ~t0 & ~t1;
```

Supported operators: `&` (AND), `|` (OR), `^` (XOR), `~` (NOT), parentheses
for grouping.  Bus member selection uses `name[index]`.

Derived signals may be used as probe targets, in assert comparisons, and in
display bindings.  They are not valid connection endpoints — they observe, they
do not drive.

## Release action (tri-state stimulus)

```component
release <endpoint>;
```

A release action removes the stimulus driver from an endpoint, allowing it to
float to high-impedance (Z) or be driven by the circuit's own devices.  This
is essential for testing bidirectional buses and tri-state outputs.

```component
step test_bus_direction {
  set data = 0xFF;
  settle;
  release data;
  settle;
  assert data_out == Z;
}
```

## Bounded repeat

```component
repeat <count> { <action>* }
```

A bounded repeat executes its body a fixed number of times.  The count must
be a compile-time integer literal.  There is no dynamic loop, no break, no
early exit.

```component
step count_to_fifteen {
  apply count_mode;
  settle;
  set clear_n = 0;
  settle;
  set clear_n = 1;
  repeat 15 {
    pulse clk;
    settle;
  }
  probe;
}
```

Inside a repeat, the iterator `$i` is available (0-indexed) for indexed
stimulus:

```component
step opcode_sweep {
  repeat 256 {
    set opcode = $i;
    clock main 3;
    probe;
  }
}
```

The maximum permitted repeat count is 65536.  A resolver rejects unbounded
or non-literal repeat counts.

## Sequence declarations

```component
sequence <sequence-id> after <reset-id> {
  clock <clock-id>; expect <observations>;
  clock <clock-id>; expect <observations>;
  ...
}
```

A sequence is a compact table of expected states after each clock edge,
starting from a named reset.  This is the natural representation for ring
counters, state machines, and instruction traces.

```component
sequence ring_phases after power_on {
  clock sys_clk; expect phase_t0 == 1, phase_t1 == 0, phase_t2 == 0;
  clock sys_clk; expect phase_t0 == 0, phase_t1 == 1, phase_t2 == 0;
  clock sys_clk; expect phase_t0 == 0, phase_t1 == 0, phase_t2 == 1;
  clock sys_clk; expect phase_t0 == 1, phase_t1 == 0, phase_t2 == 0;
}
```

A sequence is both documentation and an executable test.  If the circuit
does not produce the expected values at each step, the sequence fails with a
diagnostic identifying the first divergence.

## Explicit non-goals

- Arbitrary looping, branching, or conditional scripting within steps.
- Analog signal generation (voltage ramps, current sources).
- Board-specific interaction commands (those belong to `component:operation`).
- Replacing the `test {}` block — tests may use stimuli but stimulus is not a test.
- Physical hardware IO (GPIO toggling, serial protocols).
- Dynamic memory allocation or unbounded data structures.

## Required conformance cases

1. A Component with a named `input` preset can apply it and observe results.
2. A `clock` drives periodic edges at the declared frequency.
3. A `channel` can be injected interactively without re-resolving topology.
4. A `step` sequence executes in declared order and halts.
5. A `clock_profile` overrides only timing parameters, not topology.
6. Invalid stimulus targets (driving an output, duplicate drivers) fail before
   execution.
7. A `memory` declaration makes content visible to the circuit at session start.
8. A `reset` declaration establishes known initial state and verifies it.
9. A `derive` signal computes correct values from net state without driving.
10. A `release` action floats an endpoint to Z.
11. A `repeat` executes exactly N times and halts.
12. A `sequence` validates expected clock-by-clock behavior.
