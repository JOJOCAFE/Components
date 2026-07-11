"""Command-line entry point for schematic JSON designs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .db import audit_db, component_catalog, component_detail, component_summary, db_status_report, generate_component_artifacts, load_component, load_component_package, load_digital_definition, student_component_catalog
from .services import DesignCommandService, headless_capabilities, project_builder_workflow
from .virtual_faults import load_circuit_fault_report


def main(argv: list[str] | None = None, *, design_service: DesignCommandService | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m chiplib.cli")
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ("validate", "snapshot", "run", "probe", "export-json", "export-block-ui", "import-block-ui"):
        cmd = sub.add_parser(name)
        cmd.add_argument("json_file")
        if name == "run":
            cmd.add_argument("--steps", default="all", help="'all' or 'none'")
        if name in ("export-json", "export-block-ui", "import-block-ui"):
            cmd.add_argument("-o", "--output")

    for name in ("export-netlist", "export-verilog"):
        cmd = sub.add_parser(name)
        cmd.add_argument("json_file")
        cmd.add_argument("-o", "--output")
        if name == "export-verilog":
            cmd.add_argument("--text", action="store_true", help="write only Verilog source text")

    fault = sub.add_parser("circuit-faults")
    fault.add_argument("json_file")
    fault.add_argument("-o", "--output")

    headless = sub.add_parser("headless", help="emit CLI/API/AI capability manifest")
    headless.add_argument("-o", "--output")

    builder = sub.add_parser("project-builder", help="emit AI/student project-builder workflow")
    builder.add_argument("--part", help="optional selected component, such as 74HC00")
    builder.add_argument("--goal", help="optional project goal text")
    builder.add_argument("-o", "--output")

    db = sub.add_parser("db")
    db.add_argument("part", nargs="?", help="optional component part, such as 74HC00")
    db.add_argument("--audit", action="store_true", help="audit DB manifests against legacy catalog files")
    db.add_argument("--status", action="store_true", help="compare DB status categories with Docs/CHIP_STATUS.md")
    db.add_argument("--catalog", action="store_true", help="emit frontend-oriented component catalog metadata")
    db.add_argument("--student", action="store_true", help="emit learner-facing component catalog metadata")
    db.add_argument("--detail", action="store_true", help="emit frontend-oriented metadata for one component")
    db.add_argument("--digital", action="store_true", help="emit generator-ready definition/definition.json for one component")
    db.add_argument("--package", action="store_true", help="emit definition plus package layers for one component")
    db.add_argument("--generate", action="store_true", help="emit generated artifact data from definition/definition.json")
    db.add_argument("--group", help="filter --catalog by DB group, such as 74xx or memory")
    db.add_argument("-o", "--output")

    args = parser.parse_args(argv)
    designs = design_service or DesignCommandService()

    if args.command == "headless":
        return write_json(headless_capabilities(), output=getattr(args, "output", None))
    if args.command == "project-builder":
        return write_json(
            project_builder_workflow(part=getattr(args, "part", None), goal=getattr(args, "goal", None)),
            output=getattr(args, "output", None),
        )

    if args.command == "db":
        if getattr(args, "audit", False):
            data = audit_db()
            return write_json(data, output=getattr(args, "output", None), status=0 if data["ok"] else 2)
        if getattr(args, "status", False):
            data = db_status_report()
            return write_json(data, output=getattr(args, "output", None), status=0 if data["ok"] else 2)
        part = getattr(args, "part", None)
        if getattr(args, "catalog", False):
            data = component_catalog(group=getattr(args, "group", None))
            return write_json(data, output=getattr(args, "output", None))
        if getattr(args, "student", False):
            data = student_component_catalog(group=getattr(args, "group", None))
            return write_json(data, output=getattr(args, "output", None))
        if getattr(args, "detail", False):
            if not part:
                parser.error("db --detail requires a part")
            data = component_detail(part)
            return write_json(data, output=getattr(args, "output", None))
        if getattr(args, "digital", False):
            if not part:
                parser.error("db --digital requires a part")
            data = load_digital_definition(part)
            return write_json(data, output=getattr(args, "output", None), status=0 if data["validation"]["ok"] else 2)
        if getattr(args, "package", False):
            if not part:
                parser.error("db --package requires a part")
            data = load_component_package(part)
            return write_json(data, output=getattr(args, "output", None), status=0 if data["definition"]["validation"]["ok"] else 2)
        if getattr(args, "generate", False):
            if not part:
                parser.error("db --generate requires a part")
            data = generate_component_artifacts(part)
            return write_json(data, output=getattr(args, "output", None), status=0 if load_digital_definition(part)["validation"]["ok"] else 2)
        data = load_component(part) if part else component_summary()
        return write_json(data, output=getattr(args, "output", None))

    if args.command == "circuit-faults":
        data = load_circuit_fault_report(args.json_file)
        return write_json(data, output=getattr(args, "output", None), status=0 if data["ok"] else 2)
    if args.command == "validate":
        return write_json(designs.validate(args.json_file))
    if args.command == "snapshot":
        return write_json(designs.snapshot(args.json_file))
    if args.command == "run":
        steps: str | list[str] = [] if args.steps == "none" else "all"
        return write_json(designs.run(args.json_file, steps=steps))
    if args.command == "probe":
        return write_json(designs.probe(args.json_file))
    if args.command == "export-json":
        return write_json(designs.export_json(args.json_file), output=getattr(args, "output", None))
    if args.command == "export-block-ui":
        return write_json(designs.export_block_ui(args.json_file), output=getattr(args, "output", None))
    if args.command == "import-block-ui":
        return write_json(designs.import_block_ui(args.json_file), output=getattr(args, "output", None))
    if args.command == "export-netlist":
        return write_json(designs.export_netlist(args.json_file), output=getattr(args, "output", None))
    if args.command == "export-verilog":
        exported = designs.export_verilog(args.json_file)
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
