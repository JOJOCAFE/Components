# 16 — Operation and Trace Protocol Proposal

Status: proposal for the next Language revision.  This document adds no parser
keyword and changes none of the frozen v1 source grammar.

## Purpose

An Operation is a request to act on a resolved Component topology.  A Trace is
the immutable record of what execution observed.  Neither is a Board command,
renderer state, or a replacement for device behavior.

This proposal turns the useful Operation/trace ideas in the legacy reference
set into a small, testable runtime boundary.

## Ownership

| Thing | Owner |
|---|---|
| Operation syntax and structural validity | Language/schema layer |
| Target resolution and permission checks | Resolver/runtime |
| Signal/device behavior | Device Library and interpreter |
| Executable graph | Resolved topology |
| Event ordering and values | Execution model |
| Trace/result records | Runtime |
| Rendering, controls, layout | Board/Resource client |

An interactive Resource or Board emits an Operation.  It must never mutate
device state directly.

## Operation envelope

An operation is a serializable request with a stable target and parameters:

```json
{
  "kind": "inject",
  "target": "Counter.CLK",
  "value": 1,
  "at": { "time_ns": 100, "delta": 0 },
  "request_id": "op-001"
}
```

Initial supported kinds are `inject`, `step`, `run`, `probe`, `inspect`, and
`validate`.  A kind must declare its accepted target type, parameter schema,
permission requirements, and failure modes.  Unknown kinds fail structurally;
they do not become arbitrary interpreter commands.

## Result envelope

Every accepted operation returns a result, even if it produced no signal
change:

```json
{
  "request_id": "op-001",
  "status": "accepted",
  "start": { "time_ns": 100, "delta": 0 },
  "end": { "time_ns": 100, "delta": 2 },
  "trace_id": "trace-42",
  "diagnostics": []
}
```

`rejected`, `failed`, and `timed_out` are distinct statuses.  Diagnostics are
structured records from the Error Model; a UI may format them, but must not
invent their cause.

## Trace contract

A trace records observations, not a second mutable circuit model:

```json
{
  "trace_id": "trace-42",
  "topology_id": "sha256:...",
  "events": [
    {
      "time_ns": 100,
      "delta": 2,
      "target": "Counter.Q[0]",
      "value": "1",
      "cause": "device-evaluation"
    }
  ]
}
```

`value` uses the execution-model signal domain (`0`, `1`, `X`, `Z` where
applicable).  A trace can include named snapshots for test comparison, but
each snapshot must state its observation point and timing coordinate.

## Determinism and replay

For a replayable run, the runtime retains:

- resolved-topology identity and library versions;
- operation sequence and parameters;
- deterministic random seed where randomness is requested;
- initial device state and memory images where those are not topology-derived;
- execution limits and the resulting trace/result records.

This is enough for a test, CLI, Board, Python SDK, or AI client to request the
same operation without granting any client direct access to runtime internals.

## Boundaries

- This protocol does not decide Board layout, resource precedence, or device
  package geometry.
- This protocol does not treat a trace as physical timing signoff.
- Device-specific ports, timing rules, and electrical behavior remain Device
  Library concerns.
- A future canonical JSON schema may encode these envelopes, but the envelope
  shape must first gain resolver and runtime tests.
