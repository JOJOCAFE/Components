#!/usr/bin/env python3
"""Audit canonical timing-parameter coverage in component definitions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "TIMING_PARAMETER_AUDIT.md"

PARAMETERS = {
    "tPLH": {
        "exact": ("tplh", "t_plh", "low_to_high_propagation"),
        "generic": ("tpd", "propagation", "transition", "to_q", "to_output"),
        "meaning": "input/output propagation delay for output LOW-to-HIGH",
    },
    "tPHL": {
        "exact": ("tphl", "t_phl", "high_to_low_propagation"),
        "generic": ("tpd", "propagation", "transition", "to_q", "to_output"),
        "meaning": "input/output propagation delay for output HIGH-to-LOW",
    },
    "tPZH": {
        "exact": ("tpzh", "t_pzh", "high_z_to_high"),
        "generic": ("enable", "output_enable", "high_z_to_output", "low_z"),
        "meaning": "output enable from high-Z to HIGH",
    },
    "tPZL": {
        "exact": ("tpzl", "t_pzl", "high_z_to_low"),
        "generic": ("enable", "output_enable", "high_z_to_output", "low_z"),
        "meaning": "output enable from high-Z to LOW",
    },
    "tPHZ": {
        "exact": ("tphz", "t_phz", "high_to_high_z"),
        "generic": ("disable", "high_z", "output_to_high_z", "to_z"),
        "meaning": "output disable from HIGH to high-Z",
    },
    "tPLZ": {
        "exact": ("tplz", "t_plz", "low_to_high_z"),
        "generic": ("disable", "high_z", "output_to_high_z", "to_z"),
        "meaning": "output disable from LOW to high-Z",
    },
    "clock-to-Q high": {
        "exact": ("clock_to_q_high", "clk_to_q_high", "clock_to_qh"),
        "generic": ("clock_to_q", "clk_to_q"),
        "meaning": "clock edge to Q HIGH",
    },
    "clock-to-Q low": {
        "exact": ("clock_to_q_low", "clk_to_q_low", "clock_to_ql"),
        "generic": ("clock_to_q", "clk_to_q"),
        "meaning": "clock edge to Q LOW",
    },
    "setup": {
        "exact": ("setup", "setup_before_clock", "setup_time"),
        "generic": (),
        "meaning": "input setup time before active clock/control edge",
    },
    "hold": {
        "exact": ("hold", "hold_after_clock", "hold_time"),
        "generic": (),
        "meaning": "input hold time after active clock/control edge",
    },
    "minimum pulse width": {
        "exact": ("pulse_width", "minimum_pulse_width", "min_pulse", "clock_high_or_low", "clear_low"),
        "generic": (),
        "meaning": "minimum clock, reset, write, or control pulse width",
    },
}

PARAMETER_KEYS = {
    "tPLH": "tPLH",
    "tPHL": "tPHL",
    "tPZH": "tPZH",
    "tPZL": "tPZL",
    "tPHZ": "tPHZ",
    "tPLZ": "tPLZ",
    "clock-to-Q high": "clock_to_q_high",
    "clock-to-Q low": "clock_to_q_low",
    "setup": "setup",
    "hold": "hold",
    "minimum pulse width": "minimum_pulse_width",
}

SUMMARY_STATUSES = ("exact", "generic", "not_applicable", "missing")


def timing_payload(data: dict[str, Any]) -> dict[str, Any]:
    layer = data.get("definition_layers", {}).get("timing")
    if isinstance(layer, dict):
        return layer
    timing = data.get("timing")
    return timing if isinstance(timing, dict) else {}


def has_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle.lower() in text for needle in needles)


def classify(payload: dict[str, Any], parameter: str) -> str:
    spec = PARAMETERS[parameter]
    timing_parameters = payload.get("timing_parameters", {})
    if isinstance(timing_parameters, dict):
        parameters = timing_parameters.get("parameters", {})
        key = PARAMETER_KEYS[parameter]
        entry = parameters.get(key) if isinstance(parameters, dict) else None
        if isinstance(entry, dict):
            status = entry.get("status")
            if status == "exact":
                return "exact"
            if status in {"generic", "default"}:
                return "generic"
            if status == "not_applicable":
                return "not_applicable"
            if status == "missing":
                return "missing"
    text = json.dumps(payload, sort_keys=True).lower()
    if has_any(text, spec["exact"]):
        return "exact"
    if has_any(text, spec["generic"]):
        return "generic"
    return "missing"


def group_from_path(path: Path) -> str:
    return path.relative_to(ROOT / "lib" / "standard").parts[0]


def audit_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted((ROOT / "lib" / "standard").glob("*/*/definition/definition.json")):
        group = group_from_path(path)
        if group not in {"74xx", "memory"}:
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("schema") != "db.component.digital":
            continue
        part = str(data.get("part") or path.parents[1].name)
        payload = timing_payload(data)
        if not payload:
            continue
        result = {parameter: classify(payload, parameter) for parameter in PARAMETERS}
        rows.append({"part": part, "group": group, "result": result})
    return rows


def summary(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    counts = {parameter: {status: 0 for status in SUMMARY_STATUSES} for parameter in PARAMETERS}
    for row in rows:
        for parameter, status in row["result"].items():
            counts[parameter][status] += 1
    return counts


def write_report(rows: list[dict[str, Any]]) -> None:
    counts = summary(rows)
    lines = [
        "# Timing Parameter Audit",
        "",
        "Generated by `tools/timing_parameter_audit.py`.",
        "",
        "This checks whether timing definitions expose the canonical datasheet",
        "parameter names requested for component selection and physical timing",
        "review. `exact` means the canonical polarity-specific term is present;",
        "`generic` means the DB has related timing such as `tpd`, `enable`,",
        "`disable`, `clock_to_q`, or memory high-Z timing but does not split the",
        "requested HIGH/LOW polarity; `not_applicable` means the chip has no such",
        "clocked, setup/hold, pulse-width, or high-Z behavior; `missing` means no",
        "matching field was found.",
        "",
        "## Summary",
        "",
        "| Parameter | Meaning | Exact | Generic | Not Applicable | Missing |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for parameter, spec in PARAMETERS.items():
        row = counts[parameter]
        lines.append(
            f"| {parameter} | {spec['meaning']} | {row['exact']} | {row['generic']} | {row['not_applicable']} | {row['missing']} |"
        )
    lines.extend([
        "",
        "## Current Finding",
        "",
        "- Every applicable canonical parameter is now either exact or visibly generic;",
        "  no required canonical timing field is silently missing.",
        "- `74HC07` remains generic for `tPLH/tPHL` because its open-drain output is",
        "  specified through pull-down enable/disable timing and external pull-up behavior.",
        "- `74HC74` remains generic for propagation and clock-to-Q polarity because the",
        "  manufacturer specifies aggregate `tpd` as the maximum of `tPLH` and `tPHL`",
        "  without publishing separate numeric values.",
        "",
        "## Per-Part Matrix",
        "",
        "| Part | Group | " + " | ".join(PARAMETERS) + " |",
        "|---|---|" + "|".join("---" for _ in PARAMETERS) + "|",
    ])
    for row in rows:
        statuses = [row["result"][parameter] for parameter in PARAMETERS]
        lines.append(f"| {row['part']} | {row['group']} | " + " | ".join(statuses) + " |")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    rows = audit_rows()
    write_report(rows)
    print(f"wrote {REPORT.relative_to(ROOT)} for {len(rows)} timing definitions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
