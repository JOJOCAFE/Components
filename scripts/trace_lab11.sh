#!/bin/bash
# Lab 11: Page Register (U23) — PG captures high byte for JMP/JSR targets
# Shows how PG latches from IRL for page-crossing jumps
cd /home/jo/kiro/Components

PYTHONPATH=python python3 -m chiplib.cli trace \
  examples/circuits/RV8GR_PageDataRegisters/circuit.component \
  --steps 6 \
  --probes page_reg,data_page_reg
