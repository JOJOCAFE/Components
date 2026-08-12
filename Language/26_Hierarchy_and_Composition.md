# 26 — Hierarchy and Composition

Status: proposal.  Additive v1.1 profile extension for `component:component`.
Defines how one Component instantiates another as a sub-circuit.

## Purpose

RV8GR uses 35 chips.  Expressing the entire CPU as one flat Component is
impractical.  The hierarchy model lets authors compose verified sub-circuits
into larger systems while preserving each sub-circuit's tested interface.

```text
RV8GR_WholeSystem
  ├── RV8GR_RingCounter      (U8 + U24)
  ├── RV8GR_PC16             (U3 + U4)
  ├── RV8GR_AluAccumulator   (U10..U19)
  ├── RV8GR_BusOwnership     (U7 + U14 + U25)
  └── ...
```

## Port declarations (boundary)

A Component intended for reuse declares its public boundary ports:

```component
component:component RV8GR_RingCounter is components.digital {
  -- Public boundary ports
  port CLK : digital, input;
  port /CLR : digital, input;
  port T0 : digital, output;
  port T1 : digital, output;
  port T2 : digital, output;

  -- Internal topology (devices, nets, connect)
  ...
}
```

Port declarations make the Component's external interface explicit.  Internal
nets not declared as ports are private — invisible to parent circuits.

### Port syntax

```component
port <port-id> : <signal-kind>, <direction>;
port <port-id> : <signal-kind>, <direction>, { <metadata> };
```

Direction: `input`, `output`, `inout`, `power`.  Metadata is optional:
active-low, edge sensitivity, bus membership.

### Bus ports

```component
port IBUS[8] : digital, inout;
port ADDR[16] : digital, output;
```

A bus port declares an ordered collection with explicit width.

## Sub-circuit instantiation

```component
use project.RV8GR_RingCounter as RingCounter;

instance ring, RingCounter;
```

Or with an inline path:

```component
instance ring, "RV8GR_RingCounter/circuit.component";
```

An instance is a complete, isolated copy of the sub-circuit's resolved
topology.  Its internal devices, nets, and probes are namespaced under the
instance name.

### Connecting to instance ports

```component
connect clk -> ring.CLK;
connect reset_n -> ring./CLR;
connect ring.T0 -> t0;
connect ring.T1 -> t1;
connect ring.T2 -> t2;
```

Only declared ports are accessible.  Attempting to connect to an internal net
(`ring.not_t0`) is a resolver error.

### Bus connections

```component
connect addr -> pc.ADDR;    -- bus-to-bus (widths must match)
connect ibus -> alu.IBUS;   -- bidirectional bus
```

## Resolver contract for hierarchy

1. Resolve the parent Component's imports and instance declarations.
2. For each instance, load and fully resolve the sub-circuit Component
   independently (same resolution order as spec 17).
3. Verify that each connection from parent to instance targets a declared port.
4. Verify width, direction, and signal-kind compatibility at every port
   connection.
5. Check for port width mismatches, unconnected required ports, and direction
   conflicts.
6. The instance's internal topology is immutable — the parent cannot override
   device parameters, add connections to internal nets, or access internal
   probes directly.

## Instance namespacing

| Reference | Meaning |
|-----------|---------|
| `ring.T0` | Port T0 of instance `ring` |
| `ring.U8` | ERROR — internal device, not accessible |
| `ring.phase_t0` | ERROR — internal probe, not accessible |

A parent Component may declare its own probes on the instance's port signals:

```component
probe ring_t0, ring.T0;
display ring_t0 as waveform, { "label": "Ring T0" };
```

## Stimulus and tests in hierarchical components

Sub-circuit stimulus (input presets, clocks, channels) is private.  A parent
Component provides its own stimulus at its own level:

```component
-- Parent provides the clock; ring counter receives it through port
clock sys_clk, clk, { "period_ns": 200 };
connect clk -> ring.CLK;
```

Sub-circuit tests remain valid for standalone verification.  When instantiated,
a parent test exercises the sub-circuit through its ports.

## Hierarchy depth

Composition is recursive.  A sub-circuit may itself instantiate other
sub-circuits.  Resolver recursion depth is bounded (suggested limit: 16).
Circular instantiation is a resolver error.

## Lock and versioning

An instance declaration locks to a specific resolved version of the sub-circuit
at resolution time.  The resolved topology includes:

- Component identity and content hash
- Device library identities used by the sub-circuit
- Port interface contract

If the sub-circuit's port interface changes, the parent must be re-resolved.
Internal changes that do not affect ports do not require parent re-resolution.

## AST extensions

```text
PortDeclNode         { name, signal_kind, direction, width?, metadata? }
InstanceDeclNode     { name, source_ref }
```

## Required conformance cases

1. A Component with `port` declarations exposes only those ports externally.
2. An `instance` creates an isolated resolved sub-circuit.
3. Parent-to-port connections validate width, direction, and kind.
4. Internal device references through an instance are rejected.
5. Recursive composition resolves to bounded depth.
6. Sub-circuit changes that preserve port interface do not break parents.
