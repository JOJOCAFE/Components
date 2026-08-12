"""Text-first ``component:component`` parser and resolver.

This module is the public API for parsing and resolving Component source.
It delegates to the definition-driven parser engine and pluggable handler
architecture:

  language_definition.py  — statement grammar as data (patterns, fields, categories)
  parser_engine.py        — generic parser (matches patterns, splits blocks)
  statement_handlers.py   — one handler class per statement kind (parse + resolve)
  resolver_engine.py      — ResolutionContext + dispatch + topology validation

To add a new language keyword:
  1. Add an entry to language_definition.py STATEMENTS dict
  2. Add a handler class to statement_handlers.py
  3. Register it in statement_handlers.HANDLER_REGISTRY
  4. (This file never changes)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .parser_engine import parse_source, Diagnostic
from .resolver_engine import resolve

JsonMap = dict[str, Any]


def parse_component_text(source: str, *, source_name: str = "<memory>") -> JsonMap:
    """Parse component:component source text into AST JSON.

    Returns a schema-stable AST with diagnostics. The AST contains no
    resolved types, pin numbers, or topology — only authored declarations.
    """
    return parse_source(source, source_name=source_name)


def parse_component_file(path: str | Path) -> JsonMap:
    """Parse a component:component file from disk."""
    file_path = Path(path)
    return parse_source(
        file_path.read_text(encoding="utf-8"),
        source_name=str(file_path),
    )


def resolve_component(ast: JsonMap) -> JsonMap:
    """Resolve a parsed Component AST against the active DB.

    Takes the output of parse_component_text() and validates every device
    locator, port reference, and connection against the chip definitions.
    Returns an immutable resolved topology ready for simulation.
    """
    return resolve(ast)


def component_ide_snapshot(path: str | Path) -> JsonMap:
    """Return a text-IDE friendly, serializable source/AST/resolution snapshot.

    Used by CLI and API for editor integration.
    """
    ast = parse_component_file(path)
    resolved = resolve_component(ast)
    return {
        "format": "components.text_ide@1",
        "ok": bool(resolved.get("ok")),
        "source": ast.get("source"),
        "ast": ast,
        "resolved": resolved,
        "capabilities": {
            "parse": True,
            "resolve": True,
            "validate": True,
            "run": False,
            "board": False,
        },
        "next": "Fix diagnostics, then use the existing JSON circuit runner for "
                "executable packages; Component Runtime execution is deferred.",
    }
