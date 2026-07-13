"""Golden-pipeline tests for the text-first Component language slice."""

from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys

from chiplib.component_language import component_ide_snapshot, parse_component_file, parse_component_text, resolve_component
from chiplib.component_runtime import ComponentRuntimeSession


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "Language" / "fixtures"


def test_counter_fixture_has_ast_to_resolved_topology_pipeline():
    ast = parse_component_file(FIXTURES / "component-first-draft" / "counter_first_draft.component")
    assert ast["ok"], ast["diagnostics"]
    assert ast["component"]["name"] == "CounterFirstDraft"
    assert [node["kind"] for node in ast["component"]["body"]].count("device") == 3
    resolved = resolve_component(ast)
    assert resolved["ok"], resolved["diagnostics"]
    assert resolved["component_id"] == "CounterFirstDraft"
    assert {edge["to"] for edge in resolved["edges"]} >= {"Counter.VCC", "Counter.GND", "Counter.CLK", "Counter./CLR"}
    assert any(net["id"] == "count[3]" for net in resolved["nets"])
    assert resolved["execution"] == "deferred-operation-runtime"


def test_text_ide_snapshot_is_parse_resolve_validate_not_runtime():
    snapshot = component_ide_snapshot(FIXTURES / "component-v1.1" / "digital_inverter.component")
    assert snapshot["ok"], snapshot["resolved"]["diagnostics"]
    assert snapshot["format"] == "components.text_ide@1"
    assert snapshot["capabilities"] == {"parse": True, "resolve": True, "validate": True, "run": False, "board": False}


def test_resolver_reports_unknown_port_and_scalar_bus_without_guessing():
    source = """
use standard.digital as digital;
use standard.virtual as virtual;
component:component Bad is components.digital {
  device Clock is virtual.ClockSource;
  device U1 is digital.74HC04;
  bus q[4] : digital;
  connect Clock.CLK -> U1.NOT_A_PORT;
  connect Clock.CLK -> q;
}
"""
    result = resolve_component(parse_component_text(source))
    assert result["ok"] is False
    assert {item["code"] for item in result["diagnostics"]} >= {"resolver.unknown_port", "topology.width_mismatch"}


def test_component_ide_cli_emits_both_contracts():
    result = subprocess.run(
        [sys.executable, "-B", "-m", "chiplib.cli", "component-ide", str(FIXTURES / "component-v1.1" / "digital_inverter.component")],
        cwd=ROOT / "python",
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["ast"]["schema"] == "components.component-ast@1"
    assert data["resolved"]["schema"] == "components.resolved-component@1"


def test_runtime_instantiates_resolved_inverter_and_reads_probe():
    resolved = resolve_component(parse_component_file(FIXTURES / "component-v1.1" / "digital_inverter.component"))
    runtime = ComponentRuntimeSession(resolved)
    runtime.drive("clock", 0)
    assert runtime.probe("inverted_level")["probes"]["inverted_level"] == 1
    assert runtime.run_declared_test("inversion")["ok"] is True


def test_checked_golden_pipeline_has_stable_spans_and_resolved_contract():
    root = FIXTURES / "component-v1.1"
    source = root / "golden_leaf.component"
    ast = parse_component_text(source.read_text(encoding="utf-8"), source_name=source.name)
    resolved = resolve_component(ast)
    assert ast == json.loads((root / "golden_leaf.ast.json").read_text(encoding="utf-8"))
    assert resolved == json.loads((root / "golden_leaf.resolved.json").read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "schemas" / "resolved-component.schema.json").read_text(encoding="utf-8"))
    for field in schema["required"]:
        assert field in resolved
    assert all("definition_digest" in lock for lock in resolved["library_lock"])


def test_resolved_cli_is_hash_seed_deterministic():
    fixture = FIXTURES / "component-v1.1" / "golden_leaf.component"
    outputs = []
    for seed in ("0", "1"):
        env = {**__import__("os").environ, "PYTHONHASHSEED": seed, "PYTHONPATH": str(ROOT / "python")}
        result = subprocess.run([sys.executable, "-B", "-m", "chiplib.cli", "component-resolve", str(fixture)], cwd=ROOT, text=True, capture_output=True, env=env, check=False)
        assert result.returncode == 0, result.stderr
        outputs.append(result.stdout)
    assert outputs[0] == outputs[1]


def test_leaf_validation_rejects_power_misuse_and_multiple_outputs():
    source = """
use standard.digital as digital;
use standard.virtual as virtual;
component:component Invalid is components.digital {
 device A, virtual.ClockSource;
 device B, virtual.ClockSource;
 device U1, digital.74HC04;
 net rail : power;
 net driven : digital;
 connect A.CLK -> rail;
 connect A.CLK -> driven;
 connect B.CLK -> driven;
}
"""
    result = resolve_component(parse_component_text(source))
    assert result["ok"] is False
    assert {item["code"] for item in result["diagnostics"]} >= {"validation.power_isolation", "validation.output_ownership"}


