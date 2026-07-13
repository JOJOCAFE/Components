# Build a NOT Gate with a Component

This short lesson is for a first text-based Components session. You will read
one tiny machine, run one safe digital-model test, and explain its result.

You are **not** wiring a breadboard in this lesson. A passing result helps you
learn the logic rule. It does not prove wiring, voltage, current, or speed on
real hardware.

## The idea

A NOT gate changes a value to its opposite:

| Input | Output |
|---:|---:|
| 0 | 1 |
| 1 | 0 |

The example uses one gate inside a real `74HC04` inverter chip. `Clock` gives
the example an input value, `U1` is the chip, and `Observe` lets us look at the
answer.

## 1. Meet the small machine

From the Components repository root, ask for the learner view:

```sh
PYTHONPATH=python python3 -B -m chiplib.cli component-student \
  Language/fixtures/component-v1.1/digital_inverter.component
```

Read the result in this order:

1. `parts` tells you which named pieces are in the machine.
2. `wires` tells you how many explicit connections were made.
3. `things_to_watch` gives the names you can check.
4. `try_tests` gives a small test that this Component declares.

For this example, watch `input_level` and `inverted_level`. The important
wire path is:

```text
Clock.CLK -> clock -> U1.1A
U1.1Y -> inverted -> Observe.IN
```

`U1.1A` is the input of the first inverter gate and `U1.1Y` is its output.
The source also connects the chip's `VCC` and `GND` ports. Those are real
power ports in the digital model; do not omit them when making a real circuit.

## 2. Read the text source

Open `Language/fixtures/component-v1.1/digital_inverter.component`.

Look for these lines:

```component
net clock : digital;
net inverted : digital;
connect clock -> U1.1A;
connect U1.1Y -> inverted;
probe inverted_level, inverted;
```

Say the meaning aloud: “The signal named `clock` enters the inverter. The
signal named `inverted` leaves it. We are allowed to watch `inverted_level`.”

Names make the machine readable. The resolver checks that the chip ports
exist; it does not guess a missing wire or a bus bit for you.

## 3. Run the declared test

Run the named `inversion` test:

```sh
PYTHONPATH=python python3 -B -m chiplib.cli component-run \
  Language/fixtures/component-v1.1/digital_inverter.component --test inversion
```

Find these facts in the JSON result:

- `"ok": true` means this bounded digital-model test passed.
- The test actions set `Clock.CLK` to `0`, settle the model, and check the
  declared `inverted_level` probe.
- The probe value should be `1`: NOT 0 is 1.

To try an input yourself without running the declared test, give an explicit
drive and request one probe:

```sh
PYTHONPATH=python python3 -B -m chiplib.cli component-run \
  Language/fixtures/component-v1.1/digital_inverter.component \
  --drive Clock.CLK=1 --probe inverted_level
```

The `inverted_level` probe should then read `0`: NOT 1 is 0.

## 4. Change one thing, then check it

Copy the fixture to a new file before editing it. Change only the test input
from `0` to `1`, and change the expected answer from `1` to `0`. Then run the
test again.

If a command reports a diagnostic, read its code and source line first. Common
mistakes are an unknown port name, a missing wire, connecting a single wire to
a whole bus, or putting two outputs on the same net.

## What this lesson proves—and does not prove

It proves only the supported Components **digital model** for this resolved
leaf Component. It does not create a `component:board`, select physical
placement or routing, measure timing, or prove a breadboard is safe or fast.

Before real wiring, use the student catalog for the real `74HC04` package,
check its power and pin information, and work with a teacher. Stop a physical
build if a chip is hot, supply current is unexpected, or two outputs may be
driving one wire.
