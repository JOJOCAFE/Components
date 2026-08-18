#!/bin/bash
# Lab 03: Program Counter (U1-U4) — 16-bit PC with carry chain
# Shows the PC incrementing through addresses
cd /home/jo/kiro/Components

PYTHONPATH=python python3 -m chiplib.cli trace \
  examples/circuits/RV8GR_PC16/circuit.component \
  --steps 6 \
  --probes pc_val
