# Current Board Team Sprint — Viewport Properties

Status: active, scoped Board sprint (2026-07-18).

## Sprint outcome

A learner can use the detailed Board like a schematic tool: right-click never
opens the browser menu inside the viewport; it opens Board-owned properties.
They can add one UTF-8 label anywhere, edit its text directly on the label,
select and drag it, resize it from its corner handle, and use a compact
right-click popup for size, one colour, bold, italic, and underline. These are
`component:board` presentation facts only.

This sprint does **not** promote Board v2, reopen Guides, add a font-family
chooser, permit mixed text styling/colours, add bus routes, or change Component
source/topology.

## Team route

| Owner | Sprint task | Done when |
| --- | --- | --- |
| Pim | Keep this scope separate from the Guides-only release candidate and the active Board v2 plan; record the final evidence. | No production claim is made for Board v2 and no unrelated feature is added. |
| Bank | Review the label `style` profile shape and property ownership boundary. | One label has exactly one six-digit hex colour and complete whole-label style; no electrical field enters the profile. |
| Bam | Maintain the direct-edit/right-click interaction and repair any browser-observed defect. | Device, net, pin, connection, route bend, label, and empty viewport all suppress the browser menu; labels save/reload, move, resize, and preserve the rest of the viewport after an optional UI error. |
| Fern | Independently run contract checks and observe negative ownership behavior. | Changing a label cannot alter Component source, resolved topology, route ownership, or Guides persistence. |
| Noon | Run/read the learner wording: “select, drag, right-click properties”; check Thai/English sample labels. | A beginner can locate label properties and understands that it is one label-wide style. |
| Ohm | Review that Board label appearance is never represented as pin/package/timing truth. | No physical chip fact is copied into label properties. |
| Mint | Confirm no HDL/export contract is implied by Board label style. | No Verilog, structural export, or timing artifact changes. |

## Required evidence

```sh
node --check board/app.js
node board/interaction-contract.test.mjs
node board/profile-v2.test.mjs
PYTHONPATH=python python3 -B -m tests.test_component_board_api
PYTHONPATH=python python3 -B -m tests.test_component_language
git diff --check
```

Then perform one browser observation: create a Thai/English label, edit text
on the label itself, click away to save, move it, resize it, right-click it,
change its complete style, reload, and verify that the Board profile changes
while Component source/topology remain unchanged. Also right-click each other
viewport object and verify a Board property view appears instead of the browser
menu.

## Exit and next boundary

Close this sprint only after the commands and browser observation are recorded.
Return next to the existing B2.3 browser checkpoint, then B3.1
definition-derived placement geometry. The session-only Guides release
candidate remains independently reusable and is not broadened here.
