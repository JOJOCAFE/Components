# `component:component` first-draft fixtures

These files are the public-readable examples for
[the active Component model](../../../docs/Component/Component_Model.md).
They are not a
parser implementation and do not replace compact Device definitions.

- `counter_first_draft.component` uses the selected `device X is Y;` spelling,
  a Device clock, typed rails/nets/bus, explicit wires, `probe`, `watch`,
  `display`, and a bounded test.
- `mux_first_draft.component` keeps every 74HC157 channel connection explicit,
  proving no bus/wiring inference from similarly named ports.
- `counter_first_draft.resolved.json` is canonical resolved topology target
  JSON.  It is a generated artifact, not editable source.

Run from repository root:

```bash
PYTHONPATH=python python3 tools/check_component_first_draft.py
```
