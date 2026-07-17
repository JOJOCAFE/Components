# Component Board Workflow

Status: workflow specification before the next Board implementation slice.
This document describes how a learner aged about 13–15 uses the first,
KiCad-style schematic Board. It does not create a second circuit model,
authorize breadboard/PCB work, or change the Component language.

## Goal

A learner should be able to open one small Component, understand its parts,
connect named pins by mouse or command, see the exact readable source change,
run one declared test, and recover from one mistake.

The first complete route is the NOT-gate fixture:

```text
IN -> U1 (74HC04) -> OUT
```

The Board is a KiCad-style **schematic view and checked authoring surface**. It may show
chip frames, pins, anchors, wires, placement, and selection. It never becomes
the authority for a pin, net, timing value, logic function, or connection.

## One authority, three surfaces

```text
Learner action
      |
      +-- Drawing mouse/stylus gesture
      +-- Readable Component text
      +-- Small Terminal command
               |
               v
  checked source-edit intent or bounded runtime request
               |
               v
 Component parser + resolver / runtime service
               |
               +-- accepted source patch and refreshed topology
               +-- or visible diagnostic with no topology change
```

One readable `.component` source is the electrical/topology authority.
Resolved Component JSON provides immutable facts to the Board. SVG chip frames
and Board placement are presentation resources only.

## Before the learner starts

The Board opens a resolved, valid Component. The default screen shows:

- a short title and sentence: “This is a NOT gate. It changes 0 into 1, and 1
  into 0.”;
- Drawing on the left, readable Component text on the upper right, and a small
  Terminal on the lower right;
- `IN`, `U1`, and `OUT` in the Drawing;
- one prominent safe action: **Try inversion**; and
- a visible statement near the result: “Digital-model result; not proof that a
  breadboard is wired safely.”

If text is invalid while being edited, Drawing keeps the last valid resolved
view and says so. It must never guess a replacement wire or pin.

## Working Box — stage parts before placing them

The **Working Box** is a small, source-backed staging list. It answers “which
declared parts have I brought into this Component but not yet placed on this
Board?” It is derived from valid Component declarations minus saved
Board-profile placements; it is not a second library, netlist, or hidden
electrical model.

### Add one part

The learner browses a library and may use a friendly Board or Terminal intent,
for example:

```text
add part digital.74HC04 as U1
```

That is an authoring command, not Component source syntax. Before anything is
saved, the Board must preview the exact source declaration it will create:

```text
device U1, digital.74HC04;
```

The preview checks the library identity, instance name, required parameters,
and resolver acceptance. **Apply checked part** writes the declaration through
the same revision-checked source path used for connections. The refreshed
resolved instance then appears in Working Box. Duplicate references, unknown
parts, or a rejected declaration leave source, topology, and the Box unchanged.

### Add parts from a BOM sheet

A BOM sheet may be pasted, selected, or loaded as a small text/CSV table with
at least a library part and quantity; it may also provide desired references
such as `U1` and `U2`. The Board first presents a batch preview listing every
generated `device` declaration and any proposed references.

The learner confirms the whole batch once. The service must parse and resolve
the candidate source as one atomic revision-checked edit: either every
declaration is added and every new instance appears in Working Box, or none is
added. A BOM never creates wires, chooses pins, connects power, places parts,
or silently repairs duplicate references. If a part requires information that
the current language cannot declare safely, the preview asks for that
information instead of adding a partial part.

### Pick up and place

Each unplaced item in Working Box has its reference and part name, for example
`U1 — 74HC04`. The learner picks one item, moves its presentation frame onto
the workspace, and clicks to place it. This changes only the Board-profile
placement after the resolved instance is known; it cannot create a device,
change a pin, or alter topology. Placing is intentionally one part at a time,
even after a BOM batch, so the learner can see what each part is.

## Workflow A — inspect a placed chip and its pins

1. The learner selects `U1`.
2. The Learning Lens explains what the part does here and shows its real name:
   `74HC04`.
3. The Board may show the shared DIP-frame SVG resource.
4. Visible pin anchors come from resolved definition facts: physical pin
   number, port name, direction, and DIP side/order. They never come from SVG
   coordinates, artwork labels, or a duplicate Board netlist.
5. Selecting an anchor highlights the matching source endpoint, for example
   logical pin `U1.1Y` or physical pin selector `U1.@2`, and explains whether
   it is an input, output, power, or other declared port.

The learner may inspect a frame even when no artwork exists. The fallback is
the resolved pin list and readable source, not an invented symbol.

## Workflow B — connect placed pins with the mouse or stylus

This is the standard KiCad-style connection flow. It deliberately has a
preview step so a drag cannot silently change a circuit.

1. The learner chooses **Connect** and presses a visible source anchor, for
   example `U1.1Y`.
2. The Board draws a temporary dashed route to the current pointer. It is not
   a net and is not saved.
3. The learner releases on a compatible visible endpoint, such as `OUT` or a
   declared input pin. The learner may choose a pin by its logical port name
   or its physical number; the Board makes that selection explicit. Keyboard
   users Tab to the same visible pin controls, then press Enter or Space once
   to choose the first pin and again to choose the second.
4. The Board builds the explicit intent:

   ```text
   connect U1.1Y -> OUT;
   ```

5. The Board sends a **pure preview** with the current source revision. The
   service parses and resolves the candidate, returning either a patch and
   topology digest or a diagnostic. Source and current topology remain
   unchanged during preview.
6. For a valid preview, the Board shows the exact line and offers **Apply
   checked connection** and **Cancel**.
