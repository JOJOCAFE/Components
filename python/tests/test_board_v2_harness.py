"""Focused no-browser checks for the Board v2 Gate-0 harness."""
from __future__ import annotations

import json

from chiplib.board_v2_harness import (
    BoardV2ContractError, canonical_topology_projection, deterministic_export,
    fixtures, fresh_profile, migrate_profile_placeholder, project_resolved_topology, run_harness,
    validate_operation_queue, validate_profile,
)
from chiplib.component_language import parse_component_text, resolve_component


_CACHED_REPORT: dict | None = None


def _report() -> dict:
    global _CACHED_REPORT
    if _CACHED_REPORT is None:
        _CACHED_REPORT = run_harness(iterations=3)
    return _CACHED_REPORT


def _projection():
    resolved = resolve_component(parse_component_text(fixtures()[0]["source_text"]))
    assert resolved["ok"], resolved["diagnostics"]
    return resolved, project_resolved_topology(resolved)


def test_corpus_is_consumed_and_canonical_projection_matches_every_case() -> None:
    assert [item["id"] for item in fixtures()] == ["not-gate", "chain-4", "dense-16x32"]
    for fixture in fixtures():
        resolved = resolve_component(parse_component_text(fixture["source_text"], source_name=fixture["source"]))
        assert resolved["ok"], resolved["diagnostics"]
        assert canonical_topology_projection(resolved) == fixture["canonical_projection"]


def test_harness_report_has_fern_shape_eight_negatives_and_disabled_short_run_thresholds() -> None:
    report = _report()
    assert report["schema"] == "components.board-v2-harness-result@1"
    assert report["result"] == "pass", report["failures"]
    assert report["failure_count"] == 0
    assert [item["fixture_id"] for item in report["fixture_results"]] == ["not-gate", "chain-4", "dense-16x32"]
    required_checks = {"fixture_integrity", "projection", "profile_validation_or_migration", "queue_dependency", "source_ownership", "deterministic_export"}
    for fixture in report["fixture_results"]:
        assert fixture["profile_input_version"] == 1
        assert fixture["profile_output_version"] == 2
        assert fixture["export_bytes"] > 0
        assert {item["name"] for item in fixture["checks"]} >= required_checks
        for measurement in ("load_resolve_projection", "profile_migration", "queue_validate_apply"):
            assert fixture["measurements"][measurement]["iterations"] == 3
            assert len(fixture["measurements"][measurement]["samples_ns"]) == 3
    assert {item["case_id"] for item in report["negative_results"]} == {"stale-profile-digest", "invalid-world-point", "forbidden-direct-mutation", "route-before-connect", "unknown-edge-route", "bus-route-without-contract", "malformed-profile-migration", "stale-source-operation"}
    assert all(item["result"] == "pass" and item["source_unchanged"] and item["topology_unchanged"] and item["profile_unchanged"] for item in report["negative_results"])
    assert report["determinism"]["stable"] is True
    assert report["environment"]["warmup_iterations"] == 0
    assert report["threshold_evaluation"]["enabled"] is False
    assert "disabled" in report["threshold_evaluation"]["reason"]


def test_bad_profile_and_route_before_connect_are_rejected_without_mutation() -> None:
    _resolved, projection = _projection(); profile = migrate_profile_placeholder(fresh_profile(projection), projection)["profile"]
    bad_digest = {**profile, "topology_ref": {**profile["topology_ref"], "digest": "sha256:wrong"}}
    try: validate_profile(bad_digest, projection)
    except BoardV2ContractError as exc: assert str(exc).startswith("board.stale_profile_digest:")
    else: raise AssertionError("bad digest must reject")
    try: validate_operation_queue([{ "id": "route", "kind": "board.route", "edge_id": "edge:not-yet", "points": []}], projection)
    except BoardV2ContractError as exc: assert str(exc).startswith("board.route_before_connect:")
    else: raise AssertionError("dependent route must reject before source edge")


def test_export_is_deterministic() -> None:
    _resolved, projection = _projection(); profile = migrate_profile_placeholder(fresh_profile(projection), projection)["profile"]
    operations = [{"id": "connect", "kind": "component.connect.apply", "edge_id": "edge:source", "expected_source_revision": "sha256:" + "0" * 64}]
    first, second = deterministic_export(projection, profile, operations), deterministic_export(projection, profile, operations)
    assert first["digest"] == second["digest"] and first["json"] == second["json"]


def test_warmups_are_recorded_but_not_in_measurement_samples() -> None:
    report = run_harness(iterations=3, warmup_iterations=2)
    assert report["result"] == "pass", report["failures"]
    assert report["environment"]["warmup_iterations"] == 2
    for fixture in report["fixture_results"]:
        for measurement in ("load_resolve_projection", "profile_migration", "queue_validate_apply"):
            assert fixture["measurements"][measurement]["iterations"] == 3
            assert len(fixture["measurements"][measurement]["samples_ns"]) == 3


def main() -> None:
    test_corpus_is_consumed_and_canonical_projection_matches_every_case()
    test_harness_report_has_fern_shape_eight_negatives_and_disabled_short_run_thresholds()
    test_bad_profile_and_route_before_connect_are_rejected_without_mutation()
    test_export_is_deterministic()
    print(json.dumps(_report(), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
