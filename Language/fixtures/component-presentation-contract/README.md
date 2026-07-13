# Presentation-contract fixtures

These are schema and ownership fixtures for the deferred C3 Resource binding
and C4 Board profile contracts.  They are not Component source, executable
topology, Board rendering, or physical evidence.

- `resource-binding.valid.json` binds labels/views to targets in a locked,
  already-resolved Component.
- `board-profile.valid.json` consumes the same topology identity and uses only
  existing target/edge references.
- `negative-ownership.json` must reject attempts to redefine electrical truth.

Run `python3 -B tools/check_component_presentation_contracts.py`.
