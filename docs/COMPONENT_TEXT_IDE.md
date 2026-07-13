# Component Text IDE and CLI

The first Components authoring tool is text-first.  It reads a leaf
`component:component` file, shows the AST and resolved topology, and gives
student-safe diagnostics before any future Board editor exists.

It currently understands imports, Device instances, typed nets and buses,
explicit connections, probes/watches, display intent, and bounded declared
tests.  It resolves Device ports and physical-pin selectors against the active
Components catalog.  It does **not** execute declared tests, simulate a new
Component topology, draw a Board, or replace the existing circuit JSON runner.

Run from the repository root:

```sh
PYTHONPATH=python python3 -B -m chiplib.cli component-parse \
  Language/fixtures/component-first-draft/counter_first_draft.component

PYTHONPATH=python python3 -B -m chiplib.cli component-resolve \
  Language/fixtures/component-first-draft/counter_first_draft.component

PYTHONPATH=python python3 -B -m chiplib.cli component-ide \
  Language/fixtures/component-v1.1/digital_inverter.component
```

`component-parse` emits the AST contract.  `component-resolve` and
`component-validate` emit the resolved Component topology plus stable
diagnostics.  `component-ide` emits both views and explicit capability flags;
it is the JSON-friendly backend for a terminal UI or later visual editor.

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
