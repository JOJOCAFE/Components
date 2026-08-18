#!/bin/bash
# Lab 12: RAM + Data Page (RAM, U32, U33) — SETDP + memory access
# Shows DP register and RAM addressing via data page store/load
cd /home/jo/kiro/Components

PYTHONPATH=python python3 -m chiplib.cli trace \
  examples/circuits/RV8GR_StoreLoadBranchTrace/circuit.component \
  --steps 12 \
  --probes bus_ibus,bus_abus,acc \
  --annotate \
  --program "LI \$42; SB \$00; LI \$00; LB \$00"
