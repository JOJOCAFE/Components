# 10 — Harness Verification Spec

**Status:** Required evidence contract (Gate 0)
**Purpose:** What the headless harness must prove, no GUI required.

---

## Command

```bash
PYTHONPATH=python python3 -B -m tests.test_board_v2_harness
```

Exit 0 only when all fixtures, negatives, determinism, and thresholds pass.

## Regression Command

```bash
BOARD_V2_HARNESS_ITERATIONS=25 BOARD_V2_HARNESS_WARMUP_ITERATIONS=5 \
BOARD_V2_HARNESS_ENFORCE_THRESHOLDS=1 \
PYTHONPATH=python python3 -B -m tests.test_board_v2_harness
```

## Required Negative Cases

| Case | Category | Preserves |
|------|----------|-----------|
| stale-profile-digest | Digest mismatch | source, topology, profile |
| invalid-world-point | NaN/infinity | source, topology, profile |
| forbidden-direct-mutation | No operation result | source, topology, profile |
| route-before-connect | Dependency order | source, topology, profile |
| unknown-edge-route | No resolved edge | source, topology, profile |
| bus-route-without-contract | No bus contract | source, topology, profile |
| malformed-profile-migration | Invalid v1 | source, topology, profile |
| stale-source-operation | Wrong revision | source, topology, profile |

## Determinism

Run 3x in one process + PYTHONHASHSEED=0 and =1. Byte-identical:
- Canonical profile export
- Operation order and IDs
- Source revision, topology digest, projection digest, export digest
- Failure codes and flags for negatives

## Baseline Protocol

1. Clean checkout, no unstaged harness changes
2. Disable network work, record environment
3. 5 warmup + 25 measured iterations per fixture (monotonic ns clock)
4. Retain all samples, calculate median + p95
5. Verify hash-seed determinism
6. Commit baseline + reviewed threshold record together

## No-Claim Rules

Passing harness proves only deterministic headless behavior for checked
fixtures. NOT: browser frame rate, pointer latency, accessibility, startup,
mobile, memory, student comprehension, electrical correctness, breadboard
safety, PCB routing, physical timing, or scalability.
