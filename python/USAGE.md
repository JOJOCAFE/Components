# Components Python Library Usage

Practical pin-level behavior models for JOJOCAFE TTL projects. Use this library
to wire simulated chips like physical DIP parts, cross-check CPU subsystems, and
catch bus, pinout, tri-state, memory, and timing mistakes before breadboard,
PCB, or Verilog work.

The Python models are the physical reference for implemented chips. Verilog may
keep HDL-friendly vector ports, but overlapping behavior must stay compatible
with the real-pin Python model.

The library is also the backend contract for future visual tools. It must stay
frontend-agnostic: a JavaScript/web UI can call it through an API wrapper, and a
Python UI can import it directly, but chip behavior, pin metadata, net
resolution, timing, and memory behavior should live here rather than in the UI.

## Import Path

Run examples from `Components/python`, or add that folder to `PYTHONPATH`:

```bash
cd /home/jo/kiro/Components/python
python3 -B -m tests.test_chips

PYTHONPATH=/home/jo/kiro/Components/python python3 your_test.py
```

```python
from chiplib import Board, BusConflictError, ProbeController, X, Z, create_chip, load_image, load_memory
```

## CLI Runner

The same Python backend can be used from the command line with a schematic JSON
file:

```bash
cd /home/jo/kiro/Components/python

python3 -B -m chiplib.cli validate rv8gr_lab01.json
python3 -B -m chiplib.cli snapshot rv8gr_lab01.json
python3 -B -m chiplib.cli run rv8gr_lab01.json
python3 -B -m chiplib.cli probe rv8gr_lab01.json
python3 -B -m chiplib.cli export-json rv8gr_lab01.json -o canonical.json
python3 -B -m chiplib.cli export-netlist rv8gr_lab01.json -o rv8gr_lab01.net.json
python3 -B -m chiplib.cli export-verilog rv8gr_lab01.json -o rv8gr_lab01.verilog.json
python3 -B -m chiplib.cli export-verilog rv8gr_lab01.json --text -o rv8gr_lab01.v
```

`run` currently supports the first simple step commands: `apply <input-set>`,
`settle`, `run <duration>`, `clock <name> ...`, `probe`, and recorded
`expect <name>` entries. Netlist export writes the normalized bridge format used
by future UI and HDL tools. Verilog export is first-pass and conservative: it
uses explicit pin-number-to-port maps for supported 74HC parts and reports
unsupported chips instead of guessing.

## Create A Chip

Instantiate by part number and reference name. Part names are normalized to
uppercase and may omit dashes.

```python
from chiplib import create_chip

u1 = create_chip("74HC00", "U1")
rom = create_chip("AT28C256", "ROM")
ram = create_chip("62256", "RAM")
flash = create_chip("SST39SF010A", "FLASH")
```

Unsupported parts raise `KeyError`.

## Pins By Number Or Name

Pins can be addressed by real DIP pin number or by pin name. Pin numbers are the
source of truth; names are readability aliases loaded from the model/pinout.

```python
from chiplib import create_chip

u1 = create_chip("74HC00", "U1")

u1.set_input(1, 1)        # pin 1, 1A
u1.set_input("1B", 0)     # named alias for pin 2
u1.update()
u1.commit()

assert u1.read(3) == 1
assert u1.read("1Y") == 1
assert u1.pin_number("1Y") == 3
```

For simple one-chip tests, call `update()` then `commit()` after changing
inputs. Sequential chips expose `clock_edge(pin=None)` for the modeled clock
action. Pass the physical clock pin when the part has more than one clock input
or when the simulator should respect a datasheet-defined clock edge.

```python
from chiplib import create_chip

reg = create_chip("74HC574", "U2")
reg.set_input("/OE", 0)
for i, pin in enumerate([2, 3, 4, 5, 6, 7, 8, 9]):
    reg.set_input(pin, (0x5A >> i) & 1)

reg.clock_edge("CLK")
reg.commit()
```

## Board And Net Wiring

Use `Board` when pins share nets or when propagation delay matters. Connect a
net by name, chip, and pin number/name. Drive inputs through the board, then
settle the event queue.

