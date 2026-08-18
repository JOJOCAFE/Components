# Components Session Handoff

Last updated: 2026-08-18

## Session 2026-08-18 — CLI Trace Viewer Complete + Bug Fixes

### What was done

Cleared all pending items then completed the full CLI Trace Viewer Plan (all 4 phases). Fixed 7 parse bugs, wired U34 integration path, fixed trace engine phase auto-drive, added MCP tool + diff mode + lab scripts.

### Commits (1 today)

```
05efd10 CLI trace viewer complete: phase auto-drive, MCP tool, diff mode, lab scripts
```

### Results

| Metric | Start | End |
|--------|-------|-----|
| Circuit tests | 137/137 (100%) | **137/137 (100%)** |
| Trace tests | 6/6 | **6/6** |
| Verilog crosscheck | 70/70 | **70/70** |
| MCP tools | 9 | **10** (+ trace_circuit) |
| CLI Trace Viewer Plan | Phase 1-2 done | **All 4 phases complete** |

### Bug fixes

| Fix | Files affected |
|-----|---------------|
| 7 same-line parse bugs (`-- Power  connect...`) | AddressMux16, BootSequenceTrace, BusOwnership, FetchCycleTrace, InterruptEnable, PageDataRegisters, StorePath |
| U34 Y-output wiring (IRL→U34→IBUS integration) | Lab13MarkerTrace (tests updated: `set irl` + `set irl_oe_n = 0` instead of `set ibus`) |
| Trace formatter `val==2` treated as Z | trace_format.py (was corrupting PC display) |

### CLI Trace Viewer features added

| Feature | What it does |
|---------|--------------|
| Phase auto-drive | Detects `phase_t0/t1/t2` input presets, cycles them T0→T1→T2 |
| Deferred clock edges | `defer_clocks=True` lets bus settle before latches fire |
| Phase-aware annotation | Notes show `T0: fetch $30 (LI)`, `T1: fetch $42`, `T2: LI $42` |
| `trace_circuit` MCP tool | 10th MCP tool — trace from AI with steps/probes/program/annotate |
| `--diff golden.json` | Compare trace against reference, exit 0/1, formatted report |
| Lab scripts (12) | `scripts/trace_lab02.sh` through `trace_lab13.sh` |

### Verification (pending items cleared)

| Team | Task | Result |
|------|------|--------|
| Mint | Verilog behavior crosscheck | ✅ 70/70, 0 failures |
| Fern | WholeSystem test coverage | ✅ 9/9 tests pass (structural+composition) |
| Ohm | Same-line parse bug audit | ✅ 7 found and fixed |
| Ohm | U34 Y-side wiring status | ✅ Lab13MarkerTrace fully wired as integration proof |

### Git state

```
main ← 05efd10 (pushed to origin)
```

### Team next-steps (Pim routing)

**Next session: ADVISOR PRESENTATION**

The CLI Trace Viewer is now the primary demo tool. Show:
1. `bash scripts/trace_lab02.sh` — ring counter phases (2 chips)
2. `bash scripts/trace_lab06.sh` — IR latch capturing opcodes (9 chips)
3. `bash scripts/trace_lab13.sh` — full program execution with annotation (9 chips)
4. `--diff golden.json` — student verification workflow
5. `--format json` — AI-consumable output
6. Board interactive + all 137 circuit tests pass
7. Gap analysis: what's missing for classroom (see below)

**Classroom readiness gap analysis:**
- ✅ Learning path: Lab 01→14, progressive (2→35 chips)
- ✅ CLI trace: students run `bash scripts/trace_labNN.sh` before building
- ✅ Board viewer: interactive, loads .component files
- ✅ 137/137 tests pass, 70/70 Verilog crosscheck
- ⚠️ Labs 03,04,07-12 trace scripts show static data (circuits lack phase presets) — works for demo but not ideal for students
- ⚠️ Student guide not yet updated with "simulation check" sections
- ⚠️ No Thai localization in CLI output yet
- ⚠️ Physical build not started (parts not ordered)

**Bam (SW):**
- MCP trace_circuit tool ready for live test
- Consider adding phase presets to PC16, AluAccumulator, etc. for full lab trace coverage
- `repeat` statement support still pending

**Noon (Docs):**
- Add "simulation check" section to each lab: "ก่อนต่อวงจร ให้รัน: `bash scripts/trace_labNN.sh`"
- Student guide update with new trace workflow

**Ohm (HW):**
- Physical build prep: parts ordering, BOM check
- Labs 03,04,07-12 circuits could benefit from phase presets (low priority)

**Bank (Architect):**
- RV8-R architecture design (when ready, parked)
- Consider: should intermediate circuits get phase presets or should students always use FetchCycleTrace for execution demos?

