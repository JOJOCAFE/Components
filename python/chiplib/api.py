"""Local JSON API adapter for Components services."""

from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import sys
from typing import Any

from .services import CONTRACT, CircuitCommandService, CircuitSessionRegistry, FrontendDesignService, headless_capabilities, project_builder_workflow
from .component_language import parse_component_text, resolve_component
from .component_runtime import ComponentRuntimeError, ComponentRuntimeSession
from .component_transport import board_view
from .component_edit import apply_component_edit, preview_component_edit


JsonMap = dict[str, Any]
ROOT = Path(__file__).resolve().parents[2]
BOARD_ROOT = ROOT / "board"
BOARD_RESOURCE_ROOT = BOARD_ROOT / "assets" / "74hc-functional-pinouts"
NOT_GATE_FIXTURE = ROOT / "Language" / "fixtures" / "component-v1.1" / "digital_inverter.component"


def handle_request(
    request: JsonMap,
    service: FrontendDesignService | None = None,
    circuit_service: CircuitCommandService | None = None,
    *,
    circuit_sessions: CircuitSessionRegistry | None = None,
    require_circuit_session: bool = False,
) -> JsonMap:
    """Handle one service request for stdio or HTTP adapters."""

    service = service or FrontendDesignService()
    circuit_service = circuit_service or getattr(service, "_circuit_service", None) or CircuitCommandService()
    service._circuit_service = circuit_service
    try:
        command = str(request.get("command", ""))
        input_data = request.get("input", {})
        options = request.get("options", {})
        if not isinstance(input_data, dict):
            input_data = {}
        if not isinstance(options, dict):
            options = {}
        schematic = input_data.get("schematic")
        if isinstance(schematic, dict):
            service.load(schematic)

        if command == "create-design":
            return service.create_design(
                str(options.get("name", input_data.get("name", "untitled"))),
                description=str(options.get("description", input_data.get("description", ""))),
            )
        if command in {
            "circuit-load", "circuit-validate", "circuit-run", "circuit-step", "circuit-probe", "timed-run"
        }:
            def dispatch(selected: CircuitCommandService) -> JsonMap:
                return _handle_circuit_command(command, input_data, options, selected)

            session_id = request.get("session_id", options.get("session_id", input_data.get("session_id")))
            if circuit_sessions is not None:
                if session_id is None:
                    return _error(command, "api.session_id_required", "HTTP circuit commands require session_id")
                session_text = str(session_id)
                try:
                    return circuit_sessions.execute(session_text, dispatch)
                except Exception as exc:
                    response = _error(command, "api.request_failed", str(exc), exception=exc.__class__.__name__)
                    response["session_id"] = session_text
                    return response
            if require_circuit_session:
                return _error(command, "api.session_id_required", "HTTP circuit commands require session_id")
            return dispatch(circuit_service)
        if command == "explain-violations":
            response = input_data.get("response", input_data.get("result", input_data))
            if not isinstance(response, dict):
                raise ValueError("input.response must be an object")
            return circuit_service.explain_violations(response)
        if command == "export-evidence":
            response = input_data.get("response", input_data.get("result", input_data))
            if not isinstance(response, dict):
                raise ValueError("input.response must be an object")
            return circuit_service.export_evidence(response, include_traces=bool(options.get("include_traces", input_data.get("include_traces", False))))
        if command in {"headless-capabilities", "ai-capabilities"}:
            return _ok(command, headless_capabilities())
        if command == "component-language-example":
            return _ok(command, {"id": "not-gate", "source": NOT_GATE_FIXTURE.read_text(encoding="utf-8")})
        if command == "component-language-edit":
            source = input_data.get("source")
            revision = input_data.get("source_revision", options.get("source_revision"))
            edit = input_data.get("edit", options.get("edit"))
            if not isinstance(source, str) or not isinstance(revision, str) or not isinstance(edit, dict):
                raise ValueError("component-language-edit needs source, source_revision, and edit")
            return _ok(command, apply_component_edit(source, expected_revision=revision, edit=edit, source_name=str(input_data.get("source_name", "<api>"))))
        if command == "component-language-edit-preview":
            source = input_data.get("source")
            revision = input_data.get("source_revision", options.get("source_revision"))
            edit = input_data.get("edit", options.get("edit"))
            if not isinstance(source, str) or not isinstance(revision, str) or not isinstance(edit, dict):
                raise ValueError("component-language-edit-preview needs source, source_revision, and edit")
            return _ok(command, preview_component_edit(source, expected_revision=revision, edit=edit, source_name=str(input_data.get("source_name", "<api>"))))
        if command in {"component-language-parse", "component-language-resolve", "component-language-board-view", "component-language-run", "component-language-student"}:
            source = input_data.get("source")
            if not isinstance(source, str):
                raise ValueError("input.source must be readable component:component text")
            ast = parse_component_text(source, source_name=str(input_data.get("source_name", "<api>")))
            resolved = resolve_component(ast)
            if command == "component-language-parse": return _ok(command, ast)
            if command == "component-language-resolve": return _ok(command, resolved)
            if command == "component-language-board-view": return _ok(command, board_view(resolved))
            if command == "component-language-student":
                return _ok(command, {"format": "components.component-student@1", "component": resolved.get("component_id"), "parts": [{"name": item["id"], "part": item["part"]} for item in resolved.get("instances", [])], "wires": len(resolved.get("edges", [])), "tests": [item["id"] for item in resolved.get("tests", [])], "diagnostics": resolved.get("diagnostics", [])})
            try:
                runtime = ComponentRuntimeSession(resolved)
                drives = options.get("drives", input_data.get("drives", []))
                if not isinstance(drives, list):
                    raise ValueError("drives must be a list of target/value objects")
                for drive in drives:
                    if not isinstance(drive, dict) or not isinstance(drive.get("target"), str) or "value" not in drive:
                        raise ValueError("each drive needs target and value")
                    runtime.drive(drive["target"], drive["value"])
                test = options.get("test")
                probe = options.get("probe", input_data.get("probe"))
                return _ok(command, {"runtime": runtime.snapshot(), "test": runtime.run_declared_test(str(test)) if test else None, "probes": runtime.probe(str(probe) if probe else None)})
            except ComponentRuntimeError as exc:
                return _error(command, "component.runtime_blocked", str(exc))
        if command in {"project-builder", "ai-project-builder"}:
            part = options.get("part", input_data.get("part"))
            goal = options.get("goal", input_data.get("goal"))
            return _ok(
                command,
                project_builder_workflow(
                    part=str(part) if part is not None else None,
                    goal=str(goal) if goal is not None else None,
                ),
            )
        if command == "explain-result":
            response = input_data.get("response", input_data.get("result", input_data))
            if not isinstance(response, dict):
                raise ValueError("input.response must be an object")
            source_command = options.get("source_command", options.get("sourceCommand"))
            return service.explain_result(
                response,
                source_command=str(source_command) if source_command is not None else None,
            )
        if command == "load":
            return service.load(_required_map(input_data, "schematic"))
        if command == "create-chip":
            properties = dict(options.get("properties", {})) if isinstance(options.get("properties"), dict) else {}
            return service.create_chip(str(options.get("ref", input_data.get("ref"))), str(options.get("part", input_data.get("part"))), **properties)
        if command == "delete-chip":
            return service.delete_chip(str(options.get("ref", input_data.get("ref"))))
        if command == "connect":
            return service.connect(str(options.get("rule", input_data.get("rule"))))
        if command == "disconnect":
            return service.disconnect(str(options.get("rule", input_data.get("rule"))))
        if command == "add-bus":
            return service.add_bus(str(options.get("name", input_data.get("name"))), int(options.get("width", input_data.get("width", 1))))
        if command == "set-inputs":
            return service.set_inputs(str(options.get("name", input_data.get("name"))), options.get("rules", input_data.get("rules", [])))
        if command == "step":
            return service.step(str(options.get("step", input_data.get("step"))))
        if command == "validate":
            return service.validate()
        if command == "snapshot":
            return service.snapshot()
        if command == "frontend-snapshot":
            return service.frontend_snapshot()
        if command == "export-block-ui":
            return service.export_block_ui()
        if command == "import-block-ui":
            block_ui = input_data.get("block_ui", input_data)
            if not isinstance(block_ui, dict):
                raise ValueError("input.block_ui must be an object")
            return service.import_block_ui(block_ui)
        if command == "component-catalog":
            group = options.get("group", input_data.get("group"))
            return service.component_catalog(group=str(group) if group is not None else None)
        if command == "student-component-catalog":
            group = options.get("group", input_data.get("group"))
            return service.student_component_catalog(group=str(group) if group is not None else None)
        if command == "component-detail":
            return service.component_detail(str(options.get("part", input_data.get("part"))))
        if command == "component-metadata":
            return service.component_metadata(str(options.get("part", input_data.get("part"))))
        if command == "component-digital":
            return service.component_digital(str(options.get("part", input_data.get("part"))))
        if command == "component-package":
            return service.component_package(str(options.get("part", input_data.get("part"))))
        if command == "component-generate":
            return service.component_generate(str(options.get("part", input_data.get("part"))))
        if command == "run":
            return service.run(options.get("steps", input_data.get("steps", "all")))
        if command == "probe":
            set_name = options.get("set", input_data.get("set"))
            return service.read_probes(str(set_name) if set_name is not None else None)
        if command == "export-json":
            return service.export_json()
        if command == "export-netlist":
            return service.export_netlist()
        if command == "export-verilog":
            return service.export_verilog()
        return _error(command or "unknown", "api.unknown_command", f"unknown command {command!r}")
    except Exception as exc:  # pragma: no cover - defensive adapter boundary
        return _error(str(request.get("command", "unknown")), "api.request_failed", str(exc), exception=exc.__class__.__name__)


