# Component Learning Lens

Status: Board/Resource design contract for the learner-facing explanation
layer. It does not add Device behavior, change topology, or grant a Board
direct runtime authority.

## Why this exists

Components is made first for learners around 10–15 years old, while remaining
useful to any adult beginner. A learner must not need a reference guide or a
long course before the first Component makes sense.

A **Learning Lens** is the small explanation attached to a thing already
known by the resolved Component: a part, wire, input, output, probe, display,
or run result. It answers the learner's immediate questions without hiding the
real technical terms or electrical truth.

```text
resolved Component + Resource view + trace/result
        -> Learning Lens
        -> learner sees / reads / safely tries
```

The lens is presentation. It cannot invent a part, wire, signal value, pin,
Device rule, timing fact, or test result.

## Three depths of one machine

The learner does not switch to a different beginner circuit or expert circuit.
They look at the same resolved Component in gradually deeper views.

| Depth | What is visible | Example for a NOT gate |
| --- | --- | --- |
| First sight | plain name, one-sentence purpose, arrows/values, one safe action | “This flips the input.” `Try inversion` |
| Read it | matching readable Component line and plain explanation | `connect U1.1Y to OUT;` — “The gate sends its changed signal to OUT.” |
| See inside | real Device name, pins, timing/trace detail, DIP/breadboard/3D Resource when available | `74HC04`, pin `1Y`, trace timeline, DIP-14 view |

The first depth is default. The other two appear on selection or a short
**See details** action. No learner is blocked from the first task by missing
2D/3D art, a datasheet, or advanced vocabulary.

## The five questions every lens answers

For a visible selected object, the Board supplies:

1. **What is this?** — a short learner title, for example “Output wire.”
2. **What does it do here?** — one sentence in this Component, for example
   “It carries the changed signal to the output.”
3. **What is its real name?** — nearby, quieter technical vocabulary such as
   “Wire (`net`)” or “NOT gate (`74HC04` Device).”
4. **What can I try?** — at most one or two safe, contextual actions, such as
   `Watch OUT`, `Try inversion`, or `See the pin names`.
5. **What happened?** — after an action, a plain before/after statement plus
   an optional trace/detail route.

The Board must not turn this into a tooltip forest, a lesson wall, or a modal
dialog sequence. The explanation appears next to the selected object and
disappears when it is no longer useful.

## Safe actions, not hidden power

A Learning Lens may offer only an action already permitted by an explicit
contract:

| Lens action | Delegates to | Must show |
| --- | --- | --- |
| `Inspect` / `See details` | resolved Component or Resource reader | locked target identity and source line when applicable |
| `Watch` | read-only probe/trace request | observation target and result |
| `Try example` / `Run` | declared bounded test | test name and digital-model boundary |
| `Connect` / `Disconnect` | checked source-edit request | exact readable source patch before apply |
| `Drive` / `Pulse` | bounded Runtime Operation | target, value, time, and resulting trace |

The lens never sets a runtime value, writes source, connects a wire, or loads
a plugin by itself. It asks the existing checked service, then displays the
returned text patch, diagnostics, or trace.

## How Resource views participate

Resource Definitions may supply a short text/teaching view, a 2D visual, a
3D package, icons, or an accessible description. They remain presentation
only. The Learning Lens combines those views with locked resolved facts; it
does not trust a Resource to explain pin direction, logic, timing, or safety
in a way that conflicts with the Device Library.

Recommended view order:

```text
teaching text -> compact visual -> real package/DIP -> breadboard/3D -> debug
```

Every later view is optional. The fallback is a readable title, source line,
and resolved fact—not a blank box.

## NOT-gate first-sight fixture

The first fixture must open with:

```text
Title:      A NOT gate
Meaning:    It changes 0 into 1, and 1 into 0.
Drawing:    IN -> U1 -> OUT
Try now:    [ Try inversion ]
After run:  IN was 0; OUT became 1.
```

Selecting `U1` reveals “NOT gate (`74HC04`)”; selecting the output wire
reveals its matching `connect` line; selecting **See details** can reveal the
DIP view and real pin names. An invalid connection highlights the involved
objects and says what to do next, rather than exposing only a diagnostic code.

## Acceptance test

With no guide or prior lesson, a 10–15-year-old learner and an adult beginner
must each open this fixture and, within five minutes:

1. explain the NOT gate in their own words;
2. point to the input, part, and output;
3. run the example and say what changed;
4. make one safe change through Drawing, Text, or a suggested Terminal action;
5. recover from one deliberate invalid connection; and
6. find the real Device/pin detail only after choosing to see it.

Failure is a Board design failure. Add neither a longer manual nor another
feature until the learner can complete the path.

## Relationship to earlier ideas

This adopts the useful intent of the archived Board and Resource proposals:
Board is a workbench; Components describes; Resources offer teaching, package,
and debug views; the timeline/waveform explains observed behavior. The active
ownership boundary remains unchanged: Components/Devices define truth;
Resources and Board present it; Operations request bounded work.
