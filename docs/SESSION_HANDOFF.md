# Components Session Handoff

Last updated: 2026-08-12

## Session 2026-08-12 (evening) — Component Language Full Model + Verilog Export

### What was done

Complete component:component language model extension, 28 circuit conversions
to `.component` format, Verilog export verification, and full audit/fix cycle.

### Language specs written (specs 24-27)

| Spec | Content |
|------|---------|
| 24_Stimulus_Model.md | input, clock, channel, step, reset, derive, memory, sequence, release, repeat, clock_profile |
| 25_Virtual_Device_Catalog.md | 9 virtual devices (ClockSource, Switch, Probe, BusProbe, BusDriver, OutputAssert, RCParasitic, DelayNoise, SequenceGenerator, LogicAnalyzer) |
| 26_Hierarchy_and_Composition.md | port boundary, instance sub-circuit, namespacing, recursive composition |
| 27_Safety_and_Timing_Contracts.md | bus_safety, policy, edge_criteria, timing_check, extended assert modes |

### Circuit conversions

- 5 standalone: nand, counter, bus_transceiver, memory_read, tiny_cpu_slice
- 23 RV8GR: all circuits from RV8GR_RingCounter through RV8GR_WholeSystemChipLevelVirtual
- Total: 28 `.component` files, ~8000 lines, 150 tests

### Verilog export verification

- Tool: `tools/component_to_verilog.py`
- 25 circuits export to valid Verilog (all compile with iverilog)
- 3 virtual-only (hierarchy compositions) correctly skipped
- 70/70 behavior crosscheck rows pass

### Board enhancements

- `app.html`: Added `?load=` URL param for .component file loading
- `app.html`: Added stimulus panel (clocks/channels/presets/steps/probes in terminal)
- `src/model/file.js`: Added `instance` line parsing (treats as device for rendering)
- Board tests: 885 passed, 0 failed

### Audit and fixes

- Fixed library locators (digital.AT28C256 → memory.AT28C256) in 3 files
- Fixed edge_criteria syntax (trigger_edge → trigger) in all files
- Fixed virtual device missing params (width, period_ns) in ~10 files
- Fixed device child.X → instance syntax in BootSequenceTrace
- Added virtual.OutputAssert to spec 25 catalog
- Updated Language/README.md with specs 24-27

### Test results

- Board engine: 885 passed, 0 failed
- Python: chips, design, contracts, simulation, equivalence, db, cli, netlist — all pass
- Verilog: 74xx smoke PASSED, memory smoke PASSED
- Verilog crosscheck: 70 rows, 0 failures
- Component parse: 28/28 files pass Board parser

### Resume notes (next session)

1. **Implement parser/resolver** for new language features (port, instance,
   channel, derive, clock, input, reset, sequence) in `component_language.py`.
2. **Board stimulus execution** — make the stimulus panel interactive (click
   channels, run steps, animate signal flow through viewport).
3. **First-sight student trial** — Board with loaded RV8GR circuit.
4. **Convert remaining specs to formal grammar** — the AST model (spec 03)
   needs extension nodes for specs 24-27.

### Evidence commands
```bash
# All Board tests:
cd /home/jo/kiro/Components/board
for f in test/*.test.js; do node "$f"; done

# Python tests:
cd /home/jo/kiro/Components/python
python3 -B -m tests.test_chips
python3 -B -m tests.test_contracts
python3 -B -m tests.test_netlist

# Verilog export check:
cd /home/jo/kiro/Components
PYTHONPATH=python python3 tools/component_to_verilog.py --all

# Serve Board:
cd /home/jo/kiro/Components
python3 -c "from http.server import HTTPServer, SimpleHTTPRequestHandler; SimpleHTTPRequestHandler.extensions_map['.component']='text/plain'; HTTPServer(('0.0.0.0',8080),SimpleHTTPRequestHandler).serve_forever()"
# Open: http://127.0.0.1:8080/board/app.html?load=/examples/circuits/RV8GR_RingCounter/circuit.component
```

---

## Session 2026-08-12 — Board Interactive Wiring + Real Scale

### What was done

Full interactive Board session: boundary cleanup, zoom+pan, grid snap,
guide/connect tools, real DIP scale, HTTP adapter, and pin visualization.
9 commits pushed to main (98accb5..bef2ba7).

### Boundary cleanup (Fern-verified)

- `executor.js`: removed `component.js` import, inlined trivial model ops as
  local undo/redo shadow. Only `engine-mock.js` imports component.js now.
- `app.html`: removed `twin-sync.js` dependency, replaced with inline
  state-to-text helpers using file.js serializers.
- Fern verified all engine-interface.md section 7 checklist items pass.

### New features

