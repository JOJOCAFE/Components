# RV8GR Chip-Level Test Plan

Purpose: make RV8GR chip definitions and chip-level tests pass before circuit
packages are treated as ready for system testing.

This is the Components-side gate. Circuit-level packages in `Lib/Circuits/`
must not hide missing chip timing, bus, edge, or propagation evidence.

## Test Order

1. Definition and datasheet gate
   - Pinout, package, logic, active-low controls, and bus direction must match
     the selected datasheet.
   - Timing and electrical rows must be either datasheet-backed or explicitly
     marked as a gap in `DB/RV8GR_CHIP_LEVEL_READINESS.json`.
   - A model-derived delay can support functional simulation, but it cannot
     support a hardware speed claim.
   - Physical chip tests must be recorded at `4.5 V`, `5.0 V`, and `5.5 V`.
     Datasheet rows may only cover nearby reference voltages, so the 5.0 V and
     5.5 V points are bench-measurement requirements unless explicitly sourced.
   - Physical chip tests must also cover a 100-tick manual push-switch run and
     oscillator runs at `50 kHz`, `1 MHz`, `2 MHz`, and `5 MHz`.

2. Chip-level split-record gate
   - Every RV8GR chip must have `truth_table.json`, `timing.json`,
     `tri_state.json`, `bus_fight.json`, and `propagation.json`.
   - Truth vectors must be executable against the Python model.
   - Edge-sensitive chips must show trigger edge, non-trigger behavior, reset or
     clear priority, and hold behavior.
   - Tri-state and bus-fight records must show both safe high-Z and forced
     conflict behavior where the chip can drive a bus.

3. Circuit-level package gate
   - Circuit tests may run after chip functional records pass.
   - Circuit timing claims are blocked when any participating chip still has
     model-derived timing or missing electrical extraction.
   - Physical timing signoff requires datasheet-backed or measured chip rows
     plus bench evidence from the real build.

4. Whole-system gate
   - RV8GR Verilog behavioral and chip-level benches must pass after circuit
     changes.
   - Bugs that change the main CPU wiring, RTL, simulator, or lab instructions
     are fixed first in `/home/jo/kiro/RV8/RV8GR`, then mirrored here.

## Required RV8GR Chip Set

The machine-readable status lives in `DB/RV8GR_CHIP_LEVEL_READINESS.json` and
is enforced by `tests.test_generated_split_records`.

| Part | RV8GR role | Current chip-level gate |
|---|---|---|
| `74HC00` | NAND gates for control decode and glue logic | Ready for circuit functional tests |
| `74HC04` | Inverters for active-low control and reset/clock glue | Ready for circuit functional tests |
| `74HC21` | Dual 4-input AND gates for decode and control qualification | Ready for circuit functional tests |
| `74HC32` | OR gates for control composition | Ready for circuit functional tests |
| `74HC74` | Positive-edge D flip-flops for flags, IRQ latch, and synchronous state | Ready for circuit functional tests |
| `74HC86` | XOR gates for ALU and compare/control paths | Ready for circuit functional tests |
| `74HC157` | Quad muxes for address and data path selection | Ready for circuit functional tests |
| `74HC161` | Positive-edge program counter and counter-style state | Ready for circuit functional tests |
| `74HC164` | Serial-in parallel-out ring/control sequencing support | Ready for circuit functional tests |
| `74HC245` | Bidirectional bus transceiver for shared bus isolation | Ready for circuit functional tests |
| `74HC283` | 4-bit binary adders for the ALU | Ready for circuit functional tests |
| `74HC541` | Octal buffers for unidirectional bus and visible outputs | Ready for circuit functional tests |
| `74HC574` | Positive-edge octal registers for IR, AC, page, and data-path latches | Ready for circuit functional tests |
| `74HC688` | 8-bit equality comparator for branch/page/control decisions | Ready for circuit functional tests |
| `62256` | Generic 32K x 8 SRAM-compatible RAM footprint | Ready for circuit functional tests when Samsung KM62256C-compatible SRAM is installed |
| `AS6C62256` | Alliance 32K x 8 SRAM option for RAM | Ready for circuit functional tests |
| `AT28C256` | 32K x 8 EEPROM option for program ROM | Ready for circuit functional tests |
| `SST39SF010A` | Flash ROM option for program storage | Ready for circuit functional tests |

## Focus Tests

### Timing Margin

- Check chip-level timing records for expected delay, setup/hold, pulse width,
  and output-enable/disable timing where applicable.
- For real build, record the installed part marking and selected datasheet row.
- For each RV8GR chip, repeat the physical timing/logic check at `4.5 V`,
  `5.0 V`, and `5.5 V`.
- For each voltage point, record results for:
  - 100 manual push-switch ticks
  - `50 kHz`
  - `1 MHz`
  - `2 MHz`
  - `5 MHz`
- Do not claim 1 MHz, 2 MHz, or 5 MHz readiness from a model-derived delay.

### Bus Racing

- For `74HC245`, `74HC541`, `74HC574`, EEPROM, SRAM, and flash outputs, prove
  disabled high-Z before another driver owns the bus.
- Bus-fight tests must intentionally force an external conflict and prove the
  simulator reports it.
- For hardware, scope `/OE`, `DIR`, `/WE`, and representative bus bits through
  read/write turnarounds.

### Edge Trigger

- For `74HC74`, `74HC161`, `74HC164`, and `74HC574`, positive-edge capture and
  no-edge hold are required before circuit-level state tests.
- Active-low clear/reset/load controls must be named with `/` prefixes or
  explicit `active_low` metadata.
- Negative-edge behavior must be tested as hold/no-capture unless the datasheet
  says otherwise.

### Propagation Delay

- Propagation records must name source, destination, control condition, and
  expected delay.
- Multi-chip circuit budgets must use chip-level propagation rows as inputs.
- Any path that still uses model-derived chip delay must stay marked as a
  model/source estimate, not physical proof.

## Next Datasheet Extraction Queue

Highest priority before circuit timing signoff:

All RV8GR chip definitions now have datasheet-backed timing/electrical rows.
Next evidence action is physical measurement: record actual chip markings and
run the voltage/frequency sweep before any hardware speed claim.

## Acceptance

Before starting a new circuit-level timing pass:

- `DB/RV8GR_CHIP_LEVEL_READINESS.json` names every RV8GR chip.
- Every part has all five split-record files.
- `DB/RV8GR_CHIP_LEVEL_READINESS.json` declares physical voltage test points
  `4.5 V`, `5.0 V`, and `5.5 V`.
- `DB/RV8GR_CHIP_LEVEL_READINESS.json` declares physical clock profiles for
  100 manual push-switch ticks, `50 kHz`, `1 MHz`, `2 MHz`, and `5 MHz`.
- Every missing datasheet timing/electrical row is visible in the readiness
  file with `physical_timing_allowed: false`.
- `PYTHONPATH=python python3 -B -m tests.test_generated_split_records` passes.
- `PYTHONPATH=python python3 -B -m tests.test_db` passes.
