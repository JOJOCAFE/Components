# 23 — `component:operation` Contract

Status: planned contract. `component:operation` is the command/replay layer
between a student-facing Board gesture/shortcut and the three authoritative
systems: readable Component source, Board profile, and bounded runtime.

It gives the Board a Maya/Blender-like property: every **meaningful** action
has a readable command equivalent, can be shown in an action history, and can
be replayed or undone where its target supports it. It does not record every
mouse-move event or individual text keystroke; those are transient UI input
that is coalesced into one semantic operation such as `place`, `route`,
`apply-source-patch`, or `run-test`.

## The three Component layers

```text
component:component  -> what the circuit is
component:board      -> how the resolved circuit is displayed
component:operation  -> what the student/Board asks to happen
```

| Layer | Owns | Examples | Must not own |
| --- | --- | --- | --- |
| `component:component` | Electrical topology and its readable source. | `device`, `net`, `bus`, `connect`, `probe`, declared test. | Canvas coordinates, route bends, raw pointer input. |
| `component:board` | Digest-locked presentation of a resolved circuit. | placement, rotation, visual route points, view/profile metadata. | Device facts, hidden connections, simulation state. |
| `component:operation` | A checked intent, action result, and optional replay/undo record. | place, route, connect preview/apply, inspect, run test, drive, step, undo/redo. | A second topology, guessed pins/wires, unrestricted host scripting. |

## Operation shape

The interchange record is versioned JSON, not arbitrary Python:

```json
{
  "format": "components.component-operation@1",
  "id": "op-0042",
  "kind": "board.route",
  "target": "board-profile",
  "source_revision": "sha256:...",
  "topology_digest": "sha256:...",
  "intent": {
    "edge_id": "edge:U1.1Y->U2.1A",
    "points": [{"x": 42, "y": 36}, {"x": 42, "y": 58}]
  },
  "result": "pending"
}
```

The service validates the target authority before it applies an operation. A
completed record includes its canonical result, diagnostics, and inverse when
an inverse is safe. A rejected operation leaves its target unchanged.

## Transaction queue

The upper-right Board panel is a transaction queue containing one or more
pending semantic operations. It is a staging area, not a second model and not
a place where a canvas mutation can bypass validation. A queue may hold
dependent operations, such as a source `connect` followed by a Board route for
the edge that connect creates.

Each operation retains exactly one authority target. **Apply all** processes
source operations first against their expected source revision, resolves the
new topology, then applies only Board operations whose expected digest and
referenced IDs exist. A rejection leaves the target unchanged and blocks its
dependents. This gives Board, CLI, API, macros, AI assistance, undo/redo, and
headless execution the same reviewable path.

## Operation families

### Source operations — circuit changes

`component.connect.preview`, `component.connect.apply`, `component.disconnect`,
`component.add-device`, `component.add-net`, and `component.add-bus` create
candidate readable source patches. They must carry the expected source
revision, parse/resolve before Apply, and return the exact changed lines. A
Board pin drag is only a front end for one of these operations.

### Board operations — schematic actions

`board.place`, `board.move`, `board.route`, `board.route.cancel`,
`board.select`, `board.pan`, `board.zoom`, `board.inspect`, and `board.undo` /
`board.redo` act on the Board profile or local view state. A route operation
must name an already-resolved scalar edge and the matching topology digest.
`board.pan`, `board.zoom`, and selection may remain session-local by default;
placement and route results are profile-persisted only after Apply.

When Component code creates or imports an electrical edge, the Board may emit
`board.show-connection-guide` for its dashed guide. It is a visual operation,
not a route and not an electrical connection.
Its temporary in-viewport label shows the exact source proposal, for example
`connect U1.1Y → OUT`.

### Runtime operations — bounded simulation

`runtime.run-test`, `runtime.drive`, `runtime.pulse`, `runtime.step`,
`runtime.wait`, and `runtime.probe` invoke only declared/allowed runtime
capabilities. They return trace/result records and never rewrite Component
source or Board profile unless a separate checked operation explicitly does so.

### Import operations — guided reconstruction

`import.image.detect`, `import.image.choose-part`, `import.image.map-pin`,
`import.image.confirm-junction`, and `import.image.apply-source-proposal`
support schematic-image reconstruction. Detection results are candidates;
only the final source-apply operation can create circuit topology.

## Gesture and shortcut mapping

The UI should show a command equivalent for each meaningful gesture:

| Student action | Operation shown in history | Effect |
| --- | --- | --- |
| Drag a part, then release | `board.place U2 at (70,36)` | Board profile only. |
| Drag a route bend, then release | `board.route edge:... via (...)` | Board profile only. |
| Drag pin A to pin B | `component.connect.preview A -> B`, then Apply/Cancel | Source changes only after resolver acceptance. |
| Press **Try inversion** | `runtime.run-test inversion` | Bounded runtime result/trace. |
| Press Escape during guide/route | `board.route.cancel` | Discards transient preview. |
| Undo | `board.undo` or `component.undo` | Applies the recorded safe inverse. |

Typing in the readable code editor is normal text editing. It becomes an
operation only on explicit Apply or after the existing debounced parse/resolve
checkpoint; this avoids recording one operation per character while retaining
replayable source revisions.

## Non-negotiable boundaries

- An operation must declare exactly one target authority and cannot silently
  update source, profile, and runtime together.
- The Board creates operations only; it never directly edits a resolved
  Component, source text, or saved Board profile.
- Operations must be revision/digest checked and fail rather than retarget.
- The command log is not permission to execute arbitrary Python, shell, or
  plugin code.
- Raw pointer coordinates, hover, animation frames, and individual keystrokes
  are not durable source; record only the final meaningful intent/result.
- Image detection, routing suggestions, and AI assistance always create
  reviewable operations, never hidden circuit edits.
