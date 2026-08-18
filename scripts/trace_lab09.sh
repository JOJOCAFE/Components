#!/bin/bash
# Lab 09: Z Flag (U21+U22) — Zero flag from AC comparator
# Shows Z_flag going high when AC equals zero
cd /home/jo/kiro/Components

PYTHONPATH=python python3 -m chiplib.cli trace \
  examples/circuits/RV8GR_AluAccumulator/circuit.component \
  --steps 9 \
  --probes z,accumulator
