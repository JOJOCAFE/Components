# Board Image Reconstruction Contract

Status: planned import route for the KiCad-style Board. It lets a student
start from a schematic image, but an image is evidence to review—not an
electrical authority.

## Two Board directions

```text
Component source -> resolve -> devices placed on schematic + connection guides
schematic image -> detected proposal -> student review -> Component source + Board profile
```

### Component source to Board

For every resolved `device`, the Board places a real library-backed symbol or
package frame in an initial readable layout. Each frame shows definition-owned
physical pin number, logical port name, direction, and source identity.

For every resolved explicit `connect` edge, the Board can show a **dashed
guide** from the exact source pin/net to the exact target pin/net. Unrouted
guides are hidden by default; selecting a device or pin toggles only its
relevant guides. The guide means:
“this electrical connection already exists in Component code; now draw its
schematic path.” It is not an inferred wire and it is not saved as a Board
route.

The student draws bends/segments over that guide. Saving the route updates only
the digest-locked Board profile; the source connection is unchanged. A later
auto-router may suggest or create a visual route for an existing edge, but it
may never add, remove, or retarget a Component connection.

### Schematic image to Component source and Board

The importer stages a reconstruction instead of silently accepting an image:

1. Keep the source image and create a candidate Board overlay.
2. Detect possible symbols/packages, reference labels, value/part text, pin
   labels/numbers, wire segments, net labels, rails, and junctions.
3. Resolve each detected part against the Components library. Show confidence,
   alternatives, and unresolved items; do not invent a part or pin mapping.
4. Present candidate `device`, `net`, `bus`, and `connect` lines next to the
   corresponding highlighted image region.
5. Require the student/teacher to confirm or correct every low-confidence
   part, pin, junction, and connection before Apply.
6. Parse and resolve the complete candidate Component source. Only a valid
   result becomes source authority; the accepted visual positions and route
   segments become a digest-locked Board profile.

An unlabelled line crossing, blurred pin number, unknown package, ambiguous
junction, or bus member mapping remains visibly **Needs review**. The importer
does not guess it, connect it, simulate it, or call it safe.

## Student-facing interaction

- **Read code → see circuit:** open a `.component`; all devices appear and all
  explicit connections receive dashed routing guides.
- **Draw circuit → see code:** choose two real pins, inspect the proposed
  `connect` line, Apply it, then route the new dashed guide.
- **Start from image:** import a schematic screenshot/photo; correct the
  highlighted proposal until each device/pin/wire is explained, then Apply its
  checked Component code.
- **Run and explain:** only after resolution, run declared bounded tests and
  explain values from the resulting model.

## Explicit exclusions

- No direct image-to-simulation claim.
- No automatic acceptance of a wire crossing as a junction.
- No guessed bus expansion, power net, pin number, chip behavior, or timing.
- No breadboard/PCB extraction or build-safety claim.
- No source rewrite or Board-profile overwrite without review and Apply.

## Delivery order

1. Code-to-Board initial placement plus dashed connection-guide renderer.
2. Manual visual route editing and deterministic profile reload.
3. Pin-to-pin checked source edit that creates a new guide.
4. Image import overlay for one tightly bounded schematic style, with manual
   correction and resolver-gated Component-source proposal.
5. Optional visual auto-routing of already-resolved scalar edges only.
6. Consider buses only after the explicit member/ownership contract.
