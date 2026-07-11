# Schematic JSON Script Spec

This is the student-readable source format for digital logic and TTL CPU
simulation. It is easier to read than a raw netlist or Verilog, but it can be
normalized into both.

The primary learner is expected to be around `10-15` years old, with the same
format still useful for older students up to about `24`. Names, examples,
validation messages, and UI-facing metadata should therefore be readable for
beginners without hiding real pins, buses, rails, and logic behavior.

The format is pin-level: `U1:1` means chip `U1`, physical DIP pin `1`.
`DATA:0` means bus `DATA`, line `0`.

## Main Goal

The main simulator goal is a student-friendly UI with chip blocks, bus blocks,
controls, probes, and displays that are easy to understand. The JSON script and
the block UI must round-trip 1-to-1:

- JSON -> block UI must preserve every chip, pin connection, bus, rail, pull,
  input, clock, control, probe, display, label, module, expectation, and step.
- Block UI -> JSON must produce the same logical design without hidden UI-only
  wiring.
- A student may edit either side: typed JSON or visual blocks.
- Probes/displays are part of the design, not temporary debugger state, so they
  must map cleanly in both directions.

The parser should normalize JSON into an internal design model first. Python
simulation, netlist export, Verilog/testbench generation, and UI rendering
should all consume that same model.

The front-end should talk to this model through Python backend commands, in the
same style as Blender or Maya. A block edit in the UI and a Python script call
should perform the same operation on the same design model.

## Complete Shape

```json
{
  "name": "rv8gr_lab_example",
  "description": "Small CPU-lab style schematic with buses, clock, probes, and checks.",

  "chips": {
    "U1": {
      "part": "74HC00",
      "label": "NAND gates",
      "module": "control"
    },
    "U2": {
      "part": "74HC161",
      "label": "4-bit counter",
      "module": "pc"
    },
    "ROM1": {
      "part": "AT28C256",
      "label": "program ROM",
      "module": "memory"
    }
  },

  "buses": {
    "ADDR": { "width": 16, "label": "address bus" },
    "DATA": { "width": 8, "label": "data bus" },
    "CTRL": { "width": 16, "label": "control bus" }
  },

  "aliases": {
    "RESET": "CTRL:0",
    "CLK": "CTRL:1",
    "RD_N": "CTRL:2",
    "WR_N": "CTRL:3",
    "D0": "DATA:0",
    "A0": "ADDR:0"
  },

  "groups": {
    "DBUS": ["DATA:0", "DATA:1", "DATA:2", "DATA:3", "DATA:4", "DATA:5", "DATA:6", "DATA:7"],
    "ABUS_LOW": ["ADDR:0", "ADDR:1", "ADDR:2", "ADDR:3", "ADDR:4", "ADDR:5", "ADDR:6", "ADDR:7"]
  },

  "modules": {
    "control": {
      "label": "Control logic",
      "chips": ["U1"]
    },
    "pc": {
      "label": "Program counter",
      "chips": ["U2"]
    },
    "memory": {
      "label": "ROM and RAM",
      "chips": ["ROM1"]
    }
  },

  "rails": {
    "VCC": 1,
    "GND": 0
  },

  "connect": [
    "VCC -> U1:14, U2:16, ROM1:28",
    "GND -> U1:7, U2:8, ROM1:14",

    "RESET -> U2:1",
    "CLK -> U2:2",

    "U2:14 -> ADDR:0",
    "U2:13 -> ADDR:1",
    "U2:12 -> ADDR:2",
    "U2:11 -> ADDR:3",

    "ADDR:0 -> ROM1:10",
    "ADDR:1 -> ROM1:9",
    "ADDR:2 -> ROM1:8",
    "ADDR:3 -> ROM1:7",

    "ROM1:11 <-> DATA:0",
    "ROM1:12 <-> DATA:1",

    "U1:3 -> U2:7",
    "U1:6, U1:8, U1:11 -> CTRL:4"
  ],

  "pullups": [
    "RESET",
    "RD_N",
    "WR_N"
  ],

  "pulldowns": [
    "DATA:7"
  ],

  "inputs": {
    "power_on": [
      "RESET = 1",
      "CLK = 0",
      "U2:7 = 1",
      "U2:10 = 1"
    ],
    "test_pattern": [
      "DATA:0 = 1",
      "DATA:1 = 0"
    ]
  },

  "input_sets": {
    "front_panel": {
      "channels": [
        { "name": "RESET_SW", "to": "RESET", "initial": 1 },
        { "name": "STEP_SW", "to": "CLK", "initial": 0 }
      ]
    },
    "tester": {
      "channels": [
        { "name": "FORCE_D0", "to": "DATA:0", "initial": 0 }
      ]
    }
  },

  "clocks": {
    "main": {
      "to": "CLK",
      "frequency_hz": 1,
      "duty": 0.5,
      "initial": 0,
      "enabled": false
    }
  },

  "controls": {
    "RESET_BUTTON": {
      "to": "RESET",
      "idle": 1,
      "active": 0,
      "pulse_ns": 1000
    },
    "STEP_BUTTON": {
      "to": "CLK",
      "idle": 0,
      "active": 1,
      "pulse_ns": 1000
    }
  },

  "memory_images": {
    "ROM1": {
      "file": "programs/testrom.hex",
      "offset": 0,
      "clear": 255
    }
  },

  "probes": {
    "front_panel": [
      "RESET",
      "CLK",
      "ADDR:0",
      "ADDR:1",
      "DATA:0"
    ],
    "debug": [
      "U1:3",
      "U2:14",
      "ROM1:11"
    ]
  },

  "displays": {
    "front_leds": {
      "type": "led_bank",
      "signals": ["DATA:0", "DATA:1", "ADDR:0", "ADDR:1"],
      "labels": ["D0", "D1", "A0", "A1"]
    },
    "hex_address_low": {
      "type": "hex",
      "signals": ["ADDR:0", "ADDR:1", "ADDR:2", "ADDR:3"],
      "label": "ADDR low"
    }
  },

  "expect": {
    "after_power_on": [
      "RESET is 1",
      "CLK is 0",
      "DATA:7 is 0"
    ],
    "counter_running": [
      "ADDR:0 changes",
      "CLK has rising"
    ]
  },

  "steps": [
    "apply power_on",
    "settle",
    "expect after_power_on",
    "clock main start",
    "run 1000 ms",
    "clock main frequency 10",
    "run 500 ms",
    "clock main stop",
    "expect counter_running"
  ],

  "validate": {
    "require_power_pins": true,
    "warn_floating_inputs": true,
    "warn_unconnected_outputs": false,
    "error_output_conflicts": true,
    "error_pull_conflicts": true,
    "max_bus_width": 128,
    "max_input_channels_per_set": 64,
    "max_probe_channels_per_set": 64
  }
}
```

