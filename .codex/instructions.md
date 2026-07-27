# Components — Codex Instructions

## Project

Shared 74HC/memory component library for education. Audience: students 10–15 years old.
Repo: chip definitions, Python behavior models, Verilog structural models, pinout evidence,
circuit examples, Board visual tool, and a Component-source language.

## Source of Truth

`definition/definition.json` + manufacturer datasheet PDF = authoritative.
Generated Python, Verilog, KiCad, SVG, and docs are derived — never authoritative alone.

## Team

| Name | Role | Scope |
|------|------|-------|
| Pim | Coordinator | Route tasks, cross-file alignment, commits |
| Bank | Architect | Schema, package boundaries, service contracts |
| Fern | Verifier | Regression, timing/bus proof, release confidence |
| Mint | RTL Coder | Verilog models, structural export, HDL benches |
| Ohm | HW Coder | Pinout truth, DIP evidence, breadboard realism |
| Bam | SW Coder | Python chiplib, CLI/API, circuit simulation, Board |
| Noon | Docs Writer | Student guides, examples, labels, labs |

## Rules

- No specialist verifies only their own work — Fern reviews what ships.
- DB, Python, Verilog, pinout evidence, and docs must not drift apart.
- Missing properties allowed only when visible in status/task docs.
- Active `simulation/model.py` must run standalone with only `chiplib/core.py`.
- Pinouts require manufacturer datasheet + explicit DIP package proof.
- Student clarity is a hard requirement, not a polish pass.
- Compact definition files: don't duplicate derivable layers.
- Edge criteria required: clocked chips prove active-edge + no-edge hold; tri-state chips prove high-Z + no bus fight; memory chips prove read/write windows.

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
├── board/                 Visual Board tool (JS)
├── Language/              Component-source language spec
├── tools/                 Crosscheck and audit scripts
├── schemas/               JSON schemas
└── docs/                  Team docs, agent skills, design plans
```

## Quality Gates

```bash
# Python tests
cd python && python3 -m pytest tests/ -q

# Verilog smoke (all 74xx + memory)
cd verilog && for f in 74xx/*/tb_*.v memory/*/tb_*.v; do iverilog -o /tmp/tb "$f" && /tmp/tb; done

# Pinout crosscheck
python3 tools/pinout_crosscheck.py

# Timing crosscheck
python3 tools/timing_crosscheck.py

# Python/Verilog behavior crosscheck
python3 tools/python_behavior_crosscheck.py
python3 tools/verilog_behavior_crosscheck.py

# Circuit virtual physical checker
PYTHONPATH=python python3 -B -m chiplib.cli circuit-faults examples/circuits/<name>/circuit.json
```

## Board Tool

- Component source owns `device`/`net`/`bus`/`connect` — Board never alters topology.
- Board profile: digest-locked positions + visual paths for resolved scalar edges.
- Guides: session-only semantic toggles (never alternate topology editor).
- Labels: text editing in Label mode, move/resize in Select mode, never alters source.

## Component Language

- Additive to frozen Language v1.0.
- Parser/resolver/runtime work only after Bank's contract and Fern's conformance agree.
- Board and Operation layers deferred until source/runtime stable.

## Datasheet Policy

- Prefer direct manufacturer PDFs proving DIP/PDIP/P-DIP/N-P package.
- AllDatasheet only as locator when direct access unavailable.
- Keep only final cited PDF in `source/`; remove failed downloads and duplicates.
- 74HC150 and 74HC260 removed (no HC-family DIP evidence).

## RV8GR Circuit Examples

Circuits in `examples/circuits/` derived from the RV8 CPU must carry:
wiring data, proof vectors, Python tests, and student docs together.
Timing, sync-edge, and bus-race concerns must be explicit tasks.
RV8GR board: 36 instances, 16 part types, 18 RV8GR-ready definitions.
