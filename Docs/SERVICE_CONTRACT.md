# Components Service Contract

This document defines the stable CLI/API contract for future Components
services. It is a service-facing layer over the existing backend direction:
schematic JSON is normalized into the Python `Design` model, and every CLI,
API, UI, exporter, or future external engine works from that normalized state.

The service layer is pluggable. Simulation engines, exporters, and UI/API
wrappers may be replaced or added later, but the main Components program keeps
the canonical chip DB and schematic JSON rules. Services must not create a
second chip database or parse schematic files with private behavior rules.

## Contract Version

Every machine-readable request and response carries a contract version:

```json
{
  "contract": "components.service.v1"
}
```

Versioning rules:

- `components.service.v1` is the first JSON service contract.
- Additive response fields are allowed in the same major version.
- Removing fields, changing field meanings, or changing command semantics
  requires a new major contract such as `components.service.v2`.
- Clients should ignore unknown fields and must check `ok` before using result
  payloads.
- Services should echo the requested contract version when they can honor it.

## Shared Request Shape

CLI commands and API calls use the same logical request shape. A CLI adapter may
construct this object from arguments and files before calling the service.

```json
{
  "contract": "components.service.v1",
  "command": "validate",
  "request_id": "optional-client-id",
  "input": {
    "schematic": {},
    "design": null,
    "netlist": null
  },
  "options": {},
  "context": {
    "cwd": ".",
    "project": null
  }
}
```

Fields:

- `command`: one of the commands in this document.
- `request_id`: optional client value echoed in the response.
- `input.schematic`: readable schematic JSON from `SCHEMATIC_JSON_SPEC.md`.
- `input.design`: canonical normalized design JSON, when the caller already
  has it.
- `input.netlist`: normalized netlist JSON, for exporter or external-engine
  boundaries.
- `options`: command-specific options.
- `context`: optional adapter context for path resolution and user display.

Input precedence:

1. Use `input.design` when supplied because it is already canonical.
2. Otherwise normalize `input.schematic` through `Design`.
3. Use `input.netlist` only for commands that explicitly accept the normalized
   netlist boundary.

CLI file arguments are paths to these same JSON payloads. For example:

```sh
python3 -m chiplib.cli validate rv8gr_lab01.json
python3 -m chiplib.cli run rv8gr_lab01.json
```

## Shared Success Response

