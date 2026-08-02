/**
 * Components Board — Editor State
 * Phase 2, Task 2.2: DOM-free text editor state model
 *
 * Manages: lines, cursor, selection, scroll, highlight.
 * Pure state object + functions. No DOM, no rendering.
 * ES module syntax, Node.js compatible.
 *
 * State shape:
 *   {
 *     lines: string[],
 *     cursor: { line: number, col: number },
 *     selection: { start: {line, col}, end: {line, col} } | null,
 *     scroll: { line: number, col: number },
 *     highlight: { line: number, length: number } | null,
 *     visibleLines: number,    // how many lines fit in the viewport
 *     readOnly: boolean,
 *   }
 */

// =============================================================================
// CREATE
// =============================================================================

/**
 * Create a new editor state from text content.
 * @param {string} text — file content (or empty string)
 * @param {object} [opts] — { visibleLines, readOnly }
 * @returns {object} editor state
 */
export function createEditor(text = '', opts = {}) {
  const lines = text.split('\n');
  return {
    lines,
    cursor: { line: 0, col: 0 },
    selection: null,
    scroll: { line: 0, col: 0 },
    highlight: null,
    visibleLines: opts.visibleLines || 30,
    readOnly: opts.readOnly || false,
  };
}

// =============================================================================
// CURSOR MOVEMENT
// =============================================================================

/**
 * Move cursor to specific position. Clamps to valid range.
 * @param {object} state
 * @param {number} line
 * @param {number} col
 * @returns {object} new state
 */
export function setCursor(state, line, col) {
  const l = clampLine(state, line);
  const c = clampCol(state, l, col);
  return { ...state, cursor: { line: l, col: c }, selection: null };
}

/**
 * Move cursor up by n lines.
 */
export function cursorUp(state, n = 1) {
  return setCursor(state, state.cursor.line - n, state.cursor.col);
}

/**
 * Move cursor down by n lines.
 */
export function cursorDown(state, n = 1) {
  return setCursor(state, state.cursor.line + n, state.cursor.col);
}

/**
 * Move cursor left by n columns. Wraps to previous line end.
 */
export function cursorLeft(state, n = 1) {
  let { line, col } = state.cursor;
  col -= n;
  while (col < 0 && line > 0) {
    line--;
    col += state.lines[line].length + 1; // +1 for the newline
  }
  if (col < 0) col = 0;
  return setCursor(state, line, col);
}

/**
 * Move cursor right by n columns. Wraps to next line start.
 */
export function cursorRight(state, n = 1) {
  let { line, col } = state.cursor;
  col += n;
  while (line < state.lines.length - 1 && col > state.lines[line].length) {
    col -= state.lines[line].length + 1;
    line++;
  }
  const maxCol = state.lines[line] ? state.lines[line].length : 0;
  if (col > maxCol) col = maxCol;
  return setCursor(state, line, col);
}

/**
 * Move cursor to start of line.
 */
export function cursorHome(state) {
  return setCursor(state, state.cursor.line, 0);
}

/**
 * Move cursor to end of line.
 */
export function cursorEnd(state) {
  const lineLen = state.lines[state.cursor.line]?.length || 0;
  return setCursor(state, state.cursor.line, lineLen);
}

/**
 * Move cursor to start of document.
 */
export function cursorDocStart(state) {
  return setCursor(state, 0, 0);
}

/**
 * Move cursor to end of document.
 */
export function cursorDocEnd(state) {
  const lastLine = state.lines.length - 1;
  const lastCol = state.lines[lastLine]?.length || 0;
  return setCursor(state, lastLine, lastCol);
}

// =============================================================================
// SELECTION
// =============================================================================

/**
 * Set selection range.
 * @param {object} state
 * @param {{line: number, col: number}} start
 * @param {{line: number, col: number}} end
 * @returns {object} new state
 */
export function setSelection(state, start, end) {
  const s = {
    line: clampLine(state, start.line),
    col: clampCol(state, clampLine(state, start.line), start.col),
  };
  const e = {
    line: clampLine(state, end.line),
    col: clampCol(state, clampLine(state, end.line), end.col),
  };
  return { ...state, selection: { start: s, end: e } };
}

