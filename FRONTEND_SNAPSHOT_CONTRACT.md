# Frontend Snapshot Contract

Purpose: define the JSON shape a block UI, API client, or teaching tool can
draw without scraping Python simulator internals.

The primary learners are around `10-15` years old, with the same data still
usable by older learners up to about `24`. Field names should stay clear and
direct, while preserving real pins, buses, rails, and logic states.

## Service Command

Current Python entry point:

```python
SimulationService().frontend_snapshot(design)
```

Service envelope:

```json
{
  "contract": "components.service.v1",
  "command": "frontend-snapshot",
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

## Result Shape

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
  "time_ns": 12,
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

## Field Rules

- `chips`: drawable chip blocks with current pin values from `Board.snapshot()`.
- `buses`: bus blocks and their line states.
- `nets`: wires/tags with connected pins, pulls, sources, and current logic
  value.
- `rails`: visible rail blocks such as `VCC` and `GND`.
- `sources`: virtual input, clock, and rail sources that drive nets.
- `stimulus`: input sets and clocks available to UI controls.
- `probes`: probe sets, channels, current values, and history.
- `displays`: student-facing display declarations from schematic JSON.
- `validation`: current validation report.
- `errors`: board/runtime errors that should be visible to the student.
- `warnings`: non-fatal validation or service warnings.
- `layout`: optional UI layout metadata. Layout must never change logic.
- `labels`: aliases that a UI can draw as readable signal names.

## UI Rules

- A frontend may draw only this snapshot plus static DB metadata.
- A frontend must not duplicate chip behavior.
- UI-only coordinates belong in `layout`, not in chip behavior or net logic.
- Missing or unsupported behavior should be shown as clear warnings/errors.
- Student-facing labels should favor simple words, but real pin names and
  numbers must stay visible when inspecting a chip.