### Evidence commands

```bash
# Full demo:
cd /home/jo/kiro/Components
bash scripts/trace_lab02.sh    # Ring counter
bash scripts/trace_lab06.sh    # IR latch + fetch
bash scripts/trace_lab13.sh    # Full program execution

# JSON for AI:
PYTHONPATH=python python3 -m chiplib.cli trace \
  examples/circuits/RV8GR_FetchCycleTrace/circuit.component \
  --steps 9 --format json --annotate --program "LI \$42; ADDI \$01; SUBI \$43"

# Diff mode:
PYTHONPATH=python python3 -m chiplib.cli trace \
  examples/circuits/RV8GR_RingCounter/circuit.component \
  --steps 6 --format json > /tmp/golden.json
PYTHONPATH=python python3 -m chiplib.cli trace \
  examples/circuits/RV8GR_RingCounter/circuit.component \
  --steps 6 --diff /tmp/golden.json

# Full test suite:
cd /home/jo/kiro/Components/python
python3 -B -m tests.test_trace
python3 -B -c "
import sys,warnings; warnings.filterwarnings('ignore')
from pathlib import Path
from chiplib.component_language import parse_component_file, resolve_component
from chiplib.component_runtime import ComponentRuntimeSession
ROOT=Path('..')
p=t=0
for f in sorted(ROOT.glob('examples/circuits/*/*.component')):
    ast=parse_component_file(f)
    if not ast.get('ok'): continue
    resolved=resolve_component(ast)
    if not resolved or not resolved.get('ok'): continue
    for test in resolved.get('tests',[]):
        t+=1
        try:
            s=ComponentRuntimeSession(resolved)
            if s.run_declared_test(test['id']).get('ok'): p+=1
        except: pass
print(f'{p}/{t}')
"

# MCP server:
PYTHONPATH=python python3 -B -c "from chiplib.mcp_server import TOOLS; print(len(TOOLS), 'tools')"

# Verilog crosscheck:
PYTHONPATH=python python3 -B tools/verilog_behavior_crosscheck.py
```
   port boundaries at simulation time.

### Commits (2 today)

```
dc24666 Runtime: hierarchy flatten — expand sub-circuit instances, bus-to-bus union, power prefix — 107/139 (77%)
aed1045 Board AI command channel: fix cache — no-store on /api/commands, no-cache on HTML
```

### Key changes

| Fix | Impact |
|-----|--------|
| `Cache-Control: no-store` on `/api/commands` GET | Browser no longer caches empty command queue |
| `Cache-Control: no-cache` on HTML files | App.html always fresh during dev |
| `cache: 'no-store'` on fetch in poller | Client-side belt-and-suspenders |
| `_flatten_hierarchy()` function | Expands `instance` declarations into real chips |
| Bus-to-bus bit-level union | `connect alu.AC -> ac;` properly unions all 8 bits |
| Power rail prefix detection | `alu.vcc` / `ieff.gnd` recognized as VCC/GND rails |
| z_flag test data fix | `expect z_flag == 0` → `== 1` in reset (AC=0 → Z=1 is correct) |

### Hierarchy flatten implementation

- New function `_flatten_hierarchy(resolved, depth)` in `component_runtime.py`
- Recursively resolves sub-circuit `.component` files from `examples/circuits/`
- Prefixes all devices, nets, buses, edges with instance name
- Builds port-to-internal-net mapping from sub-circuit boundary edges
- Rewrites parent edges that target `instance.PORT` to point at prefixed internal net
- Bus-to-bus edges expanded to bit-level unions in `_build()`
- Depth limit 16, caching per source_ref to avoid redundant parsing

### Results

| Metric | Before | After |
|--------|--------|-------|
| Runtime test pass | 99/139 (71%) | 107/139 (77%) |
| Fully passing circuits | 15/23 | 15/23 |
| Regression suites | 12/12 green | 12/12 green |
| Build errors | 0 | 0 |

Newly passing tests (8): ei_sets_ie, beq_taken_z1, jump_unconditional,
setpg_12 (FullControlOpcodeSweep), + 4 from WholeSystemChipLevelVirtual
that were blocked by z_flag test data.

### Remaining 32 failures (circuit data path gaps)

These are NOT hierarchy bugs — the flatten works correctly. The tests fail
because the partial circuits lack data path components:

- **IBUS not driven** (no U34 IRL→IBUS buffer): li_42_z0, setdp_80, bne_taken_z0,
  most Lab13/PageJump/StoreLoadBranch tests
- **No ROM model**: BootSequenceTrace needs ROM to feed opcodes
- **Bus conflict**: full_sweep_512_deterministic tries to externally drive z_flag
  while U21 already drives it
