"""
Component Language — Parser Engine
===================================

Generic parser that turns component:component source text into an AST.
It reads statement definitions from language_definition.py and matches
them against source lines.

THIS FILE NEVER CHANGES when adding new keywords.
New keywords go in language_definition.py + statement_handlers.py only.

Pipeline:
    source text → strip comments → find header → split statements → match patterns → AST JSON
"""

from __future__ import annotations

import json
import re
from typing import Any

from .language_definition import STATEMENTS, BLOCK_KEYWORDS, FIELD_PATTERNS

JsonMap = dict[str, Any]


# =============================================================================
# COMPILED PATTERNS (built lazily, cached)
# =============================================================================

_COMPILED: dict[str, re.Pattern | None] = {}

_HEADER_RE = re.compile(
    r"component:component\s+([A-Za-z_][A-Za-z0-9_]*)"
    r"\s+(?:is\s+([A-Za-z_][A-Za-z0-9_.]*))?\s*\{"
)

_USE_RE = re.compile(
    r"\buse\s+([A-Za-z_][A-Za-z0-9_.]*)"
    r"(?:\s+as\s+([A-Za-z_][A-Za-z0-9_]*))?\s*;"
)

_BLOCK_HEADER_RE = re.compile(
    r"(\w+)\s+([^\s{]+)\s*(?:after\s+(\w+)\s*)?\{(.*)}",
    re.DOTALL,
)


def _compile_patterns() -> None:
    """Compile regex patterns from statement definitions (once)."""
    if _COMPILED:
        return
    for name, defn in STATEMENTS.items():
        raw = defn["pattern"]
        if not raw:
            _COMPILED[name] = None
            continue
        regex = raw
        for field_name, field_re in FIELD_PATTERNS.items():
            regex = regex.replace("{" + field_name + "}", field_re)
        _COMPILED[name] = re.compile(regex + "$")


# =============================================================================
# DIAGNOSTIC
# =============================================================================

class Diagnostic:
    """A parse or resolve error/warning with source location."""
    __slots__ = ("code", "message", "line", "severity")

    def __init__(self, code: str, message: str, line: int, severity: str = "error"):
        self.code = code
        self.message = message
        self.line = line
        self.severity = severity

    def as_dict(self) -> JsonMap:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
            "span": {"line": self.line},
        }


# =============================================================================
# COMMENT STRIPPING
# =============================================================================

def _without_comments(source: str) -> str:
    """Remove all comments: //, --, and /* */."""
    # Block comments first (may span lines)
    result = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    # Line comments
    lines = []
    for line in result.splitlines():
        # Strip // comments
        stripped = line.split("//", 1)[0]
        # Strip -- comments (unless inside quotes)
        dash_idx = stripped.find("--")
        if dash_idx >= 0 and stripped[:dash_idx].count('"') % 2 == 0:
            stripped = stripped[:dash_idx]
        lines.append(stripped)
    return "\n".join(lines)


# =============================================================================
# STATEMENT SPLITTING
# =============================================================================

def _line_number(source: str, offset: int) -> int:
    """Character offset → 1-based line number."""
    return source.count("\n", 0, offset) + 1


def _span(line: int, text: str) -> JsonMap:
    """Compact source span."""
    return {"line": line, "end_line": line + text.count("\n")}


def split_statements(source: str, start: int) -> tuple[list[tuple[str, int]], list[Diagnostic]]:
    """Split the Component body into individual statements.

    Handles:
    - Semicolons terminate single-line statements at depth 1
    - Block keywords { ... } are captured as one statement (braces balanced)
    - The final } closes the Component body
    """
    items: list[tuple[str, int]] = []
    errors: list[Diagnostic] = []
    depth = 1
    stmt_start = start

    for i in range(start, len(source)):
        ch = source[i]

        if ch == "{":
            depth += 1

        elif ch == "}":
            depth -= 1
            if depth == 0:
                # End of Component body
                tail = source[stmt_start:i].strip()
                if tail:
                    first = tail.split()[0] if tail.split() else ""
                    line = _line_number(source, stmt_start)
                    if first in BLOCK_KEYWORDS and tail.endswith("}"):
                        items.append((tail, line))
                    elif tail:
                        errors.append(Diagnostic(
                            "parser.missing_semicolon",
                            "expected ';' before Component closing brace", line))
                return items, errors

            elif depth == 1:
                # End of a nested block — capture it
                text = source[stmt_start:i + 1].strip()
                first = text.split()[0] if text.split() else ""
                if first in BLOCK_KEYWORDS and "{" in text:
                    items.append((text, _line_number(source, stmt_start)))
                    stmt_start = i + 1

        elif ch == ";" and depth == 1:
            text = source[stmt_start:i].strip()
            if text:
                items.append((text, _line_number(source, stmt_start)))
            stmt_start = i + 1

    errors.append(Diagnostic(
        "parser.unclosed_component",
        "Component body has no closing '}'",
        _line_number(source, start)))
    return items, errors