def run_stdio(service: FrontendDesignService | None = None) -> int:
    service = service or FrontendDesignService()
    for line in sys.stdin:
        if not line.strip():
            continue
        response = handle_request(json.loads(line), service)
        sys.stdout.write(json.dumps(response, sort_keys=True) + "\n")
        sys.stdout.flush()
    return 0


def run_http(host: str = "127.0.0.1", port: int = 8765, service: FrontendDesignService | None = None) -> int:
    service = service or FrontendDesignService()
    circuit_sessions = CircuitSessionRegistry()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - stdlib API name
            relative = self.path.split("?", 1)[0].lstrip("/") or "index.html"
            candidate = board_static_file(relative)
            if candidate is None:
                self.send_error(404)
                return
            if not candidate.is_file():
                self.send_error(404)
                return
            body = candidate.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mimetypes.guess_type(str(candidate))[0] or "application/octet-stream")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:  # noqa: N802 - stdlib API name
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length)
            try:
                request = json.loads(raw.decode("utf-8"))
                response = handle_request(
                    request, service, circuit_sessions=circuit_sessions, require_circuit_session=True
                )
                status = 200 if response.get("ok", False) else 400
            except Exception as exc:  # pragma: no cover - defensive HTTP boundary
                response = _error("http", "api.bad_request", str(exc), exception=exc.__class__.__name__)
                status = 400
            body = json.dumps(response, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - stdlib API name
            return

    server = ThreadingHTTPServer((host, port), Handler)
    try:
        server.serve_forever()
    finally:
        server.server_close()
    return 0


def board_static_file(relative: str) -> Path | None:
    """Resolve one Board-owned static file without allowing path escape."""
    prefix = "resources/74hc-functional-pinouts/"
    root, child = (BOARD_RESOURCE_ROOT, relative[len(prefix):]) if relative.startswith(prefix) else (BOARD_ROOT, relative)
    candidate = (root / child).resolve()
    if candidate != root.resolve() and root.resolve() not in candidate.parents:
        return None
    return candidate if candidate.is_file() else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m chiplib.api")
    parser.add_argument("--stdio", action="store_true", help="read newline-delimited JSON requests from stdin")
    parser.add_argument("--http", action="store_true", help="serve local HTTP POST requests")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)

    if args.http:
        return run_http(args.host, args.port)
    return run_stdio()


