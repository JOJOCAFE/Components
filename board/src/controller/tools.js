/**
 * Components Board — Tool Plugin System
 * Phase 3, Task 3.1: Tool registry, activation, shortcut dispatch, gesture routing
 *
 * DOM-free. Pure state management for the toolbar rail.
 * One tool active at a time. Escape always returns to 'select'.
 *
 * Tool definition contract:
 *   { id, name, icon, shortcut, commands[], gestures{} }
 *
 * Usage:
 *   import { createToolSystem } from './tools.js';
 *   const tools = createToolSystem();
 *   tools.register({ id: 'select', name: 'Select', ... });
 *   tools.activate('select');
 *   tools.dispatchShortcut('W'); // activates 'connect'
 *   tools.dispatchGesture('drag'); // returns command type for active tool
 */

// =============================================================================
// PHASE 1 TOOL DEFINITIONS
// =============================================================================

const PHASE1_TOOLS = [
  {
    id: 'select', name: 'Select', icon: 'arrow', shortcut: 'V',
    commands: ['select', 'move', 'rotate', 'delete'],
    gestures: { click: 'select', drag: 'move', escape: 'deselect' }
  },
  {
    id: 'tray', name: 'Project Tray', icon: 'tray', shortcut: 'L',
    commands: ['open-tray', 'place'],
    gestures: { click: 'open-tray', drag: 'place' }
  },
  {
    id: 'guide', name: 'Guide', icon: 'guide', shortcut: 'G',
    commands: ['add-guide', 'move-guide', 'remove-guide'],
    gestures: { click: 'add-guide', drag: 'move-guide', dblclick: 'remove-guide' }
  },
  {
    id: 'connect', name: 'Connect', icon: 'wire', shortcut: 'W',
    commands: ['start-wire', 'end-wire', 'cancel-wire'],
    gestures: { click: 'start-wire', drag: 'end-wire', escape: 'cancel-wire' }
  },
  {
    id: 'eraser', name: 'Eraser', icon: 'eraser', shortcut: 'E',
    commands: ['erase'],
    gestures: { click: 'erase', drag: 'erase' }
  },
  {
    id: 'label', name: 'Label', icon: 'text', shortcut: 'T',
    commands: ['add-label', 'edit-label'],
    gestures: { click: 'add-label', dblclick: 'edit-label' }
  },
  {
    id: 'inspect', name: 'Inspect', icon: 'info', shortcut: 'I',
    commands: ['inspect'],
    gestures: { click: 'inspect' }
  },
  {
    id: 'more', name: 'More', icon: 'dots', shortcut: '.',
    commands: ['open-menu'],
    gestures: { click: 'open-menu' }
  }
];

// =============================================================================
// TOOL SYSTEM FACTORY
// =============================================================================

/**
 * Create a tool system instance.
 * Pre-registers Phase 1 tools by default.
 *
 * @param {object} [options]
 * @param {boolean} [options.preload=true] — register Phase 1 tools on creation
 * @returns {object} Tool system API
 */
export function createToolSystem(options = {}) {
  const { preload = true } = options;

  /** @type {Map<string, object>} id → tool definition */
  const registry = new Map();

  /** @type {Map<string, string>} shortcut (uppercase) → tool id */
  const shortcuts = new Map();

  /** @type {string} currently active tool id */
  let activeId = null;

  // ---------------------------------------------------------------------------
  // REGISTRATION
  // ---------------------------------------------------------------------------

  /**
   * Register a tool definition.
   * @param {object} def — tool definition object
   * @throws if id already registered or definition invalid
   */
  function register(def) {
    validate(def);
    if (registry.has(def.id)) {
      throw new Error(`Tool already registered: '${def.id}'`);
    }
    const tool = Object.freeze({ ...def, shortcut: def.shortcut.toUpperCase() });
    registry.set(tool.id, tool);
    shortcuts.set(tool.shortcut, tool.id);
  }

  /**
   * Validate a tool definition object.
   * @param {object} def
   */
  function validate(def) {
    if (!def || typeof def.id !== 'string' || !def.id) {
      throw new Error('Tool definition requires a string id');
    }
    if (typeof def.name !== 'string' || !def.name) {
      throw new Error(`Tool '${def.id}' requires a name`);
    }
    if (typeof def.icon !== 'string' || !def.icon) {
      throw new Error(`Tool '${def.id}' requires an icon`);
    }
    if (typeof def.shortcut !== 'string' || !def.shortcut) {
      throw new Error(`Tool '${def.id}' requires a shortcut`);
    }
    if (!Array.isArray(def.commands)) {
      throw new Error(`Tool '${def.id}' requires a commands array`);
    }
    if (!def.gestures || typeof def.gestures !== 'object') {
      throw new Error(`Tool '${def.id}' requires a gestures object`);
    }
  }

  // ---------------------------------------------------------------------------
  // ACTIVATION
  // ---------------------------------------------------------------------------

  /**
   * Activate a tool by id.
   * @param {string} id
   * @returns {object} the activated tool definition
   * @throws if tool not registered
   */
  function activate(id) {
    if (!registry.has(id)) {
      throw new Error(`Cannot activate unknown tool: '${id}'`);
    }
    activeId = id;
    return registry.get(id);
  }

  /**
   * Deactivate current tool (returns to 'select').
   * @returns {object} the select tool definition
   */
  function deactivate() {
    return activate('select');
  }

  /**
   * Get the currently active tool definition.
   * @returns {object|null}
   */
  function getActive() {
    if (!activeId) return null;
    return registry.get(activeId) || null;
  }

  // ---------------------------------------------------------------------------
  // SHORTCUT DISPATCH
  // ---------------------------------------------------------------------------

  /**
   * Dispatch a keyboard shortcut. Activates the matching tool.
   * Escape always returns to 'select'.
   *
   * @param {string} key — the key pressed (case-insensitive)
   * @returns {object|null} activated tool, or null if no match
   */
  function dispatchShortcut(key) {
    if (key === 'Escape' || key === 'escape') {
      return activate('select');
    }
    const upper = key.toUpperCase();
    const id = shortcuts.get(upper);
    if (!id) return null;
    return activate(id);
  }

  // ---------------------------------------------------------------------------
  // GESTURE DISPATCH
  // ---------------------------------------------------------------------------

  /**
   * Given a gesture type, return the command type for the active tool.
   *
   * @param {string} gesture — e.g. 'click', 'drag', 'escape', 'dblclick'
   * @returns {string|null} command type to emit, or null if not mapped
   */
  function dispatchGesture(gesture) {
    const tool = getActive();
    if (!tool) return null;
    return tool.gestures[gesture] || null;
  }

  // ---------------------------------------------------------------------------
  // LISTING
  // ---------------------------------------------------------------------------

  /**
   * List all registered tools in registration order.
   * @returns {object[]} array of frozen tool definitions
   */
  function list() {
    return Array.from(registry.values());
  }

  /**
   * Get a tool definition by id.
   * @param {string} id
   * @returns {object|null}
   */
  function get(id) {
    return registry.get(id) || null;
  }

  // ---------------------------------------------------------------------------
  // PRELOAD
  // ---------------------------------------------------------------------------

  if (preload) {
    for (const def of PHASE1_TOOLS) {
      register(def);
    }
    activate('select');
  }

  // ---------------------------------------------------------------------------
  // PUBLIC API
  // ---------------------------------------------------------------------------

  return {
    register,
    activate,
    deactivate,
    getActive,
    dispatchShortcut,
    dispatchGesture,
    list,
    get,
  };
}
