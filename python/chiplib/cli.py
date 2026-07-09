"""Command-line entry point for schematic JSON designs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .design import Design
from .db import audit_db, component_summary, db_status_report, load_component


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m chiplib.cli")
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ("validate", "snapshot", "run", "probe", "export-json"):
        cmd = sub.add_parser(name)
        cmd.add_argument("json_file")
        if name == "run":
            cmd.add_argument("--steps", default="all", help="'all' or 'none'")
        if name in ("export-json",):
            cmd.add_argument("-o", "--output")

    for name in ("export-netlist", "export-verilog"):
        cmd = sub.add_parser(name)
        cmd.add_argument("json_file")
        cmd.add_argument("-o", "--output")
        if name == "export-verilog":
            cmd.add_argument("--text", action="store_true", help="write only Verilog source text")

    db = sub.add_parser("db")
    db.add_argument("part", nargs="?", help="optional component part, such as 74HC00")
    db.add_argument("--audit", action="store_true", help="audit DB manifests against legacy catalog files")
    db.add_argument("--status", action="store_true", help="compare DB status categories with CHIP_STATUS.md")
    db.add_argument("-o", "--output")

    args = parser.parse_args(argv)

    if args.command == "db":
        if getattr(args, "audit", False):
            data = audit_db()
            return write_json(data, output=getattr(args, "output", None), status=0 if data["ok"] else 2)
        if getattr(args, "status", False):
            data = db_status_report()
            return write_json(data, output=getattr(args, "output", None), status=0 if data["ok"] else 2)
        part = getattr(args, "part", None)
        data = load_component(part) if part else component_summary()
        return write_json(data, output=getattr(args, "output", None))

    design = Design.load_json(args.json_file)
    if args.command == "validate":
        return write_json(design.validate())
    if args.command == "snapshot":
        design.to_board()
        return write_json(design.snapshot())
    if args.command == "run":
        steps: str | list[str] = [] if args.steps == "none" else "all"
        return write_json(design.run(steps=steps))
    if args.command == "probe":
        design.to_board()
        io = design.to_io()
        io["probes"].sample()
        return write_json(io["probes"].snapshot())
    if args.command == "export-json":
        return write_json(design.to_dict(), output=getattr(args, "output", None))
    if args.command == "export-netlist":
        return write_json(design.to_netlist(), output=getattr(args, "output", None))
    if args.command == "export-verilog":
        exported = design.to_verilog()
        if getattr(args, "text", False):
            return write_text(exported["verilog"], output=getattr(args, "output", None))
        return write_json(exported, output=getattr(args, "output", None), status=0 if exported["ok"] else 2)
    raise AssertionError(args.command)


def write_json(data: Any, *, output: str | None = None, status: int = 0) -> int:
    text = json.dumps(data, indent=2, sort_keys=True) + "\n"
    return write_text(text, output=output, status=status)


def write_text(text: str, *, output: str | None = None, status: int = 0) -> int:
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
