#!/bin/bash
# Lab 10: Branch/Jump Control (U25-U28) — PC load decision logic
# Shows how pc_load activates when branch condition is met (Z=1 after SUBI makes AC=0)
cd /home/jo/kiro/Components

PYTHONPATH=python python3 -m chiplib.cli trace \
  examples/circuits/RV8GR_StoreLoadBranchTrace/circuit.component \
  --steps 12 \
  --probes pc_load,z,pc_val \
  --annotate \
  --program "LI \$01; SUBI \$01; BEQ \$00"
