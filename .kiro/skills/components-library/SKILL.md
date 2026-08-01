# Components Library — Skill Reference

## Project
- Repository: https://github.com/JOJOCAFE/Components
- Path: /home/jo/kiro/Components
- Audience: Students 10–15 years old (usable by older learners up to ~25)

## Mission
- Shared 74HC/memory component library for education
- Preserve datasheet truth, real pin behavior, active-low naming, timing limits, tri-state rules, and bus ownership
- Keep DB definitions, Python behavior, Verilog export, pinout evidence, tests, docs, and circuit examples aligned

## Source of Truth
- `definition/definition.json` + manufacturer datasheet PDF = authoritative
- Generated Python, Verilog, KiCad, SVG, docs, tests, and demos are derived — never authoritative alone
- Compact DB source files: don't duplicate derivable layers

## Team (7-person model)

| Name | Role | Scope |
|------|------|-------|
| Pim | Coordinator | Route tasks, cross-file alignment, commits, pushes |
| Bank | Architect | Schema, package boundaries, service contracts |
| Fern | Verifier | Regression, timing/bus proof, release confidence |
| Mint | RTL Coder | Verilog models, structural export, HDL benches |
| Ohm | HW Coder | Pinout truth, DIP evidence, breadboard realism |
| Bam | SW Coder | Python chiplib, CLI/API, circuit simulation, Board |
| Noon | Docs Writer | Student guides, examples, labels, labs |

## Repo Layout
```
Components/
├── lib/standard/          Chip definitions (definition.json per family)
├── python/chiplib/        Python behavior models + core.py
├── python/tests/          Python test suite
├── verilog/74xx/          Verilog structural models
├── verilog/memory/        Memory chip Verilog
├── source/                Manufacturer datasheet PDFs
├── examples/circuits/     RV8GR and standalone circuit examples
├── board/                 Visual Board tool (JS, MVC)
├── Language/              Component-source language spec (23+ docs)
├── tools/                 Crosscheck and audit scripts
├── schemas/               JSON schemas
├── docs/                  Team docs, agent skills, design plans
└── .codex/instructions.md Codex agent instructions
```

## Non-Negotiable Rules
1. No specialist verifies only their own work — Fern reviews what ships
2. DB, Python, Verilog, pinout evidence, and docs must not drift apart
3. Missing properties allowed only when visible in status/task docs
4. Active `simulation/model.py` must run standalone with only `chiplib/core.py`
5. Pinouts require manufacturer datasheet + explicit DIP package proof
6. Student clarity is a hard requirement, not a polish pass
7. Edge criteria required: clocked chips prove active-edge + no-edge hold; tri-state chips prove high-Z + no bus fight; memory chips prove read/write windows
8. Do not describe functional simulation as physical hardware signoff

## Board Tool Architecture (Frozen)
- Component source owns `device`/`net`/`bus`/`connect` — Board never alters topology
- Board profile: digest-locked positions + visual paths for resolved scalar edges
- Guides: session-only semantic toggles (never alternate topology editor)
- Labels: text editing in Label mode, move/resize in Select mode
- MVC: app.js (controller) → model.js + views/ + tools/
- UI v1.0 RC1: Macintosh spirit, max circuit area, grayscale + green accent, 8-tool rail
- Architecture: Screen → Viewport → centered World → snap/selection → semantic operation → transaction queue → validation → update → re-render
- Profile v2: centered Cartesian, finite unbounded world points, digest-locked topology, discrete rotation only
- Board v2 sprint: Gate 0 ✓, B1.1 ✓, B1.3 ✓, B2.1 ✓, B2.2 ✓, B2.3 (needs human observation)

## Component Language
- Additive to frozen Language v1.0
- Parser/resolver/runtime: `component-parse`, `component-resolve`, `component-validate`, `component-ide`, `component-student`, `component-run`
- Three layers: `component:component` (circuit), `component:board` (visual), `component:operation` (actions)
- Board and Operation layers deferred until source/runtime stable

## RV8GR Integration
- 36 board instances, 16 board-used part types, 18 RV8GR-ready definitions
- Circuits in `examples/circuits/` must carry: wiring data, proof vectors, Python tests, student docs
- Software coverage complete (boot, Lab 13, whole-system, mutation kills)
- Physical timing NOT proven — hardware signoff still pending
- Cross-repo: `COMPONENTS_ROOT=/home/jo/kiro/Components` for RV8GR verification

## Quality Gates
```bash
# Python tests
PYTHONPATH=python python3 -B -m pytest tests/ -q

# Component language
PYTHONPATH=python python3 -B -m tests.test_component_language

# Board tests
node board/interaction-contract.test.mjs
node board/profile-v2.test.mjs
node board/guide-operation.test.mjs

# Board API
PYTHONPATH=python python3 -B -m tests.test_component_board_api

# DB audit
PYTHONPATH=python python3 -B -m chiplib.cli db --audit

# Crosschecks
python3 tools/pinout_crosscheck.py
python3 tools/timing_crosscheck.py
python3 tools/python_behavior_crosscheck.py
python3 tools/verilog_behavior_crosscheck.py
```

## Datasheet Policy
- Prefer direct manufacturer PDFs proving DIP/PDIP/P-DIP/N-P package
- AllDatasheet only as locator when direct access unavailable
- Keep only final cited PDF in `source/`; remove failed downloads and duplicates
- 74HC150 and 74HC260 removed (no HC-family DIP evidence)

## Current Status (2026-07-27)
- Board MVC refactoring complete, UI v1.0 RC1 frozen
- Profile v2 migration deterministic, harness/regression baseline active
- Component language: parse/resolve/validate/run working
- Five active compact Device sources: 74HC00, 74HC161, 74HC157, 74HC245, 74HC574
- Functional-pinout SVGs: 74HC00, 02, 03, 04, 05, 08, 14 reviewed
- Next: implement frozen UI in index.html, Board human trial, Working Box/BOM

## Current TODO
- Implement frozen Board UI v1.0 RC1 in index.html (title bar, tab bar, status bar)
- Human first-sight trial (13-15 y/o learner + adult beginner)
- Working Box and atomic BOM preview (after add-declaration service)
- Bus-route contract (before visual bus bundle command)
- Fern browser flow review
