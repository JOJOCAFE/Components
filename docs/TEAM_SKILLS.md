# Components Team Skills

This is the compact team contract every Components agent must know and follow.
Role-specific detail lives in `docs/agents/`.

## Mission

- Build a shared Components library for students around 10-15 years old, while
  staying accurate enough for older learners and real hardware work.
- Preserve datasheet truth, real pin behavior, active-low naming, timing limits,
  tri-state rules, and bus ownership.
- Keep DB definitions, Python behavior, Verilog export, pinout evidence, tests,
  docs, and circuit-library examples aligned.

## Non-Negotiable Rules

- `definition/definition.json` plus datasheet evidence is the source of truth.
  Generated Python, Verilog, KiCad, SVG, docs, tests, and demos are not
  authoritative by themselves.
- Compact DB source files are intentional. Do not duplicate derivable layers;
  add embedded layers only when they carry non-derivable evidence or detail.
- Missing chip properties are acceptable only when visible in status,
  `missing_properties`, `missing_files`, or task docs.
- Active chip-local `simulation/model.py` files must run standalone with only
  `chiplib/core.py`, expose `create(name)`, and avoid full app dependencies.
- Truth records for active ICs must state `edge_criteria`. Clocked chips prove
  active-edge behavior and no-edge hold; tri-state/bus chips prove high-Z and
  no bus fight; memory chips prove read/write control windows.
- RV8GR-derived circuits in `examples/circuits/` must carry wiring data, proof
  vectors, Python tests, and student docs together.
- Virtual helpers may clarify tests, but must not replace real chip behavior
  when a DB package has a real model.
- Do not describe functional simulation, including 5 MHz profiles, as physical
  hardware signoff without voltage, clock, bus-deadband, scope, and chip-marking
  evidence.
- Student clarity is required. Errors, examples, and docs must point to the
  chip, pin, net, command, source, or missing property a learner can fix.
- Counts must be explicit: RV8GR has 36 physical board packages, 16 board-used
  part types, and 18 RV8GR-ready definitions/options including memory choices.

## Team Roles

| Agent | Must own | Skill file |
|---|---|---|
| Pim | Routing, task order, handoffs, commits, pushes, cross-file alignment | `docs/agents/Pim.md` |
| Bank | Architecture, schema, package boundaries, service contracts | `docs/agents/Bank.md` |
| Fern | Verification, timing/bus proof, regression gates, release confidence | `docs/agents/Fern.md` |
| Mint | Verilog models, structural export, HDL benches, RTL timing honesty | `docs/agents/Mint.md` |
| Ohm | Datasheets, pin/package truth, electrical evidence, breadboard realism | `docs/agents/Ohm.md` |
| Bam | Python behavior, loaders, CLI/API services, circuit simulation | `docs/agents/Bam.md` |
| Noon | Student docs, examples, labels, labs, beginner clarity | `docs/agents/Noon.md` |

No specialist verifies only their own work. Fern reviews behavior that is meant
to ship, and Pim keeps the route visible.

## Saved Team Checkpoint: 2026-07-12

- Components `main` is pushed at `01d7ea1 Promote virtual test helper circuit`.
  `RV8GR_VirtualTestHelpers` is directly promoted through its declared virtual
  vectors; campaign artifacts and the package gate are execution-derived.
- RV8 `team-setup` is pushed at `7d2dac5 Support migrated Components layout`.
  The RV8GR Verilog runners support both external `verilog/` and the retained
  vendored `verilog/` snapshot.
- Next technical boundary: BusOwnership and FullControl cannot be promoted by
  inferred wiring. Bank and Ohm must establish authoritative gate/child-port
  mappings from canonical RV8GR RTL and wiring sources; Bam implements only
  those mappings; Mint checks HDL alignment; Fern gates each promotion; Noon
  preserves the modeled-versus-physical student boundary.

## Active RV8GR Software Differential-Hardening Lane: 2026-07-13

The passing directed, opcode-control, and chip-level gates remain the baseline.
This lane increases software confidence before physical wiring; it does not
claim physical timing or board signoff.

| Owner | Bounded deliverable | Paired review |
|---|---|---|
| Pim | Task order, checkpoints, cross-repo scope, and reproducible handoff | Fern |
| Bank | Four-model state/phase trace contract and canonical-source boundaries | Bam + Ohm |
| Fern | Seed ledger, differential oracle, mutation acceptance criteria, regression gate | Mint |
| Mint | Behavioural/chip-level RTL trace probes and mutation benches | Fern |
| Ohm | Signal/pin interpretation for bus handoff, ROM `/WE`, store direction, reset | Bank + Noon |
| Bam | Deterministic Python/Components differential runner and `/tmp` reproducibility wrapper | Fern + Mint |
| Noon | Student-safe explanation of coverage, reserved encodings, and simulation limits | Ohm |

Required work packages are: seeded instruction-stream differential tests,
end-to-end reserved-encoding characterization, a T0/T1/T2 trace contract,
negative mutation tests, and a clean external-Components runner.  Preserve
the current directed suite; do not replace it.  A result is promotable only if
the command fails on mismatch and retains the seed, ROM/program, phase trace,
and model versions needed to reproduce it.

## Active `component:component` Language Model Lane: 2026-07-13

The first language implementation target is an executable Component source
model, not Board/UI.  It instantiates compact Device definitions, declares
typed nets/buses, makes explicit connections, names probes/display intent, and
attaches bounded deterministic tests.  It resolves into immutable topology.
`component:board` and `component:operation` remain deferred clients of that
model.

- Bank owns the source/AST/resolver contract and compatibility boundary.
- Bam owns the parser/resolver/runtime prototype once the contract is frozen.
- Fern owns conformance fixtures for invalid ports, widths, drivers, power,
  probes, displays, and deterministic test failures.
