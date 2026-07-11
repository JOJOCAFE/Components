# RV8GR BranchJumpControl

This circuit decides whether the PC should load a new address.

```text
Z_match      = Z_flag XOR ALU_SUB
BR_TAKEN     = BR AND Z_match
PC_LOAD_COND = JMP OR BR_TAKEN
/PC_LD       = NAND(T2, PC_LOAD_COND)
```

`/PC_LD` is active LOW. Even if a jump or branch condition is true, the PC must
not load during T0 or T1.

## Proof

The proof checks:

- T0/T1 do not load PC.
- J loads during T2.
- BEQ loads only when `Z=1`.
- BNE loads only when `Z=0`.
- No branch/no jump holds `/PC_LD` HIGH.
- JMP+BR overlap still gives one load condition.
- Manual push switch, random 100-push, 50 kHz, 1 MHz, 2 MHz, and 5 MHz
  functional profiles are declared and executed.

Run:

```sh
PYTHONPATH=python python3 -B -m tests.test_lib_circuits
```

## Build and test guide

- **Build/probe:** Build U26-U28 from Lab 10. Probe `T2`, `JMP`, `BR`, `ALU_SUB`, `Z_flag`, `Z_match`, `PC_LOAD_COND`, and active-low `/PC_LD`.
- **Isolated manual-clock test:** Hold T2 low while setting each J, BEQ, and BNE case. Raise T2 once and observe `/PC_LD`; lower T2 before changing controls.
- **Integration test:** Reconnect `/PC_LD` to U1-U4, set `{PG,IRL}`, and single-step taken and not-taken branches plus J.
- **Pass:** `/PC_LD` stays HIGH in T0/T1 and for a false condition; it is LOW only during taken T2, and the next PC value is `{PG,IRL}`. Parallel load wins over count.
- **Stop:** Stop if `/PC_LD` pulses outside T2, PC changes on a not-taken branch, or PC becomes unknown.
- **Temporary wiring:** Remove Lab 10 control switches and any direct `/PC_LD` test connection before reconnecting IRH, Z, T2, and the PC chain.
- **Boundary:** Logic profiles through 5 MHz are simulated behavior; physical timing needs a scope capture of control settling before the PC clock edge.
