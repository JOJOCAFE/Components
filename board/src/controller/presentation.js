/**
 * Components Board — Presentation Mode + Undo/Redo History
 * Phase 5, Tasks 5.2–5.3
 *
 * Pure functions, no DOM, no side effects.
 * ES module syntax, Node.js compatible.
 */

// =============================================================================
// 5.2 PRESENTATION MODE
// =============================================================================

/**
 * Convert a full board state into a clean presentation-only version.
 * Strips ALL chrome: grid, tools, status bar, title block, borders, margins, selection.
 * Returns ONLY circuit content on a white background.
 *
 * @param {object} boardState — full board state (devices, routes, labels, plus any chrome)
 * @returns {object} { mode: 'presentation', devices, routes, labels, background }
 */
export function toPresentationMode(boardState) {
  if (!boardState || typeof boardState !== 'object') {
    return {
      mode: 'presentation',
      devices: [],
      routes: [],
      labels: [],
      background: '#ffffff',
    };
  }

  // Extract only circuit content arrays, stripping everything else
  const devices = extractDevices(boardState.devices);
  const routes = extractRoutes(boardState.routes);
  const labels = extractLabels(boardState.labels);

  return Object.freeze({
    mode: 'presentation',
    devices,
    routes,
    labels,
    background: '#ffffff',
  });
}

/**
 * Extract device data (positions only), strip selection/hover state.
 */
function extractDevices(devices) {
  if (!Array.isArray(devices)) return [];
  return devices.map(d => ({
    ref: d.ref || null,
    part: d.part || null,
    x: d.x ?? 0,
    y: d.y ?? 0,
    width: d.width ?? 10,
    height: d.height ?? 10,
    rotation: d.rotation ?? 0,
    fill: d.fill || '#ffffff',
    stroke: d.stroke || '#000000',
  }));
}

/**
 * Extract route data (paths only), strip selection/hover state.
 */
function extractRoutes(routes) {
  if (!Array.isArray(routes)) return [];
  return routes.map(r => ({
    from: r.from || null,
    to: r.to || null,
    color: r.color || '#007C3D',
    points: Array.isArray(r.points) ? r.points.map(p => ({ x: p.x, y: p.y })) : [],
  }));
}

/**
 * Extract label data (positions only), strip selection/hover state.
 */
function extractLabels(labels) {
  if (!Array.isArray(labels)) return [];
  return labels.map(l => ({
    text: l.text || '',
    x: l.x ?? 0,
    y: l.y ?? 0,
    fontSize: l.fontSize ?? 3,
    color: l.color || '#000000',
  }));
}

// =============================================================================
// 5.3 UNDO/REDO COMMAND HISTORY
// =============================================================================

/**
 * Create a command history manager for undo/redo operations.
 * Commands are stored in chronological order.
 * Position tracks where we are in the history (for undo/redo navigation).
 *
 * @returns {object} history manager API
 */
export function createCommandHistory() {
  let log = [];
  let position = 0; // Points to next insertion index (same as "how many commands are active")

  /**
   * Push a new command onto the history.
   * If we're not at the end (due to undo), truncate the future.
   * @param {*} command — the command object that was executed
   */
  function push(command) {
    // Truncate anything after current position (discard redo future)
    if (position < log.length) {
      log = log.slice(0, position);
    }
    log.push(command);
    position = log.length;
  }

  /**
   * Undo: move back one step, return the command to reverse.
   * @returns {*} command to undo, or null if at start
   */
  function undo() {
    if (position <= 0) return null;
    position--;
    return log[position];
  }

  /**
   * Redo: move forward one step, return the command to replay.
   * @returns {*} command to redo, or null if at end
   */
  function redo() {
    if (position >= log.length) return null;
    const cmd = log[position];
    position++;
    return cmd;
  }

  /**
   * Can we undo?
   * @returns {boolean}
   */
  function canUndo() {
    return position > 0;
  }

  /**
   * Can we redo?
   * @returns {boolean}
   */
  function canRedo() {
    return position < log.length;
  }

  /**
   * Get the full command history log (frozen copy).
   * @returns {Array}
   */
  function getLog() {
    return Object.freeze([...log]);
  }

  /**
   * Get current position in history.
   * 0 = start (nothing done or fully undone).
   * @returns {number}
   */
  function getPosition() {
    return position;
  }

  /**
   * Clear all history and reset position.
   */
  function clear() {
    log = [];
    position = 0;
  }

  return Object.freeze({
    push,
    undo,
    redo,
    canUndo,
    canRedo,
    getLog,
    getPosition,
    clear,
  });
}
