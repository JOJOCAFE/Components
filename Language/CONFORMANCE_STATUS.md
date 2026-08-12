# Language Conformance Status

Last verified: 2026-08-12

## Architecture

```
language_definition.py  → Statement grammar as data (patterns, fields, categories)
parser_engine.py        → Generic parser engine (never changes)
statement_handlers.py   → One handler class per keyword (pluggable)
resolver_engine.py      → ResolutionContext + dispatch + validation
component_language.py   → Thin public API facade
```

## Implemented (parse + resolve)

| Spec | Feature | Parse | Resolve | Execute |
|------|---------|:-----:|:-------:|:-------:|
| 01 | `//`, `--`, `/* */` comments | ✓ | — | — |
| 01 | Identifiers with `/` (PortIdentifier) | ✓ | ✓ | — |
| 02 | `use X as Y;` imports | ✓ | ✓ | — |
| 02 | `component:component Name is Profile { }` | ✓ | ✓ | — |
| 17 | `device Name, Library.Part, {params};` | ✓ | ✓ (DB lookup) | — |
| 17 | `net name : kind;` | ✓ | ✓ | — |
| 17 | `bus name[width] : kind;` | ✓ | ✓ (member nets) | — |
| 17 | `connect endpoint -> endpoint;` | ✓ | ✓ (pin resolve) | — |
| 17 | `probe name, target;` / `watch` | ✓ | ✓ (read-only) | — |
| 17 | `display target as kind, {opts};` | ✓ | ✓ (binding) | — |
| 17 | `test name { body }` | ✓ | ✓ (stored) | deferred |
| 24 | `clock name, endpoint, {params};` | ✓ | ✓ (stored) | deferred |
| 24 | `channel name, endpoint, {params};` | ✓ | ✓ (stored) | deferred |
| 24 | `derive name = expr;` | ✓ | ✓ (creates net) | deferred |
| 24 | `release endpoint;` | ✓ | ✓ (stored) | deferred |
| 24 | `input name { }` | ✓ | ✓ (stored) | deferred |
| 24 | `reset name { }` | ✓ | ✓ (stored) | deferred |
| 24 | `step name { }` | ✓ | ✓ (stored) | deferred |
| 24 | `memory name { }` | ✓ | ✓ (stored) | deferred |
| 24 | `sequence name after X { }` | ✓ | ✓ (stored) | deferred |
| 24 | `clock_profile name { }` | ✓ | ✓ (stored) | deferred |
| 24 | `repeat count { }` | ✓ | ✓ (stored) | deferred |
| 25 | Virtual device resolution (ClockSource, Probe, etc.) | ✓ | ✓ | — |
| 25 | `bus_probe name, bus, {params};` | ✓ | ✓ | — |
| 26 | `port name : kind, direction;` | ✓ | ✓ (creates net) | — |
| 26 | `port name[width] : kind, direction;` | ✓ | ✓ (creates bus) | — |
| 26 | `instance name, ref;` | ✓ | ✓ (hierarchy) | — |
| 27 | `bus_safety name { }` | ✓ | ✓ (stored) | deferred |
| 27 | `policy name { }` | ✓ | ✓ (stored) | deferred |
| 27 | `edge_criteria name { }` | ✓ | ✓ (stored) | deferred |
| 27 | `timing_check name { }` | ✓ | ✓ (stored) | deferred |

## Resolver Validation (implemented)

| Check | Status |
|-------|--------|
| Duplicate symbol detection | ✓ |
| Import alias uniqueness | ✓ |
| Local-shadows-import | ✓ |
| Device locator against DB | ✓ |
| Library ownership (digital→74xx, memory→memory, etc.) | ✓ |
| Named port lookup | ✓ |
| Physical pin selector `@N` | ✓ |
| Quoted selector `"I/O0"` | ✓ |
| Power net isolation | ✓ |
| Multiple output driver detection | ✓ |
| Bus member bounds checking | ✓ |

## Resolver Validation (deferred)

| Check | Spec | When |
|-------|------|------|
| Width compatibility on bus connections | 17 step 7 | Runtime phase |
| Direction compatibility on connections | 17 step 7 | Runtime phase |
| Tri-state ownership validation | 17 step 7 | Runtime phase |
| Timing constraint checking | 17 step 7 | Runtime phase |
| Hierarchy port visibility enforcement | 26 | Hierarchy resolver |
| Recursive depth limit (16) | 26 | Hierarchy resolver |
| Interface lock/digest verification | 26 | Hierarchy resolver |
| Bus-to-bus scalar edge expansion | 17 step 6 | Runtime phase |

## Not Implemented (future phases)

| Spec | Feature | Phase |
|------|---------|-------|
| 09 | Interpreter (load→resolve→execute→trace) | Runtime |
| 10 | Event-loop simulation, 4-state resolution | Runtime |
| 15 | Runtime event kernel | Runtime |
| 16 | Operation protocol (inject/step/run/probe) | Runtime |
| 18 | RuntimeSession, DeviceInstance state | Runtime |
| 20 | `about { }` metadata block | System profile |
| 20 | `evidence { }` block | System profile |
| 20 | `timing contract { }` block | System profile |
| 20 | `test-suite "path"` reference | System profile |
| 02 | `component:schema`, `component:board`, `component:operation` | Multi-form parser |

## Language Extensions (beyond original spec)

These are implemented and in active use but were not in the frozen v1.0 spec:

| Extension | Rationale |
|-----------|-----------|
| `--` line comments | Ada-style, student-friendly, used in all 28 .component files |
| `/` in port identifiers | Datasheet-authentic active-low names without quoting |
| `watch` as probe alias | Fixture compatibility, more intuitive for beginners |
| Implicit `vcc`/`gnd` power rails | Convenience — avoids requiring power net declarations in every file |
| Bus-port prefix fallback | Pragmatic shorthand for `ROM1.A` → address bus group |
| `device X, Y` (comma form only) | v1.1 canonical syntax; `device X is Y` form is a deferred alternative |

## Test Evidence

```bash
# Parse + resolve all 28 circuits:
cd python && python3 -B -c "
from pathlib import Path
from chiplib.component_language import parse_component_text, resolve_component
files = sorted(Path('../examples/circuits').rglob('*.component'))
ok = sum(1 for f in files if resolve_component(parse_component_text(f.read_text(), source_name=f.name)).get('ok'))
print(f'{ok}/{len(files)} fully resolve')
"

# All Python tests:
python3 -B -m tests.test_chips
python3 -B -m tests.test_design
python3 -B -m tests.test_contracts
python3 -B -m tests.test_netlist
python3 -B -m tests.test_simulation_service
python3 -B -m tests.test_equivalence
python3 -B -m tests.test_db
python3 -B -m tests.test_cli

# Verilog export:
PYTHONPATH=python python3 tools/component_to_verilog.py --all
```