```json
{
  "contract": "components.service.v1",
  "command": "validate",
  "request_id": "optional-client-id",
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

Rules:

- `ok` is the first compatibility gate.
- `result` is command-specific.
- `warnings` are non-fatal issues that should be visible to CLI/API/UI clients.
- `metadata.engine` identifies the service implementation, not a different
  behavior contract.

## Shared Error Response

```json
{
  "contract": "components.service.v1",
  "command": "run",
  "request_id": "optional-client-id",
  "ok": false,
  "error": {
    "code": "validation.failed",
    "message": "Design validation failed.",
    "severity": "error",
    "location": {
      "path": "$.chips.U1.part",
      "file": "rv8gr_lab01.json",
      "line": null,
      "column": null,
      "ref": "U1"
    },
    "suggested_fix": "Use a part present in the Components DB.",
    "details": {}
  },
  "warnings": [],
  "metadata": {
    "engine": "python",
    "components_version": null,
    "elapsed_ms": 0
  }
}
```

Error fields:

- `code`: stable machine-readable code such as `parse.invalid_json`,
  `validation.failed`, `db.missing_part`, `simulation.bus_conflict`,
  `export.unsupported_part`, or `internal.error`.
- `message`: short human-readable summary.
- `severity`: `error` or `fatal`; warnings belong in `warnings`.
- `location`: best available JSON path, source file position, net, chip, pin,
  or reference name.
- `suggested_fix`: practical fix when the service can infer one.
- `details`: structured command-specific facts.

## Commands

### validate

Purpose: parse and normalize schematic JSON, check chip DB references, verify
connection shape, and report warnings/errors without running simulation.

CLI:

```sh
python3 -m chiplib.cli validate design.json
```

Request:

```json
{
  "contract": "components.service.v1",
  "command": "validate",
  "input": {
    "schematic": {}
  },
  "options": {
    "strict": false
  }
}
```

Result:

```json
{
  "valid": true,
  "design_id": "rv8gr_lab01",
  "summary": {
    "chips": 3,
    "buses": 2,
    "nets": 14,
    "probes": 5
  },
  "errors": [],
  "warnings": []
}
```

### snapshot

Purpose: return the canonical normalized design and current board-facing state
for UI/debug display.

CLI:

```sh
python3 -m chiplib.cli snapshot design.json
```

Request:

```json
{
  "contract": "components.service.v1",
  "command": "snapshot",
  "input": {
    "schematic": {}
  },
  "options": {
    "include_design": true,
    "include_board": true
  }
}
```

Result:

```json
{
  "design": {},
  "board": {
    "time_ns": 0,
    "chips": {},
    "nets": {},
    "buses": {},
    "rails": {},
    "sources": {},
    "pulls": {}
  },
  "displays": {}
}
```

### run

Purpose: build the simulator board, apply input sets, clock/run steps, evaluate
expectations, and return serializable simulation state.

CLI:

```sh
python3 -m chiplib.cli run design.json
```

Request:

```json
{
  "contract": "components.service.v1",
  "command": "run",
  "input": {
    "schematic": {}
  },
  "options": {
    "steps": [
      { "op": "apply", "input_set": "power_on" },
      { "op": "settle" },
      { "op": "clock", "name": "main", "cycles": 1 },
      { "op": "probe", "set": "front_panel" }
    ],
    "max_time_ns": 1000000
  }
}
```

Result:

```json
{
  "time_ns": 1000,
  "steps": [],
  "snapshot": {},
  "probes": {},
  "displays": {},
  "expectations": {
    "passed": [],
    "failed": []
  },
  "timing": {
    "events": 0,
    "max_time_ns": 1000000
  }
}
```

### probe

Purpose: sample named probe sets from a design after optional run steps.

CLI:

```sh
python3 -m chiplib.cli probe design.json
```

Request:

```json
{
  "contract": "components.service.v1",
  "command": "probe",
  "input": {
    "schematic": {}
  },
  "options": {
    "set": "front_panel",
    "steps": [
      { "op": "settle" }
    ],
    "include_history": true
  }
}
```

Result:

```json
{
  "set": "front_panel",
  "time_ns": 0,
  "samples": [
    {
      "name": "CLK",
      "target": "CLK",
      "value": 0,
      "history": []
    }
  ]
}
```

### explain-result

Purpose: summarize an existing `validate`, `run`, `probe`, or
`circuit-faults` style JSON response for headless CLI/API clients without
rerunning simulation and without adding new electronics facts. The service only
uses fields already present in the provided response, such as `ok`, `command`,
`errors`, `warnings`, `error`, `result.validation`, `snapshot.board.errors`,
`expectations.failed`, and `findings`.

CLI:

```sh
python3 -m chiplib.cli run design.json > /tmp/run-result.json
python3 -m chiplib.cli explain-result /tmp/run-result.json
python3 -m chiplib.cli explain-result /tmp/legacy-result.json --source-command validate
```

API:

```json
{
  "contract": "components.service.v1",
  "command": "explain-result",
  "input": {
    "response": {
      "command": "run",
      "ok": false,
      "result": {}
    }
  },
  "options": {
    "source_command": "run"
  }
}
```

Result:

```json
{
  "format": "components.explain_result",
  "version": 1,
  "contract": "components.service.v1",
  "source_command": "run",
  "ok": false,
  "status": "needs_attention",
  "summary": {
    "command": "run",
    "ok": false,
    "issue_count": 1,
    "warning_count": 0,
    "top_fields": ["command", "ok", "result"]
  },
  "issues": [
    {
      "severity": "error",
      "code": "expectation_failed",
      "summary": "Y was 1",
      "source_path": "$.result.expectations.failed[0]",
      "field_refs": {
        "name": "nand_both_high"
      }
    }
  ],
  "likely_next_steps": [
    {
      "step": "Fix the referenced run fields, then rerun run and explain-result.",
      "source": "references.issue_fields"
    }
  ],
  "stop_before_hardware_warnings": [
    {
      "reason": "run did not report ok=true.",
      "source": "$.ok"
    }
  ],
  "references": {
    "command_field": "$.command",
    "ok_field": "$.ok",
    "issue_fields": ["$.result.expectations.failed[0]"]
  }
}
```

Rules:

- `explain-result` is a summarizer, not a simulator or circuit checker.
- It must not invent pinouts, timing, active-low behavior, bus rules, or
  hardware-ready claims.
- It may repeat `suggested_fix`, `fix`, or `fix_method` text already present in
  the source response.
- It adds generic next steps only when the response does not provide a specific
  fix.
- It reports stop-before-hardware warnings when the source result is not
  `ok=true` for `validate`, `run`, `probe`, or `circuit-faults`, and when the
  provided issue text mentions bus/output/current risk.

### export-block-ui / import-block-ui

Purpose: convert between readable schematic JSON and the drawable block-UI
shape without creating a separate behavior model. Both directions pass through
the normalized Python `Design` contract and preserve probes, inputs, tests, DB
part references, and UI-owned layout metadata.

CLI:

```sh
python3 -m chiplib.cli export-block-ui design.json -o design.block.json
python3 -m chiplib.cli import-block-ui design.block.json -o design.json
```

Requests:

```json
{
  "contract": "components.service.v1",
  "command": "export-block-ui",
  "input": {
    "schematic": {}
  }
}
```

```json
{
  "contract": "components.service.v1",
  "command": "import-block-ui",
  "input": {
    "block_ui": {
      "format": "components.block_ui",
      "version": 1
    }
  }
}
```

Result:

```json
{
  "format": "components.block_ui",
  "version": 1,
  "design": {},
  "blocks": [],
  "wires": [],
  "layout": {}
}
```

### export-netlist

Purpose: export the normalized bridge netlist used by CLI, UI, HDL generation,
and future external engines.

CLI:

```sh
python3 -m chiplib.cli export-netlist design.json -o design.net.json
```

Request:

```json
{
  "contract": "components.service.v1",
  "command": "export-netlist",
  "input": {
    "schematic": {}
  },
  "options": {
    "format": "chiplib.netlist"
  }
}
```

Result:

```json
{
  "format": "chiplib.netlist",
  "version": 1,
  "netlist": {},
  "unsupported": [],
  "warnings": []
}
```

### export-verilog

Purpose: lower the normalized netlist/design to structural Verilog only for
parts with explicit export metadata. The service reports unsupported parts
instead of guessing from names.

CLI:

```sh
python3 -m chiplib.cli export-verilog design.json -o design.verilog.json
python3 -m chiplib.cli export-verilog design.json --text -o design.v
```

Request:

```json
{
  "contract": "components.service.v1",
  "command": "export-verilog",
  "input": {
    "schematic": {}
  },
  "options": {
    "text": false,
    "include_testbench": false,
    "module_name": "rv8gr_lab01"
  }
}
```

Result:

```json
{
  "module": "rv8gr_lab01",
  "verilog": "module rv8gr_lab01; endmodule\n",
  "testbench": null,
  "unsupported": [],
  "warnings": [],
  "required_files": []
}
```

### db --audit

Purpose: audit the canonical Components DB against schema, referenced files,
legacy coverage, export metadata, and visible missing-property reports.

CLI:

```sh
python3 -m chiplib.cli db --audit
```

Request:

```json
{
  "contract": "components.service.v1",
  "command": "db --audit",
  "input": {},
  "options": {
    "strict": true
  }
}
```

Result:

```json
{
  "valid": true,
  "parts_checked": 62,
  "checks": [
    {
      "name": "schema",
      "ok": true,
      "errors": [],
      "warnings": []
    }
  ],
  "missing": [],
  "coverage": {
    "db_parts": 62,
    "legacy_models": 62,
    "legacy_pinouts": 62
  }
}
```

### db --status

Purpose: report DB-backed chip status for humans, automation, and future UI/API
metadata panels.

CLI:

```sh
python3 -m chiplib.cli db --status
```

Request:

```json
{
  "contract": "components.service.v1",
  "command": "db --status",
  "input": {},
  "options": {
    "part": null,
    "include_missing": true
  }
}
```

Result:

```json
{
  "parts": [
    {
      "part": "74HC00",
      "status": "active",
      "package": "DIP14",
      "pinout": "verified",
      "behavior": "available",
      "verilog": "available",
      "export": "available",
      "missing_properties": []
    }
  ],
  "summary": {
    "active": 1,
    "blocked": 0,
    "missing_properties": 0
  }
}
```

### db --catalog

Purpose: return frontend-oriented component palette metadata from grouped DB
manifests without exposing raw migration internals.

CLI:

```sh
python3 -m chiplib.cli db --catalog
python3 -m chiplib.cli db --catalog --group virtual
python3 -m chiplib.cli db --student
python3 -m chiplib.cli db --student --group virtual
python3 -m chiplib.cli db 74HC00 --detail
```

API commands:

- `component-catalog`
- `student-component-catalog`
- `component-detail`
- `component-metadata`

Result shapes:

```json
{
  "format": "components.db.catalog",
  "version": 1,
  "root": "DB",
  "group": "virtual",
  "groups": [
    {
      "id": "virtual",
      "title": "Virtual simulation components",
      "path": "DB/Virtual",
      "count": 8
    }
  ],
  "components": [
    {
      "part": "Probe",
      "group": "virtual",
      "kind": "virtual",
      "role": "measurement",
      "package": {"kind": "virtual", "pins": 1},
      "status": {},
      "evidence": {},
      "procurement": {},
      "capabilities": {
        "physical_pinout": false,
        "python_behavior": false,
        "simulation_service": "sim.probe"
      },
      "warnings": []
    }
  ]
}
```

The `student-component-catalog` command returns
`format: components.db.student_catalog`. It is a smaller learner-facing view
with `readiness`, visible status fields, simulation/export capability flags,
procurement hints, pin previews, and warnings for missing information. It is
intended for students around ages 10-15 while still remaining machine-readable
for frontend clients.

```json
{
  "format": "components.db.component",
  "version": 1,
  "part": "74HC00",
  "group": "74xx",
  "db_path": "DB/74xx/74HC00/definition/definition.json",
  "pins": [
    {"number": 1, "name": "1A", "direction": "input"}
  ],
  "capabilities": {
    "physical_pinout": true,
    "datasheet_verified": true,
    "python_behavior": true,
    "verilog_model": true,
    "verilog_export": true
  },
  "warnings": []
}
```

### circuit-faults

Purpose: run the virtual physical-system fault checker on a circuit-package
JSON file before students trust a virtual circuit.

CLI:

```sh
python3 -m chiplib.cli circuit-faults Lib/Circuits/RV8GR_WholeSystemChipLevelVirtual/circuit.json
```

API:

```json
{
  "command": "circuit-faults",
  "input": {
    "circuit": {
      "schema": "components.lib.circuit",
      "id": "student-circuit",
      "chips": [{"ref": "U1", "part": "74HC04"}],
      "wiring": [{"net": "Y", "connections": ["U1.1", "U1.2"]}]
    }
  }
}
```

`circuit-fault-report` is an API alias with the same input and result shape.
The API accepts the circuit package as JSON data so local HTTP/stdin clients do
not need filesystem access. The CLI keeps the existing path-based behavior.

Result:

```json
{
  "schema": "components.virtual_physical_fault_report",
  "version": 1,
  "circuit": "rv8gr_whole_system_chip_level_virtual",
  "ok": true,
  "checks": {
    "pin_number_truth": {"status": "pass", "finding_count": 0},
    "output_output_bus_contention": {"status": "pass", "finding_count": 0},
    "edge_polarity": {"status": "pass", "finding_count": 0},
    "propagation_delay_deadband": {"status": "pass", "finding_count": 0}
  },
  "findings": []
}
```

This checker is a virtual gate. It catches common pin, bus, edge, and
delay/deadband mistakes, but it is not hardware signoff.

### frontend-snapshot

Purpose: return the stable UI/API drawing snapshot for chips, nets, probes,
displays, warnings, and validation state.

Python:

```python
SimulationService().frontend_snapshot(design)
```

Result:

```json
{
  "format": "components.frontend.snapshot",
  "version": 1,
  "design": {
    "name": "nand",
    "description": "",
    "modules": {},
    "groups": {}
  },
  "time_ns": 0,
  "chips": [],
  "buses": [],
  "nets": [],
  "rails": [],
  "sources": [],
  "stimulus": {},
  "probes": {},
  "displays": {},
  "validation": {},
  "errors": [],
  "warnings": [],
  "layout": {},
  "labels": {}
}
```

### local API wrapper

Purpose: expose the same backend through local stdio JSON lines or HTTP POST
without duplicating chip behavior.

Entrypoints:

```sh
python3 -m chiplib.api --stdio
python3 -m chiplib.api --http --host 127.0.0.1 --port 8765
```

The API accepts the standard service envelope and dispatches by `command`.
Stateful frontend-edit commands operate on the loaded in-memory design:

- `headless-capabilities`
- `ai-capabilities`
- `project-builder`
- `ai-project-builder`
- `create-design`
- `load`
- `create-chip`
- `delete-chip`
- `connect`
- `disconnect`
- `add-bus`
- `set-inputs`
- `step`
- `validate`
- `snapshot`
- `frontend-snapshot`
- `component-catalog`
- `student-component-catalog`
- `component-detail`
- `component-metadata`
- `component-digital`
- `component-package`
- `component-generate`
- `run`
- `probe`
- `export-json`
- `export-netlist`
- `export-verilog`
- `export-block-ui`
- `import-block-ui`

Example:

```json
{
  "contract": "components.service.v1",
  "command": "create-chip",
  "options": {
    "ref": "U1",
    "part": "74HC00",
    "properties": {
      "label": "NAND"
    }
  }
}
```

### headless-capabilities / ai-capabilities

Purpose: return a compact machine-readable manifest for CLI users, local API
clients, and AI assistants. The manifest lists entrypoints, transport behavior,
safe student workflow, student guardrails, command groups, important docs, and
known limits.

CLI:

```sh
python3 -m chiplib.cli headless
```

API:

```json
{
  "contract": "components.service.v1",
  "command": "headless-capabilities"
}
```

AI assistants should read this manifest before helping a student choose parts,
write schematic JSON, run simulation, or suggest real breadboard changes.

### project-builder / ai-project-builder

Purpose: return the concrete build-along workflow for an AI assistant or
headless client helping a student. The response includes discovery, inspection,
drafting, validation, simulation, probe, and safety-check steps plus a starter
schematic and result-explanation rules.

CLI:

```sh
python3 -m chiplib.cli project-builder --part 74HC00
```

API:

```json
{
  "contract": "components.service.v1",
  "command": "project-builder",
  "options": {
    "part": "74HC00",
    "goal": "Build and test a NAND gate before breadboard wiring."
  }
}
```

AI assistants should use `selected_part`, `starter_schematic`, `workflow`, and
`explain_result_rules` from this response instead of hard-coding private
teaching flow.

## Pluggable Service Rules

- The canonical chip identity DB is `DB/` and is read through Components DB
  APIs.
- The canonical student-facing schematic format is `SCHEMATIC_JSON_SPEC.md`.
- A plugin may implement simulation, netlist export, Verilog export, or API
  transport, but it must consume canonical `Design` or normalized netlist JSON.
- A plugin must return the response shapes in this document.
- External simulation engines must consume canonical `Design` or normalized
  netlist JSON and return this service response shape; they must not parse
  student schematic JSON with private chip behavior rules.
- A plugin must report unsupported parts, missing DB metadata, and unsupported
  export features as structured errors or `unsupported` entries.
- A plugin must not silently infer pin mappings or chip behavior from names
  when canonical DB or design metadata is missing.

## CLI Output Modes

Current CLI commands print JSON without extra text. Future readable summaries
may be added only if they do not break automation; JSON must remain available
for every command.

Nonzero exit rules:

- Return exit code `0` when `ok` is true and the command-specific result is
  successful.
- Return a nonzero exit code when `ok` is false.
- `db --audit` should also return nonzero when hard audit failures exist, even
  if the JSON response includes partial check results.
