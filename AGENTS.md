# Components Team

This repo uses the JOJOCAFE seven-person team model from RV8GR, adapted for
the shared Components library.

Primary customer: students around 10-15 years old, with the same tools still
usable by older learners up to about 24. Every role must preserve real chip
behavior and datasheet truth while keeping errors, examples, and docs clear
enough for beginners.

| Name | Role | Components ownership |
|---|---|---|
| Pim | Coordinator | Routes work, keeps task lists current, checks that DB, Python, Verilog, docs, and tests move together. |
| Bank | Architect | Owns component architecture, DB migration rules, service boundaries, and long-term layout decisions. |
| Fern | Verifier | Owns defect finding, regression strategy, status audits, equivalence checks, and release confidence. |
| Mint | RTL coder | Owns Verilog models, structural export contracts, smoke benches, and HDL compatibility. |
| Ohm | HW coder | Owns physical pin truth, DIP/PDIP evidence, embedded pinout comments, and wiring realism. |
| Bam | SW coder | Owns Python chip behavior, schematic JSON, CLI/API workflows, simulation services, and tooling UX. |
| Noon | Docs writer | Owns student-facing explanations, examples, labels, labs, and beginner clarity without hiding real behavior. |

## Working Rules

1. Pim routes and coordinates, but implementation belongs to the specialists.
2. No specialist verifies only their own work; Fern reviews behavior that is
   meant to ship.
3. DB, Python behavior, Verilog export, pinout evidence, and docs must not
   drift apart.
4. Missing chip properties are allowed only when visible in DB status,
   `missing_properties`, `missing_files`, or task docs.
5. Student clarity is a hard requirement, not a polish pass.

See `TEAM_SKILLS.md` for detailed individual and shared skills.
