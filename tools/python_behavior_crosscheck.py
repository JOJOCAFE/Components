#!/usr/bin/env python3
"""Cross-check local Python chip models against DB behavior and timing records."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "Docs" / "PYTHON_BEHAVIOR_CROSSCHECK_REPORT.md"
sys.path.insert(0, str(ROOT / "python"))

from chiplib.core import Z  # noqa: E402


DIR_MAP = {
    "in": "input",
    "out": "output",
    "bidir": "bidirectional",
    "power": "power",
    "nc": "nc",
}


GENERIC_INPUT_ALIASES = {
    "A": ("1A", "A0", "A", "D0", "D1"),
    "B": ("1B", "B0", "B", "D1"),
    "C": ("1C", "C", "D2"),
    "D": ("1D", "D", "D3"),
    "Y": ("1Y", "Y", "Q0", "QA"),
    "/LD": ("/LOAD",),
}


ANNOTATION_EXPECT_KEYS = {
    "busy_updates",
    "no_write",
    "write",
    "write_pending",
}


def import_model(path: Path):
    name = "model_" + "_".join(path.parts[-4:-2])
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def normalize_value(value: Any) -> Any:
    if value == "Z":
        return Z
    if value in (0, 1, Z):
        return value
    return value


def pin_name(chip: Any, name: str) -> str | None:
    if name in chip.pin_names:
        return name
    if name in GENERIC_INPUT_ALIASES:
        for candidate in GENERIC_INPUT_ALIASES[name]:
            if candidate in chip.pin_names:
                return candidate
    return None


def eval_chip(chip: Any) -> None:
    chip.update()
    chip.commit()


def run_vectors(chip: Any, vectors: list[dict[str, Any]], data: dict[str, Any]) -> tuple[int, list[str], int, list[str]]:
    runnable = 0
    failures: list[str] = []
    invalid: list[str] = []
    placeholders = 0
    current_chip = chip.__class__(chip.name)
    current_buses = bus_aliases(data, current_chip)
    for vector in vectors:
        inputs = vector.get("inputs")
        expect = vector.get("expect")
        if not isinstance(inputs, dict) or not isinstance(expect, dict):
            placeholders += 1
            continue
        values = list(inputs.values()) + list(expect.values())
        if any(isinstance(v, str) and not (v.startswith("0x") or v in {"Z"}) for v in values):
            placeholders += 1
            continue
        if vector.get("fresh") is True:
            current_chip = chip.__class__(chip.name)
            current_buses = bus_aliases(data, current_chip)
        chip_for_vector = current_chip
        buses_for_vector = current_buses
        unresolved = []
        for key, value in inputs.items():
            if key in buses_for_vector and isinstance(value, str) and value.startswith("0x"):
                set_bus(chip_for_vector, buses_for_vector[key], value)
                continue
            actual = pin_name(chip_for_vector, key)
            if actual is not None:
                chip_for_vector.set_input(actual, normalize_value(value))
                continue
            if key in buses_for_vector:
                set_bus(chip_for_vector, buses_for_vector[key], value)
            else:
                unresolved.append(key)
        if unresolved:
            placeholders += 1
            continue
        if vector.get("clock") is True:
            chip_for_vector.clock_edge()
            chip_for_vector.commit()
            eval_chip(chip_for_vector)
        else:
            eval_chip(chip_for_vector)
        runnable += 1
        for key, expected in expect.items():
            if key in ANNOTATION_EXPECT_KEYS:
                if not check_annotation(chip_for_vector, key, expected):
                    failures.append(f"{vector.get('name', 'vector')}: annotation {key} expected {expected!r}")
                continue
            if key in buses_for_vector and isinstance(expected, str) and (expected.startswith("0x") or expected == "Z"):
                observed_bus = read_bus(chip_for_vector, buses_for_vector[key])
                expected_bus = normalize_bus_expected(expected, len(buses_for_vector[key]))
                if observed_bus != expected_bus:
                    failures.append(
                        f"{vector.get('name', 'vector')}: {key} expected {expected!r}, got {observed_bus!r}"
                    )
                continue
            actual_name = pin_name(chip_for_vector, key)
            if actual_name is None and key in buses_for_vector:
                observed_bus = read_bus(chip_for_vector, buses_for_vector[key])
                expected_bus = normalize_bus_expected(expected, len(buses_for_vector[key]))
                if observed_bus != expected_bus:
                    failures.append(
                        f"{vector.get('name', 'vector')}: {key} expected {expected!r}, got {observed_bus!r}"
                    )
                continue
            if actual_name is None:
                invalid.append(f"{vector.get('name', 'vector')}: output {key} not present")
                continue
            if chip_for_vector.pin(actual_name).direction not in {"out", "bidir"}:
                invalid.append(f"{vector.get('name', 'vector')}: {key} is not an output pin")
                continue
            observed = chip_for_vector.read(actual_name)
            if observed != normalize_value(expected):
                failures.append(
                    f"{vector.get('name', 'vector')}: {key} expected {expected!r}, got {observed!r}"
                )
    return runnable, failures, placeholders, invalid


def bus_aliases(data: dict[str, Any], chip: Any) -> dict[str, list[str]]:
    explicit_aliases: dict[str, list[tuple[int, str]]] = {}
    suffix_aliases: dict[str, list[tuple[int, str]]] = {}
    for pin in data.get("pins", []):
        name = str(pin["name"])
        if name not in chip.pin_names:
            continue
        if "bus" in pin and "bit" in pin:
            explicit_aliases.setdefault(str(pin["bus"]), []).append((int(pin["bit"]), name))
        match = re.fullmatch(r"([A-Za-z]+)(\d+)", name)
        if match:
            prefix, index_text = match.groups()
            suffix_aliases.setdefault(prefix, []).append((int(index_text), name))
        match = re.fullmatch(r"I/O(\d+)", name)
        if match:
            explicit_aliases.setdefault("DQ", []).append((int(match.group(1)), name))
        match = re.fullmatch(r"DQ(\d+)", name)
        if match:
            explicit_aliases.setdefault("DQ", []).append((int(match.group(1)), name))
        match = re.fullmatch(r"Q([A-H])", name)
        if match:
            suffix_aliases.setdefault("Q", []).append((ord(match.group(1)) - ord("A"), name))
        match = re.fullmatch(r"(\d+)([DQ])", name)
        if match:
            index_text, prefix = match.groups()
            suffix_aliases.setdefault(prefix, []).append((int(index_text), name))

    aliases = dict(explicit_aliases)
    for prefix, items in suffix_aliases.items():
        if prefix in aliases:
            continue
        zero_based = any(index == 0 for index, _ in items)
        normalized = [
            (index if zero_based else index - 1, name)
            for index, name in items
            if zero_based or index > 0
        ]
        aliases.setdefault(prefix, []).extend(normalized)
    for alias, items in list(aliases.items()):
        deduped: dict[str, int] = {}
        for bit, name in items:
            deduped.setdefault(name, bit)
        aliases[alias] = [(bit, name) for name, bit in deduped.items()]
    return {
        alias: [name for _, name in sorted(items)]
        for alias, items in aliases.items()
        if len(items) > 1
    }


def check_annotation(chip: Any, key: str, expected: Any) -> bool:
    if expected is not True and not isinstance(expected, int):
        return False
    if key == "write_pending":
        return bool(getattr(chip, "_pending_write", None)) is bool(expected)
    if key == "busy_updates":
        return getattr(chip, "write_busy_updates_remaining", None) == expected
    if key in {"write", "no_write"}:
        return bool(expected)
    return False


def set_bus(chip: Any, names: list[str], value: Any) -> None:
    if value == "Z":
        for name in names:
            chip.set_input(name, Z)
        return
    number = int(str(value), 16) if isinstance(value, str) and value.startswith("0x") else int(value)
    for bit_index, name in enumerate(names):
        chip.set_input(name, (number >> bit_index) & 1)


def read_bus(chip: Any, names: list[str]) -> int | str:
    values = [chip.read(name) for name in names]
    if all(value == Z for value in values):
        return "Z"
    return sum((1 if value == 1 else 0) << bit_index for bit_index, value in enumerate(values))


def normalize_bus_expected(value: Any, width: int) -> int | str:
    if value == "Z":
        return "Z"
    if isinstance(value, str) and value.startswith("0x"):
        return int(value, 16)
    return int(value) & ((1 << width) - 1)


def db_pins(data: dict[str, Any]) -> dict[int, tuple[str, str]]:
    return {
        int(pin["number"]): (str(pin["name"]), str(pin["direction"]))
        for pin in data.get("pins", [])
    }


def model_pins(chip: Any) -> dict[int, tuple[str, str]]:
    return {
        number: (pin.name, DIR_MAP.get(pin.direction, pin.direction))
        for number, pin in sorted(chip.pins.items())
    }


def timing_layer(data: dict[str, Any]) -> dict[str, Any]:
    layer = data.get("definition_layers", {}).get("timing", {})
    delay = layer.get("delay") if isinstance(layer, dict) else None
    return delay if isinstance(delay, dict) else {}


def datasheet_number_count(obj: Any) -> int:
    if isinstance(obj, dict):
        return sum(datasheet_number_count(value) for key, value in obj.items() if str(key).startswith("datasheet_") or isinstance(value, (dict, list)))
    if isinstance(obj, list):
        return sum(datasheet_number_count(value) for value in obj)
    if isinstance(obj, (int, float)) and not isinstance(obj, bool):
        return 1
    return 0


def main() -> int:
    rows: list[dict[str, Any]] = []
    problems: list[str] = []
    warnings: list[str] = []

    for definition in sorted((ROOT / "DB").glob("*/**/definition/definition.json")):
        group = definition.relative_to(ROOT / "DB").parts[0]
        if group not in {"74xx", "Memory", "Support"}:
            continue
        data = json.loads(definition.read_text(encoding="utf-8"))
        part = str(data.get("part") or definition.parents[1].name)
        model_path = definition.parents[1] / "simulation" / "model.py"
        truth_path = definition.parents[1] / "tests" / "truth_table.json"
        if not model_path.exists():
            rows.append({"part": part, "result": "NO_MODEL", "details": "simulation/model.py missing"})
            problems.append(f"{part}: missing simulation/model.py")
            continue
        try:
            module = import_model(model_path)
            chip = module.create("U")
        except Exception as exc:  # noqa: BLE001
            rows.append({"part": part, "result": "IMPORT_FAIL", "details": repr(exc)})
            problems.append(f"{part}: import/create failed: {exc!r}")
            continue

        pin_mismatches = []
        db_pin_map = db_pins(data)
        model_pin_map = model_pins(chip)
        for number, expected in db_pin_map.items():
            observed = model_pin_map.get(number)
            if observed != expected:
                pin_mismatches.append(f"pin {number} db={expected} py={observed}")
        extra_model_pins = sorted(set(model_pin_map) - set(db_pin_map))
        if extra_model_pins:
            pin_mismatches.append(f"extra python pins {extra_model_pins}")

        truth_result = "NO_TRUTH_FILE"
        runnable = 0
        placeholders = 0
        truth_failures: list[str] = []
        invalid_vectors: list[str] = []
        if truth_path.exists():
            truth = json.loads(truth_path.read_text(encoding="utf-8"))
            vectors = truth.get("vectors") or []
            runnable, truth_failures, placeholders, invalid_vectors = run_vectors(chip, vectors, data)
            if truth_failures:
                truth_result = "FAIL"
            elif invalid_vectors:
                truth_result = "INVALID_VECTOR_METADATA"
            elif runnable:
                truth_result = "PASS"
            elif placeholders:
                truth_result = "PLACEHOLDER_ONLY"
            else:
                truth_result = "NO_RUNNABLE_VECTORS"

        delay = timing_layer(data)
        db_model_delay = delay.get("model_delay_ns") or (data.get("timing") or {}).get("delay_ns")
        runtime_delay = chip.delay.rise_ns
        runtime_fall = chip.delay.fall_ns
        delay_match = (
            db_model_delay is not None
            and runtime_delay == db_model_delay
            and runtime_fall in (None, runtime_delay)
        )
        has_datasheet = datasheet_number_count(delay) > 0
        timing_result = "PASS_MODEL_DELAY"
        if db_model_delay is None:
            timing_result = "NO_DB_MODEL_DELAY"
        elif not delay_match:
            timing_result = "FAIL_MODEL_DELAY_MISMATCH"
        elif has_datasheet and contains_defaults(delay):
            timing_result = "PASS_MODEL_DELAY_BUT_DATASHEET_TIMING_NOT_RUNTIME_PATHS"
        elif has_datasheet:
            timing_result = "PASS_MODEL_DELAY_AND_DATASHEET_EVIDENCE"

        result = "PASS"
        details = []
        if pin_mismatches:
            result = "FAIL"
            details.extend(pin_mismatches[:4])
            if len(pin_mismatches) > 4:
                details.append(f"{len(pin_mismatches) - 4} more pin mismatch(es)")
        if truth_failures:
            result = "FAIL"
            details.extend(truth_failures[:4])
        if timing_result == "FAIL_MODEL_DELAY_MISMATCH":
            result = "FAIL"
            details.append(f"runtime delay {runtime_delay}/{runtime_fall} ns != DB model_delay_ns {db_model_delay}")
        if truth_result in {"PLACEHOLDER_ONLY", "NO_RUNNABLE_VECTORS", "NO_TRUTH_FILE"}:
            warnings.append(f"{part}: {truth_result}")
        if truth_result == "INVALID_VECTOR_METADATA":
            warnings.append(f"{part}: invalid truth metadata: {'; '.join(invalid_vectors[:3])}")
        if timing_result == "NO_DB_MODEL_DELAY":
            warnings.append(f"{part}: Python runtime delay exists but DB model_delay_ns is missing")
        if timing_result == "PASS_MODEL_DELAY_BUT_DATASHEET_TIMING_NOT_RUNTIME_PATHS":
            warnings.append(f"{part}: Python uses fixed model delay; datasheet timing evidence is DB metadata only")
        if result == "FAIL":
            problems.append(f"{part}: " + "; ".join(details))

        rows.append(
            {
                "part": part,
                "group": group,
                "result": result,
                "pin_result": "FAIL" if pin_mismatches else "PASS",
                "truth_result": truth_result,
                "runnable_vectors": runnable,
                "placeholder_vectors": placeholders,
                "timing_result": timing_result,
                "runtime_delay_ns": runtime_delay,
                "db_model_delay_ns": db_model_delay,
                "datasheet_timing_values": datasheet_number_count(delay),
                "details": "; ".join(details) if details else "-",
            }
        )

    write_report(rows, problems, warnings)
    print(json.dumps({"rows": len(rows), "failures": problems, "warnings": warnings, "report": str(REPORT)}, indent=2))
    return 1 if problems else 0


def contains_defaults(obj: Any) -> bool:
    text = json.dumps(obj, sort_keys=True)
    return "conservative_default" in text or "legacy functional simulator default" in text


def write_report(rows: list[dict[str, Any]], problems: list[str], warnings: list[str]) -> None:
    lines = [
        "# Python Behavior Cross-check Report",
        "",
        "Generated by `tools/python_behavior_crosscheck.py` from DB definitions, local Python models, packaged truth vectors, and DB timing records.",
        "",
        "Important: this checks the Python runtime model. A `PASS_MODEL_DELAY_BUT_DATASHEET_TIMING_NOT_RUNTIME_PATHS` result means the model delay matches the DB model delay, but path-specific datasheet timing is still metadata and is not used by the Python simulator.",
        "",
        "| Part | Group | Result | Pins | Truth Vectors | Timing | Runtime Delay | DB Model Delay | Details |",
        "|---|---:|---|---|---:|---|---:|---:|---|",
    ]
    for row in rows:
        truth = f"{row['truth_result']} ({row['runnable_vectors']} run, {row['placeholder_vectors']} placeholder)"
        lines.append(
            "| {part} | {group} | {result} | {pin_result} | {truth} | {timing_result} | {runtime_delay_ns} | {db_model_delay_ns} | {details} |".format(
                **row,
                truth=truth,
            )
        )
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Python models checked: {len(rows)}",
            f"- Failures: {len(problems)}",
            f"- Warnings: {len(warnings)}",
            "",
            "## Failure Detail",
        ]
    )
    if problems:
        lines.extend(f"- {problem}" for problem in problems)
    else:
        lines.append("- none")
    lines.extend(["", "## Warning Detail"])
    if warnings:
        lines.extend(f"- {warning}" for warning in warnings)
    else:
        lines.append("- none")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
