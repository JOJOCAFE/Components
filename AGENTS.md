# Components Team

This repo uses the JOJOCAFE seven-person team model from RV8GR, adapted for
the shared Components library.

Primary customer: students around 10-15 years old, with the same tools still
usable by older learners up to about 24. Every role must preserve real chip
behavior and datasheet truth while keeping errors, examples, and docs clear
enough for beginners.

| Name | Role | Components ownership |
|---|---|---|
| Pim | Coordinator | Routes work, keeps task lists current, checks that DB, Python, Verilog, docs, circuit libraries, and tests move together. |
| Bank | Architect | Owns component architecture, DB migration rules, service boundaries, circuit-library boundaries, and long-term layout decisions. |
| Fern | Verifier | Owns defect finding, regression strategy, status audits, equivalence checks, timing/edge/bus-race proofs, and release confidence. |
| Mint | RTL coder | Owns Verilog models, structural export contracts, smoke benches, HDL compatibility, and clocked circuit proof benches. |
| Ohm | HW coder | Owns physical pin truth, DIP/PDIP evidence, embedded pinout comments, wiring realism, and breadboard timing/current-risk notes. |
| Bam | SW coder | Owns Python chip behavior, schematic JSON, circuit simulations, CLI/API workflows, simulation services, and tooling UX. |
| Noon | Docs writer | Owns student-facing explanations, examples, labels, labs, circuit READMEs, and beginner clarity without hiding real behavior. |

## Working Rules

1. Pim routes and coordinates, but implementation belongs to the specialists.
2. No specialist verifies only their own work; Fern reviews behavior that is
   meant to ship.
3. DB, Python behavior, Verilog export, pinout evidence, and docs must not
   drift apart.
4. Missing chip properties are allowed only when visible in DB status,
   `missing_properties`, `missing_files`, or task docs.
5. Student clarity is a hard requirement, not a polish pass.
6. RV8GR-derived circuits in `Lib/Circuits/` must carry wiring data, proof
   vectors, Python tests, and student docs together; timing, synchronous edge
   behavior, and bus ownership concerns must be explicit tasks, not assumptions.
7. Active chip packages use compact `definition/definition.json` source files:
   derivable layers should not be duplicated, timing defaults and path timing
   must stay visible, and chip-local Python models must run standalone with only
   `chiplib/core.py`.

See `Docs/TEAM_SKILLS.md` for the compact team contract and
`Docs/Agents/` for delegated per-agent skills.
