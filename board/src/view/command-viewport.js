/**
 * Components Board — Command Viewport
 * Task 1.5: CLI-style command viewport state controller.
 *
 * DOM-independent module that manages command input, history,
 * logging, and autocomplete. A thin DOM adapter renders this state.
 *
 * ES module syntax, Node.js compatible, no browser APIs.
 */

/**
 * All known command keywords (for autocomplete).
 */
const COMMAND_KEYWORDS = Object.freeze([
  'place',
  'move',
  'rotate',
  'delete',
  'connect',
  'disconnect',
  'route',
  'label',
  'select',
  'deselect',
  'zoom',
  'pan',
  'undo',
  'redo',
  'new-page',
  'switch-page',
  'rename-page',
  'delete-page',
  'set-config',
]);

/**
 * Creates a command viewport controller.
 * @param {object} engine - The engine instance (from createEngine)
 * @returns {object} Command viewport API
 */
export function createCommandViewport(engine) {
  if (!engine || typeof engine.run !== 'function') {
    throw new Error('CommandViewport requires an engine with run() method');
  }

  /** @type {Array<{timestamp: number, input: string, success: boolean, message: string, type: string}>} */
  const log = [];

  /** @type {string[]} */
  const history = [];

  /** History navigation cursor (-1 = no navigation, 0 = most recent) */
  let historyCursor = -1;

  /**
   * Submit a command string to the engine.
   * Adds the input to history, runs it, and logs the result.
   * @param {string} text - Command text (human or JSON)
   * @returns {object} Log entry {timestamp, input, success, message, type}
   */
  function submit(text) {
    const input = (text || '').trim();
    if (!input) {
      const entry = {
        timestamp: Date.now(),
        input: '',
        success: false,
        message: 'Empty command',
        type: 'error',
      };
      log.push(entry);
      return entry;
    }

    // Add to history (always, even if command fails)
    history.push(input);
    // Reset cursor on new submit
    historyCursor = -1;

    // Run through engine
    const result = engine.run(input);

    // Build log entry
    const entry = {
      timestamp: Date.now(),
      input,
      success: result.success === true,
      message: result.success ? (result.message || 'OK') : (result.error || 'Unknown error'),
      type: result.parsed ? result.parsed.type : 'error',
    };

    log.push(entry);
    return entry;
  }

  /**
   * Get all log entries (copy).
   * @returns {Array<{timestamp: number, input: string, success: boolean, message: string, type: string}>}
   */
  function getLog() {
    return [...log];
  }

  /**
   * Get all past input strings (for display/export).
   * @returns {string[]}
   */
  function getHistory() {
    return [...history];
  }

  /**
   * Navigate history up (older commands).
   * @returns {string|null} Previous input string, or null if at beginning
   */
  function historyUp() {
    if (history.length === 0) return null;

    if (historyCursor === -1) {
      // Start navigating from the most recent
      historyCursor = history.length - 1;
      return history[historyCursor];
    }

    if (historyCursor <= 0) {
      // Already at the beginning
      return null;
    }

    historyCursor--;
    return history[historyCursor];
  }

  /**
   * Navigate history down (newer commands).
   * @returns {string|null} Next input string, or null if at end
   */
  function historyDown() {
    if (history.length === 0) return null;

    if (historyCursor === -1) {
      // Not navigating
      return null;
    }

    if (historyCursor >= history.length - 1) {
      // At the end — reset cursor
      historyCursor = -1;
      return null;
    }

    historyCursor++;
    return history[historyCursor];
  }

  /**
   * Clear the visible log.
   */
  function clear() {
    log.length = 0;
  }

  /**
   * Get command suggestions for partial input (basic keyword autocomplete).
   * @param {string} partial - Partial text typed so far
   * @returns {string[]} Matching command keywords
   */
  function getSuggestions(partial) {
    const p = (partial || '').trim().toLowerCase();
    if (p === '') {
      return [...COMMAND_KEYWORDS];
    }
    return COMMAND_KEYWORDS.filter(kw => kw.startsWith(p));
  }

  return Object.freeze({
    submit,
    getLog,
    getHistory,
    historyUp,
    historyDown,
    clear,
    getSuggestions,
  });
}