/**
 * Clear selection.
 */
export function clearSelection(state) {
  return { ...state, selection: null };
}

/**
 * Select entire line.
 */
export function selectLine(state, line) {
  const l = clampLine(state, line);
  const lineLen = state.lines[l]?.length || 0;
  return setSelection(state, { line: l, col: 0 }, { line: l, col: lineLen });
}

/**
 * Select all text.
 */
export function selectAll(state) {
  const lastLine = state.lines.length - 1;
  const lastCol = state.lines[lastLine]?.length || 0;
  return setSelection(state, { line: 0, col: 0 }, { line: lastLine, col: lastCol });
}

/**
 * Get selected text (or empty string if no selection).
 */
export function getSelectedText(state) {
  if (!state.selection) return '';
  const { start, end } = normalizeSelection(state.selection);
  if (start.line === end.line) {
    return state.lines[start.line].slice(start.col, end.col);
  }
  const parts = [];
  parts.push(state.lines[start.line].slice(start.col));
  for (let i = start.line + 1; i < end.line; i++) {
    parts.push(state.lines[i]);
  }
  parts.push(state.lines[end.line].slice(0, end.col));
  return parts.join('\n');
}

// =============================================================================
// SCROLL
// =============================================================================

/**
 * Set scroll position (top-left visible line/col).
 */
export function setScroll(state, line, col = 0) {
  const maxLine = Math.max(0, state.lines.length - 1);
  const l = Math.max(0, Math.min(line, maxLine));
  const c = Math.max(0, col);
  return { ...state, scroll: { line: l, col: c } };
}

/**
 * Scroll to make cursor visible (auto-scroll).
 */
export function scrollToCursor(state) {
  let { line: scrollLine, col: scrollCol } = state.scroll;
  const { line: curLine } = state.cursor;

  // Vertical: keep cursor within visible range
  if (curLine < scrollLine) {
    scrollLine = curLine;
  } else if (curLine >= scrollLine + state.visibleLines) {
    scrollLine = curLine - state.visibleLines + 1;
  }

  return setScroll(state, scrollLine, scrollCol);
}

/**
 * Scroll to a specific line (put it at top of viewport).
 */
export function scrollToLine(state, line) {
  return setScroll(state, line, state.scroll.col);
}

/**
 * Page down.
 */
export function pageDown(state) {
  const newScroll = state.scroll.line + state.visibleLines;
  const newCursor = state.cursor.line + state.visibleLines;
  let s = setScroll(state, newScroll);
  s = setCursor(s, newCursor, state.cursor.col);
  return s;
}

/**
 * Page up.
 */
export function pageUp(state) {
  const newScroll = state.scroll.line - state.visibleLines;
  const newCursor = state.cursor.line - state.visibleLines;
  let s = setScroll(state, newScroll);
  s = setCursor(s, newCursor, state.cursor.col);
  return s;
}

// =============================================================================
// HIGHLIGHT (for viewport-to-editor sync)
// =============================================================================

/**
 * Highlight a line (e.g. device clicked in viewport).
 * @param {object} state
 * @param {number} line — 0-based line number
 * @returns {object} new state with highlight set
 */
export function setHighlight(state, line) {
  const l = clampLine(state, line);
  const length = state.lines[l]?.length || 0;
  return { ...state, highlight: { line: l, length } };
}

/**
 * Clear highlight.
 */
export function clearHighlight(state) {
  return { ...state, highlight: null };
}

/**
 * Highlight and scroll to line (combined action for viewport click).
 */
export function highlightAndScroll(state, line) {
  let s = setHighlight(state, line);
  s = setCursor(s, line, 0);
  s = scrollToCursor(s);
  return s;
}

// =============================================================================
// TEXT EDITING
// =============================================================================

/**
 * Insert text at cursor position.
 * @param {object} state
 * @param {string} text
 * @returns {object} new state
 */
