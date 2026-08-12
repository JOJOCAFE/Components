# 25 — Virtual Device Catalog

Status: proposal.  Additive v1.1 profile extension.  Defines the standard
virtual device types available in `use standard.virtual as virtual;` for
digital circuit testing and interactive exploration.

## Purpose

Virtual devices are not physical chips.  They are simulation-only constructs
that provide signal sources, observations, and environmental conditions.
They have no DIP package, no manufacturer datasheet, and no physical timing.

Virtual devices are declared with the same `device` syntax as real chips:

```component
device Clock, virtual.ClockSource, { "period_ns": 100 };
device Probe1, virtual.Probe;
```

The `virtual` namespace is the standard library for test infrastructure.
It provides the devices needed to exercise any digital circuit without
coupling the language to a specific simulator or UI framework.

## Catalog

### virtual.ClockSource

Periodic square-wave generator.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `period_ns` | 100 | Period in nanoseconds |
| `initial` | 0 | Starting level |
| `duty` | 0.5 | Duty cycle (0.0–1.0) |
| `phase_ns` | 0 | Phase offset from time zero |

| Port | Direction | Description |
|------|-----------|-------------|
| `OUT` | output | Clock signal |
| `CLK` | output | Alias for OUT (convenience) |

```component
device SysClock, virtual.ClockSource, { "period_ns": 200, "initial": 0 };
connect SysClock.OUT -> clk;
```

**Note:** When using the `clock` stimulus declaration (spec 24), an explicit
ClockSource device is optional.  The `clock` declaration creates an implicit
source.  When both exist, the stimulus declaration configures the device.

### virtual.Switch

Interactive binary toggle.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `initial` | 0 | Starting state |
| `label` | (none) | Human-readable label |
| `kind` | "toggle" | `toggle`, `momentary` |

| Port | Direction | Description |
|------|-----------|-------------|
| `OUT` | output | Current switch state (0 or 1) |

```component
device SW_A, virtual.Switch, { "initial": 1, "label": "Input A" };
connect SW_A.OUT -> a;
```

**Note:** When using the `channel` stimulus declaration, an explicit Switch
device is optional.

### virtual.Probe

Single-signal read-only observation point.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `label` | (none) | Human-readable label |
| `display` | "value" | `value`, `led`, `waveform` |
| `radix` | "bin" | `bin`, `hex`, `dec` |

| Port | Direction | Description |
|------|-----------|-------------|
| `IN` | input | Signal being observed |

A Probe does not load the circuit.  It is a zero-impedance observer.

```component
device Lamp, virtual.Probe, { "display": "led", "label": "Output Y" };
connect y -> Lamp.IN;
```

**Note:** When using the `probe` and `display` declarations, explicit Probe
devices are optional.  The declarations create implicit observation points.

### virtual.BusProbe

Multi-signal bus observation with driver identity and conflict detection.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `width` | (required) | Bus width in bits |
| `label` | (none) | Human-readable label |
| `policy` | "observe" | `observe`, `single_driver`, `no_float` |
| `radix` | "hex" | `bin`, `hex`, `dec` |

| Port | Direction | Description |
|------|-----------|-------------|
| `BUS[n]` | input | Bus signals (width-indexed) |

When `policy` is `single_driver`, the BusProbe raises a diagnostic if more
than one active driver is detected on any bit.  When `no_float`, it raises
a diagnostic if any bit is Z when a driver should be present.

```component
device IBUS_MON, virtual.BusProbe, { "width": 8, "policy": "single_driver", "label": "IBUS monitor" };
connect ibus[0] -> IBUS_MON.BUS[0];
connect ibus[1] -> IBUS_MON.BUS[1];
-- ... all 8 bits
```

**Note:** The `bus_probe` shorthand declaration (spec 27) avoids manual per-bit
wiring:

```component
bus_probe ibus_mon, ibus, { "policy": "single_driver" };
```

### virtual.BusDriver

Programmable bus driver for stimulus injection.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `width` | (required) | Bus width in bits |
| `initial` | Z | Initial drive value (integer or Z) |
| `tristate` | true | Whether the driver can be released |

| Port | Direction | Description |
|------|-----------|-------------|
| `OUT[n]` | output | Driven bus signals |
| `OE` | input | Output enable (active high) |

```component
device DATA_DRV, virtual.BusDriver, { "width": 8 };
connect DATA_DRV.OUT[0] -> data[0];
-- ... or use bus connection shorthand
```

### virtual.RCParasitic

RC load model for timing stress testing.  Adds parasitic capacitance and
series resistance to a net to observe timing degradation.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `R_ohm` | 0 | Series resistance |
| `C_pf` | 0 | Load capacitance |
| `label` | (none) | Human-readable label |

