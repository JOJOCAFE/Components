# 17 — `component:component` Language Model v1.1 Proposal

Status: proposal.  This is an additive v1.1 authoring and resolver contract.
It does not modify frozen Language v1.0 documents `00`–`15`, the compact
Device-definition schemas, or any imported `old_references` document.

## Purpose and boundary

`component:component` describes one machine that can be wired, validated,
tested, simulated, and observed.  It is the source model above the compact
chip-definition library and below a future Board or Operation client.

```text
compact human Device definition
          ↓ resolve
resolved Device facts (ports, pins, behavior, timing, evidence)
          ↓ instantiate and connect
component:component source
          ↓ parse + resolve + validate
resolved Component topology
          ↓ execute
simulation results and immutable traces
```

The Component source owns instance names, nets, bus membership, explicit
connectivity, declarative checks, and named observations.  It does **not** own
copied chip behavior, pin truth, timing values, symbol coordinates, Board
layout, or imperative simulator commands.

`component:board` and `component:operation` remain deferred.  A future
Operation may execute a declared Component test, inject a value, or read a
declared display; a Board may render a declared display.  Neither changes the
Component topology behind the author’s back.

## Authoring model

The following syntax is the proposed v1.1 profile of the v1 generic
`ComponentStatement` mechanism.  It deliberately uses readable names rather
than positional encoding.  `test` and `display` blocks are profile syntax;
they are not new frozen-core keywords.

```component
use standard.digital as digital;
use standard.virtual as virtual;

component:component CounterDemo is components.digital {
  title "Four-bit counter demonstration";

  device Counter, digital.74HC161;
  device Clock, virtual.ClockSource, { "period_ns": 100 };
  device Lamp0, virtual.Probe;

  net vcc : power;
  net gnd : power;
  net clear_n : digital;
  bus q[4] : digital;

  connect vcc -> Counter.VCC;
  connect gnd -> Counter.GND;
  connect Clock.OUT -> Counter.CLK;
  connect clear_n -> Counter./CLR;
  connect Counter.QA -> q[0];
  connect Counter.QB -> q[1];
  connect Counter.QC -> q[2];
  connect Counter.QD -> q[3];
  connect q[0] -> Lamp0.IN;

  probe count, q;
  display count as waveform, { "label": "Counter Q" };

  test clear_then_count {
    arrange { set clear_n = 0; }
    settle;
    assert q == 0;
    arrange { set clear_n = 1; pulse Clock.OUT; }
    settle;
    assert q == 1;
  }
}
```

The example demonstrates intent, not a Board format.  `waveform` is a
display *kind* bound to a resolved signal; a UI decides where and how it is
drawn.  The model continues to work with no UI at all.

## Source declarations

### Imports and component identity

`use` imports a version-resolved Device-library namespace.  An alias is local
to the source file.  A Component has a stable qualified ID supplied by its
containing package or explicit metadata; a display label is never an ID.

### Device instances

```component
device <instance-id>, <library-alias>.<device-id>, <parameters>?;
```

The library locator resolves to a compact human-authored Device definition and
then to its generated/resolved Device record.  Only the resolved record is
used to validate ports, physical pin selectors, parameter names, defaults,
behavior, and timing.  The Component never selects `model.py`, `model.v`, or
a generated path directly.

Parameters are explicit overrides to Device-declared parameters.  A resolver
rejects unknown parameters, invalid units, and an attempt to override a
library-owned fact such as a pin number or output direction.

### Nets and buses

```component
net <net-id> : <signal-kind>;
bus <bus-id>[<width>] : <signal-kind>;
```

A net is one named electrical connection point.  A bus is an ordered,
fixed-width collection of member nets; `q[0]` is the least-significant member
only when the declaration or Device port establishes that ordering.  Textual
names such as `Q0` never create bus membership implicitly.

`signal-kind` begins with `digital`, `power`, `analog`, or `virtual`; its
electrical constraints come from the Type System and the resolved Device
facts.  Supply rails are ordinary typed nets, not hidden globals.

### Connections

```component
connect <endpoint> -> <endpoint>;
```

An endpoint is exactly one of:

- a declared net or bus member (`q[2]`);
- a Device logical port (`Counter.QA`);
- a Device physical pin selector (`Counter.@14`), if its resolved definition
  authorizes that selector;
- an explicitly declared Component boundary port in a future hierarchy
  profile.

One bus-to-bus connection is permitted only when both widths and ordered
member mappings are explicit and equal.  A scalar-to-bus connection is an
error.  Direction is checked after endpoint resolution; arrows make source
intent readable but do not erase real bidirectional or tri-state behavior.
Multiple drivers, contention policy, floating required inputs, power-domain
misuse, and timing violations are semantic errors or explicit warnings from
the resolved topology—never silently repaired by a renderer.

### Probes and displays

```component
probe <probe-id>, <endpoint>;
display <probe-id | endpoint> as <display-kind>, <options>?;
```

