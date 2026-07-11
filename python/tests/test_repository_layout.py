"""Regression checks for the lower-case repository layout."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "verify_repository_layout.py"
SPEC = importlib.util.spec_from_file_location("verify_repository_layout", TOOL)
assert SPEC and SPEC.loader
LAYOUT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LAYOUT)


def test_current_repository_layout_has_no_legacy_paths():
    assert LAYOUT.audit_layout(ROOT) == []


def test_layout_audit_reports_missing_roots_legacy_directories_and_references():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        for name in LAYOUT.REQUIRED_ROOTS:
            (root / name).mkdir()
        (root / "source").rmdir()
        (root / LAYOUT.LEGACY_ROOTS[0]).mkdir()
        stale = root / "python" / "stale.py"
        stale.write_text(f'path = "{LAYOUT.LEGACY_ROOTS[1]}/guide.md"\n', encoding="utf-8")

        problems = LAYOUT.audit_layout(root)

        assert "missing required root directory: source/" in problems
        assert f"legacy root directory must not exist: {LAYOUT.LEGACY_ROOTS[0]}/" in problems
        assert f"python/stale.py:1: legacy path prefix {LAYOUT.LEGACY_ROOTS[1]}/" in problems


def run_all() -> None:
    test_current_repository_layout_has_no_legacy_paths()
    test_layout_audit_reports_missing_roots_legacy_directories_and_references()


if __name__ == "__main__":
    run_all()
    print("Repository layout tests passed")
