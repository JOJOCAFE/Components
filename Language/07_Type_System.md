# Type System v1.0

## Purpose

The type system prevents a resolver or interpreter from treating every named
connection as interchangeable. It is checked after name resolution and before
topology execution.

## Core types

```text
DigitalSignal(width, state_domain)
AnalogSignal(unit, range)
PowerRail(name, voltage_domain)
ClockSignal(width=1, edge_policy)
VirtualSignal(kind)
Bus(member_type, width, order)
```

Every Port/Pin has one signal type, a direction, and optional capabilities.
Directions are `input`, `output`, `bidir`, `power`, and `passive`.
Capabilities include active-low meaning, drive mode, tri-state enable, edge
trigger, and physical pin mapping. Capabilities are Device-owned and
evidence-backed.

## Compatibility

1. Connection endpoints require compatible signal kinds and widths.
2. `output` to `output` is invalid unless Device/Schema declares a legal
   shared-drive policy; unresolved contention is an execution error.
3. An `input` does not become a driver merely because an Operation injects a
   value. Operations target declared sources or an explicit test harness.
4. A `PowerRail` cannot join a normal DigitalSignal.
5. Bus ordering, slices, concatenation, and scalar selection are explicit
   topology operations; matching-name expansion is forbidden.
6. `VirtualSignal` participates only where its Schema declares an adapter.

## Unknown and high impedance

TTL-compatible DigitalSignal supports `0`, `1`, `Z`, and `X`. `Z` is not `0`;
`X` indicates unknown or unresolved value and must not be silently converted.
The interpreter defines propagation and settling, not this document.

## Device classes

`digital`, `memory`, `passive`, `virtual`, `discrete`, and `support` are
Device-class schemas, not signal types. Each maps its ports into the core types
and may add domain constraints without changing core direction or topology.
