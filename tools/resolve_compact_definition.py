#!/usr/bin/env python3
"""Write the canonical resolved view of one compact component definition."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from chiplib.compact_definition import COMPACT_SCHEMA, resolve_compact_definition  # noqa: E402
from chiplib.compact_component_definition import resolve_compact_component  # noqa: E402
from chiplib.memory_definition import MEMORY_SCHEMA, resolve_compact_memory_definition  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="human-authored compact JSON")
    parser.add_argument("--output", type=Path, help="resolved JSON destination (default: sibling generated/resolved.json)")
    parser.add_argument("--check", action="store_true", help="fail if the destination is absent or stale")
    args = parser.parse_args()
    source = args.source.resolve()
    data = json.loads(source.read_text(encoding="utf-8"))
    # Keep one authoring command for all Components classes.  Digital needs a
    # package root for conventional model paths; other classes resolve straight
    # to the existing generic package-definition shape.
    resolved = (
        resolve_compact_definition(data, source.parents[1])
        if data.get("schema") == COMPACT_SCHEMA
        else (resolve_compact_memory_definition(data, source.parents[1])
              if data.get("schema") == MEMORY_SCHEMA else resolve_compact_component(data))
    )
    rendered = json.dumps(resolved, indent=2, sort_keys=True) + "\n"
    output = args.output.resolve() if args.output else source.parents[1] / "generated" / "resolved.json"
    if args.check:
        if not output.exists() or output.read_text(encoding="utf-8") != rendered:
            print(f"stale compact resolved definition: {output}", file=sys.stderr)
            return 1
        print(f"compact resolved definition is current: {output.relative_to(ROOT)}")
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    print(f"wrote {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