- **Derives not modeled**: forbidden_opcode_detected needs complex derive eval

To push beyond 77%, these circuits need either:
1. Add U34 (74HC541 IBUS buffer) to circuits that test opcode execution, OR
2. Add explicit `set ibus = <value>` to test presets alongside `set irl`

### Test results

- All 12 existing suites pass (chips, design, contracts, netlist, cli, api, db,
  simulation_service, equivalence, generated_split_records, virtual_runtime,
  lib_circuit_campaign)

### Git state

```
main ← dc24666 (pushed to origin)
Commits today (2):
dc24666 Runtime: hierarchy flatten — expand sub-circuit instances, bus-to-bus union, power prefix — 107/139 (77%)
aed1045 Board AI command channel: fix cache — no-store on /api/commands, no-cache on HTML
```

### Resume notes (next session)

1. **Push past 77%** — add `set ibus = <value>` to test presets in
   FullControlOpcodeSweep/Lab13/PageJump/StoreLoadBranch circuits (quick fix)
2. **Board AI channel live test** — channel now works without incognito; test with
   `curl -X POST http://127.0.0.1:8765/api/commands -d '["place U1, 74HC04 at (80,80)"]'`
3. **MCP server live test** — restart Kiro in Components dir
4. **First-sight student trial** — Board interactive enough
5. Or switch lanes: RV8-GR physical build prep, RV8-R architecture

### Evidence commands

```bash
# Full campaign:
cd /home/jo/kiro/Components/python
python3 -B -c "
import sys,warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'.')
from pathlib import Path
from chiplib.component_language import parse_component_file, resolve_component
from chiplib.component_runtime import ComponentRuntimeSession
ROOT=Path('..')
p=t=0
for f in sorted(ROOT.glob('examples/circuits/*/*.component')):
    ast=parse_component_file(f)
    if not ast.get('ok'): continue
    resolved=resolve_component(ast)
    if not resolved or not resolved.get('ok'): continue
    for test in resolved.get('tests',[]):
        t+=1
        try:
            s=ComponentRuntimeSession(resolved)
            if s.run_declared_test(test['id']).get('ok'): p+=1
        except: pass
print(f'{p}/{t}')
"

# Full regression:
cd /home/jo/kiro/Components/python
python3 -B -m tests.test_chips
python3 -B -m tests.test_design
python3 -B -m tests.test_contracts
python3 -B -m tests.test_simulation_service
python3 -B -m tests.test_equivalence
python3 -B -m tests.test_db
python3 -B -m tests.test_cli
python3 -B -m tests.test_api
python3 -B -m tests.test_netlist
python3 -B -m tests.test_generated_split_records
python3 -B -m tests.test_virtual_runtime
python3 -B -m tests.test_lib_circuit_campaign

# Board AI command channel test:
cd /home/jo/kiro/Components/python
setsid python3 -B -m chiplib.api --http --host 127.0.0.1 --port 8765 < /dev/null > /tmp/board_api.log 2>&1 &
sleep 1
curl -X POST http://127.0.0.1:8765/api/commands -H "Content-Type: application/json" -d '["place U1, 74HC04 at (80, 50)"]'
curl http://127.0.0.1:8765/api/commands
```
   Once visible, test: `curl -X POST http://127.0.0.1:8765/api/commands -d '["place X, 74HC04 at (80,80)"]'`
2. **MCP server live test** — restart Kiro in Components dir to pick up
   `.kiro/settings/mcp.json`, then use @components-board tools
3. **Hierarchy flatten** — only way to pass remaining 40 tests
4. **First-sight student trial** — Board is interactive enough
5. Or switch lanes: RV8-GR physical build prep, RV8-R architecture

### Git state

```
main ← 15279d1 (pushed to origin)
Commits today (8):
  15279d1 Board: AI command channel — API queue + browser poller
  2b7539d MCP server: add --api HTTP forwarding + Kiro workspace config
  4130459 MCP server: 9 tools for AI-Board interaction over stdio
  d5aee8c Session handoff: 2026-08-13 final — 99/139 (71%), 15/23 circuits green
  231526b Circuit tests: fix timing order + z_flag second pulse — 99/139 (71%)
  4e6f12c AluAccumulator: complete 8-bit data path + async preset update
  956e63c Runtime: derive-aware _probe_single, defer_clocks param on drive()
  74cb18b Runtime: derive-target resolution, NOT-mask fix, AluAccumulator z_flag wiring
  3f79898 Runtime: propagation-aware clock edges, graceful skip, derive resolution, assert extensions
```

### Evidence commands

