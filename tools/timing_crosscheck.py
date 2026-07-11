#!/usr/bin/env python3
"""Audit DB timing definitions against local datasheet evidence.

This does not infer new timing from datasheets. It checks what is already in
the DB and reports whether those timing numbers are source-backed, default-only,
or mixed with conservative simulator timing.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Source"
REPORT = ROOT / "TIMING_CROSSCHECK_REPORT.md"

SOURCE_ALIASES = {
    "62256": ["KM62256C.PDF", "AS6C62256.PDF"],
    "AS6C62256": ["AS6C62256.PDF"],
    "CY7C199": ["CY7C199.PDF"],
    "74HC4078": ["M74HC4078.PDF"],
    "74HC593": ["M54HC593.PDF"],
    "74HC922": ["MM74C922.PDF"],
}


def part_filename_match(part: str, name: str) -> bool:
    stem = Path(name).stem
    if stem == part:
        return True
    if not stem.startswith(part):
        return False
    return stem[len(part) : len(part) + 1] in {"", "_", "-", "."}


def clean_source_path(raw: str) -> Path:
    text = raw.strip().strip("`")
    if text.startswith("Components/"):
        text = text[len("Components/") :]
    if text.startswith("./"):
        text = text[2:]
    return ROOT / text


def source_entries(data: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    entries.extend((data.get("datasheet") or {}).get("sources") or [])
    entries.extend(data.get("sources") or [])
    for layer in data.get("definition_layers", {}).values():
        if isinstance(layer, dict):
            evidence = layer.get("evidence")
            if isinstance(evidence, dict):
                entries.append(evidence)
    return entries


def candidate_sources(part: str, data: dict[str, Any]) -> tuple[list[Path], list[Path]]:
    explicit: list[Path] = []
    for entry in source_entries(data):
        if entry.get("file"):
            explicit.append(clean_source_path(str(entry["file"])))
    alias = [SOURCE / name for name in SOURCE_ALIASES.get(part, [])]
    globbed = [
        path
        for path in SOURCE.iterdir()
        if path.is_file()
        and path.suffix.lower() == ".pdf"
        and part_filename_match(part, path.name)
    ]
    seen: set[str] = set()
    existing: list[Path] = []
    missing: list[Path] = []
    for path in explicit + alias + globbed:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        if path.exists():
            existing.append(path)
        elif path in explicit:
            missing.append(path)
    return existing, missing


def pdf_text(path: Path) -> str | None:
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", str(path), "-"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout


def timing_layer(data: dict[str, Any]) -> dict[str, Any] | None:
    layered = data.get("definition_layers", {}).get("timing")
    if isinstance(layered, dict):
        return layered
    if isinstance(data.get("timing"), dict):
        return {"delay": data["timing"]}
    return None


def delay_block(layer: dict[str, Any]) -> dict[str, Any]:
    delay = layer.get("delay")
    return delay if isinstance(delay, dict) else layer


def contains_token(obj: Any, token: str) -> bool:
    return token in json.dumps(obj, sort_keys=True)


def collect_datasheet_numbers(obj: Any, in_datasheet: bool = False) -> list[int | float]:
    values: list[int | float] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            key_is_datasheet = in_datasheet or str(key).startswith("datasheet_")
            values.extend(collect_datasheet_numbers(value, key_is_datasheet))
    elif isinstance(obj, list):
        for value in obj:
            values.extend(collect_datasheet_numbers(value, in_datasheet))
    elif in_datasheet and isinstance(obj, (int, float)) and not isinstance(obj, bool):
        values.append(obj)
    return values


def unique_values(values: list[int | float]) -> list[int | float]:
    unique = []
    seen = set()
    for value in values:
        key = float(value)
        if key in seen:
            continue
        seen.add(key)
        unique.append(value)
    return unique


def value_in_text(value: int | float, text: str) -> bool:
    # Match standalone numeric tokens and common decimal forms. This is evidence
    # of presence in the source text, not a full semantic table parser.
    if isinstance(value, float) and not value.is_integer():
        forms = {str(value), f"{value:g}"}
    else:
        n = int(value)
        forms = {str(n), f"{n}.0"}
    for form in forms:
        if re.search(rf"(?<![A-Za-z0-9.]){re.escape(form)}(?![A-Za-z0-9.])", text):
            return True
    if isinstance(value, (int, float)) and float(value).is_integer():
        n = int(value)
        if n >= 1000 and n % 1000 == 0:
            ms = n // 1000
            if re.search(rf"(?<![A-Za-z0-9.]){ms}(?![A-Za-z0-9.])\s*m\s*s", text, re.I):
                return True
    return False


def source_text_status(part: str, data: dict[str, Any]) -> tuple[str, str | None]:
    existing, missing = candidate_sources(part, data)
    if existing:
        texts = []
        labels = []
        for path in existing:
            text = pdf_text(path)
            rel = str(path.relative_to(ROOT))
            if text is not None:
                texts.append(text)
                labels.append(rel)
            else:
                labels.append(f"UNREADABLE:{rel}")
        return "; ".join(labels), "\n".join(texts) if texts else None
    if missing:
        return "; ".join(f"MISSING:{p.relative_to(ROOT)}" for p in missing), None
    return "NO_LOCAL_SOURCE_PDF", None


def group_from_definition(path: Path) -> str:
    return path.relative_to(ROOT / "DB").parts[0]


def main() -> int:
    rows = []
    failures = []
    not_source_verified = []
    mixed_defaults = []

    for definition in sorted((ROOT / "DB").glob("*/**/definition/definition.json")):
        group = group_from_definition(definition)
        if group not in {"74xx", "Memory"}:
            continue
        data = json.loads(definition.read_text(encoding="utf-8"))
        part = str(data.get("part") or definition.parents[1].name)
        layer = timing_layer(data)
        if layer is None:
            continue
        delay = delay_block(layer)
        status = str(delay.get("status") or "")
        has_datasheet_values = any(k.startswith("datasheet_") for k in delay)
        has_conservative = contains_token(delay, "conservative_default")
        has_model_default = contains_token(delay, "model-derived") or contains_token(
            delay, "legacy functional simulator default"
        )
        source_label, text = source_text_status(part, data)
        ds_values = unique_values(collect_datasheet_numbers(delay))

        missing_values: list[int | float] = []
        if has_datasheet_values:
            if text is None:
                result = "CANNOT_READ_SOURCE_FOR_DATASHEET_TIMING"
                details = "datasheet timing values exist in DB but local source text is unavailable"
                failures.append(f"{part}:source unavailable")
            else:
                missing_values = [
                    value for value in ds_values if not value_in_text(value, text)
                ]
                if missing_values:
                    result = "FAIL_DATASHEET_VALUE_NOT_FOUND_IN_SOURCE_TEXT"
                    details = "missing timing values in source text: " + ", ".join(
                        str(v) for v in missing_values
                    )
                    failures.append(f"{part}:{details}")
                elif has_conservative or has_model_default:
                    result = "PASS_SOURCE_VALUES_PRESENT_BUT_PUBLIC_TIMING_HAS_DEFAULTS"
                    details = (
                        f"datasheet values present ({', '.join(str(v) for v in ds_values)}); "
                        "public/simulator timing still includes defaults"
                    )
                    mixed_defaults.append(part)
                else:
                    result = "PASS_SOURCE_VALUES_PRESENT"
                    details = f"datasheet values present: {', '.join(str(v) for v in ds_values)}"
        else:
            if has_conservative:
                result = "NOT_SOURCE_VERIFIED_CONSERVATIVE_DEFAULT"
                details = "timing uses conservative/default model delay, not datasheet timing"
            elif status == "model-derived" or has_model_default or "delay_ns" in delay:
                result = "NOT_SOURCE_VERIFIED_MODEL_DERIVED"
                details = "timing is model-derived/default only"
            else:
                result = "NO_DATASHEET_TIMING_VALUES_IN_DB"
                details = "no datasheet timing values found in timing definition"
            not_source_verified.append(part)

        rows.append(
            {
                "part": part,
                "group": group,
                "status": status or "-",
                "result": result,
                "source": source_label,
                "values": ", ".join(str(v) for v in ds_values) if ds_values else "-",
                "details": details,
            }
        )

    lines = [
        "# Timing Cross-check Report",
        "",
        "Generated by `tools/timing_crosscheck.py` from DB timing definitions and local datasheet PDFs.",
        "",
        "Important: this is timing-only. `PASS_SOURCE_VALUES_PRESENT` means the DB datasheet timing numbers are present in extracted local PDF text. It does not infer missing timing tables. Any conservative/default simulator timing remains reported as not source-verified or mixed.",
        "",
        "| Part | Group | Timing Status | Result | Source/PDF | Datasheet Values Checked | Details |",
        "|---|---:|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {part} | {group} | {status} | {result} | {source} | {values} | {details} |".format(
                **row
            )
        )

    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Timing definitions checked: {len(rows)}",
            f"- Failures: {len(failures)}",
            f"- Source-backed values present but public/default timing still mixed: {len(mixed_defaults)}",
            f"- Not source-verified timing definitions: {len(not_source_verified)}",
            "",
            "## Failure Detail",
        ]
    )
    lines.extend([f"- {item}" for item in failures] or ["- none"])
    lines.extend(["", "## Mixed Default Detail"])
    lines.extend([f"- {item}" for item in mixed_defaults] or ["- none"])
    lines.extend(["", "## Not Source-verified Detail"])
    lines.extend([f"- {item}" for item in not_source_verified] or ["- none"])
    lines.append("")

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(
        json.dumps(
            {
                "rows": len(rows),
                "failures": failures,
                "mixed_defaults": mixed_defaults,
                "not_source_verified": not_source_verified,
                "report": str(REPORT),
            },
            indent=2,
        )
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
