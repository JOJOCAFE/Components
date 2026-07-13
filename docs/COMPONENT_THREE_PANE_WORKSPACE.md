# Component Three-Pane Workspace

Status: interaction contract for the smallest desktop client. It describes one learner workspace, not a second language, simulator, or shell.

The workspace is designed first for learners around 10–15 years old and for
any adult beginner. It must make a first working action understandable without
a guide or prior electronics course. See
[`COMPONENT_FIRST_SIGHT_DESIGN.md`](COMPONENT_FIRST_SIGHT_DESIGN.md).
The contextual explanation next to selected objects follows
[`COMPONENT_LEARNING_LENS.md`](COMPONENT_LEARNING_LENS.md).

## Default layout: a small workbench

```text
+--------------------------------+--------------------------------+
| 1. Drawing                     | 2. Component text              |
| point, connect, inspect        | readable code, diagnostics     |
+--------------------------------+--------------------------------+
| 3. Terminal: a few live command/result lines             [expand] |
+--------------------------------------------------------------------+
```

1. **Drawing** lets a learner see and directly edit declared parts and wires.
2. **Component text** always shows the readable `component:component` source that learners save, share, and review.
3. **Terminal** sends immediate, visible source-edit or safe runtime requests.

Drawing and Text start left/right. Terminal starts at the bottom and is only a
few lines high: last command, result, and the next useful prompt. It expands
only when the learner asks to inspect a trace or history.

Every region may be resized, collapsed, detached into its own window, or made
full-window/full-screen. Returning to the default workbench must take one
obvious action. These are layout choices around one active Component session,
not separate copies of the circuit.

## Minimal by default

The screen should look like an electronics workbench, not a Microsoft-style
application with large permanent ribbons and rarely-used menus.

- Keep one small always-visible tool row: **select**, **place part**,
  **connect**, **inspect**, **run**, and **undo/redo**. A tool explains itself
  in plain words when pointed at.
- Put uncommon actions—import/export, settings, update channel, plugin
  management, advanced diagnostics—in one compact overflow menu. They are
  searchable; they do not occupy the working screen.
- Prefer a contextual action near the selected part, pin, wire, or error over
  a global dialog. Selecting a wire can offer **Inspect**, **Disconnect**, and
  **Explain**; it must not show unrelated commands.
- Keep the current Component name, validation color/word, save state, and
  Run button visible. Do not show a dashboard, project tree, or inspector
  until the learner opens it.
- Use icons together with short words until the meaning is well learned.
  Color supports a label such as “Needs fixing”; color alone never carries a
  safety or validation meaning.

## Pointer and stylus first

The most common work is direct manipulation. Mouse, trackpad, touch, and
tablet stylus use the same clear gestures:

| Gesture | In Drawing | Safety rule |
| --- | --- | --- |
| Point/tap | select and explain a part, pin, or wire | never changes the circuit |
| Drag a part | move its Board picture | changes placement only |
| Drag from a visible endpoint to another | propose a connection | show the exact Component line and validate before applying |
| Tap `+` near an empty area | choose a compatible declared part/probe | show the generated text before commit |
| Long-press/right-click | short contextual actions | no hidden destructive action |
| Two-finger/pinch/scroll | pan and zoom | presentation only |

A stylus is a precise pointing tool, not a freehand electrical-wire tool.
Freehand marks may later become private study annotations, but never nets or
Device definitions. Keyboard shortcuts and Terminal commands remain available
for faster experienced users; they are not required for the first lesson.

## One source, two ways to edit it

The source text is the durable human-readable authority. Drawing is an equal authoring surface, but it never stores a secret competing circuit.

```text
text edit -> parse -> working AST -> resolve -> Drawing + diagnostics

Drawing edit -> explicit edit intent -> checked AST rewrite -> formatted text
             -> parse/resolve -> refreshed Drawing + diagnostics
```

For example, dragging from `U1.1Y` to `OUT` does not directly alter a canvas net. It asks the service to make the explicit Component edit:

```text
connect U1.1Y to OUT;
```

The service validates endpoint names, direction, signal kind, width, and ownership. On success, Text shows the new line and Drawing refreshes from the resolved topology. On failure, neither source nor drawing receives a hidden wire; the learner sees a diagnostic beside the attempted connection.

Deleting a wire, adding a declared Device, changing a declared label, or placing a Probe follows the same rule. Moving a picture only changes a Board profile placement and never rewrites an electrical connection.

## Synchronization rules

- The session has one increasing `source_revision`.
- A text edit is parsed after a short idle delay or an explicit Apply. While incomplete/invalid, Drawing keeps the last valid view and labels it **“Showing the last valid version.”**
- A Drawing or Terminal source-edit request includes the revision it was made against. A stale request is rejected and refreshed, never applied to different text.
- A successful visual edit returns the exact source patch/new text, AST diagnostics, resolved topology digest, and update reason.
- Formatting preserves learner comments where possible. If a safe rewrite cannot preserve source, the client offers a visible patch for approval; it never rewrites silently.
- Undo/redo stores source patches, so it works the same after typing, drawing, or a Terminal source command.

## The Terminal is not an operating-system shell

The Terminal accepts a small Component command language and shows a structured request/result. It has no arbitrary Python, Rust, shell, file, or network execution.

| Learner says | Meaning | Result |
| --- | --- | --- |
| `connect U1.1Y to OUT` | edit the Component declaration | checked source patch, then re-resolve |
| `disconnect U1.1Y from OUT` | remove one explicit connection | checked source patch, then re-resolve |
| `add probe OUTPUT on OUT` | add a readable observation declaration | checked source patch, then re-resolve |
| `drive IN 1 at 0ns` | send a bounded runtime Operation | trace/result only; source unchanged |
| `pulse CLK 0 1 at 10ns` | send a bounded runtime Operation | trace/result only; source unchanged |
| `run inversion` | run a declared bounded test | trace/result only; source unchanged |
| `watch OUTPUT` | request a declared/read-only observation | trace/result only; source unchanged |

`at` belongs to a runtime command's `(time, delta)` request. It does not make a wire temporary: electrical connections remain explicit source declarations. The Terminal repeats Component name, topology digest, and that the result is a digital-model result—not breadboard timing or safety proof.

## First student flow

1. Open the NOT-gate Component. Drawing shows `U1`, `IN`, and `OUT`; Text shows the same names and connection lines.
2. Select a wire. All three panes explain its source and target.
3. Add a declared Probe by Drawing or `add probe OUTPUT on OUT`. The new readable line appears in Text.
4. Type `drive IN 1 at 0ns`, then `watch OUTPUT`. Terminal shows the trace; Drawing shows a read-only value badge; Text remains unchanged.
5. Make an invalid connection. The attempted wire is only a temporary dashed/red explanation; source remains safe and the diagnostic says what to do.

## First acceptance slice

The first client is ready for learner testing when it can:

1. show the three panes from one `.component` NOT-gate file;
2. sync an accepted text edit into Drawing;
3. add/remove one legal scalar connection from Drawing and show the exact text change;
4. reject an illegal Drawing/Terminal connection without changing source;
5. run `drive` and `watch` through the bounded runtime boundary with a read-only trace; and
6. undo/redo a text-originated and drawing-originated source patch.

No automatic pin choice, wire repair, implicit bus mapping, raw runtime access, or physical-signoff claim is part of this slice.
