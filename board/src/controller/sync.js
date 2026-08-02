/**
 * Components Board — Page Sync Controller
 * Phase 2, Task 2.3: Synchronize page tabs with editors
 *
 * When user switches page tab:
 *   1. Detect @page offset in both files (circuit + board)
 *   2. Scroll both editors to the matching @page section
 *   3. Set highlight on the @page line
 *
 * When user clicks device in viewport:
 *   1. Find device line in Components:circuit
 *   2. Find placement line in Components:board
 *   3. Highlight + scroll both editors
 *
 * Pure functions. Takes file models + editor states, returns new editor states.
 * No DOM, no side effects.
 */

import { getPageOffset, findDeviceLine, findPlacementLine, findDevicePage } from '../model/file.js';
import { setCursor, scrollToLine, scrollToCursor, setHighlight, clearHighlight, highlightAndScroll } from '../view/editor.js';

// =============================================================================
// PAGE SWITCH SYNC
// =============================================================================

/**
 * Sync editors to a page switch.
 * Returns new editor states for both circuit and board editors.
 *
 * @param {object} circuitFile — parsed Components:circuit file
 * @param {object} boardFile — parsed Components:board file
 * @param {object} circuitEditor — current circuit editor state
 * @param {object} boardEditor — current board editor state
 * @param {string} pageName — page to switch to
 * @returns {{ circuitEditor, boardEditor }} new editor states
 */
export function syncToPage(circuitFile, boardFile, circuitEditor, boardEditor, pageName) {
  const circuitOffset = getPageOffset(circuitFile, pageName);
  const boardOffset = getPageOffset(boardFile, pageName);

  let newCircuitEditor = circuitEditor;
  let newBoardEditor = boardEditor;

  // Sync circuit editor
  if (circuitOffset >= 0) {
    newCircuitEditor = highlightAndScroll(newCircuitEditor, circuitOffset);
  } else {
    newCircuitEditor = clearHighlight(newCircuitEditor);
  }

  // Sync board editor
  if (boardOffset >= 0) {
    newBoardEditor = highlightAndScroll(newBoardEditor, boardOffset);
  } else {
    newBoardEditor = clearHighlight(newBoardEditor);
  }

  return { circuitEditor: newCircuitEditor, boardEditor: newBoardEditor };
}

// =============================================================================
// DEVICE CLICK SYNC (viewport → editors)
// =============================================================================

/**
 * Sync editors when a device is clicked in the viewport.
 * Highlights the device line in circuit editor and placement line in board editor.
 *
 * @param {object} circuitFile — parsed Components:circuit file
 * @param {object} boardFile — parsed Components:board file
 * @param {object} circuitEditor — current circuit editor state
 * @param {object} boardEditor — current board editor state
 * @param {string} ref — device reference (e.g. 'U1')
 * @returns {{ circuitEditor, boardEditor, page: string|null }} new states + page name
 */
export function syncToDevice(circuitFile, boardFile, circuitEditor, boardEditor, ref) {
  const circuitLine = findDeviceLine(circuitFile, ref);
  const boardLine = findPlacementLine(boardFile, ref);
  const page = findDevicePage(circuitFile, ref);

  let newCircuitEditor = circuitEditor;
  let newBoardEditor = boardEditor;

  // Sync circuit editor to device line
  if (circuitLine >= 0) {
    newCircuitEditor = highlightAndScroll(newCircuitEditor, circuitLine);
  } else {
    newCircuitEditor = clearHighlight(newCircuitEditor);
  }

  // Sync board editor to placement line
  if (boardLine >= 0) {
    newBoardEditor = highlightAndScroll(newBoardEditor, boardLine);
  } else {
    newBoardEditor = clearHighlight(newBoardEditor);
  }

  return { circuitEditor: newCircuitEditor, boardEditor: newBoardEditor, page };
}

// =============================================================================
// FIND WHICH PAGE IS VISIBLE (editor → page tab)
// =============================================================================

/**
 * Determine which page the editor cursor is currently in.
 * Useful for keeping page tabs in sync when user scrolls/navigates the editor.
 *
 * @param {object} file — parsed file model
 * @param {object} editorState — current editor state
 * @returns {string} page name (or '' for default/unnamed page)
 */
export function getCurrentPage(file, editorState) {
  const cursorLine = editorState.cursor.line;

  // Walk pages in reverse to find which one contains the cursor
  for (let i = file.pages.length - 1; i >= 0; i--) {
    const page = file.pages[i];
    if (cursorLine >= page.startLine) {
      return page.name;
    }
  }
  return '';
}

// =============================================================================
// BATCH: sync both editors + determine active page
// =============================================================================

/**
 * Full sync state: given file models and editor states, compute what page is active.
 * @param {object} circuitFile
 * @param {object} circuitEditor
 * @returns {string} active page name
 */
export function getActivePageFromEditor(circuitFile, circuitEditor) {
  return getCurrentPage(circuitFile, circuitEditor);
}

/**
 * Create initial sync state from file content.
 * Returns editor states positioned at the first page.
 *
 * @param {object} circuitFile — parsed Components:circuit
 * @param {object} boardFile — parsed Components:board
 * @param {object} circuitEditor — base circuit editor
 * @param {object} boardEditor — base board editor
 * @returns {{ circuitEditor, boardEditor, activePage: string }}
 */
export function initSync(circuitFile, boardFile, circuitEditor, boardEditor) {
  const pages = circuitFile.pages.filter(p => p.name !== '');
  if (pages.length === 0) {
    return { circuitEditor, boardEditor, activePage: '' };
  }

  const firstPage = pages[0].name;
  const result = syncToPage(circuitFile, boardFile, circuitEditor, boardEditor, firstPage);
  return { ...result, activePage: firstPage };
}
