/**
 * Components Board — Tool Actions (Pure Functions)
 * Phase 3, Tasks 3.3, 3.4, 3.6, 3.7, 3.8
 *
 * DOM-free tool action functions. Each export returns a command object
 * (or null) that the executor can dispatch.
 *
 * Tools: Tray, Guide, Eraser, Label, Inspect
 */

// =============================================================================
// 3.3 PROJECT TRAY
// =============================================================================

/**
 * Pick a part from the tray (select for placement).
 * @param {string} part — part identifier
 * @returns {object} command
 */
export function trayPick(part) {
  return { type: 'tray-pick', part };
}

/**
 * Place a part from tray onto the board.
 * @param {string} part — part identifier
 * @param {object} pos — {x, y} position in mm
 * @param {number} [rotation=0] — rotation in degrees
 * @returns {object} command
 */
export function trayPlace(part, pos, rotation = 0) {
  return { type: 'place', ref: null, part, x: pos.x, y: pos.y, rotation };
}

/**
 * Remove a part from the tray.
 * @param {string} part — part identifier
 * @returns {object} command
 */
export function trayRemove(part) {
  return { type: 'tray-remove', part };
}

/**
 * List all items in the tray. Returns a frozen copy.
 * @param {Array} items — current tray items
 * @returns {Array} frozen copy of items
 */
export function trayList(items) {
  return Object.freeze([...items]);
}

// =============================================================================
// 3.4 GUIDE
// =============================================================================

/**
 * Toggle guide visibility for a pin.
 * @param {string} pinId — pin identifier
 * @param {boolean} currentState — true if guide is currently shown
 * @returns {object} command
 */
export function guideToggle(pinId, currentState) {
  if (currentState) {
    return { type: 'guide-hide', pin: pinId };
  }
  return { type: 'guide-show', pin: pinId };
}

/**
 * Clear all guides.
 * @returns {object} command
 */
export function guideClear() {
  return { type: 'guide-clear' };
}

// =============================================================================
// 3.6 ERASER
// =============================================================================

/**
 * Eraser click on a device — delete it.
 * @param {string} ref — device reference
 * @returns {object} command
 */
export function eraserClick(ref) {
  return { type: 'delete', ref };
}

/**
 * Eraser shift-click on a net — delete entire net.
 * @param {string} netId — net identifier
 * @returns {object} command
 */
export function eraserShiftClick(netId) {
  return { type: 'delete-net', net: netId };
}

/**
 * Eraser click on empty space — no-op.
 * @returns {null}
 */
export function eraserClickNothing() {
  return null;
}

// =============================================================================
// 3.7 LABEL
// =============================================================================

/**
 * Create a new label.
 * @param {string} text — label text
 * @param {object} pos — {x, y} position in mm
 * @returns {object} command
 */
export function labelCreate(text, pos) {
  return { type: 'label', text, x: pos.x, y: pos.y };
}

/**
 * Edit an existing label's text.
 * @param {string} id — label id
 * @param {string} newText — new text content
 * @returns {object} command
 */
export function labelEdit(id, newText) {
  return { type: 'label-edit', id, text: newText };
}

/**
 * Move a label to a new position.
 * @param {string} id — label id
 * @param {object} pos — {x, y} new position in mm
 * @returns {object} command
 */
export function labelMove(id, pos) {
  return { type: 'label-move', id, x: pos.x, y: pos.y };
}

/**
 * Delete a label.
 * @param {string} id — label id
 * @returns {object} command
 */
export function labelDelete(id) {
  return { type: 'label-delete', id };
}

// =============================================================================
// 3.8 INSPECT
// =============================================================================

/**
 * Inspect a device — returns frozen info.
 * @param {string} ref — device reference
 * @param {object} definition — {part, pins:[...], description}
 * @returns {object} command with frozen info
 */
export function inspect(ref, definition) {
  return { type: 'inspect', ref, info: Object.freeze({ ...definition }) };
}

/**
 * Clear the inspect panel.
 * @returns {object} command
 */
export function inspectClear() {
  return { type: 'inspect-clear' };
}
