# 19 — Example-Circuit Coverage of `component:component` First Draft

Status: **audit-only proposal**. This is a coverage map, not a parser,
migration, or runtime claim. It preserves the current JSON circuits as the
working compatibility format while identifying the smallest safe next
Component profiles.

The machine-readable audit is
[`fixtures/component-first-draft/examples-circuits-coverage.json`](fixtures/component-first-draft/examples-circuits-coverage.json).
Run:

```bash
python3 tools/check_component_examples_coverage.py
```

## Result

All **28 topology sources** can express their internal electrical graph with
the First Draft core after explicit expansion to `device`, `net`/`bus`, and
`connect`. This is deliberately narrower than saying they can be parsed,
resolved, or simulated today.

Five root JSON files are campaigns, coverage, timing, or physical-evidence
records rather than circuit sources. They remain compatibility/evidence data;
they are not candidates for `component:component` syntax.

| Source class | Count | First Draft result | What is still needed |
|---|---:|---|---|
| Legacy root topology JSON | 5 | core topology is expressible | compatibility importer; test actions compile to Operation |
| Leaf RV8GR package `circuit.json` | 17 | internal graph is expressible | Component boundary-port, metadata/evidence, and timing profiles |
| Composite RV8GR package `circuit.json` | 6 | nets and explicit connections remain valid | hierarchy plus locked child Component interface contracts |
| Campaign/coverage JSON | 3 | not topology | retain as compatibility/report records |
| Timing/physical JSON | 2 | not First Draft machine syntax | Component timing/evidence profile and later Board/lab workflow |

## What the core already covers

The examples are a useful stress set for the First Draft core:

- explicit DIP pin connections become `U1.@1`, not inferred wiring;
- scalar and ordered buses cover address, instruction, data, and accumulator
  paths;
- tri-state and bidirectional DBUS/IBUS cases exercise the planned resolver
  ownership checks;
- `Probe` and `BusProbe` observations map to read-only `probe`/`watch` and
  optional `display` intent;
- small assertions can be retained as bounded `test` declarations.

Existing JSON `aliases`, `inputs`, `clocks`, `steps`, trace replay, and
campaign commands are **not** First Draft topology. They are retained until a
future `component:operation` executes the bounded test requests. The First
Draft has intentionally no generic imperative compatibility syntax.

## Concrete blockers revealed by the examples

1. **Boundary-port profile.** Every reusable RV8GR package has a public
   `ports` list. First Draft currently has no Component boundary declaration,
   so a package cannot yet be instantiated by another Component without
   copying its internal names.
2. **Hierarchy profile.** Six packages instantiate another `RV8GR_*` package.
   They require a locked child resolved-topology/interface contract, not a
   fake chip definition or textual include.
3. **Compact Device migration.** The topology language can name all present
   chips, but its resolver must only lock compact resolved Device records.
   Examples currently need records for 74HC164/21/32/74/86/283/541/688,
   62256, and several virtual test devices before full resolution.
4. **Circuit evidence/timing profile.** Current `behavior`, `timing`,
   `verification`, `audience`, and physical warnings are valuable Component
   package facts. They must not be copied into Device definitions or silently
   turned into electrical behavior.
5. **Operation protocol.** Phase traces, opcode sweeps, seeded stress, and
   physical capture are executions and evidence collection, not wiring.

## Coverage closure before implementation

The following Component-owned blockers are now specified additively by the
[System Profile](20_Component_System_Profile.md), with the RV8GR whole-system
fixture as the conformance target:

- public boundary ports, including exported bus order and direction;
- hierarchy using locked published child Component interfaces;
- circuit metadata, scoped evidence, timing limitations, and test-suite
  references.

This closes the language-model gaps without changing a legacy JSON file or
pretending the unavailable child interfaces/compact Devices already resolve.
Operation execution, Board presentation, analog runtime semantics, and
physical evidence are explicitly deferred to their owners.  The profile gate
checks every blocker in this audit:

```bash
python3 tools/check_component_system_profile.py
```

## Safe implementation order

1. Implement a tiny parser/resolver only for a leaf First Draft circuit
   (`nand.json` and `counter.json` projections), validating physical pin
   selectors against compact resolved records.
2. Add the **Component boundary-port profile** and migrate one leaf RV8GR
   package such as `RV8GR_RingCounter` without deleting its `circuit.json`.
3. Add hierarchy using `RV8GR_BootSequenceTrace` only after child interface
   locks exist.
4. Add `component:operation` adapters for the existing JSON test vectors and
   trace campaigns. Board remains a later consumer of resolved observations.

No existing example should be rewritten or removed as part of this audit.
