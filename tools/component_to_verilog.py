"""Bridge: component:component text → Design → Verilog export.

This tool extracts the topology subset (device + connect) from .component
files and exports them through the existing Verilog pipeline.  Stimulus,
tests, probes, policies, and other runtime-only features are skipped since
they have no Verilog representation.

Usage:
    python3 -m tools.component_to_verilog examples/circuits/nand.component
    python3 -m tools.component_to_verilog --all       # test all .component files
    python3 -m tools.component_to_verilog --verify    # compare against existing Verilog
"""

import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

from chiplib.design import Design
from chiplib.db import load_component

_ROOT = Path(__file__).resolve().parents[1]

# Virtual parts that have no Verilog export
VIRTUAL_PARTS = {
    "ClockSource", "Switch", "Probe", "BusProbe", "BusDriver",
    "RCParasitic", "DelayNoise", "SequenceGenerator", "LogicAnalyzer",
    "OutputAssert", "InputSource",
}

# Library prefix to DB group mapping
LIBRARY_GROUPS = {
    "digital": "74xx",
    "memory": "memory",
    "virtual": "virtual",
    "passive": "passive",
}


def extract_topology(source: str) -> dict:
    """Extract device and connect declarations from component text."""
    chips = {}
    connections = []
    aliases = {}
    buses = {}

    lines = source.split("\n")
    for raw in lines:
        line = raw.strip()

        # Remove inline comments (-- style)
        if "--" in line:
            line = line[:line.index("--")].strip()

        # Remove trailing semicolons
        if line.endswith(";"):
            line = line[:-1].strip()

        # Skip empty or comment-only lines
        if not line or line.startswith("//") or line.startswith("#"):
            continue

        # device REF, LIBRARY.PART or device REF, LIBRARY.PART, {params}
        dev_match = re.match(r"device\s+(\S+)\s*,\s*(\S+?)(?:\s*,\s*\{.*\})?$", line)
        if dev_match:
            ref = dev_match.group(1)
            locator = dev_match.group(2)
            # Extract part name (last segment)
            part = locator.rsplit(".", 1)[-1]
            # Skip virtual devices and hierarchy references
            prefix = locator.split(".", 1)[0] if "." in locator else ""
            if part in VIRTUAL_PARTS or prefix in ("virtual", "child", "project"):
                continue
            chips[ref] = {"part": part}
            continue

        # instance REF, TYPE -- treat as sub-circuit (skip for Verilog)
        inst_match = re.match(r"instance\s+(\S+)\s*,\s*(\S+)", line)
        if inst_match:
            # Hierarchical instances can't be directly exported without resolving sub-circuits
            continue

        # connect ENDPOINT -> ENDPOINT
        conn_match = re.match(r"connect\s+(.+?)\s*->\s*(.+)$", line)
        if conn_match:
            src = conn_match.group(1).strip()
            tgt = conn_match.group(2).strip()
            # Convert port-name references to pin numbers
            src_pin = _to_pin_ref(src, chips)
            tgt_pin = _to_pin_ref(tgt, chips)
            if src_pin and tgt_pin:
                connections.append(f"{src_pin} -> {tgt_pin}")
            continue

        # bus NAME[WIDTH] : KIND
        bus_match = re.match(r"bus\s+(\w+)\[(\d+)\]\s*:", line)
        if bus_match:
            buses[bus_match.group(1)] = {"width": int(bus_match.group(2))}
            continue

    return {
        "name": _extract_name(source),
        "chips": chips,
        "connect": connections,
        "aliases": aliases,
        "buses": buses,
    }


def _extract_name(source: str) -> str:
    """Extract component name from header."""
    match = re.search(r"component:component\s+(\w+)", source)
    return match.group(1) if match else "unnamed"


def _to_pin_ref(endpoint: str, chips: dict) -> str | None:
    """Convert endpoint like U1.1A or U1.VCC to pin-number reference U1:N."""
    if "." not in endpoint:
        # It's a net name (vcc, gnd, etc.) or bus member
        if endpoint.lower() in ("vcc", "gnd"):
            return endpoint.upper()
        return endpoint

    instance, port_name = endpoint.split(".", 1)

    # Skip connections to virtual devices
    if instance not in chips:
        return None

    # Handle quoted port names like "I/O0"
    if port_name.startswith('"') and port_name.endswith('"'):
        port_name = json.loads(port_name)

    part = chips[instance]["part"]
    try:
        definition = load_component(part)
    except (KeyError, ValueError):
        return f"{instance}.{port_name}"  # fallback

    pins = definition.get("pins", [])
    # Find pin number by name
    if isinstance(pins, dict):
        # Compact format: {"1": ["1A", "in"], "2": ["1B", "in"], ...}
        for pin_num, pin_data in pins.items():
            if isinstance(pin_data, list) and pin_data[0] == port_name:
                return f"{instance}:{pin_num}"
    elif isinstance(pins, list):
        # List format: [{"number": 1, "name": "A14", "direction": "input"}, ...]
        for pin in pins:
            if pin.get("name") == port_name:
                return f"{instance}:{pin['number']}"

    # Fallback: return as-is (Design will try to resolve)
    return f"{instance}.{port_name}"