```python
from chiplib import Board, create_chip

board = Board()
inv = board.add_chip("U1", create_chip("74HC04", "U1"))

board.drive(inv, "1A", 1)
board.settle()

assert inv.read("1Y") == 0
assert board.time_ns == 12
```

Shared nets resolve from enabled output and bidirectional pins:

```python
from chiplib import Board, create_chip

bus = Board()
buf = bus.add_chip("U1", create_chip("74HC541", "U1"))
gate = bus.add_chip("U2", create_chip("74HC00", "U2"))

bus.connect("DATA0", buf, "Y1")
bus.connect("DATA0", gate, "1A")

bus.drive(buf, "A1", 1)
bus.drive(buf, "/OE1", 0)
bus.drive(buf, "/OE2", 0)
bus.settle()

assert gate.read("1A") == 1
```

## Bus Tags

Use `Bus` when a design has grouped lines such as address, data, control, or
internal CPU buses. A schematic can place any number of bus objects, such as
`b0`, `b1`, `b2`, or more. Each bus is a group of named net tags up to 128
lines wide. Line tags use the form `bus:<name>[<index>]`, for example
`bus:b1[0]` through `bus:b1[127]`.

Any number of chip pins can plug into the same tag to define the same
connection. One physical pin can belong to one net/tag at a time.

```python
from chiplib import Board, create_chip

board = Board()
b0 = board.bus("b0", width=128)
b1 = board.bus("b1", width=128)
b2 = board.bus("b2", width=64)

buf = board.add_chip("U1", create_chip("74HC541", "U1"))
nand_a = board.add_chip("U2", create_chip("74HC00", "U2"))
nand_b = board.add_chip("U3", create_chip("74HC00", "U3"))

# These three pins are all on the same connection: bus:b1[0].
board.attach("bus:b1[0]", buf, "Y1")
board.attach("bus:b1[0]", nand_a, "1A")
b1.connect(0, nand_b, "1A")

buf.set_input("A1", 1)
buf.set_input("/OE1", 0)
buf.set_input("/OE2", 0)
board.settle()

assert nand_a.read("1A") == 1
assert nand_b.read("1A") == 1
assert b0.tag(127) == "bus:b0[127]"
assert b2.tag(63) == "bus:b2[63]"
```

`board.attach(tag, chip, pin)` also accepts ordinary non-bus net names, so UI or
API clients can treat tag connection as one operation.

## Pull-Up And Pull-Down Defaults

Use pull-up and pull-down helpers to define the normal state of a floating
connection. This models a weak VCC+resistor pull-up or ground pull-down in the
schematic. Active chip outputs override the pull; conflicting pull directions
on the same net raise `BusConflictError`.

Pulls can attach to ordinary net names, bus tags, or individual chip pins:

```python
from chiplib import Board, create_chip

board = Board()
board.bus("ctrl", width=8)

gate = board.add_chip("U1", create_chip("74HC00", "U1"))
driver = board.add_chip("U2", create_chip("74HC541", "U2"))

# Default ctrl[0] high unless something actively drives it.
board.attach("bus:ctrl[0]", gate, "1A")
board.pullup("bus:ctrl[0]")
board.settle()
assert gate.read("1A") == 1

# An enabled output can override the weak pull-up.
board.attach("bus:ctrl[0]", driver, "Y1")
driver.set_input("A1", 0)
driver.set_input("/OE1", 0)
driver.set_input("/OE2", 0)
board.settle()
assert gate.read("1A") == 0

# Pulls can also be placed directly on otherwise unconnected chip pins.
loose = board.add_chip("U3", create_chip("74HC00", "U3"))
board.pullup_pin(loose, "1A")
board.pulldown_pin(loose, "1B")
assert loose.read("1A") == 1
assert loose.read("1B") == 0
```

## Rails, Logic Sources, And Snapshots

Use rails for visible schematic power/ground drivers and logic sources for
switches, jumpers, buttons, or UI-controlled test inputs. These are strong
drivers, unlike weak pull-ups/pull-downs.

