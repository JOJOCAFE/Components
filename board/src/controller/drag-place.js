/**
 * Components Board — Drag-to-Place Controller
 * Headless drag state machine: drag from tray panel → drop on viewport → place.
 *
 * Lifecycle:
 *   1. dragStart(part, screenPos) — user grabs part from tray
 *   2. dragMove(screenPos)        — user moves over viewport (ghost follows)
 *   3. dragEnd(screenPos)         — user releases on viewport → place
 *   4. dragCancel()               — user cancels (Esc, leave viewport)
 *
 * This module manages state only. The browser wires HTML5 drag events
 * (dragstart/dragover/drop) or pointer events to these methods.
 *
 * DOM-free. Pure state management.
 * ES module syntax, Node.js compatible.
 */

import { snapToGrid } from './device-tray.js';

// =============================================================================
// DRAG STATE
// =============================================================================

/** @typedef {'idle'|'dragging'|'over-target'} DragPhase */

/**
 * @typedef {object} DragState
 * @property {DragPhase} phase
 * @property {string|null} part — part being dragged
 * @property {{ x: number, y: number }|null} startScreen — initial screen pos
 * @property {{ x: number, y: number }|null} currentScreen — current screen pos
 * @property {{ x: number, y: number }|null} worldPos — snapped world position (when over target)
 * @property {boolean} valid — true if current position is a valid drop target
 */

// =============================================================================
// DRAG-PLACE FACTORY
// =============================================================================

/**
 * Create a drag-to-place controller.
 *
 * @param {object} options
 * @param {object} options.tray — device tray instance
 * @param {object} options.viewport — viewport instance (for screenToWorld)
 * @param {object} [options.gridSnap=true] — snap to grid on drop
 * @returns {object} drag-place API
 */
