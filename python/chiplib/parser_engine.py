"""Generic component:component parser engine.

This engine reads statement definitions from language_definition.py and
uses them to parse source text into AST nodes.  It knows nothing about
specific language keywords — those come from the definition data.

To add a new keyword: add it to language_definition.py and (optionally)
create a handler in statement_handlers.py.  This file never changes.
"""

from __future__ import annotations

import json
import re
from typing import Any

from .language_definition import STATEMENTS, BLOCK_KEYWORDS, FIELD_PATTERNS

JsonMap = dict[str, Any]

# Compiled patterns (built once at import time)
_COMPILED: dict[str, re.Pattern | None] = {}

_HEADER_RE = re.compile(
    r"component:component\s+([A-Za-z_][A-Za-z0-9_]*)\s+(?:is\s+([A-Za-z_][A-Za-z0-9_.]*))?\s*\{"
)
_USE_RE = re.compile(
    r"\buse\s+([A-Za-z_][A-Za-z0-9_.]*)(?:\s+as\s+([A-Za-z_][A-Za-z0-9_]*))?\s*;"
)


def _compile_patterns() -> None:
    """Compile statement patterns from definitions into regex objects."""
    if _COMPILED:
        return
    for name, defn in STATEMENTS.items():
        raw = defn["pattern"]
        if not raw:
            _COMPILED[name] = None
            continue
        # Replace field placeholders with capture groups
        regex = raw
        for field_name, field_re in FIELD_PATTERNS.items():
            regex = regex.replace("{" + field_name + "}", field_re)
        _COMPILED[name] = re.compile(regex + "$")


def _without_comments(source: str) -> str:
    """Strip //, --, and /* */ style comments from source."""
    # First pass: strip block comments /* ... */
    result = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    # Second pass: strip line comments (// and --)
    lines = []
    for line in result.splitlines():
        stripped = line.split("//", 1)[0]
        dash_idx = stripped.find("--")
        if dash_idx >= 0:
            pre = stripped[:dash_idx]
            if pre.count('"') % 2 == 0:
                stripped = pre
        lines.append(stripped)
    return "\n".join(lines)


def _line_number(source: str, offset: int) -> int:
    """Convert character offset to 1-based line number."""
    return source.count("\n", 0, offset) + 1


def _span(line: int, text: str) -> JsonMap:
    """Compact source span."""
    return {"line": line, "end_line": line + text.count("\n")}


class Diagnostic:
    """A single parse/resolve diagnostic."""
    __slots__ = ("code", "message", "line", "severity")

    def __init__(self, code: str, message: str, line: int, severity: str = "error"):
        self.code = code
        self.message = message
        self.line = line
        self.severity = severity

    def as_dict(self) -> JsonMap:
        return {"code": self.code, "message": self.message,
                "severity": self.severity, "span": {"line": self.line}}


def split_statements(source: str, start: int) -> tuple[list[tuple[str, int]], list[Diagnostic]]:
    """Split top-level Component body into statements.

    Handles:
    - Semicolon-terminated single-line statements
    - Block statements (keyword { ... }) that end with }
    - Nested braces within blocks
    """
    items: list[tuple[str, int]] = []
    errors: list[Diagnostic] = []
    depth = 1
    statement_start = start

    for index in range(start, len(source)):
        char = source[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                # End of the Component body
                tail = source[statement_start:index].strip()
                if tail:
                    line = _line_number(source, statement_start)
                    first_word = tail.split()[0] if tail.split() else ""
                    if first_word in BLOCK_KEYWORDS and tail.endswith("}"):
                        items.append((tail, line))
                    elif tail:
                        errors.append(Diagnostic("parser.missing_semicolon",
                            "expected ';' before Component closing brace", line))
                return items, errors
            elif depth == 1:
                # End of a nested block
                text = source[statement_start:index + 1].strip()
                first_word = text.split()[0] if text.split() else ""
                if first_word in BLOCK_KEYWORDS and "{" in text:
                    line = _line_number(source, statement_start)
                    items.append((text, line))
                    statement_start = index + 1
        elif char == ";" and depth == 1:
            text = source[statement_start:index].strip()
            if text:
                line = _line_number(source, statement_start)
                items.append((text, line))
            statement_start = index + 1

    errors.append(Diagnostic("parser.unclosed_component",
        "Component body has no closing '}'", _line_number(source, start)))
    return items, errors


def match_statement(text: str, line: int) -> tuple[JsonMap | None, str | None]:
    """Try to match a statement against all registered patterns.

    Returns (node, None) on match, or (None, error_message) on failure.
    """
    _compile_patterns()

    # Try block keywords first (they contain { })
    first_word = text.split()[0] if text.split() else ""
    if first_word in BLOCK_KEYWORDS and "{" in text and text.endswith("}"):
        return _parse_block(first_word, text, line), None

    # Try single-line patterns
    for name, pattern in _COMPILED.items():
        if pattern is None:
            continue
        match = pattern.fullmatch(text)
        if match:
            return _build_node(name, match, line, text), None

    return None, f"unsupported Component statement: {first_word!r}"


def _build_node(kind: str, match: re.Match, line: int, text: str) -> JsonMap:
    """Build an AST node from a regex match using the definition's field list."""
    defn = STATEMENTS[kind]
    fields = defn["fields"]
    optional = set(defn.get("optional_fields", []))
    node: JsonMap = {"kind": kind, "span": _span(line, text)}

    groups = match.groups()
    field_idx = 0
    for i, field in enumerate(fields):
        if field_idx >= len(groups):
            if field in optional:
                node[field] = None
            break
        value = groups[field_idx]
        field_idx += 1

        if value is None:
            node[field] = None
            continue

        # Type conversion based on field name conventions
        if field == "parameters" or field == "options" or field == "metadata":
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
    """Parse a block statement (keyword name { body })."""
    # Match: keyword name [after qualifier] { body }
    block_re = re.compile(r"(\w+)\s+([^\s{]+)\s*(?:after\s+(\w+)\s*)?\{(.*)}", re.DOTALL)
    m = block_re.match(text)
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
    # Fallback
    return {"kind": kind, "text": text, "span": _span(line, text),
            "execution": "deferred-operation-runtime"}


def parse_source(source: str, *, source_name: str = "<memory>") -> JsonMap:
    """Parse component:component source into AST JSON.

    This is the main entry point. Returns the same schema as the old
    parse_component_text() for backward compatibility.
    """
    clean = _without_comments(source)
    diagnostics: list[Diagnostic] = []

    # Find component header
    match = _HEADER_RE.search(clean)
    if not match:
        diagnostics.append(Diagnostic("parser.component_header",
            "expected 'component:component Name is profile {'", 1))
        return {
            "schema": "components.component-ast@1",
            "source": source_name,
            "ok": False,
            "uses": [],
            "component": None,
            "diagnostics": [d.as_dict() for d in diagnostics],
        }

    # Collect use/import declarations
    uses = []
    for use in _USE_RE.finditer(clean):
        uses.append({
            "kind": "use",
            "library": use.group(1),
            "alias": use.group(2),
            "span": {"line": _line_number(clean, use.start())},
        })

    # Split body into statements
    statements, split_errors = split_statements(clean, match.end())
    diagnostics.extend(split_errors)

    # Parse each statement against definitions
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
