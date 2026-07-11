# Components Documentation Index

Root is kept small on purpose. `README.md` is the project entry point and
`AGENTS.md` is the active team instruction file. Everything else that is general
documentation lives here.

## Start Here

- `STUDENT_GUIDE.md` - beginner-first CLI/API path for students.
- `CHIP_STATUS.md` - 74xx/memory status baseline used by DB status checks.
- `SESSION_HANDOFF.md` - latest work state, verification, and next lanes.
- `TEAM_SKILLS.md` - compact Components team routing and quality-gate contract.
- `Agents/` - delegated per-agent skill files for Pim, Bank, Fern, Mint, Ohm,
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
