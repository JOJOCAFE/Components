/**
 * Components Board — HTTP Engine Adapter
 *
 * Connects Board to the real Python Components engine via HTTP API.
 * Implements the same adapter interface as engine-mock.js:
 *   { getState, submit, submitBatch }
 *
 * Usage:
 *   const adapter = await createHttpAdapter({ baseUrl: 'http://127.0.0.1:8765' });
 *   const engine = createEngineInterface(adapter);
 *
 * The Python API must be running:
 *   PYTHONPATH=python python3 -B -m chiplib.api --http --host 127.0.0.1 --port 8765
 */

// =============================================================================
// ADAPTER FACTORY
// =============================================================================

/**
 * Create an HTTP engine adapter.
 * Call init() after creation to load initial state from the server.
 *
 * @param {object} options
 * @param {string} options.baseUrl — API base URL (default: same origin)
 * @returns {object} adapter with getState, submit, submitBatch, init
 */
export function createHttpAdapter(options = {}) {
  const baseUrl = options.baseUrl || '';

  // Cached state — updated after every successful submit
  let cachedState = {
    sourceRevision: '',
    topologyDigest: '',
    devices: {},
    edges: [],
    sourceText: '',
    diagnostics: [],
    probes: [],
    displays: [],
  };

  // Current source text (authoritative for edits)
  let currentSource = '';

  // --- API helpers ---

  async function post(command, input = {}, opts = {}) {
    const body = { command, input, options: opts };
    const res = await fetch(baseUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return res.json();
  }

  // --- State projection ---

  function projectState(resolved, boardView, source, revision) {
    const devices = {};
    for (const block of (boardView?.blocks || [])) {
      const pins = {};
      for (const pin of (block.pins || [])) {
        pins[pin.name] = { direction: pin.direction, type: 'digital' };
      }
      devices[block.id] = {
        ref: block.id,
        part: block.part,
        instanceId: block.id,
        pins,
        pinAnchors: block.pin_anchors || [],
        resource: block.resource || null,
      };
    }

    const edges = (boardView?.wires || []).map(w => ({
      id: w.id,
      from: w.from,
      to: w.to,
      type: w.kind || 'scalar',
    }));

    const diagnostics = (resolved?.diagnostics || []).map(d => ({
      severity: d.severity || 'info',
      message: d.message || '',
      location: d.location || null,
    }));

    // Topology digest: use component_id + edge count as proxy
    const topologyDigest = `resolved:${resolved?.component_id || 'unknown'}:${edges.length}`;

    return {
      sourceRevision: revision,
      topologyDigest,
      devices,
      edges,
      sourceText: source,
      diagnostics,
      probes: resolved?.probes || [],
      displays: resolved?.displays || [],
    };
  }

  // --- Public API ---

  /**
   * Initialize by loading source from the server.
   * @param {string} [source] — initial source text (if not provided, loads example)
   */
  async function init(source) {
    if (!source) {
      // Load the default example
      const exampleRes = await post('component-language-example');
      if (exampleRes.ok !== false && exampleRes.result?.source) {
        source = exampleRes.result.source;
      } else {
        throw new Error('Failed to load component example from server');
      }
    }

    currentSource = source;

    // Resolve and get board view
    const resolveRes = await post('component-language-resolve', { source });
    const boardViewRes = await post('component-language-board-view', { source });

    const resolved = resolveRes.ok !== false ? resolveRes.result : {};
    const boardView = boardViewRes.ok !== false ? boardViewRes.result : {};

    // Compute revision
    const revision = `sha256:${await sha256(source)}`;

    cachedState = projectState(resolved, boardView, source, revision);
  }

  function getState() {
    return cachedState;
  }

  async function submit(operation) {
    const { kind, intent } = operation;

    // Map Board operation kinds to component-language-edit edits
    let edit;
    switch (kind) {
      case 'component.add-device':
        edit = { kind: 'add-device', ref: intent.ref, part: intent.part };
        break;
      case 'component.remove-device':
        edit = { kind: 'remove-device', ref: intent.ref };
        break;
      case 'component.connect.apply':
        edit = { kind: 'connect', from: intent.from, to: intent.to };
        break;
      case 'component.disconnect':
        edit = { kind: 'disconnect', from: intent.from, to: intent.to };
        break;
      case 'component.connect.preview':
        // Preview only — validate without mutation
        const previewRes = await post('component-language-edit-preview', {
          source: currentSource,
          source_revision: cachedState.sourceRevision,
          edit: { kind: 'connect', from: intent.from, to: intent.to },
        });
        if (previewRes.ok !== false && previewRes.result?.ok) {
          return { ok: true, operationId: `http-preview-${Date.now()}` };
        }
        return {
          ok: false,
          operationId: `http-preview-${Date.now()}`,
          error: previewRes.result?.diagnostics?.[0]?.message || 'Preview rejected',
        };
      default:
        return { ok: false, operationId: `http-${Date.now()}`, error: `Unknown kind: ${kind}` };
    }

    // Submit the edit
    const res = await post('component-language-edit', {
      source: currentSource,
      source_revision: cachedState.sourceRevision,
      edit,
    });

    if (res.ok === false || !res.result?.ok) {
      const errMsg = res.result?.diagnostics?.[0]?.message || res.result?.error || res.error || 'Edit rejected';
      return { ok: false, operationId: `http-${Date.now()}`, error: errMsg };
    }

    // Edit succeeded — update cached state
    const newSource = res.result.source;
    const newRevision = res.result.source_revision;
    currentSource = newSource;

    // Re-resolve and refresh board view
    const resolveRes = await post('component-language-resolve', { source: newSource });
    const boardViewRes = await post('component-language-board-view', { source: newSource });

    const resolved = resolveRes.ok !== false ? resolveRes.result : {};
    const boardView = boardViewRes.ok !== false ? boardViewRes.result : {};

    cachedState = projectState(resolved, boardView, newSource, newRevision);

    return {
      ok: true,
      operationId: `http-${Date.now()}`,
      newState: cachedState,
      diagnostics: cachedState.diagnostics,
    };
  }

  async function submitBatch(operations) {
    const results = [];
    let allOk = true;
    for (const op of operations) {
      if (!allOk) {
        results.push({ ok: false, operationId: `http-batch-${Date.now()}`, error: 'Blocked by prior failure' });
        continue;
      }
      const result = await submit(op);
      results.push(result);
      if (!result.ok) allOk = false;
    }
    return { ok: allOk, results };
  }

  return Object.freeze({
    init,
    getState,
    submit,
    submitBatch,
  });
}

// =============================================================================
// HELPERS
// =============================================================================

async function sha256(text) {
  if (typeof crypto !== 'undefined' && crypto.subtle) {
    const buf = new TextEncoder().encode(text);
    const hash = await crypto.subtle.digest('SHA-256', buf);
    return Array.from(new Uint8Array(hash)).map(b => b.toString(16).padStart(2, '0')).join('');
  }
  // Fallback for environments without crypto.subtle
  let h = 0x811c9dc5;
  for (let i = 0; i < text.length; i++) {
    h ^= text.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return 'fnv:' + (h >>> 0).toString(16).padStart(8, '0');
}
