#!/bin/bash
# Lab 06: Instruction Latch (U5+U6) — IRH captures control, IRL captures operand
# Shows fetch cycle: T0 latches IRH (opcode), T1 latches IRL (operand)
cd /home/jo/kiro/Components

PYTHONPATH=python python3 -m chiplib.cli trace \
  examples/circuits/RV8GR_FetchCycleTrace/circuit.component \
  --steps 9 \
  --probes ir_high,ir_low,ibus_data \
  --annotate \
  --program "LI \$42; ADDI \$01; LI \$FF"
