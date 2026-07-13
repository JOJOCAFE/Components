# Component First-Sight Design

Component and Components serve learners around **10–15 years old** first. They
must also welcome an adult beginner—up to about 25 or any age—who knows
nothing yet about electronics or digital logic.

The product is not allowed to require a reference guide, a 21-day course, or
prior vocabulary before a learner can make a first working change. Guides and
lessons can deepen understanding later; the first screen must already make
the next safe action obvious.

## The first-sight promise

When a learner opens a Component, they should be able to answer these
questions without leaving the screen:

1. **What is this?** — a plain title and one sentence, such as “This is a NOT
   gate: it changes 0 into 1, and 1 into 0.”
2. **What are its important parts?** — visible named parts, inputs, outputs,
   and wires; no unexplained symbols as the only explanation.
3. **What can I try now?** — one large safe action, usually **Try it** or
   **Run example**, with a visible expected result.
4. **What happened?** — a simple before/after value and one short reason,
   with the trace available but not forced on them.
5. **What can I change safely?** — a highlighted input, connection, or part
   with a preview of the readable Component line that will change.

If the learner cannot answer these within the first minute, the screen is too
complicated—even if every advanced feature works.

`COMPONENT_LEARNING_LENS.md` defines how the Board gives these answers beside
the selected part, wire, value, or result without becoming a separate lesson
system or a second electrical model.

## Teach by showing, not by sending learners away

The three-pane workspace is the first explanation:

| Surface | What it teaches at first sight |
| --- | --- |
| Drawing | “These are the things and paths in my machine.” Names and arrows explain direction. |
| Readable Component text | “This is the short sentence version of what I see.” Selecting a part or wire highlights its line. |
| Small Terminal | “I can ask the machine to try something now.” It offers examples, not a blank command prompt. |

The default NOT-gate screen should show `IN`, `U1`, and `OUT`; a clear path
between them; `0 -> 1` / `1 -> 0`; and one **Try inversion** action. It should
not begin with a library tree, an empty canvas, a long form, a datasheet, or a
command manual.

## Beginner language rules

- Say **part**, **wire**, **input**, **output**, **watch**, and **try** before
  specialist terms such as instance, net, probe, topology, or operation.
- Show the real technical name too, quietly and nearby: “Wire (`net`)”. This
  respects growing learners without making first use difficult.
- Every warning says what happened, why it matters, and one next action:
  “This output is already connected. Pick another output or remove the old
  wire.” Never show only a code such as `E_OUTPUT_OWNERSHIP`.
- Explain one concept at the point it is used. Do not display a lesson wall or
  force a multi-step onboarding sequence.
- Keep physical truth honest: “This is a digital-model result, not proof that
  a breadboard is wired safely.” Make the sentence short and attached to Run,
  not hidden in a manual.

## Interaction rules for a true beginner

- The main path uses point/tap, drag, and short labelled actions. Keyboard and
  Terminal are welcome shortcuts, never prerequisites.
- A connection gesture previews the readable source line and either applies it
  safely or explains why it cannot be used. It never creates a mysterious
  hidden connection.
- Direct manipulation always has a visible result: selection highlights the
  related Drawing object and text line; Run highlights the values it changed.
- The interface starts with a small useful example, not a blank project.
- Advanced panels stay closed until requested. A learner can grow into traces,
  pin facts, resources, tests, and terminal history when ready.

## First-sight acceptance test

Ask a new 10–15-year-old learner and a non-electronics adult to open the
NOT-gate example with no prior lesson. Within five minutes, they should be
able to:

1. say what the example does in their own words;
2. point to its input and output;
3. run the example and describe the result;
4. make one safe input or connection change; and
5. recover from one deliberate mistake using the on-screen message.

If either learner needs a reference guide to complete this, redesign the
screen before adding features. This is a usability gate alongside parser,
runtime, and ownership tests.