```python
from chiplib import Board, create_chip

board = Board()
board.bus("ctrl", width=4)

gate = board.add_chip("U1", create_chip("74HC00", "U1"))
board.attach("bus:ctrl[1]", gate, "1A")
board.attach("bus:ctrl[2]", gate, "1B")

# Rails are visible named drivers.
board.vcc("bus:ctrl[1]")
board.ground("GND_NET")

# Logic sources are for visible switches or UI-controlled inputs.
board.logic_source("SW1", "bus:ctrl[2]", 1)
board.settle()
assert gate.read("1A") == 1
assert gate.read("1B") == 1

board.set_source("SW1", 0)
assert gate.read("1B") == 0

state = board.snapshot()
errors = board.errors()
```

`Board.snapshot()` returns plain dictionaries/lists for frontend/API use:

- `chips`: part/ref and per-pin number/name/direction/value/net metadata
- `nets`: value, attached pins, pulls, and strong sources
- `buses`: name, width, line tags, values, and attached pins
- `rails`: named rail values such as `VCC=1`, `GND=0`
- `sources`: named logic sources and enabled/value state
- `errors`: structured conflict records suitable for UI display

`Board.clock_edge()` calls `clock_edge()` on every chip, then settles scheduled
outputs. For UI and pin-level simulation, prefer explicit stimulus clock
channels so the backend can apply each part's real rising or falling edge.

For future UI work, `Board` is the natural service boundary. A frontend should
send operations such as "create chip", "create bus", "attach pin to tag",
"add pull", "add rail", "set source", "clock", "settle", and "probe"; the
backend should return `Board.snapshot()` plus probe snapshots for drawing.

## Probe Channels And Assertions

Use `ProbeController` to inspect pins, named nets, or bus tags without mixing
test logic into chip behavior. A board can have any number of named probe sets,
and each probe set has up to 64 channels. Probes record sampled values with
`board.time_ns`, expose a serializable snapshot, and provide assertion helpers
for backend tests.

```python
from chiplib import Board, ProbeController, StimulusController, create_chip

board = Board()
stimulus = StimulusController(board)
probes = ProbeController(board)
front_panel = probes.set("front_panel")
debug_bus = probes.set("debug_bus")

inv = board.add_chip("U1", create_chip("74HC04", "U1"))
stimulus.bind_input(0, inv, "1A", initial=0)
board.attach("bus:probe[0]", inv, "1Y")

y_pin = front_panel.pin("u1_y", inv, "1Y")
y_net = debug_bus.net("inv_out", "bus:probe[0]")
y_bus = debug_bus.tag("inv_out_bus", "bus:probe[0]")

board.settle()
probes.sample()
y_pin.expect(1)
y_net.expect_stable(1)
y_bus.expect(1)

stimulus.input(0).set(1)
board.settle()
probes.sample()

y_pin.expect(0)
y_pin.expect_transition("falling")
y_pin.expect_pulses(1, edge="falling")
state = probes.snapshot()
```

Probe assertions currently cover:

- current or sampled value: `expect(0)`, `expect(1)`, `expect(Z)`, `expect(X)`
- stable windows: `expect_stable(value, since_ns=..., until_ns=...)`
- transitions: `expect_transition("rising"|"falling")`
- pulse counts: `expect_pulses(count, edge="rising"|"falling")`

The snapshot form groups channels by probe set and uses plain dictionaries/lists
so a Python UI or API wrapper can return probe state directly to a web frontend.

## Z, X, And Bus Conflicts

Logic values are `0`, `1`, `Z`, and `X`.

- `Z` is high impedance. Disabled tri-state outputs and released bidirectional
  pins must drive `Z`.
- `X` is accepted as a logic value for tests that need an unknown marker, but
  most chip behavior currently treats non-`1` values as `0` through `bit()`.
- A net with no active driver resolves to `Z`.
- A net with active drivers at different values raises `BusConflictError`.

```python
from chiplib import Board, BusConflictError, create_chip

board = Board()
a = board.add_chip("A", create_chip("74HC541", "A"))
b = board.add_chip("B", create_chip("74HC541", "B"))

board.connect("BUS0", a, "Y1")
board.connect("BUS0", b, "Y1")

a.drive_output("Y1", 1)
try:
    b.drive_output("Y1", 0)
except BusConflictError:
    pass
else:
    raise AssertionError("expected bus conflict")
```

## Propagation Delay And Scheduler

