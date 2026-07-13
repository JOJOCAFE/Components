# Component v0.1 reconciliation backlog

Status: non-normative working inventory.  The uploaded v0.1 material remains
reference material.  [Language/](../../Language/README.md) is the frozen
Language Specification v1.0, and
[Definition ownership](../DEFINITION_OWNERSHIP_V0_1.md) is the package
ownership contract.  This file neither changes those contracts nor authorizes
an implementation or file migration.

## How to read this backlog

- **Adopted** means the requirement is already represented by a Language v1 or
  ownership rule; it needs no competing specification.
- **Deferred** means it belongs to the later Board/Resource implementation
  phase, not Language Core.
- **Needs decision** means the requirement has useful intent but needs an
  explicit v2 proposal and tests before it can become normative.

Each row is one requirement candidate, combined where the v0.1 documents
repeat the same idea.

## Device Library candidates

| Candidate requirement | v0.1 sources | Status | Reconciliation / conflict |
|---|---|---|---|
| Stable qualified Device identity and explicit library resolution | `05_Device_Library_Spec_v0.1.md` §§4, 27–29; `01_Components_Component_Model_v0.1.md` Libraries | Adopted | Language Object/Resolver models require stable qualified IDs and reject unknown providers; keep existing `lib/standard` compatibility names during migration. |
| Device owns ports, physical pins, behavior, timing, electrical limits, evidence, and model identity | `05` §§6–11, 17–22, 25; `01` Libraries | Adopted | This is exactly the Device row of the ownership contract.  Resource must not duplicate or override these facts. |
| Physical and virtual devices share one DeviceDefinition interface; virtual devices may omit packages | `05` §§10, 23 | Adopted | Language Object Model supports DeviceDefinition/Port/Pin and the current typed Device classes; absence of a physical package is valid. |
| Direction/electrical/active-level metadata is semantic validation data, not parser behavior | `05` §§7–9 | Adopted | Language keeps parser AST-only; resolver/topology validation owns directions, types, power, and driver rules. |
| Device parameters and unit-bearing values normalize after parsing | `05` §§14–15 | Needs decision | The intent fits resolver ownership, but canonical unit grammar, dimensions, overflow policy, and JSON representation are not frozen in Language v1. |
| Declarative, provider, external-adapter, and composite behavior-model options | `05` §§17–20, 24, 33 | Needs decision | Language v1 requires a behavior provider and immutable DeviceDefinition, but does not yet freeze provider ABI, trust/sandbox rules, or composite Device packaging. |
| Explicit initial-state and memory-injection policies | `05` §§16, 20 | Needs decision | Current Interpreter initialization supports explicit reset/default inputs.  A portable Device policy vocabulary (`undefined`, image injection, power-on state) needs a separate Device-profile proposal. |
| Device test categories and source evidence provenance | `05` §§25–26 | Needs decision | Evidence is Device-owned and current package tests exist, but a universal evidence-map format and test-manifest schema are not Language Core. |
| Version/category metadata | `05` §§4–5, 29 | Deferred | Useful library catalog metadata, but it must not change parser or runtime semantics.  Add only with a concrete library-manifest consumer. |

## Resource Library candidates

