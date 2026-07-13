# 11 — JSON Model

Status: Language Specification v1.0 — canonical interchange contract.

JSON is an interchange syntax for the resolved Object/Topology model, not an
alternate owner of Device behavior. It round-trips the semantic Component
model; presentation-only Resource and Board data are separate references.

## Canonical shape

```json
{
  "schema": "components.topology@1",
  "component": { "id": "example" },
  "instances": [],
  "nets": [],
  "buses": [],
  "operations": [],
  "probes": [],
  "resources": []
}
```

All object IDs are unique within their declared scope. Endpoints identify an
instance and Device-owned port/pin; a net records concrete endpoints, not an
unexpanded expression. Buses record ordered line IDs. Values use explicit
four-state strings where JSON cannot preserve a logical value unambiguously.

## Rules

- Export canonical ordering for reproducible diffs; consumers must not rely on
  object-array position as identity.
- Preserve unknown additive metadata for source round trips, but do not execute
  it without a schema/provider that owns it.
- Generated JSON records must be reproducible from author-owned Device and
  Component source. They are never hand-edited truth.
- Device records use their typed Device schemas; Resource maps use typed
  Resource schemas; neither is embedded as an uncontrolled blob here.

The current repository's schematic JSON and normalized netlist remain
compatibility formats. `components.topology@1` is the language target, not a
requirement to break existing consumers in v1.0.
