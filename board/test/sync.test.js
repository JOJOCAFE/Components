/**
 * Components Board — Page Sync Controller Tests
 * Phase 2, Task 2.3: Tests for page↔editor synchronization
 */

import { parseFile, FILE_TYPES } from '../src/model/file.js';
import { createEditor } from '../src/view/editor.js';
import {
  syncToPage, syncToDevice, getCurrentPage, getActivePageFromEditor, initSync,
} from '../src/controller/sync.js';

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

// =============================================================================
// TEST DATA
// =============================================================================

const CIRCUIT_TEXT = `@page CPU
device U1, digital.74HC04;
device U2, digital.74HC161;
connect U1.1Y -> U2.CLK;

@page Memory
device U3, memory.62256;
connect U2.QA -> U3.A0;

@page ALU
device U4, digital.74HC283;
device U5, digital.74HC86;`;

const BOARD_TEXT = `@page CPU
paper A4 landscape;
place U1 at (50, 30) rotate 0;
place U2 at (120, 30) rotate 0;
route U1.1Y -> U2.CLK via (85, 30) (85, 45) (120, 45);

@page Memory
paper A3 landscape;
place U3 at (80, 50) rotate 0;

@page ALU
paper A4 landscape;
place U4 at (30, 20) rotate 0;
place U5 at (100, 20) rotate 0;`;

const circuitFile = parseFile(CIRCUIT_TEXT, FILE_TYPES.CIRCUIT);
const boardFile = parseFile(BOARD_TEXT, FILE_TYPES.BOARD);

function makeEditors() {
  return {
    circuitEditor: createEditor(CIRCUIT_TEXT, { visibleLines: 5 }),
    boardEditor: createEditor(BOARD_TEXT, { visibleLines: 5 }),
  };
}

// =============================================================================
// syncToPage
// =============================================================================

section('syncToPage — switch to CPU');
{
  const { circuitEditor, boardEditor } = makeEditors();
  const result = syncToPage(circuitFile, boardFile, circuitEditor, boardEditor, 'CPU');

  eq(result.circuitEditor.highlight.line, 0, 'circuit highlight at @page CPU');
  eq(result.circuitEditor.cursor.line, 0, 'circuit cursor at @page CPU');
  eq(result.boardEditor.highlight.line, 0, 'board highlight at @page CPU');
  eq(result.boardEditor.cursor.line, 0, 'board cursor at @page CPU');
}

section('syncToPage — switch to Memory');
{
  const { circuitEditor, boardEditor } = makeEditors();
  const result = syncToPage(circuitFile, boardFile, circuitEditor, boardEditor, 'Memory');

  eq(result.circuitEditor.highlight.line, 5, 'circuit highlight at @page Memory');
  eq(result.circuitEditor.cursor.line, 5, 'circuit cursor at Memory');
  eq(result.boardEditor.highlight.line, 6, 'board highlight at @page Memory');
  eq(result.boardEditor.cursor.line, 6, 'board cursor at Memory');
}

section('syncToPage — switch to ALU');
{
  const { circuitEditor, boardEditor } = makeEditors();
  const result = syncToPage(circuitFile, boardFile, circuitEditor, boardEditor, 'ALU');

  eq(result.circuitEditor.highlight.line, 9, 'circuit highlight at @page ALU');
  eq(result.boardEditor.highlight.line, 10, 'board highlight at @page ALU');
}

section('syncToPage — missing page clears highlight');
{
  const { circuitEditor, boardEditor } = makeEditors();
  // First set a highlight
  const withHighlight = syncToPage(circuitFile, boardFile, circuitEditor, boardEditor, 'CPU');
  // Now switch to non-existent page
  const result = syncToPage(circuitFile, boardFile, withHighlight.circuitEditor, withHighlight.boardEditor, 'NonExistent');

  eq(result.circuitEditor.highlight, null, 'circuit highlight cleared for missing page');
  eq(result.boardEditor.highlight, null, 'board highlight cleared for missing page');
}

section('syncToPage — scroll adjusts for off-screen pages');
{
  const { circuitEditor, boardEditor } = makeEditors();
  // ALU is at line 9/10 — with visibleLines=5, should scroll
  const result = syncToPage(circuitFile, boardFile, circuitEditor, boardEditor, 'ALU');

  // Scroll should be adjusted so line 9 is visible
  assert(result.circuitEditor.scroll.line <= 9, 'circuit scrolled to show ALU');
  assert(
    result.circuitEditor.scroll.line + result.circuitEditor.visibleLines > 9,
    'circuit ALU within viewport'
  );
}