```bash
# Start Board API:
cd /home/jo/kiro/Components/python
setsid python3 -B -m chiplib.api --http --host 127.0.0.1 --port 8765 < /dev/null > /tmp/board_api.log 2>&1 &

# Open Board: http://127.0.0.1:8765/app.html (incognito if cached)

# Push AI commands to Board:
curl -X POST http://127.0.0.1:8765/api/commands \
  -H "Content-Type: application/json" \
  -d '["place U1, 74HC04 at (80, 50)", "place U2, 74HC164 at (180, 50)", "connect U2.QA -> U1.1A", "route U2.QA -> U1.1A via (140, 55) (110, 55)"]'

# Test MCP server standalone:
cd /home/jo/kiro/Components/python
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python3 -B -m chiplib.mcp_server

# Runtime sweep:
cd /home/jo/kiro/Components/python
python3 -B -c "
import sys,warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'.')
from pathlib import Path
from chiplib.component_language import parse_component_file, resolve_component
from chiplib.component_runtime import ComponentRuntimeSession
ROOT=Path('/home/jo/kiro/Components')
p=t=0
for f in sorted(ROOT.glob('examples/circuits/*/*.component')):
    ast=parse_component_file(f)
    if not ast.get('ok'): continue
    resolved=resolve_component(ast)
    if not resolved or not resolved.get('ok'): continue
    tests=resolved.get('tests',[])
    for test in tests:
        t+=1
        try:
            s=ComponentRuntimeSession(resolved)
            if s.run_declared_test(test['id']).get('ok'): p+=1
        except: pass
print(f'{p}/{t}')
"

# Full regression:
cd /home/jo/kiro/Components/python
python3 -B -m tests.test_chips
python3 -B -m tests.test_design
python3 -B -m tests.test_contracts
python3 -B -m tests.test_simulation_service
python3 -B -m tests.test_equivalence
python3 -B -m tests.test_db
python3 -B -m tests.test_cli
python3 -B -m tests.test_api
python3 -B -m tests.test_netlist
python3 -B -m tests.test_generated_split_records
python3 -B -m tests.test_virtual_runtime
python3 -B -m tests.test_lib_circuit_campaign
```

### Evidence commands

```bash
# Runtime sweep:
cd /home/jo/kiro/Components/python
python3 -B -c "
import sys; sys.path.insert(0,'.')
from pathlib import Path
from chiplib.component_language import parse_component_file, resolve_component
from chiplib.component_runtime import ComponentRuntimeSession, ComponentRuntimeError
ROOT = Path('..')
total=passed=0
for f in sorted(ROOT.glob('examples/circuits/*/*.component')):
    ast = parse_component_file(f)
    if not ast.get('ok'): continue
    resolved = resolve_component(ast)
    if not resolved or not resolved.get('ok'): continue
    tests = resolved.get('tests', [])
    if not tests: continue
    try: session = ComponentRuntimeSession(resolved)
    except: total += len(tests); continue
    for t in tests:
        total += 1
        try:
            if session.run_declared_test(t['id']).get('ok'): passed += 1
        except: pass
print(f'{passed}/{total}')
"

# Full regression:
cd /home/jo/kiro/Components/python
python3 -B -m tests.test_chips
python3 -B -m tests.test_design
python3 -B -m tests.test_contracts
python3 -B -m tests.test_simulation_service
python3 -B -m tests.test_equivalence
python3 -B -m tests.test_db
python3 -B -m tests.test_cli
python3 -B -m tests.test_api
python3 -B -m tests.test_netlist
python3 -B -m tests.test_generated_split_records
python3 -B -m tests.test_virtual_runtime
python3 -B -m tests.test_lib_circuit_campaign
```

---

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

1. **Runtime test pass rate** — currently 41/101 pass. Fix:
   - Skip virtual/hierarchy devices in `_build()` (fixes 9 build errors)
   - Fix probe name mismatches (tests reference names not in observations)
   - Trace clock pulse routing for counter/sequential circuits
2. **Board stimulus execution** — make stimulus panel interactive
3. **First-sight student trial** — Board with loaded RV8GR circuit
4. **9 compact-schema chips → v1** — cosmetic consistency (tracked in docs/DEFINITION_MIGRATION_STATUS.md)

### Git state
```
main ← 2ba8638 (pushed to origin)
tag: v0.1-language-stable ← b6797ce

Commits today (4):
  2ba8638 Runtime: extend test executor with full stimulus support
  36a2d27 Docs: add Language/ to Layout, fix test counts, add specs 24-27 refs
  a2a5f38 v0.2: Clean parser architecture for community readability
  b6797ce Component Language v0.1: full parse+resolve pipeline, 28 circuits, 4 specs
```

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
