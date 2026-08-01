/**
 * Components Board — Command Executor
 * Task 1.3: Engine executor that applies parsed commands to Component + Board models.
 *
 * Stateful controller — the only mutable piece.
 * ES module syntax, Node.js compatible.
 */

import {
  createComponentModel,
  addDevice,
  removeDevice,
  addConnection,
  removeConnection,
  getDevice,
  getConnections,
} from '../model/component.js';

import {
  createBoardModel,
  setPlacement,
  removePlacement,
  getPlacement,
  setRoute,
  removeRoute,
  addLabel,
  removeRoutesForDevice,
} from '../model/board.js';

import { createConfig } from '../model/config.js';

/**
 * Deep clone via JSON round-trip (safe for plain objects).
 */
function snapshot(obj) {
  return JSON.parse(JSON.stringify(obj));
}

/**
 * Set a value at a dot-path on a plain object (mutates target).
 */
function setAtPath(obj, path, value) {
  const keys = path.split('.');
  let current = obj;
  for (let i = 0; i < keys.length - 1; i++) {
    if (current[keys[i]] === undefined || typeof current[keys[i]] !== 'object') {
      current[keys[i]] = {};
    }
    current = current[keys[i]];
  }
  current[keys[keys.length - 1]] = value;
}

/**
 * Extract device ref from a pin reference (e.g. "U1.1Y" → "U1").
 */
function refFromPin(pin) {
  const dot = pin.indexOf('.');
  return dot >= 0 ? pin.slice(0, dot) : pin;
}

/**
 * Create a new executor instance.
 * @param {object} [componentModel] - initial component model
 * @param {object} [boardModel] - initial board model
 * @param {object} [config] - initial config
 * @returns {object} executor with execute, undo, redo, getState
 */