export function insertText(state, text) {
  if (state.readOnly) return state;

  // If there's a selection, delete it first
  let s = state;
  if (s.selection) {
    s = deleteSelection(s);
  }

  const { line, col } = s.cursor;
  const currentLine = s.lines[line] || '';
  const insertLines = text.split('\n');
  const newLines = [...s.lines];

  if (insertLines.length === 1) {
    // Single line insert
    newLines[line] = currentLine.slice(0, col) + insertLines[0] + currentLine.slice(col);
    return setCursor({ ...s, lines: newLines }, line, col + insertLines[0].length);
  }

  // Multi-line insert
  const before = currentLine.slice(0, col);
  const after = currentLine.slice(col);
  newLines.splice(line, 1,
    before + insertLines[0],
    ...insertLines.slice(1, -1),
    insertLines[insertLines.length - 1] + after
  );
  const newLine = line + insertLines.length - 1;
  const newCol = insertLines[insertLines.length - 1].length;
  return setCursor({ ...s, lines: newLines }, newLine, newCol);
}

/**
 * Delete selection content.
 */
export function deleteSelection(state) {
  if (state.readOnly || !state.selection) return state;
  const { start, end } = normalizeSelection(state.selection);
  const newLines = [...state.lines];
  const before = state.lines[start.line].slice(0, start.col);
  const after = state.lines[end.line].slice(end.col);
  newLines.splice(start.line, end.line - start.line + 1, before + after);
  return setCursor({ ...state, lines: newLines, selection: null }, start.line, start.col);
}

/**
 * Delete character at cursor (like Delete key).
 */
export function deleteForward(state) {
  if (state.readOnly) return state;
  if (state.selection) return deleteSelection(state);

  const { line, col } = state.cursor;
  const currentLine = state.lines[line] || '';

  if (col < currentLine.length) {
    // Delete char in current line
    const newLines = [...state.lines];
    newLines[line] = currentLine.slice(0, col) + currentLine.slice(col + 1);
    return { ...state, lines: newLines };
  } else if (line < state.lines.length - 1) {
    // Join with next line
    const newLines = [...state.lines];
    newLines.splice(line, 2, currentLine + state.lines[line + 1]);
    return { ...state, lines: newLines };
  }
  return state;
}

/**
 * Delete character before cursor (like Backspace key).
 */
export function deleteBackward(state) {
  if (state.readOnly) return state;
  if (state.selection) return deleteSelection(state);

  const { line, col } = state.cursor;

  if (col > 0) {
    const currentLine = state.lines[line];
    const newLines = [...state.lines];
    newLines[line] = currentLine.slice(0, col - 1) + currentLine.slice(col);
    return setCursor({ ...state, lines: newLines }, line, col - 1);
  } else if (line > 0) {
    // Join with previous line
    const prevLine = state.lines[line - 1];
    const currentLine = state.lines[line];
    const newLines = [...state.lines];
    newLines.splice(line - 1, 2, prevLine + currentLine);
    return setCursor({ ...state, lines: newLines }, line - 1, prevLine.length);
  }
  return state;
}

/**
 * Insert newline at cursor.
 */
export function insertNewline(state) {
  return insertText(state, '\n');
}

// =============================================================================
// CONTENT ACCESS
// =============================================================================

/**
 * Get full text content.
 */
export function getText(state) {
  return state.lines.join('\n');
}

/**
 * Set full text content (resets cursor/selection).
 */
export function setText(state, text) {
  return createEditor(text, {
    visibleLines: state.visibleLines,
    readOnly: state.readOnly,
  });
}

/**
 * Get line count.
 */
export function getLineCount(state) {
  return state.lines.length;
}

/**
 * Get specific line content.
 */
export function getLine(state, lineNumber) {
  return state.lines[lineNumber] ?? '';
}

// =============================================================================
// HELPERS
// =============================================================================

function clampLine(state, line) {
  return Math.max(0, Math.min(line, state.lines.length - 1));
}

function clampCol(state, line, col) {
  const maxCol = state.lines[line]?.length || 0;
  return Math.max(0, Math.min(col, maxCol));
}

function normalizeSelection(selection) {
  const { start, end } = selection;
  if (start.line > end.line || (start.line === end.line && start.col > end.col)) {
    return { start: end, end: start };
  }
  return { start, end };
}
