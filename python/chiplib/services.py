"""Internal service interfaces over the Components design backend."""

from __future__ import annotations

import json
from pathlib import Path
import re
from threading import RLock
from time import perf_counter
from typing import Any, Callable

from .db import component_catalog, component_detail, generate_component_artifacts, load_component_package, load_digital_definition, load_digital_package, student_component_catalog
from .netlist import _verilog_mapping, design_to_verilog


JsonMap = dict[str, Any]
CONTRACT = "components.service.v1"
CIRCUIT_STUDENT_CONTRACT = "components.circuit_runner.student.v1"


class CircuitCommandService:
    """Stateful service adapter for executable circuit-library packages."""

    contract = CONTRACT

    def __init__(self) -> None:
        self.runner: Any | None = None

    def load(self, path: str | Path) -> JsonMap:
        from .circuit_runner import load_circuit_runner

        try:
            self.runner = load_circuit_runner(path)
            return self._response("circuit-load", self.runner.snapshot())
        except Exception as exc:
            return self._failure("circuit-load", exc)

    def validate(self, path: str | Path | None = None) -> JsonMap:
        loaded = self._load_if_requested(path, "circuit-validate")
        if loaded is not None:
            return loaded
        runner = self._require_runner()
        snapshot = runner.snapshot()
        result = self._student_result(
            "validate",
            runner,
            summary=f"{len(runner.board.chips)} chips, {len(runner.board.nets)} nets, 0 errors, 0 warnings.",
            details={"snapshot": snapshot},
        )
        return self._response("circuit-validate", result)

    def run(self, path: str | Path | None = None, *, operations: list[str] | None = None) -> JsonMap:
        loaded = self._load_if_requested(path, "circuit-run")
        if loaded is not None:
            return loaded
        runner = self._require_runner()
        executed: list[JsonMap] = []
        try:
            for operation in operations or []:
                executed.append(self._apply_operation(runner, operation))
            result = self._student_result(
                "run", runner, summary=f"Functional run completed with {len(executed)} operation(s).",
                details={"executed_steps": executed, "snapshot": runner.snapshot()},
            )
            return self._response("circuit-run", result)
        except Exception as exc:
            return self._failure("circuit-run", exc, student_command="run")

    def step(self, operation: str, path: str | Path | None = None) -> JsonMap:
        loaded = self._load_if_requested(path, "circuit-step")
        if loaded is not None:
            return loaded
        runner = self._require_runner()
        before = runner.snapshot()
        try:
            executed = self._apply_operation(runner, operation)
            result = self._student_result(
                "step", runner, summary=f"Completed one operation: {operation}",
                details={"operation": operation, "action": executed["action"], "before": before, "snapshot": runner.snapshot()},
            )
            return self._response("circuit-step", result)
        except Exception as exc:
            return self._failure("circuit-step", exc, student_command="step")

    def probe(self, name: str | None = None, path: str | Path | None = None) -> JsonMap:
        loaded = self._load_if_requested(path, "circuit-probe")
        if loaded is not None:
            return loaded
        runner = self._require_runner()
        try:
            values = {name: runner.read(name)} if name else runner.read()
            samples = [{"name": key, "target": key, "value": value, "time_ns": 0} for key, value in values.items()]
            result = self._student_result(
                "probe", runner, summary=f"Read {len(samples)} probe(s).",
                details={"samples": samples, "snapshot": runner.snapshot()},
            )
            return self._response("circuit-probe", result)
        except Exception as exc:
            return self._failure("circuit-probe", exc, student_command="probe")

    def _load_if_requested(self, path: str | Path | None, command: str) -> JsonMap | None:
        if path is None:
            return None
        loaded = self.load(path)
        if not loaded["ok"]:
            loaded["command"] = command
            if isinstance(loaded.get("result"), dict):
                loaded["result"]["command"] = command.removeprefix("circuit-")
            return loaded
        return None

    def _require_runner(self) -> Any:
        if self.runner is None:
            raise ValueError("no circuit loaded; call circuit-load or provide input.path")
        return self.runner

    def _apply_operation(self, runner: Any, operation: str) -> JsonMap:
        words = str(operation).strip().split()
        if len(words) == 3 and words[0] == "set":
            value = runner.set_input(words[1], words[2])
            return {"operation": operation, "action": "set", "port": words[1], "value": value}
        if len(words) in {1, 2} and words[0] == "clock":
            name = words[1] if len(words) == 2 else "CLK"
            return {"operation": operation, "action": "clock", "port": name, "outputs": runner.pulse_clock(name)}
        if words == ["reset"]:
            return {"operation": operation, "action": "reset", "outputs": runner.reset()}
        if words == ["settle"]:
            runner.board.settle()
            return {"operation": operation, "action": "settle"}
        from .circuit_runner import CircuitRunnerError, CircuitRunnerIssue
        raise CircuitRunnerError([CircuitRunnerIssue(
            "runner.unsupported_step", "operation",
            f"unsupported operation {operation!r}; use 'set PORT VALUE', 'clock [PORT]', 'reset', or 'settle'",
        )], runner.package.source_path)

    def _student_result(self, command: str, runner: Any, *, summary: str, details: JsonMap) -> JsonMap:
        return {
            "contract": CIRCUIT_STUDENT_CONTRACT,
            "command": command,
            "ok": True,
            "status": "pass",
            "design": {"id": runner.package.id, "source": str(runner.package.source_path)},
            "summary": summary,
            "violations": [],
            "warnings": [],
            **details,
            "evidence_boundary": {
                "proves": ["the listed functional checks passed in the Python simulator"],
                "does_not_prove": ["physical wiring", "electrical safety", "physical timing"],
            },
            "metadata": {"engine": "python", "engine_version": None, "components_version": None, "elapsed_ms": 0},
        }

    def _response(self, command: str, result: JsonMap) -> JsonMap:
        return {"contract": CONTRACT, "command": command, "ok": True, "result": result, "warnings": [], "metadata": {"engine": "python", "components_version": None, "elapsed_ms": 0}}

    def _failure(self, command: str, exc: Exception, *, student_command: str | None = None) -> JsonMap:
        issues = [issue.to_dict() for issue in getattr(exc, "issues", ())]
        code = issues[0]["code"] if issues else "runner.request_failed"
        status = "blocked" if code in {"unsupported_part", "composite_not_executable", "virtual_part_not_executable", "symbolic_aggregate_not_executable", "range_not_executable"} else "error"
        violation = {"code": code, "message": str(exc), "location": {"source_path": issues[0].get("path") if issues else None}, "details": {"issues": issues, "exception": exc.__class__.__name__}}
        result = {"contract": CIRCUIT_STUDENT_CONTRACT, "command": student_command or command.removeprefix("circuit-"), "ok": False, "status": status, "summary": str(exc), "violations": [violation], "warnings": [], "evidence_boundary": {"proves": [], "does_not_prove": ["physical wiring", "electrical safety", "physical timing"]}, "metadata": {"engine": "python", "engine_version": None, "components_version": None, "elapsed_ms": 0}}
        return {"contract": CONTRACT, "command": command, "ok": False, "result": result, "warnings": [], "error": {"code": code, "message": str(exc), "severity": "error", "details": violation["details"]}, "metadata": {"engine": "python", "components_version": None, "elapsed_ms": 0}}


