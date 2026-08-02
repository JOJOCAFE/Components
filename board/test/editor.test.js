/**
 * Components Board — Editor State Tests
 * Phase 2, Task 2.2: Tests for DOM-free editor state
 */

import {
  createEditor,
  setCursor, cursorUp, cursorDown, cursorLeft, cursorRight,
  cursorHome, cursorEnd, cursorDocStart, cursorDocEnd,
  setSelection, clearSelection, selectLine, selectAll, getSelectedText,
  setScroll, scrollToCursor, scrollToLine, pageDown, pageUp,
  setHighlight, clearHighlight, highlightAndScroll,
  insertText, deleteSelection, deleteForward, deleteBackward, insertNewline,
  getText, setText, getLineCount, getLine,
} from '../src/view/editor.js';

// =============================================================================
// Test Harness
// =============================================================================

let passed = 0, failed = 0;
const failures = [];

function assert(condition, msg) {
  if (condition) { passed++; }
  else { failed++; failures.push(msg); }
}
function eq(a, b, msg) {
  const pass = JSON.stringify(a) === JSON.stringify(b);
  if (pass) { passed++; }
  else { failed++; failures.push(`${msg}: got ${JSON.stringify(a)}, expected ${JSON.stringify(b)}`); }
}
function section(name) { console.log(`  ${name}`); }

const SAMPLE = `@page CPU
device U1, digital.74HC04;
device U2, digital.74HC161;
connect U1.1Y -> U2.CLK;

@page Memory
device U3, memory.62256;`;

// =============================================================================
// CREATE
// =============================================================================

section('createEditor');
{
  const e = createEditor(SAMPLE);
  eq(e.lines.length, 7, 'line count');
  eq(e.cursor, { line: 0, col: 0 }, 'initial cursor');
  eq(e.selection, null, 'no initial selection');
  eq(e.scroll, { line: 0, col: 0 }, 'initial scroll');
  eq(e.highlight, null, 'no initial highlight');
  eq(e.visibleLines, 30, 'default visible lines');
  eq(e.readOnly, false, 'default not readonly');
}

section('createEditor with options');
{
  const e = createEditor('hello', { visibleLines: 10, readOnly: true });
  eq(e.visibleLines, 10, 'custom visible lines');
  eq(e.readOnly, true, 'custom readonly');
}

section('createEditor empty');
{
  const e = createEditor('');
  eq(e.lines, [''], 'empty editor has one empty line');
  eq(e.cursor, { line: 0, col: 0 }, 'empty cursor at 0,0');
}

// =============================================================================
// CURSOR MOVEMENT
// =============================================================================

section('setCursor');
{
  const e = createEditor(SAMPLE);
  const s = setCursor(e, 2, 5);
  eq(s.cursor, { line: 2, col: 5 }, 'cursor set');
}

section('setCursor clamps line');
{
  const e = createEditor(SAMPLE);
  const s = setCursor(e, 100, 0);
  eq(s.cursor.line, 6, 'line clamped to max');
  const s2 = setCursor(e, -5, 0);
  eq(s2.cursor.line, 0, 'line clamped to 0');
}

section('setCursor clamps col');
{
  const e = createEditor(SAMPLE);
  const s = setCursor(e, 0, 999);
  eq(s.cursor.col, e.lines[0].length, 'col clamped to line length');
  const s2 = setCursor(e, 0, -5);
  eq(s2.cursor.col, 0, 'col clamped to 0');
}

section('setCursor clears selection');
{
  const e = setSelection(createEditor(SAMPLE), { line: 0, col: 0 }, { line: 1, col: 5 });
  const s = setCursor(e, 3, 0);
  eq(s.selection, null, 'selection cleared on cursor move');
}

section('cursorUp / cursorDown');
{
  const e = setCursor(createEditor(SAMPLE), 3, 5);
  eq(cursorUp(e).cursor.line, 2, 'cursor up');
  eq(cursorDown(e).cursor.line, 4, 'cursor down');
  // Clamp at boundaries
  const top = setCursor(createEditor(SAMPLE), 0, 0);
  eq(cursorUp(top).cursor.line, 0, 'cursor up at top stays');
  const bot = setCursor(createEditor(SAMPLE), 6, 0);
  eq(cursorDown(bot).cursor.line, 6, 'cursor down at bottom stays');
}

