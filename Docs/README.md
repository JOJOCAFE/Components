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

## Verification Reports

- `PINOUT_CROSSCHECK_REPORT.md` - DB/model pinout consistency.
- `POLARITY_CROSSCHECK_REPORT.md` - active-low naming and behavior checks.
- `TIMING_CROSSCHECK_REPORT.md` - timing metadata extraction and defaults.
- `TIMING_PARAMETER_AUDIT.md` - canonical datasheet timing-name coverage.
- `TIMING_SIMULATION_AUDIT.md` - executable timing-hook coverage by model.
- `STATE_BEHAVIOR_CROSSCHECK_REPORT.md` - stateful chip behavior checks.
- `PYTHON_BEHAVIOR_CROSSCHECK_REPORT.md` - Python model pin/truth/timing checks.
- `VERILOG_BEHAVIOR_CROSSCHECK_REPORT.md` - Verilog truth-vector checks.
- `EXTERNAL_MODEL_CROSSCHECK_REPORT.md` - external model availability checks.
