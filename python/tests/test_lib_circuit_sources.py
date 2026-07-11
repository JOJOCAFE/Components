"""Source-reference checks for RV8GR library circuit packages."""

from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
RV8GR_ROOT = ROOT.parent / "RV8" / "RV8GR"
COMPONENTS_LOCAL_ROOTS = (
    ROOT / "examples" / "circuits",
    ROOT / "lib" / "standard",
)


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


class LibCircuitSourceTests(unittest.TestCase):
    def test_all_source_project_paths_resolve(self) -> None:
        findings: list[str] = []

        circuit_files = sorted(ROOT.glob("examples/circuits/RV8GR_*/circuit.json"))
        self.assertTrue(circuit_files, "No RV8GR circuit packages found")
        for circuit_file in circuit_files:
            circuit = json.loads(circuit_file.read_text(encoding="utf-8"))
            package = circuit_file.parent.name
            source_project = circuit.get("source_project")
            if not isinstance(source_project, dict) or source_project.get("name") != "RV8GR":
                findings.append(f"{package}: source_project must name RV8GR")
                continue
            sources = source_project.get("paths")
            if not isinstance(sources, list) or not sources:
                findings.append(f"{package}: source_project.paths must be a nonempty list")
                continue

            for source in sources:
                if not isinstance(source, str) or not source.strip():
                    findings.append(f"{package}: source path must be a nonempty string")
                    continue
                source_path = Path(source)
                resolved = (source_path if source_path.is_absolute() else ROOT / source_path).resolve()
                approved = is_relative_to(resolved, RV8GR_ROOT) or any(
                    is_relative_to(resolved, root) for root in COMPONENTS_LOCAL_ROOTS
                )
                if not approved:
                    findings.append(f"{package}: source escapes approved roots: {source}")
                elif not resolved.is_file():
                    findings.append(f"{package}: source is not a regular file: {source}")
                elif resolved.stat().st_size == 0:
                    findings.append(f"{package}: source file is empty: {source}")
                elif is_relative_to(resolved, ROOT / "examples" / "circuits"):
                    if resolved.name != "circuit.json" or not resolved.parent.name.startswith("RV8GR_"):
                        findings.append(f"{package}: local circuit source is not a package circuit.json: {source}")
                elif is_relative_to(resolved, ROOT / "lib" / "standard"):
                    if resolved != ROOT / "lib" / "standard" / "VIRTUAL_TEST_GENERATOR_CONTRACT.json":
                        findings.append(f"{package}: DB source is not the canonical virtual-test contract: {source}")

        self.assertFalse(
            findings,
            "Invalid source_project paths:\n" + "\n".join(findings),
        )


if __name__ == "__main__":
    unittest.main()
