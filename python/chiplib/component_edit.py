"""Checked, source-owning edits for the small Component Board client.

The Board never owns a parallel canvas netlist.  It sends a small intent and
receives readable Component text only after the normal parser/resolver accepts
it. This module owns declarations and explicit scalar connections; it never
accepts visual coordinates or a parallel canvas netlist.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from .component_language import parse_component_text, resolve_component


_ENDPOINT = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*(?:\.(?:[A-Za-z0-9_][A-Za-z0-9_]*|@\d+|"(?:[^"\\]|\\.)*"))?(?:\[\d+\])?$')
_IDENTIFIER = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
_LIBRARY_REFERENCE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z0-9_]+$')
_SIGNAL_KIND = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')


def source_revision(source: str) -> str:
    """Return a stable revision token for an exact authored source string."""

    return "sha256:" + hashlib.sha256(source.encode("utf-8")).hexdigest()


def apply_component_edit(
    source: str, *, expected_revision: str, edit: dict[str, Any], source_name: str = "<board>"
) -> dict[str, Any]:
    """Apply one validated source edit, or return diagnostics without mutation."""

    prepared, candidate = _prepare_component_edit(
        source, expected_revision=expected_revision, edit=edit, source_name=source_name,
    )
    if candidate is None:
        return prepared
    patch, ast, resolved = prepared
    return {
        "format": "components.component-edit@1", "ok": True,
        "source": candidate, "source_revision": source_revision(candidate),
        "patch": patch, "ast": ast, "resolved": resolved,
        "diagnostics": [],
        "student": {"message": f"Text updated: {_line_for_patch(patch)}", "next_action": "Read the new line, then follow the refreshed Drawing."},
    }


def preview_component_edit(
    source: str, *, expected_revision: str, edit: dict[str, Any], source_name: str = "<board>"
) -> dict[str, Any]:
    """Validate a prospective Board patch without returning changed source.

    This is deliberately a pure preview.  The current text and revision remain
    the response source of truth; a later explicit apply must repeat the same
    revision-checked request.
    """
    prepared, candidate = _prepare_component_edit(
        source, expected_revision=expected_revision, edit=edit, source_name=source_name,
    )
    if candidate is None:
        prepared["format"] = "components.component-edit-preview@1"
        return prepared
    patch, _ast, resolved = prepared
    canonical = json.dumps(resolved, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "format": "components.component-edit-preview@1", "ok": True,
        "source": source, "source_revision": source_revision(source),
        "patch": patch,
        "candidate_source_revision": source_revision(candidate),
        "resolved_digest": "sha256:" + hashlib.sha256(canonical).hexdigest(),
        "diagnostics": [],
        "student": {"message": f"Proposed: {_line_for_patch(patch)}", "next_action": "Review the proposed source line, then explicitly apply it."},
    }


def _prepare_component_edit(
    source: str, *, expected_revision: str, edit: dict[str, Any], source_name: str
) -> tuple[dict[str, Any] | tuple[dict[str, Any], dict[str, Any], dict[str, Any]], str | None]:
    """Return checked patch facts and candidate text, never mutating input."""
    current_revision = source_revision(source)
    if expected_revision != current_revision:
        return _rejected(
            source, current_revision, "board.stale_source",
            "This Board action was made for an older text version. Read the current text, then try again.",
        ), None
    kind = edit.get("kind")
    if kind in {"connect", "disconnect"}:
        from_endpoint, to_endpoint = edit.get("from"), edit.get("to")
        if not isinstance(from_endpoint, str) or not isinstance(to_endpoint, str):
            return _rejected(source, current_revision, "board.edit_shape", "Choose a connection action and two named endpoints."), None
        if not _ENDPOINT.fullmatch(from_endpoint) or not _ENDPOINT.fullmatch(to_endpoint):
            return _rejected(source, current_revision, "board.endpoint_syntax", "Use a declared net or a Device port such as U1.1Y."), None
        line = f"connect {from_endpoint} -> {to_endpoint};"
        if kind == "connect":
            if _connection_exists(source, from_endpoint, to_endpoint):
                return _rejected(source, current_revision, "board.connection_exists", "That connection is already written in this Component."), None
            candidate = _insert_connection(source, line)
            patch = {"kind": "connect", "added_line": line}
        else:
            candidate, removed = _remove_connection(source, from_endpoint, to_endpoint)
            if not removed:
                return _rejected(source, current_revision, "board.connection_missing", "That exact connection is not written in this Component."), None
            patch = {"kind": "disconnect", "removed_line": line}
    elif kind == "add_device":
        identifier, part = edit.get("id"), edit.get("part")
        if not isinstance(identifier, str) or not isinstance(part, str) or not _IDENTIFIER.fullmatch(identifier) or not _LIBRARY_REFERENCE.fullmatch(part):
            return _rejected(source, current_revision, "board.device_shape", "Use a new device name and library part such as U2 and digital.74HC04."), None
        line = f"device {identifier}, {part};"
        candidate = _insert_declaration(source, line)
        patch = {"kind": kind, "added_line": line}
    elif kind in {"add_net", "add_bus"}:
        identifier, signal_kind = edit.get("id"), edit.get("signal_kind")
        if not isinstance(identifier, str) or not isinstance(signal_kind, str) or not _IDENTIFIER.fullmatch(identifier) or not _SIGNAL_KIND.fullmatch(signal_kind):
            return _rejected(source, current_revision, "board.signal_shape", "Use a signal name and kind such as data and digital."), None
        if kind == "add_net":
            line = f"net {identifier} : {signal_kind};"
        else:
            width = edit.get("width")
            if not isinstance(width, int) or isinstance(width, bool) or width < 1:
                return _rejected(source, current_revision, "board.bus_width", "Choose a bus width of at least 1."), None
            line = f"bus {identifier}[{width}] : {signal_kind};"
        candidate = _insert_declaration(source, line)
        patch = {"kind": kind, "added_line": line}
    else:
        return _rejected(source, current_revision, "board.edit_shape", "Choose a supported add, connect, or disconnect command."), None

    ast = parse_component_text(candidate, source_name=source_name)
    resolved = resolve_component(ast)
    if not resolved.get("ok"):
        return {
            "format": "components.component-edit@1", "ok": False,
            "source": source, "source_revision": current_revision,
            "diagnostics": resolved.get("diagnostics", []),
            "student": {"message": "I did not change the text because this command is not valid yet.", "next_action": "Read the diagnostic and use declared names and library parts."},
        }, None
    return (patch, ast, resolved), candidate


def _line_for_patch(patch: dict[str, Any]) -> str:
    return str(patch.get("added_line", patch.get("removed_line", "connection edit")))


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


def _insert_declaration(source: str, line: str) -> str:
    """Insert a readable declaration before the first connection or observation."""

    insertion = re.search(r"^\s*(?:connect|probe|watch|display|test)\b", source, re.MULTILINE)
    if insertion:
        return source[:insertion.start()] + f"  {line}\n" + source[insertion.start():]
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
