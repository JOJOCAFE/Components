# Component Text IDE and CLI

The first Components authoring tool is text-first.  It reads a leaf
`component:component` file, shows the AST and resolved topology, and gives
student-safe diagnostics before any future Board editor exists.

It currently understands imports, Device instances, typed nets and buses,
explicit connections, probes/watches, display intent, and bounded declared
tests. It resolves Device ports and physical-pin selectors against the active
Components catalog. The supported leaf digital-model subset can instantiate a
resolved Component and run its declared beginner test actions (`set`, `pulse`,
`wait`, `settle`, and `assert`). It does **not** draw a Board, replace the
existing circuit JSON runner, or prove physical wiring, voltage, or timing.

Run from the repository root:

```sh
PYTHONPATH=python python3 -B -m chiplib.cli component-parse \
  Language/fixtures/component-first-draft/counter_first_draft.component

PYTHONPATH=python python3 -B -m chiplib.cli component-resolve \
  Language/fixtures/component-first-draft/counter_first_draft.component

PYTHONPATH=python python3 -B -m chiplib.cli component-ide \
  Language/fixtures/component-v1.1/digital_inverter.component

PYTHONPATH=python python3 -B -m chiplib.cli component-student \
  Language/fixtures/component-v1.1/digital_inverter.component

PYTHONPATH=python python3 -B -m chiplib.cli component-run \
  Language/fixtures/component-v1.1/digital_inverter.component --test inversion
```

`component-parse` emits the AST contract.  `component-resolve` and
`component-validate` emit the resolved Component topology plus stable
diagnostics.  `component-ide` emits both views and explicit capability flags;
it is the JSON-friendly backend for a terminal UI or later visual editor.
`component-student` is the short learner route: parts, wire count, things to
watch, and named tests. `component-run` is the bounded digital-model route;
use `--test NAME`, `--drive TARGET=0|1|Z|X`, and optional `--probe NAME`.

For the first guided example, read
[`COMPONENT_BUILD_NOT_GATE.md`](COMPONENT_BUILD_NOT_GATE.md).

The first golden pipeline is exercised by
`python/tests/test_component_language.py`:

```text
counter_first_draft.component
        -> components.component-ast@1
        -> components.resolved-component@1
        -> immutable scalar edges, locked Devices, read-only observations
```

An invalid port or an implicit scalar-to-bus connection fails with a named
diagnostic.  The tool never guesses ports, wires, bus bits, or Device behavior.

## Honest boundary

Component text is human-authored. AST, resolved topology, CLI/API results, and
future Board interchange are machine-readable JSON contracts. A future
`component:board` consumes the resolved Component; it cannot invent wiring or
change the Device truth. The current leaf runtime result is a digital-model
result only, never a breadboard, electrical-safety, or speed signoff.

## Resources: a picture is not a circuit

Resources give a reader or future editor a safe way to show an already
resolved part. They are ordinary JSON messages: a visual Board, API, or AI
helper can send and receive them without being allowed to rewrite a Component.

```sh
PYTHONPATH=python python3 -B -m chiplib.cli component-resource-inspect 74HC04

PYTHONPATH=python python3 -B -m chiplib.cli component-resource-bind \
  Language/fixtures/component-v1.1/digital_inverter.component \
  --target U1 --resource 74HC04 --view dip --label "My NOT gate"
```

The first command answers “what pictures can I use?” in student language. The
second produces a `components.resource-binding@1` message tied to the resolved
Component digest. It does not save a Board, add coordinates, route wires, or
change pins, logic, timing, nets, tests, or runtime state. A missing Resource,
wrong Device instance, wrong part, or unknown view is a clear error rather
than a guessed replacement.