def component_to_verilog(source: str) -> dict:
    """Convert component:component source text to Verilog via Design pipeline."""
    topology = extract_topology(source)

    if not topology["chips"]:
        return {"ok": False, "error": "no physical chips found (all virtual)", "name": topology["name"]}

    try:
        design = Design.from_dict(topology)
        result = design.to_verilog()
        return result
    except Exception as e:
        return {"ok": False, "error": str(e), "name": topology["name"]}


def verify_file(path: Path, verbose: bool = False) -> dict:
    """Verify a single .component file can export to Verilog."""
    source = path.read_text(encoding="utf-8")
    result = component_to_verilog(source)

    name = _extract_name(source)
    chips_count = len(extract_topology(source)["chips"])

    status = {
        "file": str(path.relative_to(_ROOT)),
        "name": name,
        "chips": chips_count,
        "ok": result.get("ok", False),
        "unsupported": result.get("unsupported", []),
    }

    if result.get("ok") and result.get("verilog"):
        status["verilog_lines"] = len(result["verilog"].splitlines())
        # Try compiling with iverilog if available
        if _has_iverilog():
            compile_ok = _iverilog_check(result["verilog"], result.get("required_files", []))
            status["iverilog_ok"] = compile_ok
    elif not result.get("ok"):
        status["error"] = result.get("error", "export failed")

    if verbose:
        if result.get("verilog"):
            print(f"\n--- {name} Verilog ({status.get('verilog_lines', 0)} lines) ---")
            print(result["verilog"][:1000])
            if len(result["verilog"]) > 1000:
                print("... (truncated)")

    return status


def _has_iverilog() -> bool:
    """Check if iverilog is available."""
    try:
        subprocess.run(["iverilog", "--version"], capture_output=True, timeout=5)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _iverilog_check(verilog: str, required_files: list) -> bool:
    """Try compiling the Verilog with iverilog."""
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".v", delete=False) as f:
        f.write(verilog)
        f.flush()
        # Build file list: required model .v files + generated file
        files = []
        for rf in required_files:
            if rf.endswith(".v"):
                full = _ROOT / rf
                if full.exists():
                    files.append(str(full))
        files.append(f.name)

        try:
            result = subprocess.run(
                ["iverilog", "-g2012", "-o", "/dev/null"] + files,
                capture_output=True, timeout=30, text=True,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
        finally:
            Path(f.name).unlink(missing_ok=True)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Component → Verilog export bridge")
    parser.add_argument("files", nargs="*", help=".component files to process")
    parser.add_argument("--all", action="store_true", help="Process all .component files in examples/circuits/")
    parser.add_argument("--verify", action="store_true", help="Compile with iverilog to verify")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show Verilog output")
    args = parser.parse_args()

    if args.all:
        files = sorted(_ROOT.glob("examples/circuits/**/*.component"))
    elif args.files:
        files = [Path(f) for f in args.files]
    else:
        parser.print_help()
        return

    results = []
    for f in files:
        status = verify_file(f, verbose=args.verbose)
        results.append(status)

    # Summary
    print("\n" + "━" * 60)
    print(f"{'File':<50} {'Chips':>5} {'Verilog':>8} {'iverilog':>8}")
    print("━" * 60)

    ok_count = 0
    skip_count = 0
    fail_count = 0

    for s in results:
        name = s["name"][:48]
        chips = s["chips"]
        if chips == 0:
            v_status = "virtual"
            skip_count += 1
        elif s["ok"]:
            v_status = f"{s.get('verilog_lines', '?')}L"
            ok_count += 1
        else:
            v_status = "FAIL"
            fail_count += 1

        iv = ""
        if "iverilog_ok" in s:
            iv = "✓" if s["iverilog_ok"] else "✗"

        print(f"  {name:<48} {chips:>5} {v_status:>8} {iv:>8}")

        if not s["ok"] and s.get("error"):
            print(f"    error: {s['error']}")
        if s.get("unsupported"):
            print(f"    unsupported: {', '.join(s['unsupported'])}")

    print("━" * 60)
    print(f"Total: {len(results)} | OK: {ok_count} | Virtual-only: {skip_count} | Failed: {fail_count}")

    sys.exit(0 if fail_count == 0 else 1)


if __name__ == "__main__":
    main()
