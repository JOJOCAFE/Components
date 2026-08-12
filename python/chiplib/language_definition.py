"""Component Language statement definitions as data.

Each entry defines one kind of statement the parser can recognize.
Adding a new language feature means adding an entry here + a handler class.
The parser engine itself never changes.

Categories:
  topology  — affects circuit structure (device, net, bus, connect, port, instance)
  stimulus  — affects test input generation (clock, channel, input, reset, step, etc.)
  safety    — runtime invariants and timing contracts
  observe   — read-only observation declarations
  test      — bounded acceptance tests
  meta      — title, use, annotations
"""

from __future__ import annotations
from typing import Any

# Field placeholder tokens used in patterns
# {NAME}     = identifier ([A-Za-z_/][A-Za-z0-9_/]*)
# {LOCATOR}  = dotted identifier ([A-Za-z_][A-Za-z0-9_.]*)
# {ENDPOINT} = net/device.port/bus[n] reference
# {JSON}     = JSON object literal ({...})
# {EXPR}     = expression (everything to end)
# {STRING}   = quoted string ("...")
# {REST}     = rest of line (greedy)

FIELD_PATTERNS = {
    "NAME": r"([A-Za-z_/][A-Za-z0-9_/]*)",
    "NAME_OR_QUOTED": r"([A-Za-z_/][A-Za-z0-9_/]*|\"[^\"]+\")",
    "LOCATOR": r"([A-Za-z_][A-Za-z0-9_.]*)",
    "ENDPOINT": r"([^\s;,]+)",
    "JSON": r"(\{[^}]*\})",
    "EXPR": r"(.+)",
    "STRING": r'("(?:[^"\\\\]|\\\\.)*")',
    "INT": r"(\d+)",
    "REST": r"(.+)",
}


def _def(pattern: str, fields: list[str], *, block: bool = False,
         category: str = "meta", optional_fields: list[str] | None = None) -> dict[str, Any]:
    """Create a statement definition entry."""
    return {
        "pattern": pattern,
        "fields": fields,
        "optional_fields": optional_fields or [],
        "block": block,
        "category": category,
    }


# ============================================================================
# STATEMENT DEFINITIONS — the language grammar as data
# ============================================================================

STATEMENTS: dict[str, dict[str, Any]] = {
    # --- Topology (circuit structure) ---
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

    # --- Stimulus (test signal generation) ---
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
    "repeat": _def("", ["count"], block=True, category="stimulus"),
    "bus_probe": _def(
        r"bus_probe\s+{NAME}\s*,\s*{NAME}\s*,\s*{JSON}",
        ["name", "bus", "parameters"],
        category="observe",
    ),

    # --- Block statements (have { body }) ---
    "input": _def("", ["name"], block=True, category="stimulus"),
    "reset": _def("", ["name"], block=True, category="stimulus"),
    "step": _def("", ["name"], block=True, category="stimulus"),
    "sequence": _def("", ["name", "after"], block=True, category="stimulus"),
    "memory": _def("", ["name"], block=True, category="stimulus"),
    "clock_profile": _def("", ["name"], block=True, category="stimulus"),
    "bus_safety": _def("", ["name"], block=True, category="safety"),
    "policy": _def("", ["name"], block=True, category="safety"),
    "edge_criteria": _def("", ["name"], block=True, category="safety"),
    "timing_check": _def("", ["name"], block=True, category="safety"),
    "test": _def("", ["name"], block=True, category="test"),

    # --- Observation ---
    "probe": _def(
        r"(?:probe|watch)\s+{NAME}\s*,\s*{ENDPOINT}",
        ["name", "target"],
        category="observe",
    ),
    "display": _def(
        r"display\s+{ENDPOINT}\s+as\s+{NAME}(?:\s*,\s*{JSON})?",
        ["target", "display_kind", "options"],
        optional_fields=["options"],
        category="observe",
    ),

    # --- Meta ---
    "title": _def(
        r"title\s+{STRING}",
        ["value"],
        category="meta",
    ),
}


# Block keywords that the statement splitter must recognize
BLOCK_KEYWORDS = frozenset(name for name, defn in STATEMENTS.items() if defn["block"])

# All statement categories
CATEGORIES = {
    "topology": "Circuit structure (device, net, bus, connect, port, instance)",
    "stimulus": "Test signal generation (clock, channel, input, reset, step, derive, memory, sequence, clock_profile)",
    "safety": "Runtime invariants and timing (bus_safety, policy, edge_criteria, timing_check)",
    "observe": "Read-only observations (probe, display, bus_probe)",
    "test": "Bounded acceptance tests",
    "meta": "Metadata (title, use)",
}
