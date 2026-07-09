# Shared Component Library

Reusable component models, DIP pinout notes, and datasheet evidence for RV8, RV8GR, and future `/home/jo/kiro` hardware projects.

This folder is shared project infrastructure. Keep reusable chip models here instead of copying them into one CPU project unless a project needs a frozen local snapshot.

## Layout

- `74HC/` - behavioral Verilog models for 74HC-family logic chips plus per-chip pinout files named `74hcxx-pin.md`.
- `Memory/` - behavioral Verilog models and pinout files for EEPROM, flash EEPROM, and SRAM parts.
- `python/` - reusable Python pin-level behavior models, net wiring, tri-state conflict checks, and propagation-delay simulation.
- `source/` - manufacturer datasheet PDFs used as local evidence for pinout documentation; see `source/README.md` for the retained evidence list.
- `SCHEMATIC_JSON_SPEC.md` - readable JSON schematic script contract for
  digital simulation, CPU labs, netlist export, Verilog/testbench generation,
  and future UI display.
- `PYTHON_BACKEND_ARCHITECTURE.md` - backend-first architecture where JSON,
  UI blocks, CLI commands, Python scripts, netlists, and Verilog all talk
  through one Python design model.

## Verification Rule

Pinout files are for physical wiring, so they must be verified from a manufacturer datasheet, not memory or generic web summaries. For DIP builds, the cited source must explicitly support a DIP, PDIP, P-DIP, or equivalent through-hole plastic package for that part.

If a part has no verified DIP/PDIP source, do not keep a physical pinout file or
catalog model for it. Add the part only after manufacturer-backed package and
pin evidence is available.

## System Cross-Check Rule

Use `python/` as the first-line behavioral cross-check for TTL CPU systems. The
Python models are pin-number/pin-name addressable, support net wiring and
tri-state conflict checks, and carry propagation-delay metadata for timing
analysis.

The long-term simulator goal is a student-friendly block UI whose design state
round-trips 1-to-1 with `SCHEMATIC_JSON_SPEC.md`: JSON can become editable
blocks, and blocks can become the same logical JSON, including probes and
display blocks. The UI should behave like Blender or Maya: a front-end that
calls Python backend commands and renders the returned design/simulation state.
The same backend must also be callable by CLI and by direct Python scripts, all
using the same JSON schematic file.

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

`Design.to_netlist()` exports the normalized bridge format used by CLI, future
block UI work, and HDL generation. `Design.to_verilog()` lowers that netlist to
structural Verilog only for parts with explicit pin-number-to-port mappings; it
reports unsupported parts instead of guessing from names.
`Design.from_kicad_netlist()` can import KiCad generic netlists for compatibility
smoke tests against existing projects such as RV8GR-V2.

Parts without manufacturer-verified DIP evidence, such as the previously
provisional `74HC150` and `74HC260`, are intentionally absent from the active
catalog.

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
python3 -B -m tests.test_design
python3 -B -m tests.test_netlist
python3 -B -m tests.test_cli

iverilog -g2012 -Wall -o /tmp/tb_74hc_smoke.vvp Components/74HC/*.v Components/74HC/tests/tb_74hc_smoke.v
vvp /tmp/tb_74hc_smoke.vvp

iverilog -g2012 -Wall -o /tmp/tb_memory_smoke.vvp Components/Memory/*.v Components/Memory/tests/tb_memory_smoke.v
vvp /tmp/tb_memory_smoke.vvp
```

Expected pass markers:

- `Components Python chip tests passed`
- `Components Python design tests passed`
- `Components Python netlist tests passed`
- `Components Python CLI tests passed`
- `74HC SMOKE TEST PASSED`
- `MEMORY SMOKE TEST PASSED`

## Subfolder Docs

- `74HC/README.md` - full 74HC model list, scan notes, and 74xx source coverage.
- `Memory/README.md` - memory model list and datasheet sources.
- `python/README.md` - Python chip-library coverage and usage.
- `SCHEMATIC_JSON_SPEC.md` - complete JSON schematic-script shape for digital
  and CPU simulation projects.
- `PYTHON_BACKEND_ARCHITECTURE.md` - Python command/API model for the future
  block UI, CLI tool, Python script use, netlist exporter, and Verilog/testbench
  exporter.
- `BACKLOG.md` - deferred future work, including the visual chip-block UI idea.
