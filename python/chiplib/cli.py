"""Command-line entry point for schematic JSON designs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .db import audit_db, component_catalog, component_detail, component_summary, db_status_report, generate_component_artifacts, load_component, load_component_package, load_digital_definition, student_component_catalog
from .services import CircuitCommandService, DesignCommandService, headless_capabilities, project_builder_workflow
from .virtual_faults import load_circuit_fault_report
from .component_language import component_ide_snapshot, parse_component_file, resolve_component
from .component_runtime import ComponentRuntimeError, ComponentRuntimeSession
from .component_resources import bind_resource, inspect_resource


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

    for name in ("component-parse", "component-resolve", "component-validate", "component-ide"):
        cmd = sub.add_parser(name, help="parse/resolve a text component:component source file")
        cmd.add_argument("component_file")
        cmd.add_argument("-o", "--output")
    component_run = sub.add_parser("component-run", help="instantiate a validated leaf Component in the digital model")
    component_run.add_argument("component_file")
    component_run.add_argument("--drive", action="append", default=[], help="target=value; repeat for several explicit operation drivers")
    component_run.add_argument("--probe", help="one probe/watch name; omit for all")
    component_run.add_argument("--test", help="run one declared beginner test")
    component_run.add_argument("-o", "--output")
    component_student = sub.add_parser("component-student", help="show a short learner-friendly Component summary")
    component_student.add_argument("component_file")
    component_student.add_argument("-o", "--output")
    resource_inspect = sub.add_parser("component-resource-inspect", help="show a presentation Resource without changing a Device")
    resource_inspect.add_argument("part", help="component part, such as 74HC04")
    resource_inspect.add_argument("-o", "--output")
    resource_bind = sub.add_parser("component-resource-bind", help="create presentation-only Resource binding JSON for one resolved Device")
    resource_bind.add_argument("component_file")
    resource_bind.add_argument("--target", required=True, help="existing Device instance ID, such as U1")
    resource_bind.add_argument("--resource", required=True, help="matching library part, such as 74HC04")
    resource_bind.add_argument("--view", required=True, help="declared Resource view, such as dip")
    resource_bind.add_argument("--label", help="optional student-facing label")
    resource_bind.add_argument("-o", "--output")

    for name in ("circuit-validate", "circuit-run", "circuit-step", "circuit-probe", "timed-run"):
        cmd = sub.add_parser(name)
        cmd.add_argument("json_file")
        if name in {"circuit-run", "timed-run"}:
            cmd.add_argument("--op", action="append", default=[], help="operation; repeat for multiple operations")
        if name == "circuit-step":
            cmd.add_argument("--op", required=True, help="one operation")
        if name == "circuit-probe":
            cmd.add_argument("--name", help="one output/probe name; omit to read all outputs")

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

    explain = sub.add_parser("explain-result", help="explain a prior CLI/API result JSON without rerunning hardware logic")
    explain.add_argument("json_file")
    explain.add_argument("--source-command", help="override source command name when the JSON does not include command")
    explain.add_argument("-o", "--output")

    explain_violations = sub.add_parser("explain-violations", help="explain existing circuit-runner violations without rerunning")
    explain_violations.add_argument("json_file")
    explain_violations.add_argument("-o", "--output")

    evidence = sub.add_parser("export-evidence", help="export existing circuit-runner evidence without upgrading its claims")
    evidence.add_argument("json_file")
    evidence.add_argument("-o", "--output", required=True)
    evidence.add_argument("--include-traces", action="store_true")

    db = sub.add_parser("db")
    db.add_argument("part", nargs="?", help="optional component part, such as 74HC00")
    db.add_argument("--audit", action="store_true", help="audit DB manifests against legacy catalog files")
    db.add_argument("--status", action="store_true", help="compare DB status categories with docs/CHIP_STATUS.md")
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
    circuits = CircuitCommandService()

    if args.command == "headless":
        return write_json(headless_capabilities(), output=getattr(args, "output", None))
    if args.command == "component-parse":
        data = parse_component_file(args.component_file)
        return write_json(data, output=args.output, status=0 if data["ok"] else 2)
    if args.command in {"component-resolve", "component-validate"}:
        data = resolve_component(parse_component_file(args.component_file))
        return write_json(data, output=args.output, status=0 if data["ok"] else 2)
    if args.command == "component-ide":
        data = component_ide_snapshot(args.component_file)
        return write_json(data, output=args.output, status=0 if data["ok"] else 2)
    if args.command == "component-run":
        resolved = resolve_component(parse_component_file(args.component_file))
        try:
            runtime = ComponentRuntimeSession(resolved)
            for operation in args.drive:
                if "=" not in operation: raise ComponentRuntimeError("--drive must be target=value")
                target, value = operation.split("=", 1); runtime.drive(target.strip(), value.strip())
            test = runtime.run_declared_test(args.test) if args.test else None
            data = {"ok": True, "runtime": runtime.snapshot(), "probe": runtime.probe(args.probe), "test": test}
            return write_json(data, output=args.output)
        except ComponentRuntimeError as exc:
            return write_json({"ok": False, "diagnostics": [{"code": "runtime.blocked", "message": str(exc)}]}, output=args.output, status=2)
    if args.command == "component-student":
        resolved = resolve_component(parse_component_file(args.component_file))
        data = {
            "format": "components.component-student@1", "ok": bool(resolved.get("ok")),
            "component": resolved.get("component_id"),
            "parts": [{"name": item["id"], "part": item["part"]} for item in resolved.get("instances", [])],
            "wires": len(resolved.get("edges", [])), "things_to_watch": [item["id"] for item in resolved.get("observations", [])],
            "try_tests": [item["id"] for item in resolved.get("tests", [])],
            "message": "A Component is a small machine. Read the parts, follow each named wire, then run one test.",
            "safety": "A passing simulation helps you learn logic. It does not prove breadboard wiring, voltage, or speed.",
            "diagnostics": resolved.get("diagnostics", []),
        }
        return write_json(data, output=args.output, status=0 if data["ok"] else 2)
    if args.command == "component-resource-inspect":
        data = inspect_resource(args.part)
        return write_json(data, output=args.output, status=0 if data["ok"] else 2)
    if args.command == "component-resource-bind":
        resolved = resolve_component(parse_component_file(args.component_file))
        data = bind_resource(resolved, target_id=args.target, part=args.resource, view=args.view, label=args.label)
        return write_json(data, output=args.output, status=0 if data["ok"] else 2)
    if args.command == "project-builder":
        return write_json(
            project_builder_workflow(part=getattr(args, "part", None), goal=getattr(args, "goal", None)),
            output=getattr(args, "output", None),
        )
    if args.command == "explain-result":
        return write_json(
            designs.explain_result(args.json_file, source_command=getattr(args, "source_command", None)),
            output=getattr(args, "output", None),
        )
    if args.command == "explain-violations":
        return write_json(
            circuits.explain_violations(_read_json(args.json_file)), output=getattr(args, "output", None),
            status=0,
        )
    if args.command == "export-evidence":
        data = circuits.export_evidence(_read_json(args.json_file), include_traces=args.include_traces)
        return write_json(data, output=args.output, status=0 if data["ok"] else 2)

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
    if args.command == "circuit-validate":
        data = circuits.validate(args.json_file)
        return write_json(data, status=0 if data["ok"] else 2)
    if args.command == "circuit-run":
        data = circuits.run(args.json_file, operations=args.op)
        return write_json(data, status=0 if data["ok"] else 2)
    if args.command == "circuit-step":
        data = circuits.step(args.op, args.json_file)
        return write_json(data, status=0 if data["ok"] else 2)
    if args.command == "circuit-probe":
        data = circuits.probe(args.name, args.json_file)
        return write_json(data, status=0 if data["ok"] else 2)
    if args.command == "timed-run":
        data = circuits.timed_run(args.json_file, operations=args.op)
        return write_json(data, status=0 if data["ok"] else 2)
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


def _read_json(path: str) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("runner result JSON must be an object")
    return value


def write_text(text: str, *, output: str | None = None, status: int = 0) -> int:
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
