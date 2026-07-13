"""Contract tests for the text Component Resource bridge."""

from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys

from chiplib.component_language import parse_component_file, resolve_component
from chiplib.component_resources import bind_resource, inspect_resource


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "Language" / "fixtures" / "component-v1.1" / "digital_inverter.component"


def test_inspect_returns_only_existing_presentation_resource() -> None:
    data = inspect_resource("74HC04")
    assert data["ok"], data["diagnostics"]
    assert data["resource"]["id"] == "standard.74xx.74HC04.resource@1"
    assert data["resource"]["views"] == [{
        "id": "dip", "kind": "symbol.dip", "artifact": "lib/standard/74xx/74HC04/symbol/dip.json",
    }]
    assert "logic" not in json.dumps(data["resource"])
    assert "picture" in data["student"]["message"]


def test_missing_resource_is_explicit_not_guessed() -> None:
    data = inspect_resource("Probe")
    assert data["ok"] is False
    assert data["diagnostics"][0]["code"] == "resource.missing"


def test_bind_locks_real_resource_to_existing_matching_device_only() -> None:
    resolved = resolve_component(parse_component_file(FIXTURE))
    before = json.dumps(resolved, sort_keys=True)
    data = bind_resource(resolved, target_id="U1", part="74HC04", view="dip", label="My NOT gate")
    assert data["ok"], data["diagnostics"]
    binding = data["binding"]
    assert binding["schema"] == "components.resource-binding@1"
    assert binding["bindings"][0]["target"] == {"kind": "device-instance", "id": "U1"}
    assert binding["bindings"][0]["presentation"] == {"label": "My NOT gate"}
    assert binding["topology_ref"]["component_id"] == "DigitalInverterFixture"
    assert binding["topology_ref"]["digest"].startswith("sha256:")
    assert json.dumps(resolved, sort_keys=True) == before


def test_bind_rejects_wrong_target_part_and_view() -> None:
    resolved = resolve_component(parse_component_file(FIXTURE))
    assert bind_resource(resolved, target_id="missing", part="74HC04", view="dip")["diagnostics"][0]["code"] == "resource.target_missing"
    assert bind_resource(resolved, target_id="U1", part="74HC00", view="dip")["diagnostics"][0]["code"] == "resource.part_mismatch"
    assert bind_resource(resolved, target_id="U1", part="74HC04", view="symbol")["diagnostics"][0]["code"] == "resource.view_missing"


def test_resource_cli_is_json_api_ready_and_student_readable() -> None:
    result = subprocess.run(
        [sys.executable, "-B", "-m", "chiplib.cli", "component-resource-bind", str(FIXTURE),
         "--target", "U1", "--resource", "74HC04", "--view", "dip"],
        cwd=ROOT, text=True, capture_output=True, check=False,
        env={**__import__("os").environ, "PYTHONPATH": str(ROOT / "python")},
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["ok"] and data["student"]["next_step"].startswith("Send this JSON")


def main() -> None:
    test_inspect_returns_only_existing_presentation_resource()
    test_missing_resource_is_explicit_not_guessed()
    test_bind_locks_real_resource_to_existing_matching_device_only()
    test_bind_rejects_wrong_target_part_and_view()
    test_resource_cli_is_json_api_ready_and_student_readable()
    print("Components Resource bridge tests passed")


if __name__ == "__main__":
    main()
