# Component Board Prototype

Status: prototype contract. This document is the design checkpoint before more
Board command or UI implementation. It separates electrical authoring from
visual layout so a learner never creates a hidden circuit by drawing. The
architecture freeze in [BOARD_ARCHITECTURE_FREEZE.md](BOARD_ARCHITECTURE_FREEZE.md)
takes precedence over the early local-coordinate experiment described below.

## The big picture

One lesson uses four related but different things:

```text
Library part facts
       ↓
component:component source ──resolve──> immutable electrical topology
       ↓                                      ↓
Working Box (unplaced declarations)     component:board profile
       ↓                                      ↓
pick/place a picture                    positions and visual line paths
       ↑                                      ↑
       └──── component:operation checked intents / action history ─────┘
```

The library owns real pins, directions, timing, and behaviour. The readable
`component:component` source owns devices, nets, buses, and electrical
connections. The Board owns only the picture: positions, rotations, route
points, selection, and optional read-only widgets. `component:operation`
records a meaningful Board/source/runtime intent and result; it is the
replayable command layer, not a second circuit or a raw mouse-event recorder.

## Two commands with deliberately different meanings

### `component:component` — make or change the circuit

These actions are checked source edits. They parse and resolve before they are
saved, and their exact readable source line is shown to the learner.

```component
device U2, digital.74HC04;
net data : digital;
bus address[8] : digital;
connect U1.1Y -> U2.1A;
```

The real electrical connection is the final line. A chip reference alone is
not enough: the source must name the actual logical port or physical selector,
for example `U1.1Y` or `U1.@2`.

### `component:board` — describe only how that circuit looks

Board actions are saved as a digest-locked `components.board-profile@1`
record. They never enter Component source and cannot create a Device, net,
bus, connection, driver, or value.

```text
component:board place U1 at (24, 36);
component:board route edge:U1.1Y->U2.1A via (42, 36) -> (42, 58);
```

The readable command form is a Board-terminal convenience. Its saved
interchange is the profile route `{ edge_id, points }`. The `edge_id` must
refer to a connection already present in resolved topology. If the connection
does not exist, the Board says **“Connect it first”** and saves no route.

## Objects and lifecycle

| Object | Added by | Electrical authority | Board treatment |
| --- | --- | --- | --- |
| Device | library picker, one-part command, or approved BOM | `device` declaration | Working Box item, then placed picture |
| Net | source command | `net` declaration | named connection target/label |
| Bus | source command | `bus` declaration and explicit member mapping | named bundle/label; no implied bit wiring |
| Connection | checked `connect` edit | explicit source edge | may receive a visual Board route |
| Placement | pick/place or drag | none | profile position/rotation |
| Route | route drag, coordinates, or pen | none | profile points for one existing edge |

The Working Box is derived, not a second inventory: it is the valid declared
devices without a placement in the matching Board profile. A BOM may add a
batch of declarations only after one atomic preview; it never auto-places or
auto-wires anything.

## Coordinate route language — superseded prototype detail

The existing local implementation uses Board-local coordinates from `0` to
`100`: origin top-left, `x` right, `y` down. This is a tested prototype format,
not the architecture for the complete Board. New Board work must migrate to
the frozen centered world-coordinate/viewport model before extending this
format. See [BOARD_ARCHITECTURE_FREEZE.md](BOARD_ARCHITECTURE_FREEZE.md).

```text
route U1.1Y to U2.1A via (42, 36) (42, 58) (73, 58)
```

Before accepting it, the Board checks all of the following:

1. Both endpoint names resolve to the named existing edge in the current
   topology.
2. Every point is a finite coordinate in the Board bounds.
3. The profile topology digest is still the current resolved digest.
4. The route contains at least the edge endpoints; supplied points are only
   visual bends.

Moving a route handle edits one bend point. Moving a chip updates its
placement; route endpoints follow their attached resolved edge rather than
becoming new electrical endpoints.

## LOGO-style pen route language

The pen is an alternate way to create the same Board route points. It is not a
freehand electrical-wire tool.

```text
route from U1.1Y to U2.1A
pd
fd 100
rt 90
fd 100
pu
pen to U2.1A
```

Meaning:

- `route from A to B` chooses one existing resolved edge and puts the pen at
  `A`; it fails if `A -> B` is not an existing electrical connection.
- `pd` / `pu` mean pen down / pen up. Only a down movement creates a route
  bend.
- `fd n`, `bk n`, `rt degrees`, and `lt degrees` move/turn the visual pen.
  Heading `0` points right; positive `rt` turns clockwise.
- `pen to B` finishes only at the selected edge's already-resolved endpoint.
  It then saves one `component:board route` command/profile record.
- Escape, `cancel route`, or an invalid endpoint discards the unsaved pen
  preview. No Component source is changed.

During the sequence, the Drawing shows a dashed preview path. After a valid
finish it becomes the normal route; after cancel it disappears.

## Net and bus decisions that must not be guessed

Nets and buses are Component-source concepts first. The prototype must not
infer a net from a nearby line, a bus from parallel lines, or a bus bit from a
label.

- A scalar connection can have one Board route because it has one stable edge
  ID.
- A bus needs an explicit future **bus-route contract**: whether it represents
  one declared bus-to-bus edge, its expanded scalar members, or a labelled
  bundle. Until that contract is frozen, the Board may display a bus label but
  must not save a decorative bus route that pretends to wire bits.
- A net can be positioned/labelled as a Board target, but moving its label does
  not create a driver or attach a pin.

## Required interaction rules

- A click selects and explains; it never changes the circuit.
- Dragging a chip moves only its Board placement.
- Dragging a line or bend moves only its Board route.
- Dragging pin to pin proposes `connect`; it shows a source preview before
  apply.
- A typed `connect` between two pins may show a temporary blue guide, but that
  guide is neither a route nor a source edit until the learner applies the
  checked connection.
- Every Board command has an Undo/Redo entry and a text equivalent.
- Mouse, touch, stylus, keyboard, and screen reader controls expose the same
  placement and route result; colour alone cannot distinguish preview,
  accepted route, and error.

## Persistence and recovery

Component source and Board profile save separately:

```text
source_revision -> readable Component source
topology_digest -> Board profile placements/routes
```

If source changes and resolves to a different topology digest, the Board must
not retarget an old route to a similarly named new object. It keeps source,
reports that the Board picture is stale, and offers to discard/rebuild the
profile. An incomplete pen route is an unsaved preview and is discarded on
reload.

## First prototype acceptance scenarios

1. Add `U2` from the library through a checked `device` declaration; it first
   appears in Working Box.
2. Place `U2` at `(70, 36)`; source remains byte-for-byte unchanged and a
   Board placement is saved.
3. Create and apply `connect U1.1Y -> U2.1A;`; source changes only after
   resolver acceptance.
4. Route that existing edge through three coordinate bends; source remains
   unchanged and the route reloads with the same topology digest.
5. Repeat step 4 with the LOGO pen sequence; the resulting profile points are
   equivalent to a coordinate route.
6. Attempt to route two unconnected pins; the Board refuses and saves nothing.
7. Add a bus; verify that no Board command infers or paints individual bus-bit
   connections until the bus-route contract exists.

## Deliberately postponed

- automatic reference allocation, automatic wiring, route avoidance, or
  electrical repair;
- freehand lines becoming nets;
- board routes for a bus before the explicit bus-route contract;
- PCB tracks, lengths, clearance, manufacturing files, or breadboard safety
  claims; and
- hidden Board state that cannot be shown as a profile command/JSON record.
