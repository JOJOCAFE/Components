#!/usr/bin/env python3
"""Render the source page containing each 74HC DIP pinout reference.

These PNGs are review references for Board-vector authors. They are not Board
assets and must not replace package definitions or the source PDFs.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
PARTS = sorted(path.name for path in (ROOT / "lib" / "standard" / "74xx").glob("74HC*") if path.is_dir())
SOURCE = ROOT / "source"
OUT = ROOT / "resource" / "temp" / "74hc-functional-pinout-pages"
TOKENS = (
    "functional pinout",
    "functional pin configuration",
    "pin configuration",
    "pinning information",
    "pin assignment",
    "functional diagram",
)


def page_for(pdf: Path, allow_reviewed_non_dip: bool) -> tuple[int | None, str | None, bool]:
    pages = int(subprocess.check_output(["pdfinfo", str(pdf)], text=True).split("Pages:")[1].splitlines()[0].strip())
    first_match: tuple[int, str, bool] | None = None
    dip_candidates: list[tuple[int, int, str]] = []
    priority = {
        "pin configuration": 0,
        "pinning information": 0,
        "pin assignment": 1,
        "functional pinout": 2,
        "functional pin configuration": 2,
        "functional diagram": 3,
    }
    for page in range(1, pages + 1):
        text = subprocess.check_output(["pdftotext", "-f", str(page), "-l", str(page), str(pdf), "-"], text=True, errors="replace").lower()
        if "table of contents" in text:
            continue
        for token in TOKENS:
            if token in text:
                # A source page may show more than one package.  The cropper may
                # use it only when its source text explicitly includes DIP/PDIP.
                # The few original functional-pinout references are retained as
                # reviewed exceptions because their diagrams are already known to
                # be the DIP view.
                has_dip = "dip" in text or "pdip" in text
                if allow_reviewed_non_dip:
                    return page, token, has_dip
                if has_dip:
                    dip_candidates.append((priority[token], page, token))
                    break
                if first_match is None:
                    first_match = page, token, False
    if allow_reviewed_non_dip and first_match is not None:
        return first_match
    if dip_candidates:
        _, page, token = min(dip_candidates)
        return page, token, True
    return None, None, False


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    records = []
    for part in PARTS:
        matches = sorted(SOURCE.glob(f"{part}_*.pdf"))
        if not matches:
            records.append({"part": part, "status": "missing-local-source"})
            continue
        pdf = matches[0]
        page, token, has_dip_text = page_for(pdf, part in {
            "74HC00", "74HC02", "74HC03", "74HC04", "74HC05", "74HC08", "74HC14", "74HC21",
        })
        status = "extracted"
        if page is None:
            # Never turn an arbitrary first page into artwork.  It was the
            # source of logo/text/partial-package crops in the old workflow.
            records.append({"part": part, "source": pdf.name, "status": "no-pinout-source-page"})
            continue
        output = OUT / f"{part.lower()}-source-page.png"
        subprocess.run(["pdftoppm", "-f", str(page), "-l", str(page), "-r", "144", "-png", "-singlefile", str(pdf), str(output.with_suffix(""))], check=True)
        records.append({"part": part, "source": pdf.name, "page": page, "matched": token, "source_mentions_dip": has_dip_text, "image": output.name, "status": status})
    (OUT / "manifest.json").write_text(json.dumps({"schema": "components.74hc-source-page-manifest@1", "records": records}, indent=2) + "\n", encoding="utf-8")
    print(f"extracted={sum(item['status'].startswith('extracted') for item in records)} missing_source={sum(item['status'] == 'missing-local-source' for item in records)} fallback={sum(item['status'] == 'extracted-first-page-fallback' for item in records)}")


if __name__ == "__main__":
    main()
