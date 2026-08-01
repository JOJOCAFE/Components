/**
 * Components Board — Status Bar
 * Task 1.7: DOM-free status bar state manager.
 *
 * Tracks current tool, cursor position, zoom, paper info,
 * and document modified state. A thin DOM adapter renders this state.
 *
 * ES module syntax, Node.js compatible, no browser APIs.
 */

/**
 * Create a status bar controller.
 * @param {object} engine - The engine instance (from createEngine)
 * @param {object} viewport - The viewport instance (from createViewport)
 * @returns {object} Status bar API
 */
export function createStatusBar(engine, viewport) {
  if (!engine || typeof engine.getState !== 'function') {
    throw new Error('StatusBar requires an engine with getState() method');
  }
  if (!viewport || typeof viewport.getViewState !== 'function') {
    throw new Error('StatusBar requires a viewport with getViewState() method');
  }

  let tool = 'select';
  let cursorX = 0;
  let cursorY = 0;
  let modified = false;

  /**
   * Get full status bar state.
   * @returns {object} {tool, cursorX, cursorY, zoom, paperSize, orientation, modified}
   */
  function getState() {
    const viewState = viewport.getViewState();
    const engineState = engine.getState();
    const config = engineState.config;

    return {
      tool,
      cursorX,
      cursorY,
      zoom: viewState.zoom,
      paperSize: config.paper.size,
      orientation: config.paper.orientation,
      modified,
    };
  }

  /**
   * Set the current active tool name.
   * @param {string} name - Tool name
   */
  function setTool(name) {
    tool = name;
  }

  /**
   * Set cursor position in world mm.
   * @param {number} worldX
   * @param {number} worldY
   */
  function setCursor(worldX, worldY) {
    cursorX = worldX;
    cursorY = worldY;
  }

  /**
   * Get formatted cursor position string.
   * @returns {string} e.g. "x: 42.5  y: -15.0 mm"
   */
  function getFormattedCursor() {
    const xStr = Number.isInteger(cursorX) ? cursorX.toFixed(1) : parseFloat(cursorX.toFixed(1)).toString();
    const yStr = Number.isInteger(cursorY) ? cursorY.toFixed(1) : parseFloat(cursorY.toFixed(1)).toString();
    // Always show one decimal place
    const xFormatted = cursorX.toFixed(1);
    const yFormatted = cursorY.toFixed(1);
    return `x: ${xFormatted}  y: ${yFormatted} mm`;
  }

  /**
   * Get formatted zoom level string.
   * @returns {string} e.g. "100%"
   */
  function getFormattedZoom() {
    const viewState = viewport.getViewState();
    return `${Math.round(viewState.zoom)}%`;
  }

  /**
   * Get formatted paper info string.
   * @returns {string} e.g. "A4 L" or "A3 P"
   */
  function getFormattedPaper() {
    const engineState = engine.getState();
    const config = engineState.config;
    const initial = config.paper.orientation === 'landscape' ? 'L' : 'P';
    return `${config.paper.size} ${initial}`;
  }

  /**
   * Set document modified state.
   * @param {boolean} bool
   */
  function setModified(bool) {
    modified = Boolean(bool);
  }

  return Object.freeze({
    getState,
    setTool,
    setCursor,
    getFormattedCursor,
    getFormattedZoom,
    getFormattedPaper,
    setModified,
  });
}
