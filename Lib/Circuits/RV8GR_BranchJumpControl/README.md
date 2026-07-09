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
