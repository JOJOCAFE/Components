#!/usr/bin/env python3
"""Guard the pre-implementation whole-system Component language contract."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "Language/fixtures/component-first-draft/examples-circuits-coverage.json"
FIXTURES = ROOT / "Language/fixtures/component-system-profile"
SOURCE = FIXTURES / "rv8gr_whole_system.component"
TARGET = FIXTURES / "rv8gr_whole_system.resolved-contract.json"


def main() -> int:
    errors: list[str] = []
    source = SOURCE.read_text(encoding="utf-8")
    target = json.loads(TARGET.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))

    required_source = (
        "component:component RV8GRWholeSystemChipLevelVirtual",
        "port CLK : digital input;",
        "bus port IBUS[8] : digital bidirectional;",
        "component Boot is rv8gr.BootSequenceTrace",
        "lock \"components.rv8gr.BootSequenceTrace@sha256:pending-interface-publication\";",
        "timing contract virtual_stress_only",
        "evidence {",
        "test-suite \"examples/circuits/RV8GR_WholeSystemChipLevelVirtual/tests/whole_system_chip_level_virtual.json\"",
    )
    for token in required_source:
        if token not in source:
            errors.append(f"fixture source missing: {token}")
    forbidden_source = ("inject ", "tick(", "place ", "route ", "run campaign")
    for token in forbidden_source:
        if token in source:
            errors.append(f"fixture wrongly pulls deferred syntax into Component: {token}")

    if target.get("schema") != "components.resolved-component-contract@1":
        errors.append("wrong resolved contract schema")
    if target.get("status") != "contract-only; no parser, child interface, or execution claim":
        errors.append("contract target must remain non-executable")
    port_ids = {entry.get("id") for entry in target.get("public_interface", {}).get("ports", [])}
    expected_ports = {"CLK", "/RST", "IBUS", "DBUS", "ABUS", "PC", "AC", "Z", "PG", "DP", "RAM_/OE", "RAM_/WE", "ROM_/OE"}
    if port_ids != expected_ports:
        errors.append("whole-system boundary ports do not match the source-shaped RV8GR contract")
    for bus in ("IBUS", "DBUS", "ABUS", "PC", "AC", "PG", "DP"):
        entry = next((p for p in target["public_interface"]["ports"] if p["id"] == bus), {})
        if entry.get("width") not in (8, 16) or "bit_order" not in entry:
            errors.append(f"{bus}: boundary bus lacks locked width/order")
    if len(target.get("child_locks", [])) < 5:
        errors.append("whole-system fixture needs independent locked child Components")

    owned = set(target.get("component_owned", []))
    expected_owned = {"boundary_ports", "hierarchy_locks", "typed_topology", "circuit_metadata", "timing_contracts", "evidence", "test_suite_references", "read_only_observations"}
    if not expected_owned <= owned:
        errors.append("resolved contract omits a Component-owned system concept")
    deferred = " ".join(
        f"{item.get('owner', '')} {item.get('item', '')}"
        for item in target.get("deferred_capabilities", [])
    )
    # Every blocker family in the coverage audit is supplied here or assigned
    # to its proper later owner.  This prevents a misleading "covers all"
    # claim while the real records/interfaces do not exist yet.
    blocker_expectations = {
        "public ports": "boundary_ports",
        "hierarchy": "hierarchy_locks",
        "metadata": "circuit_metadata",
        "timing": "timing_contracts",
        "trace execution": "component:operation",
        "opcode sweep": "component:operation",
        "stress/campaign": "component:operation",
        "orchestration metadata": "circuit_metadata",
        "passive/analog": "analog/passive",
        "compact Device": "compact resolved",
        "compact device": "compact resolved",
        "child Component": "resolved child interfaces",
        "child interfaces": "resolved child interfaces",
        "physical": "physical timing",
        "legacy aliases": "component:operation",
        "legacy input": "component:operation",
        "62256 needs": "compact resolved",
        "range expansion": "typed_topology",
        "multi-chip counter": "hierarchy_locks",
        "rv8gr_aluaccumulator": "resolved child interfaces",
        "report, not": "legacy compatibility",
        "coverage index": "legacy compatibility",
        "measurement workflow": "component:board",
    }
    blockers = [blocker.lower() for entry in audit["files"].values() for blocker in entry.get("blockers", [])]
    for blocker in blockers:
        matched = False
        for phrase, remedy in blocker_expectations.items():
            if phrase.lower() in blocker:
                matched = remedy in owned or remedy.lower() in deferred.lower()
                break
        if not matched:
            errors.append(f"coverage blocker not addressed or explicitly deferred: {blocker}")
    if errors:
        print("COMPONENT SYSTEM PROFILE CHECK FAIL")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print("COMPONENT SYSTEM PROFILE CHECK PASS (all audit blockers owned or explicitly deferred)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
