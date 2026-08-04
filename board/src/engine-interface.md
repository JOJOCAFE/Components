# Board ↔ Engine Interface Contract

Status: design document for thin-client refactor (Bank-reviewed v2).
Date: 2026-08-04
Reviewer: Bank (architect)

## Principle

Board is a thin client. It owns ONLY visual state (`component:board`).
All circuit/electrical truth lives in the Components engine.
Board communicates with the engine via `component:operation` protocol.

Board never creates devices, nets, connections, or topology.
Board never parses `device`/`connect` syntax.
Board never generates circuit source text.

---

## 1. What Board READS from engine

Board receives a read-only projection of the Resolved Component.
This projection is the minimum Board needs to render and route.

```ts
interface EngineState {
  // --- Identity ---
  sourceRevision: string          // sha256 digest of current source text
  topologyDigest: string          // sha256 of resolved topology (immutable per revision)

  // --- Resolved devices (instances) ---
  devices: {
    [ref: string]: {
      ref: string                 // reference designator (U1, R3, etc.)
      part: string                // library identity (digital.74HC04)
      instanceId: string          // stable resolved ID (board-profile target)
      pins: {
        [name: string]: {
          direction: 'input' | 'output' | 'bidirectional' | 'power'
          type: 'digital' | 'power' | 'analog'
        }
      }
    }
  }

  // --- Resolved edges (scalar connections) ---
  edges: {
    id: string                    // stable edge ID (board route references this)
    from: string                  // pin ref (U1.1Y)
    to: string                    // pin ref (U2.1A)
    type: 'scalar' | 'bus'
  }[]

  // --- Source text (read-only display in editor) ---
  sourceText: string

  // --- Resolver diagnostics ---
  diagnostics: {
    severity: 'error' | 'warning' | 'info'
    message: string
    location?: { ref?: string, pin?: string, line?: number }
  }[]

  // --- Declared observations (for widget rendering) ---
  probes: { id: string, name: string, target: string }[]
  displays: { id: string, name: string, kind: string, config: object }[]
}
```

### Board uses these for:

| EngineState field | Board uses it for |
|---|---|
| `devices[ref].instanceId` | Board-profile placement `target.id` |
| `devices[ref].pins` | Pin label rendering, connect-tool validation |
| `edges[].id` | Board-profile route `edge_id` |
| `sourceRevision` | Operation revision check (stale detection) |
| `topologyDigest` | Board-profile `topology_ref.digest` |
| `sourceText` | Read-only editor display |
| `diagnostics` | Status bar, error markers |
| `probes`, `displays` | Widget placement targets |

---

## 2. What Board WRITES to engine (operations)

Board never directly mutates circuit state. It produces checked operations.

```ts
interface Operation {
  format: 'components.component-operation@1'
  kind: string                    // operation family (dot-separated)
  target: 'source' | 'runtime'   // authority target (board ops stay local)
  source_revision: string         // expected source digest (stale check)
  topology_digest: string         // expected topology digest
  intent: object                  // operation-specific payload
}
```

Engine rejects any operation where `source_revision` or `topology_digest`
does not match current state. Board must re-read state and retry or show
conflict to user.

### Source operations (circuit changes — engine validates + applies)

| Board gesture | Operation kind | Intent |
|---|---|---|
| Pin drag A→B (preview) | `component.connect.preview` | `{ from, to }` |
| Apply connect | `component.connect.apply` | `{ from, to }` |
| Tray add device | `component.add-device` | `{ ref, part }` |
| Delete device | `component.remove-device` | `{ ref }` |
| Disconnect | `component.disconnect` | `{ from, to }` |

### Board operations (visual-only — Board applies locally, no engine round-trip)

These are NOT sent to the engine. Board owns them directly:

| Board gesture | Local action | Persisted in |
|---|---|---|
| Drop at position | `setPlacement(ref, x, y, rotation)` | board-profile |
| Drag move | `setPlacement(ref, x, y, rotation)` | board-profile |
| Rotate | `setPlacement(ref, x, y, newAngle)` | board-profile |
| Draw route | `setRoute(edgeId, points)` | board-profile |
| Add label | `addLabel(text, x, y)` | board-profile |
| Pan/zoom | viewport state | session-local (not persisted) |

Board-profile operations reference only IDs that exist in the current
`EngineState`. If topology changes (device removed), Board marks affected
placements/routes stale rather than silently deleting them.

### Runtime operations (future — engine validates + applies)

| Action | Operation kind | Intent |
|---|---|---|
| Run test | `runtime.run-test` | `{ testName }` |
| Drive signal | `runtime.drive` | `{ net, value }` |
| Step | `runtime.step` | `{ count }` |
| Pulse clock | `runtime.pulse` | `{ clock, edges }` |

---

## 3. Engine API surface

