# Presentation-contract fixtures

These are schema and ownership fixtures for the deferred C3 Resource binding
and Resource Definition contracts plus the C4 Board profile contract.  They
are not Component source, executable topology, Board rendering, or physical
evidence.

- `resource-definitions.valid.json` provides safe text, 2D, and optional 3D
  views.  It is selected by the matching IDs/digests/views in the binding
  fixture.
- `resource-binding.valid.json` binds labels/views to targets in a locked,
  already-resolved Component.
- `board-profile.valid.json` consumes the same topology identity and uses only
  existing target/edge references.
- `negative-ownership.json` must reject attempts to redefine electrical truth.

Run `python3 -B tools/check_component_presentation_contracts.py`.