section('cursorLeft / cursorRight');
{
  const e = setCursor(createEditor('abc\ndef'), 0, 2);
  eq(cursorLeft(e).cursor, { line: 0, col: 1 }, 'left within line');
  eq(cursorRight(e).cursor, { line: 0, col: 3 }, 'right within line');
}

section('cursorLeft wraps to previous line');
{
  const e = setCursor(createEditor('abc\ndef'), 1, 0);
  const s = cursorLeft(e);
  eq(s.cursor, { line: 0, col: 3 }, 'left wraps to prev line end');
}

section('cursorRight wraps to next line');
{
  const e = setCursor(createEditor('abc\ndef'), 0, 3);
  const s = cursorRight(e);
  eq(s.cursor, { line: 1, col: 0 }, 'right wraps to next line start');
}

section('cursorHome / cursorEnd');
{
  const e = setCursor(createEditor(SAMPLE), 1, 10);
  eq(cursorHome(e).cursor.col, 0, 'home goes to col 0');
  eq(cursorEnd(e).cursor.col, e.lines[1].length, 'end goes to line end');
}

section('cursorDocStart / cursorDocEnd');
{
  const e = setCursor(createEditor(SAMPLE), 3, 5);
  const start = cursorDocStart(e);
  eq(start.cursor, { line: 0, col: 0 }, 'doc start');
  const end = cursorDocEnd(e);
  eq(end.cursor.line, 6, 'doc end line');
  eq(end.cursor.col, e.lines[6].length, 'doc end col');
}

// =============================================================================
// SELECTION
// =============================================================================

section('setSelection');
{
  const e = createEditor(SAMPLE);
  const s = setSelection(e, { line: 0, col: 5 }, { line: 2, col: 10 });
  eq(s.selection.start, { line: 0, col: 5 }, 'selection start');
  eq(s.selection.end, { line: 2, col: 10 }, 'selection end');
}

section('clearSelection');
{
  const e = setSelection(createEditor(SAMPLE), { line: 0, col: 0 }, { line: 1, col: 5 });
  const s = clearSelection(e);
  eq(s.selection, null, 'selection cleared');
}

section('selectLine');
{
  const e = createEditor(SAMPLE);
  const s = selectLine(e, 1);
  eq(s.selection.start, { line: 1, col: 0 }, 'select line start');
  eq(s.selection.end.line, 1, 'select line end line');
  eq(s.selection.end.col, e.lines[1].length, 'select line end col');
}

section('selectAll');
{
  const e = createEditor(SAMPLE);
  const s = selectAll(e);
  eq(s.selection.start, { line: 0, col: 0 }, 'select all start');
  eq(s.selection.end.line, 6, 'select all end line');
}

section('getSelectedText — single line');
{
  const e = setSelection(createEditor('hello world'), { line: 0, col: 0 }, { line: 0, col: 5 });
  eq(getSelectedText(e), 'hello', 'selected text single line');
}

section('getSelectedText — multi line');
{
  const e = setSelection(createEditor('abc\ndef\nghi'), { line: 0, col: 1 }, { line: 2, col: 2 });
  eq(getSelectedText(e), 'bc\ndef\ngh', 'selected text multi line');
}

section('getSelectedText — no selection');
{
  const e = createEditor('hello');
  eq(getSelectedText(e), '', 'no selection empty string');
}

section('getSelectedText — reversed selection');
{
  const e = setSelection(createEditor('hello world'), { line: 0, col: 5 }, { line: 0, col: 0 });
  eq(getSelectedText(e), 'hello', 'reversed selection normalized');
}

// =============================================================================
// SCROLL
// =============================================================================

section('setScroll');
{
  const e = createEditor(SAMPLE);
  const s = setScroll(e, 3, 5);
  eq(s.scroll, { line: 3, col: 5 }, 'scroll set');
}

