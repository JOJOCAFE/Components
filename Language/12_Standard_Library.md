# 12 — Standard Library

Status: Language Specification v1.0 — interface contract.

The Standard Library supplies named, versioned Device definitions and optional
Resource definitions. It is not part of the parser and does not change the
core grammar.

## Required interface

Each published Device exposes:

- stable library ID and version;
- typed ports/pins, direction, width, active polarity, and physical mapping
  where applicable;
- Device-owned behavior provider identity or an explicit non-simulatable
  declaration;
- Device-owned timing/electrical metadata and evidence references; and
- compatibility information needed to resolve existing Components packages.

Initial interface families include `74HC00`, `74HC04`, `74HC08`, `74HC161`,
`74HC245`, `74HC574`, `AT28C256`, `62256`, `Resistor`, `LED`, `BUTTON`,
`CLOCK`, and `Probe`. Listing a Device here does not assert that every model,
physical package, or timing corner is complete; package status remains visible
in its generated audit record.

Resources expose a Device link plus view/footprint/symbol mapping. They may
repeat labels for presentation only and must validate against the resolved
Device. They cannot define logic, timing, or simulation behavior.

Schemas define allowed shape; the Device Library defines meaning and behavior;
the Resource Library defines presentation/physical mapping. See
[`../docs/DEFINITION_OWNERSHIP_V0_1.md`](../docs/DEFINITION_OWNERSHIP_V0_1.md).
