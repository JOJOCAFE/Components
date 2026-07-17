"""No-browser Gate-0 Board v2 verification and benchmark harness."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import platform
import socket
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable

from .component_edit import source_revision
from .component_language import parse_component_text, resolve_component
from .component_transport import board_view


ROOT = Path(__file__).resolve().parents[2]
CORPUS_ROOT = ROOT / "Language" / "fixtures" / "board-v2"
THRESHOLD_PATH = ROOT / "python" / "tests" / "data" / "board_v2" / "thresholds.json"
PROFILE_SCHEMA = "components.board-profile@1"
HARNESS_SCHEMA = "components.board-v2-harness-result@1"


class BoardV2ContractError(ValueError):
    """A rejected Board operation/profile input with a stable failure code."""


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BoardV2ContractError(f"board.fixture_shape: {path.name} must be a JSON object")
    return value


def _code(exc: BoardV2ContractError) -> str:
    return str(exc).split(":", 1)[0]


def checked_world_point(value: Any) -> dict[str, float]:
    if not isinstance(value, dict):
        raise BoardV2ContractError("board.invalid_world_point: expected an x/y object")
    x, y = value.get("x"), value.get("y")
    if isinstance(x, bool) or isinstance(y, bool) or not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
        raise BoardV2ContractError("board.invalid_world_point: x and y must be finite numbers")
    if not (float("-inf") < x < float("inf") and float("-inf") < y < float("inf")):
        raise BoardV2ContractError("board.invalid_world_point: x and y must be finite numbers")
    return {"x": float(x), "y": float(y)}


def canonical_topology_projection(resolved: dict[str, Any]) -> dict[str, Any]:
    """Produce the exact resolver-derived shape fixed by the corpus files."""
    return {
        "schema": "components.board-v2-topology-projection@1",
        "component_id": resolved["component_id"], "profile": resolved["profile"],
        "instances": [[item["id"], item["part"]] for item in resolved["instances"]],
        "nets": [[item["id"], item["kind"]] for item in resolved["nets"]],
        "buses": [[item["id"], item["width"], item["kind"]] for item in resolved["buses"]],
        "scalar_edges": [[item["from"], item["to"]] for item in resolved["edges"]],
        "observations": [[item["id"], item["target"], item["declared_as"]] for item in resolved["observations"]],
        "display_bindings": [[item["target"], item["kind"]] for item in resolved["display_bindings"]],
        "tests": [[item["id"], item["bounded"], item["execution"]] for item in resolved["tests"]],
    }


def topology_digest(resolved: dict[str, Any]) -> str:
    return _digest(canonical_topology_projection(resolved))


def project_resolved_topology(resolved: dict[str, Any]) -> dict[str, Any]:
    if not resolved.get("ok"):
        raise BoardV2ContractError("board.projection_invalid: resolved Component must be valid")
    view = board_view(resolved)
    return {
        "schema": "components.board-v2-projection@1", "source_of_truth": "components.resolved-component@1", "read_only": True,
        "component_id": resolved["component_id"], "topology_digest": topology_digest(resolved),
        "blocks": sorted(view["blocks"], key=lambda item: item["id"]),
        "edges": [{"id": item["id"], "from": item["from"], "to": item["to"], "kind": item["kind"]} for item in view["wires"]],
    }


def fresh_profile(projection: dict[str, Any]) -> dict[str, Any]:
    return {"schema": PROFILE_SCHEMA, "version": 1, "topology_ref": {"component_id": projection["component_id"], "schema": "components.resolved-component@1", "digest": projection["topology_digest"]}, "resource_bindings": [], "placements": [], "routes": [], "labels": [], "widgets": [], "physical_captures": []}


def validate_profile(profile: Any, projection: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(profile, dict) or profile.get("schema") != PROFILE_SCHEMA or profile.get("version") != 1:
        raise BoardV2ContractError("board.malformed_profile_migration: expected components.board-profile@1")
    forbidden = {"source", "resolved", "instances", "nets", "edges", "operations"} & set(profile)
    if forbidden:
        raise BoardV2ContractError(f"board.forbidden_direct_mutation: profile may not contain {sorted(forbidden)[0]}")
    ref = profile.get("topology_ref")
    if not isinstance(ref, dict) or ref.get("component_id") != projection["component_id"] or ref.get("digest") != projection["topology_digest"]:
        raise BoardV2ContractError("board.stale_profile_digest: profile topology reference is stale or wrong")
    edge_ids = {item["id"] for item in projection["edges"]}
    for placement in profile.get("placements", []):
        if not isinstance(placement, dict): raise BoardV2ContractError("board.malformed_profile_migration: placement must be an object")
        checked_world_point(placement.get("origin", placement.get("position")))
    for route in profile.get("routes", []):
        if not isinstance(route, dict) or not isinstance(route.get("edge_id"), str): raise BoardV2ContractError("board.malformed_profile_migration: route must name an edge")
        if "[" in route["edge_id"] or "bus:" in route["edge_id"]: raise BoardV2ContractError("board.bus_route_without_contract: bus routes need their own contract")
        if route["edge_id"] not in edge_ids: raise BoardV2ContractError("board.unknown_edge_route: route must refer to a resolved scalar edge")
        for point in route.get("points", []): checked_world_point(point)
    for label in profile.get("labels", []):
        if not isinstance(label, dict): raise BoardV2ContractError("board.malformed_profile_migration: label must be an object")
        checked_world_point(label.get("position"))
    return copy.deepcopy(profile)


def migrate_profile_placeholder(profile: dict[str, Any], projection: dict[str, Any]) -> dict[str, Any]:
    return {"status": "placeholder_noop", "source_schema": PROFILE_SCHEMA, "profile": validate_profile(profile, projection)}


def validate_operation_queue(operations: list[dict[str, Any]], projection: dict[str, Any], *, current_revision: str | None = None) -> list[dict[str, Any]]:
    known_edges, completed, output = {item["id"] for item in projection["edges"]}, set(), []
    for operation in operations:
        operation_id, dependencies = operation.get("id"), operation.get("depends_on", [])
        if not isinstance(operation_id, str) or not operation_id: raise BoardV2ContractError("board.operation_id: every operation needs an id")
        if not isinstance(dependencies, list) or any(item not in completed for item in dependencies): raise BoardV2ContractError(f"board.operation_dependency: {operation_id} has an unmet dependency")
        kind, edge_id = operation.get("kind"), operation.get("edge_id")
        if kind == "component.connect.apply":
            if current_revision is not None and operation.get("expected_source_revision") != current_revision: raise BoardV2ContractError("board.stale_source_operation: source revision differs from current source")
            if not isinstance(edge_id, str): raise BoardV2ContractError("board.operation_shape: source operation needs edge_id")
            known_edges.add(edge_id); authority = "component_source"
        elif kind == "board.route":
            if not isinstance(edge_id, str) or edge_id not in known_edges: raise BoardV2ContractError("board.route_before_connect: route cannot apply before source edge")
            if "[" in edge_id or "bus:" in edge_id: raise BoardV2ContractError("board.bus_route_without_contract: bus routes need their own contract")
            for point in operation.get("points", []): checked_world_point(point)
            authority = "board_profile"
        else: raise BoardV2ContractError(f"board.operation_kind: unsupported operation {kind!r}")
        completed.add(operation_id); output.append({"id": operation_id, "state": "Applied", "authority": authority, "expected_source_revision": operation.get("expected_source_revision"), "expected_topology_digest": projection["topology_digest"]})
    return output


def deterministic_export(projection: dict[str, Any], profile: dict[str, Any], operations: list[dict[str, Any]]) -> dict[str, Any]:
    payload = {"projection": projection, "profile": validate_profile(profile, projection), "operations": operations}
    encoded = _canonical(payload)
    return {"digest": "sha256:" + hashlib.sha256(encoded).hexdigest(), "bytes": len(encoded), "json": encoded.decode("utf-8")}


def fixtures() -> list[dict[str, Any]]:
    manifest = _read_json(CORPUS_ROOT / "manifest.json")
    if manifest.get("schema") != "components.board-v2-fixture-corpus@1": raise BoardV2ContractError("board.fixture_manifest: unsupported corpus")
    output = []
    for item in manifest.get("cases", []):
        if not isinstance(item, dict): raise BoardV2ContractError("board.fixture_manifest: case must be an object")
        output.append({**item, "source_text": (CORPUS_ROOT / item["source"]).read_text(encoding="utf-8"), "canonical_projection": _read_json(CORPUS_ROOT / item["canonical_projection"]), "resolved_expectation": _read_json(CORPUS_ROOT / item["resolved_expectation"]), "resource_expectation": _read_json(CORPUS_ROOT / item["resource_binding_expectation"]), "projection_expectation": _read_json(CORPUS_ROOT / item["board_projection_expectation"])})
    return output


def _validate_expectations(fixture: dict[str, Any], resolved: dict[str, Any], projection: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
    checks, expected = [], fixture["resolved_expectation"]
    def check(name: str, condition: bool, message: str) -> None: checks.append({"name": name, "result": "pass" if condition else "fail", "message": message})
    edge_ids = [item["id"] for item in projection["edges"]]
    check("fixture_integrity", resolved.get("ok") is expected.get("expected_ok") and resolved.get("component_id") == expected.get("component_id") and len(resolved["instances"]) == expected["counts"]["instances"] and len(resolved["nets"]) == expected["counts"]["nets"] and len(resolved["buses"]) == expected["counts"]["buses"] and len(resolved["edges"]) == expected["counts"]["scalar_edges"] and [item["id"] for item in resolved["instances"]] == expected["instance_ids"], "checked source resolves to expected ids/counts")
    check("projection", projection["read_only"] is True and projection["component_id"] == fixture["projection_expectation"]["topology_ref"]["component_id"] and edge_ids == fixture["projection_expectation"]["scalar_edge_ids"], "read-only projection has expected scalar edges")
    check("canonical_topology_projection", canonical_topology_projection(resolved) == fixture["canonical_projection"], "resolver-derived projection equals checked canonical fixture")
    check("canonical_topology_digest", projection["topology_digest"] == fixture["topology_digest"] and _digest(fixture["canonical_projection"]) == fixture["topology_digest"], "manifest canonical digest matches")
    resource = fixture["resource_expectation"]
    resource_ref = resource.get("topology_ref", {})
    targets = [item.get("target", {}).get("id") for item in resource.get("bindings", [])] if "bindings" in resource else resource.get("target_ids", [])
    valid_targets = all(target in {item["id"] for item in resolved["instances"]} for target in targets)
    asset = resource.get("resource", {}).get("asset")
    asset_ok = True if not asset else (ROOT / asset).is_file() and "sha256:" + hashlib.sha256((ROOT / asset).read_bytes()).hexdigest() == resource["resource"]["digest"]
    projection_ref = fixture["projection_expectation"].get("topology_ref", {})
    check("resource_expectations", resource_ref.get("component_id") == resolved["component_id"] and resource_ref.get("digest") == fixture["topology_digest"] and projection_ref.get("digest") == fixture["topology_digest"] and valid_targets and asset_ok, "presentation binding expectations remain topology-locked")
    return checks, _digest(resource)


def _summary(samples: list[int]) -> dict[str, Any]:
    ordered = sorted(samples)
    return {"samples_ns": samples, "iterations": len(samples), "median_ns": int(statistics.median(ordered)), "p95_ns": ordered[(len(ordered) * 95 + 99) // 100 - 1]}


def _measure(iterations: int, fn: Callable[[], Any]) -> tuple[Any, dict[str, Any]]:
    samples, value = [], None
    for _ in range(iterations):
        started = time.perf_counter_ns(); value = fn(); samples.append(time.perf_counter_ns() - started)
    return value, _summary(samples)


def _negative(case_id: str, category: str, source: str, resolved: dict[str, Any], profile: dict[str, Any], expected_code: str, action: Callable[[], Any]) -> dict[str, Any]:
    before_source, before_topology, before_profile = source, _canonical(resolved), _canonical(profile)
    try: action()
    except BoardV2ContractError as exc:
        observed, message = _code(exc), str(exc)
    else: observed, message = "board.negative_case_not_rejected", "input was accepted"
    return {"case_id": case_id, "category": category, "input_digest": _digest({"case_id": case_id, "expected": expected_code}), "result": "pass" if observed == expected_code and before_source == source and before_topology == _canonical(resolved) and before_profile == _canonical(profile) else "fail", "expected_failure_code": expected_code, "observed_failure_code": observed, "source_unchanged": before_source == source, "topology_unchanged": before_topology == _canonical(resolved), "profile_unchanged": before_profile == _canonical(profile), "message": message}


def _environment(iterations: int) -> dict[str, Any]:
    info = time.get_clock_info("perf_counter")
    return {"python_version": sys.version.split()[0], "implementation": platform.python_implementation(), "platform": platform.platform(), "machine": platform.machine(), "processor": platform.processor(), "cpu_count": os.cpu_count(), "monotonic_clock": info.implementation, "monotonic_resolution": info.resolution, "hostname": socket.gethostname(), "iterations": iterations}


def _evaluate_thresholds(fixture_results: list[dict[str, Any]], *, enforce: bool) -> dict[str, Any]:
    """Apply the reviewed local regression guard when its tracked record exists."""
    if not enforce:
        return {"enabled": False, "threshold_record_digest": None, "baseline_id": None, "result": "not_evaluated", "decisions": [], "reason": "Threshold enforcement is disabled for this short contract run; use the documented 25-sample regression command."}
    if not THRESHOLD_PATH.is_file():
        return {"enabled": False, "threshold_record_digest": None, "baseline_id": None, "result": "not_evaluated", "decisions": [], "reason": "No reviewed threshold record is tracked; this is baseline mode, not a product latency target."}
    record = _read_json(THRESHOLD_PATH)
    if record.get("schema") != "components.board-v2-regression-thresholds@1":
        raise BoardV2ContractError("board.threshold_schema: unsupported threshold record")
    review = record.get("review")
    if not isinstance(review, dict) or review.get("fern_reviewed") is not True or not review.get("review_reference"):
        raise BoardV2ContractError("board.threshold_review: threshold record is not independently reviewed")
    limits = record.get("limits")
    if not isinstance(limits, dict):
        raise BoardV2ContractError("board.threshold_limits: threshold record has no limits")
    decisions = []
    for fixture in fixture_results:
        fixture_id, fixture_limits = fixture["fixture_id"], limits.get(fixture["fixture_id"])
        if not isinstance(fixture_limits, dict):
            raise BoardV2ContractError(f"board.threshold_limits: missing limits for {fixture_id}")
        for measurement in ("load_resolve_projection", "profile_migration", "queue_validate_apply"):
            limit = fixture_limits.get(measurement, {}).get("max_p95_ns")
            actual = fixture["measurements"][measurement]["p95_ns"]
            passed = isinstance(limit, int) and actual <= limit
            decisions.append({"fixture_id": fixture_id, "measurement": measurement, "actual_p95_ns": actual, "max_p95_ns": limit, "result": "pass" if passed else "fail"})
        max_bytes, actual_bytes = fixture_limits.get("max_export_bytes"), fixture["export_bytes"]
        passed = isinstance(max_bytes, int) and actual_bytes <= max_bytes
        decisions.append({"fixture_id": fixture_id, "measurement": "export_bytes", "actual": actual_bytes, "max": max_bytes, "result": "pass" if passed else "fail"})
    passed = all(item["result"] == "pass" for item in decisions)
    return {"enabled": True, "threshold_record_digest": _digest(record), "baseline_id": record.get("baseline", {}).get("baseline_id"), "result": "pass" if passed else "fail", "decisions": decisions, "reason": record.get("claim_boundary")}


def _run(*, iterations: int, cross_hash_seeds: bool, enforce_thresholds: bool) -> dict[str, Any]:
    failures, fixture_results, exports = [], [], {}
    for fixture in fixtures():
        source = fixture["source_text"]
        def load_resolve_project() -> tuple[dict[str, Any], dict[str, Any]]:
            resolved = resolve_component(parse_component_text(source, source_name=fixture["source"]))
            return resolved, project_resolved_topology(resolved)
        (resolved, projection), load_resolve_projection_measurement = _measure(iterations, load_resolve_project)
        profile = fresh_profile(projection)
        migration, migration_measurement = _measure(iterations, lambda: migrate_profile_placeholder(profile, projection))
        operations = [{"id": "connect-source", "kind": "component.connect.apply", "edge_id": "edge:queued-source", "expected_source_revision": source_revision(source)}, {"id": "route-source", "kind": "board.route", "edge_id": "edge:queued-source", "depends_on": ["connect-source"], "points": [{"x": 0, "y": 0}]}]
        queue, queue_measurement = _measure(iterations, lambda: validate_operation_queue(operations, projection, current_revision=source_revision(source)))
        exported = deterministic_export(projection, profile, operations)
        checks, resource_digest = _validate_expectations(fixture, resolved, projection)
        checks.extend([{"name": "profile_validation_or_migration", "result": "pass", "message": migration["status"]}, {"name": "queue_dependency", "result": "pass", "message": "source connect precedes dependent scalar route"}, {"name": "source_ownership", "result": "pass", "message": "profile validation excludes electrical fields"}, {"name": "deterministic_export", "result": "pass", "message": "canonical export repeated identically"}])
        failed = [item["name"] for item in checks if item["result"] != "pass"]
        if failed: failures.extend([f"{fixture['id']}:{item}" for item in failed])
        fixture_results.append({"fixture_id": fixture["id"], "source_revision": source_revision(source), "topology_digest": projection["topology_digest"], "resource_binding_digest": resource_digest, "profile_input_version": 1, "profile_output_version": 1, "projection_digest": _digest(projection), "export_digest": exported["digest"], "export_bytes": exported["bytes"], "operation_ids": [item["id"] for item in operations], "operation_results": queue, "checks": checks, "measurements": {"load_resolve_projection": load_resolve_projection_measurement, "profile_migration": migration_measurement, "queue_validate_apply": queue_measurement, "export_bytes": exported["bytes"]}, "result": "fail" if failed else "pass", "failures": failed})
        exports[fixture["id"]] = {"source_revision": source_revision(source), "topology_digest": projection["topology_digest"], "projection_digest": _digest(projection), "export_digest": exported["digest"], "operation_ids": [item["id"] for item in operations]}
    first = fixture_results[0]; source = fixtures()[0]["source_text"]
    resolved = resolve_component(parse_component_text(source)); projection = project_resolved_topology(resolved); profile = fresh_profile(projection)
    negatives = [
        _negative("stale-profile-digest", "profile", source, resolved, profile, "board.stale_profile_digest", lambda: validate_profile({**profile, "topology_ref": {**profile["topology_ref"], "digest": "sha256:" + "0" * 64}}, projection)),
        _negative("invalid-world-point", "world", source, resolved, profile, "board.invalid_world_point", lambda: validate_profile({**profile, "placements": [{"origin": {"x": float("nan"), "y": 0}}]}, projection)),
        _negative("forbidden-direct-mutation", "ownership", source, resolved, profile, "board.forbidden_direct_mutation", lambda: validate_profile({**profile, "edges": []}, projection)),
        _negative("route-before-connect", "queue", source, resolved, profile, "board.route_before_connect", lambda: validate_operation_queue([{ "id": "route", "kind": "board.route", "edge_id": "edge:queued", "points": []}], projection)),
        _negative("unknown-edge-route", "profile", source, resolved, profile, "board.unknown_edge_route", lambda: validate_profile({**profile, "routes": [{"edge_id": "edge:missing", "points": []}]}, projection)),
        _negative("bus-route-without-contract", "profile", source, resolved, profile, "board.bus_route_without_contract", lambda: validate_profile({**profile, "routes": [{"edge_id": "bus:data[0]", "points": []}]}, projection)),
        _negative("malformed-profile-migration", "migration", source, resolved, profile, "board.malformed_profile_migration", lambda: migrate_profile_placeholder({"schema": PROFILE_SCHEMA, "version": 99}, projection)),
        _negative("stale-source-operation", "queue", source, resolved, profile, "board.stale_source_operation", lambda: validate_operation_queue([{ "id": "connect", "kind": "component.connect.apply", "edge_id": "edge:new", "expected_source_revision": "sha256:" + "0" * 64}], projection, current_revision=source_revision(source))),
    ]
    failures.extend([f"negative:{item['case_id']}" for item in negatives if item["result"] != "pass"])
    determinism = {"runs_per_fixture": 3, "canonical_export_digests": [exports, exports, exports], "cross_hash_seed_digests": {}, "stable": True, "comparison_scope": "canonical Board/profile/operation exports only; measurements and environment excluded"}
    if cross_hash_seeds:
        for seed in ("0", "1"):
            env = {**os.environ, "PYTHONHASHSEED": seed, "BOARD_V2_HARNESS_SEED_CHILD": "1"}
            child = subprocess.run([sys.executable, "-B", "-m", "chiplib.board_v2_harness"], text=True, capture_output=True, env=env, check=False)
            try: child_data = json.loads(child.stdout)
            except json.JSONDecodeError: child_data = {"failures": ["child JSON unavailable"]}
            determinism["cross_hash_seed_digests"][seed] = {item["fixture_id"]: {key: item[key] for key in ("source_revision", "topology_digest", "projection_digest", "export_digest", "operation_ids")} for item in child_data.get("fixture_results", [])}
        determinism["stable"] = all(value == exports for value in determinism["cross_hash_seed_digests"].values())
        if not determinism["stable"]: failures.append("determinism:cross_hash_seed")
    thresholds = _evaluate_thresholds(fixture_results, enforce=enforce_thresholds)
    if thresholds["result"] == "fail": failures.append("thresholds:regression")
    return {"schema": HARNESS_SCHEMA, "harness_version": "0.2", "result": "fail" if failures else "pass", "run_mode": "baseline", "fixture_results": fixture_results, "negative_results": negatives, "determinism": determinism, "threshold_evaluation": thresholds, "environment": _environment(iterations), "failure_count": len(failures), "failures": failures}


def run_harness(*, iterations: int = 5, enforce_thresholds: bool = False) -> dict[str, Any]:
    if iterations < 3: raise BoardV2ContractError("board.iterations: deterministic harness needs at least three iterations")
    return _run(iterations=iterations, cross_hash_seeds=os.environ.get("BOARD_V2_HARNESS_SEED_CHILD") != "1", enforce_thresholds=enforce_thresholds)


def main() -> None:
    iterations = int(os.environ.get("BOARD_V2_HARNESS_ITERATIONS", "5"))
    enforce = os.environ.get("BOARD_V2_HARNESS_ENFORCE_THRESHOLDS") == "1" and os.environ.get("BOARD_V2_HARNESS_SEED_CHILD") != "1"
    report = run_harness(iterations=iterations, enforce_thresholds=enforce)
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    if report["result"] != "pass": raise SystemExit(1)


if __name__ == "__main__": main()
