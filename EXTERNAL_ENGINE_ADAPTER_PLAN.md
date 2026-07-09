# External Engine Adapter Plan

Purpose: allow a future Rust, C, or C++ simulator to plug into Components
without changing schematic JSON, DB manifests, CLI commands, or UI code.

Python remains the reference engine. An external engine is optional and must
prove compatibility before becoming selectable.

## Boundary

External engines must not parse student schematic JSON directly.

The adapter input is one of:

- normalized design JSON from `Design.to_dict()`
- normalized netlist JSON from `Design.to_netlist()`

The adapter output must match the `SimulationService.run()` result shape:

```json
{
  "ok": true,
  "log": [],
  "snapshot": {},
  "probes": {},
  "displays": {},
  "expectations": {
    "passed": [],
    "failed": []
  },
  "timing": {
    "time_ns": 0,
    "steps": 0,
    "events": 0
  }
}
```

Service wrappers still return the standard service envelope:

```json
{
  "contract": "components.service.v1",
  "command": "run",
  "ok": true,
  "result": {},
  "warnings": [],
  "metadata": {
    "engine": "python",
    "components_version": null,
    "elapsed_ms": 0
  }
}
```

`metadata.engine` may become `rust`, `c`, `cpp`, or another explicit adapter
name, but the result contract must remain stable.

## Invocation Options

Allowed future invocation styles:

- in-process Python extension module
- subprocess with JSON on stdin/stdout
- local stdio JSON-RPC worker

Do not add network transport for an engine until the local adapter contract is
stable.

## Compatibility Rules

- Pin names and pin numbers must match DB/manufacturer-backed manifests.
- `0`, `1`, `Z`, and `X` logic values must match Python semantics.
- Tri-state conflicts and pull conflicts must report structured errors.
- Probe history, expectation results, display state, and timing metadata must
  be serializable JSON.
- Unsupported chips or features must return warnings/errors, not guessed
  behavior.

## Acceptance Tests

Before an external engine is enabled:

- It must run the same service-ready examples as Python.
- It must pass selected Python-vs-engine equivalence tests for gates,
  counters, memories, tri-state bus parts, and ALU-like chips.
- It must produce the same `ok`, board errors, probe values, and expectation
  pass/fail results for each shared test.
- It must be selectable through the service layer, not by UI-specific code.
