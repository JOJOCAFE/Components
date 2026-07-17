# Board v2 Headless Harness — Fern Verification Specification

Status: required verification contract for Gate 0 B0.2, B0.3, and B0.4. This
specification defines the evidence that the future headless harness must
produce. It does not authorize a Board implementation change, a browser test
substitute, or a product-performance claim.

The normative architecture is
[`BOARD_ARCHITECTURE_FREEZE.md`](BOARD_ARCHITECTURE_FREEZE.md), and the task
sequence is [`BOARD_V2_SPRINT_PLAN.md`](BOARD_V2_SPRINT_PLAN.md). The harness
must run with no GUI, browser, network service, wall-clock-dependent fixture,
or screen-coordinate input.

## Required command and exit behavior

The harness command is:

```sh
PYTHONPATH=python python3 -B -m tests.test_board_v2_harness
```

It must exit zero only when every required fixture, negative case,
determinism comparison, and enabled regression threshold passes. It must exit
nonzero for any failed check, missing required field, malformed threshold
record, missing baseline when thresholds are enabled, or attempted direct
mutation. A failure must still emit one complete JSON report to stdout or to a
documented output path so CI can retain the specific reason.

The final B0/B5 focused exit set, once Bam lands the harness, is:

```sh
BOARD_V2_HARNESS_ITERATIONS=25 BOARD_V2_HARNESS_WARMUP_ITERATIONS=5 BOARD_V2_HARNESS_ENFORCE_THRESHOLDS=1 PYTHONPATH=python python3 -B -m chiplib.board_v2_harness
PYTHONPATH=python python3 -B -m tests.test_board_v2_harness
PYTHONPATH=python python3 -B -m tests.test_component_board_api
PYTHONPATH=python python3 -B -m tests.test_component_language
```

All four commands must pass; this is deliberately separate from human
first-sight trials.

## Harness JSON result contract

The top-level result must be JSON with these required fields. All digest
fields use lowercase `sha256:<64 lowercase hex characters>` values.

```json
{
  "schema": "components.board-v2-harness-result@1",
  "harness_version": "...",
  "result": "pass | fail",
  "run_mode": "baseline | regression",
  "fixture_results": [],
  "negative_results": [],
  "determinism": {},
  "threshold_evaluation": {},
  "environment": {},
  "failure_count": 0,
  "failures": []
}
```

`environment` is required for benchmark interpretation, but is excluded from
deterministic export comparisons. It records at least `python_version`,
`implementation`, `platform`, `machine`, `processor`, `cpu_count`, and the
monotonic clock name/resolution. It must contain no user name, home path,
random UUID, or wall-clock value in the canonical export payload.

Every entry in `fixture_results` requires:

```json
{
  "fixture_id": "not-gate | chain-4 | dense-16x32",
  "source_revision": "sha256:...",
  "topology_digest": "sha256:...",
  "resource_binding_digest": "sha256:...",
  "profile_input_version": 1,
  "profile_output_version": 2,
  "projection_digest": "sha256:...",
  "export_digest": "sha256:...",
  "export_bytes": 0,
  "operation_ids": ["..."],
  "checks": [],
  "measurements": {},
  "result": "pass | fail",
  "failures": []
}
```

`checks` must name and report `fixture_integrity`, `projection`,
`profile_validation_or_migration`, `queue_dependency`, `source_ownership`,
and `deterministic_export`. `measurements` must carry integer nanosecond
sample arrays plus `iterations`, `median_ns`, and `p95_ns` for
`load_resolve_projection`, `profile_migration`, and `queue_validate_apply`;
it must also carry `export_bytes`. All durations are non-negative integers.

`operation_ids` are semantic, stable IDs from the fixture/operation generator.
They must not be raw pointer events, timestamps, random IDs, or hashes that
depend on map iteration order. Each operation result must expose its one
authority target (`component_source`, `board_profile`, or `runtime`) and its
expected source revision or topology digest.

Each `negative_results` entry requires `case_id`, `category`, `input_digest`,
`result`, `expected_failure_code`, `observed_failure_code`, `source_unchanged`,
`topology_unchanged`, `profile_unchanged`, and `message`. A negative case
passes only when it is rejected for its expected code and all applicable
unchanged flags are true.

`determinism` requires `runs_per_fixture`, `canonical_export_digests`,
`cross_hash_seed_digests`, `stable`, and `comparison_scope`. It compares the
canonical Board/profile/operation export only; measurement values and machine
metadata must not be included in that byte stream.

`threshold_evaluation` requires `enabled`, `threshold_record_digest`,
`baseline_id`, `result`, and one per-fixture/per-measurement decision. In
`baseline` mode it may be disabled, but it must explicitly say why. In
`regression` mode it is required and cannot silently warn-pass.

## Mandatory positive and negative cases

Run the three Gate 0 fixtures: `not-gate`, `chain-4`, and `dense-16x32`. The
harness must show the exact checked fixture/source/topology/resource digests;
a fixture whose expected digest changes is not a benchmark continuation until
its fixture review is explicit.