7. **Apply** sends the same intent through the revision-checked source-edit
   path. On success, the returned readable source replaces Text and the Board
   redraws only from the refreshed resolved topology.
8. **Cancel**, Escape, `cancel route`, or a pointer release on empty space
   removes the dashed preview and changes nothing.

The Board may choose the natural display direction, such as output to input,
but it must send the exact resolved endpoint names and let the resolver make
the real decision.

## Workflow C — type the same connection by pin name or number

The Terminal and mouse gesture are equivalent authoring routes. A learner or
advanced user can enter:

```text
connect U1.1Y to OUT
```

The equivalent physical-pin selector remains readable and uses the Component
language `@` form, not an SVG coordinate or a Board-only identity:

```text
connect U1.@2 to OUT
```

Two placed chips can be connected the same way:

```text
connect U1.1Y to U2.1A
connect U1.@2 to U2.@1
```

When both endpoints are placed chip pins, this command first shows a temporary
blue guide from the first resolved pin anchor to the second. It does not edit
source. The Board immediately follows that guide with the same pure
preview-and-explicit-Apply route used by a pointer gesture; the guide remains
only as a visual explanation and disappears on Apply, Cancel, or Escape.

For all other commands, the Terminal shows the same readable patch, preview,
apply/cancel choice, and diagnostic wording as the Drawing route. It must not
bypass source revision checking or call a separate canvas/netlist service.

## Workflow D — recover from a mistake

For an invalid endpoint, incompatible direction, width error, output-ownership
conflict, or stale source revision:

1. The temporary route turns red/dashed and is labelled **Not connected**.
2. The Board says what happened, why it matters, and one next action. Example:
   “This output already has a driver. Choose an input or remove the old wire.”
3. Text, source revision, saved Board profile, and resolved topology stay
   unchanged.
4. The learner can dismiss the attempt, inspect either endpoint, or make a new
   connection.

Raw error codes may appear under **See details**, but never as the only
beginner-facing explanation.

## Workflow E — run and understand the result

1. The learner presses **Try inversion** or enters `run inversion`.
2. The Board sends only the declared bounded test to the runtime service.
3. The result names the test, observed values, and a short reason: “IN was 0;
   OUT became 1 because this part inverts the input.”
4. The result also states the boundary: it is a digital-model result, not
   breadboard wiring, electrical safety, timing-margin, or speed signoff.

Runtime actions return trace/result data; they never rewrite Component source.

## Placement and routes

Dragging a placed chip writes a visual-only Board command such as
`component:board place U1 at (52.0%, 36.0%);`. Dragging an existing line writes
`component:board route edge:U1.1Y->U2.1A via (61.0%, 48.0%);`. These commands
are saved as a digest-locked `components.board-profile@1` presentation record;
they do not enter Component source or create/alter an electrical connection.

Moving a placed chip is visual only. It changes a Board-profile placement,
not the Component source or topology. A visible wire route is likewise a
Board profile route around an already resolved connection.

The first Board implementation may keep placement fixed. Before drag-to-move
is enabled, the Board-profile save/load contract must prove that its topology
digest matches the current resolved Component.

## Delivery order

| Step | Learner outcome | Required evidence |
| --- | --- | --- |
| 1. Add a part | Preview and add one library part to Working Box. | Exact `device` declaration, resolver preview, revision-checked apply. |
| 2. Add from BOM | Review and atomically add a small batch. | Whole-batch preview; no partial declarations or automatic wiring. |
| 3. Pick and place | Put one staged part on the workspace. | Placement derives from a resolved instance and only updates the Board profile. |
| 4. Inspect | Identify `IN`, `U1`, `OUT`, and a real 74HC pin. | Definition-derived frame/anchor contract and text highlight. |
| 5. Preview connection | See the exact named or numbered-pin `connect` line without changing the circuit. | Preview preserves source/revision/topology. |
| 6. Apply or cancel | Make one legal connection or safely abandon it. | Revision-checked patch; redraw from resolver only. |
| 7. Recover | Understand and dismiss an invalid attempt. | Rejected preview leaves all electrical state unchanged. |
| 8. Run | See one understandable digital-model result. | Declared bounded test plus clear physical boundary. |
| 9. Learner trial | Complete the route without a guide. | One 13–15-year-old and one adult beginner complete the first-sight test. |

## Explicit exclusions

- No automatic pin choice, wire repair, bus expansion, or conflict repair.
- No automatic reference assignment without showing it in a part/BOM preview;
  no partial BOM import.
- No automatic placement, power wiring, or electrical connection from a BOM.
- No direct Board mutation of Device truth, timing, behavior, power, drivers,
  or runtime state.
- No PCB placement, routing, netlist export, manufacturing, or BOM purchasing
  claim.
- No plugin, updater, timeline, waveform, 3D, or multiwindow prerequisite for
  the first NOT-gate route.

## Related contracts

- `COMPONENT_THREE_PANE_WORKSPACE.md` — synchronized Drawing, Text, and
  Terminal authority.
- `COMPONENT_LEARNING_LENS.md` — learner explanation beside selected objects.
- `COMPONENT_FIRST_SIGHT_DESIGN.md` — five-minute learner acceptance test.
- `COMPONENT_VISUAL_BOARD_DESIGN.md` — Board/resource/profile boundaries.
- `Language/21_Resource_Binding_Contract.md` — presentation resource binding.
- `Language/22_Board_Profile_Contract.md` — future placement and route
  interchange.
