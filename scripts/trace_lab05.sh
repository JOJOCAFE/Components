#!/bin/bash
# Lab 05: ROM + Bus Buffer (ROM+U7) — Data flows from ROM through DBUS to IBUS
# Shows how bytes read from ROM travel through the bus bridge
cd /home/jo/kiro/Components

PYTHONPATH=python python3 -m chiplib.cli trace \
  examples/circuits/RV8GR_FetchCycleTrace/circuit.component \
  --steps 6 \
  --probes DBUS,IBUS \
  --annotate \
  --program "LI \$42; LI \$FF; LI \$00"
