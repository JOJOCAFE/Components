# 23 — Resource Definition Contract

Status: proposal for C3.3.  This contract describes a Resource that can be
shown as short text, a 2D visual, a 3D model, or a later presentation kind.
It is deliberately separate from Device definitions, Components, and Board
profiles.

## The simple idea

A **Device** answers “what does this chip really do?”  A **Resource** answers
“how can a learner look at it?”

```text
Device truth          -> owned by the Device Library
Resource definition   -> a safe description, picture, model, or data view
Resource binding      -> chooses one Resource view for one resolved target
Board/text client     -> displays the chosen view
```

For example, a 74HC04 Resource may offer a short explanation, a DIP drawing,
and later a 3D package.  None of those may say that the chip is a NAND gate,
change pin 1, add a wire, or make a test pass.

## Canonical document

`schemas/resource-definition.schema.json` defines one closed
`components.resource-definition@1` document.  It contains:

- stable `id` and immutable-content `digest` identity;
- a `target` identity saying which Device, Probe, or Display this Resource may
  present, without embedding its electrical definition; and
- one or more named `views`, each with a learner-facing accessible label and
  either inline text or one non-executable artifact reference.

Standard view types are `text`, `visual-2d`, `model-3d`, and `data`.  The
`kind` string lets a later profile name a more specific form such as
`package.dip` or `model.glb` without changing this document's ownership rule.
No client is required to understand every type.  It must show a text view when
one exists, or clearly say that the requested view is unavailable.

An artifact is only a reference: URI/path, media type, optional digest, and
optional byte size.  It is not JavaScript, a callback, a driver, an Operation,
or a request to execute code.  A 3D view is loaded only when the learner asks
to see it.

## Binding rule

A `components.resource-binding@1` record selects a Resource by its `id`,
`digest`, and declared view ID.  Binding resolution must prove all three match
an available Resource Definition and that the definition's target is
compatible with the already-resolved Component target.

Changing a Resource or binding can change only presentation output.  It does
not change the resolved-topology digest, Device behavior, runtime identity,
or trace result.  If a matching Resource is missing, the Component remains
valid and clients show readable target/device facts instead.

## Hard exclusions

A Resource Definition must not contain, directly or under another name:

- Device pins, ports, direction, polarity, behavior, model, timing,
  electrical limits, evidence, or test status;
- Component instances, parameters, nets, buses, edges, connections, power
  rails, drivers, or topology;
- runtime values, events, clocks, operations, callbacks, executable scripts,
  or state; and
- Board placements, routes, widgets, or hidden layout precedence.

The existing package-local `lib/standard/*/*/resource/definition.json`
mapping remains a migration-era library map.  It may be adapted to emit this
interchange shape later, but this proposal does not change current device
packages, Python behavior, or CLI output.

## Checked examples

The fixtures in `fixtures/component-presentation-contract/` include text,
2D, and 3D views plus negative ownership cases.  Check them with:

```bash
python3 -B tools/check_component_presentation_contracts.py
```

They prove a binding can select a declared view.  They do not claim that a
Board client, 3D renderer, plugin host, or Resource importer exists yet.
