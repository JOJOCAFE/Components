"""Internal service interfaces over the Components design backend."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .netlist import _verilog_mapping, design_to_verilog


JsonMap = dict[str, Any]
ROOT = Path(__file__).resolve().parents[2]


class VerilogExportService:
    """Stable internal boundary for structural Verilog export."""

    contract = "components.service.v1"

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
        return sorted(files)


def export_verilog(design: Any, *, include_testbench: bool = True) -> JsonMap:
    """Export structural Verilog through the service boundary."""

    return VerilogExportService().export(design, include_testbench=include_testbench)


def _verilog_file_for_part(part: str, module: str) -> str | None:
    db_file = ROOT / "db" / part / "chip.json"
    if db_file.exists():
        try:
            import json

            manifest = json.loads(db_file.read_text(encoding="utf-8"))
            verilog = manifest.get("verilog", {})
            if isinstance(verilog, dict) and isinstance(verilog.get("file"), str):
                return str(verilog["file"])
        except (OSError, ValueError):
            pass
    if module.startswith("ttl_"):
        return f"verilog/74HC/{part.lower()}.v"
    if module.startswith("mem_"):
        return f"verilog/Memory/{module[4:]}.v"
    return None
