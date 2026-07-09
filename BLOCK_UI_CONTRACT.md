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
  "layout": {}
}
```

Rules:

- `blocks` contains drawable things: `chip`, `bus`, and `rail` blocks.
- `wires` contains visual wire records, each with the original schematic
  connection `rule`, resolved endpoint labels, and optional layout metadata.
- Simulation sections such as `inputs`, `input_sets`, `clocks`, `probes`,
  `displays`, `expect`, `steps`, and `validate` stay at top level so beginners
  can edit the visible circuit while tests and probes remain attached.
- `layout.blocks` and `layout.wires` are UI-owned metadata. The backend
  preserves them but does not use them for electrical behavior.
- Unknown future layout keys should be preserved by clients where practical.

## CLI

```sh
cd python
python3 -m chiplib.cli export-block-ui ../Examples/nand_gate.json
python3 -m chiplib.cli import-block-ui nand_gate.block.json
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
