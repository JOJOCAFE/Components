# 10 — Execution Model

Status: Language Specification v1.0 — frozen event-simulation contract.

Runtime time is an ordered pair `(time, delta)`. `time` is a non-negative
duration in the selected canonical unit; `delta` orders causally dependent
zero-delay work at the same time. A scheduled event has target driver, value,
time, deterministic sequence, and source span.

## Event loop

```text
take all earliest events
apply driver changes atomically
resolve affected nets (0/1/Z/X)
notify sensitive devices
schedule outputs at delay or next delta
record probes and diagnostics
repeat until quiescent or a declared limit fails
```

Sequential devices sample declared clock edges after the net value is resolved
for that delta. Multiple same-edge state updates commit together; their outputs
then propagate through normal events. Delayed paths use Device-owned timing.
An implementation may offer functional mode where supported delays are zero,
but it must preserve delta causality and edge semantics.

## Resolution

Enabled strong `0` and `1` drives conflict to `X`; any active strong `X`
produces `X`; all `Z` leaves the net at its weak pull or `Z`. A persistent
conflict reports an execution diagnostic. A temporary same-timestamp handoff
may settle only when the event queue proves one driver is withdrawn; it must
not mask a persistent conflict.

## Limits and boundary

The runtime must bound events, time, and same-time/delta iterations. A limit
exceedance is an `InfiniteOscillation`, `Timeout`, or resource diagnostic—not
an arbitrary final signal value. This is a digital logical simulator, not
physical timing, analog, PCB, current, or frequency signoff.
