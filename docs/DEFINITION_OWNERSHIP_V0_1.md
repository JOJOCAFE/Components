# Definition ownership v0.1

Components has one platform and one resolved runtime contract, but each fact
has one owner.  This avoids treating a validation schema, a chip's behavior,
and its drawing as interchangeable definitions.

| Owner | Answers | Must contain | Must not contain |
|---|---|---|---|
| Schema | What may be written? | field grammar, required fields, structural constraints | chip behavior, timing values, symbols, generated status |
| Device | What is this device and how does it behave? | ports/pins, logic, timing, electrical limits, evidence, model identity | board placement or drawing implementation |
| Resource | How is the device presented or physically mapped? | symbol/footprint/board-view artifact links and layout data | behavior, timing, datasheet truth, test status |
| Component | What machine exists? | device instances and explicit connections | device-library behavior copies or board coordinates |
| Board | How is a machine shown and controlled? | placement, labels, interaction bindings | new device behavior |
| Operation | What is done to a machine? | load, inject, simulate, inspect, validate, export requests | hidden topology or resource defaults |
| Generated | What did the resolver/audit derive? | normalized runtime record, artifacts, audit result | manually edited source facts |

`lib/standard/*/*.schema.json` is the Schema layer.  Compact
`definition/definition.json` is the Device source.  A package may add
`resource/definition.json` for its Resource map.  `generated/resolved.json`
and `generated/status.json` are Generated data only.

[`DEFINITION_MIGRATION_STATUS.md`](DEFINITION_MIGRATION_STATUS.md) is the
authoritative active/pilot inventory. Its gate compares the exact generated
runtime JSON to a fresh resolver result; parsing alone is not enough.

## 74HC00 pilot

`74HC00` is the first lossless split.  Its active compact Device source keeps
the pin truth, NAND behavior, timing, electrical limits, sources, and model
names.  Its existing `symbol/dip.json` remains unchanged and is now linked by
`resource/definition.json`.  The resource map is validated whenever the
compact device is resolved, but it is deliberately not copied into
`db.component.digital`; existing DB, Python, Verilog, and generated-file
contracts therefore remain unchanged.

The DIP artifact repeats pin labels solely for presentation.  The focused test
requires every displayed pin number/name/direction to equal the resolved
Device pin.  Resource cannot override Device truth.

## Migration rule

Do not move a field merely because it is convenient.  Move it only when its
owner is unambiguous and its consumer contract has an equivalence test.  The
current pilot does not yet split KiCad footprints, SVG pinouts, board layouts,
or rich evidence maps because no lossless, active package representation for
those artifacts has been identified.  Those remain in their existing package
locations until a dedicated Resource mapping and consumer proof exist.

## 74HC245, 74HC157, 74HC161, 74HC574, and AT28C256 boundary pilots

`74HC245` is the second Resource pilot. Its existing DIP symbol maps physical
side order, named control/power labels, and A/B bus groups back to the resolved
Device pin map. The Resource contains no direction rule, tri-state rule, or
timing value, so it cannot override transceiver behavior.

`74HC157` and `74HC574` extend that same presentation-only rule to a mux and a
clocked tri-state register. Their Resource files select the existing DIP view;
ownership tests prove every visible pin label and bus group against the
resolved Device. The tests also prove `/G` remains a Device-owned active-low
enable for the 74HC157, while `/OE`, `CLK`, rising-edge behavior, and
tri-state behavior remain Device-owned for the 74HC574. No Resource field can
change those meanings.

`74HC161` maps its existing DIP view only after every displayed label and bus
group is checked against the resolved Device pins. `/CLR`, `CLK`, and `RCO`
remain visible presentation labels, while asynchronous-clear polarity,
rising-edge behavior, terminal-count meaning, and timing remain Device-owned.

`AT28C256` is the active asynchronous-memory Device source. It validates as
`db.component.memory.compact` with `memory.async@0.2`, rather than being
authored as a generic digital part. The compatibility resolver emits the legacy
digital runtime record required by current DB/Python/Verilog consumers; that is
a runtime adapter, not a Device-class claim.