## Reference Rules

- `U1:1` is chip reference `U1`, physical pin `1`.
- `DATA:0` is bus `DATA`, line `0`.
- `RESET` can be an alias for another reference such as `CTRL:0`.
- `VCC` and `GND` are rails.
- `A -> B` connects both endpoints to one net. The arrow helps readability.
- `A <-> B` also connects both endpoints to one net, but marks the connection
  as intentionally bidirectional/shared.
- `A, B, C -> D` connects all listed endpoints to one net.
- `pullups` and `pulldowns` are weak defaults.
- `inputs` are one-time initial states applied before simulation.
- `input_sets` are named groups of UI/tester input channels. Each set can have
  up to 64 channels.
- `clocks` are adjustable repeated timing sources.
- `controls` are UI-style buttons or switches.
- `probes` are named groups of signal observers. Each probe set can have up to
  64 channels.
- `displays` are student-facing visual output blocks. They observe signals like
  probes but are meant for UI display, such as LEDs, hex digits, bus viewers, or
  simple logic indicators.
- `expect` and `steps` make the schematic usable as a lab/test file.

## Mapping Targets

The same script can map to:

- Python simulator: chips, buses, rails, pulls, inputs, clocks, controls,
  probes, expectations, and steps.
- Normalized netlist: chips, pins, nets, buses, rails, pulls, sources, and
  metadata.
- Verilog/testbench: module instances, wires, assigns, clock/testbench tasks,
  assertions, and probe signals.
- UI display: modules/sheets, chips, pins, buses, labels, controls, probes, and
  displays, with structured errors from validation.

## UI Round-Trip Rules

- Each JSON chip becomes one block with the same reference name.
- Each bus becomes one bus block with the same name and width.
- Each connection string becomes one or more visible wires/tags.
- Each alias becomes a visible label attached to its target.
- Each module can become a sheet/group/frame in the UI.
- Each input set becomes a visible input header/panel with up to 64 channels.
- Each probe set becomes a visible probe header/panel with up to 64 channels.
- Each display becomes a visible display block.
- UI layout coordinates may be stored later in a `layout` block, but layout
  must not change the logical design.

## RV8GR Use

For RV8GR labs, keep one JSON file per lab or module. Use `modules` for the
student build blocks:

- `clock_reset`
- `pc`
- `rom_buffer`
- `ir_latch`
- `alu`
- `accumulator`
- `ram_datapage`
- `branch_jump`
- `irq_bus`

Use `expect` and `steps` as the lab checklist so the file both documents and
tests the wiring.
