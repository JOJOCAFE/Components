#!/usr/bin/env python3
"""Crop only DIP/PDIP pinout drawings from rendered 74HC source pages.

The old caption-relative crop deliberately kept the last ink cluster above a
caption.  That works for the original small functional-pinout drawings, but it
silently selected logos, prose, or an adjacent SO/SSOP/LCCC drawing on modern
multi-package datasheets.  This tool has two explicit paths:

* the reviewed original functional-pinout samples use their caption geometry;
* all other output must come from the left DIP/PDIP pinout area of a source
  page whose text explicitly says DIP or PDIP.

It is intentionally fail-closed: no first-page fallbacks and no output for a
page that cannot establish a DIP form.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess

from PIL import Image, ImageChops


ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "resource" / "temp" / "74hc-functional-pinout-pages"
OUT = ROOT / "board" / "assets" / "74hc-functional-pinouts"
REVIEWED_FUNCTIONAL_DIP = {
    "74HC00", "74HC02", "74HC03", "74HC04", "74HC05", "74HC08", "74HC14", "74HC21",
}
# These source pages have one complete leaded/shared DIP diagram in the
# selected left-hand source region.  Parts not listed here require an explicit
# reviewed bounding box; a plausible-looking fragment is not an asset.
AUTOMATIC_DIP_VIEW = {
    "74HC132", "74HC138", "74HC139", "74HC151", "74HC153", "74HC157",
    "74HC164", "74HC165", "74HC166", "74HC240", "74HC244", "74HC245",
    "74HC251", "74HC257", "74HC266", "74HC273", "74HC283", "74HC30",
    "74HC32", "74HC374", "74HC541", "74HC574", "74HC595", "74HC74",
    "74HC86", "74HCT04", "74HCT14", "74HCT245", "74HCT541", "74HCT574",
}
# These six pages place the DIP drawing somewhere other than the standard TI
# left-hand region.  Fractions are explicit source-page review boxes, ordered
# left, top, right, bottom.  Each excludes the neighbouring non-DIP drawing.
MANUAL_DIP_VIEW = {
    "74HC11": (0.16, 0.49, 0.43, 0.67),
    "74HC147": (0.40, 0.12, 0.60, 0.29),
    "74HC154": (0.18, 0.29, 0.43, 0.51),
    "74HC238": (0.18, 0.57, 0.42, 0.75),
    "74HC27": (0.18, 0.28, 0.42, 0.47),
    "74HC688": (0.40, 0.11, 0.62, 0.32),
}


def caption_box(pdf: Path, page: int) -> tuple[float, float, float] | None:
    xml = subprocess.check_output(["pdftotext", "-f", str(page), "-l", str(page), "-bbox", str(pdf), "-"], text=True, errors="replace")
    # Some historic vendor PDFs emit invalid control characters in the bbox
    # text. Read only the word tags and coordinates so one bad character does
    # not block the whole extraction batch.
    words = [(text, float(x0), float(y0), float(x1), float(y1)) for x0, y0, x1, y1, text in re.findall(r'<word xMin="([^"]+)" yMin="([^"]+)" xMax="([^"]+)" yMax="([^"]+)">(.*?)</word>', xml, flags=re.DOTALL)]
    # Prefer the actual two-word figure caption.  A modern first page often
    # contains earlier prose such as "functional pinout" or a package table;
    # choosing its first isolated ``pinout`` word was the reason 74HC14 was
    # cropped as a header instead of the drawing at the bottom of the page.
    candidates = [words[index + 1] for index, item in enumerate(words[:-1])
                  if item[0].strip().lower() == "functional"
                  and words[index + 1][0].strip().lower() == "pinout"
                  and abs(words[index + 1][2] - item[2]) < 2]
    if not candidates:
        candidates = [item for item in words if item[0].lower() in {"pinout", "configuration", "diagram"}]
    if not candidates:
        return None
    _, x0, y0, x1, y1 = candidates[0]
    same_line = [item for item in words if abs(item[2] - y0) < 2 and item[1] < x0]
    left = same_line[-1][1] if same_line else x0
    return left, y0, x1


def crop_functional(image: Path, marker: tuple[float, float, float], output: Path, window_height: int = 230) -> None:
    with Image.open(image).convert("RGB") as page:
        scale_x, scale_y = page.width / 612, page.height / 792
        left, caption_y, right = marker
        center = ((left + right) / 2) * scale_x
        bottom = caption_y * scale_y - 14
        # The symbol sits immediately above the caption. A short window avoids
        # pulling in unrelated tables from the upper half of first pages.
        box = (max(0, int(center - 250)), max(0, int(bottom - window_height)), min(page.width, int(center + 250)), max(0, int(bottom)))
        candidate = page.crop(box)
        ink = ImageChops.difference(candidate, Image.new("RGB", candidate.size, "white")).convert("L").point(lambda value: 255 if value > 38 else 0)
        # If a nearby table/footer appears above the diagram, split at the
        # largest blank band and retain the lower diagram cluster.
        rows = [y for y in range(ink.height) if ink.crop((0, y, ink.width, y + 1)).getbbox()]
        if rows:
            groups = [[rows[0], rows[0]]]
            for row in rows[1:]:
                if row - groups[-1][1] <= 14:
                    groups[-1][1] = row
                else:
                    groups.append([row, row])
            if len(groups) > 1:
                candidate = candidate.crop((0, groups[-1][0], candidate.width, candidate.height))
                ink = ink.crop((0, groups[-1][0], ink.width, ink.height))
        bounds = ink.getbbox()
        if bounds is None:
            raise ValueError("no diagram ink in candidate region")
        margin = 12
        x0, y0, x1, y1 = bounds
        candidate.crop((max(0, x0 - margin), max(0, y0 - margin), min(candidate.width, x1 + margin), min(candidate.height, y1 + margin))).save(output)


def pin_functions_top(pdf: Path, page: int) -> float | None:
    """Return the first lower-page ``Pin Functions`` heading, in PDF points."""
    xml = subprocess.check_output(["pdftotext", "-f", str(page), "-l", str(page), "-bbox", str(pdf), "-"], text=True, errors="replace")
    words = [(text.lower(), float(y0)) for _, y0, _, _, text in re.findall(r'<word xMin="([^"]+)" yMin="([^"]+)" xMax="([^"]+)" yMax="([^"]+)">(.*?)</word>', xml, flags=re.DOTALL)]
    for index, (text, y) in enumerate(words[:-1]):
        if text == "pin" and words[index + 1][0].startswith("functions") and y > 120:
            return y
    return None


def crop_dip_view(image: Path, pdf: Path, page_number: int, source_name: str, output: Path, explicit_fractions: tuple[float, float, float, float] | None = None) -> None:
    """Keep the source page's left DIP/PDIP diagram, never a second package.

    TI pages conventionally put the leaded/shared DIP pinout at upper left and
    QFN/LCCC variants to its right.  NXP/Philips pages use a taller left-hand
    pinning panel.  The fixed source-region selection is deliberate: it is
    reviewable and avoids inferring a package from drawing coordinates.
    """
    with Image.open(image).convert("RGB") as page:
        if explicit_fractions is not None:
            fractions = explicit_fractions
        elif any(vendor in source_name.upper() for vendor in ("NXP", "PHILIPS")):
            fractions = (0.06, 0.18, 0.54, 0.62)
        else:
            fractions = (0.08, 0.13, 0.56, 0.45)
        table_top = pin_functions_top(pdf, page_number)
        if explicit_fractions is None and table_top is not None:
            fractions = (*fractions[:3], min(fractions[3], table_top / 792 - 0.015))
        x0, y0, x1, y1 = fractions
        candidate = page.crop((int(page.width * x0), int(page.height * y0), int(page.width * x1), int(page.height * y1)))
        ink = ImageChops.difference(candidate, Image.new("RGB", candidate.size, "white")).convert("L").point(lambda value: 255 if value > 38 else 0)
        bounds = ink.getbbox()
        if bounds is None:
            raise ValueError("no DIP-view ink in selected source region")
        margin = 12
        left, top, right, bottom = bounds
        candidate.crop((max(0, left - margin), max(0, top - margin), min(candidate.width, right + margin), min(candidate.height, bottom + margin))).save(output)


def main() -> None:
    manifest_path = PAGES / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    # Every file in this directory is a generated review crop.  Clear stale
    # images first so a previously bad SO/SSOP/logo crop cannot remain usable.
    for stale in OUT.glob("*.png"):
        stale.unlink()
    cropped = 0
    for item in manifest["records"]:
        if item.get("status") != "extracted":
            continue
        output = OUT / f"{item['part'].lower()}.png"
        if item["part"] in REVIEWED_FUNCTIONAL_DIP:
            pdf = ROOT / "source" / item["source"]
            marker = caption_box(pdf, item["page"])
            if marker is None:
                item["crop_status"] = "blocked-reviewed-caption-not-found"
                continue
            crop_functional(PAGES / item["image"], marker, output, 165 if item["part"] == "74HC14" else 230)
            item["crop_selection"] = "reviewed-functional-dip"
        elif item["part"] in AUTOMATIC_DIP_VIEW and item.get("source_mentions_dip"):
            crop_dip_view(PAGES / item["image"], ROOT / "source" / item["source"], item["page"], item["source"], output)
            item["crop_selection"] = "left-dip-or-pdip-source-view"
        elif item["part"] in MANUAL_DIP_VIEW and item.get("source_mentions_dip"):
            crop_dip_view(PAGES / item["image"], ROOT / "source" / item["source"], item["page"], item["source"], output, MANUAL_DIP_VIEW[item["part"]])
            item["crop_selection"] = "reviewed-explicit-dip-source-bbox"
        else:
            item["crop_status"] = "blocked-needs-reviewed-dip-bbox"
            continue
        item["crop"] = output.relative_to(ROOT).as_posix()
        item["crop_status"] = "cropped-dip-only"
        cropped += 1
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"cropped={cropped}")


if __name__ == "__main__":
    main()
