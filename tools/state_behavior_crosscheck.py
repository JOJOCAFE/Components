#!/usr/bin/env python3
"""Deep checks for stateful Python chip models.

The generic behavior checker proves recorded vectors. This tool adds explicit
contracts for state machines: clocked hold, async/sync clear and load, output
enable, count direction, shift direction, and carry/terminal behavior.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "STATE_BEHAVIOR_CROSSCHECK_REPORT.md"
sys.path.insert(0, str(ROOT / "python"))

from chiplib import Z, create_chip  # noqa: E402


Check = Callable[[], list[str]]


def eval_chip(chip: Any) -> None:
    chip.update()
    chip.commit()


def has(chip: Any, name: str) -> bool:
    return name in chip.pin_names


def set_pin(chip: Any, *names: str, value: int | str) -> None:
    for name in names:
        if has(chip, name):
            chip.set_input(name, value)
            return
    raise AssertionError(f"{chip.part}: none of pins exist: {names}")


def read_pin(chip: Any, *names: str) -> int | str:
    for name in names:
        if has(chip, name):
            return chip.read(name)
    raise AssertionError(f"{chip.part}: none of pins exist: {names}")


def set_bus(chip: Any, names: list[str], value: int) -> None:
    for index, name in enumerate(names):
        chip.set_input(name, (value >> index) & 1)


def read_bus(chip: Any, names: list[str]) -> int | str:
    values = [chip.read(name) for name in names]
    if all(value == Z for value in values):
        return "Z"
    return sum((1 if value == 1 else 0) << index for index, value in enumerate(values))


def expect(errors: list[str], label: str, got: Any, want: Any) -> None:
    if got != want:
        errors.append(f"{label}: expected {want!r}, got {got!r}")


def edge(chip: Any, pin: str | None = None) -> None:
    chip.clock_edge(pin)
    chip.commit()
    eval_chip(chip)


def check_74hc74() -> list[str]:
    c = create_chip("74HC74", "U")
    errors: list[str] = []
    set_pin(c, "/1CLR", "/CLR1", value=1)
    set_pin(c, "/1PRE", "/PR1", value=1)
    set_pin(c, "1D", "D1", value=1)
    edge(c, "1CLK" if has(c, "1CLK") else "CLK1")
    expect(errors, "74HC74 captures D on clock", read_pin(c, "1Q", "Q1"), 1)
    set_pin(c, "1D", "D1", value=0)
    eval_chip(c)
    expect(errors, "74HC74 holds when D changes without clock", read_pin(c, "1Q", "Q1"), 1)
    set_pin(c, "/1CLR", "/CLR1", value=0)
    eval_chip(c)
    expect(errors, "74HC74 async clear forces Q low", read_pin(c, "1Q", "Q1"), 0)
    expect(errors, "74HC74 async clear forces /Q high", read_pin(c, "/1Q", "/Q1"), 1)
    set_pin(c, "/1CLR", "/CLR1", value=1)
    set_pin(c, "/1PRE", "/PR1", value=0)
    eval_chip(c)
    expect(errors, "74HC74 async preset forces Q high", read_pin(c, "1Q", "Q1"), 1)
    expect(errors, "74HC74 async preset forces /Q low", read_pin(c, "/1Q", "/Q1"), 0)
    return errors


def counter_names(part: str, chip: Any) -> tuple[list[str], list[str], str, str, str, str | None, int]:
    if part == "74HC161":
        return ["D0", "D1", "D2", "D3"], ["QA", "QB", "QC", "QD"], "/CLR", "/LD", "ENP", "ENT", 15
    terminal = 9 if part in {"74HC160", "74HC162"} else 15
    return ["D0", "D1", "D2", "D3"], ["Q0", "Q1", "Q2", "Q3"], "MR", "PE", "CEP", "CET", terminal


def check_sync_counter(part: str) -> list[str]:
    c = create_chip(part, "U")
    errors: list[str] = []
    d, q, clear, load, en1, en2, terminal = counter_names(part, c)
    clear_inactive = 1
    load_inactive = 1
    set_pin(c, clear, value=clear_inactive)
    set_pin(c, load, value=load_inactive)
    set_pin(c, en1, value=1)
    set_pin(c, en2, value=1)
    edge(c)
    expect(errors, f"{part} increments when enabled", read_bus(c, q), 1)
    set_pin(c, en1, value=0)
    edge(c)
    expect(errors, f"{part} holds when first enable is low", read_bus(c, q), 1)
    set_pin(c, en1, value=1)
    set_bus(c, d, 5)
    set_pin(c, load, value=0)
    edge(c)
    expect(errors, f"{part} parallel load on clock", read_bus(c, q), 5)
    set_pin(c, load, value=1)
    set_pin(c, clear, value=0)
    eval_chip(c)
    if part in {"74HC160", "74HC161"}:
        expect(errors, f"{part} clear visible without waiting for clock", read_bus(c, q), 0)
    edge(c)
    expect(errors, f"{part} clear path resets count", read_bus(c, q), 0)
    set_pin(c, clear, value=1)
    set_bus(c, d, terminal)
    set_pin(c, load, value=0)
    edge(c)
    set_pin(c, load, value=1)
    tc_name = "RCO" if has(c, "RCO") else "TC"
    expect(errors, f"{part} terminal carry asserted at terminal count", read_pin(c, tc_name), 1)
    edge(c)
    expected_next = 0 if part in {"74HC160", "74HC162"} else 0
    expect(errors, f"{part} wraps after terminal count", read_bus(c, q), expected_next)
    return errors


def check_74hc164() -> list[str]:
    c = create_chip("74HC164", "U")
    errors: list[str] = []
    q = ["Q0", "Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7"]
    set_pin(c, "/CLR", value=1)
    set_pin(c, "A", value=1)
    set_pin(c, "B", value=1)
    edge(c, "CLK")
    expect(errors, "74HC164 shifts A&B high into Q0", read_bus(c, q), 1)
    set_pin(c, "B", value=0)
    edge(c, "CLK")
    expect(errors, "74HC164 serial input is A AND B", read_bus(c, q), 2)
    set_pin(c, "/CLR", value=0)
    eval_chip(c)
    expect(errors, "74HC164 async clear resets outputs", read_bus(c, q), 0)
    return errors


def check_74hc165() -> list[str]:
    c = create_chip("74HC165", "U")
    errors: list[str] = []
    set_bus(c, ["A", "B", "C", "D", "E", "F", "G", "H"], 0x80)
    set_pin(c, "/SH/LD", value=0)
    eval_chip(c)
    expect(errors, "74HC165 parallel load exposes H at QH", read_pin(c, "QH"), 1)
    expect(errors, "74HC165 /QH complements QH", read_pin(c, "/QH"), 0)
    set_pin(c, "/SH/LD", value=1)
    set_pin(c, "CLK INH", value=1)
    set_pin(c, "SER", value=0)
    edge(c, "CLK")
    expect(errors, "74HC165 clock inhibit holds state", read_pin(c, "QH"), 1)
    set_pin(c, "CLK INH", value=0)
    edge(c, "CLK")
    expect(errors, "74HC165 shift advances toward QH", read_pin(c, "QH"), 0)
    return errors


def check_74hc166() -> list[str]:
    c = create_chip("74HC166", "U")
    errors: list[str] = []
    set_pin(c, "/CLR", value=1)
    set_bus(c, ["A", "B", "C", "D", "E", "F", "G", "H"], 0x80)
    set_pin(c, "/SH/LD", value=0)
    edge(c, "CLK")
    expect(errors, "74HC166 parallel load exposes H at QH", read_pin(c, "QH"), 1)
    set_pin(c, "/SH/LD", value=1)
    set_pin(c, "CLK INH", value=1)
    set_pin(c, "SER", value=0)
    edge(c, "CLK")
    expect(errors, "74HC166 clock inhibit holds state", read_pin(c, "QH"), 1)
    set_pin(c, "CLK INH", value=0)
    edge(c, "CLK")
    expect(errors, "74HC166 shift advances toward QH", read_pin(c, "QH"), 0)
    set_pin(c, "/CLR", value=0)
    eval_chip(c)
    expect(errors, "74HC166 async clear resets QH", read_pin(c, "QH"), 0)
    return errors


def check_74hc193() -> list[str]:
    c = create_chip("74HC193", "U")
    errors: list[str] = []
    q = ["QA", "QB", "QC", "QD"]
    set_pin(c, "CLR", value=0)
    set_pin(c, "/LOAD", value=1)
    set_pin(c, "UP", value=1)
    set_pin(c, "DOWN", value=1)
    set_bus(c, ["A", "B", "C", "D"], 3)
    set_pin(c, "/LOAD", value=0)
    eval_chip(c)
    expect(errors, "74HC193 parallel load visible while /LOAD low", read_bus(c, q), 3)
    set_pin(c, "/LOAD", value=1)
    edge(c, "UP")
    expect(errors, "74HC193 UP clock increments when DOWN high", read_bus(c, q), 4)
    edge(c, "DOWN")
    expect(errors, "74HC193 DOWN clock decrements when UP high", read_bus(c, q), 3)
    set_pin(c, "CLR", value=1)
    eval_chip(c)
    expect(errors, "74HC193 clear resets count", read_bus(c, q), 0)
    expect(errors, "74HC193 borrow output active at zero", read_pin(c, "/BO"), 0)
    return errors


def check_74hc273() -> list[str]:
    c = create_chip("74HC273", "U")
    errors: list[str] = []
    d = [f"{i}D" for i in range(1, 9)]
    q = [f"{i}Q" for i in range(1, 9)]
    set_pin(c, "/CLR", value=1)
    set_bus(c, d, 0xA5)
    edge(c, "CLK")
    expect(errors, "74HC273 latches D on clock", read_bus(c, q), 0xA5)
    set_bus(c, d, 0x00)
    eval_chip(c)
    expect(errors, "74HC273 holds without clock", read_bus(c, q), 0xA5)
    set_pin(c, "/CLR", value=0)
    eval_chip(c)
    expect(errors, "74HC273 async clear resets outputs", read_bus(c, q), 0)
    return errors


def check_74hc374_like(part: str) -> list[str]:
    c = create_chip(part, "U")
    errors: list[str] = []
    if part == "74HC377":
        d = [f"D{i}" for i in range(8)]
        q = [f"Q{i}" for i in range(8)]
        set_pin(c, "E", value=0)
        set_bus(c, d, 0x5A)
        edge(c, "CLK" if has(c, "CLK") else "CP")
        expect(errors, "74HC377 latches when enable low", read_bus(c, q), 0x5A)
        set_pin(c, "E", value=1)
        set_bus(c, d, 0x00)
        edge(c, "CLK" if has(c, "CLK") else "CP")
        expect(errors, "74HC377 holds when enable high", read_bus(c, q), 0x5A)
        return errors

    d = [f"{i}D" for i in range(1, 9)] if has(c, "1D") else [f"D{i}" for i in range(1, 9)]
    if has(c, "1Q"):
        q = [f"{i}Q" for i in range(1, 9)]
    elif has(c, "Q1"):
        q = [f"Q{i}" for i in range(1, 9)]
    else:
        raise AssertionError(f"{part}: no known output bus naming")
    set_bus(c, d, 0x3C)
    if has(c, "/OE"):
        set_pin(c, "/OE", value=0)
    edge(c, "CLK")
    expect(errors, f"{part} latches D on clock", read_bus(c, q), 0x3C)
    set_bus(c, d, 0x00)
    eval_chip(c)
    expect(errors, f"{part} holds without clock", read_bus(c, q), 0x3C)
    if has(c, "/OE"):
        set_pin(c, "/OE", value=1)
        eval_chip(c)
        expect(errors, f"{part} active-low OE disables outputs", read_bus(c, q), "Z")
    return errors


def check_74hc595() -> list[str]:
    c = create_chip("74HC595", "U")
    errors: list[str] = []
    q = ["QA", "QB", "QC", "QD", "QE", "QF", "QG", "QH"]
    set_pin(c, "/SRCLR", value=1)
    set_pin(c, "/OE", value=0)
    for bit_value in [1, 0, 1, 0, 0, 1, 0, 1]:
        set_pin(c, "SER", value=bit_value)
        edge(c, "SRCLK")
    eval_chip(c)
    expect(errors, "74HC595 storage register holds before RCLK", read_bus(c, q), 0)
    edge(c, "RCLK")
    expect(errors, "74HC595 RCLK copies shift register to outputs", read_bus(c, q), 0xA5)
    set_pin(c, "/OE", value=1)
    eval_chip(c)
    expect(errors, "74HC595 active-low OE disables outputs", read_bus(c, q), "Z")
    set_pin(c, "/SRCLR", value=0)
    edge(c, "SRCLK")
    set_pin(c, "/OE", value=0)
    edge(c, "RCLK")
    expect(errors, "74HC595 shift-register clear resets latched outputs after RCLK", read_bus(c, q), 0)
    return errors


def check_74hc593() -> list[str]:
    c = create_chip("74HC593", "U")
    errors: list[str] = []
    q = ["A/QA", "B/QB", "C/QC", "D/QD", "E/QE", "F/QF", "G/QG", "H/QH"]
    set_pin(c, "CCLR", value=1)
    set_pin(c, "CLOAD", value=1)
    set_pin(c, "CCKEN", value=1)
    if has(c, "/CCKEN"):
        set_pin(c, "/CCKEN", value=0)
    set_pin(c, "G", value=1)
    if has(c, "/G"):
        set_pin(c, "/G", value=0)
    edge(c, "CCK")
    expect(errors, "74HC593 counter increments on CCK", read_bus(c, q), 1)
    set_pin(c, "CCLR", value=0)
    eval_chip(c)
    expect(errors, "74HC593 counter clear resets outputs", read_bus(c, q), 0)
    return errors


def check_74hc4520() -> list[str]:
    c = create_chip("74HC4520", "U")
    errors: list[str] = []
    q1 = ["1Q0", "1Q1", "1Q2", "1Q3"]
    q2 = ["2Q0", "2Q1", "2Q2", "2Q3"]
    set_pin(c, "1MR", value=0)
    set_pin(c, "2MR", value=0)
    set_pin(c, "1E", value=1)
    set_pin(c, "2E", value=1)
    eval_chip(c)
    expect(errors, "74HC4520 block 1 starts reset", read_bus(c, q1), 0)
    expect(errors, "74HC4520 block 2 starts reset", read_bus(c, q2), 0)
    edge(c, "1CP")
    edge(c, "1CP")
    expect(errors, "74HC4520 block 1 counts up on enabled clock", read_bus(c, q1), 2)
    expect(errors, "74HC4520 block 1 clock leaves block 2 unchanged", read_bus(c, q2), 0)
    set_pin(c, "1E", value=0)
    edge(c, "1CP")
    expect(errors, "74HC4520 block 1 holds when enable is low", read_bus(c, q1), 2)
    set_pin(c, "1E", value=1)
    set_pin(c, "1MR", value=1)
    eval_chip(c)
    expect(errors, "74HC4520 block 1 async reset clears count", read_bus(c, q1), 0)
    set_pin(c, "1MR", value=0)
    for _ in range(16):
        edge(c, "2CP")
    expect(errors, "74HC4520 block 2 wraps after 16 counts", read_bus(c, q2), 0)
    edge(c, "2CP")
    expect(errors, "74HC4520 block 2 resumes count after wrap", read_bus(c, q2), 1)
    return errors


def check_74hc4538() -> list[str]:
    c = create_chip("74HC4538", "U")
    errors: list[str] = []
    set_pin(c, "/1R", value=1)
    set_pin(c, "/2R", value=1)
    eval_chip(c)
    expect(errors, "74HC4538 block 1 idle Q low", read_pin(c, "1Q"), 0)
    expect(errors, "74HC4538 block 1 idle /Q high", read_pin(c, "/1Q"), 1)
    edge(c, "1A")
    expect(errors, "74HC4538 block 1 trigger sets Q high", read_pin(c, "1Q"), 1)
    expect(errors, "74HC4538 block 1 trigger sets /Q low", read_pin(c, "/1Q"), 0)
    set_pin(c, "1B", value=1)
    eval_chip(c)
    expect(errors, "74HC4538 block 1 holds without a trigger edge", read_pin(c, "1Q"), 1)
    set_pin(c, "/1R", value=0)
    eval_chip(c)
    expect(errors, "74HC4538 block 1 reset clears Q", read_pin(c, "1Q"), 0)
    expect(errors, "74HC4538 block 1 reset drives /Q high", read_pin(c, "/1Q"), 1)
    edge(c, "2B")
    expect(errors, "74HC4538 block 2 trigger sets Q high", read_pin(c, "2Q"), 1)
    expect(errors, "74HC4538 block 2 trigger sets /Q low", read_pin(c, "/2Q"), 0)
    set_pin(c, "/2R", value=0)
    eval_chip(c)
    expect(errors, "74HC4538 block 2 reset clears Q", read_pin(c, "2Q"), 0)
    return errors


def check_74hc922() -> list[str]:
    c = create_chip("74HC922", "U")
    errors: list[str] = []
    columns = ["COLUMN X1", "COLUMN X2", "COLUMN X3", "COLUMN X4"]
    data = ["DATA OUT A", "DATA OUT B", "DATA OUT C", "DATA OUT D"]
    for row in range(1, 5):
        set_pin(c, f"ROW Y{row}", value=1)
    set_pin(c, "KEYBOUNCE MASK", value=1)
    set_pin(c, "OUTPUT ENABLE", value=0)
    eval_chip(c)
    expect(errors, "74HC922 initial scan drives column X1 low", read_bus(c, columns), 0xE)
    edge(c, "OSCILLATOR")
    expect(errors, "74HC922 oscillator advances scan to column X2", read_bus(c, columns), 0xD)
    eval_chip(c)
    expect(errors, "74HC922 holds scan column without oscillator edge", read_bus(c, columns), 0xD)
    edge(c, "OSCILLATOR")
    expect(errors, "74HC922 oscillator advances scan to column X3", read_bus(c, columns), 0xB)
    set_pin(c, "ROW Y3", value=0)
    eval_chip(c)
    expect(errors, "74HC922 reports row/column key code", read_bus(c, data), 0xA)
    expect(errors, "74HC922 asserts DATA AVAILABLE when keybounce mask is high", read_pin(c, "DATA AVAILABLE"), 1)
    set_pin(c, "KEYBOUNCE MASK", value=0)
    eval_chip(c)
    expect(errors, "74HC922 keybounce mask gates DATA AVAILABLE", read_pin(c, "DATA AVAILABLE"), 0)
    set_pin(c, "OUTPUT ENABLE", value=1)
    eval_chip(c)
    expect(errors, "74HC922 output enable disables data outputs", read_bus(c, data), "Z")
    return errors


CHECKS: dict[str, Check] = {
    "74HC74": check_74hc74,
    "74HC160": lambda: check_sync_counter("74HC160"),
    "74HC161": lambda: check_sync_counter("74HC161"),
    "74HC162": lambda: check_sync_counter("74HC162"),
    "74HC163": lambda: check_sync_counter("74HC163"),
    "74HC164": check_74hc164,
    "74HC165": check_74hc165,
    "74HC166": check_74hc166,
    "74HC193": check_74hc193,
    "74HC273": check_74hc273,
    "74HC374": lambda: check_74hc374_like("74HC374"),
    "74HC377": lambda: check_74hc374_like("74HC377"),
    "74HC4520": check_74hc4520,
    "74HC4538": check_74hc4538,
    "74HC574": lambda: check_74hc374_like("74HC574"),
    "74HCT574": lambda: check_74hc374_like("74HCT574"),
    "74HC593": check_74hc593,
    "74HC595": check_74hc595,
    "74HC922": check_74hc922,
}


def main() -> int:
    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    for part, check in sorted(CHECKS.items()):
        try:
            errors = check()
        except Exception as exc:  # noqa: BLE001
            errors = [f"checker exception: {exc!r}"]
        result = "PASS" if not errors else "FAIL"
        failures.extend(f"{part}: {error}" for error in errors)
        rows.append({"part": part, "result": result, "checks": len(errors) if errors else "all", "details": "; ".join(errors) if errors else "-"})

    write_report(rows, failures)
    print(json.dumps({"rows": len(rows), "failures": failures, "report": str(REPORT)}, indent=2))
    return 1 if failures else 0


def write_report(rows: list[dict[str, Any]], failures: list[str]) -> None:
    lines = [
        "# Stateful Chip Behavior Cross-check Report",
        "",
        "Generated by `tools/state_behavior_crosscheck.py` against the live Python `create_chip()` behavior path.",
        "",
        "This is a deep state-machine check for flip-flops, registers, counters, and shift registers. It complements the generic DB vector, pinout, timing, and polarity cross-checks.",
        "",
        "| Part | Result | Detail |",
        "|---|---|---|",
    ]
    for row in rows:
        lines.append(f"| {row['part']} | {row['result']} | {row['details']} |")
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Stateful parts checked: {len(rows)}",
            f"- Failures: {len(failures)}",
            "",
            "## Failure Detail",
        ]
    )
    if failures:
        lines.extend(f"- {failure}" for failure in failures)
    else:
        lines.append("- none")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
