#!/bin/bash
# Start Components Board API server
cd /home/jo/kiro/Components/python
exec python3 -B -m chiplib.api --http --host 127.0.0.1 --port 8765