```ts
interface EngineInterface {
  // --- State (read-only snapshot) ---
  getState(): EngineState
  
  // --- Mutations (async — may be network call in Phase B) ---
  submit(operation: Operation): Promise<OperationResult>
  submitBatch(operations: Operation[]): Promise<BatchResult>
  
  // --- Reactive updates ---
  onStateChange(callback: (state: EngineState) => void): () => void  // returns unsubscribe
  
  // --- Source text for editor (convenience, same as getState().sourceText) ---
  getSourceText(): string
}

interface OperationResult {
  ok: boolean
  operationId: string             // tracking ID
  error?: string                  // human-readable if !ok
  diagnostics?: Diagnostic[]      // resolver output after apply
  newState?: EngineState          // updated state (if ok)
  inverse?: Operation             // safe undo operation (if reversible)
}

interface BatchResult {
  ok: boolean                     // true only if ALL succeeded
  results: OperationResult[]      // one per submitted operation, in order
  // If a source op fails, subsequent dependent ops are not attempted
}
```

### Async contract

All mutations are `async` from day one. The mock resolves immediately
(synchronous under the hood), but the interface is async so Phase B
swap to HTTP/WebSocket requires zero Board code changes.

### Undo/Redo

- **Source undo**: `OperationResult.inverse` is a valid `Operation` that can
  be submitted to reverse the change. Board keeps an undo stack of inverses.
- **Board undo**: Board manages its own undo stack for visual operations
  (placement/route/label changes). These never touch the engine.

---

## 4. Pages decision

**Pages are Board-local visual grouping.** They are NOT part of the Component
source model. The engine knows nothing about pages.

- Board groups placements/routes/labels into pages for multi-sheet schematics
- Page structure lives in `component:board` profile only
- Source operations are page-agnostic (the engine sees one flat component)
- The editor UI may show page-filtered views of source text, but that's a
  Board display concern

---

## 5. Boundary rules (non-negotiable)

1. Board NEVER imports `model/component.js` directly
2. Board NEVER parses `device`/`connect`/`net`/`bus`/`probe` syntax
3. Board NEVER generates or serializes circuit source text
4. Board reads engine state ONLY through `EngineInterface.getState()`
5. Board changes circuit ONLY through `EngineInterface.submit(operation)`
6. Board MAY directly manage: placements, routes, labels, config, viewport, selection, pages
7. All operations carry `source_revision` + `topology_digest` for stale detection
8. Board-profile references (placement targets, route edge_ids) must exist in current EngineState
9. If topology changes invalidate board-profile refs, Board marks them stale (not silent delete)

---

## 6. Implementation phases

### Phase A (now): Extract interface + local mock

```
board/src/
  engine-interface.js       ← exports createEngineInterface() factory
  engine-mock.js            ← implements interface using local JS (temporary)
  model/board.js            ← Board owns (placements, routes, labels)
  model/config.js           ← Board owns
  model/library.js          ← Board owns (catalog UI)
  model/catalog-loader.js   ← Board owns (fetch for display)
  controller/parser.js      ← Board commands ONLY (place, move, route, label)
  controller/executor.js    ← Board state ONLY + delegates circuit ops via interface
  controller/tools.js       ← Board owns
  controller/select-tool.js ← Board owns
  controller/connect-tool.js ← Produces operations via interface
  controller/device-tray.js  ← Produces operations via interface
  controller/drag-place.js  ← Board owns
  controller/presentation.js ← Board owns
  controller/command-registry.js ← Board owns
  controller/sync.js        ← Board-editor sync only (page display)
  view/*                    ← Board owns

  [REMOVED]
  controller/twin-sync.js   ← deleted (engine serializes own source)
  model/component.js        ← moved inside engine-mock.js
  model/file.js             ← circuit parsing moved to engine-mock.js
                              board-line parsing (place/route/label) stays
```

Mock implementation:
- Wraps current `component.js` functions (addDevice, addConnection, etc.)
- Wraps current `file.js` circuit parser (parseCircuitLine, serializeDevice, etc.)
- Exposes same `EngineInterface` API
- `submit()` resolves synchronously (wrapped in Promise)
- Generates `sourceRevision` = sha256 of serialized source
- Generates `topologyDigest` = sha256 of canonical device+edge list
- Returns `inverse` for reversible operations

### Phase B (future): Real engine connection

- Replace `engine-mock.js` with HTTP/WebSocket adapter to Python Components engine
- Or: In-browser WASM parser/resolver
- Or: Node.js subprocess with JSON-RPC
- Board code unchanged — only import path for the interface implementation changes
- `createEngineInterface({ adapter: 'mock' | 'http' | 'wasm' })` factory pattern

---

## 7. Verification checklist (Fern)

After refactor:
- [ ] No Board module imports from `model/component.js`
- [ ] No Board module calls `parseCircuitLine` or `serializeDevice`
- [ ] No Board module calls `stateToCircuit` (old twin-sync)
- [ ] All circuit mutations go through `engine.submit()`
- [ ] All `submit()` calls include correct `source_revision` + `topology_digest`
- [ ] Board-profile placements/routes reference valid `instanceId`/`edge_id`
- [ ] Stale detection works: topology change → affected board-profile entries marked stale
- [ ] All existing tests pass (mock behaves identically to current code)
- [ ] New test: submit with wrong `source_revision` → rejected
- [ ] New test: submit with wrong `topology_digest` → rejected