class CircuitSessionRegistry:
    """Thread-safe circuit services isolated by caller-provided session ID."""

    _SESSION_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")

    def __init__(self) -> None:
        self._sessions: dict[str, tuple[CircuitCommandService, RLock]] = {}
        self._lock = RLock()

    def execute(self, session_id: str, operation: Callable[[CircuitCommandService], JsonMap]) -> JsonMap:
        if not self._SESSION_ID.fullmatch(session_id):
            raise ValueError("session_id must be 1-64 letters, digits, '.', '_', or '-' and start with a letter or digit")
        with self._lock:
            service, session_lock = self._sessions.setdefault(
                session_id, (CircuitCommandService(), RLock())
            )
        with session_lock:
            response = operation(service)
            response["session_id"] = session_id
            return response


def headless_capabilities() -> JsonMap:
    """Return the machine-readable CLI/API/AI contract summary."""

    return {
        "format": "components.headless.capabilities",
        "version": 1,
        "contract": CONTRACT,
        "purpose": "Headless Components access for CLI tools, local APIs, and AI assistants helping students build digital logic projects.",
        "primary_users": {
            "student_age_range": "10-15",
            "also_useful_for": "older learners and project builders up to about 24",
            "teacher_or_adult_required_for": [
                "real breadboard power-up",
                "ordering parts",
                "raising clock speed",
                "debugging hot chips or unexpected current",
            ],
        },
        "entrypoints": {
            "cli": "PYTHONPATH=python python3 -B -m chiplib.cli",
            "api_stdio": "PYTHONPATH=python python3 -B -m chiplib.api --stdio",
            "api_http": "PYTHONPATH=python python3 -B -m chiplib.api --http --host 127.0.0.1 --port 8765",
        },
        "transports": [
            {
                "name": "cli",
                "state": "stateless per command",
                "output": "JSON on stdout unless --text is explicitly requested",
            },
            {
                "name": "stdio-api",
                "state": "stateful for one newline-delimited JSON session",
                "output": "one JSON response per input line",
            },
            {
                "name": "http-api",
                "state": "stateful per explicit session_id while the local server process is running",
                "output": "JSON POST response",
            },
        ],
        "ai_workflow": [
            "Discover parts with student-component-catalog before choosing chips.",
            "Inspect selected parts with component-detail or component-package before wiring.",
            "Create or load schematic JSON using real chip refs, real DIP pin numbers, rails, buses, inputs, and probes.",
            "Run validate before run.",
            "Run run and probe before suggesting real wiring changes.",
            "Run circuit-faults for circuit-package JSON that may touch real breadboard wiring.",
            "Export netlist or Verilog only after simulation passes, and report unsupported parts instead of guessing.",
        ],
        "student_guardrails": [
            "Do not invent pinouts, active-low markers, chip behavior, timing, or procurement facts.",
            "Do not hide validation errors, bus conflicts, unsupported exports, missing timing evidence, or missing datasheet evidence.",
            "Explain failures with the chip ref, part, pin, net, command, and suggested fix when available.",
            "Treat virtual simulation as a learning and wiring check, not physical hardware signoff.",
            "Tell students to stop a real build when a chip is hot, current is unexpected, or two outputs may fight.",
        ],
        "core_commands": {
            "catalog": ["component-catalog", "student-component-catalog", "component-detail", "component-package"],
            "design": ["create-design", "load", "create-chip", "delete-chip", "connect", "disconnect", "add-bus", "set-inputs"],
            "simulation": ["validate", "snapshot", "frontend-snapshot", "run", "step", "probe", "explain-result"],
            "circuit_simulation": ["circuit-load", "circuit-validate", "circuit-run", "circuit-step", "circuit-probe"],
            "export": ["export-json", "export-netlist", "export-verilog", "export-block-ui", "import-block-ui"],
            "verification": ["circuit-faults", "db --audit", "db --status"],
        },
        "important_docs": [
            "Docs/STUDENT_GUIDE.md",
            "Docs/SERVICE_CONTRACT.md",
            "Docs/SCHEMATIC_JSON_SPEC.md",
            "Docs/DB_COMPONENT_PACKAGE_SPEC.md",
            "Docs/TIMING_PARAMETER_AUDIT.md",
            "Docs/TIMING_SIMULATION_AUDIT.md",
        ],
        "limits": [
            "Headless simulation currently uses generic chip-level timing for most models.",
            "Hardware frequency claims require physical timing and signal-integrity evidence outside this service.",
            "Verilog export is explicit and conservative; unsupported parts are reported.",
        ],
    }


