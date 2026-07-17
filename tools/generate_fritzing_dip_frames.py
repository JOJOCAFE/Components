#!/usr/bin/env python3
"""Generate definition-backed Board SVG frames in the Fritzing DIP style.

The frame geometry is adapted from Adr-hyng/74LS-Series-Fritzing-Parts
(`Schematic/`, CC BY-SA 3.0).  It is deliberately only a presentation style:
this generator reads every visible pin number, name, side, and direction from
our local ``symbol/dip.json`` record.  No Fritzing connector name or 74LS
pinout is treated as component truth.
"""

from __future__ import annotations

import html
import json
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib" / "standard" / "74xx"
OUT = ROOT / "board" / "assets" / "74hc-functional-pinouts"
NO_PIN_OUT = ROOT / "board" / "assets" / "74hc-chip-frames-no-pins"
MANIFEST = OUT / "fritzing-frames.manifest.json"
README = OUT / "FRITZING_FRAMES.md"
EXTERNAL_SOURCE = "https://github.com/Adr-hyng/74LS-Series-Fritzing-Parts/tree/main/Schematic"
EXTERNAL_LICENSE = "CC BY-SA 3.0"
INTERNAL_SYMBOLS = {"74HC04", "74HC05", "74HC08", "74HC14"}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def frame_svg(record: dict, *, include_pinout: bool = True, include_leads: bool = True) -> str:
    part = record["part"]
    package = record["package"]
    pins = record["pins"]
    total = package["pins"]
    if total % 2:
        raise ValueError(f"{part}: DIP package has odd pin count")
    rows = total // 2
    width = 1100
    row_pitch = 100
    top = 100
    body_x, body_width = 200, 700
    body_y, body_height = 30, rows * row_pitch + 90
    height = body_y + body_height + 120
    by_number = {pin["number"]: pin for pin in pins}
    expected = set(range(1, total + 1))
    if set(by_number) != expected:
        raise ValueError(f"{part}: symbol record does not cover pins 1..{total}")

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f'  <title id="title">{esc(part)} definition-backed DIP frame</title>',
        f'  <desc id="desc">{esc(part)} DIP frame. Frame style adapted from {esc(EXTERNAL_SOURCE)} under {EXTERNAL_LICENSE}; local Components definition provides all pin truth.</desc>',
        '  <style>.body{fill:#fff;stroke:#000;stroke-width:12.5}.lead{stroke:#787878;stroke-width:9.72;stroke-linecap:round}.pin{fill:none;stroke:none}.name{font:50px "Droid Sans",Arial,sans-serif;fill:#444}.number{font:30px "Droid Sans",Arial,sans-serif;fill:#666}.title{font:44px "Droid Sans",Arial,sans-serif;fill:#111}</style>',
        f'  <text class="title" x="550" y="{height - 34}" text-anchor="middle">{esc(part)} · DIP-{total}</text>',
        f'  <rect class="body" x="{body_x}" y="{body_y}" width="{body_width}" height="{body_height}" rx="4"/>',
        f'  <path d="M{width / 2 - 35:.1f} {body_y}a35 35 0 0 0 70 0" fill="none" stroke="#000" stroke-width="12.5"/>',
    ]
    for number in range(1, total + 1):
        pin = by_number[number]
        left = number <= rows
        row = number - 1 if left else total - number
        y = top + row * row_pitch
        x1, x2 = (5, body_x) if left else (body_x + body_width, width - 5)
        connector = number - 1
        name_x = body_x + 20 if left else body_x + body_width - 20
        name_anchor = "start" if left else "end"
        number_x = 100 if left else width - 100
        if include_pinout:
            if include_leads:
                lines.append(f'  <line class="lead" x1="{x1}" y1="{y}" x2="{x2}" y2="{y}"/>')
            lines.extend((
                f'  <rect class="pin" id="connector{connector}pin" data-pin-number="{number}" data-pin-name="{esc(pin["name"])}" data-direction="{esc(pin["direction"])}" x="{min(x1, x2)}" y="{y - 5}" width="{abs(x2 - x1)}" height="10"/>',
                f'  <text class="name" x="{name_x}" y="{y + 17}" text-anchor="{name_anchor}">{esc(pin["name"])}</text>',
                f'  <text class="number" x="{number_x}" y="{y - 15}" text-anchor="middle">{number}</text>',
            ))
    lines.append('</svg>')
    return "\n".join(lines) + "\n"


def read_records() -> list[dict]:
    records = []
    for path in sorted(SOURCE.glob("*/symbol/dip.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("shape") != "dip" or record.get("package", {}).get("kind") != "DIP":
            continue
        records.append(record)
    return records


def main() -> None:
    records = read_records()
    OUT.mkdir(parents=True, exist_ok=True)
    NO_PIN_OUT.mkdir(parents=True, exist_ok=True)
    # Keep source PNGs and the hand-drawn internal-symbol SVGs in the shared
    # review folder. Remove only names recorded by the last frame manifest.
    if MANIFEST.exists():
        previous = json.loads(MANIFEST.read_text(encoding="utf-8"))
        for item in previous.get("frames", []):
            candidate = OUT / item.get("file", "")
            if candidate.parent == OUT and candidate.suffix == ".svg":
                candidate.unlink(missing_ok=True)
    manifest = []
    for record in records:
        part = record["part"]
        output = OUT / f"{part.lower()}.svg"
        output.write_text(frame_svg(record), encoding="utf-8")
        ET.parse(output)
        no_pin_output = NO_PIN_OUT / output.name
        no_pin_output.write_text(frame_svg(record, include_pinout=True, include_leads=False), encoding="utf-8")
        ET.parse(no_pin_output)
        manifest.append({
            "part": part,
            "file": output.name,
            "pins": record["package"]["pins"],
            "frame_style": "Adr-hyng 74LS-Series-Fritzing-Parts Schematic DIP frame",
            "external_source": EXTERNAL_SOURCE,
            "license": EXTERNAL_LICENSE,
            "internal_symbol_asset": f"{part.lower()}-internal.svg" if part in INTERNAL_SYMBOLS else None,
        })
    MANIFEST.write_text(json.dumps({"schema": "components.board.fritzing-dip-frame@1", "frames": manifest}, indent=2) + "\n", encoding="utf-8")
    README.write_text(
        "# Definition-backed Fritzing-style DIP frames\n\n"
        f"The outside-frame style is adapted from [{EXTERNAL_SOURCE}]({EXTERNAL_SOURCE}), licensed {EXTERNAL_LICENSE}. "
        "These derived SVGs are therefore distributed under CC BY-SA 3.0 with this attribution.\n\n"
        "Local `symbol/dip.json` files—not the external 74LS schematics—supply pin numbers, names, sides, and directions. "
        "The external connector metadata is not reused because it can differ from visible labels.\n\n"
        "For 74HC04, 74HC05, 74HC08, and 74HC14, the manifest links the existing Components internal functional-pinout SVG. "
        "A Board may compose that internal art inside this frame, but must obtain connectable ports from the resolved definition.\n",
        encoding="utf-8",
    )
    (NO_PIN_OUT / "README.md").write_text(
        "# Definition-backed no-pin DIP frames\n\n"
        "These SVGs are generated from the same reviewed DIP records as the sibling functional frames, but deliberately omit the long pin lead stubs. "
        "They retain readable pin labels while the Board renders definition-owned connection dots at the node locations; it must never infer a pin, port, or behavior from this frame.\n",
        encoding="utf-8",
    )
    print(f"generated={len(manifest)}")


if __name__ == "__main__":
    main()
