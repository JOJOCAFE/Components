"""Focused tests for the first source-owning Component Board service path."""

from __future__ import annotations

from pathlib import Path

from chiplib.api import handle_request
from chiplib.component_edit import source_revision


ROOT = Path(__file__).resolve().parents[2]
SOURCE = (ROOT / "Language" / "fixtures" / "component-v1.1" / "digital_inverter.component").read_text(encoding="utf-8")


def test_board_example_resolve_run_and_checked_source_edit() -> None:
    example = handle_request({"command": "component-language-example"})
    assert example["ok"] is True
    source = example["result"]["source"]
    board = handle_request({"command": "component-language-board-view", "input": {"source": source}})
    assert board["ok"] is True
    assert board["result"]["component_id"] == "DigitalInverterFixture"
    run = handle_request({"command": "component-language-run", "input": {"source": source}, "options": {"test": "inversion"}})
    assert run["ok"] is True
    assert run["result"]["test"]["ok"] is True

    edited = handle_request({
        "command": "component-language-edit",
        "input": {"source": source, "source_revision": source_revision(source), "edit": {"kind": "connect", "from": "clock", "to": "Observe.IN"}},
    })
    assert edited["ok"] is True
    assert edited["result"]["ok"] is True
    assert edited["result"]["patch"] == {"kind": "connect", "added_line": "connect clock -> Observe.IN;"}
    assert "connect clock -> Observe.IN;" in edited["result"]["source"]


def test_board_edit_rejects_stale_or_missing_connection_without_mutating_text() -> None:
    stale = handle_request({
        "command": "component-language-edit",
        "input": {"source": SOURCE, "source_revision": "sha256:" + "0" * 64, "edit": {"kind": "connect", "from": "clock", "to": "U1.1A"}},
    })
    assert stale["result"]["ok"] is False
    assert stale["result"]["diagnostics"][0]["code"] == "board.stale_source"
    removed = handle_request({
        "command": "component-language-edit",
        "input": {"source": SOURCE, "source_revision": source_revision(SOURCE), "edit": {"kind": "disconnect", "from": "clock", "to": "Observe.IN"}},
    })
    assert removed["result"]["ok"] is False
    assert removed["result"]["source"] == SOURCE


def main() -> None:
    test_board_example_resolve_run_and_checked_source_edit()
    test_board_edit_rejects_stale_or_missing_connection_without_mutating_text()
    print("Component Board API tests passed")


if __name__ == "__main__":
    main()
