# Board Learner Circuit Direction

Status: product direction and delivery contract. The Board is the detailed,
bidirectional visual editor for Component language: it should feel immediate
like Canva/MakeCode and approachable like SketchUp, while retaining the
pin-by-pin circuit clarity of KiCad. It must not become a second circuit
simulator or a rough block-only representation.

The first Board audience is students about **13–15 years old**. Its first
physical-looking surface is a **KiCad-style schematic**, not a breadboard.
Students should see logical symbols/package frames, pin names and numbers,
nets, explicit wires, probes, and diagnostics without first learning the
constraints of jumper placement. Breadboard layout, rails, jumper routing,
current limits, and physical build guidance are a later, separate view after
the schematic/editor route is proven.

## Primary commitment: detailed text ↔ circuit editing

The Board exists because a student can write/read Component language but also
needs to see and edit the *same complete circuit* spatially. Both directions
are first-class and deterministic:

```text
Component source -> parse/resolve -> complete visual circuit
visual part/pin/wire edit -> exact source patch preview -> parse/resolve -> refreshed circuit
```

Every meaningful Board gesture also has a `component:operation` command
equivalent—similar to a Maya/Blender action history—so it can be explained,
replayed, and safely undone. This command layer targets either source, Board
profile, or bounded runtime; it does not record raw pointer movement or become
a second circuit. See `Language/23_Component_Operation_Contract.md`.

The visual circuit must expose every resolved instance, named net, explicit
connection, and definition-owned pin that the current view needs. A student
can select, inspect, and connect an individual pin—not merely connect a vague
“input block” to an “output block.” Logical port names and physical selectors
such as `U1.1Y` and `U1.@2` remain visible and link directly to their source
line. A canvas wire is accepted only after the matching readable `connect`
line resolves; an edit in code immediately redraws the affected pins/wires.

The frozen coordinate and command architecture is
[`BOARD_ARCHITECTURE_FREEZE.md`](BOARD_ARCHITECTURE_FREEZE.md): the visible
surface is a world-coordinate **Viewport**, and Board actions enter a checked
transaction queue rather than mutating the model directly.

Easy interaction is an on-ramp, not a lower-fidelity mode. Blocks, palettes,
context actions, and plain-language explanations help a beginner make the
same real edits quickly. The detailed Board remains available at all times:
zoom/pan, package frame, pin anchors, named wires, selection, route handles,
source highlight, diagnostics, and test/probe values.

When Component code already declares an edge, the Board first draws a dashed
**connection guide** between its exact endpoints. This tells the student where
to draw a clean schematic route; it is not a second electrical connection.
After the student finishes the visual path, only the Board profile changes.
Later automatic routing may create such a visual path for an already-resolved
edge, never invent the edge itself.

## First surface: schematic, not breadboard

The first Board presents a clean schematic workspace:

- KiCad-style symbols/package frames and visible named pin anchors;
- explicit wires and net labels with no implied electrical contact;
- familiar select, place, connect, inspect, pan, zoom, and run/test actions;
- simple student language and one visible next action at a time; and
- a readable Component-code panel always synchronized with the circuit.

It deliberately does **not** imitate a solderless breadboard, auto-arrange
jumpers, draw rails as if they were verified power wiring, estimate physical
wire lengths, or claim a generated layout can be built safely. A later
Breadboard view may consume the same resolved circuit and Board profile only
after its own placement, rail, electrical-safety, and evidence contract.

## One circuit, three synchronized views

```text
Student action
  Blocks / palette / canvas gesture
             |
             v
  checked Component edit intent (shown before Apply)
             |
             v
  readable .component source  <---- the only electrical/topology authority
             |
             v
  parser + resolver -> immutable topology -> Components Runtime
             |                                      |
             +--> Board layout/profile              +--> values, trace, test result
             +--> blocks and KiCad-style drawing    +--> student explanation
```

The three visible views are:

| View | Student feeling | What it may change | What it must never own |
| --- | --- | --- | --- |
| **Blocks** | MakeCode-like assistance: choose a part, a wire, an input, or **Try it** from short labelled actions. | A checked Component edit intent that opens/shows its exact code and pin targets. | Pins, behavior, timing, hidden nets, or a second program. |
| **Code** | Block + code: every accepted block shows the exact `device`, `net`, `bus`, or `connect` line. | The readable Component source through parse/resolve. | A secret AST or canvas-only edit. |
| **Circuit Board** | Detailed KiCad-like circuit: place a real DIP/SVG resource, inspect every definition-owned pin, select/route named edges, and see values/diagnostics in context. | Source-edit proposal for a connection; profile-only placement/route after resolution. | Electrical truth inferred from art, proximity, or a drawn line. |

