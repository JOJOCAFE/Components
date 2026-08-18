#!/bin/bash
# Lab 04: Address Multiplexer (U15-U16, U29-U30) — Selects PC or DP:IRL for ABUS
# Shows how address mux switches between fetch (PC) and data ({DP,IRL}) modes
cd /home/jo/kiro/Components

PYTHONPATH=python python3 -m chiplib.cli trace \
  examples/circuits/RV8GR_AddressMux16/circuit.component \
  --steps 6 \
  --probes addr_bus,addr_select
