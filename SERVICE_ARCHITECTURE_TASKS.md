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

1. ✅ Define package boundaries without moving code yet.
   - `db/`: canonical per-chip manifests, schema, status, source evidence,
     legacy implementation references, and DB-owned export metadata.
   - `chipdb`: Python DB access layer over `db/`; owns chip metadata,
     package/pin descriptions, status reports, audit checks, and capability
     queries. Current implementation: `python/chiplib/db.py`.
   - `behavior`: Python physical pin-level chip behavior and catalog-backed
     chip construction. Current implementation: `python/chiplib/chips.py` and
     `python/chiplib/catalog.py`.
   - `design`: schematic JSON parsing, normalized `Design`, round-trip JSON,
     and conversion into runtime boards. Current implementation:
     `python/chiplib/design.py`.
   - `sim`: board/net/bus/source/probe/clock simulation runtime. Current
     implementation: `python/chiplib/core.py` plus stimulus/probe helpers.
   - `exporters.verilog`: structural Verilog/testbench export and DB-backed
     pin-to-port mapping. Current implementation: `python/chiplib/netlist.py`.
   - `exporters.netlist`: normalized netlist import/export using
     `schemas/normalized-netlist.schema.json`. Current implementation:
     `python/chiplib/netlist.py`.
   - `cli`: command-line adapter over service-style APIs; it may format human
     output but should not own chip behavior, schema rules, or exporter logic.
     Current implementation: `python/chiplib/cli.py`.
   - `api`: future HTTP, stdio JSON-RPC, or frontend adapter that exposes the
     same contracts as `SERVICE_CONTRACT.md` without creating a second backend.
   - Boundary rule: these are ownership boundaries first. Do not move files
     into new packages until service interfaces and contract tests prove public
     behavior did not change.

2. ✅ Write the service contract document.
   - See `SERVICE_CONTRACT.md`.
   - Inputs: schematic JSON, normalized design JSON, normalized netlist JSON.
   - Outputs: validation report, snapshot, simulation result, probe result,
     netlist export, Verilog export, equivalence report.
   - Error shape: stable machine-readable code, message, severity, location,
     and suggested fix.

3. ✅ Freeze the normalized netlist schema as the first plugin boundary.
   - See `schemas/normalized-netlist.schema.json`.
   - Every exporter or external engine must read this schema.
   - No exporter should parse student schematic JSON directly unless it goes
     through `Design`.

4. ✅ Refactor Verilog export behind an internal service interface.
   - Current service boundary: `python/chiplib/services.py`
     `VerilogExportService`.
   - Keep current behavior unchanged.
   - Move exporter-specific mapping logic behind a narrow function/class.
   - Return structured export data: `ok`, `verilog`, `testbench`,
     `unsupported`, `warnings`, and `required_files`.

5. ✅ Refactor simulation behind an internal service interface.
   - Input: normalized `Design` plus run options.
   - Output: serializable snapshot, probe history, display state, warnings,
     errors, and timing metadata.
   - Keep Python `Board` as the reference engine.
   - Current service boundary: `python/chiplib/services.py`
     `SimulationService`.

6. ✅ Make CLI commands call service interfaces only.
   - CLI should not know chip internals.
   - CLI should print JSON for machine use and readable summaries for humans.
   - Current adapter: `DesignCommandService`, used by `python/chiplib/cli.py`.

7. ✅ Add contract tests.
   - Current coverage: `python/tests/test_contracts.py`.
   - Same fixture JSON should validate, snapshot, export netlist, export
     Verilog when supported, and run through simulation.
   - Use examples as regression fixtures.

8. ✅ Add service-ready examples.
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
