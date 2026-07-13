# 18 — `component:component` First Draft Release

Status: **first draft, additive proposal**.  This document turns the
human-first keyword style in `docs/Component/old_references/` into one small,
implementable source profile.  It builds on the v1.1 proposal in document 17;
it does not modify frozen Language v1.0 documents, compact Device definitions,
or any legacy reference.

## What this release is

`component:component` is the language for describing one machine:

```text
choose Devices → name nets/buses → connect them → declare checks → observe
```

The source is deliberately readable aloud.  A student should be able to find
the clock, power rails, signal path, and test intention without opening a UI.
The resolver—not the author—reads pin truth, behavior, timing, and simulator
providers from the selected compact Device definitions.

This release covers chip selection, wiring/connecting, bounded tests, and
read-only display intent.  `component:board` and `component:operation` are
deferred.  A future Board renders a resolved Component; a future Operation
executes its declared tests.  Neither is another circuit source of truth.

## Deliberate syntax choices

The uploaded v0.1 examples use `device Counter is 74HC161;`.  Document 17
temporarily showed a comma form.  This first draft selects the more readable
legacy word form as the public spelling:

```component
device Counter is digital.74HC161;
```

Other retained human-first words are `use`, `net`, `bus`, `connect`, `probe`,
`watch`, `test`, and `display`.  `watch` is an optional friendly alias for a
read-only probe declaration; it never starts a simulator or opens a Board.

The following old ideas are intentionally **not** accepted without a later
proposal:

- implicit wiring from matching names, symbols, or physical placement;
- `inject` as imperative source syntax (belongs to future Operation);
- `tick(...)` connections (a clock is a Device plus a test request);
- a generic `group` or `module` construct before hierarchy semantics exist;
- Board coordinates, symbols, wire routes, terminal sessions, or widgets.

## First-draft source shape

```ebnf
component      = use_statement* component_header "{" declaration* "}" ;
component_header = "component:component" identifier ("is" profile_ref)? ;
use_statement  = "use" library_ref "as" identifier ";" ;
declaration    = device | net | bus | connect | probe | watch | display | test ;
device         = "device" identifier "is" device_ref parameter_object? ";" ;
net            = "net" identifier ":" signal_kind ";" ;
bus            = "bus" identifier "[" positive_integer "]" ":" signal_kind ";" ;
connect        = "connect" endpoint "->" endpoint ";" ;
probe          = "probe" identifier "," endpoint ";" ;
watch          = "watch" identifier "," endpoint ";" ;
display        = "display" observation "as" display_kind option_object? ";" ;
test           = "test" identifier "{" test_step* "}" ;
```

An endpoint is a declared net/member (`count[0]`), logical Device port
(`Counter.QA`), or permitted physical-pin selector (`Counter.@14`).  Physical
selectors are checked against the resolved definition; logical names are
preferred in normal teaching source.

`connect A -> B` declares intended signal flow.  Resolution expands only
explicit legal mappings: scalar-to-scalar, scalar fan-out, and equal-width
ordered bus mappings.  It rejects scalar/bus mismatch, unequal ranges,
unknown ports, duplicate symbols, power misuse, and unapproved multiple drive.

## Tests and displays

Tests are bounded declarations, not scripts.  This draft permits the small
action vocabulary below only inside a `test` block:

```component
arrange { set reset_n = 0; }
settle;
assert count == 0;
arrange { set reset_n = 1; pulse Clock.OUT; }
wait 25 ns;
```

`set`, `pulse`, and `wait` compile to a future Operation request.  `assert`
reads a declared probe/watch or an otherwise resolvable read-only endpoint.
No test may redefine topology, Device behavior, pin numbers, or timing.

A display is only an observation request:

```component
probe total, count;
display total as waveform, { "label": "Count" };
```

Permitted built-in display kinds are `value`, `led`, `waveform`, and `table`.
Options hold presentation-neutral values such as label and radix.  Coordinates
and resource selection are Board/Resource work and remain out of this draft.

## Two complete examples

The release fixtures are intentionally small but real Device-library clients:

- [`counter_first_draft.component`](fixtures/component-first-draft/counter_first_draft.component)
  demonstrates power, a clock, active-low clear, a four-bit bus, a probe,
  watch alias, display intent, and a bounded reset/count test.
- [`mux_first_draft.component`](fixtures/component-first-draft/mux_first_draft.component)
  demonstrates four explicit signal paths through a 74HC157.  It does not
  pretend that source labels automatically create bus membership or wiring.

## Canonical resolved JSON target

Source is human-authored.  The resolver produces immutable canonical JSON
with scalar topology edges and locked Device records.  The exact target shape
is demonstrated in
[`counter_first_draft.resolved.json`](fixtures/component-first-draft/counter_first_draft.resolved.json).

Its rules are:

1. `schema` is `components.resolved-component@1`.
2. `source` identifies the authored Component file and source digest/identity
   when packaging is implemented.
3. `library_lock` identifies each compact Device definition by resolved record,
   not a Python/Verilog source path.
4. `instances`, `nets`, and `edges` are resolved, typed facts.  Every bus edge
   is scalarized and retains the source connection as provenance.
5. `observations` and `display_bindings` are read-only.
6. `tests` are bounded requests with no arbitrary executable payload.
7. `diagnostics` and `execution_limits` are explicit; unresolved or
   unsupported analog behavior is never silently converted to digital truth.

Generated JSON is reproducible cache/interchange data.  It must not be edited
as a second machine definition.

## Release acceptance boundary

This is a **language draft and resolver target**, not a parser release.  It is
ready for a parser/resolver implementation only after the following narrow
acceptance checks continue to pass:

```bash
python3 tools/check_language_spec.py
PYTHONPATH=python python3 tools/check_component_language_fixtures.py
PYTHONPATH=python python3 tools/check_component_first_draft.py
```

The last checker validates the first-draft fixtures against active resolved
Device facts and the canonical JSON invariants.  It deliberately does not
claim that it parses this proposed language.
