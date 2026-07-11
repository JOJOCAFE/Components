# Virtual Test Instruments

Human guide for `lib/standard/VIRTUAL_TEST_INSTRUMENTS.json`.

The JSON file is canonical. This Markdown explains the student-facing intent of
the instrument set.

## Purpose

Virtual instruments let tests stimulate, observe, estimate, and fail clearly
without changing real chip definitions.

Use them to learn what should happen. Use real instruments to prove what did
happen on hardware.

## Instruments

| Instrument | Use |
|---|---|
| `InputSource` | drives truth-table and control input vectors |
| `ClockSource` | generates repeatable clock profiles |
| `Switch` | models manual on/off or push behavior |
| `Probe` | observes one logic node |
| `BusProbe` | observes active bus drivers and conflicts |
| `RCParasitic` | estimates wiring/probe capacitance delay |
| `OutputAssert` | makes a virtual test fail when output is wrong |
| `DelayNoise` | injects deterministic delay, jitter, or glitch stress |
| `VCC` / `GND` | marks intended virtual rails |
| `Pullup` / `Pulldown` | models weak default logic states |

## Rules

- Put virtual instruments in circuit/test packages, not inside real chip
  definitions.
- Use `OutputAssert` whenever a generated test has an expected result.
- Use `BusProbe` for every shared-bus proof.
- Use `RCParasitic` and `DelayNoise` to choose what must be measured later.
- Never call virtual stress a physical signoff.
