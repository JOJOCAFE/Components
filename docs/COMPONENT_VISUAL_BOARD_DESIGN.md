# Component Visual Board Design

Status: design discussion for the later visual Board client.  This document
does not authorize a Board implementation or change Component, Device, or
runtime behavior.

## One picture, two safe views

Students author one readable `component:component` text file. Components
turns that text into machine JSON. The Drawing pane can also author declared
parts and wires, but every accepted drawing action is visibly rewritten into
that same readable text. It never becomes a secret second circuit.

```text
text or explicit Drawing edit
  -> AST JSON -> resolved Component JSON -> Resource bindings -> Board profile
  -> synchronized visual Board
```

The existing `components.block_ui@1` is different: it is the editable
schematic view for the older normalized `Design`/circuit-JSON workflow.  A
future Component Board consumes `components.resolved-component@1` and
`components.board-profile@1`.  Do not silently translate between those two
models or claim that one is the source for the other.

## Inputs and outputs

The Component Board opens only these locked inputs:

| Input | Why it is needed | Authority |
| --- | --- | --- |
| `components.resolved-component@1` | parts, typed endpoints, scalar edges, probes, displays, diagnostics | Component resolver |
| `components.resource-binding@1` | labels and selected text/2D/3D/JSON views | Resource binding service |
| `components.board-profile@1` | positions, line paths, read-only widgets, capture references | Board presentation service |
| runtime/trace result JSON | current values and explained test result | Runtime service |

The client emits four separate JSON envelopes, never a merged hidden circuit:

```json
{"command":"component-language-resolve","source":"...readable Component text..."}
```

```json
{"command":"component-language-board-view","resolved_component":{}}
```

```json
{"schema":"components.board-profile@1","topology_ref":{},"placements":[],"routes":[],"widgets":[]}
```

```json
{"command":"component-language-run","source":"...","test":"inversion"}
```

The first and last envelopes are service requests/results.  The middle two
are stored/interchanged presentation data.  Each presentation envelope must
retain the resolved topology digest, and the client must discard it rather
than retarget it when that digest no longer matches.

## Editing authority

### Student may edit

- Component text: Devices, declared connections, probes, displays, and
  bounded tests, through the text IDE/CLI.
- Drawing: add/remove a declared Device or connection, and add a declared
  Probe/Display, only by a checked source-edit request that shows the
  resulting readable Component patch.
- Board profile: title, zoom, positions, rotations, wire paths, theme, and
  which already-declared probe/display is shown as a read-only widget.
- Resource selection: only a view and learner-facing label that match the
  locked resolved target.

### Student cannot edit directly in the Board

- Device model, pins, port direction, timing, behavior, values, or evidence.
- nets, buses, scalar edges, drivers, hidden connections, power rails, or
  Resource-to-Device compatibility without a checked, explicit source edit.
- runtime state by dragging a wire or clicking a picture.

A control such as a button or clock switch is not a Board mutation.  It must
appear later as an explicit Runtime Operation with an authority check and a
recorded trace.

## First screen for a 15-year-old

Start with a *Read and change my Component* screen, not an empty drawing tool.

1. **Top bar — “What am I looking at?”**: Component title, a green/yellow/red
   validation badge, and a plain sentence such as “This is a NOT gate.”
2. **Left — Parts**: one card per resolved Device, showing its reference,
   student label, selected Resource picture/text, and a link to the real pin
   facts.  A missing Resource says “No picture yet; circuit facts are still
   available.”
3. **Center — Drawing**: placed parts and routes drawn from resolved targets
   and edge IDs. Selecting a wire highlights its source and target. A
   connection gesture opens an explicit “Add this Component line” preview,
   never a guessed/freehand electrical connection.
4. **Right — Understand**: selected part/wire explanation, declared probes,
   display widgets, and visible warnings.  Warnings say what is missing and
   what to do next, not only an error code.
5. **Bottom — Try it**: named declared tests such as `inversion`; Run shows
   digital-model trace/result and repeats “not a breadboard speed or safety
   result.”

The first walkthrough opens the existing NOT-gate fixture. The learner reads
the text, sees `U1`, follows the input-to-output path, makes one checked
change by Drawing or Text, and uses Terminal to run `inversion`. This makes
the visual layer a genuine beginner-friendly authoring surface without hiding
the programming language.

The Board must pass the first-sight learner test in
[`COMPONENT_FIRST_SIGHT_DESIGN.md`](COMPONENT_FIRST_SIGHT_DESIGN.md): a new
10–15-year-old or adult beginner can understand the NOT gate, run it, make one
safe change, and recover from one mistake without opening a reference guide.

## Desktop, updates, and optional plugins

The Board will be a screen inside the lightweight desktop client described in
`docs/COMPONENT_DESKTOP_PLATFORM_PLAN.md`: a Rust/Tauri shell, React/
TypeScript UI, and the existing Python Components service behind versioned
JSON.  This is a client decision, not a new electrical layer.

Auto-update and plugins start as contracts, not as hidden background power:

- updates are signed, compatibility-checked, restart-to-apply, and preserve
  drafts; they never restart an active runtime request;
- the core Board works with no plugin installed;
- a plugin may add a text, 2D, or on-demand 3D Resource view, but only from
  locked JSON snapshots and declared capabilities; and
- a plugin cannot edit topology, change Device truth, or obtain direct Python,
  shell, filesystem, or network authority by default.

The Resource Definition contract remains a prerequisite for a true visual or
3D Resource viewer.  Until then, the Board uses a readable text fallback.

## Minimal acceptance slice

A first three-pane Board client is useful when it can:

1. load a resolved NOT-gate JSON plus compatible Resource bindings;
2. reject stale/mismatched topology and show the resolver diagnostic;
3. draw Device, boundary/probe, and scalar-edge IDs, and turn one explicit
   drawing connection into an accepted/rejected readable source patch without
   inventing pins or wires;
4. save/load only valid Board placements/routes/widgets without changing the
   topology digest;
5. send one bounded Terminal runtime command through the existing runtime
   service and show its read-only trace; and
6. explain its safety boundary in student language.

## Explicit exclusions

- No unchecked drag-to-connect electrical editing: every drawing connection
  must become an explicit validated Component source change.
- No automatic wiring, pin choice, bus expansion, or conflict repair.
- No Board-originated simulation model, timing model, or physical-signoff
  statement.
- No PCB placement, routing, netlist export, BOM, or manufacturing output.
- No mutable probe/display/control widgets; controls require the later
  Runtime Operation contract.
- No requirement that every Resource has a picture or 3D asset.  Text remains
  the safe fallback and hardware truth remains in Components definitions.

## Contract references

- `Language/22_Board_Profile_Contract.md` owns Board-profile interchange.
- `Language/21_Resource_Binding_Contract.md` owns presentation bindings.
- `docs/BLOCK_UI_CONTRACT.md` owns the separate editable normalized-Design
  schematic view.
- `docs/COMPONENT_TEXT_IDE.md` owns the current student text workflow.
- `docs/COMPONENT_DESKTOP_PLATFORM_PLAN.md` owns desktop-shell, updater, and
  plugin boundaries.
- `docs/COMPONENT_THREE_PANE_WORKSPACE.md` owns text/Drawing/Terminal
  synchronization and command authority.
- `docs/COMPONENT_FIRST_SIGHT_DESIGN.md` owns beginner first-sight acceptance.
