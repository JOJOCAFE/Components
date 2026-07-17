# Components Board — first local workbench

This is the smallest real Board client: Drawing is on the left, readable
Component text is upper-right, and a short bounded Terminal is lower-right.
It has no npm dependencies, no plugin host, no network requirement after
startup, and no hidden canvas circuit model.

Run from the Components repository root:

```sh
PYTHONPATH=python python3 -B -m chiplib.api --http --host 127.0.0.1 --port 8765
```

Open <http://127.0.0.1:8765/>. The Python API serves this folder, so the Board
and Component service share one local origin.

Read [`docs/COMPONENT_BOARD_WORKFLOW.md`](docs/COMPONENT_BOARD_WORKFLOW.md)
before extending Board behavior. It defines the learner workflow and preserves
the one-source, checked-preview, explicit-apply boundary.

First slice included:

- the real NOT-gate Component fixture, parser, resolver, Board JSON view, and
  declared `inversion` runtime test;
- local draft autosave/recovery through browser local storage;
- selection-to-readable-source highlighting and a Learning Lens explanation;
- definition-backed 74HC no-pin DIP-frame SVG Board resources from
  `board/assets/74hc-chip-frames-no-pins/`; and
- visible definition-owned connection dots over a selected supported 74HC
  frame (the artwork replaces lead stubs with compact dots while retaining
  readable pin labels).
  A pointer gesture first calls the pure `component-language-edit-preview`
  request, which parse/resolves the proposed patch and returns its digest while
  retaining the exact current source. Only after that preview can the learner
  explicitly submit the existing revision-checked source-patch request; and
- bounded Terminal commands: `run`, `drive`, `watch`, `connect`,
  `disconnect`, and `help`; and
- checked Board/Terminal connect/disconnect source patches. An invalid edit
  leaves text and resolved topology unchanged.

This is intentionally a dependency-free browser proof. A later Tauri wrapper
must consume this same local JSON/source-edit boundary; it must not introduce
a second circuit model.

Board placement and scalar-edge routing use `components.board-profile@1` in
browser-local storage. Coordinates are stable Board units from `0` to `100`,
not screen pixels: invalid or out-of-bounds route points are rejected. A
saved picture whose topology digest no longer matches is never reused or
retargeted; the learner must explicitly run `discard board profile` before
starting an empty replacement picture. `fd` and `bk` pen distances use the
same Board units, so a pen path and matching coordinate path save equivalent
route points. Bus routes remain unavailable pending their own contract.

Interaction proof currently covers pointer and keyboard pin selection, exact
source-edit preview before Apply, Cancel/Escape/`cancel route` recovery, and
typed pin-to-pin commands using that same preview. The machine checks are in
`board/interaction-contract.test.mjs`; the final first-sight acceptance trial
still requires a real 10–15-year-old learner and adult beginner.

Unrouted connections are quiet by default. A normal click on a chip or net is
reserved for its definition/inspection. Choose **Guides** in the left rail,
then left-click a device, net, or precise connection dot to toggle its related
routing guides. The choices accumulate: click three nodes and their guide
groups stay visible together, which lets a learner arrange related paths as a
future bus. While Guides is active, node clicks only toggle guides; they do
not select, inspect, or create a connection. Click a node again to hide only
its guides, even when the same edge is also part of a selected device or net
group. A saved Board route remains
visible because it is the learner's drawing, not a temporary guide.

The current canvas keeps visual artifacts vector-first: reviewed chip frames
are SVG resources, connection guides/routes are SVG paths, and Board labels
are SVG text. Choose **Label**, click the canvas, enter one or more lines, and
set a size from `1.5` to `8` Board units. Labels and routes save only in the
digest-locked Board profile; they do not alter Component source or pin truth.

The SVG chip frames are deliberately presentation-only. The Board serves the
no-pin frames through `resources/74hc-chip-frames-no-pins/` when a matching
local frame exists. The older functional-pinout frames remain review assets,
not Board artwork. The resolved Component and package definition remain the
only source for ports, logic, timing, and wiring.

Every visible Board object is connectable at a border node: a 74HC frame uses
its definition-aligned DIP dots; a net such as `Clock` or `OUT`, and a device
without a chip SVG, uses a bordered frame with resolved endpoint dots. These
are the targets for routes and for the **Guides** on/off switch; none creates
an electrical connection by itself.
