# Visual Module Plan

This plan defines the first usable visual chip-block editor for Components.
It must stay a client over `components.block_ui`; it must not become a second
circuit model.

## First Screen

Build one workbench screen with these regions:

- Left palette: searchable component groups from `student-component-catalog`
  and `component-detail`.
- Center canvas: draggable chip, bus, and rail blocks from
  `components.block_ui.blocks`.
- Right inspector: selected block pins, package evidence status, timing status,
  and missing-data warnings.
- Bottom results panel: `validate`, `run`, `probe`, `circuit-faults`, and
  `explain-result` responses.

## Required Student Workflow

1. Start from a loaded schematic or a new empty design.
2. Place a chip from the backend catalog.
3. Place `VCC`, `GND`, and a bus or input source.
4. Connect endpoints by selecting visible pins or bus terminals.
5. Run `validate` before any simulation.
6. Run `circuit-faults` before any breadboard claim.
7. Use `explain-result` to show fixable next steps.
8. Export canonical schematic JSON through `import-block-ui`.

## Backend Commands

The first screen should only call existing stable commands:

- `headless-capabilities`
- `student-component-catalog`
- `component-detail`
- `create-design`
- `create-chip`
- `connect`
- `disconnect`
- `snapshot`
- `validate`
- `run`
- `probe`
- `circuit-faults`
- `explain-result`
- `export-block-ui`
- `import-block-ui`
- `export-json`

## Data Rules

- Coordinates, viewport state, selected block, and wire bend points are UI
  state and belong in `layout`.
- Electrical truth comes only from the normalized `Design` model and DB
  component definitions.
- Pin names and numbers shown on screen must come from `blocks[].pins`.
- Missing datasheet, timing, pinout, Verilog, or simulation data must be shown
  as warnings instead of hidden.
- Package-level RV8GR trace refs are allowed only where `circuit-faults` accepts
  them as symbolic boundaries.

## First Acceptance Gate

The first visual module is ready when a student can build and validate a NAND
sketch without writing JSON:

- choose `74HC00`
- place `VCC`, `GND`, two inputs, and one output/probe
- wire real DIP pins
- run `validate`
- run `run` or `probe`
- view `explain-result` for any failure
- export canonical schematic JSON

## Not In First Screen

- No physical-speed pass/fail claims.
- No custom simulator behavior in the frontend.
- No MCP adapter until UI command names and state transitions settle.
- No freehand pin labels that are not present in DB metadata.
