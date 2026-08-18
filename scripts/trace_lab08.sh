#!/bin/bash
# Lab 08: Accumulator + Mux (U9, U14, U17-U20) — Store path
# Shows AC value being stored back to IBUS via the output buffer
cd /home/jo/kiro/Components

PYTHONPATH=python python3 -m chiplib.cli trace \
  examples/circuits/RV8GR_AluAccumulator/circuit.component \
  --steps 9 \
  --probes accumulator,ibus_val
