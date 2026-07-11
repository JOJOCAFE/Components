#!/usr/bin/env python3
"""Cross-check selected Python chip behavior against downloaded vendor models.

This tool intentionally separates a true vendor simulation model from a
datasheet/product-page behavior source. A product page is reliable evidence,
but it is not an executable simulator.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Source" / "ExternalModels"
REPORT = ROOT / "EXTERNAL_MODEL_CROSSCHECK_REPORT.md"
sys.path.insert(0, str(ROOT / "python"))

from chiplib import Z, create_chip  # noqa: E402


@dataclass(frozen=True)
class ExternalPart:
    part: str
    product_page: Path
    product_url: str
    model_path: Path | None = None
    model_url: str | None = None
    extra_model_paths: tuple[Path, ...] = ()
    local_vectors: bool = True
    expected_terms: tuple[str, ...] = ()


PARTS = (
    ExternalPart(
        part="74HC00",
        product_page=SOURCE / "SN74HC00_TI_product.html",
        product_url="https://www.ti.com/product/SN74HC00",
        model_path=SOURCE / "SN74HC00_TI_SCLM235" / "SN74HC00.cir",
        model_url="https://www.ti.com/lit/zip/sclm235",
        expected_terms=("NAND", "SN74HC00"),
    ),
    ExternalPart(
        part="74HC245",
        product_page=SOURCE / "SN74HC245_TI_product.html",
        product_url="https://www.ti.com/product/SN74HC245",
        expected_terms=("Octal Bus Transceivers", "3-State", "DIR"),
    ),
    ExternalPart(
        part="74HC595",
        product_page=SOURCE / "SN74HC595_TI_product.html",
        product_url="https://www.ti.com/product/SN74HC595",
        expected_terms=("shift registers", "3-state output registers"),
    ),
    ExternalPart(
        part="74HC161",
        product_page=SOURCE / "SN74HC161_TI_product.html",
        product_url="https://www.ti.com/product/SN74HC161",
        expected_terms=("4-Bit Synchronous Binary Counters", "ACTIVE"),
    ),
    ExternalPart(
        part="74HC574",
        product_page=SOURCE / "SN74HC574_TI_product.html",
        product_url="https://www.ti.com/product/SN74HC574",
        expected_terms=("Octal Edge-Triggered D-Type Flip-Flops", "3-State Outputs"),
    ),
    ExternalPart(
        part="74HC165",
        product_page=SOURCE / "SN74HC165_TI_product.html",
        product_url="https://www.ti.com/product/SN74HC165",
        expected_terms=("8-Bit Parallel-Load Shift Registers", "ACTIVE"),
    ),
    ExternalPart(
        part="74HC166",
        product_page=SOURCE / "SN74HC166_TI_product.html",
        product_url="https://www.ti.com/product/SN74HC166",
        expected_terms=("8-Bit Parallel-Load Shift Registers", "ACTIVE"),
    ),
    ExternalPart(
        part="NE555",
        product_page=SOURCE / "NE555_TI_product.html",
        product_url="https://www.ti.com/product/NE555",
        local_vectors=False,
        expected_terms=("Single Precision Timer", "PSPICE-FOR-TI"),
    ),
    ExternalPart(
        part="MAX232",
        product_page=SOURCE / "MAX232_TI_product.html",
        product_url="https://www.ti.com/product/MAX232",
        local_vectors=False,
        expected_terms=("RS-232 line driver/receiver", "ACTIVE"),
    ),
    ExternalPart(
        part="LM358",
        product_page=SOURCE / "LM358_TI_product.html",
        product_url="https://www.ti.com/product/LM358",
        model_path=SOURCE / "LM358_TI_SNOM268" / "lmx58_lm2904.lib",
        model_url="https://www.ti.com/lit/zip/snom268",
        extra_model_paths=(
            SOURCE / "LM358_TI_SNOM670" / "LMx58_LM2904.TSM",
            SOURCE / "LM358_TI_SNOM671" / "LMx58_LM2904_RefDesign.TSC",
        ),
        local_vectors=False,
        expected_terms=("Dual, 30-V, 700-kHz operational amplifier",),
    ),
    ExternalPart(
        part="LM393",
        product_page=SOURCE / "LM393_TI_product.html",
        product_url="https://www.ti.com/product/LM393",
        model_path=SOURCE / "LM393_TI_SLCJ016" / "lm393.lib",
        model_url="https://www.ti.com/lit/zip/slcj016",
        extra_model_paths=(SOURCE / "LM393_TI_SLCM004" / "TINA" / "Macro" / "LM393.TSM",),
        local_vectors=False,
        expected_terms=("Dual differential comparator",),
    ),
)


def eval_chip(chip: Any) -> None:
    chip.update()
    chip.commit()


def set_byte(chip: Any, pins: list[str], value: int) -> None:
    for index, pin in enumerate(pins):
        chip.set_input(pin, (value >> index) & 1)


def read_byte(chip: Any, pins: list[str]) -> int | str:
    values = [chip.read(pin) for pin in pins]
    if all(value == Z for value in values):
        return "Z"
    return sum((1 if value == 1 else 0) << index for index, value in enumerate(values))


def run_python_vectors(part: str) -> tuple[bool, str]:
    if part == "74HC00":
        chip = create_chip(part, "U")
        for a, b, y in ((0, 0, 1), (0, 1, 1), (1, 0, 1), (1, 1, 0)):
            chip.set_input("1A", a)
            chip.set_input("1B", b)
            eval_chip(chip)
            if chip.read("1Y") != y:
                return False, f"1Y expected {y} for A={a} B={b}, got {chip.read('1Y')!r}"
        return True, "quad NAND truth vectors pass"

    if part == "74HC245":
        chip = create_chip(part, "U")
        a_pins = [f"A{i}" for i in range(1, 9)]
        b_pins = [f"B{i}" for i in range(1, 9)]
        set_byte(chip, a_pins, 0xA5)
        chip.set_input("DIR", 1)
        chip.set_input("/OE", 0)
        eval_chip(chip)
        if read_byte(chip, b_pins) != 0xA5 or read_byte(chip, a_pins) != "Z":
            return False, "DIR=1 did not drive A to B with A side high-Z"
        chip = create_chip(part, "U")
        set_byte(chip, b_pins, 0x3C)
        chip.set_input("DIR", 0)
        chip.set_input("/OE", 0)
        eval_chip(chip)
        if read_byte(chip, a_pins) != 0x3C or read_byte(chip, b_pins) != "Z":
            return False, "DIR=0 did not drive B to A with B side high-Z"
        chip.set_input("/OE", 1)
        eval_chip(chip)
        if read_byte(chip, a_pins) != "Z" or read_byte(chip, b_pins) != "Z":
            return False, "/OE=1 did not put both buses high-Z"
        return True, "DIR and active-low OE tri-state vectors pass"

    if part == "74HC595":
        chip = create_chip(part, "U")
        chip.set_input("SER", 1)
        chip.set_input("/SRCLR", 1)
        chip.set_input("/OE", 0)
        for _ in range(8):
            chip.clock_edge("SRCLK")
            chip.commit()
        chip.clock_edge("RCLK")
        chip.commit()
        eval_chip(chip)
        q_pins = [f"Q{letter}" for letter in "ABCDEFGH"]
        if read_byte(chip, q_pins) != 0xFF:
            return False, "serial shift/register latch did not produce 0xFF"
        chip.set_input("/OE", 1)
        eval_chip(chip)
        if read_byte(chip, q_pins) != "Z":
            return False, "/OE=1 did not put QA-QH high-Z"
        return True, "serial shift, storage latch, and active-low OE vectors pass"

    if part == "74HC161":
        chip = create_chip(part, "U")
        set_byte(chip, ["D0", "D1", "D2", "D3"], 0xC)
        for pin, value in (("/CLR", 1), ("/LD", 0), ("ENT", 1), ("ENP", 1)):
            chip.set_input(pin, value)
        chip.clock_edge()
        chip.commit()
        if read_byte(chip, ["QA", "QB", "QC", "QD"]) != 0xC:
            return False, "parallel load did not latch 0xC"
        chip.set_input("/LD", 1)
        chip.clock_edge()
        chip.commit()
        if read_byte(chip, ["QA", "QB", "QC", "QD"]) != 0xD:
            return False, "enabled count did not increment 0xC to 0xD"
        chip.set_input("/CLR", 0)
        eval_chip(chip)
        if read_byte(chip, ["QA", "QB", "QC", "QD"]) != 0:
            return False, "active-low MR did not clear counter"
        return True, "parallel load, count, and active-low reset vectors pass"

    if part == "74HC574":
        chip = create_chip(part, "U")
        chip.set_input("/OE", 0)
        d_pins = [f"D{i}" for i in range(1, 9)]
        q_pins = [f"Q{i}" for i in range(1, 9)]
        set_byte(chip, d_pins, 0xA5)
        chip.clock_edge()
        chip.commit()
        if read_byte(chip, q_pins) != 0xA5:
            return False, "rising edge did not latch 0xA5"
        set_byte(chip, d_pins, 0x00)
        eval_chip(chip)
        if read_byte(chip, q_pins) != 0xA5:
            return False, "outputs changed without clock edge"
        chip.set_input("/OE", 1)
        eval_chip(chip)
        if read_byte(chip, q_pins) != "Z":
            return False, "active-low OE high did not put outputs high-Z"
        return True, "edge latch, hold, and active-low OE vectors pass"

    if part == "74HC165":
        chip = create_chip(part, "U")
        for pin, value in {
            "/SH/LD": 0,
            "CLK INH": 0,
            "SER": 0,
            "A": 1,
            "B": 0,
            "C": 1,
            "D": 0,
            "E": 1,
            "F": 0,
            "G": 1,
            "H": 1,
        }.items():
            chip.set_input(pin, value)
        eval_chip(chip)
        if chip.read("QH") != 1 or chip.read("/QH") != 0:
            return False, "parallel load did not expose H on QH and /QH"
        chip.set_input("/SH/LD", 1)
        chip.set_input("SER", 0)
        chip.clock_edge("CLK")
        chip.commit()
        if chip.read("QH") not in (0, 1) or chip.read("/QH") != 1 - chip.read("QH"):
            return False, "clocked shift did not keep complementary QH outputs"
        return True, "parallel-load and complementary serial-output vectors pass"

    if part == "74HC166":
        chip = create_chip(part, "U")
        for pin, value in {
            "/CLR": 1,
            "/SH/LD": 0,
            "CLK INH": 0,
            "SER": 0,
            "A": 0,
            "B": 1,
            "C": 0,
            "D": 1,
            "E": 0,
            "F": 1,
            "G": 0,
            "H": 1,
        }.items():
            chip.set_input(pin, value)
        chip.clock_edge("CLK")
        chip.commit()
        if chip.read("QH") != 1:
            return False, "parallel load did not expose H on QH"
        chip.set_input("/CLR", 0)
        eval_chip(chip)
        if chip.read("QH") != 0:
            return False, "active-low clear did not clear QH"
        return True, "parallel-load and active-low clear vectors pass"

    return False, "no local vector set"


def python_vector_status(part: ExternalPart) -> tuple[str, str, bool]:
    if not part.local_vectors:
        return "not_applicable", "support/analog package has no local digital runtime model", True
    ok, detail = run_python_vectors(part.part)
    return ("pass" if ok else "fail"), detail, ok


def product_page_status(part: ExternalPart) -> tuple[str, str]:
    if not part.product_page.exists():
        return "missing", "product page snapshot missing"
    text = part.product_page.read_text(encoding="utf-8", errors="ignore")
    missing_terms = [term for term in part.expected_terms if term.lower() not in text.lower()]
    zip_links = sorted(set(re.findall(r"/lit/zip/[a-z0-9]+", text, flags=re.IGNORECASE)))
    if missing_terms:
        return "incomplete", "missing expected page terms: " + ", ".join(missing_terms)
    if zip_links:
        return "ok", "simulation/model links found: " + ", ".join(zip_links)
    return "ok", "no chip-specific simulation model link found in saved product page"


def structural_model_status(part: ExternalPart) -> tuple[str, str]:
    if part.model_path is None:
        return "not_available", "no downloaded vendor simulation model for this part"
    if not part.model_path.exists():
        return "missing", f"model file missing: {part.model_path.relative_to(ROOT)}"
    text = part.model_path.read_text(encoding="utf-8", errors="ignore")
    if part.part == "74HC00":
        checks = {
            "top_subckt": ".SUBCKT SN74HC00 Y A B VCC AGND" in text,
            "nand_selected": re.search(r"\.PARAM\s+NAND\s*=\s*1\b", text) is not None,
            "nand_equation": "1 - V(A,VEE)*V(B,VEE)" in text,
            "timing_table": "TPD_LVC_2i_NAND_PP_CMOS_SN74HC00" in text and "(4.5,18.5)" in text,
        }
        failed = [name for name, passed in checks.items() if not passed]
        if failed:
            return "fail", "model structural checks failed: " + ", ".join(failed)
        return "pass", "TI PSpice model declares NAND function and propagation-delay table"
    if part.part == "LM358":
        checks = {
            "ti_copyright": "Texas Instruments Corporation" in text,
            "macro_model": "MACRO-MODEL SIMULATED PARAMETERS" in text,
            "subckt": ".subckt LMX58_LM2904 IN+ IN- VCC VEE OUT" in text,
            "tina_macro": any(path.exists() for path in part.extra_model_paths),
        }
        failed = [name for name, passed in checks.items() if not passed]
        if failed:
            return "fail", "model structural checks failed: " + ", ".join(failed)
        return "pass", "TI PSpice op-amp macro-model and TINA artifacts present"
    if part.part == "LM393":
        checks = {
            "ti_copyright": "Texas Instruments Incorporated" in text,
            "pspice": "Simulator: PSPICE" in text,
            "subckt": ".SUBCKT LM2903B IN+ IN- Vcc GND OUT" in text,
            "tina_macro": any(path.exists() for path in part.extra_model_paths),
        }
        failed = [name for name, passed in checks.items() if not passed]
        if failed:
            return "fail", "model structural checks failed: " + ", ".join(failed)
        return "pass", "TI PSpice comparator model and TINA macro present"
    return "unknown", "no structural parser for this vendor model yet"


def ngspice_model_status(part: ExternalPart) -> tuple[str, str]:
    if part.model_path is None or not part.model_path.exists():
        return "not_run", "no vendor simulation model to run"
    ngspice = shutil.which("ngspice")
    if ngspice is None:
        return "not_run", "ngspice not installed"
    with tempfile.TemporaryDirectory(prefix="components-ngspice-") as tmp:
        tmp_path = Path(tmp)
        (tmp_path / ".spiceinit").write_text("set ngbehavior=psa\n", encoding="utf-8")
        deck = tmp_path / f"{part.part.lower()}_op.cir"
        include = part.model_path.resolve()
        deck.write_text(build_ngspice_deck(part, include), encoding="utf-8")
        result = subprocess.run(
            [ngspice, "-b", deck.name],
            cwd=tmp_path,
            text=True,
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=30,
            check=False,
        )
    output = clean_ngspice_output(result.stdout)
    if result.returncode == 0:
        ok, detail = validate_ngspice_output(part, result.stdout)
        if ok:
            return "pass", detail
        return "unexpected", detail
    if "no simulations run" in output.lower() and result.returncode == 1:
        return "parse_only", "raw model parses, but no test deck was run"
    return "incompatible", output[:240] or f"ngspice exited {result.returncode}"


def build_ngspice_deck(part: ExternalPart, include: Path) -> str:
    if part.part == "74HC00":
        return f"""* {part.part} vendor-model compatibility smoke
