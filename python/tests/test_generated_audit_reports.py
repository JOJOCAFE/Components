"""Ensure committed deterministic audit reports match their generators."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
AUDIT_REPORTS = (
    ("tools/timing_parameter_audit.py", "docs/TIMING_PARAMETER_AUDIT.md"),
    ("tools/timing_simulation_audit.py", "docs/TIMING_SIMULATION_AUDIT.md"),
)


def load_generator(relative_path: str):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load report generator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GeneratedAuditReportTests(unittest.TestCase):
    def test_committed_reports_match_generators(self):
        for generator_path, report_path in AUDIT_REPORTS:
            with self.subTest(report=report_path), tempfile.TemporaryDirectory(dir=ROOT) as tmp:
                generator = load_generator(generator_path)
                generated_report = Path(tmp) / Path(report_path).name
                generator.REPORT = generated_report

                self.assertEqual(generator.main(), 0)
                self.assertEqual(
                    generated_report.read_bytes(),
                    (ROOT / report_path).read_bytes(),
                    f"{report_path} is stale; regenerate with python3 {generator_path}",
                )


if __name__ == "__main__":
    unittest.main()