def test_leaf_resolver_requires_real_imports_and_a_single_local_namespace():
    source = """
use standard.digital as digital;
use standard.virtual as digital;
component:component Imports is components.digital {
 device digital, digital.74HC04;
 device U1, missing.74HC04;
 net U1 : digital;
 probe U1, U1;
}
"""
    result = resolve_component(parse_component_text(source))
    assert result["ok"] is False
    assert {item["code"] for item in result["diagnostics"]} >= {
        "resolver.duplicate_import_alias",
        "resolver.local_shadows_import",
        "resolver.unknown_import_alias",
        "resolver.duplicate_symbol",
    }


def test_leaf_resolver_rejects_alias_that_claims_the_wrong_library():
    source = """
use arbitrary.namespace as digital;
component:component WrongLibrary is components.digital {
 device U1, digital.74HC04;
}
"""
    result = resolve_component(parse_component_text(source))
    assert result["ok"] is False
    assert "resolver.library_ownership" in {item["code"] for item in result["diagnostics"]}


def test_leaf_resolver_rejects_zero_width_self_wiring_and_net_aliases():
    source = """
use standard.digital as digital;
component:component Unsafe is components.digital {
 device U1, digital.74HC04;
 bus empty[0] : digital;
 net a : digital;
 net b : digital;
 connect a -> a;
 connect a -> b;
}
"""
    result = resolve_component(parse_component_text(source))
    assert result["ok"] is False
    assert {item["code"] for item in result["diagnostics"]} >= {
        "validation.bus_width",
        "validation.self_connection",
        "validation.net_alias_unsupported",
    }


def test_leaf_resolver_keeps_quoted_datasheet_port_names_exact():
    source = '''
use standard.memory as memory;
component:component MemoryPin is components.digital {
 device RAM, memory.62256;
 net chip_enable : digital;
 connect chip_enable -> RAM."/CE";
}
'''
    result = resolve_component(parse_component_text(source))
    assert result["ok"], result["diagnostics"]
    assert result["edges"][0]["target_endpoint"]["port"] == "/CE"


def test_mux_fixture_and_rv8gr_address_mux_keep_the_live_74hc157_pin_contract():
    """Keep a learner-readable Component fixture tied to real library pins.

    ``MuxFirstDraft`` is deliberately not an executable RV8GR replacement.
    It is the small, readable four-bit lesson that uses the same 74HC157
    definition and the same numbered pins as the four chips in AddressMux16.
    This catches a definition rename or pin-number drift before text tooling
    teaches a student a connection that the circuit library cannot make.
    """
    resolved = resolve_component(parse_component_file(FIXTURES / "component-first-draft" / "mux_first_draft.component"))
    assert resolved["ok"], resolved["diagnostics"]
    mux = next(instance for instance in resolved["instances"] if instance["id"] == "Mux")
    assert mux["part"] == "74HC157"
    assert mux["definition_path"] == "lib/standard/74xx/74HC157/definition/definition.json"

    fixture_ports = {
        (edge["source_endpoint"].get("port"), edge["source_endpoint"].get("pin"))
        for edge in resolved["edges"]
        if edge["source_endpoint"].get("instance") == "Mux"
    } | {
        (edge["target_endpoint"].get("port"), edge["target_endpoint"].get("pin"))
        for edge in resolved["edges"]
        if edge["target_endpoint"].get("instance") == "Mux"
    }
    assert fixture_ports == {
        ("A/B", 1), ("1A", 2), ("1B", 3), ("1Y", 4),
        ("2A", 5), ("2B", 6), ("2Y", 7), ("GND", 8),
        ("3Y", 9), ("3B", 10), ("3A", 11), ("4Y", 12),
        ("4B", 13), ("4A", 14), ("/G", 15), ("VCC", 16),
    }

    circuit = json.loads((ROOT / "examples" / "circuits" / "RV8GR_AddressMux16" / "circuit.json").read_text(encoding="utf-8"))
    assert {chip["part"] for chip in circuit["chips"]} == {"74HC157"}
    live_pins = {pin for _port, pin in fixture_ports}
    address_mux_pins = {
        int(connection.rsplit(".", 1)[1])
        for wire in circuit["wiring"]
        for connection in wire["connections"]
        if connection.startswith(("U15.", "U16.", "U29.", "U30."))
    }
    assert address_mux_pins == live_pins


def main() -> None:
    test_counter_fixture_has_ast_to_resolved_topology_pipeline()
    test_text_ide_snapshot_is_parse_resolve_validate_not_runtime()
    test_resolver_reports_unknown_port_and_scalar_bus_without_guessing()
    test_component_ide_cli_emits_both_contracts()
    test_runtime_instantiates_resolved_inverter_and_reads_probe()
    test_checked_golden_pipeline_has_stable_spans_and_resolved_contract()
    test_resolved_cli_is_hash_seed_deterministic()
    test_leaf_validation_rejects_power_misuse_and_multiple_outputs()
    test_leaf_resolver_requires_real_imports_and_a_single_local_namespace()
    test_leaf_resolver_rejects_alias_that_claims_the_wrong_library()
    test_leaf_resolver_rejects_zero_width_self_wiring_and_net_aliases()
    test_leaf_resolver_keeps_quoted_datasheet_port_names_exact()
    test_mux_fixture_and_rv8gr_address_mux_keep_the_live_74hc157_pin_contract()
    print("Components Component-language tests passed")


if __name__ == "__main__":
    main()
