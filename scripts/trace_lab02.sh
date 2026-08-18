#!/bin/bash
# Lab 02: Ring Counter (U8+U24) — Three-phase timing T0/T1/T2
# Shows how the ring counter generates the 3-cycle instruction phases
cd /home/jo/kiro/Components

PYTHONPATH=python python3 -m chiplib.cli trace \
  examples/circuits/RV8GR_RingCounter/circuit.component \
  --steps 6 \
  --probes T0,T1,T2