def project_builder_workflow(*, part: str | None = None, goal: str | None = None) -> JsonMap:
    """Return an AI-friendly workflow for helping a student build a project."""

    selected_part: JsonMap | None = None
    if part:
        selected_part = component_detail(part)
    starter_schematic = {
        "name": "student-nand",
        "description": "Starter 74HC00 NAND gate check before breadboard wiring.",
        "chips": {"U1": {"part": "74HC00"}},
        "aliases": {"A": "U1:1", "B": "U1:2", "Y": "U1:3"},
        "connect": [
            "VCC -> U1:14",
            "GND -> U1:7",
        ],
        "inputs": {
            "both_high": ["A = 1", "B = 1"],
            "a_low": ["A = 0", "B = 1"],
        },
        "probes": {"logic": ["A", "B", "Y"]},
        "expect": {
            "nand_both_high": ["Y = 0"],
            "nand_changed": ["Y has rising"],
        },
        "steps": [
            "apply both_high",
            "settle",
            "probe",
            "expect nand_both_high",
            "apply a_low",
            "settle",
            "probe",
            "expect nand_changed",
        ],
    }
    return {
        "format": "components.ai.project_builder_workflow",
        "version": 1,
        "contract": CONTRACT,
        "goal": goal or "Help a student choose parts, build schematic JSON, simulate, probe, and explain the result before real wiring.",
        "selected_part": selected_part,
        "workflow": [
            {
                "step": "discover",
                "why": "Choose chips from the Components DB instead of inventing parts.",
                "cli": "PYTHONPATH=python python3 -B -m chiplib.cli db --student --group 74xx",
                "api": {"command": "student-component-catalog", "options": {"group": "74xx"}},
            },
            {
                "step": "inspect",
                "why": "Check real DIP pins, active-low pins, evidence, timing notes, and procurement hints.",
                "cli": "PYTHONPATH=python python3 -B -m chiplib.cli db 74HC00 --detail",
                "api": {"command": "component-detail", "options": {"part": part or "74HC00"}},
            },
            {
                "step": "draft",
                "why": "Create schematic JSON with real refs, rails, buses, inputs, and probes.",
                "artifact": "starter_schematic",
            },
            {
                "step": "validate",
                "why": "Catch missing chips, bad pins, invalid wiring rules, and schema mistakes before simulation.",
                "cli": "PYTHONPATH=python python3 -B -m chiplib.cli validate /tmp/student-nand.json",
                "api": {"command": "validate", "input": {"schematic": starter_schematic}},
            },
            {
                "step": "simulate",
                "why": "Run the virtual circuit and collect board errors and expectation results.",
                "cli": "PYTHONPATH=python python3 -B -m chiplib.cli run /tmp/student-nand.json",
                "api": {"command": "run", "input": {"schematic": starter_schematic}},
            },
            {
                "step": "probe",
                "why": "Read named signals so the student can compare expected and actual behavior.",
                "cli": "PYTHONPATH=python python3 -B -m chiplib.cli probe /tmp/student-nand.json",
                "api": {"command": "probe", "input": {"schematic": starter_schematic}},
            },
            {
                "step": "safety-check",
                "why": "For circuit packages, check common AI wiring mistakes before real breadboard work.",
                "cli": "PYTHONPATH=python python3 -B -m chiplib.cli circuit-faults Lib/Circuits/RV8GR_WholeSystemChipLevelVirtual/circuit.json",
                "api": None,
            },
        ],
        "starter_schematic": starter_schematic,
        "explain_result_rules": [
            "Start with whether ok is true or false.",
            "Name the command that produced each issue.",
            "For wiring issues, include chip ref, part, pin, and net when available.",
            "For bus conflicts, tell the student which outputs may be fighting and to stop before real wiring.",
            "For unsupported exports, say the simulator can still be used and do not guess a Verilog mapping.",
            "For timing, say whether the result is generic simulation timing or source-backed datasheet timing.",
        ],
        "stop_before_hardware_when": [
            "validation fails",
            "simulation board errors are present",
            "two outputs can drive the same net without a bus-owner rule",
            "pinout evidence or active-low meaning is missing",
            "chip gets hot or supply current is unexpected",
        ],
    }


