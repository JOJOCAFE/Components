# Student Readability Audit

Date: 2026-07-10

Purpose: check whether the current Components documentation can support
students around ages 10-15, from late primary to secondary school, while still
preserving real chip behavior, datasheet truth, and physical safety boundaries.

## Verdict

The repo is usable for student-supported learning, but not as a single linear
book. A 10-15 year old should start from the student guide and small examples,
then use circuit package READMEs as proof cards with a teacher or mentor.

The advanced protocol, DB, service, migration, and generation documents are
accurate reference material for teachers and tool builders. They are not the
right first reading for most young students.

## Student Route

Use this order for a beginner:

1. `STUDENT_GUIDE.md`
2. `Examples/nand.json` with `validate`, `run`, and `probe`
3. `DB/STUDENT_CATALOG.md` to look up chips before wiring
4. One `Lib/Circuits/RV8GR_*/README.md` proof card at a time
5. `Lib/Circuits/RV8GR_TEST_PROTOCOL.md` only with a teacher for real build
   timing and measurement

The student should not start with `SERVICE_CONTRACT.md`,
`DB_COMPONENT_PACKAGE_SPEC.md`, `DB_MIGRATION_PLAN.md`, or the full RV8GR
multi-level protocol. Those files are for maintainers and teachers.

## Build-Along Rule

For physical breadboard work:

- Build one small module at a time.
- Use a manual or very slow clock first.
- Check the expected state before adding the next module.
- Stop if a chip gets hot, supply current is unexpected, a bus conflict is
  reported, or an output is connected to another output without a valid
  tri-state/bus-owner rule.
- Treat 50 kHz, 1 MHz, 2 MHz, and 5 MHz as later tests. A virtual pass does not
  mean the real board passes those speeds.

## File Audience Map

| File or folder | Student fit | Note |
|---|---|---|
| `README.md` | Student with teacher | Good repo map; now points to the beginner path. |
| `STUDENT_GUIDE.md` | Student | Best first file for CLI/API use. |
| `DB/STUDENT_CATALOG.md` | Student | Good short catalog explanation. |
| `Examples/*.json` | Student | Best hands-on start with CLI. |
| `SCHEMATIC_JSON_SPEC.md` | Student with teacher | Useful but long; use after small examples. |
| `python/USAGE.md` | Older student / teacher | Strong practical Python reference, too long for first session. |
| `python/README.md` | Teacher / older student | Explains simulator role and source-of-truth rules. |
| `Lib/Circuits/README.md` | Teacher | Good map of RV8GR circuit proof packages. |
| `Lib/Circuits/RV8GR_*/README.md` | Student with teacher | Good proof cards; most need lab wiring beside them. |
| `DB/COMPONENT_TEST_PROTOCOL.md` | Teacher | Serious protocol, not first-reading student text. |
| `Lib/Circuits/RV8GR_TEST_PROTOCOL.md` | Teacher / advanced student | Good real-build measurement guide. |
| `DB/RV8GR_MULTI_LEVEL_TEST_PROTOCOL.md` | Teacher / verifier | Good gate structure, too dense for beginners. |
| `DB/RV8GR_CHIP_LEVEL_TEST_PLAN.md` | Teacher / verifier | Required chip-level gate and physical sweep plan. |
| `DB/RV8GR_TEST_REPORT.md` | Teacher / verifier | Current pass/block status. |
| `DB/RV8GR_VIRTUAL_BENCH_PLAN.md` | Teacher / tool builder | Virtual instrument mapping. |
| `DB/RV8GR_BATCH2_VERIFICATION_AUDIT.md` | Maintainer | Evidence audit, not a lesson. |
| `CHIP_STATUS.md` | Teacher / maintainer | Catalog status snapshot. |
| `DB/README.md` | Maintainer | DB model and package layout. |
| `DB_COMPONENT_PACKAGE_SPEC.md` | Maintainer | Component package contract. |
| `GENERATION_PIPELINE.md` | Maintainer | Generator contract. |
| `COMPONENT_GENERATION_BACKLOG.md` | Maintainer | Team backlog and generator status. |
| `SERVICE_CONTRACT.md` | Tool builder | API/CLI contract reference. |
| `PYTHON_BACKEND_ARCHITECTURE.md` | Tool builder | Backend architecture. |
| `BLOCK_UI_CONTRACT.md` | Tool builder | Future visual editor contract. |
| `FRONTEND_SNAPSHOT_CONTRACT.md` | Tool builder | UI snapshot shape. |
| `SERVICE_ARCHITECTURE_TASKS.md` | Maintainer | Internal service boundary tasks. |
| `EXTERNAL_ENGINE_ADAPTER_PLAN.md` | Maintainer | Future engine adapter plan. |
| `DB_MIGRATION_PLAN.md` | Maintainer | Historical migration and active package rules. |
| `Verilog/74xx/README.md` | Teacher / RTL student | HDL model list and smoke command. |
| `Verilog/Memory/README.md` | Teacher / RTL student | Memory HDL model list and sources. |
| `Verilog/74xx/SCAN_74XX_MAP.md` | Maintainer | Source/evidence scan notes. |
| `Verilog/74xx/SOURCE_7400_COVERAGE.md` | Maintainer | Imported model coverage. |
| `Source/README.md` | Teacher / maintainer | Datasheet evidence inventory. |
| `Lib/README.md` | Teacher | Explains circuit-library boundary. |
| `Lib/Circuits/BACKLOG.md` | Maintainer | Circuit-library next work. |
| `BACKLOG.md` | Maintainer | Whole-repo task state. |
| `TEAM_SKILLS.md` | Maintainer | Team ownership and quality gates. |
| `SESSION_HANDOFF.md` | Maintainer | Current session state and handoff. |
| `AGENTS.md` | Maintainer | Local team instructions. |

## Gaps To Fix Before GUI Editor

1. Add generated chip cards that explain each chip with purpose, pins to care
   about, active-low controls, what to try first, and what a failing result
   usually means.
2. Add a short "student command card" for the most common CLI/API actions:
   create chip, connect pins, add bus, add probe, run, inspect errors, and
   export.
3. Add a beginner layer over circuit packages: exact chips, visible test
   points, expected LED/probe values, and stop conditions.
4. Keep the four common wiring traps visible in every student-facing circuit
   check: wrong pin, output-output conflict, wrong clock edge, and missing
   delay/deadband margin.
5. Keep all fast-clock language conservative. Functional simulation at 5 MHz is
   not physical hardware signoff.

## Current Conclusion

Students can build along if the teacher gives them the beginner route and one
small task at a time. The repo already has strong truth and verification docs;
the next improvement is not more technical depth, but a thinner student layer
over chip cards, circuit cards, and system wiring commands.
