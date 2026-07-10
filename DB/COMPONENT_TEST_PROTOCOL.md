# Components Test Protocol

Purpose: define a serious but student-usable protocol for testing Components
chip definitions, virtual test components, circuit packages, and real
breadboard builds.

This protocol adapts professional practice without pretending this repo is an
IC qualification lab. MIL-STD-883 is a high-reliability microcircuit test-method
baseline, JESD78 is the common IC latch-up standard reference, and instrument
vendors such as Keysight document probe selection, bandwidth, and loading as
part of measurement quality. Components uses those ideas as discipline:
source-controlled evidence, non-destructive checks first, calibrated
measurement, repeatable logs, and clear claim boundaries.

Reference anchors:

- MIL-STD-883 overview: https://en.wikipedia.org/wiki/MIL-STD-883
- JESD78 latch-up reference overview: https://en.wikipedia.org/wiki/Latch-up
- Keysight oscilloscope probe selection/loading resource:
  https://www.keysight.com/us/en/assets/7018-01494/technical-overviews/5989-6162.pdf
- TI HCMOS design considerations reference:
  https://www.ti.com/lit/an/scla007a/scla007a.pdf

## Claims

Every test result must say which claim it supports:

| Claim | Allowed evidence |
|---|---|
| Datasheet truth | Local or stable manufacturer datasheet, pinout, timing, electrical rows |
| Model truth | Python/Verilog model vectors that fail the test process on mismatch |
| Circuit functional truth | Circuit JSON plus proof vectors using real component models where available |
| Timing estimate | Datasheet timing, virtual R/C estimate, and explicit margin math |
| Hardware signoff | Physical measurement on the installed circuit at the required voltage and clock points |

Timing estimates and simulations can guide a build, but they cannot become
hardware signoff unless the real circuit was measured.

## Gate 1: Source And Definition

Required for each real chip:

- manufacturer, part family, package, and pin count
- pin names, directions, active-low notation, and buses
- truth table or behavioral equation
- edge-trigger behavior for flip-flops, counters, shift registers, and latches
- tri-state and high-Z behavior for bus drivers and memories
- propagation delay, setup/hold, pulse width, output-enable, and output-disable
  rows where the datasheet provides them
- voltage range and logic threshold/current rows where the datasheet provides
  them

Missing rows are allowed only when visible in readiness/status docs. They must
not be hidden inside circuit tests.

## Gate 2: Non-Destructive Chip Test

Before a chip is used in a circuit package:

1. Inspect the installed part marking and package orientation.
2. Current-limit the supply for first power-on.
3. Check VCC-to-GND resistance before power.
4. Power at 5.0 V first, then repeat required logic checks at 4.5 V and 5.5 V.
5. Do not intentionally perform latch-up, overvoltage, ESD, or destructive
   stress tests in student builds.
6. Record supply current if the part or module behaves unexpectedly.

Pass condition: no excessive current, no hot package, no floating required
input, correct static truth behavior, and no datasheet absolute maximum
violation.

## Gate 3: Timing And Edge Test

Required timing profiles:

- 100 manual push-switch ticks
- 50 kHz
- 1 MHz
- 2 MHz
- 5 MHz

Required voltage points:

- 4.5 V
- 5.0 V
- 5.5 V

For every clocked part, test:

- active edge captures exactly once
- opposite edge holds
- reset/clear/load priority
- setup and hold margin at destination pins
- minimum pulse width

For propagation delay, record:

- driver pin transition time
- destination pin transition time
- threshold-crossing delay
- selected datasheet row or measured row
- pass/fail margin against the selected clock profile

## Gate 4: Bus Ownership And Race Test

For every shared bus:

- name every possible driver
- assert only one enabled driver at a time
- force a simulator conflict vector and prove the test fails correctly
- measure hardware driver turn-off before turn-on when moving between ROM, RAM,
  register, and transceiver ownership
- record `/OE`, `/WE`, `DIR`, selected clock/phase signal, and one representative
  data bit on the same capture

Pass condition: no overlap between active output drivers and enough deadband for
memory output-disable plus buffer enable/disable skew.

## Gate 5: Virtual Parasitic Test Components

Virtual components may be used to model board effects that do not belong in chip
definitions.

Virtual test instruments are listed in `DB/VIRTUAL_TEST_INSTRUMENTS.json`.
They let students use the same protocol shape in simulation before touching the
real build.

Allowed virtual instruments:

- `RCParasitic`: estimates breadboard R/C delay on a named net
- `DelayNoise`: injects deterministic delay, jitter, and optional short glitch
  stress between chip output and chip input
- `OutputAssert`: checks that an observed output matches the expected value and
  makes the virtual test fail loudly
- `Probe`: observes a single logic node
- `BusProbe`: observes active bus drivers and conflicts
- `ClockSource` and `Switch`: generate repeatable clock/push profiles
- `VCC`, `GND`, `Pullup`, and `Pulldown`: make intended rails and default
  states explicit

`RCParasitic` uses:

```text
tau_ns = source_resistance_ohm * total_capacitance_pf / 1000
settling_10_90_ns = 2.2 * tau_ns
```

It must be attached at the circuit/test level, not inside a real chip
definition. It is estimate-only and must not be used as hardware signoff without
oscilloscope measurement at the real driver and destination pins.

`DelayNoise` is different from `RCParasitic`: `RCParasitic` estimates the
physical delay from wiring and capacitance, while `DelayNoise` deliberately
stresses a net with seeded delay, jitter, or a short glitch. Use it between
chips when testing whether a chip output still makes the next chip pass under
delay noise.

Representative nets to model before physical signoff:

- `CLK`
- `/RST`
- memory `/OE` and `/WE`
- one `IBUS` bit
- one `DBUS` bit
- longest or most-loaded address/control net

Student-friendly workflow:

1. Choose the claim: model behavior, circuit behavior, timing estimate, or
   hardware signoff.
2. Add the smallest virtual instruments needed to stimulate and observe it.
3. Run a proof that fails loudly if the expected signal is wrong.
4. Write down what the virtual instrument proved and what it did not prove.
5. Repeat the same signal list with real instruments before hardware signoff.

## Gate 6: Physical Measurement Log

Every physical run must record:

- date, builder, module, board revision, and installed chip markings
- supply voltage at power entry and at a far IC
- clock profile and measured clock period
- probe type and approximate probe capacitance
- measured driver edge and destination edge
- expected value, observed value, pass/fail, root cause, fix, and rerun result

Screenshots or CSV captures are preferred for edge, bus-race, and propagation
claims. A text-only note is acceptable for beginner labs only when it names the
test points and measured values.

## Components Acceptance

A component or circuit package is ready for RV8GR use only when:

- source and definition gates pass
- model tests fail on mismatch
- virtual parasitic estimates exist for timing-sensitive breadboard nets
- physical claims remain blocked until measured
- docs explain the pass/fail rule clearly enough for a 10-15 year old student
  to repeat the test safely
