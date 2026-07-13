# Compact Component Classes v0.2

Components has one authoring platform, not one oversized schema.  Every compact
source uses the common envelope in `compact.component.schema.json`, then picks
one typed payload: `db.component.passive.compact`, `.virtual.compact`,
`.discrete.compact`, or `.support.compact`.  Each resolves to the current
`db.component.definition` shape, so the DB loader, editor, and simulation
services keep one package interface.

Asynchronous memory is deliberately separate from those four non-digital
classes and from generic digital authoring: `db.component.memory.compact` uses
`compact.memory.schema.json` and resolves through the legacy runtime adapter
only while existing consumers still require `db.component.digital` output.

The common envelope owns student-readable identity, physical pin order,
package, simulation service, UI symbol, sources, and known limitations.  The
typed payload owns facts that only that class understands: `passive` values or
ratings, `virtual` UI/event behavior, `discrete` device parameters, or
`support` functional-model scope.  Do not put digital timing/HDL fields here.

Activation is package-by-package: resolve a candidate, compare canonical
package fields with its current source, run package tests and DB audit, then
replace the active source only after review. The digital activation set is
already `74HC00`, `74HC161`, `74HC157`, `74HC245`, and `74HC574`.
`Resistor`, `Capacitor` (passive), and `ClockSource` (virtual) are lossless
active Device sources. They also demonstrate that a typed class is not automatically a
Resource split: their legacy UI labels remain compatibility data until a real
symbol/footprint artifact and its consumer can be mapped without guessing.
Generated resolved JSON is evidence/cache, never another editable source.

Schema validates structure only. The typed source is a Device definition;
symbols, footprints, and board presentation belong in a Resource definition,
while normalized runtime/audit data belongs in `generated/`. See
[`DEFINITION_OWNERSHIP_V0_1.md`](DEFINITION_OWNERSHIP_V0_1.md).

Use the existing single command for every class:

```bash
PYTHONPATH=python python3 tools/resolve_compact_definition.py \
  lib/standard/passive/Capacitor/definition/definition.json
```

It dispatches from `schema`; digital sources retain their package-root model
path handling, while the four non-digital classes resolve directly to
`db.component.definition`.
