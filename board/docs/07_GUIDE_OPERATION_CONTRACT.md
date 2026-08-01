# 07 — Guide Operation Contract

**Status:** Release candidate (2026-07-18)
**Purpose:** Frozen rule for the Guides interaction feature.

---

## Operation Shape

```json
{
  "schema": "components.operation@1",
  "kind": "board.guide.toggle",
  "authority": "board_session",
  "target": {"kind": "device-pin", "endpoint": "U1.1Y"},
  "topology_ref": {"digest": "sha256:..."}
}
```

Targets: one resolved device-instance, net, or device-pin.

## Frozen Rule

1. Find all declared scalar edges touching target
2. If every matching edge visible -> remove all
3. Otherwise -> add every matching edge ID
4. Saved routes drawn independently (this controls dashed guides only)

Click node = show group. Click again = hide. Another endpoint = toggle shared.

## Ownership

Authority: `board_session` only. Updates transient visibility set.
Never mutates source, topology, profile, or viewport.
Outside persisted profile. Not a Transaction Queue row (yet).

## Reuse

Future clients must reuse `board.guide.toggle` and `board/guide-operation.js`.
No parallel raw-click guide behavior.

## Evidence

```bash
node board/guide-operation.test.mjs
```
