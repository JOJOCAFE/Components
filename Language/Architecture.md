# Components Language Architecture

Status: architecture map.  This document is the shared pipeline reference for
the Language documents and Component fixtures.  It does not change the frozen
v1.0 grammar (`00`–`15`) or make the deferred runtime, Operation, or Board
features implemented.

## Names and boundary

- **Component** is the authored description of one machine: its instances,
  explicit nets, observations, and declarative tests.
- **Components** is this library: its Device definitions, resolver inputs,
  compatibility models, and future runtime host.
- A Component **resolves against Components**.  It may run only when a future
  Components Runtime has instantiated its resolved topology.  A fixture that
  has no runtime result must not claim execution.

The lowercase `component:component` spelling is a frozen source-language
keyword.  Capitalization in explanatory text does not create a second keyword.

## Authoring-to-runtime pipeline

```text
Component source
      |
      v
Lexer -> tokens -> Parser -> AST -> structural diagnostics
                                      |
                                      v
                         Resolver + locked Components libraries
                                      |
                                      v
                         Resolved Component
                         - pinned Device definitions
                         - typed endpoints and scalar edges
                         - provenance and validation results
                                      |
                                      v
                         immutable Topology / Signal Graph
                                      |
                                      v
                         Components Runtime
                         - instances and signal values
                         - event queue and delta scheduler
                         - Device evaluation and propagation
                                      |
                                      v
                         Trace, probes, diagnostics, exports
                                      |
                                      v
                         optional Operation client or Board view
```

Each arrow is one-way in ownership.  A Board renders or observes a resolved
Component; it never creates hidden topology.  A trace records runtime facts;
it does not become editable Device truth or physical timing signoff.

## Phase contracts

| Phase | Input | Output | Must not do |
|---|---|---|---|
| Lexer | Component source text | token stream and lexical diagnostics | read libraries or simulate |
| Parser | tokens | AST with source spans | resolve names or infer topology |
| Resolver | AST and locked Components libraries | Resolved Component | mutate Device definitions or execute behavior |
| Validator | Resolved Component | stable diagnostics and validated topology | silently repair ambiguity |
| Topology compiler | validated Component | immutable signal graph | create live signal values |
| Runtime scheduler | topology plus explicit operations | signal transitions, state, trace | read raw AST or bypass a driver |
| Board/Operation client | resolved topology and runtime API | presentation or bounded request | alter topology/device truth privately |

## Resolved Component contract

The resolver returns a reproducible, immutable `ResolvedComponent`.  At a
minimum it contains:

- Component identity, source digest, profile, and source provenance;
- locked Device-definition identities and resolved ports, pins, behavior, and
  timing references;
- typed instances, nets, buses, boundary endpoints, and scalar edges;
- explicit drivers, receivers, clocks, probes, and displays;
- validation result and stable diagnostics.

The normalized topology is the executable signal graph.  It is generated from
Component source plus locked library facts and is not an editable competing
source format.

## Validation boundary

Validation is distinct from topology construction even though a successful
resolver performs both in sequence.  Structural and resolution failures stop
topology production.  Topology validation covers types, widths, power,
direction, explicit driver ownership, and statically knowable clock loops.
Runtime validation covers enable-dependent contention, unknown state,
oscillation, limits, and timing at actual scheduled events.

No layer guesses same-name connections, bus membership, power rails, Device
behavior, or physical timing evidence.

## Runtime boundary

The runtime consumes the topology, never raw AST.  It creates isolated
`ComponentInstance`, `DeviceInstance`, `NetInstance`, `Signal`, `Event`,
`Clock`, `Probe`, and `Trace` state.  It schedules deterministic `(time,
delta)` events, resolves four-state nets, propagates Device-owned delays, and
records observations.  The detailed proposed object contract is
[18_Runtime_Model.md](18_Runtime_Model.md).

The runtime result is digital simulation evidence only.  It cannot establish
PCB layout correctness, analog behavior, current limits, or physical timing
signoff.

## Fixture layers

Fixtures are organized by contract, not by one end-to-end parser claim:

| Layer | Fixture purpose |
|---|---|
| lexer | tokenization and lexical diagnostics |
| parser | AST shape, spans, and recovery |
| resolver | locked library identity and endpoint resolution |
| validator/topology | type, width, rail, and ownership diagnostics plus graph shape |
| runtime | event, edge, delta, propagation, and trace behavior |

The current `component-v1.1` fixtures are resolver/topology conformance
targets, while `component-system-profile` records hierarchy ownership and
deferred runtime boundaries.  New executable fixture families must be added
only with a parser or runtime implementation that can consume them.
