# 18 — Runtime Model Proposal

Status: proposal.  This defines the runtime object boundary for a future
Components Runtime.  It changes no frozen v1.0 grammar and does not claim that
the current Language fixtures execute.

## Purpose

AST nodes are authoring records and a resolved Component is immutable
compilation output.  Runtime objects are the isolated, mutable state created
when that resolved Component is run.

```text
AST -> Resolved Component -> immutable Topology -> Runtime Session -> Trace
```

The runtime never uses raw source syntax to decide behavior.  It invokes
locked Device behavior through the topology and records only explicit drivers,
scheduled events, and observations.

## Runtime objects

| Object | Owns | Does not own |
|---|---|---|
| RuntimeSession | one execution, limits, deterministic seed | Component source or library truth |
| ComponentInstance | runtime identity for one resolved Component | mutable topology structure |
| DeviceInstance | private state of one resolved Device | Device definition behavior/timing facts |
| NetInstance | current resolved signal and active drivers | AST names or implicit endpoints |
| Signal | four-state value and change coordinate | analog-voltage interpretation |
| Event | target driver, value/action, `(time, delta)`, order, cause | arbitrary host callback authority |
| Clock | explicit source/edge schedule | hidden global time |
| Probe | read-only sampled observation | a signal driver |
| Trace | immutable event/observation/diagnostic record | a second mutable circuit model |

All runtime identities reference stable resolved-topology IDs and library-lock
identities so a trace can be replayed against the same definition set.

## Session lifecycle

1. Accept one validated immutable topology and explicit run options.
2. Construct isolated Device and Net instances with declared initial state.
3. Install explicit rails, pulls, clocks, and requested operation drivers.
4. Schedule events in deterministic `(time, delta, sequence)` order.
5. Atomically apply the next coordinate, resolve affected nets, and notify
   sensitive Device instances.
6. Schedule Device-owned output changes at the declared delay or next delta.
7. Repeat until quiescence, requested stop condition, or an execution limit.
8. Seal the Trace and return result plus structured diagnostics.

This is the event model specified by
[10_Execution_Model.md](10_Execution_Model.md); this proposal names the
objects needed to implement it without changing its semantics.

## Scheduler rules

- Event ordering is deterministic: time, then delta, then a stable sequence.
- All driver changes at one coordinate are applied before affected nets are
  resolved.
- Net resolution uses the digital `0`, `1`, `Z`, `X` domain.  A conflict is a
  visible diagnostic, not an arbitrary winner.
- Sequential Devices sample their declared resolved clock edge, commit state
  together at that edge, then propagate outputs as later events.
- The session enforces event, time, and delta-iteration limits.  A limit is a
  diagnostic result (`timeout` or `oscillation`), never a fabricated value.

## Operations and traces

Clients request bounded operations such as `inject`, `step`, `run`, `probe`,
`inspect`, and `validate`.  An operation becomes an explicit runtime driver or
read-only request; it may not mutate a Device input privately.  The operation
envelope and replay fields remain governed by
[16_Operation_and_Trace_Protocol.md](16_Operation_and_Trace_Protocol.md).

A trace records the resolved-topology identity, library locks, initial state
that is not topology-derived, operation sequence, deterministic seed where
used, event coordinates, requested observations, and diagnostics.  It is
sufficient for reproducible simulation, but is not physical hardware proof.

## Implementation acceptance

A first Components Runtime implementation is ready to claim this contract only
when it has fixtures for:

- event ordering and atomic same-coordinate driver updates;
- delta-cycle propagation and quiescence;
- rising/falling/no-edge behavior for clocked Devices;
- high-Z handoff and output contention;
- declared propagation delay and bounded timeout/oscillation;
- deterministic replay from topology lock plus operation sequence.

Until then, the Language fixtures remain parser/resolver/topology acceptance
targets and must state that execution is deferred.