| Feature | How |
|---------|-----|
| Zoom + Pan | Ctrl+scroll=zoom (pointer-anchored), scroll=pan, shift+scroll=pan horizontal, middle-drag=pan |
| Undo/Redo | Ctrl+Z / Ctrl+Y / Ctrl+Shift+Z |
| Grid snap | Dots at intersections, dashed green ghost at snapped position during drag |
| Guide tool (G) | Click device toggles connection visibility. Diagonal green line + edge label. Hidden by default. |
| Connect tool (W) | 90° orthogonal only (KiCad style). Pin-to-pin targeting. Live L-shaped preview. Turning points on empty space click. Escape cancels. |
| Auto-pan | During connect, cursor near edge (40px) auto-pans viewport |
| Pin visualization | Selected device shows pin labels (number + name) at real DIP positions |
| HTTP adapter | `engine-http.js` — connects Board to real Python API via `?engine=http` |
| Real DIP scale | 2.54mm pin pitch, 7.62mm narrow / 15.24mm wide. Renders at true mm scale. |
| Max zoom 5000% | 50x magnification for pin-level detail |
| RingCounter example | Real RV8GR circuit (U8 74HC164 + U24 74HC04) loaded by default |

### New files

| File | Purpose | Status |
|------|---------|--------|
| `src/engine-http.js` | HTTP adapter for real Python Components API | Permanent |

### Modified files

| File | Change |
|------|--------|
| `src/controller/executor.js` | Removed component.js import, inlined model ops |
| `src/view/viewport.js` | Added `zoomAtPoint`, `panByScreenDelta`, MAX_ZOOM=5000 |
| `test/viewport.test.js` | +14 zoom+pan tests |
| `app.html` | All interactive features wired (guide, connect, grid, pan, zoom, pins, real scale, example) |

### Test count

- Board: **885 passed, 0 failed** (19 test files)
- Core Python: all key suites pass (unchanged)
- Tag: `core-stable-2026-08-11` at `98accb5`

### Resume notes (next session)

1. **First-sight student trial** — the Board is now interactive enough to test
   with a 13-15 year old. Load it, place a chip, connect pins, toggle guides.
2. **HTTP adapter integration test** — start Python API, open
   `app.html?engine=http`, verify real pin data + resolve + run test.
3. **Pin-to-pin connect with real pin names** — when using HTTP adapter, connect
   tool should show pin name options (not just nearest-click).
4. **Route drag** — drag route bends to reshape existing routes (prototype had this).
5. **Label tool** — click blank space in Label mode to create/edit text labels.
6. **Save/Load real .component files** — File menu loads/saves component:component
   text to disk (currently uses localStorage only).
7. **Multi-chip example** — load RV8GR_AluAccumulator or RV8GR_FetchCycleTrace
   (5-8 chips) to test larger layouts.
8. Or switch lanes: RV8-GR physical build prep, RV8-R architecture.

### Evidence commands
```bash
# All 1274 Board tests:
cd /home/jo/kiro/Components/board
for f in test/*.test.js; do node "$f"; done

# Core Python gate:
cd /home/jo/kiro/Components/python
python3 -B -m tests.test_chips
python3 -B -m tests.test_design
python3 -B -m tests.test_contracts

# Serve Board:
cd /home/jo/kiro/Components/board && python3 -m http.server 8080
# Open: http://127.0.0.1:8080/app.html

# With real engine:
PYTHONPATH=python python3 -B -m chiplib.api --http --host 127.0.0.1 --port 8765
# Open: http://127.0.0.1:8080/app.html?engine=http

# Git log:
# bef2ba7 Board: load RV8GR RingCounter example, default zoom 500%
# 800bd67 Board: max zoom 5000%
# 0b6f749 Board: real DIP package scale
# 9fb090e Board: wheel=pan, Ctrl+wheel=zoom
# c793332 Board: auto-pan viewport when connect line reaches edge
# b9f3c0e Board: connect 90° pin-targeted, guide diagonal toggle-only
# 54efb0d Board: guide toggle, connect draw-line preview, grid snap
# afbb2c7 Board: grid snap visual, HTTP adapter, pin visualization
# 387a36e Board: boundary cleanup, zoom+pan, undo/redo
```

---

## Session 2026-08-04 (late) — Engine Interface / Thin-Client Refactor

### What was done

Board now communicates with the Components engine through a single
**EngineInterface** boundary. Board reads state, writes `component:operation`
objects. It never touches component.js or file.js directly.

Architecture decision: **Board reads state, writes operations.**
- Reads: devices, edges, sourceText, diagnostics (via `getState()`)
- Writes: `{ kind, target, intent }` operations (via `submit()`)
- Revision-checked: stale operations are rejected with a clear error

### Test count

- **1260 passed, 0 failed** (24 test files)

### Resume notes

Superseded by session 2026-08-12 above.
