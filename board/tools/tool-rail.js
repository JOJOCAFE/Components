/**
 * ToolRail — plugin-style tool management system.
 * Tools register themselves as plugin objects with identity + hooks.
 * DOM manipulation stays in app.js; tools only declare behavior.
 */
export class ToolRail {
  constructor() {
    this._tools = new Map();
    this._activeId = null;
  }

  /**
   * Register a tool plugin object.
   * @param {object} tool - Tool plugin with id, label, icon, and hook methods.
   */
  register(tool) {
    if (!tool || !tool.id) {
      throw new Error('Tool must have an id property');
    }
    this._tools.set(tool.id, tool);
  }

  /**
   * Remove a tool by id.
   * @param {string} toolId
   */
  unregister(toolId) {
    if (this._activeId === toolId) {
      this._activeId = null;
    }
    this._tools.delete(toolId);
  }

  /**
   * Set the active tool. Calls onDeactivate on the previous tool
   * and onActivate on the new tool.
   * @param {string} toolId
   * @param {object} [state] - Application state passed to hooks.
   */
  activate(toolId, state = {}) {
    const prev = this._tools.get(this._activeId);
    const next = this._tools.get(toolId);

    if (!next) {
      throw new Error(`Tool "${toolId}" is not registered`);
    }

    if (prev && prev.id !== toolId && typeof prev.onDeactivate === 'function') {
      prev.onDeactivate(state);
    }

    this._activeId = toolId;

    if (typeof next.onActivate === 'function') {
      next.onActivate(state);
    }
  }

  /**
   * Returns the currently active tool object, or null.
   * @returns {object|null}
   */
  active() {
    return this._tools.get(this._activeId) || null;
  }

  /**
   * Check if a specific tool is the active one.
   * @param {string} toolId
   * @returns {boolean}
   */
  isActive(toolId) {
    return this._activeId === toolId;
  }

  /**
   * Returns array of all registered tool objects.
   * @returns {object[]}
   */
  tools() {
    return Array.from(this._tools.values());
  }
}