.include {include}
VCC VCC 0 5
VA00 A00 0 0
VB00 B00 0 0
VA01 A01 0 0
VB01 B01 0 5
VA10 A10 0 5
VB10 B10 0 0
VA11 A11 0 5
VB11 B11 0 5
X00 Y00 A00 B00 VCC 0 SN74HC00
X01 Y01 A01 B01 VCC 0 SN74HC00
X10 Y10 A10 B10 VCC 0 SN74HC00
X11 Y11 A11 B11 VCC 0 SN74HC00
.op
.print op V(Y00) V(Y01) V(Y10) V(Y11)
.end
"""
    if part.part == "LM358":
        return f"""* {part.part} vendor-model compatibility smoke
.include {include}
VCC VCC 0 5
VEE VEE 0 0
VINP INP 0 2.5
VINM INM 0 2.4
XU INP INM VCC VEE OUT LMX58_LM2904
RL OUT 0 100k
.op
.print op V(OUT)
.end
"""
    if part.part == "LM393":
        return f"""* {part.part} vendor-model compatibility smoke
.include {include}
VCC VCC 0 5
VINP INP 0 2.5
VINM INM 0 2.4
XU INP INM VCC 0 OUT LM2903B
RPU OUT VCC 10k
.op
.print op V(OUT)
.end
"""
    return f".include {include}\n.end\n"


def validate_ngspice_output(part: ExternalPart, text: str) -> tuple[bool, str]:
    if part.part == "74HC00":
        values = {name: value for name, value in extract_node_voltages(text).items() if name in {"y00", "y01", "y10", "y11"}}
        missing = sorted({"y00", "y01", "y10", "y11"} - set(values))
        if missing:
            return False, "ngspice ran but missing NAND output nodes: " + ", ".join(missing)
        expected_high = all(values[name] > 4.0 for name in ("y00", "y01", "y10"))
        expected_low = values["y11"] < 0.8
        if expected_high and expected_low:
            return True, "ngspice PSpice-mode vendor model executed all four NAND truth cases"
        return False, f"unexpected NAND voltages: {values}"
    if part.part == "LM358":
        out = extract_node_voltages(text).get("out")
        if out is None:
            return False, "ngspice ran but missing LM358 OUT voltage"
        if out > 3.0:
            return True, f"ngspice PSpice-mode op-amp macro executed non-inverting smoke, OUT={out:.3g} V"
        return False, f"unexpected LM358 OUT={out:.3g} V"
    if part.part == "LM393":
        out = extract_node_voltages(text).get("out")
        if out is None:
            return False, "ngspice ran but missing LM393 OUT voltage"
        if out > 4.0:
            return True, f"ngspice PSpice-mode comparator macro executed high-output smoke, OUT={out:.3g} V"
        return False, f"unexpected LM393 OUT={out:.3g} V"
    return True, "ngspice executed vendor model operating-point deck"


def extract_node_voltages(text: str) -> dict[str, float]:
    values: dict[str, float] = {}
    for line in text.splitlines():
        match = re.match(r"\s*([A-Za-z][A-Za-z0-9_']*)\s+([-+]?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?)\s*$", line)
        if match:
            values[match.group(1).lower()] = float(match.group(2))
    return values


def clean_ngspice_output(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    interesting = [
        line
        for line in lines
        if "error" in line.lower()
        or "warning" in line.lower()
        or "unable to find" in line.lower()
        or "simulation interrupted" in line.lower()
        or "v(y" in line.lower()
        or "v(out)" in line.lower()
        or re.match(r"^[0-9]+\s+[-+0-9.eE]+", line)
    ]
    return "; ".join(interesting[:8])


def main() -> int:
    rows: list[dict[str, str]] = []
    failures: list[str] = []

    for part in PARTS:
        page_status, page_detail = product_page_status(part)
        model_status, model_detail = structural_model_status(part)
        spice_status, spice_detail = ngspice_model_status(part)
        python_status, py_detail, py_ok = python_vector_status(part)
        if not py_ok:
            failures.append(f"{part.part}: Python vectors failed: {py_detail}")
        if page_status != "ok":
            failures.append(f"{part.part}: product source problem: {page_detail}")
        if model_status in ("fail", "missing"):
            failures.append(f"{part.part}: vendor model structural problem: {model_detail}")
        rows.append(
            {
                "part": part.part,
                "source": page_status,
                "vendor_model": model_status,
                "ngspice": spice_status,
                "python": python_status,
                "result": row_result(page_status, model_status, spice_status, py_ok, python_status),
                "notes": "; ".join((page_detail, model_detail, spice_detail, py_detail)),
                "url": part.product_url,
            }
        )

    write_report(rows, failures)
    print(json.dumps({"rows": len(rows), "failures": failures, "report": str(REPORT)}, indent=2))
    return 1 if failures else 0


def row_result(
    page_status: str, model_status: str, spice_status: str, py_ok: bool, python_status: str
) -> str:
    if not py_ok or page_status != "ok" or model_status == "fail":
        return "FAIL"
    if model_status == "pass" and spice_status == "pass":
        return "VENDOR_SIM_PASS"
    if model_status == "pass" and python_status == "not_applicable":
        return "VENDOR_MODEL_PRESENT_NO_LOCAL_DIGITAL_MODEL"
    if model_status == "pass":
        return "VENDOR_MODEL_STRUCTURAL_PASS"
    return "SOURCE_CONFIRMED_NO_VENDOR_SIM"


def write_report(rows: list[dict[str, str]], failures: list[str]) -> None:
    lines = [
        "# External Model Cross-check Report",
        "",
        "Generated by `tools/external_model_crosscheck.py` from official vendor source snapshots in `Source/ExternalModels/`.",
        "",
        "A product page or datasheet confirms behavior, but only a downloaded executable model counts as external simulation evidence.",
        "Support IC rows can have vendor analog models while remaining `not_applicable` for local digital Python vectors.",
        "",
        "| Part | Source | Vendor model | ngspice | Python vectors | Result | Notes |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {part} | [{source}]({url}) | {vendor_model} | {ngspice} | {python} | {result} | {notes} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Parts checked: {len(rows)}",
            f"- Failures: {len(failures)}",
            "- Scope: pilot external verification for parts with downloaded official TI product pages; broader DB behavior remains covered by local datasheet/truth-vector cross-check tools.",
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
