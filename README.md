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

## Naming

- Chip model files use lowercase part names, for example `74HC/74hc245.v`.
- 74HC Verilog modules use `ttl_74hcxx` names.
- Memory Verilog modules use `mem_<part>` names.
- Pinout files use `<part>-pin.md`, one file per chip.

## Tests

Run from `/home/jo/kiro`:

```sh
iverilog -g2012 -Wall -o /tmp/tb_74hc_smoke.vvp Components/74HC/*.v Components/74HC/tests/tb_74hc_smoke.v
vvp /tmp/tb_74hc_smoke.vvp

iverilog -g2012 -Wall -o /tmp/tb_memory_smoke.vvp Components/Memory/*.v Components/Memory/tests/tb_memory_smoke.v
vvp /tmp/tb_memory_smoke.vvp

cd Components/python
python3 -m tests.test_chips
```

Expected pass markers:

- `74HC SMOKE TEST PASSED`
- `MEMORY SMOKE TEST PASSED`
- `Components Python chip tests passed`

## Subfolder Docs

- `74HC/README.md` - full 74HC model list, scan notes, and 74xx source coverage.
- `Memory/README.md` - memory model list and datasheet sources.
- `python/README.md` - Python chip-library coverage and usage.
