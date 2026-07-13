# RV8GR compact Device migration plan

This is the narrow migration plan for the RV8GR-ready definition set.  It is
not a claim that every standard-library package is compact, and it does not
replace legacy sources until all device facts resolve identically.

## Fixed readiness set

The set has 18 definition/options:

- the 16 physical board-used types: `74HC00`, `74HC04`, `74HC21`, `74HC32`,
  `74HC74`, `74HC86`, `74HC157`, `74HC161`, `74HC164`, `74HC245`, `74HC283`,
  `74HC541`, `74HC574`, `74HC688`, `62256`, and `AT28C256`;
- the `AS6C62256` and `CY7C199` SRAM alternatives used by the memory contract.

Virtual helpers are deliberately outside this count: they are test
infrastructure, not physical board packages.

## Current split

| State | Parts |
|---|---|
| Already compact and generated | `74HC00`, `74HC04`, `74HC157`, `74HC161`, `74HC245`, `74HC574`, `AT28C256` |
| Legacy source, lossless bridge proven; source conversion still pending | `74HC21`, `74HC32`, `74HC74`, `74HC86`, `74HC164`, `74HC283`, `74HC541`, `74HC688`, `62256`, `AS6C62256`, `CY7C199` |

## Safe batch order

1. Add a **generic legacy timing payload** to the compact resolver, with an
   equivalence test that proves the resolved `timing`, `timing_parameters`,
   `definition_layers.timing`, pins, logic, electrical facts, model targets,
   evidence, variants, and verification vectors equal the legacy canonical
   record.  It must preserve, not reinterpret, every existing timing path.
2. Convert the four combinational gates together: `74HC21`, `74HC32`,
   `74HC86`, then `74HC283`.  Each retains its package-local Python, Verilog,
   netlist, tests, symbol, and generated artifacts.
3. Convert the clocked pair: `74HC74`, `74HC164`, proving active edge and
   hold/no-edge behavior in both Python and Verilog.
4. Convert `74HC541` and `74HC688`, proving output enable/high-Z and the
   comparator active-low semantics respectively.
5. Convert the SRAM family together: `62256`, `AS6C62256`, and `CY7C199`.
   Preserve each selected timing variant, read/write control window, and
   bus-float behavior; do not copy `AT28C256` timing into SRAM records.  The
   dedicated memory bridge and
   `tools/check_rv8gr_legacy_memory_compact_equivalence.py` already prove the
   three current canonical records losslessly; the remaining work is reviewed
   compact source authoring plus normal package regressions.

## Required promotion gate per part

1. Human compact `definition/definition.json` validates.
2. `generated/resolved.json` is freshly regenerated and byte-compares to the
   legacy canonical Device truth for all non-derived fields.
3. Existing Python model, Verilog model, netlist, and five package vector
   files remain present; focused Python/Verilog tests pass.
4. An optional Resource map validates when present, but never supplies pins,
   timing, logic, evidence, or status.
5. `PYTHONPATH=python python3 tools/check_definition_migration.py` remains
   green, followed by `tools/audit_rv8gr_definition_migration.py`.

## Explicit blockers

The generic digital and dedicated memory compatibility adapters now preserve
the complete canonical timing and definition-layer payloads verbatim.  They
prove byte-equivalence for all eleven legacy RV8GR-ready records before any
source rewrite.  Batch conversion remains deliberately pending—not blocked—so
that each human compact source can be reviewed for clarity while the gate
continues to prevent loss of timing parameters, source conditions, or legacy
compatibility fields.
