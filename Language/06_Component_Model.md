# Component Model v1.0

## Definition

A Component describes one machine: named Device instances, explicit nets,
optional probes, declared metadata, and firmware references. It does not
contain copied Device behavior, a symbol layout, or hidden connections inferred
from labels.

```text
Component
  id
  schema
  devices: DeviceInstance[]
  nets: Net[]
  probes: Probe[]
  firmware_refs: Reference[]
  metadata: map
  provenance
```

## Connectivity rules

- Every connection is explicit and becomes a topology edge only after
  resolution and type checking.
- Device pins and ports may be addressed only by a library-proven selector.
- A bus has declared member order and width; it is not a text-name convention.
- Power rails and signal nets are typed separately.
- A Component may reference Resources for presentation, but a Resource cannot
  modify behavior, timing, port direction, or pin truth.

## Component versus Board and Operation

A Board may place or present a Component but cannot create behavior. An
Operation may inject, step, inspect, validate, or export a Component but
cannot create hidden topology. Both are distinct from Component.

## Validation boundary

Structural validation checks a Component against its Schema. Semantic
validation checks real Device ports, widths, direction, power, timing, and
driver ownership. Topology construction starts only after both stages pass.
