/**
 * Components Board — Connect Tool (Orthogonal Wiring)
 * Phase 3, Task 3.5: DOM-free connect tool that handles orthogonal wiring.
 *
 * Click source pin → place turning points → click target pin → emit commands.
 * All segments are orthogonal (horizontal or vertical only).
 * Escape cancels at any time.
 *
 * Usage:
 *   import { createConnectTool } from './connect-tool.js';
 *   const tool = createConnectTool();
 *   tool.clickPin('U1.1Y');           // start
 *   tool.clickPoint({x: 10, y: 5});   // turning point
 *   const cmds = tool.clickPin('U2.1A'); // complete → [connect, route]
 */

// =============================================================================
// CONNECT TOOL FACTORY
// =============================================================================

/**
 * Create a Connect Tool instance.
 * Maintains internal state for the current connection being drawn.
 *
 * @returns {object} tool instance with clickPin, clickPoint, escape, isActive, getPreview
 */
export function createConnectTool() {

  /** @type {string|null} source pin id */
  let sourcePin = null;

  /** @type {{x:number, y:number}[]} turning points placed so far */
  let points = [];

  /** @type {boolean} whether a connection is in progress */
  let active = false;

  // ---------------------------------------------------------------------------
  // HELPERS
  // ---------------------------------------------------------------------------

  /**
   * Snap a point to be orthogonal relative to the previous point.
   * If the point is already aligned on one axis, keep it.
   * Otherwise snap to the axis with the smaller delta (closer to aligned).
   *
   * @param {{x:number, y:number}} pos — desired point
   * @param {{x:number, y:number}} prev — previous point to align against
   * @returns {{x:number, y:number}} snapped point
   */
  function snapOrthogonal(pos, prev) {
    const dx = Math.abs(pos.x - prev.x);
    const dy = Math.abs(pos.y - prev.y);

    // Already aligned on one axis
    if (dx === 0 || dy === 0) return { x: pos.x, y: pos.y };

    // Snap to the axis with the smaller delta (keep the larger movement)
    if (dx <= dy) {
      // Snap X to prev.x (make vertical segment)
      return { x: prev.x, y: pos.y };
    } else {
      // Snap Y to prev.y (make horizontal segment)
      return { x: pos.x, y: prev.y };
    }
  }

  /**
   * Get the last reference point (last turning point, or conceptual origin).
   * For orthogonal snapping we need the previous point in the path.
   *
   * @returns {{x:number, y:number}|null}
   */
  function lastPoint() {
    if (points.length > 0) return points[points.length - 1];
    return null;
  }

  /**
   * Reset internal state.
   */
  function reset() {
    sourcePin = null;
    points = [];
    active = false;
  }

  // ---------------------------------------------------------------------------
  // CLICK PIN
  // ---------------------------------------------------------------------------

  /**
   * Handle a pin click.
   * - When not active: starts a new connection from this pin.
   * - When active: completes the connection to this pin.
   *
   * @param {string} pinId — pin identifier like "U1.1Y"
   * @returns {object[]|null} array of two commands on completion, or null on start
   */
  function clickPin(pinId) {
    if (!active) {
      // Start connection
      sourcePin = pinId;
      points = [];
      active = true;
      return null;
    }

    // Complete connection
    const from = sourcePin;
    const to = pinId;
    const via = points.slice(); // copy

    const commands = [
      { type: 'connect', from, to },
      { type: 'route', from, to, via }
    ];

    reset();
    return commands;
  }

  // ---------------------------------------------------------------------------
  // CLICK POINT
  // ---------------------------------------------------------------------------

  /**
   * Handle a point click to add a turning point.
   * Only works when connection is active.
   * Enforces orthogonal constraint by snapping to nearest axis.
   *
   * @param {{x:number, y:number}} pos — position in mm
   * @returns {null} always null (turning points don't produce commands)
   */
  function clickPoint(pos) {
    if (!active) return null;

    const prev = lastPoint();
    if (prev) {
      // Snap to orthogonal relative to previous point
      const snapped = snapOrthogonal(pos, prev);
      points.push(snapped);
    } else {
      // First turning point — no previous reference, accept as-is
      points.push({ x: pos.x, y: pos.y });
    }

    return null;
  }

  // ---------------------------------------------------------------------------
  // ESCAPE
  // ---------------------------------------------------------------------------

  /**
   * Cancel the current connection.
   * @returns {object} cancel-connect command
   */
  function escape() {
    reset();
    return { type: 'cancel-connect' };
  }

  // ---------------------------------------------------------------------------
  // IS ACTIVE
  // ---------------------------------------------------------------------------

  /**
   * Check if a connection is currently in progress.
   * @returns {boolean}
   */
  function isActive() {
    return active;
  }

  // ---------------------------------------------------------------------------
  // GET PREVIEW
  // ---------------------------------------------------------------------------

  /**
   * Get the current path preview for rendering.
   * @returns {object} {from, points, active}
   */
  function getPreview() {
    return {
      from: sourcePin,
      points: points.slice(),
      active
    };
  }

  // ---------------------------------------------------------------------------
  // TO OPERATIONS (EngineInterface-compatible operation objects)
  // ---------------------------------------------------------------------------

  /**
   * Convert a completed connection's commands to engine-compatible operations.
   * Use this when submitting through EngineInterface instead of executor.
   *
   * @param {object[]} commands — array from clickPin() completion (connect + route)
   * @returns {object} { circuitOp, boardCmd } — circuitOp for engine, boardCmd for local executor
   */
  function toOperations(commands) {
    if (!commands || commands.length === 0) return null;

    const connectCmd = commands.find(c => c.type === 'connect');
    const routeCmd = commands.find(c => c.type === 'route');

    const result = {};

    if (connectCmd) {
      result.circuitOp = {
        kind: 'component.connect.apply',
        target: 'source',
        intent: { from: connectCmd.from, to: connectCmd.to },
      };
    }

    if (routeCmd) {
      result.boardCmd = {
        type: 'route',
        from: routeCmd.from,
        to: routeCmd.to,
        via: routeCmd.via,
      };
    }

    return result;
  }

  // ---------------------------------------------------------------------------
  // PUBLIC API
  // ---------------------------------------------------------------------------

  return { clickPin, clickPoint, escape, isActive, getPreview, toOperations };
}
