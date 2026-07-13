# Compact Digital Definition v0.2

## Decision

Add a human-authored format without changing the live `db.component.digital`
runtime contract.  A compact source is resolved into the same canonical object
that `python/chiplib/db.py` validates and existing tools consume.  Existing
`definition/definition.json` remains authoritative for every package. Five
digital packages have passed their individual equivalence gates and now use a
compact source there: `74HC00`, `74HC161`, `74HC157`, `74HC245`, and `74HC574`.
Other packages retain their existing canonical source until they pass the same
gate.

```text
definition/compact.json --resolver--> canonical in-memory db.component.digital
                                      + generated/resolved.json (optional cache)
```

The source schema is
[`lib/standard/compact.digital.schema.json`](../lib/standard/compact.digital.schema.json):
`schema: "db.component.digital.compact"`, `version: "0.2"`.
This is additive; it does not replace [`digital.schema.json`](../lib/standard/digital.schema.json).

## What a student or maintainer edits

Compact files keep only human decisions: identity, package kind, a physical
pin map, logic intent, datasheet source values, model-name overrides, required
proof categories, variants, and known limitations. Pins are keyed by their
physical number so a PDIP can be checked in order without following a second
bus map:

```json
"pins": {
  "1": ["/CLR", "in", {"active": "low"}],
  "2": ["CLK", "in", {"edge": "rising"}],
  "8": ["GND", "power", {"rail": "GND"}],
  "14": ["QA", "out", {"bus": "Q", "bit": 0}],
  "16": ["VCC", "power", {"rail": "VCC"}]
}
```

The first two values are always name and direction. The optional third value
is named metadata; compact syntax never uses unnamed third-or-later fields.
The schema accepts both a 74HC00-style combinational definition and a
74HC161-style clocked/counter definition.

### Clocked timing

For a clocked part, `timing.clocked` is the human source for every named
datasheet row. It requires conditions, the five named propagation rows
(`clear_to_q`, `clock_to_q`, `clock_to_rco`, `ent_to_rco`, and
`transition_any`), setup classes, hold-after-clock, minimum pulse widths,
maximum clock frequency, and source evidence. Values are keyed by readable
voltage strings such as `"4.5V"` and expressed as `"25ns"`; the resolver
normalizes them to the existing `vcc_4_5_v` canonical keys. No generic delay
may replace an omitted row.

`74HC161/definition/definition.json` is the lossless clocked compact source.
Its focused gate requires the resolved `timing` object and the
`definition_layers.timing` object to equal its generated canonical evidence
exactly.

### Multi-path and clocked tri-state timing

`timing.multipath` is for push-pull logic where a data input, selector,
strobe, and output transition each have different datasheet values.  The
active `74HC157` source names those four rows explicitly and retains every
voltage and temperature column in the definition layer; its existing public
timing-parameter view is resolved from the published 4.5 V column.

`timing.clocked_tri_state` is for an edge-register whose stored state and
output-bus release are separate facts.  The active `74HC574` source names
CLK-to-Q, `/OE` enable-to-Q, `/OE` disable-to-Z, output transition, setup,
hold, pulse width, and maximum clock frequency.  It does not treat `/OE` as
a generic combinational delay or discard the high-Z rows.

### Asynchronous memory timing

`timing.asynchronous_memory` is a separate named grammar for EEPROM/SRAM
style devices.  It keeps address-, `/CE`-, and `/OE`-to-data timing separate
from `/CE`/`/OE`-to-float timing, and keeps `/WE` pulse, data setup, address
hold, speed-grade rows, post-write busy behavior, and unsupported-programming
scope explicit. The active `AT28C256` source is authored as the separate
`db.component.memory.compact` Device class with `memory.async@0.2`, not as a
generic digital Device. Its resolver adapts only at the legacy runtime boundary
and proves that it recreates the read, high-Z, write, electrical, evidence, and
required-vector contracts exactly.

## Profiles and defaults

`profile` is mandatory and versioned (for example `74hc.digital@0.2`). A
profile may supply declared defaults such as output drive, units, targets, and
package conventions. The resolver records the exact profile ID and resolved
defaults. A compact source states only an exception to those defaults.

Profiles are data, not guesswork. The resolver **must fail** when the named
profile, a required default, or an override is unavailable. It must not infer
family, package pins, model paths, pin direction, timing, or bus membership
from a part name, folder name, pin name, or a same-named signal. Package pin
count is derived only from the explicit `pins` object.

## Evidence, status, and generated files

`sources` keeps the source label, location, and physical-package evidence in
the compact file because this is part of the edited chip truth. Page/table
provenance may live in `evidence/evidence.json`; it must point back to a source
listed in `sources`.

`known_limitations` is also authored truth: use it for an unresolved property
or deliberate scope boundary. Do not author pass/fail status duplicated from
files or test results. The audit may write derived availability and latest-test
state to `generated/status.json`.

`generated/resolved.json`, `generated/status.json`, and generated artifact
manifests are machine output. They must identify their compact input digest,
resolver version, profile ID, and generation time, and must never be edited by
hand. They are caches/evidence, not a second editable source of truth.

## Resolver output contract and migration gate

The resolver emits the current canonical `db.component.digital` shape: root
identity, `metadata`, `package`, array-form canonical `pins`, `logic`,
runtime `timing`, `generation`, `verification`, `datasheet`, required status
shape, and any canonical definition layers required by the existing DB loader.
It expands compact direction names (`in`, `out`, `io`) to the existing canonical
names and carries active-low, edge, rail, bus, bit, drive, and enable metadata
without loss.

Before a compact package becomes active, Fern's equivalence gate compares its
resolved canonical object with the existing definition at every field used by
the DB loader, Python model, Verilog export, symbol generation, and required
test contracts. Timing has one authored source; any normalized timing paths are
resolver output. A mismatch blocks migration rather than choosing a value.

The first activation set is 74HC00, 74HC161, 74HC157, 74HC245, and 74HC574.
The package loader resolves those compact sources to the same canonical input
used by existing tools. Further migration remains package-by-package.

## Ownership boundary

Compact source is a Device definition, not a general container. Schema files
define only structure; Device sources own ports, behavior, timing, electrical
limits, and evidence; Resource definitions own symbols, footprints, and board
presentation; generated files own normalized runtime/audit output. See
[`DEFINITION_OWNERSHIP_V0_1.md`](DEFINITION_OWNERSHIP_V0_1.md) for the
enforced 74HC00 Device + Resource pilot.

## Related current contracts

- `lib/standard/digital.schema.json` defines the live digital package shape.
- `python/chiplib/db.py` validates and builds the current canonical view.
- `lib/standard/README.md` defines the current package layout and validation
  commands.
