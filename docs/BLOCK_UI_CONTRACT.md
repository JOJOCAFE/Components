# Components Block-UI Contract

`components.block_ui` is the drawable editing shape for a schematic. It is not
a second simulator model. Import and export must always pass through the
normalized Python `Design` model so JSON files, CLI commands, API clients, and
future visual editors keep the same chip behavior and wiring rules.

## Shape

```json
{
  "format": "components.block_ui",
  "version": 1,
  "design": {
    "name": "nand-lab",
    "description": "one NAND gate"
  },
  "blocks": [],
  "wires": [],
  "nets": [],
  "run_config": {},
  "editor": {},
  "layout": {}
}
```

Rules:

- `blocks` contains drawable things: `chip`, `bus`, and `rail` blocks.
- `chip` blocks expose DIP placement metadata (`shape`, `package`) plus real
  pin entries with number, name, direction, side, side index, DIP position,
  value, and attached net when the backend can resolve one. `bus` and `rail`
  blocks expose drawable terminal entries too.
- `wires` contains visual wire records, each with the original schematic
  connection `rule`, resolved endpoint labels, endpoint detail objects for
  pins/nets/buses/rails, and optional layout metadata.
- `nets` exposes backend-resolved net names, connected pin endpoints, pulls,
  sources, and current logic value for drawing or inspection. It is derived
  from the normalized `Design`; layout still owns only coordinates.
- `run_config` tells a visual editor which backend command shape to prepare and
  which backend is selected. Python simulation starts from the normalized
  design, while Verilog export starts from the normalized `chiplib.netlist`
  boundary.
- `editor` exposes backend-owned editor affordances: palette command sources,
  safe editing actions, validation gates, student rules, and MCP-ready tool
  names mapped to the existing CLI/service operations. It is metadata for
  clients; it is not another circuit model.
- Simulation sections such as `inputs`, `input_sets`, `clocks`, `probes`,
  `displays`, `expect`, `steps`, and `validate` stay at top level so beginners
  can edit the visible circuit while tests and probes remain attached.
- `layout.blocks` and `layout.wires` are UI-owned metadata. The backend
  preserves them but does not use them for electrical behavior.
- Unknown future layout keys should be preserved by clients where practical.
- Import accepts either legacy `wire.rule` strings or visual endpoint objects.
  When a wire has no `rule`, the backend builds one from endpoint `ref` values
  or from `{kind, chip, pin}`, `{kind, block, number}`, `{kind, bus, index}`,
  `{kind, block, terminal}`, `{kind, rail}`, and `{kind, name}` fields.

## CLI

```sh
cd python
python3 -m chiplib.cli export-block-ui ../examples/circuits/nand.json
python3 -m chiplib.cli import-block-ui nand.block.json
```

`export-block-ui` reads schematic JSON and returns `components.block_ui`.
`import-block-ui` reads `components.block_ui` and returns canonical schematic
JSON compatible with `SCHEMATIC_JSON_SPEC.md`.

## API

Use `export-block-ui` after loading or creating a design:

```json
{"command": "export-block-ui"}
```

Use `import-block-ui` to replace the active design from a visual editor:

```json
{
  "command": "import-block-ui",
  "input": {
    "block_ui": {
      "format": "components.block_ui",
      "version": 1,
      "design": {"name": "nand-lab"},
      "blocks": [],
      "wires": []
    }
  }
}
```

Frontends should call DB catalog commands for palette metadata:

```sh
python3 -m chiplib.cli db --student
python3 -m chiplib.cli db --catalog --group 74xx
```

The visual editor should show missing DB properties as learner-facing warnings
instead of inventing chip behavior or pin data.

## Editor And MCP Adapter Boundary

The preferred architecture is:

```text
visual editor or MCP client
    -> components.block_ui editor metadata
    -> existing CLI/API/service commands
    -> normalized Design model
```

MCP tools should be thin adapters over existing service commands, for example:

- `component_catalog` -> `db --catalog`
- `component_detail` -> `db PART --detail`
- `validate_design` -> `validate JSON_FILE`
- `run_design` -> `run JSON_FILE`
- `export_block_ui` -> `export-block-ui JSON_FILE`
- `import_block_ui` -> `import-block-ui JSON_FILE`

Keep CLI and tests authoritative. MCP should not own chip behavior, pin truth,
simulation rules, or generated docs.
