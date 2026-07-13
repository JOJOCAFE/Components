# `component:component` v1.1 conformance fixtures

These are deliberately small, machine-readable fixtures for the proposal in
[17_Component_Language_Model_v1_1.md](../../17_Component_Language_Model_v1_1.md).
They are not a parser implementation and they do not add a second editable
Device definition format.

Each positive case has:

- a readable proposed Component source (`*.component`);
- an expected resolved-topology interchange record (`*.expected.json`);
- a library lock whose paths point at active compact-definition generated
  records; and
- exact port/pin facts that a fixture checker verifies against those records.

Each negative case is source-shaped JSON with stable expected diagnostic codes.
It is an acceptance target for a future parser/resolver, not an instruction to
silently repair the source.

The passive-and-virtual fixture proves only resolution and topology shape.
Current passive compact records intentionally do not yet declare sufficient
cross-domain electrical semantics to claim an executable analog/digital
simulation.  The fixture makes that limitation explicit instead of faking
behavior.

Run the narrow library-fact check from repository root:

```bash
PYTHONPATH=python python3 tools/check_component_language_fixtures.py
```

No fixture has Board coordinates, a Board resource, or an imperative Operation
transport.  A future runtime may compile its declared tests into the deferred
Operation protocol, but that protocol is not implemented here.
