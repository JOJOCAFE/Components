#!/bin/bash
# Lab 07: ALU (U10-U13) — ADD/SUB/XOR through XOR gates and adder
# Shows how data flows through the ALU path into the accumulator
cd /home/jo/kiro/Components

PYTHONPATH=python python3 -m chiplib.cli trace \
  examples/circuits/RV8GR_AluAccumulator/circuit.component \
  --steps 9 \
  --probes ibus_val,accumulator
