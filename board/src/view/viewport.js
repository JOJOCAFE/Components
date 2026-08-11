/**
 * Components Board — Viewport Renderer
 * Task 1.6: Computes render data (geometry, coordinates, grid lines).
 *
 * DOM-free. Pure math: input coordinates → output screen coordinates.
 * A thin DOM/SVG adapter will consume the output later.
 *
 * Coordinate system:
 *   - World: paper center = (0, 0), units in mm
 *   - Screen: pixels, origin top-left
 *   - Zoom 100% = 1mm = 1 screen unit
 *   - Pan is in world mm
 *
 * Formulas:
 *   screenX = (worldX + panX) * (zoom / 100) + screenWidth / 2
 *   worldX  = (screenX - screenWidth / 2) / (zoom / 100) - panX
 */

const MIN_ZOOM = 10;
const MAX_ZOOM = 5000;

/**
 * Create a viewport instance bound to a config.
 * @param {object} config - Board config (read-only, from createConfig)
 * @returns {object} Viewport API
 */
export function createViewport(config) {
  const width_mm = config.paper.width_mm;
  const height_mm = config.paper.height_mm;

  let zoom = 100; // percent
  let panX = 0;   // mm (world)
  let panY = 0;   // mm (world)

  // --- Internal helpers ---

  function clampZoom(z) {
    return Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, z));
  }

  function scale() {
    return zoom / 100;
  }

  function toScreenX(worldX, screenWidth) {
    return (worldX + panX) * scale() + screenWidth / 2;
  }

  function toScreenY(worldY, screenHeight) {
    return (worldY + panY) * scale() + screenHeight / 2;
  }

  function toWorldX(screenX, screenWidth) {
    return (screenX - screenWidth / 2) / scale() - panX;
  }

  function toWorldY(screenY, screenHeight) {
    return (screenY - screenHeight / 2) / scale() - panY;
  }

  // --- Public API ---

  /**
   * Get current view state.
   */
  function getViewState() {
    return { zoom, panX, panY, width_mm, height_mm };
  }

  /**
   * Set zoom level (clamped to 10–1000%).
   * @param {number} percent
   * @returns {object} new view state
   */
  function setZoom(percent) {
    zoom = clampZoom(percent);
    return getViewState();
  }

  /**
   * Calculate zoom to fit entire paper within given screen size.
   * Adds 5% padding so paper doesn't touch edges.
   * @param {number} screenWidth
   * @param {number} screenHeight
   * @returns {object} new view state
   */
  function zoomFit(screenWidth, screenHeight) {
    const padding = 0.95; // 5% margin
    const zoomX = (screenWidth / width_mm) * 100 * padding;
    const zoomY = (screenHeight / height_mm) * 100 * padding;
    zoom = clampZoom(Math.min(zoomX, zoomY));
    panX = 0;
    panY = 0;
    return getViewState();
  }

  /**
   * Set pan offset in world mm.
   * @param {number} x
   * @param {number} y
   * @returns {object} new view state
   */
  function setPan(x, y) {
    panX = x;
    panY = y;
    return getViewState();
  }

  /**
   * Pan by a screen-pixel delta. Converts pixels to world offset.
   * @param {number} dx — screen pixels horizontal
   * @param {number} dy — screen pixels vertical
   * @returns {object} new view state
   */
  function panByScreenDelta(dx, dy) {
    panX += dx / scale();
    panY += dy / scale();
    return getViewState();
  }

  /**
   * Zoom anchored at a screen point (pointer-anchored scroll-to-zoom).
   * The world point under the pointer stays fixed on screen after zoom.
   * @param {number} factor — multiplier (e.g. 1.1 to zoom in, 0.9 to zoom out)
   * @param {number} screenX — pointer X in screen pixels
   * @param {number} screenY — pointer Y in screen pixels
   * @param {number} screenWidth
   * @param {number} screenHeight
   * @returns {object} new view state
   */
  function zoomAtPoint(factor, screenX, screenY, screenWidth, screenHeight) {
    // World point under pointer BEFORE zoom
    const worldX = toWorldX(screenX, screenWidth);
    const worldY = toWorldY(screenY, screenHeight);

    // Apply zoom
    const newZoom = clampZoom(zoom * factor);
    if (newZoom === zoom) return getViewState(); // clamped, no change
    zoom = newZoom;

    // After zoom, adjust pan so that same world point is still under pointer
    // screenX = (worldX + panX) * scale() + screenWidth / 2
    // → panX = (screenX - screenWidth / 2) / scale() - worldX
    panX = (screenX - screenWidth / 2) / scale() - worldX;
    panY = (screenY - screenHeight / 2) / scale() - worldY;

    return getViewState();
  }

  /**
   * Convert screen pixel to world mm.
   */
  function screenToWorld(screenX, screenY, screenWidth, screenHeight) {
    return {
      x: toWorldX(screenX, screenWidth),
      y: toWorldY(screenY, screenHeight),
    };
  }

  /**
   * Convert world mm to screen pixel.
   */
  function worldToScreen(worldX, worldY, screenWidth, screenHeight) {
    return {
      x: toScreenX(worldX, screenWidth),
      y: toScreenY(worldY, screenHeight),
    };
  }

  /**
   * Compute grid line data for the current view.
   * Returns lines in screen coordinates, labels with mm values.
   * @param {number} screenWidth
   * @param {number} screenHeight
   * @returns {{major: Array, minor: Array, labels: Array}}
   */
  function getGridLines(screenWidth, screenHeight) {
    const majorSpacing = config.grid.major_mm;
    const minorSpacing = config.grid.minor_mm;

    // Visible world range
    const worldLeft = toWorldX(0, screenWidth);
    const worldRight = toWorldX(screenWidth, screenWidth);
    const worldTop = toWorldY(0, screenHeight);
    const worldBottom = toWorldY(screenHeight, screenHeight);

    const major = [];
    const minor = [];
    const labels = [];

    // --- Vertical lines (x-axis) ---
    const xStart = Math.floor(worldLeft / minorSpacing) * minorSpacing;
    const xEnd = Math.ceil(worldRight / minorSpacing) * minorSpacing;

    for (let wx = xStart; wx <= xEnd; wx += minorSpacing) {
      // Avoid floating-point drift
      const snapped = Math.round(wx / minorSpacing) * minorSpacing;
      const sx = toScreenX(snapped, screenWidth);
      const line = { x1: sx, y1: 0, x2: sx, y2: screenHeight };

      const isMajor = Math.abs(Math.round(snapped / majorSpacing) * majorSpacing - snapped) < minorSpacing * 0.01;

      if (isMajor) {
        major.push(line);
        labels.push({ text: `${Math.round(snapped)}`, x: sx, y: 12 });
      } else {
        minor.push(line);
      }
    }

    // --- Horizontal lines (y-axis) ---
    const yStart = Math.floor(worldTop / minorSpacing) * minorSpacing;
    const yEnd = Math.ceil(worldBottom / minorSpacing) * minorSpacing;

    for (let wy = yStart; wy <= yEnd; wy += minorSpacing) {
      const snapped = Math.round(wy / minorSpacing) * minorSpacing;
      const sy = toScreenY(snapped, screenHeight);
      const line = { x1: 0, y1: sy, x2: screenWidth, y2: sy };

      const isMajor = Math.abs(Math.round(snapped / majorSpacing) * majorSpacing - snapped) < minorSpacing * 0.01;

      if (isMajor) {
        major.push(line);
        labels.push({ text: `${Math.round(snapped)}`, x: 4, y: sy });
      } else {
        minor.push(line);
      }
    }

    return { major, minor, labels };
  }

  /**
   * Get paper rectangle in screen coordinates.
   * @param {number} screenWidth
   * @param {number} screenHeight
   * @returns {{x: number, y: number, width: number, height: number}}
   */
  function getPaperRect(screenWidth, screenHeight) {
    // Paper corners in world: top-left = (-w/2, -h/2), bottom-right = (w/2, h/2)
    const topLeft = worldToScreen(-width_mm / 2, -height_mm / 2, screenWidth, screenHeight);
    const bottomRight = worldToScreen(width_mm / 2, height_mm / 2, screenWidth, screenHeight);
    return {
      x: topLeft.x,
      y: topLeft.y,
      width: bottomRight.x - topLeft.x,
      height: bottomRight.y - topLeft.y,
    };
  }

  /**
   * Get margin rectangle in screen coordinates (paper minus margins).
   * @param {number} screenWidth
   * @param {number} screenHeight
   * @returns {{x: number, y: number, width: number, height: number}}
   */
  function getMarginRect(screenWidth, screenHeight) {
    const margin = config.paper.margin_mm;
    const marginLeft = -width_mm / 2 + margin.left;
    const marginTop = -height_mm / 2 + margin.top;
    const marginRight = width_mm / 2 - margin.right;
    const marginBottom = height_mm / 2 - margin.bottom;

    const topLeft = worldToScreen(marginLeft, marginTop, screenWidth, screenHeight);
    const bottomRight = worldToScreen(marginRight, marginBottom, screenWidth, screenHeight);
    return {
      x: topLeft.x,
      y: topLeft.y,
      width: bottomRight.x - topLeft.x,
      height: bottomRight.y - topLeft.y,
    };
  }

  /**
   * Produce complete render data from engine state.
   * All world positions are converted to screen coordinates.
   * @param {object} state - Engine state {component, board, config, ...}
   * @param {number} screenWidth
   * @param {number} screenHeight
   * @returns {object} Render data ready for DOM adapter
   */
  function getRenderData(state, screenWidth, screenHeight) {
    const paper = getPaperRect(screenWidth, screenHeight);
    const margin = getMarginRect(screenWidth, screenHeight);
    const grid = getGridLines(screenWidth, screenHeight);

    // Devices: merge component.devices + board.placements
    const devices = [];
    if (state.component && state.board) {
      const allDevices = state.component.devices || {};
      const placements = state.board.placements || {};

      for (const ref of Object.keys(allDevices)) {
        const device = allDevices[ref];
        const placement = placements[ref];
        const x = placement ? placement.x : 0;
        const y = placement ? placement.y : 0;
        const rotation = placement ? placement.rotation : 0;
        const screen = worldToScreen(x, y, screenWidth, screenHeight);
        devices.push({
          ref: device.ref,
          part: device.part,
          x,
          y,
          rotation,
          screenX: screen.x,
          screenY: screen.y,
        });
      }
    }

    // Connections (from component model)
    const connections = [];
    if (state.component && state.component.connections) {
      for (const conn of state.component.connections) {
        connections.push({
          from: conn.from,
          to: conn.to,
          via: (conn.via || []).map(pt => {
            const s = worldToScreen(pt.x, pt.y, screenWidth, screenHeight);
            return { x: pt.x, y: pt.y, screenX: s.x, screenY: s.y };
          }),
        });
      }
    }

    // Routes (from board model)
    const routes = [];
    if (state.board && state.board.routes) {
      for (const route of state.board.routes) {
        routes.push({
          from: route.from,
          to: route.to,
          via: (route.via || []).map(pt => {
            const s = worldToScreen(pt.x, pt.y, screenWidth, screenHeight);
            return { x: pt.x, y: pt.y, screenX: s.x, screenY: s.y };
          }),
        });
      }
    }

    // Labels (from board model)
    const labelsOut = [];
    if (state.board && state.board.labels) {
      for (const label of state.board.labels) {
        const s = worldToScreen(label.x, label.y, screenWidth, screenHeight);
        labelsOut.push({
          id: label.id,
          text: label.text,
          x: label.x,
          y: label.y,
          screenX: s.x,
          screenY: s.y,
        });
      }
    }

    return { paper, margin, grid, devices, connections, routes, labels: labelsOut };
  }

  return Object.freeze({
    getViewState,
    setZoom,
    zoomFit,
    setPan,
    panByScreenDelta,
    zoomAtPoint,
    screenToWorld,
    worldToScreen,
    getGridLines,
    getPaperRect,
    getMarginRect,
    getRenderData,
  });
}
