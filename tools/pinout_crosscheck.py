#!/usr/bin/env python3
"""Cross-check DB pin maps against available pinout evidence.

This audit is intentionally conservative:
- manually extracted maps are used for the recently added datasheet-only parts;
- otherwise DB IC packages are compared with their embedded pinout table in
  simulation/model.v;
- local PDFs are checked for readability with pdfinfo, not parsed as the sole
  authority for every legacy package.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source"
REPORT = ROOT / "docs" / "PINOUT_CROSSCHECK_REPORT.md"


MANUAL_PINOUTS: dict[str, dict[int, str]] = {
    "74HC03": {
        1: "1A",
        2: "1B",
        3: "1Y",
        4: "2A",
        5: "2B",
        6: "2Y",
        7: "GND",
        8: "3Y",
        9: "3A",
        10: "3B",
        11: "4Y",
        12: "4A",
        13: "4B",
        14: "VCC",
    },
    "74HC05": {
        1: "1A",
        2: "1Y",
        3: "2A",
        4: "2Y",
        5: "3A",
        6: "3Y",
        7: "GND",
        8: "4Y",
        9: "4A",
        10: "5Y",
        11: "5A",
        12: "6Y",
        13: "6A",
        14: "VCC",
    },
    "74HC132": {
        1: "1A",
        2: "1B",
        3: "1Y",
        4: "2A",
        5: "2B",
        6: "2Y",
        7: "GND",
        8: "3Y",
        9: "3A",
        10: "3B",
        11: "4Y",
        12: "4A",
        13: "4B",
        14: "VCC",
    },
    "74HC4049": {
        1: "VCC",
        2: "1Y",
        3: "1A",
        4: "2Y",
        5: "2A",
        6: "3Y",
        7: "3A",
        8: "GND",
        9: "4A",
        10: "4Y",
        11: "5A",
        12: "5Y",
        13: "NC",
        14: "6A",
        15: "6Y",
        16: "NC",
    },
    "74HC4050": {
        1: "VCC",
        2: "1Y",
        3: "1A",
        4: "2Y",
        5: "2A",
        6: "3Y",
        7: "3A",
        8: "GND",
        9: "4A",
        10: "4Y",
        11: "5A",
        12: "5Y",
        13: "NC",
        14: "6A",
        15: "6Y",
        16: "NC",
    },
    "74HC4520": {
        1: "1CP",
        2: "1E",
        3: "1Q0",
        4: "1Q1",
        5: "1Q2",
        6: "1Q3",
        7: "1MR",
        8: "GND",
        9: "2CP",
        10: "2E",
        11: "2Q0",
        12: "2Q1",
        13: "2Q2",
        14: "2Q3",
        15: "2MR",
        16: "VCC",
    },
    "74HC4538": {
        1: "1Cx",
        2: "1RxCx",
        3: "/1R",
        4: "1A",
        5: "1B",
        6: "1Q",
        7: "/1Q",
        8: "GND",
        9: "/2Q",
        10: "2Q",
        11: "2B",
        12: "2A",
        13: "/2R",
        14: "2RxCx",
        15: "2Cx",
        16: "VCC",
    },
    "74HCT04": {
        1: "1A",
        2: "1Y",
        3: "2A",
        4: "2Y",
        5: "3A",
        6: "3Y",
        7: "GND",
        8: "4Y",
        9: "4A",
        10: "5Y",
        11: "5A",
        12: "6Y",
        13: "6A",
        14: "VCC",
    },
    "74HCT14": {
        1: "1A",
        2: "1Y",
        3: "2A",
        4: "2Y",
        5: "3A",
        6: "3Y",
        7: "GND",
        8: "4Y",
        9: "4A",
        10: "5Y",
        11: "5A",
        12: "6Y",
        13: "6A",
        14: "VCC",
    },
    "74HCT245": {
        1: "DIR",
        2: "A1",
        3: "A2",
        4: "A3",
        5: "A4",
        6: "A5",
        7: "A6",
        8: "A7",
        9: "A8",
        10: "GND",
        11: "B8",
        12: "B7",
        13: "B6",
        14: "B5",
        15: "B4",
        16: "B3",
        17: "B2",
        18: "B1",
        19: "/OE",
        20: "VCC",
    },
    "74HCT541": {
        1: "/OE1",
        2: "A1",
        3: "A2",
        4: "A3",
        5: "A4",
        6: "A5",
        7: "A6",
        8: "A7",
        9: "A8",
        10: "GND",
        11: "Y8",
        12: "Y7",
        13: "Y6",
        14: "Y5",
        15: "Y4",
        16: "Y3",
        17: "Y2",
        18: "Y1",
        19: "/OE2",
        20: "VCC",
    },
    "74HCT574": {
        1: "/OE",
        2: "1D",
        3: "2D",
        4: "3D",
        5: "4D",
        6: "5D",
        7: "6D",
        8: "7D",
        9: "8D",
        10: "GND",
        11: "CLK",
        12: "8Q",
        13: "7Q",
        14: "6Q",
        15: "5Q",
        16: "4Q",
        17: "3Q",
        18: "2Q",
        19: "1Q",
        20: "VCC",
    },
    "LM358": {
        1: "OUT1",
        2: "IN1-",
        3: "IN1+",
        4: "VSS",
        5: "IN2+",
        6: "IN2-",
        7: "OUT2",
        8: "VCC",
    },
    "LM393": {
        1: "OUT1",
        2: "IN1-",
        3: "IN1+",
        4: "GND",
        5: "IN2+",
        6: "IN2-",
        7: "OUT2",
        8: "VCC",
    },
    "MAX232": {
        1: "C1+",
        2: "V+",
        3: "C1-",
        4: "C2+",
        5: "C2-",
        6: "V-",
        7: "T2OUT",
        8: "R2IN",
        9: "R2OUT",
        10: "T2IN",
        11: "T1IN",
        12: "R1OUT",
        13: "R1IN",
        14: "T1OUT",
        15: "GND",
        16: "VCC",
    },
    "NE555": {
        1: "GND",
        2: "TRIG",
        3: "OUT",
        4: "RESET",
        5: "CTRL",
        6: "THRESH",
        7: "DISCH",
        8: "VCC",
    },
    "ULN2803A": {
        1: "1B",
        2: "2B",
        3: "3B",
        4: "4B",
        5: "5B",
        6: "6B",
        7: "7B",
        8: "8B",
        9: "GND",
        10: "COM",
        11: "8C",
        12: "7C",
        13: "6C",
        14: "5C",
        15: "4C",
        16: "3C",
        17: "2C",
        18: "1C",
    },
}


SOURCE_ALIASES = {
    "62256": ["KM62256C.PDF", "AS6C62256.PDF"],
    "AS6C62256": ["AS6C62256.PDF"],
    "CY7C199": ["CY7C199.PDF"],
    "74HC4078": ["M74HC4078.PDF"],
    "74HC593": ["M54HC593.PDF"],
    "74HC922": ["MM74C922.PDF"],
}


def norm_name(value: str) -> str:
    value = value.strip().strip("`")
    value = value.replace("\\", "/")
    value = re.sub(r"\s+", "", value)
    return value


def db_pin_map(data: dict) -> dict[int, str]:
    return {int(pin["number"]): norm_name(str(pin["name"])) for pin in data["pins"]}


def parse_embedded_pinout(model_v: Path) -> dict[int, str] | None:
    if not model_v.exists():
        return None
    pins: dict[int, str] = {}
    for line in model_v.read_text(encoding="utf-8").splitlines():
        match = re.match(r"\s*//\s*\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|", line)
        if match:
            pins[int(match.group(1))] = norm_name(match.group(2))
    return pins or None


def source_entries(data: dict) -> list[dict]:
    entries = []
    datasheet = data.get("datasheet") or {}
    entries.extend(datasheet.get("sources") or [])
    entries.extend(data.get("sources") or [])
    return entries


def clean_source_path(raw: str) -> Path:
    text = raw.strip().strip("`")
    if text.startswith("Components/"):
        text = text[len("Components/") :]
    if text.startswith("./"):
        text = text[2:]
    return ROOT / text


def part_filename_match(part: str, name: str) -> bool:
    stem = Path(name).stem
    if stem == part:
        return True
    if not stem.startswith(part):
        return False
    next_char = stem[len(part) : len(part) + 1]
    return next_char in {"_", "-", ".", ""}


def pdf_page_count(path: Path) -> int | None:
    try:
        result = subprocess.run(
            ["pdfinfo", str(path)],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    match = re.search(r"^Pages:\s+(\d+)\s*$", result.stdout, flags=re.MULTILINE)
    return int(match.group(1)) if match else None


def candidate_sources(part: str, data: dict) -> tuple[list[Path], list[Path]]:
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
    seen = set()
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


def source_status(part: str, data: dict) -> tuple[str, bool]:
    existing, missing = candidate_sources(part, data)
    ok_bits = []
    bad_bits = []
    for path in existing:
        pages = pdf_page_count(path)
        rel = path.relative_to(ROOT)
        if pages is None:
            bad_bits.append(f"UNREADABLE:{rel}")
        else:
            ok_bits.append(f"PDF_OK:{rel}:{pages}p")
    for path in missing:
        rel = path.relative_to(ROOT)
        bad_bits.append(f"MISSING:{rel}")
    if ok_bits:
        return "; ".join(ok_bits + bad_bits), not bad_bits
    if bad_bits:
        return "; ".join(bad_bits), False
    return "NO_LOCAL_SOURCE_PDF", False


def expected_pinout(part: str, model_v: Path) -> tuple[dict[int, str] | None, str]:
    if part in MANUAL_PINOUTS:
        return {k: norm_name(v) for k, v in MANUAL_PINOUTS[part].items()}, (
            "manual_datasheet_text_extraction"
        )
    parsed = parse_embedded_pinout(model_v)
    if parsed:
        return parsed, f"embedded_pinout_doc:{model_v.relative_to(ROOT)}"
    return None, "no model.v"


def compare_pins(actual: dict[int, str], expected: dict[int, str] | None) -> list[str]:
    if expected is None:
        return []
    issues: list[str] = []
    for number in sorted(set(actual) | set(expected)):
        a = actual.get(number)
        e = expected.get(number)
        if a != e:
            issues.append(f"pin {number}: DB={a!r} evidence={e!r}")
    return issues


def group_from_definition(path: Path, data: dict) -> str:
    try:
        return path.relative_to(ROOT / "lib" / "standard").parts[0]
    except ValueError:
        return str(data.get("group") or data.get("metadata", {}).get("group") or "")


def main() -> int:
    rows = []
    mismatches = []
    source_problems = []

    for definition in sorted((ROOT / "lib" / "standard").glob("*/**/definition/definition.json")):
        data = json.loads(definition.read_text(encoding="utf-8"))
        part = str(data.get("part") or definition.parents[1].name)
        group = group_from_definition(definition, data)
        pins = db_pin_map(data)
        model_v = definition.parents[1] / "simulation" / "model.v"
        is_datasheet_ic = group in {"74xx", "memory", "support"}

        if is_datasheet_ic:
            expected, evidence = expected_pinout(part, model_v)
            issues = compare_pins(pins, expected)
            source_text, source_ok = source_status(part, data)
            if issues:
                result = "FAIL_PIN_MAP_MISMATCH"
                details = "; ".join(issues)
                mismatches.append(f"{part}:{details}")
            elif expected is None:
                result = "CANNOT_CHECK_PIN_MAP"
                details = "no independent pinout map available"
                source_problems.append(f"{part}:NO_PINOUT_EVIDENCE")
            elif not source_ok:
                result = "PASS_PIN_MAP_BUT_SOURCE_PROBLEM"
                details = f"{len(pins)} pins match"
                source_problems.append(f"{part}:{source_text}")
            else:
                result = "PASS_EXACT_PIN_MAP"
                details = f"{len(pins)} pins match"
        else:
            evidence = "no datasheet-backed IC pinout expected"
            source_text = "N/A"
            result = "SKIP_NON_IC_OR_NO_DATASHEET_PINOUT"
            details = "virtual/passive/discrete package, not an IC datasheet pinout"

        rows.append(
            {
                "part": part,
                "group": group,
                "pins": len(pins),
                "result": result,
                "evidence": evidence,
                "source": source_text,
                "details": details,
            }
        )

    lines = [
        "# Pinout Cross-check Report",
        "",
        "Generated by `tools/pinout_crosscheck.py` against DB definitions, local PDF readability, and available pinout evidence.",
        "",
        "Important: `embedded_pinout_doc` means the DB definition exactly matches the repo embedded pinout table that cites datasheet evidence; `manual_datasheet_text_extraction` means the pin map was checked against extracted datasheet text/diagram in this pass. `PDF_OK` means the local datasheet file is present and readable by `pdfinfo`.",
        "",
        "| Part | Group | Pins | Result | Evidence | source/PDF | Details |",
        "|---|---:|---:|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {part} | {group} | {pins} | {result} | {evidence} | {source} | {details} |".format(
                **row
            )
        )

    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Total DB definitions checked: {len(rows)}",
            f"- Datasheet-backed IC definitions checked: {sum(1 for r in rows if r['group'] in {'74xx', 'Memory', 'Support'})}",
            f"- Mismatches: {len(mismatches)}",
            f"- Cannot/source-problem items: {len(source_problems)}",
            "",
            "## Cannot/source-problem detail",
        ]
    )
    if source_problems:
        lines.extend(f"- {item}" for item in source_problems)
    else:
        lines.append("- none")
    lines.extend(["", "## Mismatch detail"])
    if mismatches:
        lines.extend(f"- {item}" for item in mismatches)
    else:
        lines.append("- none")
    lines.append("")

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(
        json.dumps(
            {
                "rows": len(rows),
                "datasheet_ic_rows": sum(
                    1 for r in rows if r["group"] in {"74xx", "memory", "support"}
                ),
                "mismatches": mismatches,
                "source_problems": source_problems,
                "report": str(REPORT),
            },
            indent=2,
        )
    )
    return 1 if mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())
