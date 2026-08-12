"""
Component Language — Statement Definitions
==========================================

This file defines the grammar of the component:component language as DATA.
The parser engine reads this file to know what keywords exist and how to
parse them.  You never need to touch the parser engine itself.

HOW TO ADD A NEW KEYWORD
-------------------------

1. Add an entry to STATEMENTS below:

    "my_keyword": _def(
        r"my_keyword\\s+{NAME}\\s*,\\s*{JSON}",   # regex pattern
        ["name", "parameters"],                     # field names (match groups)
        category="stimulus",                        # which category
    )

2. Add a handler in statement_handlers.py:

    class MyKeywordHandler(StatementHandler):
        def resolve(self, node, ctx):
            ctx.stimulus.append({"kind": "my_keyword", ...})

    HANDLER_REGISTRY["my_keyword"] = MyKeywordHandler()

That's it.  The parser engine and resolver engine never change.

FIELD PLACEHOLDERS
------------------

Use these in patterns — they expand to regex capture groups:

  {NAME}      — identifier: [A-Za-z_/][A-Za-z0-9_/]*
  {LOCATOR}   — dotted name: [A-Za-z_][A-Za-z0-9_.]*
  {ENDPOINT}  — any endpoint reference (until whitespace/semicolon)
  {JSON}      — JSON object: {...}
  {EXPR}      — expression: everything to end of line
  {STRING}    — quoted string: "..."
  {INT}       — integer: digits
  {REST}      — rest of line (greedy)

CATEGORIES
----------

  topology  — circuit structure (device, net, bus, connect, port, instance)
  stimulus  — test signal generation (clock, channel, input, reset, step, etc.)
  safety    — runtime invariants and timing contracts
  observe   — read-only observation declarations
  test      — bounded acceptance tests
  meta      — title, use, annotations
"""

from __future__ import annotations
from typing import Any


# =============================================================================
# FIELD PATTERNS (regex fragments for each placeholder)
# =============================================================================

FIELD_PATTERNS: dict[str, str] = {
    "NAME":           r"([A-Za-z_/][A-Za-z0-9_/]*)",
    "NAME_OR_QUOTED": r"([A-Za-z_/][A-Za-z0-9_/]*|\"[^\"]+\")",
    "LOCATOR":        r"([A-Za-z_][A-Za-z0-9_.]*)",
    "ENDPOINT":       r"([^\s;,]+)",
    "JSON":           r"(\{[^}]*\})",
    "EXPR":           r"(.+)",
    "STRING":         r'("(?:[^"\\\\]|\\\\.)*")',
    "INT":            r"(\d+)",
    "REST":           r"(.+)",
}


# =============================================================================
# HELPER
# =============================================================================

def _def(pattern: str, fields: list[str], *,
         block: bool = False,
         category: str = "meta",
         optional_fields: list[str] | None = None) -> dict[str, Any]:
    """Create a statement definition entry."""
    return {
        "pattern": pattern,
        "fields": fields,
        "optional_fields": optional_fields or [],
        "block": block,
        "category": category,
    }


# =============================================================================
# STATEMENT DEFINITIONS — the complete language grammar
# =============================================================================

