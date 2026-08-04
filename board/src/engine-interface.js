/**
 * Components Board — Engine Interface
 *
 * THE boundary between Board (thin client) and Components engine.
 * Board imports ONLY this module for circuit state and mutations.
 *
 * Phase A: backed by engine-mock.js (local JS, synchronous under async API)
 * Phase B: swap to HTTP/WebSocket/WASM adapter (zero Board code changes)
 *
 * Contract: board/src/engine-interface.md
 */

// =============================================================================
// INTERFACE FACTORY
// =============================================================================

/**
 * Create an EngineInterface instance.
 *
 * @param {object} adapter — implementation backend
 * @param {function} adapter.getState — () => EngineState
 * @param {function} adapter.submit — (operation) => Promise<OperationResult>
 * @param {function} adapter.submitBatch — (operations[]) => Promise<BatchResult>
 * @returns {object} frozen EngineInterface
 */
export function createEngineInterface(adapter) {
  if (!adapter || typeof adapter.getState !== 'function') {
    throw new Error('EngineInterface requires adapter with getState()');
  }
  if (typeof adapter.submit !== 'function') {
    throw new Error('EngineInterface requires adapter with submit()');
  }

  const listeners = new Set();

  // --- State queries (synchronous — reads cached/local state) ---

  function getState() {
    return adapter.getState();
  }

  function getDevices() {
    return getState().devices;
  }

  function getEdges() {
    return getState().edges;
  }

  function getSourceText() {
    return getState().sourceText;
  }

  function getSourceRevision() {
    return getState().sourceRevision;
  }

  function getTopologyDigest() {
    return getState().topologyDigest;
  }

  function getDiagnostics() {
    return getState().diagnostics;
  }

  // --- Mutations (async — may be network in Phase B) ---

  async function submit(operation) {
    // Inject current revision/digest if not already set
    const op = {
      format: 'components.component-operation@1',
      source_revision: getSourceRevision(),
      topology_digest: getTopologyDigest(),
      ...operation,
    };
    const result = await adapter.submit(op);
    if (result.ok) {
      _notifyListeners();
    }
    return result;
  }

  async function submitBatch(operations) {
    // For batch, we let the adapter handle revision per-op
    // Each op gets current revision at submit time (adapter handles sequencing)
    const ops = operations.map(op => ({
      format: 'components.component-operation@1',
      ...op,
      // Don't stamp revision here — adapter.submitBatch handles it per-step
    }));
    const result = await adapter.submitBatch(ops);
    if (result.ok) {
      _notifyListeners();
    }
    return result;
  }

  // --- Reactive updates ---

  function onStateChange(callback) {
    listeners.add(callback);
    return () => listeners.delete(callback);
  }

  function _notifyListeners() {
    const state = getState();
    for (const cb of listeners) {
      try { cb(state); } catch (e) { /* listener errors don't break engine */ }
    }
  }

  // --- Public API ---

  return Object.freeze({
    getState,
    getDevices,
    getEdges,
    getSourceText,
    getSourceRevision,
    getTopologyDigest,
    getDiagnostics,
    submit,
    submitBatch,
    onStateChange,
  });
}
