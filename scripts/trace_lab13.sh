#!/bin/bash
# Lab 13: Full System — Complete instruction execution with branch
# Shows the full fetch-decode-execute pipeline with annotated instructions
# Runs: LI $42, ADDI $01, SUBI $43, BEQ $00 (loops when AC=0)
cd /home/jo/kiro/Components

PYTHONPATH=python python3 -m chiplib.cli trace \
  examples/circuits/RV8GR_FetchCycleTrace/circuit.component \
  --steps 12 \
  --probes pc_value,ir_high,ir_low,ibus_data \
  --annotate \
  --program "LI \$42; ADDI \$01; SUBI \$43; BEQ \$00"