Each chip has `chip.delay`, normally a `Delay(rise_ns, fall_ns=None)`. `Board`
does not change outputs immediately. During `settle()`, each `chip.update()`
queues pending outputs, schedules them using the chip delay for the old-to-new
transition, advances `board.time_ns`, applies same-time events, and repeats
until stable.

```python
from chiplib import Board, create_chip

board = Board()
u1 = board.add_chip("U1", create_chip("74HC04", "U1"))

board.drive(u1, 1, 1)
board.settle()

assert u1.read(2) == 0
assert board.time_ns == u1.delay.rise_ns
```

Use `board.settle(max_events=N)` to catch oscillator loops or a model that never
stabilizes. It raises `RuntimeError` when the event limit is exceeded.

## Memory Usage

Memory chips expose a bytearray named `data`. You can preload it directly or
exercise the real address/data/control pins. `AT28C256`, `62256`,
`AS6C62256`, and `CY7C199` use 15 address bits and `I/O0..I/O7`.
`SST39SF010A` uses 17 address bits and `DQ0..DQ7`.

```python
from chiplib import create_chip, Z

rom = create_chip("AT28C256", "ROM")
rom.data[0x1234] = 0xAB

addr_pins = {
    0: 10, 1: 9, 2: 8, 3: 7, 4: 6, 5: 5, 6: 4, 7: 3,
    8: 25, 9: 24, 10: 21, 11: 23, 12: 2, 13: 26, 14: 1,
}
dq_pins = [11, 12, 13, 15, 16, 17, 18, 19]

for bit_index, pin in addr_pins.items():
    rom.set_input(pin, (0x1234 >> bit_index) & 1)

rom.set_input("/CE", 0)
rom.set_input("/OE", 0)
rom.set_input("/WE", 1)
rom.update()
rom.commit()

value = sum((rom.read(pin) == 1) << i for i, pin in enumerate(dq_pins))
assert value == 0xAB

rom.set_input("/CE", 1)
rom.update()
rom.commit()
assert rom.read("I/O0") == Z
```

For RAM-style writes, drive address and data pins, assert `/CE=0` and `/WE=0`,
then deassert `/WE` and read back with `/OE=0`.

`SST39SF010A` flash is modeled differently from SRAM-style writes: the
simplified simulator write occurs on the falling edge of `/WE` while `/CE=0`
and `/OE=1`, matching the shared Verilog model.

## Loading .bin Or .hex Before Simulation

Use `load_memory()` as the first stage before running a simulator. It copies a
program/data image into a ROM, RAM, EEPROM, or flash chip model that exposes a
`.data` bytearray.

Supported file forms:

- `.bin`: raw bytes copied exactly
- Intel HEX: records beginning with `:`, including extended segment/linear
  address records
- simple text hex: bytes such as `30 42 01 02` or `0x30, 0x42`

```python
from chiplib import create_chip, load_image, load_memory

rom = create_chip("AT28C256", "ROM")
ram = create_chip("62256", "RAM")

# Load a program at address 0 before building/running the CPU board.
load_memory(rom, "program.bin")

# Load data into RAM at an offset and pre-clear the rest to 0x00.
load_memory(ram, "data.hex", offset=0x1000, clear=0x00)

# Read an image without copying it yet.
payload = load_image("program.hex")
assert len(payload) <= len(rom.data)
```

`load_memory()` returns the number of bytes copied. It raises
`ImageLoadError` if the file cannot be parsed, the offset is invalid, the image
does not fit in the target memory, or the target chip has no `.data` bytearray.

This loader is intentionally backend-level. Future web/Python UIs should call it
through their simulator service before `Board.settle()` or `Board.clock_edge()`
runs the circuit.

## External Inputs And Clocks

Use `StimulusController` to create the first input state for a board and to
drive clocks during simulation. It provides:

- any number of named input sets, each with up to 64 external input channels
- 8 clock channels: `CLK0..CLK7`

Input channels can bind to any chip pin by number or name. This is useful for
reset lines, DIP switches, bus source values, or UI-controlled pins. The old
`stim.input(0)` and `stim.bind_input(...)` helpers use the default input set.

