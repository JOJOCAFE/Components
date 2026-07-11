# Virtual Test Generator Contract

Human guide for `lib/standard/VIRTUAL_TEST_GENERATOR_CONTRACT.json`.

The JSON file is canonical. This Markdown explains how to use it without
duplicating every field.

## Purpose

The contract maps chip split-record tests into reusable virtual benches.
Generated benches help students prove behavior before they wire a real circuit.

Input split records:

- `truth_table`
- `timing`
- `tri_state`
- `bus_fight`
- `propagation`

Bench levels:

- `chip`: prove one component model against package-local tests
- `circuit`: prove connected components and bus ownership
- `system`: run larger traces while injecting selected delay/noise stress

## Required Pattern

Every generated virtual bench should:

- drive inputs with `InputSource`, `ClockSource`, or `Switch`
- observe outputs with `Probe` or `BusProbe`
- fail loudly with `OutputAssert`
- use `RCParasitic` and `DelayNoise` only as virtual stress tools
- report what was proven and what still needs physical measurement

## Boundary

Generated virtual benches prove model behavior and stress assumptions. They do
not replace datasheet evidence or measured hardware timing.
