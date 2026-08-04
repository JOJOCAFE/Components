// TEMPORARY MOCK — will be replaced by real Components engine adapter in Phase B
/**
 * Components Board — Engine Mock Adapter
 *
 * TEMPORARY: wraps current local component.js + file.js code to fulfill
 * the EngineInterface contract. Will be replaced by real Components engine
 * adapter (HTTP/WebSocket/WASM) in Phase B.
 *
 * This module is the ONLY place that imports component.js and circuit
 * parsing from file.js. Board modules must not import these directly.
 *
 * @see engine-interface.md for the contract
 */

import {
  createComponentModel,
  addDevice,
  removeDevice,
  addConnection,
  removeConnection,
  getDevice,
  getConnections,
} from './model/component.js';

import {
  parseFile,
  FILE_TYPES,
  LINE_TYPES,
  serializeDevice,
  serializeConnect,
} from './model/file.js';

// =============================================================================
// HELPERS
// =============================================================================

let _opCounter = 0;

function generateOpId() {
  return `op-${String(++_opCounter).padStart(4, '0')}`;
}

/**
 * Simple sha256-like hash for revision tracking.
 * In browser: uses crypto.subtle. In Node tests: uses a fast sync hash.
 * For the mock, we use a simpler deterministic string hash (FNV-1a 64-bit style).
 */
function quickHash(text) {
  let h = 0x811c9dc5;
  for (let i = 0; i < text.length; i++) {
    h ^= text.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  // Return as hex-like string
  const u = h >>> 0;
  return 'mock:' + u.toString(16).padStart(8, '0');
}

function canonicalDeviceList(model) {
  const entries = Object.entries(model.devices)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([ref, dev]) => `${ref}:${dev.part}`);
  const conns = model.connections
    .map(c => `${c.from}->${c.to}`)
    .sort();
  return entries.join(';') + '|' + conns.join(';');
}

function serializeSource(model) {
  const lines = [];
  for (const [ref, dev] of Object.entries(model.devices)) {
    lines.push(serializeDevice(ref, dev.part));
  }
  for (const conn of model.connections) {
    lines.push(serializeConnect(conn.from, conn.to));
  }
  return lines.join('\n') + (lines.length ? '\n' : '');
}

/**
 * Generate a pin map for a device. In the mock we don't have real resolved
 * pin data, so we generate placeholder pins from connections.
 */
function inferPins(ref, model) {
  const pins = {};
  const prefix = ref + '.';
  for (const conn of model.connections) {
    if (conn.from.startsWith(prefix)) {
      const pin = conn.from.slice(prefix.length);
      if (!pins[pin]) pins[pin] = { direction: 'output', type: 'digital' };
    }
    if (conn.to.startsWith(prefix)) {
      const pin = conn.to.slice(prefix.length);
      if (!pins[pin]) pins[pin] = { direction: 'input', type: 'digital' };
    }
  }
  return pins;
}

// =============================================================================
// MOCK ADAPTER FACTORY
// =============================================================================

/**
 * Create a mock engine adapter.
 * Wraps current component.js model and provides EngineInterface-compatible API.
 *
 * @param {object} [initialModel] — initial component model (for testing)
 * @returns {object} adapter with getState, submit, submitBatch
 */