| Port | Direction | Description |
|------|-----------|-------------|
| `A` | inout | Signal side (connects to net) |
| `B` | inout | Load side (ground or next stage) |

```component
device CLK_RC, virtual.RCParasitic, { "R_ohm": 100, "C_pf": 30 };
connect clk -> CLK_RC.A;
connect CLK_RC.B -> clk_loaded;
```

This device affects **timed simulation only**.  In functional (zero-delay)
mode, it acts as a wire.  It does not model analog voltage — only additional
propagation delay proportional to RC.

### virtual.DelayNoise

Adds random timing jitter to a signal path for timing margin stress testing.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `delay_ns` | 0 | Fixed additional delay |
| `jitter_ns` | 0 | Random jitter range (±) |
| `seed` | (deterministic) | Random seed |

| Port | Direction | Description |
|------|-----------|-------------|
| `IN` | input | Input signal |
| `OUT` | output | Delayed/jittered output |

```component
device CLK_JITTER, virtual.DelayNoise, { "delay_ns": 2, "jitter_ns": 3 };
connect clk -> CLK_JITTER.IN;
connect CLK_JITTER.OUT -> clk_noisy;
```

### virtual.OutputAssert

Expected-value checker for automated test pass/fail decisions.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `label` | (none) | Human-readable label |
| `mode` | "exact" | `exact`, `mask`, `range` |

| Port | Direction | Description |
|------|-----------|-------------|
| `IN` | input | Signal or bus being checked |
| `EXPECT` | input | Expected value reference |
| `PASS` | output | High when IN matches EXPECT |

An OutputAssert raises a diagnostic when its input does not match the
expected value.  It is used by the automated test framework to convert
signal observations into pass/fail verdicts without requiring manual probe
inspection.

```component
device CHECK, virtual.OutputAssert, { "label": "AC check" };
connect accumulator -> CHECK.IN;
```

### virtual.SequenceGenerator

Programmable multi-bit pattern generator for bus stimulus.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `width` | (required) | Output width |
| `clock` | (required) | Clock endpoint name |
| `patterns` | [] | Array of integer values |
| `mode` | "once" | `once`, `repeat` |

| Port | Direction | Description |
|------|-----------|-------------|
| `OUT[n]` | output | Pattern output bits |
| `DONE` | output | High when sequence complete |

```component
device ADDR_GEN, virtual.SequenceGenerator, {
  "width": 16, "clock": "clk",
  "patterns": [0x8000, 0x8001, 0x8002, 0x8003]
};
```

### virtual.LogicAnalyzer

Multi-channel waveform capture for display and comparison.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `channels` | (required) | Number of channels |
| `trigger` | "immediate" | `immediate`, `rising`, `falling`, `pattern` |
| `depth` | 1024 | Capture depth (samples) |

| Port | Direction | Description |
|------|-----------|-------------|
| `CH[n]` | input | Channel inputs |
| `TRIG` | input | External trigger |

```component
device LA, virtual.LogicAnalyzer, { "channels": 8, "trigger": "rising", "depth": 256 };
connect t0 -> LA.CH[0];
connect t1 -> LA.CH[1];
connect t2 -> LA.CH[2];
```

## Namespace resolution

Virtual devices are resolved from the `standard.virtual` namespace:

```component
use standard.virtual as virtual;

device Clock, virtual.ClockSource;       -- resolves to standard.virtual.ClockSource
device SW, virtual.Switch;               -- resolves to standard.virtual.Switch
```

Virtual devices do not require DIP package evidence, manufacturer datasheets,
or physical timing data.  They have no procurement status.  Their behavior is
defined entirely by this specification and the runtime implementation.

## Relationship to stimulus declarations

| Stimulus shorthand | Equivalent virtual device |
|--------------------|---------------------------|
| `clock main, clk, { ... };` | `device main, virtual.ClockSource, { ... }; connect main.OUT -> clk;` |
| `channel sw, a, { ... };` | `device sw, virtual.Switch, { ... }; connect sw.OUT -> a;` |
| `probe obs, y;` | `device obs, virtual.Probe; connect y -> obs.IN;` |
| `bus_probe mon, ibus, { ... };` | `device mon, virtual.BusProbe, { ... }; connect ibus -> mon.BUS;` |

The stimulus shorthands are preferred for clarity.  Explicit devices are needed
when non-default parameters, multiple ports, or complex wiring is required.

## Required conformance cases

1. A ClockSource generates edges at the declared period.
2. A Switch holds its state between operations.
3. A Probe observes without loading or driving.
4. A BusProbe detects single-driver violations when policy is set.
5. An RCParasitic adds measurable delay in timed simulation.
6. A DelayNoise produces deterministic jitter from a fixed seed.
7. Virtual devices do not appear in physical netlists or BOM exports.
