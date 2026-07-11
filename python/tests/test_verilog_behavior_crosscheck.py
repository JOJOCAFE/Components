"""Run DB truth vectors against package-local Verilog exports."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_package_verilog_models_match_db_truth_vectors():
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "verilog_behavior_crosscheck.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
