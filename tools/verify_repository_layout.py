#!/usr/bin/env python3
"""Reject legacy root directories and path references after the layout migration."""

from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ROOTS = (
    "docs",
    "examples",
    "lib",
    "python",
    "schemas",
    "source",
    "tools",
    "verilog",
)
LEGACY_ROOTS = tuple("DB Docs Examples Lib Schemas Source Verilog".split())
TEXT_SUFFIXES = {".ini", ".json", ".md", ".py", ".rst", ".sh", ".toml", ".txt", ".yaml", ".yml"}
IGNORED_DIRECTORIES = {".git", ".pytest_cache", "__pycache__"}
LEGACY_PATH = re.compile(r"(?<![A-Za-z0-9_])(" + "|".join(LEGACY_ROOTS) + r")[/\\\\]")


def iter_text_files(root: Path):
    for path in root.rglob("*"):
        if any(part in IGNORED_DIRECTORIES for part in path.relative_to(root).parts):
            continue
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def audit_layout(root: Path) -> list[str]:
    """Return every root-layout violation so one run reports the full migration gap."""
    problems: list[str] = []
    for name in REQUIRED_ROOTS:
        if not (root / name).is_dir():
            problems.append(f"missing required root directory: {name}/")
    for name in LEGACY_ROOTS:
        if (root / name).exists():
            problems.append(f"legacy root directory must not exist: {name}/")

    for path in iter_text_files(root):
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(content.splitlines(), start=1):
            match = LEGACY_PATH.search(line)
            if match:
                relative = path.relative_to(root).as_posix()
                problems.append(f"{relative}:{line_number}: legacy path prefix {match.group(1)}/")
    return problems


def main() -> int:
    problems = audit_layout(ROOT)
    if problems:
        print("Repository layout verification failed:")
        print("\n".join(f"- {problem}" for problem in problems))
        return 1
    print("Repository layout verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
