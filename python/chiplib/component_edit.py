"""Checked, source-owning edits for the small Component Board client.

The Board never owns a parallel canvas netlist.  It sends a small intent and
receives readable Component text only after the normal parser/resolver accepts
it.  This module deliberately implements only the first two safe edits:
add/remove one explicit scalar connection.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

from .component_language import parse_component_text, resolve_component


_ENDPOINT = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*(?:\.(?:[A-Za-z_][A-Za-z0-9_]*|@\d+|"(?:[^"\\]|\\.)*"))?(?:\[\d+\])?$')


def source_revision(source: str) -> str:
    """Return a stable revision token for an exact authored source string."""

    return "sha256:" + hashlib.sha256(source.encode("utf-8")).hexdigest()


def apply_component_edit(
    source: str, *, expected_revision: str, edit: dict[str, Any], source_name: str = "<board>"
) -> dict[str, Any]:
    """Apply one validated source edit, or return diagnostics without mutation."""

    current_revision = source_revision(source)
    if expected_revision != current_revision:
        return _rejected(
            source, current_revision, "board.stale_source",
            "This Board action was made for an older text version. Read the current text, then try again.",
        )
    kind = edit.get("kind")
    from_endpoint, to_endpoint = edit.get("from"), edit.get("to")
    if kind not in {"connect", "disconnect"} or not isinstance(from_endpoint, str) or not isinstance(to_endpoint, str):
        return _rejected(source, current_revision, "board.edit_shape", "Choose a connection action and two named endpoints.")
    if not _ENDPOINT.fullmatch(from_endpoint) or not _ENDPOINT.fullmatch(to_endpoint):
        return _rejected(source, current_revision, "board.endpoint_syntax", "Use a declared net or a Device port such as U1.1Y.")
    line = f"connect {from_endpoint} -> {to_endpoint};"
    if kind == "connect":
        if _connection_exists(source, from_endpoint, to_endpoint):
            return _rejected(source, current_revision, "board.connection_exists", "That connection is already written in this Component.")
        candidate = _insert_connection(source, line)
        patch = {"kind": "connect", "added_line": line}
    else:
        candidate, removed = _remove_connection(source, from_endpoint, to_endpoint)
        if not removed:
            return _rejected(source, current_revision, "board.connection_missing", "That exact connection is not written in this Component.")
        patch = {"kind": "disconnect", "removed_line": line}

    ast = parse_component_text(candidate, source_name=source_name)
    resolved = resolve_component(ast)
    if not resolved.get("ok"):
        return {
            "format": "components.component-edit@1", "ok": False,
            "source": source, "source_revision": current_revision,
            "diagnostics": resolved.get("diagnostics", []),
            "student": {"message": "I did not change the text because this connection is not valid yet.", "next_action": "Read the highlighted endpoints and try a legal direction."},
        }
    return {
        "format": "components.component-edit@1", "ok": True,
        "source": candidate, "source_revision": source_revision(candidate),
        "patch": patch, "ast": ast, "resolved": resolved,
        "diagnostics": [],
        "student": {"message": f"Text updated: {line}", "next_action": "Read the new line, then follow the refreshed Drawing."},
    }


def _connection_exists(source: str, from_endpoint: str, to_endpoint: str) -> bool:
    pattern = re.compile(rf"^\s*connect\s+{re.escape(from_endpoint)}\s*->\s*{re.escape(to_endpoint)}\s*;\s*(?://.*)?$", re.MULTILINE)
    return bool(pattern.search(source))


def _insert_connection(source: str, line: str) -> str:
    """Insert beside existing connections, before learner observations/tests."""

    insertion = re.search(r"^\s*(?:probe|watch|display|test)\b", source, re.MULTILINE)
    if insertion:
        start = insertion.start()
        indent = re.match(r"\s*", source[start:]).group(0)
        return source[:start] + f"  {line}\n\n" + source[start:]
    close = source.rfind("}")
    if close < 0:
        return source + f"\n  {line}\n"
    return source[:close].rstrip() + f"\n\n  {line}\n" + source[close:]


def _remove_connection(source: str, from_endpoint: str, to_endpoint: str) -> tuple[str, bool]:
    pattern = re.compile(rf"^\s*connect\s+{re.escape(from_endpoint)}\s*->\s*{re.escape(to_endpoint)}\s*;\s*(?://.*)?\n?", re.MULTILINE)
    candidate, count = pattern.subn("", source, count=1)
    return candidate, count == 1


def _rejected(source: str, revision: str, code: str, message: str) -> dict[str, Any]:
    return {
        "format": "components.component-edit@1", "ok": False,
        "source": source, "source_revision": revision,
        "diagnostics": [{"code": code, "message": message, "severity": "error"}],
        "student": {"message": message, "next_action": "Keep the readable text unchanged, then choose a valid next step."},
    }