The negative corpus must include at least these intentional rejections:

| Case ID | Required failure category | Required preserved state |
| --- | --- | --- |
| `stale-profile-digest` | profile digest differs from resolved topology | source, topology, profile |
| `invalid-world-point` | NaN, infinity, or invalid world coordinate/coordinate-space metadata | source, topology, profile |
| `forbidden-direct-mutation` | Board attempts source/topology/profile mutation without an operation result | source, topology, profile |
| `route-before-connect` | dependent Board route precedes its source `connect` edge | source, topology, profile |
| `unknown-edge-route` | route references no resolved scalar edge | source, topology, profile |
| `bus-route-without-contract` | bus/bus-bit visual route is requested before an explicit bus-route contract | source, topology, profile |
| `malformed-profile-migration` | invalid or unsupported v1 profile cannot migrate | source, topology, profile |
| `stale-source-operation` | source operation revision differs from current source | source, topology, profile |

At least one passing transaction must prove the ordering `connect` source
operation → resolve/topology digest refresh → dependent scalar Board route.
Its export must demonstrate that a viewport pan/zoom change is absent from the
Board profile digest. A failed source operation must block its dependent route
rather than retarget it.

## Determinism criteria

For each fixture, run the full projection/migration/queue/export sequence at
least three times in one process and once each with `PYTHONHASHSEED=0` and
`PYTHONHASHSEED=1`. The following must be byte-identical across comparisons:

- canonical exported Board profile;
- canonical operation order and operation IDs;
- source revision, topology digest, projection digest, and export digest; and
- failure codes and preserved-state flags for each negative input.

Sort maps and collections where their order has no semantic meaning. Preserve
declared source and explicitly ordered operation sequences. Never compare raw
duration samples for determinism. A mismatch is a hard failure with the first
different field/path in `failures`.

## Baseline collection protocol (B0.3 before B0.4)

1. Start from a clean checkout with the fixture and threshold files tracked;
   record `git_revision` and confirm no harness/fixture changes are unstaged.
2. Disable network-dependent work and background benchmark services as far as
   practical. Record environment metadata; do not claim that it represents
   student hardware.
3. Run five unrecorded warm-up iterations per fixture, then record at least
   25 measured iterations per fixture in the same command invocation using a
   monotonic nanosecond clock.
4. Retain every raw sample, calculate median and nearest-rank p95 from the
   retained samples, and retain the canonical/export digests produced during
   the run.
5. Repeat the deterministic hash-seed checks. A baseline with an unstable
   export is invalid regardless of its timings.
6. Commit the resulting baseline evidence and a reviewed threshold record
   together. Only then may regression mode enforce thresholds in CI.

An interrupted run, a fixture-digest mismatch, fewer than 25 samples, or any
failed negative case is invalid baseline evidence and must not update a
threshold.

## Threshold record format (B0.4)

Store a tracked JSON record beside the future harness, for example
`python/tests/data/board_v2/thresholds.json`. Its required format is:

```json
{
  "schema": "components.board-v2-regression-thresholds@1",
  "policy_id": "board-v2-gate0-initial",
  "baseline": {
    "baseline_id": "...",
    "evidence_digest": "sha256:...",
    "git_revision": "...",
    "fixture_digests": {"not-gate": "sha256:..."},
    "environment": {"python_version": "...", "platform": "..."},
    "iterations": 25,
    "warmup_iterations": 5
  },
  "limits": {
    "not-gate": {
      "load_resolve_projection": {"baseline_median_ns": 0, "baseline_p95_ns": 0, "max_p95_ns": 0},
      "profile_migration": {"baseline_median_ns": 0, "baseline_p95_ns": 0, "max_p95_ns": 0},
      "queue_validate_apply": {"baseline_median_ns": 0, "baseline_p95_ns": 0, "max_p95_ns": 0},
      "max_export_bytes": 0
    }
  },
  "review": {"fern_reviewed": false, "review_reference": "", "change_reason": ""},
  "claim_boundary": "Regression guard for this checked baseline; not a cross-machine product latency, responsiveness, startup, memory, or learner-experience target."
}
```

There must be a limit entry for each of the three fixtures and each required
measurement. Initial `max_p95_ns` values are set only from the recorded
baseline with conservative slack chosen and documented in `change_reason`.
`max_export_bytes` guards accidental output growth and is not a memory-use
claim. A threshold change requires a new checked baseline or an explicit
fixture-contract change, a non-empty reason, and `fern_reviewed: true` with a
review reference. CI rejects missing, stale, malformed, or unreviewed records
when regression enforcement is enabled.

## No-claim rules

A passing harness proves only deterministic headless behavior for the checked
fixtures and environment. It does **not** prove browser frame rate, pointer
latency, viewport accessibility, startup time, mobile/iOS behavior, memory
use, student comprehension, electrical correctness beyond the resolver,
breadboard safety, PCB routing, physical timing, or scalability beyond the
three fixtures. The report and threshold record must use “regression guard” or
“measured baseline”, never “product target”, “real-time guarantee”, or
physical-signoff wording.