```python
from chiplib import Board, StimulusController, create_chip

board = Board()
u1 = board.add_chip("U1", create_chip("74HC00", "U1"))
stim = StimulusController(board)
panel = stim.input_set("panel")
tester = stim.input_set("tester")

panel.bind(0, u1, "1A", initial=1)
tester.bind(0, u1, "1B", initial=1)
board.settle()
assert u1.read("1Y") == 0

tester.input(0).set(0)
board.settle()
assert u1.read("1Y") == 1
```

Use `set_inputs()` to write many channels on the default set from an integer or
iterable. Use `input_set.set_values()` for named sets:

```python
reg = board.add_chip("U2", create_chip("74HC574", "U2"))
for i, pin in enumerate([2, 3, 4, 5, 6, 7, 8, 9]):
    stim.bind_input(i, reg, pin)

stim.set_inputs(0xA5, width=8)
panel.set_values(0b11, width=2)
```

Clock channels can be one-shot triggered or run as numeric-frequency clocks.
They honor each target chip's clock edge. For example, 74HC574 responds to the
rising edge of `CLK`, while 74HC73 and 74HC112 respond to the falling edge of
`CP`. The clock timing and chip propagation delays are simulator numbers; use
them to calculate and inspect behavior, not as a substitute for physical timing
closure.

```python
clk = stim.bind_clock(0, reg, "CLK")

# One pulse, useful for manual/single-step UI buttons.
clk.trigger(width_ns=100)

# Periodic clock, useful for slow human-visible runs or automated stepping.
clk.configure(frequency_hz=2.0, duty=0.5).start()
stim.run_for(2_000_000_000)  # 2 seconds of simulated time
clk.stop(level=0)
```

For a future UI, `stim.snapshot()` returns serializable input-set and clock
state with channel numbers, values, timing, and target pins. A web frontend can
call this through an API wrapper; a Python frontend can import the controller
directly.

## Coverage And Caveats

`create_chip(part, name)` currently instantiates every Verilog component in
`Components/verilog/74HC` and `Components/verilog/Memory`:

- hand-written models cover the RV8GR-V2 starter set and core memory parts
- catalog models cover the remaining 74HC and memory parts from pinout docs
- `AS6C62256`, `CY7C199`, and `SST39SF010A` are memory catalog models

Parts without manufacturer-verified HC-family DIP sources are intentionally
absent from the active Python catalog.

## Verification Commands

Run the smoke and compatibility checks from `Components/python`:

```bash
cd /home/jo/kiro/Components/python
python3 -B -m tests.test_chips
```

Expected success message:

```text
Components Python chip tests passed
```

When changing shared behavior, also run any project-level Python/Verilog tests
that consume `Components` so Python and Verilog stay aligned.

## Rules For Adding Or Changing Chips

Keep Python and Verilog compatible:

1. Use manufacturer-backed DIP pin numbers as the source of truth. Pin names are
   aliases and must match the pinout docs used by catalog loading.
2. Preserve active-low spelling and polarity, normally names beginning with `/`.
3. Disabled tri-state outputs and non-driving bidirectional pins must output
   `Z`.
4. Bidirectional parts must release the side that is not currently driving.
5. Sequential parts must implement `clock_edge(pin=None)` and
   `clock_edge_for_pin(pin)` when the datasheet clock edge is not the default
   rising edge. Multi-clock packages must use the physical pin argument so only
   the section or register tied to that pin changes.
6. Sequential parts must model asynchronous clear/load/preset controls in
   `update()` where the datasheet says those controls are asynchronous.
7. Memory parts must use the real DIP address/data/control mapping and expose
   `data` for preload/inspection.
8. Assign realistic `Delay` metadata. It is a simulation default, not a timing
   closure guarantee.
9. Add or update tests in `tests/test_chips.py` for pin aliases, logic behavior,
   tri-state behavior, memory read/write behavior, bus conflicts, and catalog
   instantiation as applicable.
10. For parts present in both Python and Verilog, compare observable behavior:
   same controls, same output polarity, same tri-state rules, and same reset or
   clock behavior. Verilog vector ports may differ, but behavior must not.
11. If a pinout is provisional, mark it clearly and block physical-wiring use
    until the pinout Markdown is manufacturer-verified.