export function createEngineMock(initialModel) {
  let model = initialModel || createComponentModel();

  // Compute derived state
  function computeState() {
    const sourceText = serializeSource(model);
    const sourceRevision = quickHash(sourceText);
    const topologyDigest = quickHash(canonicalDeviceList(model));

    const devices = {};
    for (const [ref, dev] of Object.entries(model.devices)) {
      devices[ref] = {
        ref,
        part: dev.part,
        instanceId: `inst:${ref}`,  // stable ID for board-profile target
        pins: inferPins(ref, model),
      };
    }

    const edges = model.connections.map((conn, i) => ({
      id: `edge:${conn.from}->${conn.to}`,
      from: conn.from,
      to: conn.to,
      type: 'scalar',
    }));

    return {
      sourceRevision,
      topologyDigest,
      devices,
      edges,
      sourceText,
      diagnostics: [],
      probes: [],
      displays: [],
    };
  }

  // --- Operation handlers ---

  function handleAddDevice(intent) {
    const { ref, part } = intent;
    if (!ref || !part) {
      return { ok: false, error: 'add-device requires ref and part' };
    }
    if (getDevice(model, ref)) {
      return { ok: false, error: `Device "${ref}" already exists` };
    }
    const prevModel = model;
    model = addDevice(model, ref, part);
    return {
      ok: true,
      inverse: {
        kind: 'component.remove-device',
        target: 'source',
        intent: { ref },
      },
    };
  }

  function handleRemoveDevice(intent) {
    const { ref } = intent;
    if (!ref) {
      return { ok: false, error: 'remove-device requires ref' };
    }
    const dev = getDevice(model, ref);
    if (!dev) {
      return { ok: false, error: `Device "${ref}" not found` };
    }
    const part = dev.part;
    const removedConnections = getConnections(model, ref);
    model = removeDevice(model, ref);
    return {
      ok: true,
      inverse: {
        kind: 'component.add-device',
        target: 'source',
        intent: { ref, part },
        // Note: connections are lost — full inverse would need to re-add them
      },
    };
  }

  function handleConnect(intent) {
    const { from, to } = intent;
    if (!from || !to) {
      return { ok: false, error: 'connect requires from and to' };
    }
    const fromRef = from.split('.')[0];
    const toRef = to.split('.')[0];
    if (!getDevice(model, fromRef)) {
      return { ok: false, error: `Device "${fromRef}" not found` };
    }
    if (!getDevice(model, toRef)) {
      return { ok: false, error: `Device "${toRef}" not found` };
    }
    // Check duplicate
    const exists = model.connections.some(c => c.from === from && c.to === to);
    if (exists) {
      return { ok: false, error: `Connection ${from} → ${to} already exists` };
    }
    model = addConnection(model, from, to);
    return {
      ok: true,
      inverse: {
        kind: 'component.disconnect',
        target: 'source',
        intent: { from, to },
      },
    };
  }

  function handleConnectPreview(intent) {
    // Preview doesn't mutate — just validates
    const { from, to } = intent;
    if (!from || !to) {
      return { ok: false, error: 'connect.preview requires from and to' };
    }
    const fromRef = from.split('.')[0];
    const toRef = to.split('.')[0];
    if (!getDevice(model, fromRef)) {
      return { ok: false, error: `Device "${fromRef}" not found` };
    }
    if (!getDevice(model, toRef)) {
      return { ok: false, error: `Device "${toRef}" not found` };
    }
    const exists = model.connections.some(c => c.from === from && c.to === to);
    if (exists) {
      return { ok: false, error: `Connection ${from} → ${to} already exists` };
    }
    return { ok: true }; // valid but not applied
  }

  function handleDisconnect(intent) {
    const { from, to } = intent;
    if (!from || !to) {
      return { ok: false, error: 'disconnect requires from and to' };
    }
    const exists = model.connections.some(c => c.from === from && c.to === to);
    if (!exists) {
      return { ok: false, error: `Connection ${from} → ${to} not found` };
    }
    model = removeConnection(model, from, to);
    return {
      ok: true,
      inverse: {
        kind: 'component.connect.apply',
        target: 'source',
        intent: { from, to },
      },
    };
  }

  // --- Revision checking ---

  function checkRevision(op) {
    const current = computeState();
    if (op.source_revision && op.source_revision !== current.sourceRevision) {
      return { ok: false, error: 'Stale source_revision — state has changed. Re-read and retry.' };
    }
    if (op.topology_digest && op.topology_digest !== current.topologyDigest) {
      return { ok: false, error: 'Stale topology_digest — topology has changed. Re-read and retry.' };
    }
    return null; // no error
  }

  // --- Public API ---

  function getState() {
    return computeState();
  }

  async function submit(operation) {
    const opId = generateOpId();

    // Revision check
    const revError = checkRevision(operation);
    if (revError) return { ...revError, operationId: opId };

    // Dispatch by kind
    let result;
    switch (operation.kind) {
      case 'component.add-device':
        result = handleAddDevice(operation.intent);
        break;
      case 'component.remove-device':
        result = handleRemoveDevice(operation.intent);
        break;
      case 'component.connect.preview':
        result = handleConnectPreview(operation.intent);
        break;
      case 'component.connect.apply':
        result = handleConnect(operation.intent);
        break;
      case 'component.disconnect':
        result = handleDisconnect(operation.intent);
        break;
      default:
        result = { ok: false, error: `Unknown operation kind: "${operation.kind}"` };
    }

    // Attach metadata
    result.operationId = opId;
    if (result.ok) {
      result.newState = computeState();
      result.diagnostics = [];
      if (result.inverse) {
        result.inverse = {
          format: 'components.component-operation@1',
          source_revision: result.newState.sourceRevision,
          topology_digest: result.newState.topologyDigest,
          ...result.inverse,
        };
      }
    }
    return result;
  }

  async function submitBatch(operations) {
    const results = [];
    let allOk = true;

    for (const op of operations) {
      if (!allOk) {
        // Don't attempt further ops after a failure
        results.push({ ok: false, operationId: generateOpId(), error: 'Blocked by prior failure' });
        continue;
      }
      // Within a batch, skip revision check — ops are sequential and trusted
      const opWithCurrentRev = {
        ...op,
        source_revision: computeState().sourceRevision,
        topology_digest: computeState().topologyDigest,
      };
      const result = await submit(opWithCurrentRev);
      results.push(result);
      if (!result.ok) allOk = false;
    }

    return { ok: allOk, results };
  }

  // --- Expose raw model for test/migration purposes (TEMPORARY) ---
  function _getRawModel() {
    return model;
  }

  return Object.freeze({
    getState,
    submit,
    submitBatch,
    _getRawModel,  // temporary, for migration
  });
}
