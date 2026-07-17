# Components Documentation Index

Root is kept small on purpose. `README.md` is the project entry point and
`AGENTS.md` is the active team instruction file. Everything else that is general
documentation lives here.

## Start Here

- `STUDENT_GUIDE.md` - beginner-first CLI/API path for students.
- `COMPONENT_BUILD_NOT_GATE.md` - first text Component lesson: read, run, and
  explain one NOT gate before using advanced Board detail.
- `../board/README.md` - run the first local three-pane Component Board.
- `COMPONENT_FIRST_SIGHT_DESIGN.md` - learner-first usability promise.
- `COMPONENT_LEARNING_LENS.md` - explanation/deeper-detail contract for a
  selected part, wire, value, or result.
- `COMPONENT_THREE_PANE_WORKSPACE.md` - Drawing left, Text upper-right,
  Terminal lower-right interaction contract.
- [`../board/docs/COMPONENT_BOARD_WORKFLOW.md`](../board/docs/COMPONENT_BOARD_WORKFLOW.md) - learner and implementation workflow for
  inspecting chips, previewing/applying connections, recovering from errors,
  and running the first Board example.
- [`../board/docs/COMPONENT_BOARD_PROTOTYPE.md`](../board/docs/COMPONENT_BOARD_PROTOTYPE.md) - prototype boundary and command design for
  Component topology versus `component:board` placement, routes, and LOGO pen
  paths; use this before implementing further Board commands.
- [`../board/docs/BOARD_FIRST_SIGHT_TRIAL.md`](../board/docs/BOARD_FIRST_SIGHT_TRIAL.md) - five-minute human acceptance protocol for the
  local NOT-gate Board, including safe-change and recovery checks.
- [`../board/docs/BOARD_LEARNER_CIRCUIT_DIRECTION.md`](../board/docs/BOARD_LEARNER_CIRCUIT_DIRECTION.md) - MakeCode-like blocks, readable
  Component code, and KiCad-like Board direction under one circuit authority.
- [`../board/docs/BOARD_IMAGE_RECONSTRUCTION_CONTRACT.md`](../board/docs/BOARD_IMAGE_RECONSTRUCTION_CONTRACT.md) - resolver-gated schematic-image
  reconstruction and code-to-Board connection-guide contract.
- [`../board/docs/BOARD_CANVAS_PROTOTYPE_SCOPE.md`](../board/docs/BOARD_CANVAS_PROTOTYPE_SCOPE.md) - the deliberately small mouse/stylus
  schematic-canvas prototype and its Component-layer action mapping.
- [`../board/docs/BOARD_ARCHITECTURE_FREEZE.md`](../board/docs/BOARD_ARCHITECTURE_FREEZE.md) - frozen Board v2 world-coordinate Viewport,
  semantic-operation, and transaction-queue architecture.
- [`../board/docs/BOARD_V2_SPRINT_PLAN.md`](../board/docs/BOARD_V2_SPRINT_PLAN.md) - ordered Board v2 tasks, machine/human
  checkpoints, and the benchmark-harness gate that precedes broad editor work.
- [`../board/docs/BOARD_SCHEMATIC_TOOLSET.md`](../board/docs/BOARD_SCHEMATIC_TOOLSET.md) - the staged KiCad/Tinkercad-inspired schematic
  tool inventory and its Component-layer mappings.

The related language-layer contract is
[`../Language/23_Component_Operation_Contract.md`](../Language/23_Component_Operation_Contract.md):
the replayable Board/source/runtime operation layer.
- `CHIP_STATUS.md` - 74xx/memory status baseline used by DB status checks.
- `SESSION_HANDOFF.md` - latest work state, verification, and next lanes.
- `TEAM_SKILLS.md` - compact Components team routing and quality-gate contract.
- `COMPACT_DEFINITION_V0_2.md` - additive human-authored compact-definition
  pilot and resolver contract.
- `agents/` - delegated per-agent skill files for Pim, Bank, Fern, Mint, Ohm,
  Bam, and Noon.

## Chip DB And Generation