export function createExecutor(componentModel, boardModel, config) {
  let state = {
    component: componentModel || createComponentModel(),
    board: boardModel || createBoardModel(),
    config: config || createConfig(),
    selection: null,
    viewport: { zoom: 100, panX: 0, panY: 0 },
    pages: { list: ['Page 1'], active: 'Page 1' },
  };

  // Per-page model storage (page name -> {component, board})
  const pageStore = {
    'Page 1': { component: state.component, board: state.board },
  };

  // History stacks for undo/redo
  const undoStack = [];
  const redoStack = [];

  function ok(message, command) {
    return { success: true, message, command };
  }

  function fail(errorMsg, command) {
    return { success: false, error: errorMsg, command };
  }

  /**
   * Check memory usage. Block new pages at 70% of memory limit.
   * Uses RSS (total process memory) against a configurable cap.
   * Default cap: 512MB for Node, jsHeapSizeLimit for browser.
   * Returns {blocked: false} if safe, or {blocked: true, reason} if not.
   */
  function checkMemory() {
    const THRESHOLD = 0.70; // 70%
    const DEFAULT_LIMIT_BYTES = 512 * 1024 * 1024; // 512 MB

    // Node.js environment
    if (typeof process !== 'undefined' && process.memoryUsage) {
      const mem = process.memoryUsage();
      const limit = DEFAULT_LIMIT_BYTES;
      const usage = mem.rss / limit;
      if (usage >= THRESHOLD) {
        const usedMB = (mem.rss / 1024 / 1024).toFixed(0);
        const limitMB = (limit / 1024 / 1024).toFixed(0);
        return { blocked: true, reason: `Memory ${usedMB}MB / ${limitMB}MB (${(usage * 100).toFixed(0)}%). Save work and close unused pages.` };
      }
    }

    // Browser environment (Chrome/Edge only — performance.memory)
    if (typeof performance !== 'undefined' && performance.memory) {
      const mem = performance.memory;
      const usage = mem.usedJSHeapSize / mem.jsHeapSizeLimit;
      if (usage >= THRESHOLD) {
        const pct = (usage * 100).toFixed(0);
        return { blocked: true, reason: `Memory ${pct}% used. Save work and close unused pages.` };
      }
    }

    return { blocked: false };
  }

  function pushUndo() {
    undoStack.push(snapshot(state));
    // Any new command clears the redo stack
    redoStack.length = 0;
  }

  // --- Command handlers ---

  function handlePlace(cmd) {
    const { ref, part, x, y } = cmd;
    const rotation = cmd.rotate !== undefined ? cmd.rotate : (cmd.rotation || 0);

    if (getDevice(state.component, ref)) {
      return fail(`Device "${ref}" already exists`, cmd);
    }

    pushUndo();
    state.component = addDevice(state.component, ref, part);
    state.board = setPlacement(state.board, ref, x, y, rotation);
    return ok(`Placed ${ref} (${part}) at (${x}, ${y}) rotation ${rotation}°`, cmd);
  }

  function handleMove(cmd) {
    const { ref, x, y } = cmd;

    if (!getDevice(state.component, ref)) {
      return fail(`Device "${ref}" not found`, cmd);
    }
    if (!getPlacement(state.board, ref)) {
      return fail(`Placement for "${ref}" not found`, cmd);
    }

    pushUndo();
    const existing = getPlacement(state.board, ref);
    state.board = setPlacement(state.board, ref, x, y, existing.rotation);
    return ok(`Moved ${ref} to (${x}, ${y})`, cmd);
  }

  function handleRotate(cmd) {
    const { ref } = cmd;
    const degrees = cmd.angle !== undefined ? cmd.angle : (cmd.degrees || 0);
    const VALID_ANGLES = [0, 90, 180, 270];

    if (!VALID_ANGLES.includes(degrees)) {
      return fail(`Invalid rotation angle ${degrees}. Valid: ${VALID_ANGLES.join(', ')}`, cmd);
    }
    if (!getDevice(state.component, ref)) {
      return fail(`Device "${ref}" not found`, cmd);
    }
    if (!getPlacement(state.board, ref)) {
      return fail(`Placement for "${ref}" not found`, cmd);
    }

    pushUndo();
    const existing = getPlacement(state.board, ref);
    state.board = setPlacement(state.board, ref, existing.x, existing.y, degrees);
    return ok(`Rotated ${ref} to ${degrees}°`, cmd);
  }

  function handleDelete(cmd) {
    const { ref } = cmd;

    if (!getDevice(state.component, ref)) {
      return fail(`Device "${ref}" not found`, cmd);
    }

    pushUndo();
    state.component = removeDevice(state.component, ref);
    // Remove placement if exists
    if (getPlacement(state.board, ref)) {
      state.board = removePlacement(state.board, ref);
    }
    // Remove all routes involving this device
    state.board = removeRoutesForDevice(state.board, ref);
    // Clear selection if it was this device
    if (state.selection === ref) {
      state.selection = null;
    }
    return ok(`Deleted ${ref} and its connections/routes`, cmd);
  }

  function handleConnect(cmd) {
    const { from, to, via } = cmd;

    // Check that both devices exist
    const fromRef = refFromPin(from);
    const toRef = refFromPin(to);
    if (!getDevice(state.component, fromRef)) {
      return fail(`Device "${fromRef}" not found (from pin "${from}")`, cmd);
    }
    if (!getDevice(state.component, toRef)) {
      return fail(`Device "${toRef}" not found (to pin "${to}")`, cmd);
    }

    pushUndo();
    state.component = addConnection(state.component, from, to, via || []);
    // If via points provided, also create a route
    if (via && via.length > 0) {
      state.board = setRoute(state.board, from, to, via);
    }
    return ok(`Connected ${from} → ${to}`, cmd);
  }

  function handleDisconnect(cmd) {
    const { from, to } = cmd;

    // Check connection exists
    const conn = state.component.connections.find(c => c.from === from && c.to === to);
    if (!conn) {
      return fail(`Connection from "${from}" to "${to}" not found`, cmd);
    }

    pushUndo();
    state.component = removeConnection(state.component, from, to);
    // Also remove route if exists
    const routeIdx = state.board.routes.findIndex(r => r.from === from && r.to === to);
    if (routeIdx >= 0) {
      state.board = removeRoute(state.board, from, to);
    }
    return ok(`Disconnected ${from} → ${to}`, cmd);
  }

  function handleRoute(cmd) {
    const { from, to, via } = cmd;

    // Check that the connection exists
    const conn = state.component.connections.find(c => c.from === from && c.to === to);
    if (!conn) {
      return fail(`Connection from "${from}" to "${to}" not found. Connect first.`, cmd);
    }

    pushUndo();
    state.board = setRoute(state.board, from, to, via);
    return ok(`Route set for ${from} → ${to} with ${via.length} waypoints`, cmd);
  }

  function handleLabel(cmd) {
    const { text, x, y } = cmd;

    pushUndo();
    state.board = addLabel(state.board, null, text, x, y);
    return ok(`Label "${text}" placed at (${x}, ${y})`, cmd);
  }

  function handleSelect(cmd) {
    const { ref } = cmd;

    if (!getDevice(state.component, ref)) {
      return fail(`Device "${ref}" not found`, cmd);
    }

    pushUndo();
    state.selection = ref;
    return ok(`Selected ${ref}`, cmd);
  }

  function handleDeselect(cmd) {
    pushUndo();
    state.selection = null;
    return ok('Deselected', cmd);
  }

  function handleZoom(cmd) {
    pushUndo();
    if (cmd.mode === 'fit') {
      state.viewport = { ...state.viewport, zoom: 'fit' };
      return ok('Zoom to fit', cmd);
    }
    const percent = cmd.percent !== undefined ? cmd.percent : cmd.value;
    state.viewport = { ...state.viewport, zoom: percent };
    return ok(`Zoom set to ${percent}%`, cmd);
  }

  function handlePan(cmd) {
    const { dx, dy } = cmd;
    pushUndo();
    state.viewport = {
      ...state.viewport,
      panX: state.viewport.panX + dx,
      panY: state.viewport.panY + dy,
    };
    return ok(`Panned by (${dx}, ${dy})`, cmd);
  }

  function handleNewPage(cmd) {
    const name = cmd.name;
    const paper = cmd.paper || cmd.paper_size || 'A4';
    const orientation = cmd.orientation || 'landscape';

    if (state.pages.list.includes(name)) {
      return fail(`Page "${name}" already exists`, cmd);
    }

    // Memory safety: check if memory usage exceeds 70% threshold
    const memCheck = checkMemory();
    if (memCheck.blocked) {
      return fail(`Cannot create new page: ${memCheck.reason}`, cmd);
    }

    pushUndo();
    // Save current page's state, create new page models
    pageStore[state.pages.active] = { component: state.component, board: state.board };
    pageStore[name] = { component: createComponentModel(), board: createBoardModel() };
    state.component = pageStore[name].component;
    state.board = pageStore[name].board;
    state.pages = {
      list: [...state.pages.list, name],
      active: name,
    };
    return ok(`Created page "${name}" (${paper} ${orientation})`, cmd);
  }

  function handleSwitchPage(cmd) {
    const { name } = cmd;

    if (!state.pages.list.includes(name)) {
      return fail(`Page "${name}" not found`, cmd);
    }

    pushUndo();
    // Save current page, load target page
    pageStore[state.pages.active] = { component: state.component, board: state.board };
    state.component = pageStore[name]?.component || createComponentModel();
    state.board = pageStore[name]?.board || createBoardModel();
    state.pages = { ...state.pages, active: name };
    return ok(`Switched to page "${name}"`, cmd);
  }

  function handleRenamePage(cmd) {
    const oldName = cmd.oldName || cmd.old_name;
    const newName = cmd.newName || cmd.new_name;

    if (!state.pages.list.includes(oldName)) {
      return fail(`Page "${oldName}" not found`, cmd);
    }
    if (state.pages.list.includes(newName)) {
      return fail(`Page "${newName}" already exists`, cmd);
    }

    pushUndo();
    const list = state.pages.list.map(p => p === oldName ? newName : p);
    const active = state.pages.active === oldName ? newName : state.pages.active;
    state.pages = { list, active };
    return ok(`Renamed page "${oldName}" → "${newName}"`, cmd);
  }

  function handleDeletePage(cmd) {
    const { name } = cmd;

    if (!state.pages.list.includes(name)) {
      return fail(`Page "${name}" not found`, cmd);
    }
    if (state.pages.list.length <= 1) {
      return fail('Cannot delete the last page', cmd);
    }

    pushUndo();
    const list = state.pages.list.filter(p => p !== name);
    const active = state.pages.active === name ? list[0] : state.pages.active;
    state.pages = { list, active };
    return ok(`Deleted page "${name}"`, cmd);
  }

  function handleSetConfig(cmd) {
    const { path, value } = cmd;

    pushUndo();
    const newConfig = snapshot(state.config);
    setAtPath(newConfig, path, value);
    state.config = newConfig;
    return ok(`Config ${path} = ${JSON.stringify(value)}`, cmd);
  }

  // --- Public API ---

  function execute(cmd) {
    if (!cmd || !cmd.type) {
      return fail('Invalid command: missing type', cmd);
    }

    switch (cmd.type) {
      case 'place': return handlePlace(cmd);
      case 'move': return handleMove(cmd);
      case 'rotate': return handleRotate(cmd);
      case 'delete': return handleDelete(cmd);
      case 'connect': return handleConnect(cmd);
      case 'disconnect': return handleDisconnect(cmd);
      case 'route': return handleRoute(cmd);
      case 'label': return handleLabel(cmd);
      case 'select': return handleSelect(cmd);
      case 'deselect': return handleDeselect(cmd);
      case 'zoom': return handleZoom(cmd);
      case 'pan': return handlePan(cmd);
      case 'undo': return undo();
      case 'redo': return redo();
      case 'new-page': return handleNewPage(cmd);
      case 'switch-page': return handleSwitchPage(cmd);
      case 'rename-page': return handleRenamePage(cmd);
      case 'delete-page': return handleDeletePage(cmd);
      case 'set-config': return handleSetConfig(cmd);
      case 'error': return fail(cmd.message || 'Parser error', cmd);
      default:
        return fail(`Unknown command type: "${cmd.type}"`, cmd);
    }
  }

  function undo() {
    if (undoStack.length === 0) {
      return fail('Nothing to undo', { type: 'undo' });
    }
    redoStack.push(snapshot(state));
    state = undoStack.pop();
    return ok('Undo successful', { type: 'undo' });
  }

  function redo() {
    if (redoStack.length === 0) {
      return fail('Nothing to redo', { type: 'redo' });
    }
    undoStack.push(snapshot(state));
    state = redoStack.pop();
    return ok('Redo successful', { type: 'redo' });
  }

  function getState() {
    return {
      component: state.component,
      board: state.board,
      config: state.config,
      selection: state.selection,
      viewport: state.viewport,
      history: { undoCount: undoStack.length, redoCount: redoStack.length },
      pages: state.pages,
    };
  }

  return { execute, undo, redo, getState };
}
