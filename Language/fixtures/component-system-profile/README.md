# Component System Profile fixture

`rv8gr_whole_system.component` is the source-shaped complete-system
conformance fixture.  It is deliberately not a migration of
`examples/circuits/RV8GR_WholeSystemChipLevelVirtual/circuit.json`.

The paired `resolved-contract` file is not executable topology.  It proves
the required ownership split: Component has all machine-composition facts;
unpublished child interfaces, missing Devices, Operation execution, Board,
and physical signoff remain explicit deferred work.

Component is the source-shaped machine; Components is the library/runtime host
it will resolve against.  This fixture cannot claim that the complete machine
runs until child interfaces and the Components Runtime are implemented.

Run from the repository root:

```bash
python3 tools/check_component_system_profile.py
```