- `DB_COMPONENT_PACKAGE_SPEC.md` - package-layer contract.
- `GENERATION_PIPELINE.md` - one-file definition to generated artifacts.

## Tool And Service Contracts

- `SCHEMATIC_JSON_SPEC.md` - readable schematic JSON shape.
- `SERVICE_CONTRACT.md` - CLI/API request and response contract.
- `BLOCK_UI_CONTRACT.md` - future visual block editor interchange.

## Circuit Runner

The functional circuit runner has public headless commands through
`python3 -m chiplib.cli`: `circuit-validate`, `circuit-run`, `circuit-step`,
and `circuit-probe`. The local JSON API exposes those commands plus
`circuit-load`. Package support remains staged: unsupported package features
return a structured blocked result, and a loadable package is not automatically
promoted as verified.

`timed-run` is not a public runner command. Package-level timing enforcement,
broader package execution, and physical evidence remain staged or blocked as
recorded in the task plan and campaign reports.

## Component Text IDE

[`COMPONENT_TEXT_IDE.md`](COMPONENT_TEXT_IDE.md) documents the text-first
`component:component` CLI. It parses and resolves Component fixtures against
the active library. The supported leaf digital-model subset can run its bounded
declared tests. The local `../board/` workbench consumes the same service and
readable source; advanced Resource views and physical claims remain separate.

- [`COMPONENT_PROGRAM_TASKS.md`](COMPONENT_PROGRAM_TASKS.md) - delivery order
  and owned acceptance gates from the text IDE through Runtime, Resources, the
  in-progress three-pane Board, and later `component:board` work.

- [`CIRCUIT_RUNNER_ARCHITECTURE.md`](CIRCUIT_RUNNER_ARCHITECTURE.md) - net,
  timing, execution, and future interface architecture.
- [`CIRCUIT_RUNNER_STUDENT_CONTRACT.md`](CIRCUIT_RUNNER_STUDENT_CONTRACT.md) -
  current functional commands, staged commands, results, and error language.
- [`CIRCUIT_RUNNER_TASK_PLAN.md`](../examples/circuits/CIRCUIT_RUNNER_TASK_PLAN.md) -
  staged implementation checklist and current status.
- [`CIRCUIT_RUNNER_VERIFICATION_PLAN.md`](../examples/circuits/CIRCUIT_RUNNER_VERIFICATION_PLAN.md)
  - package batches, negative tests, CI lanes, and promotion gates.

## Verification Reports

Expected RV8GR circuit-campaign outputs:

- [`RV8GR_CIRCUIT_TEST_CAMPAIGN.md`](../examples/circuits/RV8GR_CIRCUIT_TEST_CAMPAIGN.md)
  - generated readable summary of logical, part-model, composed/static,
  modeled-timing, and physical-evidence status.
- [`RV8GR_CIRCUIT_TEST_CAMPAIGN.json`](../examples/circuits/RV8GR_CIRCUIT_TEST_CAMPAIGN.json)
  - generated machine-readable form of the same campaign results and evidence
  references.

The reports exist, but their presence does not mean every campaign layer
passed. Start with Markdown for an explanation and use JSON for tools or exact
evidence details. A logical or modeled-timing pass is still not physical
measurement of the built RV8GR board.

- `PINOUT_CROSSCHECK_REPORT.md` - lib/standard/model pinout consistency.
- `POLARITY_CROSSCHECK_REPORT.md` - active-low naming and behavior checks.
- `TIMING_CROSSCHECK_REPORT.md` - timing metadata extraction and defaults.
- `TIMING_PARAMETER_AUDIT.md` - canonical datasheet timing-name coverage.
- `TIMING_SIMULATION_AUDIT.md` - executable timing-hook coverage by model.
- `STATE_BEHAVIOR_CROSSCHECK_REPORT.md` - stateful chip behavior checks.
- `PYTHON_BEHAVIOR_CROSSCHECK_REPORT.md` - Python model pin/truth/timing checks.
- `VERILOG_BEHAVIOR_CROSSCHECK_REPORT.md` - Verilog truth-vector checks.
- `EXTERNAL_MODEL_CROSSCHECK_REPORT.md` - external model availability checks.