section('setScroll clamps');
{
  const e = createEditor(SAMPLE);
  const s = setScroll(e, -5, -3);
  eq(s.scroll, { line: 0, col: 0 }, 'scroll clamped to 0');
  const s2 = setScroll(e, 999);
  eq(s2.scroll.line, 6, 'scroll clamped to max line');
}

section('scrollToCursor — cursor below viewport');
{
  const e = createEditor(SAMPLE, { visibleLines: 3 });
  const s = setCursor(e, 5, 0);
  const scrolled = scrollToCursor(s);
  eq(scrolled.scroll.line, 3, 'scrolled to show cursor (5 - 3 + 1 = 3)');
}

section('scrollToCursor — cursor above viewport');
{
  let e = createEditor(SAMPLE, { visibleLines: 3 });
  e = { ...e, scroll: { line: 4, col: 0 }, cursor: { line: 2, col: 0 } };
  const scrolled = scrollToCursor(e);
  eq(scrolled.scroll.line, 2, 'scrolled up to show cursor');
}

section('scrollToCursor — cursor within viewport');
{
  let e = createEditor(SAMPLE, { visibleLines: 5 });
  e = { ...e, scroll: { line: 0, col: 0 }, cursor: { line: 3, col: 0 } };
  const scrolled = scrollToCursor(e);
  eq(scrolled.scroll.line, 0, 'no scroll needed');
}

section('scrollToLine');
{
  const e = createEditor(SAMPLE);
  const s = scrollToLine(e, 4);
  eq(s.scroll.line, 4, 'scroll to line 4');
}

section('pageDown');
{
  const e = createEditor(SAMPLE, { visibleLines: 3 });
  const s = pageDown(e);
  eq(s.scroll.line, 3, 'page down scroll');
  eq(s.cursor.line, 3, 'page down cursor');
}

section('pageUp');
{
  let e = createEditor(SAMPLE, { visibleLines: 3 });
  e = setCursor(e, 5, 0);
  e = setScroll(e, 4);
  const s = pageUp(e);
  eq(s.scroll.line, 1, 'page up scroll');
  eq(s.cursor.line, 2, 'page up cursor');
}

// =============================================================================
// HIGHLIGHT
// =============================================================================

section('setHighlight');
{
  const e = createEditor(SAMPLE);
  const s = setHighlight(e, 1);
  eq(s.highlight.line, 1, 'highlight line');
  eq(s.highlight.length, e.lines[1].length, 'highlight length');
}

section('clearHighlight');
{
  const e = setHighlight(createEditor(SAMPLE), 1);
  const s = clearHighlight(e);
  eq(s.highlight, null, 'highlight cleared');
}

section('highlightAndScroll');
{
  const e = createEditor(SAMPLE, { visibleLines: 3 });
  const s = highlightAndScroll(e, 5);
  eq(s.highlight.line, 5, 'highlight line set');
  eq(s.cursor.line, 5, 'cursor moved to highlighted line');
  assert(s.scroll.line <= 5 && s.scroll.line + s.visibleLines > 5, 'scroll shows highlighted line');
}

// =============================================================================
// TEXT EDITING
// =============================================================================

section('insertText — single char');
{
  const e = setCursor(createEditor('hello'), 0, 5);
  const s = insertText(e, '!');
  eq(s.lines[0], 'hello!', 'char inserted');
  eq(s.cursor, { line: 0, col: 6 }, 'cursor after insert');
}

section('insertText — middle of line');
{
  const e = setCursor(createEditor('helo'), 0, 2);
  const s = insertText(e, 'l');
  eq(s.lines[0], 'hello', 'insert middle');
}

section('insertText — multi-line');
{
  const e = setCursor(createEditor('ab'), 0, 1);
  const s = insertText(e, 'X\nY\nZ');
  eq(s.lines, ['aX', 'Y', 'Zb'], 'multi-line insert');
  eq(s.cursor, { line: 2, col: 1 }, 'cursor after multi-line insert');
}

