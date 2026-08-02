/**
 * Components Board — Select Tool (Gesture → Command)
 * Phase 3, Task 3.2: DOM-free select tool that translates gestures into commands.
 *
 * Never touches the model directly. Returns command objects that the executor
 * can dispatch to mutate state.
 *
 * Usage:
 *   import { createSelectTool } from './select-tool.js';
 *   const tool = createSelectTool();
 *   const cmd = tool.click({x: 10, y: 20}, 'U1');
 *   // → {type: 'select', ref: 'U1'}
 */

// =============================================================================
// SELECT TOOL FACTORY
// =============================================================================

/**
 * Create a Select Tool instance.
 * Methods return command objects or null.
 *
 * @returns {object} tool instance with click, drag, key, boxSelect methods
 */
export function createSelectTool() {

  // ---------------------------------------------------------------------------
  // CLICK
  // ---------------------------------------------------------------------------

  /**
   * Handle click gesture.
   * @param {object} pos — {x, y} in mm
   * @param {string|null} hitRef — device ref under cursor, or null for empty space
   * @returns {object} command: {type:'select', ref} or {type:'deselect'}
   */
  function click(pos, hitRef) {
    if (hitRef) {
      return { type: 'select', ref: hitRef };
    }
    return { type: 'deselect' };
  }

  // ---------------------------------------------------------------------------
  // DRAG
  // ---------------------------------------------------------------------------

  /**
   * Handle drag gesture (move a device).
   * @param {object} start — {x, y} drag start position in mm
   * @param {object} end — {x, y} drag end position in mm
   * @param {string} ref — device ref being dragged
   * @returns {object|null} command: {type:'move', ref, dx, dy} or null if no ref
   */
  function drag(start, end, ref) {
    if (!ref) return null;
    const dx = end.x - start.x;
    const dy = end.y - start.y;
    return { type: 'move', ref, dx, dy };
  }

  // ---------------------------------------------------------------------------
  // KEY
  // ---------------------------------------------------------------------------

  /**
   * Handle keyboard shortcut while select tool is active.
   * @param {string} key — 'r', 'R', 'Delete', or 'Escape'
   * @param {string|null} selectedRef — currently selected device ref
   * @returns {object|null} command object or null
   */
  function key(key, selectedRef) {
    if (key === 'Escape') {
      return { type: 'deselect' };
    }
    if ((key === 'r' || key === 'R') && selectedRef) {
      return { type: 'rotate', ref: selectedRef, angle: 90 };
    }
    if (key === 'Delete' && selectedRef) {
      return { type: 'delete', ref: selectedRef };
    }
    return null;
  }

  // ---------------------------------------------------------------------------
  // BOX SELECT
  // ---------------------------------------------------------------------------

  /**
   * Handle box (marquee) selection.
   * Normalizes coordinates so x1<=x2, y1<=y2.
   * @param {object} start — {x, y} first corner
   * @param {object} end — {x, y} opposite corner
   * @returns {object} command: {type:'select', box:{x1,y1,x2,y2}}
   */
  function boxSelect(start, end) {
    const x1 = Math.min(start.x, end.x);
    const y1 = Math.min(start.y, end.y);
    const x2 = Math.max(start.x, end.x);
    const y2 = Math.max(start.y, end.y);
    return { type: 'select', box: { x1, y1, x2, y2 } };
  }

  // ---------------------------------------------------------------------------
  // PUBLIC API
  // ---------------------------------------------------------------------------

  return { click, drag, key, boxSelect };
}