def _required_map(data: JsonMap, key: str) -> JsonMap:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"input.{key} must be an object")
    return value


def _handle_circuit_command(
    command: str, input_data: JsonMap, options: JsonMap, service: CircuitCommandService
) -> JsonMap:
    path = options.get("path", input_data.get("path"))
    path_text = str(path) if path is not None else None
    if command == "circuit-load":
        return service.load(path_text or "")
    if command == "circuit-validate":
        return service.validate(path_text)
    if command == "circuit-run":
        operations = options.get("operations", input_data.get("operations", []))
        if not isinstance(operations, list):
            raise ValueError("input.operations must be an array")
        return service.run(path_text, operations=[str(item) for item in operations])
    if command == "timed-run":
        operations = options.get("operations", input_data.get("operations", []))
        if not isinstance(operations, list):
            raise ValueError("input.operations must be an array")
        return service.timed_run(path_text, operations=[str(item) for item in operations])
    if command == "circuit-step":
        operation = options.get("operation", input_data.get("operation"))
        if operation is None:
            raise ValueError("input.operation is required")
        return service.step(str(operation), path_text)
    name = options.get("name", input_data.get("name"))
    return service.probe(str(name) if name is not None else None, path_text)


def _ok(command: str, result: JsonMap) -> JsonMap:
    return {
        "contract": CONTRACT,
        "command": command,
        "ok": True,
        "result": result,
        "warnings": [],
        "metadata": {"engine": "python", "components_version": None, "elapsed_ms": 0},
    }


def _error(command: str, code: str, message: str, *, exception: str | None = None) -> JsonMap:
    details: JsonMap = {}
    if exception is not None:
        details["exception"] = exception
    return {
        "contract": CONTRACT,
        "command": command,
        "ok": False,
        "warnings": [],
        "error": {"code": code, "message": message, "severity": "error", "details": details},
        "metadata": {"engine": "python", "components_version": None, "elapsed_ms": 0},
    }


if __name__ == "__main__":
    raise SystemExit(main())