STATEMENTS: dict[str, dict[str, Any]] = {

    # ─── Topology (circuit structure) ────────────────────────────────────

    "device": _def(
        r"device\s+{NAME}\s*,\s*{LOCATOR}(?:\s*,\s*{JSON})?",
        ["name", "locator", "parameters"],
        optional_fields=["parameters"],
        category="topology",
    ),

    "net": _def(
        r"net\s+{NAME}\s*:\s*{NAME}",
        ["name", "signal_kind"],
        category="topology",
    ),

    "bus": _def(
        r"bus\s+{NAME}\[{INT}\]\s*:\s*{NAME}",
        ["name", "width", "signal_kind"],
        category="topology",
    ),

    "connect": _def(
        r"connect\s+{ENDPOINT}\s*->\s*{ENDPOINT}",
        ["source", "target"],
        category="topology",
    ),

    "port": _def(
        r"port\s+{NAME}(?:\[{INT}\])?\s*:\s*{NAME}\s*,\s*{NAME}(?:\s*,\s*{JSON})?",
        ["name", "width", "signal_kind", "direction", "metadata"],
        optional_fields=["width", "metadata"],
        category="topology",
    ),

    "instance": _def(
        r"instance\s+{NAME}\s*,\s*{REST}",
        ["name", "source_ref"],
        category="topology",
    ),

    # ─── Stimulus (test signal generation) ───────────────────────────────

    "clock": _def(
        r"clock\s+{NAME}\s*,\s*{ENDPOINT}\s*,\s*{JSON}",
        ["name", "endpoint", "parameters"],
        category="stimulus",
    ),

    "channel": _def(
        r"channel\s+{NAME}\s*,\s*{ENDPOINT}\s*,\s*{JSON}",
        ["name", "endpoint", "parameters"],
        category="stimulus",
    ),

    "derive": _def(
        r"derive\s+{NAME}\s*=\s*{EXPR}",
        ["name", "expression"],
        category="stimulus",
    ),

    "release": _def(
        r"release\s+{ENDPOINT}",
        ["endpoint"],
        category="stimulus",
    ),

    # Block stimulus (have { body })
    "input":         _def("", ["name"], block=True, category="stimulus"),
    "reset":         _def("", ["name"], block=True, category="stimulus"),
    "step":          _def("", ["name"], block=True, category="stimulus"),
    "sequence":      _def("", ["name", "after"], block=True, category="stimulus"),
    "memory":        _def("", ["name"], block=True, category="stimulus"),
    "clock_profile": _def("", ["name"], block=True, category="stimulus"),
    "repeat":        _def("", ["count"], block=True, category="stimulus"),

    # ─── Safety & Timing ─────────────────────────────────────────────────

    "bus_safety":    _def("", ["name"], block=True, category="safety"),
    "policy":        _def("", ["name"], block=True, category="safety"),
    "edge_criteria": _def("", ["name"], block=True, category="safety"),
    "timing_check":  _def("", ["name"], block=True, category="safety"),

    # ─── Observation ─────────────────────────────────────────────────────

    "probe": _def(
        r"(?:probe|watch)\s+{NAME}\s*,\s*{ENDPOINT}",
        ["name", "target"],
        category="observe",
    ),

    "bus_probe": _def(
        r"bus_probe\s+{NAME}\s*,\s*{NAME}\s*,\s*{JSON}",
        ["name", "bus", "parameters"],
        category="observe",
    ),

    "display": _def(
        r"display\s+{ENDPOINT}\s+as\s+{NAME}(?:\s*,\s*{JSON})?",
        ["target", "display_kind", "options"],
        optional_fields=["options"],
        category="observe",
    ),

    # ─── Test ────────────────────────────────────────────────────────────

    "test": _def("", ["name"], block=True, category="test"),

    # ─── Meta ────────────────────────────────────────────────────────────

    "title": _def(
        r"title\s+{STRING}",
        ["value"],
        category="meta",
    ),
}


# =============================================================================
# DERIVED CONSTANTS (computed from STATEMENTS)
# =============================================================================

# Block keywords the statement splitter must recognize
BLOCK_KEYWORDS: frozenset[str] = frozenset(
    name for name, defn in STATEMENTS.items() if defn["block"]
)

# Category descriptions (for help/docs generation)
CATEGORIES: dict[str, str] = {
    "topology": "Circuit structure (device, net, bus, connect, port, instance)",
    "stimulus": "Test signal generation (clock, channel, input, reset, step, derive, memory, sequence, clock_profile, release, repeat)",
    "safety":   "Runtime invariants and timing (bus_safety, policy, edge_criteria, timing_check)",
    "observe":  "Read-only observations (probe, display, bus_probe)",
    "test":     "Bounded acceptance tests",
    "meta":     "Metadata (title)",
}
