/**
 * Components Board — Engine
 * 
 * The engine composes a parser and an executor as pluggable modules.
 * Either can be replaced, extended, or versioned independently.
 * 
 * Usage:
 *   import { createEngine } from './engine.js';
 *   import { parseCommand } from './parser.js';
 *   import { createExecutor } from './executor.js';
 *   
 *   const engine = createEngine({ parser: parseCommand, executor: createExecutor() });
 *   const result = engine.run('place U1, digital.74HC04 at (50, 30) rotate 0');
 *   const state = engine.getState();
 * 
 * Custom parser:
 *   const engine = createEngine({ parser: myCustomParser, executor: createExecutor() });
 * 
 * Custom executor:
 *   const engine = createEngine({ parser: parseCommand, executor: myCustomExecutor });
 * 
 * Module contract:
 *   parser(text: string) => {type: string, ...params} | {type: 'error', message, input}
 *   executor.execute(parsedCommand) => {success, message, command} | {success: false, error, command}
 *   executor.undo() => {success, message}
 *   executor.redo() => {success, message}
 *   executor.getState() => {component, board, config, selection, viewport, history, pages}
 */

/**
 * Create an engine instance with pluggable parser and executor.
 * 
 * @param {object} modules
 * @param {function} modules.parser - Parse command text/JSON into operation object
 * @param {object} modules.executor - Executor instance with execute/undo/redo/getState
 * @param {object} [modules.middleware] - Optional middleware array [{before, after}]
 * @returns {object} Engine API
 */
export function createEngine({ parser, executor, middleware = [], maxCommandsPerSecond = 60 }) {
  if (typeof parser !== 'function') {
    throw new Error('Engine requires a parser function');
  }
  if (!executor || typeof executor.execute !== 'function') {
    throw new Error('Engine requires an executor with execute() method');
  }

  const log = [];

  // Rate limiter: sliding window (prevents bot spam / infinite loops)
  const rateWindow = [];
  const RATE_LIMIT = maxCommandsPerSecond;

  function isRateLimited() {
    const now = Date.now();
    while (rateWindow.length > 0 && rateWindow[0] < now - 1000) {
      rateWindow.shift();
    }
    return rateWindow.length >= RATE_LIMIT;
  }

  function recordCommand() {
    rateWindow.push(Date.now());
  }

  /**
   * Run a command through the full pipeline: parse → middleware.before → execute → middleware.after → log.
   * @param {string} input - Human text or JSON command string
   * @returns {object} {success, message, command, parsed}
   */
  function run(input) {
    // Rate limit: reject if too many commands per second
    if (isRateLimited()) {
      const entry = { timestamp: Date.now(), input, parsed: null, result: { success: false, error: `Rate limited: max ${RATE_LIMIT} commands/second. Slow down.` } };
      log.push(entry);
      return { success: false, error: entry.result.error, command: null, parsed: null };
    }
    recordCommand();

    // Parse
    const parsed = parser(input);
    if (parsed.type === 'error') {
      const entry = { timestamp: Date.now(), input, parsed, result: { success: false, error: parsed.message } };
      log.push(entry);
      return { success: false, error: parsed.message, command: null, parsed };
    }

    // Middleware: before execute
    for (const mw of middleware) {
      if (mw.before) {
        const blocked = mw.before(parsed, executor.getState());
        if (blocked) {
          const entry = { timestamp: Date.now(), input, parsed, result: { success: false, error: blocked.reason } };
          log.push(entry);
          return { success: false, error: blocked.reason, command: parsed, parsed };
        }
      }
    }

    // Execute
    const result = executor.execute(parsed);

    // Middleware: after execute
    for (const mw of middleware) {
      if (mw.after) {
        mw.after(parsed, result, executor.getState());
      }
    }

    // Log
    const entry = { timestamp: Date.now(), input, parsed, result };
    log.push(entry);

    return { ...result, parsed };
  }

  /**
   * Run a batch of commands (text or JSON strings).
   * Stops on first failure unless options.continueOnError is true.
   * @param {string[]} commands
   * @param {object} [options]
   * @returns {object[]} Array of results
   */
  function runBatch(commands, options = {}) {
    const results = [];
    for (const cmd of commands) {
      const result = run(cmd);
      results.push(result);
      if (!result.success && !options.continueOnError) break;
    }
    return results;
  }

  /**
   * Get complete engine state (for rendering by any client).
   */
  function getState() {
    return executor.getState();
  }

  /**
   * Get command log (for Command viewport, replay, debugging).
   */
  function getLog() {
    return [...log];
  }

  /**
   * Clear command log.
   */
  function clearLog() {
    log.length = 0;
  }

  /**
   * Get engine module info (for versioning/debugging).
   */
  function getModules() {
    return {
      parser: parser.name || 'anonymous',
      executor: executor.constructor?.name || 'executor',
      middleware: middleware.map(m => m.name || 'anonymous'),
    };
  }

  /**
   * Replace the parser at runtime (hot-swap).
   */
  function setParser(newParser) {
    if (typeof newParser !== 'function') {
      throw new Error('Parser must be a function');
    }
    parser = newParser;
  }

  /**
   * Add middleware at runtime.
   */
  function addMiddleware(mw) {
    middleware.push(mw);
  }

  return Object.freeze({
    run,
    runBatch,
    getState,
    getLog,
    clearLog,
    getModules,
    setParser,
    addMiddleware,
    // Direct access to executor for undo/redo
    undo: () => executor.undo(),
    redo: () => executor.redo(),
  });
}
