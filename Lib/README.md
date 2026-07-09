# Components Library

`Lib/` contains reusable circuits and larger systems built from proven
component packages in `DB/`.

- `Circuits/` is for small reusable subcircuits such as counters, bus buffers,
  latch blocks, decoders, and timing generators.
- `Systems/` is for larger assemblies that combine multiple circuits.

Library entries are not replacement chip definitions. They are reusable wiring
patterns with their own proof records. Each circuit should identify the DB parts
it uses, the source project it came from, the exact wiring contract, and the
tests that prove the circuit behavior.