def explain_result(response: JsonMap, *, source_command: str | None = None) -> JsonMap:
    """Summarize an existing service/CLI response without adding domain facts."""

    command = source_command or _response_command(response)
    ok = _response_ok(response)
    issues = _collect_explain_issues(response)
    warning_count = len([item for item in issues if item.get("severity") == "warning"])
    return {
        "format": "components.explain_result",
        "version": 1,
        "contract": CONTRACT,
        "source_command": command,
        "ok": ok,
        "status": "ok" if ok and not issues else "needs_attention",
        "summary": {
            "command": command,
            "ok": ok,
            "issue_count": len([item for item in issues if item.get("severity") != "warning"]),
            "warning_count": warning_count,
            "top_fields": _top_level_fields(response),
        },
        "issues": issues,
        "likely_next_steps": _explain_next_steps(command, issues),
        "stop_before_hardware_warnings": _stop_before_hardware_warnings(command, ok, issues),
        "references": {
            "command_field": "$.command" if "command" in response else None,
            "ok_field": "$.ok" if "ok" in response else "$.valid" if "valid" in response else None,
            "issue_fields": sorted({str(issue["source_path"]) for issue in issues if issue.get("source_path")}),
        },
    }


class SimulationService:
    """Stable internal boundary for simulation-backed Design operations."""

    contract = CONTRACT
    engine = "python"

    def validate(self, design: Any) -> JsonMap:
        started = perf_counter()
        try:
            validation = design.validate()
            warnings = _as_list(validation.get("warnings"))
            errors = _as_list(validation.get("errors"))
            result = {
                "valid": bool(validation.get("ok")),
                "design_id": getattr(design, "name", None),
                "summary": self._summary(design),
                "errors": errors,
                "warnings": warnings,
                "validation": validation,
            }
            return self._response(
                "validate",
                bool(validation.get("ok")),
                result,
                warnings=warnings,
                errors=errors,
                started=started,
            )
        except Exception as exc:  # pragma: no cover - defensive service boundary
            return self._exception("validate", exc, started=started)

    def snapshot(self, design: Any) -> JsonMap:
        started = perf_counter()
        try:
            if getattr(design, "_board", None) is None:
                design.to_board()
            payload = design.snapshot()
            validation = payload.get("validate", {}) if isinstance(payload, dict) else {}
            warnings = _as_list(validation.get("warnings")) if isinstance(validation, dict) else []
            errors = _as_list(validation.get("errors")) if isinstance(validation, dict) else []
            return self._response(
                "snapshot",
                not errors,
                payload,
                warnings=warnings,
                errors=errors,
                started=started,
            )
        except Exception as exc:  # pragma: no cover - defensive service boundary
            return self._exception("snapshot", exc, started=started)

    def run(self, design: Any, steps: str | list[str] = "all") -> JsonMap:
        started = perf_counter()
        try:
            payload = design.run(steps)
            warnings = _warnings_from_run(payload)
            errors = _board_errors(payload) + _expectation_errors(payload)
            return self._response(
                "run",
                bool(payload.get("ok")) and not errors,
                payload,
                warnings=warnings,
                errors=errors,
                started=started,
            )
        except Exception as exc:  # pragma: no cover - defensive service boundary
            return self._exception("run", exc, code="simulation.failed", started=started)

    def probe(
        self,
        design: Any,
        *,
        set_name: str | None = None,
        steps: str | list[str] | None = None,
        include_history: bool = True,
    ) -> JsonMap:
        started = perf_counter()
        try:
            if steps is not None:
                run_payload = design.run(steps)
                if not run_payload.get("ok", False):
                    return self._response(
                        "probe",
                        False,
                        {"run": run_payload},
                        warnings=_warnings_from_run(run_payload),
                        errors=_board_errors(run_payload),
                        started=started,
                    )
            if getattr(design, "probe_controller", None) is None:
                design.to_board()
            probes = design.probe_controller
            if probes is None:
                raise RuntimeError("design probes are not available")
            probes.sample()
            snapshot = probes.snapshot()
            sets = snapshot.get("sets", [])
            selected_name = set_name or "default"
            selected = next((item for item in sets if item.get("name") == selected_name), None)
            if selected is None:
                return self._response(
                    "probe",
                    False,
                    {"set": selected_name, "available_sets": [item.get("name") for item in sets]},
                    errors=[{"type": "probe_set_missing", "set": selected_name}],
                    started=started,
                )
            samples = []
            for channel in selected.get("channels", []):
                sample = {
                    "name": channel.get("name"),
                    "target": channel.get("target"),
                    "target_kind": channel.get("target_kind"),
                    "value": channel.get("value"),
                }
                if include_history:
                    sample["history"] = channel.get("history", [])
                samples.append(sample)
            result = {
                "set": selected.get("name"),
                "time_ns": selected.get("time_ns", snapshot.get("time_ns", 0)),
                "samples": samples,
                "probes": snapshot,
            }
            return self._response("probe", True, result, started=started)
        except Exception as exc:  # pragma: no cover - defensive service boundary
            return self._exception("probe", exc, code="simulation.failed", started=started)

    def frontend_snapshot(self, design: Any) -> JsonMap:
        started = perf_counter()
        try:
            if getattr(design, "_board", None) is None:
                design.to_board()
            return self._response("frontend-snapshot", True, _frontend_snapshot(design.snapshot()), started=started)
        except Exception as exc:  # pragma: no cover - defensive service boundary
            return self._exception("frontend-snapshot", exc, started=started)

    def _summary(self, design: Any) -> JsonMap:
        probes = getattr(design, "probes", {})
        return {
            "chips": len(getattr(design, "chips", {})),
            "buses": len(getattr(design, "buses", {})),
            "connections": len(getattr(design, "connections", [])),
            "probes": sum(len(_probe_channels(items)) for items in probes.values()) if isinstance(probes, dict) else 0,
        }

    def _response(
        self,
        command: str,
        ok: bool,
        result: JsonMap,
        *,
        warnings: list[Any] | None = None,
        errors: list[Any] | None = None,
        started: float,
    ) -> JsonMap:
        response: JsonMap = {
            "contract": self.contract,
            "command": command,
            "ok": ok,
            "result": result,
            "warnings": warnings or [],
            "metadata": self._metadata(started),
        }
        if errors:
            response["errors"] = errors
            response["error"] = {
                "code": "validation.failed" if command == "validate" else "simulation.failed",
                "message": f"{command} failed.",
                "severity": "error",
                "details": {"errors": errors},
            }
        return response

    def _exception(self, command: str, exc: Exception, *, started: float, code: str = "internal.error") -> JsonMap:
        return {
            "contract": self.contract,
            "command": command,
            "ok": False,
            "error": {
                "code": code,
                "message": str(exc),
                "severity": "error",
                "details": {"exception": exc.__class__.__name__},
            },
            "warnings": [],
            "metadata": self._metadata(started),
        }

    def _metadata(self, started: float) -> JsonMap:
        return {
            "engine": self.engine,
            "components_version": None,
            "elapsed_ms": round((perf_counter() - started) * 1000, 3),
        }