## Real library circuit rule

Selecting `digital.74HC04` (later any approved library part) must use the
library's resolved identity, definition digest, real pins, direction, timing
metadata, and available model. The Board never copies a chip description into
a block or SVG. A missing model, pin fact, timing value, or resource is shown
as a clear limitation; it is never invented to keep the canvas pretty.

An accepted circuit is therefore created in this order:

1. Pick a library part from a beginner palette.
2. Preview the exact `device U2, digital.74HC04;` source addition.
3. Apply only when the candidate source parses and resolves.
4. Derive the Working Box from resolved unplaced devices, then place the real
   package resource on the Board.
5. Propose each connection as an explicit readable `connect` line; resolve it
   before showing it as an accepted electrical wire.
6. Run only declared, bounded Runtime tests/probes and show the observed value
   with a short explanation linked to the relevant source line and part.

This makes the canvas capable of creating a real library-backed digital model,
not merely a drawing. It remains a digital-model result: it does not prove
breadboard power, current, noise margin, timing margin, PCB routing, or safe
physical construction.

## Simulation and explanation

The first Board simulation surface is intentionally small:

- **Try it** runs one declared bounded test, such as NOT inversion.
- **Watch** shows a named resolved probe/value and the relevant current trace.
- **Explain** answers: what changed, which part caused it, the exact source
  line, and what the digital model does not prove.
- For clocks and later CPU labs, start with a visible single-step/manual clock,
  named state/probe points, and binary expected outcomes before adding fast
  animation or waveform tooling.

Every shared bus stays visually and electrically explicit: show its declared
members and owner/tri-state diagnostic facts. Do not add a decorative bus
stroke, automatic bit fan-out, or a “works” message until the bus-route and
runtime contracts can prove it.

## Relation to existing `block_ui`

`components.block_ui` remains the established interchange for normalized
`Design`/schematic JSON circuits. It is valuable for a later KiCad-like canvas,
but it is not yet a replacement for Component source. Before it can join this
Board route, Bank must freeze a checked Component-to-Design bridge with:

- one library identity/digest on both sides;
- explicit pin/net/bus member mapping;
- deterministic import/export with no guessed wire;
- runtime/test/probe ownership preserved; and
- failure when either side cannot represent a fact.

Until that bridge exists, the learner Board works from resolved Component
topology. Do not silently import a `block_ui` canvas as a Component circuit.

## Schematic image reconstruction

The Board may also begin from a KiCad-style schematic image, but image
recognition is a guided reconstruction workflow. It detects candidate parts,
pins, wires, junctions, and labels; presents proposed Component code plus a
Board overlay; then requires correction and resolver acceptance before the
circuit exists. See `BOARD_IMAGE_RECONSTRUCTION_CONTRACT.md`. An image never
silently becomes simulation truth.

## Delivery order

1. Complete the small Canvas Prototype in
   `BOARD_CANVAS_PROTOTYPE_SCOPE.md`: large canvas, four left tools,
   generated/pending code at upper right, and operation/instruction panel at
   lower right.
2. Complete the human first-sight trial for the current NOT Board.
3. Add a detailed resolved-schematic renderer: all part pins/port names,
   named nets/edges, source-line selection, zoom/pan, and definition-backed
   package resources. No “rough block” is an acceptable fallback where the
   library has pin data.
4. Add code-to-Board placement plus dashed connection guides, then manual
   visual route editing for each existing scalar edge.
5. Add a beginner library palette, checked **Add part** preview, and derived
   Working Box for one approved 74HC part; placing it must reveal all of its
   real pins.
6. Add direct pin-to-pin editing and checked **Connect** assistance alongside
   readable code; prove canvas, source, and resolved topology stay in sync in
   both directions.
7. Add the bounded schematic-image reconstruction overlay and resolver-gated
   Component-code proposal.
8. Add a student simulation panel for declared test, drive, watch, and
   explanation—no raw simulator controls and no physical claim.
9. Freeze and prove the Component-to-Design bridge before adopting the broader
   `block_ui`/schematic editor as another Board client.
10. Only after an explicit bus contract: bus view, member mapping, ownership
   diagnostics, and CPU-lab single-step visualizations.

## First acceptance scene

A learner selects **NOT gate (74HC04)**, sees the real package/pins and the
new code line, places `U1`, connects `IN -> U1.1A -> OUT` through checked
previews, presses **Try inversion**, and can say: “0 becomes 1 because this
NOT gate flips the input.” The Board also says this is a digital-model result,
not breadboard proof.