- Mint and Ohm review device/pin/timing truth exposed through Component source.
- Noon owns readable examples that do not require a Board to explain a machine.
- Pim keeps this additive proposal separate from `docs/Component/old_references`.

## Saved RV8GR Software-Closeout Skill: 2026-07-13

The RV8GR software lane is closed at the digital-model boundary.  Before a
future RV8GR change is called safe, run the complete external regression:

```sh
COMPONENTS_ROOT=/home/jo/kiro/Components \
  /home/jo/kiro/RV8/RV8GR/tools/run_all_verilog_tb.sh
```

This includes behavioral tests, chip-level bring-up/full execution, dual RTL
comparison, and negative kill tests for reset release, U34/U7 ownership, ROM
`/WE` protection, U7 store direction, and output-enable ordering.  A killed
mutation is evidence that the test can observe that specific modeled fault; it
is not a physical deadband, memory-turnaround, contention-current, or PCB
clock-rate signoff.  Those claims remain Ohm's measurement work on wired
hardware.

## Saved Component Model and Definition-Migration Skill: 2026-07-13

- `docs/Component/` contains only `Component_Model.md`; all imported v0.1
  material is preserved under `docs/Component/old_references/`.
- A Component source describes explicit topology, bounded checks, and read-only
  observation.  Device definitions provide behavior/timing; Resources provide
  presentation.  Board and Operation stay deferred.
- Before replacing a legacy RV8GR definition, run the digital or memory
  lossless-equivalence gate and the migration audit.  A bridge-ready result is
  permission to author/review a compact source, never permission to discard
  canonical timing, pin, or evidence truth.
- Any direct package-file audit must resolve compact authoring through
  `chiplib.db.resolve_definition_source()` before reading pins or timing.

## Model Routing

Pim assigns the strongest available Codex coding/reasoning profile to work that
can change chip truth, verification confidence, or student-facing contracts.
Faster profiles are allowed only for low-risk mechanical work after the owner
and verification path are clear.

| Agent | Default profile | Escalate when |
|---|---|---|
| Pim | Strong reasoning/coding, high reasoning | Multi-owner routing, handoffs, commits, pushes, cross-repo consistency |
| Bank | Strong reasoning/coding, high reasoning | Schema, package, service, or DB layout decisions may become long-term contracts |
| Fern | Strong reasoning/coding, high reasoning | Result will be used as release confidence, timing proof, bus proof, or CI evidence |
| Mint | Strong coding, medium reasoning | HDL affects edge behavior, tri-state, memory ports, wrappers, or equivalence |
| Ohm | Strong reasoning, high reasoning | Datasheet interpretation, pin truth, electrical limits, or physical-readiness wording |
| Bam | Strong coding, medium reasoning | Python behavior, loaders, services, simulator state, or generated artifacts affect chips |
| Noon | Standard writing/coding, medium reasoning | Docs explain timing, hardware risk, missing evidence, or executable commands |

Do not freeze exact model slugs in this repo. Map these profiles to the current
official Codex model names in the running environment.

## Work Discipline

- Start from the responsible owner, then pull in paired reviewers when risk
  crosses boundaries.
- Keep changes scoped. Do not refactor unrelated DB, Python, Verilog, docs, or
  generated artifacts while fixing a narrow issue.
- Preserve source/status/docs together. If behavior changes, update tests and
  the student-facing route when applicable.
- Use shell-failing tests or executable checks for claims. Printed pass messages
  are not enough.
- Keep handoffs compact and evidence-based: changed files, tests run, known
  gaps, and next owner.

## Natural Pairings

- Bank + Ohm: architecture and physical truth.
- Mint + Fern: HDL behavior and verification rigor.
- Bam + Noon: usable tools and student understanding.
- Bank + Bam: service boundary and executable model.
- Fern + Ohm: bus-race, timing-risk, and physical debug evidence.
- Mint + Bam: Python/Verilog equivalence and circuit-level proof.
- Pim + everyone: routing, task order, and delivery discipline.

## Quality Gates

Run the focused tests for the files changed. Before claiming broad Components
health, use the full gate:

```sh
cd python
python3 -B -m tests.test_chips
python3 -B -m tests.test_design
python3 -B -m tests.test_block_ui
python3 -B -m tests.test_netlist
python3 -B -m tests.test_cli
python3 -B -m tests.test_api
python3 -B -m tests.test_db
python3 -B -m tests.test_generated_split_records
python3 -B -m tests.test_contracts
python3 -B -m tests.test_simulation_service
python3 -B -m tests.test_equivalence
python3 -B -m tests.test_lib_circuits
python3 -m py_compile chiplib/*.py tests/*.py
python3 -m chiplib.cli db --audit
python3 -m chiplib.cli db --status
cd ..

PYTHONPATH=python python3 tools/pinout_crosscheck.py
PYTHONPATH=python python3 tools/polarity_crosscheck.py
PYTHONPATH=python python3 tools/timing_crosscheck.py
PYTHONPATH=python python3 tools/state_behavior_crosscheck.py
PYTHONPATH=python python3 tools/python_behavior_crosscheck.py
PYTHONPATH=python python3 tools/verilog_behavior_crosscheck.py

iverilog -g2012 -Wall -o /tmp/tb_74xx_smoke.vvp verilog/74xx/*.v verilog/74xx/tests/tb_74xx_smoke.v
vvp /tmp/tb_74xx_smoke.vvp

iverilog -g2012 -Wall -o /tmp/tb_memory_smoke.vvp verilog/memory/*.v verilog/memory/tests/tb_memory_smoke.v
vvp /tmp/tb_memory_smoke.vvp
```
