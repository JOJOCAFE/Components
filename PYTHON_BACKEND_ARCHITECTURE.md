# Python Backend Architecture

The simulator should be built like Blender or Maya: the UI is a front-end over
a Python-controlled scene/design model. Every visual action should map to a
Python backend command, and every Python command should be able to update the
same design that the UI displays.

## Core Rule

There must be one authoritative backend design model.

```text
JSON schematic script
        |
        v
normalized Python design model
        |
        +--> Python simulator Board
        +--> block UI scene
        +--> normalized netlist
        +--> Verilog/testbench export
```

The UI must not keep a separate hidden schematic model. It should call Python
backend functions and render the returned state.

## Python Command Style

UI operations should map to readable Python calls:

```python
design = Design("rv8gr_lab01")

design.add_chip("U1", "74HC00", label="NAND gates", module="control")
design.add_bus("DATA", width=8)
design.add_bus("ADDR", width=16)

design.connect("VCC -> U1:14")
design.connect("GND -> U1:7")
design.connect("U1:3 -> DATA:0")

design.pullup("RESET")
design.input_set("front_panel").bind("RESET_SW", "RESET", initial=1)
design.clock("main", to="CLK", frequency_hz=1, duty=0.5)
design.probe_set("debug").add("DATA:0")
design.display("front_leds", type="led_bank", signals=["DATA:0", "DATA:1"])

design.validate()
board = design.to_board()
state = board.snapshot()
```

The block UI should issue the same commands internally when the student drags
chips, wires pins, adds buses, places probes, or edits clocks.

## Front-End / Back-End Contract

The front-end can be web, Python UI, or another tool, but it should talk to the
backend through Python-level commands:

- create/delete chip
- create/delete bus
- connect/disconnect endpoint
- add/remove pull-up or pull-down
- add rail or logic source
- add input set/channel
- add clock
- add probe set/channel
- add display block
- run/settle/step simulation
- validate design
- get design snapshot
- export JSON/netlist/Verilog

The backend returns plain serializable dictionaries for UI rendering:

- chips and pins
- buses and lines
- nets and attached endpoints
- rails, pulls, sources
- clocks, inputs, controls
- probes and displays
- warnings/errors
- simulation values over time

## CLI Tool Contract

The same backend should also be reachable from a command-line tool. The CLI is
not a separate implementation; it is another front-end over the Python design
model.

Recommended command shape:

```sh
python3 -m chiplib.cli validate rv8gr_lab01.json
python3 -m chiplib.cli snapshot rv8gr_lab01.json
python3 -m chiplib.cli run rv8gr_lab01.json --steps all
python3 -m chiplib.cli export-netlist rv8gr_lab01.json -o rv8gr_lab01.net.json
python3 -m chiplib.cli export-verilog rv8gr_lab01.json -o build/rv8gr_lab01_tb.v
```

The CLI should support these modes:

- `validate`: parse JSON, normalize the design, and print structured warnings
  and errors.
- `snapshot`: return the normalized design state as JSON for UI/debug use.
- `run`: build a Python simulator board, apply inputs/clocks/steps, and return
  simulation/probe/display results.
- `probe`: sample named probe sets after a run or step sequence.
- `export-json`: write canonical normalized JSON.
- `export-netlist`: write normalized netlist JSON.
- `export-verilog`: write Verilog module/testbench output when mappings exist.

This gives three equal ways to use the same project file:

```text
UI front-end -> Python backend -> JSON schematic file
CLI command  -> Python backend -> JSON schematic file
Python script -> Python backend -> JSON schematic file
```

Direct Python script use should look like:

```python
from chiplib.design import Design

design = Design.load_json("rv8gr_lab01.json")
report = design.validate()
board = design.to_board()
result = design.run(board, steps="all")
snapshot = design.snapshot()
```

The CLI and UI should call these same Python APIs instead of re-parsing or
re-implementing schematic behavior.

## Round-Trip Requirement

All operations must preserve the JSON/block round-trip:

```text
JSON -> Python design -> UI blocks -> Python design -> JSON
```

The second JSON must describe the same logical design. UI layout coordinates may
change, but chips, buses, connections, probes, displays, clocks, inputs, and
validation settings must remain equivalent.

## Implementation Order

1. Define a `Design` class that stores the normalized schematic model.
2. Add JSON import/export for `Design`.
3. Add `Design.to_board()` to build the existing Python simulator `Board`.
4. Add `Design.snapshot()` for UI rendering.
5. Add CLI commands that call the same `Design` API.
6. Add netlist export/import. ✅
7. Add first-pass Verilog/testbench export. ✅
8. Expand Verilog part mappings for CPU-scale TTL designs.
9. Build UI on top of these Python commands.

This keeps the simulator useful from scripts first, then makes the UI a clear
visual layer over the same backend.
