# Shared Component Library

Reusable component models, DIP pinout notes, and datasheet evidence for RV8, RV8GR, and future `/home/jo/kiro` hardware projects.

This folder is shared project infrastructure. Keep reusable chip models here instead of copying them into one CPU project unless a project needs a frozen local snapshot.

## Layout

- `74HC/` - behavioral Verilog models for 74HC-family logic chips plus per-chip pinout files named `74hcxx-pin.md`.
- `Memory/` - behavioral Verilog models and pinout files for EEPROM, flash EEPROM, and SRAM parts.
- `python/` - reusable Python pin-level behavior models, net wiring, tri-state conflict checks, and propagation-delay simulation.
- `source/` - manufacturer datasheet PDFs used as local evidence for pinout documentation; see `source/README.md` for the retained evidence list.

## Verification Rule

Pinout files are for physical wiring, so they must be verified from a manufacturer datasheet, not memory or generic web summaries. For DIP builds, the cited source must explicitly support a DIP, PDIP, P-DIP, or equivalent through-hole plastic package for that part.

If a part has a Verilog model but no verified DIP/PDIP source, leave its pinout file as a blocked placeholder instead of guessing. Current blocked 74HC pinout placeholders:

- `74HC/74hc150-pin.md`
- `74HC/74hc260-pin.md`

## System Cross-Check Rule

Use `python/` as the first-line behavioral cross-check for TTL CPU systems. The
Python models are pin-number/pin-name addressable, support net wiring and
tri-state conflict checks, and carry propagation-delay metadata for timing
analysis.

Use the Verilog files when a project needs HDL-level comparison, FPGA-oriented
tests, or a second independent implementation. Do not prefer Verilog over the
Python simulator for RV8/RV8GR system behavior checks unless the task is
specifically about Verilog or RTL equivalence.

## Python/Verilog Compatibility Rule

The Python models are the physical behavior contract. For every chip implemented
in Python, the model must use the real DIP pin numbers and names from the
manufacturer-backed pinout file and must model the real control behavior:
active-low enables, tri-state outputs, bidirectional pins, asynchronous clears,
and memory read/write controls.

The Verilog models must match that Python behavior for every overlapping part.
Verilog modules may expose HDL-friendly vector ports instead of individual DIP
pins, but their logic, direction controls, high-Z behavior, and write/read
semantics must stay compatible with the Python model.

Current exception: `74HC150` and `74HC260` have provisional Python functional
models so the full catalog can instantiate, but their physical pinout files
remain blocked until a manufacturer-verified HC-family DIP source is added.

## Naming

- Chip model files use lowercase part names, for example `74HC/74hc245.v`.
- 74HC Verilog modules use `ttl_74hcxx` names.
- Memory Verilog modules use `mem_<part>` names.
- Pinout files use `<part>-pin.md`, one file per chip.

## Tests

Run from `/home/jo/kiro`:

```sh
cd Components/python
python3 -B -m tests.test_chips

iverilog -g2012 -Wall -o /tmp/tb_74hc_smoke.vvp Components/74HC/*.v Components/74HC/tests/tb_74hc_smoke.v
vvp /tmp/tb_74hc_smoke.vvp

iverilog -g2012 -Wall -o /tmp/tb_memory_smoke.vvp Components/Memory/*.v Components/Memory/tests/tb_memory_smoke.v
vvp /tmp/tb_memory_smoke.vvp
```

Expected pass markers:

- `Components Python chip tests passed`
- `74HC SMOKE TEST PASSED`
- `MEMORY SMOKE TEST PASSED`

## Subfolder Docs

- `74HC/README.md` - full 74HC model list, scan notes, and 74xx source coverage.
- `Memory/README.md` - memory model list and datasheet sources.
- `python/README.md` - Python chip-library coverage and usage.
- `BACKLOG.md` - deferred future work, including the visual chip-block UI idea.