A probe is a stable named observation declaration.  It does not drive a net,
change load, or create a virtual Device.  A display binds presentation intent
to a declared probe or read-only endpoint.  `display-kind` may be `value`,
`led`, `waveform`, `table`, or a library-defined compatible kind.  Options are
schema-validated data such as a human label or radix; no coordinates, symbols,
wire routing, or mutable Board state belong here.

### Declarative tests and validation

```component
test <test-id> {
  arrange { <test-action>* }
  settle;
  assert <observation> <comparison> <expected>;
}
```

Tests are named, deterministic acceptance cases attached to the machine they
describe.  They may request bounded actions (`set`, `pulse`, `wait`) and make
assertions only through declared or resolvable observations.  Their execution
is delegated to the future Operation/runtime protocol; they are not an
arbitrary scripting language.  A test records initial state, requested time
or edge, settle point, expected value, and diagnostic source span so a failure
is reproducible.

Static `validate` is implicit for every Component and includes structural,
library-resolution, electrical/type, topology, and timing checks.  A future
explicit `validate <profile>;` statement may select a stricter profile, but
may never turn off baseline safety checks.

## Proposed AST profile

This profile extends the generic `ComponentNode.body` representation after a
v1.1 parser is approved.  It preserves the v1.0 rule that the parser knows no
Device behavior and creates no runtime topology.

```text
ComponentNode
  name, base_schema?, body: ComponentStatementNode[]

DeviceDeclNode       { instance, library_reference, parameter_object? }
NetDeclNode          { name, signal_kind }
BusDeclNode          { name, width, signal_kind, member_order }
ConnectNode          { source: EndpointRefNode, target: EndpointRefNode }
ProbeDeclNode        { name, endpoint }
DisplayDeclNode      { target, display_kind, options? }
TestDeclNode         { name, phases: TestPhaseNode[] }
TestPhaseNode        { kind: arrange|settle|assert, body }
```

`EndpointRefNode` remains a syntactic reference.  It cannot contain a resolved
pin, width, drive state, or timing path.  The AST records authored bus member
order and source spans; it does not expand buses or create edges.

## Resolver and validation contract

Resolution must occur in this order:

1. resolve imports to pinned Device-library identities;
2. resolve every Device locator to one generated/resolved Device record;
3. build the Component symbol table and reject duplicate identifiers;
4. resolve net/bus members, endpoints, aliases, logical ports, and permitted
   physical pin selectors;
5. apply Device-declared parameter defaults and validate explicit overrides;
6. expand each valid connection to typed scalar topology edges;
7. validate direction, width, power, drive/tri-state ownership, required
   inputs, and Device timing constraints;
8. bind probes/displays read-only to resolved targets and compile tests into
   bounded runtime requests.

Failure at one stage produces an Error Model diagnostic and prevents later
stages from inventing missing facts.  In particular, resolution does not infer
connections from matching labels, package layout, a Board wire, or a symbol
graphic.

## Resolved runtime topology

After successful resolution, execution receives an immutable topology, not
source text or AST:

```text
ResolvedComponentTopology
  component_id
  library_lock: DeviceLibraryIdentity[]
  instances: ResolvedDeviceInstance[]
  nets: ResolvedNet[]
  edges: ResolvedEdge[]
  probes: ResolvedProbe[]
  display_bindings: ResolvedDisplayBinding[]
  tests: ResolvedTestCase[]
  diagnostics: Diagnostic[]
  provenance: source spans + resolved-definition identities
```

Each `ResolvedDeviceInstance` refers to one resolved Device definition and its
approved simulator providers.  Each edge has scalar endpoints, signal type,
and provenance.  The interpreter constructs its signal graph from this model,
evaluates Device Library behavior, applies timing, and produces immutable
trace/result records.  A display binding can consume those records but cannot
write runtime state.

Generated topology JSON is a cache/interchange artifact.  It is reproducible
from Component source plus locked resolved Device definitions and must not be
hand-edited as a second source of truth.

## Required conformance cases

An implementation of this profile must prove at least:

1. a Component can instantiate an active compact digital Device and resolve
   its named ports from `generated/resolved.json`;
2. a Component can instantiate a compact passive or virtual Device without
   claiming it is a digital chip;
3. a valid scalar connection becomes one topology edge with source provenance;
4. invalid width, unknown port, duplicate instance, output conflict, and
   forbidden physical pin selectors fail before execution;
5. probe/display declarations are read-only and do not add topology drivers;
6. a test has deterministic seed/initial-state/time limits and reports an
   assertion observation point;
7. no Board coordinate, rendering resource, or imperative UI command is
   needed to resolve, validate, or execute the Component.

## Explicit non-goals

- Defining Board placement, wire drawing, panels, themes, or interaction.
- Defining Operation transport, permissions, or trace serialization beyond
  the proposal in `16_Operation_and_Trace_Protocol.md`.
- Replacing compact Device-definition JSON or making a Component source copy
  its behavior, timing, evidence, or package facts.
- Implementing an unrestricted embedded scripting language.
- Claiming simulation traces are physical breadboard timing signoff.
