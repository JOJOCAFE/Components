# Components Service Architecture Tasks

Goal: keep `Components` as one coherent repo while making chip behavior,
simulation, exporters, CLI, API, and future UI integration depend on stable
contracts instead of direct file coupling.

## Direction

Do not split into many external processes yet. First split by internal module
boundary and JSON/API contract:

```text
schematic JSON
    -> normalized Design model
        -> simulation service
        -> netlist service
        -> Verilog export service
        -> CLI/API/front-end adapters
```

The first hard boundary is the normalized `Design`/netlist contract. Python is
the reference implementation for now. Rust, C, or C++ engines can be added later
only if they consume the same normalized inputs and return the same structured
outputs.

## Task List

1. ⬜ Define package boundaries without moving code yet.
   - `db`: per-chip manifests used as the chip identity DB during
     migration.
   - `chipdb`: chip metadata, pinout evidence, package/pin descriptions.
   - `behavior`: Python physical pin-level chip behavior.
   - `design`: schematic JSON parsing and normalized `Design`.
   - `sim`: board/net/bus/probe/clock simulation runtime.
   - `exporters.verilog`: structural Verilog/testbench export.
   - `exporters.netlist`: normalized netlist import/export.
   - `cli`: command-line adapter over the same APIs.
   - `api`: future HTTP/RPC/service wrapper.

2. ⬜ Write the service contract document.
   - Inputs: schematic JSON, normalized design JSON, normalized netlist JSON.
   - Outputs: validation report, snapshot, simulation result, probe result,
     netlist export, Verilog export, equivalence report.
   - Error shape: stable machine-readable code, message, severity, location,
     and suggested fix.

3. ⬜ Freeze the normalized netlist schema as the first plugin boundary.
   - Every exporter or external engine must read this schema.
   - No exporter should parse student schematic JSON directly unless it goes
     through `Design`.

4. ⬜ Refactor Verilog export behind an internal service interface.
   - Keep current behavior unchanged.
   - Move exporter-specific mapping logic behind a narrow function/class.
   - Return structured export data: `ok`, `verilog`, `testbench`,
     `unsupported`, `warnings`, and `required_files`.

5. ⬜ Refactor simulation behind an internal service interface.
   - Input: normalized `Design` plus run options.
   - Output: serializable snapshot, probe history, display state, warnings,
     errors, and timing metadata.
   - Keep Python `Board` as the reference engine.

6. ⬜ Make CLI commands call service interfaces only.
   - CLI should not know chip internals.
   - CLI should print JSON for machine use and readable summaries for humans.

7. ⬜ Add contract tests.
   - Same fixture JSON should validate, snapshot, export netlist, export
     Verilog when supported, and run through simulation.
   - Use examples as regression fixtures.

8. ⬜ Add service-ready examples.
   - `examples/nand.json`
   - `examples/counter.json`
   - `examples/bus_transceiver.json`
   - `examples/memory_read.json`
   - `examples/tiny_cpu_slice.json`

9. ⬜ Add a future external-engine adapter plan.
   - Define how a Rust/C/C++ simulator would be invoked.
   - It must accept normalized netlist/design JSON and return the same
     simulation-result JSON shape.
   - Keep this as a plan until Python performance or correctness limits are
     proven.

10. ⬜ Add an API wrapper only after CLI contracts are stable.
    - Candidate: local HTTP server or stdio JSON-RPC.
    - API should expose the same operations as CLI/service interfaces:
      validate, snapshot, run, probe, export-json, export-netlist,
      export-verilog, and check-equivalence.

## Next Implementation Rule

Start with contracts and tests, then move code. A module move is only safe when
the CLI and tests prove the public behavior did not change.
