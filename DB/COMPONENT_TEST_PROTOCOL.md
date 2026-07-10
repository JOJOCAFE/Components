# Components Test Protocol

Protocol for deciding whether a component package, model, or circuit proof is
ready to use.

Components tests are evidence gates, not hardware certification. Simulation and
datasheet evidence can support design work; physical claims require measurement
on the installed build.

## Claim Levels

Every report must name the claim it supports.

| Claim | Required evidence |
|---|---|
| Definition ready | package definition loads, validates, and names missing data explicitly |
| Model ready | Python and/or Verilog behavior fails on wrong outputs |
| Circuit ready | circuit JSON uses real package pins and proof vectors pass |
| Timing estimate | datasheet timing, virtual stress, and explicit margin math |
| Physical signoff | measured hardware at the stated voltage, clock, and probe points |

Do not promote a lower claim into a higher claim. A passing model is not a
hardware signoff.

## Gate 1: Definition Package

Every active package must use:

```text
DB/<group>/<part>/definition/definition.json
```

IC packages in `74xx` and `Memory` must use:

```json
{"schema": "db.component.digital"}
```

Virtual, Passive, and Discrete packages must use:

```json
{"schema": "db.component.definition"}
```

Required checks:

- part identity, group, family, role, and package are present
- pin numbers, names, directions, active-low markers, rails, and buses are
  source-backed or explicitly modeled
- timing/electrical fields are datasheet-backed when available
- missing data is visible in package status, validation errors, generated
  records, or test output
- no active package uses `chip.json`, `component.json`, or `chip.schema.json`

Pass command:

```sh
PYTHONPATH=python python3 -B -m tests.test_db
```

## Gate 2: Chip Behavior

Digital ICs must have package-local split records:

- `tests/truth_table.json`
- `tests/timing.json`
- `tests/tri_state.json`
- `tests/bus_fight.json`
- `tests/propagation.json`

Required checks:

- truth vectors execute against the Python model
- clocked parts declare trigger edge and no-edge hold behavior
- async reset, clear, preset, load, enable, and hold priority is explicit
- tri-state parts prove enabled output and disabled high-Z behavior
- bus-capable parts include a forced conflict case
- propagation records name source, destination, condition, and delay source

Pass command:

```sh
PYTHONPATH=python python3 -B -m tests.test_generated_split_records
```

## Gate 3: Verilog And Export

For parts with Verilog support:

- header comments must list physical pin number and pin name
- module ports must match the DB pin names and active-low convention
- package-local `simulation/netlist.json` must describe export metadata
- generated/exported Verilog must follow the same style as checked-in models

Smoke checks should compile both shared-family models and package-local models.

## Gate 4: Circuit Proof

Circuit packages must validate wiring before behavior:

- each chip part exists in DB
- each referenced pin exists on that package
- output-to-output wiring is rejected unless it is a named bus with explicit
  one-driver ownership
- proof vectors fail loudly when expected outputs are wrong
- virtual instruments are used only at circuit/test level, not inside real chip
  definitions

Pass command:

```sh
PYTHONPATH=python python3 -B -m tests.test_lib_circuits
```

## Gate 5: Timing And Bus Risk

Timing estimates must separate:

- datasheet timing paths
- model/default delay
- virtual R/C or delay/noise stress
- measured hardware timing

For shared buses, prove:

- every possible driver is named
- only one driver is enabled at a time
- a forced conflict vector is detected
- output-disable happens before the next output-enable in the intended timing
  plan

Virtual tools:

- `RCParasitic`: estimates net delay from resistance and capacitance
- `DelayNoise`: injects deterministic delay, jitter, or glitch stress
- `BusProbe`: observes active drivers and conflicts
- `OutputAssert`: turns wrong behavior into a failing test

Virtual timing is an estimate. It is not physical signoff.

## Gate 6: Physical Signoff

A physical claim must record:

- installed chip markings and selected datasheet row
- supply voltage at entry and at a far IC
- clock profile and measured period
- probe type and approximate probe loading
- driver pin and destination pin captures for timing-sensitive nets
- expected value, observed value, pass/fail, root cause, fix, and rerun result

Student builds must not intentionally perform latch-up, overvoltage, ESD, or
destructive stress tests.

## Acceptance

A package or circuit is ready only when:

- definition validation passes
- behavior tests fail on mismatch
- pin, edge, tri-state, and bus ownership rules are explicit
- timing claims say whether they are datasheet, model, virtual, or measured
- physical claims remain blocked until measured on hardware
- docs and test names are clear enough for a 10-15 year old student to repeat
  the check safely