// =============================================================================
// syncToDevice
// =============================================================================

section('syncToDevice — U1 (on CPU page)');
{
  const { circuitEditor, boardEditor } = makeEditors();
  const result = syncToDevice(circuitFile, boardFile, circuitEditor, boardEditor, 'U1');

  eq(result.circuitEditor.highlight.line, 1, 'circuit highlights device U1 line');
  eq(result.boardEditor.highlight.line, 2, 'board highlights place U1 line');
  eq(result.page, 'CPU', 'device U1 is on CPU page');
}

section('syncToDevice — U3 (on Memory page)');
{
  const { circuitEditor, boardEditor } = makeEditors();
  const result = syncToDevice(circuitFile, boardFile, circuitEditor, boardEditor, 'U3');

  eq(result.circuitEditor.highlight.line, 6, 'circuit highlights device U3');
  eq(result.boardEditor.highlight.line, 8, 'board highlights place U3');
  eq(result.page, 'Memory', 'device U3 on Memory page');
}

section('syncToDevice — U4 (on ALU page)');
{
  const { circuitEditor, boardEditor } = makeEditors();
  const result = syncToDevice(circuitFile, boardFile, circuitEditor, boardEditor, 'U4');

  eq(result.circuitEditor.highlight.line, 10, 'circuit highlights device U4');
  eq(result.boardEditor.highlight.line, 12, 'board highlights place U4');
  eq(result.page, 'ALU', 'device U4 on ALU page');
}

section('syncToDevice — missing device');
{
  const { circuitEditor, boardEditor } = makeEditors();
  const result = syncToDevice(circuitFile, boardFile, circuitEditor, boardEditor, 'U99');

  eq(result.circuitEditor.highlight, null, 'no highlight for missing device');
  eq(result.boardEditor.highlight, null, 'no board highlight for missing device');
  eq(result.page, null, 'null page for missing device');
}

// =============================================================================
// getCurrentPage
// =============================================================================

section('getCurrentPage — cursor at top');
{
  const editor = createEditor(CIRCUIT_TEXT);
  // cursor at line 0 (within CPU page)
  eq(getCurrentPage(circuitFile, editor), 'CPU', 'cursor in CPU page');
}

section('getCurrentPage — cursor in Memory');
{
  let editor = createEditor(CIRCUIT_TEXT);
  editor = { ...editor, cursor: { line: 6, col: 0 } };
  eq(getCurrentPage(circuitFile, editor), 'Memory', 'cursor in Memory page');
}

section('getCurrentPage — cursor in ALU');
{
  let editor = createEditor(CIRCUIT_TEXT);
  editor = { ...editor, cursor: { line: 10, col: 0 } };
  eq(getCurrentPage(circuitFile, editor), 'ALU', 'cursor in ALU page');
}

section('getCurrentPage — cursor on @page line itself');
{
  let editor = createEditor(CIRCUIT_TEXT);
  editor = { ...editor, cursor: { line: 5, col: 0 } }; // @page Memory line
  eq(getCurrentPage(circuitFile, editor), 'Memory', 'cursor on @page line');
}

// =============================================================================
// getActivePageFromEditor
// =============================================================================

section('getActivePageFromEditor');
{
  let editor = createEditor(CIRCUIT_TEXT);
  editor = { ...editor, cursor: { line: 7, col: 0 } };
  eq(getActivePageFromEditor(circuitFile, editor), 'Memory', 'active page from editor cursor');
}

// =============================================================================
// initSync
// =============================================================================

section('initSync — positions at first page');
{
  const { circuitEditor, boardEditor } = makeEditors();
  const result = initSync(circuitFile, boardFile, circuitEditor, boardEditor);

  eq(result.activePage, 'CPU', 'initial active page is CPU');
  eq(result.circuitEditor.highlight.line, 0, 'circuit at first page');
  eq(result.boardEditor.highlight.line, 0, 'board at first page');
}

section('initSync — no named pages');
{
  const noPageText = `device U1, digital.74HC04;`;
  const noPageFile = parseFile(noPageText, FILE_TYPES.CIRCUIT);
  const noPageBoard = parseFile('place U1 at (50, 30) rotate 0;', FILE_TYPES.BOARD);
  const ce = createEditor(noPageText);
  const be = createEditor('place U1 at (50, 30) rotate 0;');

  const result = initSync(noPageFile, noPageBoard, ce, be);
  eq(result.activePage, '', 'no pages = empty active page');
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
