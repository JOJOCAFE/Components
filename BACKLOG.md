# Components Backlog

Future work for the shared component library.

## Deferred UI Work

- Build a visual chip-block editor where users can place DIP chip blocks on
  screen, wire pins/nets, and run either the Python simulator or Verilog
  simulation backend.

## Backend Probe And Test Logic

- Add reusable probe channels for simulator tests and future UI inspection.
- Probes should attach to chip pins or named nets, sample logic values over
  simulated time, and expose serializable state for web or Python frontends.
- Add assertion/test helpers that can check expected `0`, `1`, `Z`, `X`,
  rising/falling transitions, pulse counts, and timing windows against the
  Python simulator.
- Keep probe logic backend-only and independent from the future visual editor.

Notes:

- This is intentionally deferred.
- Current priority remains the backend component library: Python chip behavior,
  pin-number/name access, propagation delay, memory models, and Python/Verilog
  compatibility.
- The UI should consume the backend library instead of duplicating chip
  behavior.
- The backend must stay frontend-agnostic. It should be usable from a JavaScript
  web UI through an API/service wrapper, or directly from a Python-native UI,
  without changing chip behavior code.
- Future UI work should treat the backend as a simulator service: create chips,
  expose pin metadata, connect nets, step/settle clocks, probe pins/nets, and
  return serializable state for drawing.
