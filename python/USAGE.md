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
from chiplib import Board, BusConflictError, X, Z, create_chip, load_image, load_memory
```

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
inputs. Sequential chips expose `clock_edge()` for the modeled clock action.

```python
from chiplib import create_chip

reg = create_chip("74HC574", "U2")
reg.set_input("/OE", 0)
for i, pin in enumerate([2, 3, 4, 5, 6, 7, 8, 9]):
    reg.set_input(pin, (0x5A >> i) & 1)

reg.clock_edge()
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

`Board.clock_edge()` calls `clock_edge()` on every chip, then settles scheduled
outputs.

For future UI work, `Board` is the natural service boundary. A frontend should
send operations such as "create chip", "connect net", "drive pin", "clock",
"settle", and "probe"; the backend should return serializable chip, pin, net,
logic-value, and timing state for drawing.

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
drive clocks during simulation. By default it provides:

- 32 external input channels: `IN0..IN31`
- 8 clock channels: `CLK0..CLK7`

Input channels can bind to any chip pin by number or name. This is useful for
reset lines, DIP switches, bus source values, or UI-controlled pins.

```python
from chiplib import Board, StimulusController, create_chip

board = Board()
u1 = board.add_chip("U1", create_chip("74HC00", "U1"))
stim = StimulusController(board)

stim.bind_input(0, u1, "1A", initial=1)
stim.bind_input(1, u1, "1B", initial=1)
board.settle()
assert u1.read("1Y") == 0

stim.input(1).set(0)
board.settle()
assert u1.read("1Y") == 1
```

Use `set_inputs()` to write many channels from an integer or iterable:

```python
reg = board.add_chip("U2", create_chip("74HC574", "U2"))
for i, pin in enumerate([2, 3, 4, 5, 6, 7, 8, 9]):
    stim.bind_input(i, reg, pin)

stim.set_inputs(0xA5, width=8)
```

Clock channels can be one-shot triggered or run as numeric-frequency clocks.
The clock timing and chip propagation delays are simulator numbers; use them to
calculate and inspect behavior, not as a substitute for physical timing closure.

```python
clk = stim.bind_clock(0, reg, "CLK")

# One pulse, useful for manual/single-step UI buttons.
clk.trigger(width_ns=100)

# Periodic clock, useful for slow human-visible runs or automated stepping.
clk.configure(frequency_hz=2.0, duty=0.5).start()
stim.run_for(2_000_000_000)  # 2 seconds of simulated time
clk.stop(level=0)
```

For a future UI, `stim.snapshot()` returns serializable input/clock state with
channel numbers, values, timing, and target pins. A web frontend can call this
through an API wrapper; a Python frontend can import the controller directly.

## Coverage And Caveats

`create_chip(part, name)` currently instantiates every Verilog component in
`Components/74HC` and `Components/Memory`:

- hand-written models cover the RV8GR-V2 starter set and core memory parts
- catalog models cover the remaining 74HC and memory parts from pinout docs
- `AS6C62256`, `CY7C199`, and `SST39SF010A` are memory catalog models

`74HC150` and `74HC260` are functional/provisional. Their catalog entries use
fallback pinouts because the corresponding pinout Markdown files are still
placeholders without manufacturer-verified HC-family DIP sources. Do not use
those two for physical wiring until their `74HC/*-pin.md` files are verified.

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
5. Sequential parts must implement `clock_edge()` and model asynchronous
   clear/preset behavior in `update()` where the real part has it.
6. Memory parts must use the real DIP address/data/control mapping and expose
   `data` for preload/inspection.
7. Assign realistic `Delay` metadata. It is a simulation default, not a timing
   closure guarantee.
8. Add or update tests in `tests/test_chips.py` for pin aliases, logic behavior,
   tri-state behavior, memory read/write behavior, bus conflicts, and catalog
   instantiation as applicable.
9. For parts present in both Python and Verilog, compare observable behavior:
   same controls, same output polarity, same tri-state rules, and same reset or
   clock behavior. Verilog vector ports may differ, but behavior must not.
10. If a pinout is provisional, mark it clearly and block physical-wiring use
    until the pinout Markdown is manufacturer-verified.