export function createDragPlace(options = {}) {
  const { tray, viewport, gridSnap = true } = options;

  /** @type {DragState} */
  let state = createIdleState();

  /** Listeners for state changes */
  const listeners = [];

  // ---------------------------------------------------------------------------
  // STATE MANAGEMENT
  // ---------------------------------------------------------------------------

  function createIdleState() {
    return Object.freeze({
      phase: 'idle',
      part: null,
      startScreen: null,
      currentScreen: null,
      worldPos: null,
      valid: false,
    });
  }

  function setState(newState) {
    state = Object.freeze(newState);
    for (const fn of listeners) {
      try { fn(state); } catch { /* listener errors don't break state */ }
    }
  }

  // ---------------------------------------------------------------------------
  // DRAG LIFECYCLE
  // ---------------------------------------------------------------------------

  /**
   * Start dragging a part from the tray.
   * Call when user initiates drag (mousedown/dragstart on tray item).
   *
   * @param {string} part — part identifier
   * @param {{ x: number, y: number }} screenPos — initial screen position
   * @returns {object} { success, error? }
   */
  function dragStart(part, screenPos) {
    if (!part) return { success: false, error: 'No part specified' };
    if (state.phase !== 'idle') {
      // Auto-cancel previous drag
      dragCancel();
    }

    // Verify part is available in tray
    if (tray) {
      const item = tray.getItem(part);
      if (!item) {
        // Auto-add to tray if not present (convenience for library drag)
        tray.addToTray(part);
      }
      if (tray.remainingCount(part) <= 0) {
        return { success: false, error: `No remaining ${part} in tray` };
      }
    }

    setState({
      phase: 'dragging',
      part,
      startScreen: { x: screenPos.x, y: screenPos.y },
      currentScreen: { x: screenPos.x, y: screenPos.y },
      worldPos: null,
      valid: false,
    });

    return { success: true };
  }

  /**
   * Update drag position (called on mousemove/dragover).
   *
   * @param {{ x: number, y: number }} screenPos — current screen position
   * @param {object} [viewportBounds] — { left, top, width, height } of viewport element
   * @returns {object} { phase, worldPos, valid }
   */
  function dragMove(screenPos, viewportBounds) {
    if (state.phase === 'idle') {
      return { phase: 'idle', worldPos: null, valid: false };
    }

    let worldPos = null;
    let valid = false;
    let phase = 'dragging';

    // If viewport bounds provided, check if we're over the viewport
    if (viewportBounds && viewport) {
      const inBounds = (
        screenPos.x >= viewportBounds.left &&
        screenPos.x <= viewportBounds.left + viewportBounds.width &&
        screenPos.y >= viewportBounds.top &&
        screenPos.y <= viewportBounds.top + viewportBounds.height
      );

      if (inBounds) {
        phase = 'over-target';
        // Convert screen → world
        const localX = screenPos.x - viewportBounds.left;
        const localY = screenPos.y - viewportBounds.top;
        worldPos = viewport.screenToWorld(localX, localY, viewportBounds.width, viewportBounds.height);

        if (gridSnap) {
          worldPos = snapToGrid(worldPos);
        }
        valid = true;
      }
    } else if (viewport) {
      // No bounds info — trust that it's over viewport
      phase = 'over-target';
      valid = true;
    }

    setState({
      ...state,
      phase,
      currentScreen: { x: screenPos.x, y: screenPos.y },
      worldPos,
      valid,
    });

    return { phase, worldPos, valid };
  }

  /**
   * End drag (drop). Places the part if position is valid.
   *
   * @param {{ x: number, y: number }} [screenPos] — final screen position (optional, uses last known)
   * @param {object} [viewportBounds] — viewport bounds for final coordinate conversion
   * @returns {object} { success, ref?, position?, error? }
   */
  function dragEnd(screenPos, viewportBounds) {
    if (state.phase === 'idle') {
      return { success: false, error: 'No drag in progress' };
    }

    const part = state.part;

    // Compute final world position
    let finalWorld = state.worldPos;

    if (screenPos && viewportBounds && viewport) {
      const localX = screenPos.x - viewportBounds.left;
      const localY = screenPos.y - viewportBounds.top;
      finalWorld = viewport.screenToWorld(localX, localY, viewportBounds.width, viewportBounds.height);
      if (gridSnap) {
        finalWorld = snapToGrid(finalWorld);
      }
    }

    // Reset state first
    setState(createIdleState());

    // Must have a valid world position to place
    if (!finalWorld) {
      return { success: false, error: 'Drop outside valid area' };
    }

    // Place via tray
    if (!tray) {
      return { success: false, error: 'No tray configured' };
    }

    const result = tray.placeFromTray(part, { x: finalWorld.x, y: finalWorld.y });
    if (result.success) {
      return {
        success: true,
        ref: result.ref,
        position: result.position || finalWorld,
        part,
        command: result.command,
      };
    }

    return { success: false, error: result.error };
  }

  /**
   * Cancel the current drag without placing.
   * @returns {object} { cancelled: boolean, part? }
   */
  function dragCancel() {
    if (state.phase === 'idle') {
      return { cancelled: false };
    }
    const part = state.part;
    setState(createIdleState());
    return { cancelled: true, part };
  }

  // ---------------------------------------------------------------------------
  // QUERIES
  // ---------------------------------------------------------------------------

  /**
   * Get current drag state (read-only snapshot).
   * @returns {DragState}
   */
  function getState() {
    return state;
  }

  /**
   * Check if a drag is in progress.
   * @returns {boolean}
   */
  function isDragging() {
    return state.phase !== 'idle';
  }

  /**
   * Get the part currently being dragged.
   * @returns {string|null}
   */
  function getDragPart() {
    return state.part;
  }

  /**
   * Get the current snapped world position (for ghost rendering).
   * @returns {{ x: number, y: number }|null}
   */
  function getGhostPosition() {
    return state.worldPos;
  }

  // ---------------------------------------------------------------------------
  // LISTENERS
  // ---------------------------------------------------------------------------

  /**
   * Subscribe to state changes.
   * @param {function} fn — callback(state)
   * @returns {function} unsubscribe function
   */
  function onChange(fn) {
    listeners.push(fn);
    return () => {
      const idx = listeners.indexOf(fn);
      if (idx >= 0) listeners.splice(idx, 1);
    };
  }

  // ---------------------------------------------------------------------------
  // PUBLIC API
  // ---------------------------------------------------------------------------

  return {
    dragStart,
    dragMove,
    dragEnd,
    dragCancel,
    getState,
    isDragging,
    getDragPart,
    getGhostPosition,
    onChange,
  };
}