class DesignCommandService:
    """CLI-compatible service facade over design simulation and exporters."""

    def __init__(
        self,
        *,
        simulation: SimulationService | None = None,
        verilog: "VerilogExportService | None" = None,
    ):
        self.simulation = simulation or SimulationService()
        self.verilog = verilog or VerilogExportService()

    def load_design(self, json_file: str) -> Any:
        from .design import Design

        return Design.load_json(json_file)

    def validate(self, json_file: str) -> JsonMap:
        response = self.simulation.validate(self.load_design(json_file))
        result = response.get("result", {})
        if isinstance(result, dict) and isinstance(result.get("validation"), dict):
            return result["validation"]
        return response

    def snapshot(self, json_file: str) -> JsonMap:
        return self.simulation.snapshot(self.load_design(json_file))["result"]

    def run(self, json_file: str, *, steps: str | list[str] = "all") -> JsonMap:
        return self.simulation.run(self.load_design(json_file), steps=steps)["result"]

    def probe(self, json_file: str) -> JsonMap:
        response = self.simulation.probe(self.load_design(json_file))
        result = response.get("result", {})
        if isinstance(result, dict) and isinstance(result.get("probes"), dict):
            return result["probes"]
        return response

    def export_json(self, json_file: str) -> JsonMap:
        return self.load_design(json_file).to_dict()

    def export_block_ui(self, json_file: str) -> JsonMap:
        return self.load_design(json_file).to_block_ui()

    def import_block_ui(self, json_file: str) -> JsonMap:
        from .design import Design

        data = json.loads(Path(json_file).read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("block UI JSON root must be an object")
        return Design.from_block_ui(data).to_dict()

    def export_netlist(self, json_file: str) -> JsonMap:
        return self.load_design(json_file).to_netlist()

    def export_verilog(self, json_file: str) -> JsonMap:
        return self.verilog.export(self.load_design(json_file))

    def explain_result(self, json_file: str, *, source_command: str | None = None) -> JsonMap:
        data = json.loads(Path(json_file).read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("explain-result JSON root must be an object")
        return explain_result(data, source_command=source_command)


class FrontendDesignService:
    """Stateful design editing service for frontend/API adapters."""

    contract = CONTRACT

    def __init__(
        self,
        design: Any | None = None,
        *,
        simulation: SimulationService | None = None,
        verilog: "VerilogExportService | None" = None,
    ):
        self.design = design
        self.simulation = simulation or SimulationService()
        self.verilog = verilog or VerilogExportService()

    def create_design(self, name: str = "untitled", *, description: str = "") -> JsonMap:
        from .design import Design

        self.design = Design(str(name))
        self.design.description = str(description)
        return self.snapshot()

    def load(self, data: JsonMap) -> JsonMap:
        from .design import Design

        self.design = Design.from_dict(data)
        return self.snapshot()

    def export_json(self) -> JsonMap:
        design = self._require_design()
        return self._ok("export-json", design.to_dict())

    def export_block_ui(self) -> JsonMap:
        design = self._require_design()
        return self._ok("export-block-ui", design.to_block_ui())

    def import_block_ui(self, data: JsonMap) -> JsonMap:
        from .design import Design

        self.design = Design.from_block_ui(data)
        return self.snapshot()

    def create_chip(self, ref: str, part: str, **properties: Any) -> JsonMap:
        design = self._require_design()
        design.chips[str(ref)] = {"part": str(part), **properties}
        self._clear_runtime()
        return self.frontend_snapshot()

    def delete_chip(self, ref: str) -> JsonMap:
        design = self._require_design()
        ref = str(ref)
        design.chips.pop(ref, None)
        design.connections = [rule for rule in design.connections if not _rule_mentions_ref(rule, ref)]
        self._clear_runtime()
        return self.frontend_snapshot()

    def connect(self, rule: str) -> JsonMap:
        design = self._require_design()
        design.connections.append(str(rule))
        self._clear_runtime()
        return self.frontend_snapshot()

    def disconnect(self, rule: str) -> JsonMap:
        design = self._require_design()
        try:
            design.connections.remove(str(rule))
        except ValueError:
            return self._fail("disconnect", [{"type": "connection_missing", "rule": str(rule)}])
        self._clear_runtime()
        return self.frontend_snapshot()

    def add_bus(self, name: str, width: int = 1, **properties: Any) -> JsonMap:
        design = self._require_design()
        design.buses[str(name)] = {"width": int(width), **properties}
        self._clear_runtime()
        return self.frontend_snapshot()

    def set_inputs(self, name: str, rules: list[str] | dict[str, Any]) -> JsonMap:
        design = self._require_design()
        if isinstance(rules, dict):
            design.inputs[str(name)] = [f"{ref} = {value}" for ref, value in rules.items()]
        else:
            design.inputs[str(name)] = [str(rule) for rule in rules]
        self._clear_runtime()
        return self.frontend_snapshot()

    def step(self, step: str) -> JsonMap:
        design = self._require_design()
        return self.simulation.run(design, steps=[str(step)])

    def run(self, steps: str | list[str] = "all") -> JsonMap:
        return self.simulation.run(self._require_design(), steps=steps)

    def read_probes(self, set_name: str | None = None) -> JsonMap:
        return self.simulation.probe(self._require_design(), set_name=set_name)

    def validate(self) -> JsonMap:
        return self.simulation.validate(self._require_design())

    def snapshot(self) -> JsonMap:
        return self.simulation.snapshot(self._require_design())

    def frontend_snapshot(self) -> JsonMap:
        return self.simulation.frontend_snapshot(self._require_design())

    def export_netlist(self) -> JsonMap:
        return self._ok("export-netlist", self._require_design().to_netlist())

    def export_verilog(self) -> JsonMap:
        return self._ok("export-verilog", self.verilog.export(self._require_design()))

    def component_catalog(self, *, group: str | None = None) -> JsonMap:
        return self._ok("component-catalog", component_catalog(group=group))

    def student_component_catalog(self, *, group: str | None = None) -> JsonMap:
        return self._ok("student-component-catalog", student_component_catalog(group=group))

    def component_detail(self, part: str) -> JsonMap:
        return self._ok("component-detail", component_detail(part))

    def component_metadata(self, part: str) -> JsonMap:
        return self._ok("component-metadata", component_detail(part))

    def component_digital(self, part: str) -> JsonMap:
        return self._ok("component-digital", load_digital_definition(part))

    def component_package(self, part: str) -> JsonMap:
        return self._ok("component-package", load_component_package(part))

    def component_generate(self, part: str) -> JsonMap:
        return self._ok("component-generate", generate_component_artifacts(part))

    def explain_result(self, response: JsonMap, *, source_command: str | None = None) -> JsonMap:
        return self._ok("explain-result", explain_result(response, source_command=source_command))

    def _require_design(self) -> Any:
        if self.design is None:
            raise ValueError("no design loaded")
        return self.design

    def _clear_runtime(self) -> None:
        if self.design is None:
            return
        self.design._board = None
        self.design.stimulus = None
        self.design.probe_controller = None

    def _ok(self, command: str, result: JsonMap) -> JsonMap:
        return {
            "contract": self.contract,
            "command": command,
            "ok": True,
            "result": result,
            "warnings": [],
            "metadata": {"engine": "python", "components_version": None, "elapsed_ms": 0},
        }

    def _fail(self, command: str, errors: list[Any]) -> JsonMap:
        return {
            "contract": self.contract,
            "command": command,
            "ok": False,
            "warnings": [],
            "errors": errors,
            "error": {
                "code": "frontend.operation_failed",
                "message": f"{command} failed.",
                "severity": "error",
                "details": {"errors": errors},
            },
            "metadata": {"engine": "python", "components_version": None, "elapsed_ms": 0},
        }


class VerilogExportService:
    """Stable internal boundary for structural Verilog export."""

    contract = CONTRACT

    def export(self, design: Any, *, include_testbench: bool = True) -> JsonMap:
        exported = design_to_verilog(design, include_testbench=include_testbench)
        exported.setdefault("warnings", [])
        exported["required_files"] = self.required_files(exported.get("netlist", {}))
        return exported

    def required_files(self, netlist: JsonMap) -> list[str]:
        files: set[str] = set()
        for chip in netlist.get("chips", []):
            if not isinstance(chip, dict):
                continue
            part = str(chip.get("part", "")).upper()
            mapping = _verilog_mapping(part)
            if mapping is None:
                continue
            path = _verilog_file_for_part(part, str(mapping.get("module", "")))
            if path is not None:
                files.add(path)
                files.update(_verilog_dependencies_for_file(path))
            for required in _portable_files_for_part(part):
                files.add(required)
        return sorted(files)


def export_verilog(design: Any, *, include_testbench: bool = True) -> JsonMap:
    """Export structural Verilog through the service boundary."""

    return VerilogExportService().export(design, include_testbench=include_testbench)


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _probe_channels(items: Any) -> list[Any]:
    if isinstance(items, dict):
        channels = items.get("channels", [])
        return channels if isinstance(channels, list) else []
    return items if isinstance(items, list) else []


def _rule_mentions_ref(rule: str, ref: str) -> bool:
    for token in str(rule).replace("->", ",").replace("<->", ",").split(","):
        endpoint = token.strip()
        if endpoint == ref or endpoint.startswith(f"{ref}:"):
            return True
    return False


def _warnings_from_run(payload: JsonMap) -> list[JsonMap]:
    warnings: list[JsonMap] = []
    for item in payload.get("log", []):
        if isinstance(item, dict) and item.get("warning"):
            warnings.append({"step": item.get("step"), "warning": item.get("warning")})
    return warnings


def _board_errors(payload: JsonMap) -> list[Any]:
    snapshot = payload.get("snapshot", {})
    if not isinstance(snapshot, dict):
        return []
    board = snapshot.get("board", {})
    if not isinstance(board, dict):
        return []
    errors = board.get("errors", [])
    return errors if isinstance(errors, list) else []


def _expectation_errors(payload: JsonMap) -> list[Any]:
    expectations = payload.get("expectations", {})
    if not isinstance(expectations, dict):
        return []
    failed = expectations.get("failed", [])
    if not isinstance(failed, list):
        return []
    return [
        {"type": "expectation_failed", "name": item.get("name"), "checks": item.get("checks", [])}
        for item in failed
        if isinstance(item, dict)
    ]


def _frontend_snapshot(snapshot: JsonMap) -> JsonMap:
    design = snapshot.get("design", {})
    board = snapshot.get("board", {}) or {}
    return {
        "format": "components.frontend.snapshot",
        "version": 1,
        "design": {
            "name": design.get("name"),
            "description": design.get("description", ""),
            "modules": design.get("modules", {}),
            "groups": design.get("groups", {}),
        },
        "time_ns": board.get("time_ns", 0),
        "chips": board.get("chips", []),
        "buses": board.get("buses", []),
        "nets": board.get("nets", []),
        "rails": board.get("rails", []),
        "sources": board.get("sources", []),
        "stimulus": snapshot.get("stimulus"),
        "probes": snapshot.get("probes"),
        "displays": snapshot.get("displays", {}),
        "validation": snapshot.get("validate", {}),
        "errors": board.get("errors", []),
        "warnings": snapshot.get("validate", {}).get("warnings", []) if isinstance(snapshot.get("validate"), dict) else [],
        "layout": design.get("layout", {}),
        "labels": design.get("aliases", {}),
    }


def _verilog_file_for_part(part: str, module: str) -> str | None:
    try:
        manifest = component_detail(part)
        verilog = manifest.get("verilog", {})
        if isinstance(verilog, dict) and isinstance(verilog.get("file"), str):
            return str(verilog["file"])
    except (KeyError, ValueError):
        pass
    if module.startswith("ttl_"):
        return f"Verilog/74xx/{part.lower()}.v"
    if module.startswith("mem_"):
        return f"Verilog/Memory/{module[4:]}.v"
    return None


def _verilog_dependencies_for_file(path: str) -> set[str]:
    source = Path(path)
    try:
        text = source.read_text(encoding="utf-8")
    except OSError:
        return set()
    dependencies: set[str] = set()
    if re.search(r"\bmem_62256\b", text) and source.as_posix() != "DB/Memory/62256/simulation/model.v":
        dependencies.add("DB/Memory/62256/simulation/model.v")
    return dependencies


def _portable_files_for_part(part: str) -> list[str]:
    try:
        package = load_digital_package(part)
    except (KeyError, ValueError):
        return []
    result: list[str] = []
    for item in package.get("portable_files", []):
        if not isinstance(item, dict):
            continue
        source = item.get("source")
        if isinstance(source, str) and source:
            result.append(source)
    return result


def _response_command(response: JsonMap) -> str:
    command = response.get("command")
    if isinstance(command, str) and command:
        return command
    schema = response.get("schema")
    if schema == "components.virtual_physical_fault_report":
        return "circuit-faults"
    if "valid" in response or "validation" in response:
        return "validate"
    if "expectations" in response or "log" in response:
        return "run"
    if "sets" in response or "samples" in response or "probes" in response:
        return "probe"
    return "unknown"


def _response_ok(response: JsonMap) -> bool:
    if isinstance(response.get("ok"), bool):
        return bool(response["ok"])
    if isinstance(response.get("valid"), bool):
        return bool(response["valid"])
    if isinstance(response.get("result"), dict):
        result = response["result"]
        if isinstance(result.get("ok"), bool):
            return bool(result["ok"])
        if isinstance(result.get("valid"), bool):
            return bool(result["valid"])
    return not _collect_explain_issues(response)


def _top_level_fields(response: JsonMap) -> list[str]:
    return sorted(str(key) for key in response.keys())[:16]


def _collect_explain_issues(response: JsonMap) -> list[JsonMap]:
    issues: list[JsonMap] = []
    _collect_error_object(issues, response.get("error"), "$.error")
    _collect_issue_list(issues, response.get("errors"), "$.errors", default_severity="error")
    _collect_issue_list(issues, response.get("warnings"), "$.warnings", default_severity="warning")
    _collect_issue_list(issues, response.get("findings"), "$.findings", default_severity="error")
    _collect_issue_list(issues, response.get("missing"), "$.missing", default_severity="error")

    result = response.get("result")
    if isinstance(result, dict):
        _collect_issue_list(issues, result.get("errors"), "$.result.errors", default_severity="error")
        _collect_issue_list(issues, result.get("warnings"), "$.result.warnings", default_severity="warning")
        validation = result.get("validation")
        if isinstance(validation, dict):
            _collect_issue_list(issues, validation.get("errors"), "$.result.validation.errors", default_severity="error")
            _collect_issue_list(issues, validation.get("warnings"), "$.result.validation.warnings", default_severity="warning")
        run_payload = result.get("run")
        if isinstance(run_payload, dict):
            _collect_run_payload_issues(issues, run_payload, "$.result.run")
        _collect_run_payload_issues(issues, result, "$.result")

    validation = response.get("validation")
    if isinstance(validation, dict):
        _collect_issue_list(issues, validation.get("errors"), "$.validation.errors", default_severity="error")
        _collect_issue_list(issues, validation.get("warnings"), "$.validation.warnings", default_severity="warning")
    _collect_run_payload_issues(issues, response, "$")
    return issues


def _collect_run_payload_issues(issues: list[JsonMap], payload: JsonMap, base_path: str) -> None:
    board_errors = _board_errors(payload)
    if board_errors:
        _collect_issue_list(issues, board_errors, f"{base_path}.snapshot.board.errors", default_severity="error")
    expectations = payload.get("expectations")
    if isinstance(expectations, dict):
        _collect_issue_list(issues, expectations.get("failed"), f"{base_path}.expectations.failed", default_severity="error")


def _collect_error_object(issues: list[JsonMap], error: Any, path: str) -> None:
    if not isinstance(error, dict):
        return
    issues.append(_explain_issue(error, path, default_severity=str(error.get("severity", "error"))))
    details = error.get("details")
    if isinstance(details, dict):
        _collect_issue_list(issues, details.get("errors"), f"{path}.details.errors", default_severity="error")


def _collect_issue_list(issues: list[JsonMap], value: Any, path: str, *, default_severity: str) -> None:
    if not isinstance(value, list):
        return
    for index, item in enumerate(value):
        issues.append(_explain_issue(item, f"{path}[{index}]", default_severity=default_severity))


def _explain_issue(item: Any, path: str, *, default_severity: str) -> JsonMap:
    if isinstance(item, dict):
        code = item.get("code") or item.get("type") or item.get("category") or item.get("name") or "issue"
        summary = item.get("message") or item.get("detail") or item.get("summary") or _compact_json(item)
        severity = str(item.get("severity", default_severity))
        result: JsonMap = {
            "severity": severity,
            "code": str(code),
            "summary": str(summary),
            "source_path": path,
            "field_refs": _field_refs(item),
        }
        suggested = item.get("suggested_fix") or item.get("fix") or item.get("fix_method")
        if isinstance(suggested, str) and suggested:
            result["provided_next_step"] = suggested
        checks = item.get("checks")
        if isinstance(checks, list):
            result["check_count"] = len(checks)
        return result
    return {
        "severity": default_severity,
        "code": "issue",
        "summary": str(item),
        "source_path": path,
        "field_refs": {},
    }


def _field_refs(item: JsonMap) -> JsonMap:
    refs: JsonMap = {}
    for key in ("command", "ref", "part", "pin", "net", "bus", "rule", "name", "set", "step", "path"):
        value = item.get(key)
        if value is not None:
            refs[key] = value
    location = item.get("location")
    if isinstance(location, dict):
        refs["location"] = {key: value for key, value in location.items() if value is not None}
    return refs


def _compact_json(item: JsonMap) -> str:
    return json.dumps(item, sort_keys=True, separators=(",", ":"))[:240]


def _explain_next_steps(command: str, issues: list[JsonMap]) -> list[JsonMap]:
    if not issues:
        return [{"step": "No blocking issue was reported by the provided response.", "source": "$.ok"}]
    steps: list[JsonMap] = []
    seen: set[str] = set()
    for issue in issues:
        provided = issue.get("provided_next_step")
        if isinstance(provided, str) and provided and provided not in seen:
            steps.append({"step": provided, "source": issue.get("source_path")})
            seen.add(provided)
    generic = f"Fix the referenced {command} fields, then rerun {command} and explain-result."
    if generic not in seen:
        steps.append({"step": generic, "source": "references.issue_fields"})
    return steps


def _stop_before_hardware_warnings(command: str, ok: bool, issues: list[JsonMap]) -> list[JsonMap]:
    warnings: list[JsonMap] = []
    if not ok and command in {"validate", "run", "probe", "circuit-faults"}:
        warnings.append({
            "reason": f"{command} did not report ok=true.",
            "source": "$.ok",
        })
    for issue in issues:
        code = str(issue.get("code", "")).lower()
        summary = str(issue.get("summary", "")).lower()
        if any(word in f"{code} {summary}" for word in ("bus_conflict", "contention", "output_output", "hot", "current")):
            warnings.append({
                "reason": "The provided response mentions a bus/output/current risk.",
                "source": issue.get("source_path"),
            })
    return warnings
