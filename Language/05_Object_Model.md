# Object Model v1.0

## Runtime objects

These are resolved runtime concepts, not parser nodes:

| Object | Meaning |
|---|---|
| DeviceDefinition | library-owned port/pin, behavior, timing, evidence truth |
| DeviceInstance | named use of one DeviceDefinition in a Component |
| Port | logical typed connection point of a DeviceDefinition |
| Pin | physical package point mapped to zero or more ports |
| Net | explicit named electrical/logical connectivity set |
| Bus | ordered collection of compatible signal members |
| Probe | explicit observation target with no implicit driver |
| Clock | typed signal source/event declaration |
| Timeline | ordered execution events and trace records |
| ResourceBinding | presentation reference unable to modify Device truth |

`DeviceDefinition` comes from Device Library compact/canonical definitions.
`ResourceBinding` comes from Resource Library files. Their ownership stays
separate as defined by
[docs/DEFINITION_OWNERSHIP_V0_1.md](../docs/DEFINITION_OWNERSHIP_V0_1.md).

## Identity and immutability

Every resolved object has a stable qualified ID and source provenance. A
DeviceDefinition is immutable during execution. DeviceInstance state belongs to
runtime instantiation, never to the library definition or AST. Generated
runtime JSON is resolver output/cache, not an editable source owner.

## Existing Components boundary

The present `definition/definition.json`, `resource/definition.json`, and
`generated/resolved.json` remain package-level contracts. This model names
future language objects; it does not require an immediate file-layout migration.
