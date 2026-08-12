# 27 — Safety and Timing Contracts

Status: proposal.  Additive v1.1 profile extension for `component:component`.
Defines runtime invariants, bus safety policies, edge behavior declarations,
timing checks, and extended assertion modes.

## Purpose

A circuit is not just wired correctly — it must also be **safe** at runtime.
Buses must not fight, sequential devices must not be clocked with glitches,
and timing margins must be met.  These are properties that cannot be expressed
with topology alone.

This specification adds declarative contracts that the runtime monitors
continuously (policies) or evaluates on demand (checks).

## Bus safety declarations

```component
bus_safety <bus-id> {
  reject multi_driver;
  reject all_high_z during <phase>;
  require single_driver during <phase>;
}
```

A `bus_safety` block declares runtime invariants for a named bus.  The runtime
raises a diagnostic whenever a declared condition is violated.

```component
bus_safety ibus {
  reject multi_driver;
  reject all_high_z during t1;
}

bus_safety dbus {
  reject multi_driver;
}
```

### Safety conditions

| Condition | Meaning |
|-----------|---------|
| `reject multi_driver` | No two active drivers at the same time on any bit |
| `reject all_high_z` | At least one driver must be active |
| `reject all_high_z during <expr>` | Same, but only when a condition is true |
| `require single_driver` | Exactly one driver at all times |
| `require single_driver during <expr>` | Same, conditional |

The `during` clause references a net, derived signal, or phase expression that
must be high for the condition to be checked.

## Policy declarations (runtime invariants)

```component
policy <policy-id> {
  reject <condition>;
  require <condition>;
}
```

A policy is a named invariant checked at every simulation coordinate.  It is
broader than bus_safety — it can check any signal condition.

```component
policy pc_never_unknown {
  reject pc_low == X;
  reject pc_high == X;
}

policy phase_one_hot {
  reject (t0 & t1) == 1;
  reject (t0 & t2) == 1;
  reject (t1 & t2) == 1;
}
```

Policies are **always active** during simulation.  A policy violation is a
non-fatal diagnostic (warning severity by default) unless the policy declares
`severity error;`:

```component
policy bus_fight_fatal {
  severity error;
  reject ibus_conflict == 1;
}
```

## Edge criteria declarations

```component
edge_criteria <device-or-signal-id> {
  trigger <edge>;
  non_trigger <behavior>;
  async_override <signal>, <behavior>;
}
```

Edge criteria declare the expected clocking behavior of a sequential device.
They are both documentation and testable assertions.

```component
edge_criteria U1 {
  trigger rising;
  non_trigger hold;
}

edge_criteria U8 {
  trigger rising;
  non_trigger hold;
  async_override /CLR, clear_to_zero;
}
```

### Edge types

| Keyword | Meaning |
|---------|---------|
| `rising` | Positive edge triggers state change |
| `falling` | Negative edge triggers state change |
| `both` | Both edges trigger |
| `level_high` | Level-sensitive, active high |
| `level_low` | Level-sensitive, active low |
| `none` | Combinational (no edge sensitivity) |

### Non-trigger behavior

| Keyword | Meaning |
|---------|---------|
| `hold` | Outputs unchanged on non-trigger edge or no edge |
| `transparent` | Level-sensitive: output follows input while active |

### Async override

Declares an asynchronous control that overrides clocked behavior:

```component
async_override /CLR, clear_to_zero;     -- active-low async clear
async_override /PRE, preset_to_one;     -- active-low async preset
```

## Timing check declarations

```component
timing_check <check-id> {
  from <endpoint>;
  through <endpoint>*;
  to <endpoint>;
  expect <time>;
  limit <time>;
  mode <mode>;
}
```

A timing check declares a propagation path and its expected/maximum delay.
The runtime evaluates it in timed simulation mode.

```component
timing_check alu_critical_path {
  from U10.1Y;
  through U11.S0, U12.S3;
  to U19.D0;
  expect 28ns;
  limit 45ns;
}

timing_check clock_to_phase {
  from U8.CLK;
  to U8.QA;
  expect 22ns;
  limit 35ns;
}
```

### Mode

| Mode | Meaning |
|------|---------|
| `propagation` (default) | Combinational propagation delay |
| `setup` | Setup time requirement before clock edge |
| `hold` | Hold time requirement after clock edge |
| `recovery` | Time from async release to clock edge |

```component
timing_check data_setup {
  from ibus;
  to U19.CLK;
  expect 15ns;
  limit 30ns;
  mode setup;
}
```

## Extended assertion modes

The `test` block `assert` is extended beyond simple equality:

### High-Z check

```component
assert data_out is high_z;
assert data_out is not high_z;
```

### Unknown check

```component
assert pc_low is not unknown;
```

### Set membership

```component
assert phase in { 0b001, 0b010, 0b100 };
```

### Inequality

```component
assert count != 0;
assert delay < 45ns;
assert margin >= 10ns;
```

### Timing window

```component
assert z_flag stable within 20ns of clock_edge;
assert data_out valid within 70ns of address_change;
```

### Bus state

```component
assert ibus has single_driver;
assert dbus has no_conflict;
```

## Interaction with simulation modes

| Feature | Functional sim | Timed sim |
|---------|---------------|-----------|
| bus_safety | ✓ checks drivers | ✓ checks drivers |
| policy | ✓ every delta | ✓ every event |
| edge_criteria | ✓ verifies edges | ✓ verifies edges |
| timing_check | ✗ skipped | ✓ measures delay |
| assert timing | ✗ always passes | ✓ checks actual delay |

Functional simulation does not have propagation delay, so timing-specific
checks are skipped (not failed).  All non-timing safety checks run in both
modes.

## AST extensions

```text
BusSafetyNode        { bus_id, conditions: SafetyCondNode[] }
PolicyNode           { name, severity?, conditions: PolicyCondNode[] }
EdgeCriteriaNode     { target, trigger, non_trigger, overrides: AsyncOverrideNode[] }
TimingCheckNode      { name, from, through[], to, expect, limit, mode }
SafetyCondNode       { kind: reject|require, condition, during? }
PolicyCondNode       { kind: reject|require, expression }
AsyncOverrideNode    { signal, behavior }
```

## Required conformance cases

1. `bus_safety reject multi_driver` fires when two outputs drive one bus bit.
2. `policy` fires on every simulation coordinate where condition is met.
3. `edge_criteria` validates that outputs change only on declared trigger edge.
4. `timing_check` measures path delay and reports failure when exceeding limit.
5. `assert is high_z` correctly identifies all-Z bus state.
6. `assert in { ... }` validates set membership.
7. `timing_check mode setup` measures time before clock edge.
8. Functional simulation skips timing checks without false failures.