# =============================================================================
# STATEMENT MATCHING
# =============================================================================

def match_statement(text: str, line: int) -> tuple[JsonMap | None, str | None]:
    """Match a statement against registered patterns.

    Returns (node, None) on success, or (None, error_message) on failure.
    """
    _compile_patterns()
    first_word = text.split()[0] if text.split() else ""

    # Block statements (contain { })
    if first_word in BLOCK_KEYWORDS and "{" in text and text.endswith("}"):
        return _parse_block(first_word, text, line), None

    # Single-line patterns
    for name, pattern in _COMPILED.items():
        if pattern is None:
            continue
        m = pattern.fullmatch(text)
        if m:
            return _build_node(name, m, line, text), None

    return None, f"unsupported Component statement: {first_word!r}"


def _build_node(kind: str, match: re.Match, line: int, text: str) -> JsonMap:
    """Build an AST node from a regex match."""
    defn = STATEMENTS[kind]
    fields = defn["fields"]
    optional = set(defn.get("optional_fields", []))
    node: JsonMap = {"kind": kind, "span": _span(line, text)}

    groups = match.groups()
    for i, field in enumerate(fields):
        if i >= len(groups):
            node[field] = None
            continue
        value = groups[i]
        if value is None:
            node[field] = None
        elif field in ("parameters", "options", "metadata"):
            try:
                node[field] = json.loads(value) if value else {}
            except (json.JSONDecodeError, TypeError):
                node[field] = {}
        elif field == "width":
            node[field] = int(value) if value else None
        elif field == "value" and value.startswith('"'):
            node[field] = json.loads(value)
        elif field == "source_ref":
            node[field] = value.strip().rstrip(";")
        else:
            node[field] = value.strip() if isinstance(value, str) else value

    # Fill missing optional fields
    for field in fields:
        if field not in node:
            node[field] = None

    return node


def _parse_block(kind: str, text: str, line: int) -> JsonMap:
    """Parse a block statement: keyword name [after X] { body }."""
    m = _BLOCK_HEADER_RE.match(text)
    if m:
        node: JsonMap = {
            "kind": kind,
            "name": m.group(2).strip(),
            "body": m.group(4).strip(),
            "span": _span(line, text),
            "execution": "deferred-operation-runtime",
        }
        if m.group(3):
            node["after"] = m.group(3)
        return node
    return {
        "kind": kind,
        "text": text,
        "span": _span(line, text),
        "execution": "deferred-operation-runtime",
    }


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def parse_source(source: str, *, source_name: str = "<memory>") -> JsonMap:
    """Parse component:component source into AST JSON.

    This is the main parser entry point.

    Returns:
        {
            "schema": "components.component-ast@1",
            "source": "<filename>",
            "ok": true/false,
            "uses": [...],
            "component": { "kind": "component", "name": ..., "body": [...] },
            "diagnostics": [...]
        }
    """
    clean = _without_comments(source)
    diagnostics: list[Diagnostic] = []

    # Find component header
    match = _HEADER_RE.search(clean)
    if not match:
        diagnostics.append(Diagnostic(
            "parser.component_header",
            "expected 'component:component Name is profile {'", 1))
        return {
            "schema": "components.component-ast@1",
            "source": source_name,
            "ok": False,
            "uses": [],
            "component": None,
            "diagnostics": [d.as_dict() for d in diagnostics],
        }

    # Imports
    uses = [
        {"kind": "use", "library": m.group(1), "alias": m.group(2),
         "span": {"line": _line_number(clean, m.start())}}
        for m in _USE_RE.finditer(clean)
    ]

    # Split body into statements
    statements, split_errors = split_statements(clean, match.end())
    diagnostics.extend(split_errors)

    # Parse each statement
    nodes: list[JsonMap] = []
    for text, line in statements:
        node, error = match_statement(text, line)
        if node:
            nodes.append(node)
        else:
            diagnostics.append(Diagnostic("parser.unsupported_statement", error, line))
            nodes.append({"kind": "unknown", "text": text, "span": _span(line, text)})

    component = {
        "kind": "component",
        "name": match.group(1),
        "profile": match.group(2),
        "body": nodes,
        "span": _span(_line_number(clean, match.start()), match.group(0)),
    }

    return {
        "schema": "components.component-ast@1",
        "source": source_name,
        "ok": not any(d.severity == "error" for d in diagnostics),
        "uses": uses,
        "component": component,
        "diagnostics": [d.as_dict() for d in diagnostics],
    }
