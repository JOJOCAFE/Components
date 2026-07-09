# Circuit Library Backlog

## RV8GR Trace Packages

- Done: `RV8GR_StoreLoadBranchTrace` packages the SB, LB, and BEQ rows from
  `doc/03_instruction_trace.md` with machine-readable vectors for state and bus
  ownership.
- Next: add a trace package for SETDP, SETPG, and J so page-register state and
  PC page loading are checked together.
