# 20 — `component:component` System Profile

Status: **first-draft release candidate; contract only**.  This additive
profile closes the Component-owned gaps found in the examples-circuit audit
before a parser or legacy-circuit migration is attempted.  It extends the
First Draft (documents 17–19); it does not alter frozen Language v1.0,
compact Device definitions, existing JSON circuits, or the deferred Board and
Operation models.

## Decision

`component:component` is the one source language for a complete machine,
from a single gate through the RV8GR whole system.  It owns the declarative
machine contract:

```text
Component identity and package facts
  + public boundary ports
  + Device instances and child Component instances
  + typed internal nets/buses and explicit connections
  + circuit-owned timing/evidence/teaching metadata
  + references to bounded declarative test suites
  + read-only observations/display intent
                 ↓ resolve
locked, immutable Component topology contract
```

It does **not** own an imperative run, trace replay, campaign scheduling,
input injection session, Board coordinates, physical measurement form, or a
copy of chip behavior.  Those stay respectively with future
`component:operation`, `component:board`, lab evidence, and the Device
Library.

This is deliberate: a whole system must have an interface and a composition
contract before it can be safely made executable.  A source that merely
embeds the old RV8GR JSON would not establish either.

## Additive declarations

### Component boundary ports

```component
port CLK : digital input;
port /RST : digital input;
bus port IBUS[8] : digital bidirectional;
bus port ABUS[16] : digital output;
```

A boundary port is part of a Component's public interface, not an implicit
alias for an internal net.  The resolver creates one typed boundary endpoint
and requires an explicit internal connection.  `input`, `output`, and
`bidirectional` describe the Component boundary.  They do not override a
child Device's pin direction, tri-state policy, or power rule.

An exported bus has explicit bit order.  `IBUS[0]` is not inferred from a
textual name such as `IBUS0`; it is established by this declaration and
carried into the lock record.

### Hierarchy with locked child interfaces

```component
component Boot is rv8gr.BootSequenceTrace
  lock "components.rv8gr.BootSequenceTrace@sha256:...";
```

`component` in a declaration is a **child Component instance**, whereas
`component:component` starts a source file.  A child reference resolves only
to a published `ResolvedComponentInterface`, which contains the child ID,
interface digest, public ports/buses with ordered members, compatible profile,
and dependency locks.  The parent may connect only those exported endpoints.
It may never reach a child's internal `U1.@3`, rewrite a child net, or infer
an interface from its title.

Changing a child boundary, bit order, signal kind, or required timing
contract changes the digest and makes the parent fail resolution until its
lock is consciously updated.  This is the hierarchy rule needed for RV8GR:
children remain independently understandable, testable, and replaceable.

### Circuit facts, timing, evidence, and test-suite references

```component
about {
  title "RV8GR virtual whole-system gate";
  purpose "compose independently checked RV8GR packages";
  audience "students 10-15";
}

timing contract virtual_stress_only {
  applies_to CLK, /RST, IBUS, DBUS;
  limitation "not physical clock-quality or PCB signoff";
}

evidence {
  claim "one active DBUS driver in checked phases";
  source "examples/circuits/RV8GR_BusOwnership/tests/bus_ownership.json";
  status virtual_proof;
}

test-suite "tests/whole_system_chip_level_virtual.json"
  kind declarative_vectors;
```

`about` is human/package metadata.  `timing` is a circuit-level constraint or
limitation, never copied into a Device definition and never an unmeasured
physical claim.  `evidence` attaches a scoped claim to a stable source and a
status; it cannot be used to manufacture simulator behavior.

`test-suite` references a versioned declarative test artifact.  Resolution
checks identity, schema, and declared target Component.  Operation later runs
it under a chosen environment.  A test suite does not add a generic scripting
language to Component source.

## System-profile grammar

The profile augments the First Draft grammar:

```ebnf
declaration  += boundary_port | child_component | about | timing | evidence |
                test_suite ;
boundary_port = ("port" | "bus" "port") identifier range? ":"
                signal_kind direction ";" ;
child_component = "component" identifier "is" component_ref
                  "lock" string ";" ;
about        = "about" "{" about_field* "}" ;
timing       = "timing" "contract" identifier "{" timing_field* "}" ;
evidence     = "evidence" "{" evidence_field* "}" ;
test_suite   = "test-suite" string "kind" identifier ";" ;
direction    = "input" | "output" | "bidirectional" ;
```

`range?` is required for `bus port` and prohibited for scalar `port`.
`about_field`, `timing_field`, and `evidence_field` are schema-validated
named fields; they are not arbitrary object bags.  This keeps the readable
keyword style from the uploaded language examples without making a parser
guess at meaning.

## Resolver additions

After Device resolution and before edge expansion, a System-profile resolver:

1. creates and validates unique public boundary symbols;
2. resolves every child against one locked published child interface;
3. checks child lock, direction, bus width/order, and profile compatibility;
4. resolves explicit boundary-to-internal and parent-to-child edges;
5. validates circuit timing/evidence fields against their schemas, preserving
   limitations verbatim;
6. validates test-suite identity and its declarative target, without running
   it; and
7. emits `ResolvedComponentTopology` plus `ResolvedComponentInterface`.

There is no partial success: unavailable compact Devices, unpublished child
interfaces, or non-declarative test payloads remain explicit diagnostics.

## Whole-system acceptance boundary

The RV8GR fixture in
[`fixtures/component-system-profile/`](fixtures/component-system-profile/)
is source-shaped rather than a migration.  It demonstrates all public
whole-system ports, independent child packages, bus ownership, scoped timing
and evidence, and a declarative test-suite reference.

Its resolved target is intentionally a **contract target**, not a claim that
all legacy children are resolved today.  Its `deferred_capabilities` list
names the remaining Device migrations, child-interface publications, analog
runtime semantics, Operation execution, Board rendering, and physical
signoff.  This is how the language covers the RV8GR system honestly before
implementation.

Run the coverage gate:

```bash
python3 tools/check_component_system_profile.py
```

It proves that every blocker recorded by document 19 is either supplied by
this profile or explicitly deferred to its rightful owner.  It does not parse
or execute the fixture.

## Implementation gate

Do not begin a parser/resolver migration until this contract, its fixture, and
the audit gate pass together.  The first implementation should still be a
small leaf circuit; RV8GR is the complete conformance target, not the first
debugging surface.
