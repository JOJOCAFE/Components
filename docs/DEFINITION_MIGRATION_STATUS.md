# Definition migration status

This is the concise inventory for typed compact Device migration. It lists only
packages with an explicit source, generated runtime record, and regression
proof; it does not imply that the rest of the library is migrated.

| Package | Device class | State | Generated runtime | Resource map | Gate |
|---|---|---|---|---|---|
| 74HC00 | digital | active | `generated/resolved.json` | DIP symbol | lossless Device + Resource proof |
| 74HC157 | digital | active | `generated/resolved.json` | DIP symbol | lossless Device + Resource proof |
| 74HC161 | digital | active | `generated/resolved.json` | DIP symbol | lossless counter Device + Resource proof |
| 74HC245 | digital | active | `generated/resolved.json` | DIP symbol | lossless tri-state Device + Resource proof |
| 74HC574 | digital | active | `generated/resolved.json` | DIP symbol | lossless clocked tri-state Device + Resource proof |
| AT28C256 | memory | active | `generated/resolved.json` | none yet | lossless asynchronous-memory adapter proof |
| Capacitor | passive | active | `generated/resolved.json` | none yet | lossless two-terminal Device proof |
| Resistor | passive | active | `generated/resolved.json` | none yet | lossless two-terminal Device proof |
| ClockSource | virtual | active | `generated/resolved.json` | none yet | lossless virtual runtime-adapter proof |
| Probe | virtual | active | `generated/resolved.json` | none yet | lossless legacy-contract and observer-runtime proof |

Run the non-mutating gate before changing this table or activating another
package:

```bash
PYTHONPATH=python python3 tools/check_definition_migration.py
```

The command rejects missing or stale generated runtime JSON, invalid Resource
links, and a Resource that leaks into resolved Device data. A Resource is a
presentation map only; it cannot supply pin truth, timing, behavior, evidence,
or status. See [Definition ownership v0.1](DEFINITION_OWNERSHIP_V0_1.md).
