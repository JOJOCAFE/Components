#!/usr/bin/env python3
"""Fail fast if the frozen Language Specification v1.0 document set drifts."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LANGUAGE = ROOT / "Language"
REQUIRED = [
    "00_Manifesto.md",
    "01_Lexical_Specification.md",
    "02_Grammar.md",
    "03_AST_Model.md",
    "04_Name_Resolution.md",
    "05_Object_Model.md",
    "06_Component_Model.md",
    "07_Type_System.md",
    "08_Topology_Model.md",
    "09_Interpreter.md",
    "10_Execution_Model.md",
    "11_JSON_Model.md",
    "12_Standard_Library.md",
    "13_Error_Model.md",
    "14_Parser_Implementation_Guide.md",
    "15_Interpreter_Implementation_Guide.md",
    "README.md",
]


def main() -> int:
    errors: list[str] = []
    for filename in REQUIRED:
        path = LANGUAGE / filename
        if not path.is_file():
            errors.append(f"missing Language/{filename}")
            continue
        text = path.read_text(encoding="utf-8")
        if not text.startswith("# "):
            errors.append(f"Language/{filename} has no top-level title")
        for target in re.findall(r"\]\(([^)#]+\.md)\)", text):
            if not (path.parent / target).is_file():
                errors.append(f"Language/{filename} links missing {target}")

    runtime = LANGUAGE / "09_Interpreter.md"
    if runtime.is_file():
        runtime_text = runtime.read_text(encoding="utf-8")
        if not re.search(r"resolved .*Topology.*never\s+on raw source or raw AST", runtime_text, re.S):
            errors.append("Interpreter must state that runtime executes resolved topology, not AST")
    if (LANGUAGE / "README.md").is_file() and "Board/UI is explicitly deferred" not in (LANGUAGE / "README.md").read_text(encoding="utf-8"):
        errors.append("Language README must keep Board/UI deferred")

    if errors:
        print("LANGUAGE SPEC CHECK FAILED")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print(f"LANGUAGE SPEC CHECK PASS ({len(REQUIRED)} required documents)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
