# Components Student Guide

Components is a library for learning digital logic with real chip behavior.
You can use it before wiring a breadboard to check pins, buses, outputs,
clocks, and simple CPU circuits.

The main learner is around 10-15 years old. The same commands are still useful
for older students and project builders.

## Big Idea

Components has one shared backend:

- the DB says which chips and virtual tools exist
- schematic JSON says how chips, buses, rails, switches, clocks, and probes are
  connected
- the Python service validates and simulates that design
- the CLI is a command-line wrapper around the same service
- the API is a JSON wrapper for future web or desktop tools

Do not make a second chip list in a UI or a class project. Ask the Components
DB and service so the CLI, API, and future GUI all agree.

## What Components Can Check

Components can help answer questions like:

- Is this chip in the library?
- What are the real DIP pin numbers?
- Does this small circuit simulate correctly?
- Did two outputs fight on the same bus?
- Does a clocked chip use the correct rising or falling edge?
- Can this design export a normalized netlist or first-pass Verilog?
- Does an RV8GR circuit pass the current virtual physical-system checks?

Components cannot replace real hardware measurements. A virtual pass does not
prove that a breadboard passes at 1 MHz, 2 MHz, or 5 MHz. Real hardware still
needs voltage, clock, edge-quality, and bus-deadband measurements.

## Start Here

Run commands from the repo root:

```sh
cd /home/jo/kiro/Components
```

Most commands use this prefix:

```sh
PYTHONPATH=python python3 -B -m chiplib.cli
```

For shorter examples below, `CLI` means that full prefix.

For a first student session, do not read every reference document. Do this
short path:

1. Run the NAND example.
2. Look up one chip in the student catalog.
3. Read one circuit proof card only if it matches what you are building.
4. Ask a teacher before changing real wiring, power, or clock speed.

Stop the real build if a chip is hot, the supply current is unexpected, a bus
conflict appears, or two outputs are connected together without a bus-owner
rule.

## Look Up Components

List the student-friendly catalog:

```sh
PYTHONPATH=python python3 -B -m chiplib.cli db --student
```

List only one group:

```sh
PYTHONPATH=python python3 -B -m chiplib.cli db --student --group 74xx
PYTHONPATH=python python3 -B -m chiplib.cli db --student --group memory
PYTHONPATH=python python3 -B -m chiplib.cli db --student --group virtual
```

Look up one chip:

```sh
PYTHONPATH=python python3 -B -m chiplib.cli db 74HC00 --detail
PYTHONPATH=python python3 -B -m chiplib.cli db 74HC245 --package
```

Use `--detail` when you want a readable card with pins and capabilities. Use
`--package` when you want the deeper package layers used by generators and
tests.

Useful readiness words:

| Word | Meaning |
|---|---|
| `ready` | Good for normal examples and simulation. |
| `usable` | Can be used, but some advanced output or evidence may be missing. |
| `needs_info` | Visible in the catalog, but check warnings before building. |

## Run A Small Circuit

The easiest example is `Examples/nand.json`.

Validate it:

```sh
PYTHONPATH=python python3 -B -m chiplib.cli validate Examples/nand.json
```

Run it:

```sh
PYTHONPATH=python python3 -B -m chiplib.cli run Examples/nand.json
```

Read probes:

```sh
PYTHONPATH=python python3 -B -m chiplib.cli probe Examples/nand.json
```

Make a normalized copy:

```sh
PYTHONPATH=python python3 -B -m chiplib.cli export-json Examples/nand.json -o /tmp/nand.normal.json
```

Export a netlist:

```sh
PYTHONPATH=python python3 -B -m chiplib.cli export-netlist Examples/nand.json -o /tmp/nand.net.json
```

Try Verilog export:

```sh
PYTHONPATH=python python3 -B -m chiplib.cli export-verilog Examples/nand.json -o /tmp/nand.verilog.json
PYTHONPATH=python python3 -B -m chiplib.cli export-verilog Examples/nand.json --text -o /tmp/nand.v
```

Verilog export is conservative. If a part has no explicit export mapping, the
tool reports it instead of guessing.

## Read A Schematic JSON File

A schematic JSON file is a typed version of a circuit drawing. It usually has:

- `chips`: named chips such as `U1` or `ROM1`
- `buses`: grouped wires such as `DATA` or `ADDR`
- `aliases`: friendly names such as `CLK` or `RESET`
- `connect`: wiring rules, using real pins like `U1:1`
- `inputs`: named input patterns
- `clocks`: named clock sources
- `probes`: places to watch values
- `expectations`: checks that should pass

The important rule is that physical chip pins stay real. `U1:1` means physical
pin 1 on chip `U1`, not "the first pin I drew on a screen."

## Check A Circuit For Common AI Wiring Mistakes

Use `circuit-faults` on circuit-package JSON files. This is the virtual
physical-system checker added for RV8GR work.

```sh
PYTHONPATH=python python3 -B -m chiplib.cli circuit-faults Lib/Circuits/RV8GR_WholeSystemChipLevelVirtual/circuit.json
```

It checks four mistake classes:

- wrong pin number, pin name, or active-low marker
- output connected to output without a valid bus-enable rule
- missing rising/falling edge statement for clocked chips
- missing R/C, delay-noise, setup/hold, float, or deadband coverage for shared
  buses and stress nets

If `ok` is `true`, the virtual checker did not find these mistakes. If `ok` is
`false`, read the `findings` list and the `fix_method` field.

## Use The API From Another Program

The API adapter uses the same backend as the CLI. It can run as newline JSON on
standard input or as a small local HTTP server.

### Stdio API

Start with a simple catalog request:

```sh
printf '%s\n' '{"command":"student-component-catalog","options":{"group":"virtual"}}' \
  | PYTHONPATH=python python3 -B -m chiplib.api --stdio
```

Create and edit a tiny design:

```sh
printf '%s\n' \
  '{"command":"create-design","options":{"name":"student-nand"}}' \
  '{"command":"create-chip","options":{"ref":"U1","part":"74HC00"}}' \
  '{"command":"connect","options":{"rule":"VCC -> U1:14"}}' \
  '{"command":"connect","options":{"rule":"GND -> U1:7"}}' \
  '{"command":"export-json"}' \
  | PYTHONPATH=python python3 -B -m chiplib.api --stdio
```

The API is stateful during one stdio session. That means each request can build
on the previous request.

### HTTP API

Start the server:

```sh
PYTHONPATH=python python3 -B -m chiplib.api --http --host 127.0.0.1 --port 8765
```

In another terminal, send a request:

```sh
curl -s -X POST http://127.0.0.1:8765 \
  -H 'Content-Type: application/json' \
  -d '{"command":"component-detail","options":{"part":"74HC00"}}'
```

Use HTTP for a web UI or another local program. Stop the server with
`Ctrl-C`.

## Useful API Commands

These commands are available through `chiplib.api`:

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
- `run`
- `probe`
- `export-json`
- `export-netlist`
- `export-verilog`
- `export-block-ui`
- `import-block-ui`
- `component-catalog`
- `student-component-catalog`
- `component-detail`
- `component-digital`
- `component-package`
- `component-generate`

All responses include `ok`. Check `ok` before trusting the result:

```json
{
  "contract": "components.service.v1",
  "command": "snapshot",
  "ok": true,
  "result": {}
}
```

If `ok` is `false`, show the error message and suggested fix to the student
instead of hiding it.

## What To Do When A Test Fails

Read the error or finding, then fix the source of the problem:

- Wrong pin: check the datasheet-backed chip definition and the circuit wire.
- Output-output conflict: add a real bus owner rule or fix tri-state enables.
- Wrong edge: use the datasheet edge and prove the opposite edge holds.
- Delay/deadband risk: add `RCParasitic`, `DelayNoise`, setup/hold, float, or
  deadband evidence.
- Unsupported export: use the Python simulator first, then add an explicit
  export mapping only when the behavior is known.

Do not change expected results just to make a bad circuit pass.

## More Reference

- `SCHEMATIC_JSON_SPEC.md`: how schematic JSON is written.
- `STUDENT_READABILITY_AUDIT.md`: which docs are for students, teachers, or
  maintainers.
- `python/USAGE.md`: deeper Python examples.
- `DB/STUDENT_CATALOG.md`: student catalog fields.
- `DB/COMPONENT_TEST_PROTOCOL.md`: serious chip/circuit test protocol.
- `Lib/Circuits/README.md`: RV8GR circuit packages.