section('insertText — replaces selection');
{
  const e = setSelection(createEditor('hello world'), { line: 0, col: 0 }, { line: 0, col: 5 });
  const s = insertText(e, 'hi');
  eq(s.lines[0], 'hi world', 'selection replaced');
  eq(s.cursor, { line: 0, col: 2 }, 'cursor after replace');
}

section('insertText — readonly does nothing');
{
  const e = createEditor('hello', { readOnly: true });
  const s = insertText(e, 'X');
  eq(s.lines[0], 'hello', 'readonly not modified');
}

section('insertNewline');
{
  const e = setCursor(createEditor('hello world'), 0, 5);
  const s = insertNewline(e);
  eq(s.lines, ['hello', ' world'], 'newline splits');
  eq(s.cursor, { line: 1, col: 0 }, 'cursor on new line');
}

section('deleteForward — char');
{
  const e = setCursor(createEditor('hello'), 0, 0);
  const s = deleteForward(e);
  eq(s.lines[0], 'ello', 'delete forward char');
}

section('deleteForward — join lines');
{
  const e = setCursor(createEditor('abc\ndef'), 0, 3);
  const s = deleteForward(e);
  eq(s.lines, ['abcdef'], 'delete forward joins');
}

section('deleteForward — at end does nothing');
{
  const e = setCursor(createEditor('hi'), 0, 2);
  const s = deleteForward(e);
  eq(s.lines, ['hi'], 'delete at end no-op');
}

section('deleteBackward — char');
{
  const e = setCursor(createEditor('hello'), 0, 3);
  const s = deleteBackward(e);
  eq(s.lines[0], 'helo', 'backspace char');
  eq(s.cursor.col, 2, 'cursor moves back');
}

section('deleteBackward — join lines');
{
  const e = setCursor(createEditor('abc\ndef'), 1, 0);
  const s = deleteBackward(e);
  eq(s.lines, ['abcdef'], 'backspace joins');
  eq(s.cursor, { line: 0, col: 3 }, 'cursor at join point');
}

section('deleteBackward — at start does nothing');
{
  const e = setCursor(createEditor('hi'), 0, 0);
  const s = deleteBackward(e);
  eq(s.lines, ['hi'], 'backspace at start no-op');
}

section('deleteSelection');
{
  const e = setSelection(createEditor('hello world'), { line: 0, col: 5 }, { line: 0, col: 11 });
  const s = deleteSelection(e);
  eq(s.lines[0], 'hello', 'selection deleted');
  eq(s.selection, null, 'selection cleared after delete');
}

section('deleteSelection — multi-line');
{
  const e = setSelection(createEditor('abc\ndef\nghi'), { line: 0, col: 1 }, { line: 2, col: 2 });
  const s = deleteSelection(e);
  eq(s.lines, ['ai'], 'multi-line delete');
  eq(s.cursor, { line: 0, col: 1 }, 'cursor at start of deleted range');
}

// =============================================================================
// CONTENT ACCESS
// =============================================================================

section('getText');
{
  const e = createEditor('hello\nworld');
  eq(getText(e), 'hello\nworld', 'getText');
}

section('setText');
{
  const e = createEditor('old text');
  const s = setText(e, 'new\ntext');
  eq(s.lines, ['new', 'text'], 'setText updates lines');
  eq(s.cursor, { line: 0, col: 0 }, 'setText resets cursor');
}

section('getLineCount');
{
  const e = createEditor(SAMPLE);
  eq(getLineCount(e), 7, 'line count');
}

section('getLine');
{
  const e = createEditor(SAMPLE);
  eq(getLine(e, 0), '@page CPU', 'getLine 0');
  eq(getLine(e, 1), 'device U1, digital.74HC04;', 'getLine 1');
  eq(getLine(e, 99), '', 'getLine out of range');
}

// =============================================================================
// RESULTS
// =============================================================================

console.log();
if (failed > 0) {
  console.log(`━━━ Results: ${passed} passed, ${failed} FAILED ━━━`);
  failures.forEach(f => console.log(`  ✗ ${f}`));
  process.exit(1);
} else {
  console.log(`━━━ Results: ${passed} passed, 0 failed ━━━`);
}
