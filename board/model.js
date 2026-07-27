// board/model.js — shared state model, utilities, and event bus

// --- EventBus ---

export class EventBus {
  constructor() {
    this._listeners = Object.create(null);
  }

  on(event, fn) {
    (this._listeners[event] ??= []).push(fn);
  }

  off(event, fn) {
    const list = this._listeners[event];
    if (!list) return;
    const idx = list.indexOf(fn);
    if (idx !== -1) list.splice(idx, 1);
  }

  emit(event, data) {
    const list = this._listeners[event];
    if (!list) return;
    for (const fn of list) fn(data);
  }
}

// --- Storage key constants ---

export const STORAGE_KEY = 'board';
export const BOARD_PROFILE_KEY = 'boardProfile';
export const LEGACY_BOARD_PROFILE_KEY = 'board-profile';

// --- Utility functions ---

export async function request(command, input, options = {}) {
  const res = await fetch('/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...options.headers },
    body: JSON.stringify({ command, input }),
    ...options,
  });
  if (!res.ok) throw new Error(`request failed: ${res.status}`);
  return res.json();
}

export async function sha256(text) {
  const data = new TextEncoder().encode(text);
  const hash = await crypto.subtle.digest('SHA-256', data);
  return Array.from(new Uint8Array(hash))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

export function canonicalJson(value) {
  return JSON.stringify(value, (_, v) => {
    if (v && typeof v === 'object' && !Array.isArray(v)) {
      return Object.keys(v)
        .sort()
        .reduce((acc, k) => { acc[k] = v[k]; return acc; }, {});
    }
    return v;
  });
}

export async function digestResolvedTopology(resolved) {
  return sha256(canonicalJson(resolved));
}

// --- State factory ---

export function createState() {
  return {
    source: null,
    revision: 0,
    resolved: null,
    board: null,
    selected: null,
    drives: null,
    timer: null,
    resolveGeneration: 0,
    pinGesture: null,
    guide: null,
    guideVisibleEdges: null,
    boardProfile: null,
    staleBoardProfile: null,
    topologyDigest: null,
    drag: null,
    viewportDrag: null,
    viewport: null,
    nodePositions: null,
    suppressClick: false,
    pen: null,
    labelDraft: null,
    propertyLabelId: null,
    suppressNextLabelClick: false,
  };
}