| Candidate requirement | v0.1 sources | Status | Reconciliation / conflict |
|---|---|---|---|
| Stable Resource identity mapped to a Device, with multiple views per Device | `06_Resource_Library_Spec_v0.1.md` §§4–6, 10–11 | Adopted | Language Object Model has ResourceBinding; current `resource/definition.json` maps existing presentation artifacts without copying Device truth. |
| Resource selection precedence across libraries and Board-local overrides | `06` §§7–9 | Deferred | This is a Board resolver policy.  Board is explicitly deferred; no precedence is implied by current package Resource maps. |
| Resource presentation binds to resolved state but never changes simulation state | `06` §§15–17, 39; `07_Interpreter_Architecture_v0.1.md` Resource Interaction | Adopted | Language Interpreter makes Operations explicit topology drivers; ownership forbids Resource behavior/timing mutation. |
| Visual package/pin rendering must agree with Device pin truth | `06` §§11–13, 32–35 | Adopted | Existing Resource-pilot tests compare displayed pins/labels to resolved Device pins.  Resource is presentation-only. |
| Board placement, collection layout, connection routes, panels, timeline, waveform and terminal rendering | `06` §§18–26, 38 | Deferred | These are Board/UI requirements.  They must reference existing Component topology and trace data, never create topology or reconstruct trace history. |
| Themes, accessibility, resource data types, executable widget sandbox and resource dependencies | `06` §§27–31 | Deferred | Valuable Resource/Board requirements, but no Board provider ABI or artifact packaging is frozen.  Accessibility/non-colour state remains a future acceptance requirement. |
| Generic fallback for a missing visual Resource while simulation continues | `06` §33 | Needs decision | Language permits simulation without Resources.  The exact fallback appearance and diagnostic severity belong to the future Board contract. |

## Operation and Trace candidates

| Candidate requirement | v0.1 sources | Status | Reconciliation / conflict |
|---|---|---|---|
| Operations are independent requests: load, inject, run/step, probe/watch, inspect, validate, export | `01_Components_Component_Model_v0.1.md` Responsibilities and §§Inject–Probe; `03_JSON_Object_Model_v0.1.md` Operation; `07_Interpreter_Architecture_v0.1.md` Operations | Adopted | Language Component/Interpreter ownership already gives Operations this role.  Operations cannot add hidden topology or privately mutate a Device input. |
| Operation results return status, diagnostics, signals/state, and traces | `03_JSON_Object_Model_v0.1.md` Result/Diagnostics/Trace; `07` Board Relationship | Needs decision | Language freezes diagnostics and requested trace semantics, but not a public RPC/result envelope or revision protocol. |
| Inject supports ROM images, noise, glitches, faults, matrices, and time ranges | `01` Inject; `03` Operation; `07` Inject | Needs decision | Injection must become explicit typed operation schemas with permissions, deterministic values, source drivers, and reproducible file references.  It may never change topology. |
| Probe records transition history; watch is live observation | `01` Probe; `03` Trace; `07` Trace Store | Adopted | Language Object/Interpreter models define Probe, Timeline, deterministic trace/inspect, and runtime-owned trace storage.  `watch` remains UI vocabulary until a Board contract exists. |
| Time coordinates include tick, time, and event | `01` Time Model; `03` Time Coordinates; `07` Time Model/Event Queue | Needs decision | Language v1 canonically uses `(time, delta)` for deterministic execution.  A user-facing `tick` abstraction and an `event` coordinate need a mapping proposal; they must not weaken delay/delta ordering. |
| Canonical human-readable JSON corresponds to text notation | `01` JSON Philosophy; `03` Canonical Rules; `07` JSON Contract | Conflict / needs decision | Language v1 freezes JSON as resolved Object/Topology interchange, **not** serialized AST.  Text-to-JSON source parity would be a separate authoring-format proposal, not a change to the current runtime JSON contract. |

## Explicit conflicts to preserve

1. A Device definition supplies meaning and behavior; a Resource supplies
   presentation only.  The v0.1 examples must never be read as permission for
   `resource` fields to set direction, active level, timing, or simulation.
2. A Board can select presentation and issue Operations, but cannot create
   hidden electrical connections, mutate runtime state directly, or reconstruct
   missing traces.
3. Parser output remains AST only.  It must not resolve a Device, validate
   electrical behavior, construct topology, or execute an Operation.
4. Resolved/generated JSON is a reproducible output/cache.  It is not a
   manually edited source owner and is not an AST serialization format.
5. The event model remains `(time, delta)` with four-state resolution and
   bounded settling.  UI-oriented `tick` terminology cannot replace it.

## Next reconciliation gate

Before any deferred or needs-decision row is promoted, submit a small proposal
that names: owner, source format, resolved output (if any), consumer, backward
compatibility rule, and focused tests.  Do not begin Board implementation or
move existing package artifacts merely because a v0.1 document names them.
