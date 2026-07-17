# Board v2 deterministic fixture corpus

This is data for Board v2 acceptance tests, not Board implementation.  Each
case has one readable Component source plus three separate expectations:

- `*.resolved.expectation.json` records the resolved topology contract;
- `*.resource-bindings.expectation.json` records presentation-only bindings;
- `*.board-projection.expectation.json` records the read-only projection the
  Board may draw.

`manifest.json` is the index and fixes the canonical topology-digest algorithm.
Each `*.topology-projection.json` is the complete hash input, so a checker does
not need to reconstruct it from prose or runtime output. It deliberately
excludes source paths, spans, Board coordinates, and SVG geometry. The
resulting digest is a stable topology identity for stale-profile tests, not a
physical or timing signature.

All Board edges in this corpus are scalar.  Resource records name an existing
local presentation asset and its content digest, but remain expectations until
the Resource Definition contract publishes a matching resource record.  Pin,
direction, behavior, timing, and electrical ownership remain resolved-library
facts; no expectation here is an alternate device definition.

Cases:

- `not_gate`: baseline Clock -> 74HC04 -> Probe route.
- `chain_4`: exactly four declared devices in a three-inverter chain.
- `dense_16x32`: exactly sixteen 74HC04 instances and thirty-two scalar edges
  across four acyclic layers.  It is a deterministic projection/load fixture,
  not an executable timing or breadboard claim.
