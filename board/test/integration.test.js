/**
 * Components Board — Integration Tests (Phase 5)
 * Tasks 5.1–5.3: Presentation mode, Command history, Full pipeline
 * Run: node test/integration.test.js
 */

import assert from 'node:assert/strict';
import { toPresentationMode, createCommandHistory } from '../src/controller/presentation.js';
import { parseFile, FILE_TYPES, getPageOffset, findDeviceLine } from '../src/model/file.js';
import { createEditor } from '../src/view/editor.js';
import { syncToPage } from '../src/controller/sync.js';
import { generatePrintPreview, exportSVG } from '../src/view/export.js';
import { createEngine } from '../src/controller/engine.js';
import { parseCommand } from '../src/controller/parser.js';
import { createExecutor } from '../src/controller/executor.js';

let passed = 0;
let failed = 0;

function test(name, fn) {
  try {
    fn();
    passed++;
    console.log(`  ✓ ${name}`);
  } catch (err) {
    failed++;
    console.log(`  ✗ ${name}`);
    console.log(`    ${err.message}`);
  }
}

// =============================================================================
// 5.2 PRESENTATION MODE
// =============================================================================

console.log('\n━━━ Integration Tests ━━━\n');
console.log('toPresentationMode:');

test('returns presentation mode object', () => {
  const result = toPresentationMode({ devices: [], routes: [], labels: [] });
  assert.equal(result.mode, 'presentation');
});

test('sets white background', () => {
  const result = toPresentationMode({ devices: [], routes: [], labels: [] });
  assert.equal(result.background, '#ffffff');
});

test('handles null input gracefully', () => {
  const result = toPresentationMode(null);
  assert.equal(result.mode, 'presentation');
  assert.deepEqual(result.devices, []);
  assert.deepEqual(result.routes, []);
  assert.deepEqual(result.labels, []);
});

test('handles undefined input gracefully', () => {
  const result = toPresentationMode(undefined);
  assert.equal(result.mode, 'presentation');
});

test('handles non-object input gracefully', () => {
  const result = toPresentationMode(42);
  assert.equal(result.mode, 'presentation');
  assert.deepEqual(result.devices, []);
});

test('preserves device positions', () => {
  const state = { devices: [{ ref: 'U1', part: '74HC04', x: 50, y: 30, width: 20, height: 10, rotation: 0 }], routes: [], labels: [] };
  const result = toPresentationMode(state);
  assert.equal(result.devices[0].x, 50);
  assert.equal(result.devices[0].y, 30);
  assert.equal(result.devices[0].ref, 'U1');
});

test('preserves route paths', () => {
  const state = { devices: [], routes: [{ from: 'U1.1Y', to: 'U2.CLK', color: '#007C3D', points: [{x:10,y:20},{x:30,y:40}] }], labels: [] };
  const result = toPresentationMode(state);
  assert.equal(result.routes[0].points.length, 2);
  assert.equal(result.routes[0].points[0].x, 10);
});

test('preserves label positions', () => {
  const state = { devices: [], routes: [], labels: [{ text: 'VCC', x: 10, y: 90, fontSize: 3 }] };
  const result = toPresentationMode(state);
  assert.equal(result.labels[0].text, 'VCC');
  assert.equal(result.labels[0].x, 10);
});

test('strips grid property', () => {
  const state = { devices: [], routes: [], labels: [], grid: { show: true, spacing: 5 } };
  const result = toPresentationMode(state);
  assert.equal(result.grid, undefined);
});

test('strips tools property', () => {
  const state = { devices: [], routes: [], labels: [], tools: { active: 'select' } };
  const result = toPresentationMode(state);
  assert.equal(result.tools, undefined);
});

test('strips statusBar property', () => {
  const state = { devices: [], routes: [], labels: [], statusBar: { text: 'Ready' } };
  const result = toPresentationMode(state);
  assert.equal(result.statusBar, undefined);
});

test('strips titleBlock property', () => {
  const state = { devices: [], routes: [], labels: [], titleBlock: { project: 'RV8' } };
  const result = toPresentationMode(state);
  assert.equal(result.titleBlock, undefined);
});

test('strips borders property', () => {
  const state = { devices: [], routes: [], labels: [], borders: { show: true } };
  const result = toPresentationMode(state);
  assert.equal(result.borders, undefined);
});

test('strips margins property', () => {
  const state = { devices: [], routes: [], labels: [], margins: { top: 10 } };
  const result = toPresentationMode(state);
  assert.equal(result.margins, undefined);
});

test('strips selection property', () => {
  const state = { devices: [{ ref: 'U1', x: 10, y: 20, selected: true }], routes: [], labels: [], selection: ['U1'] };
  const result = toPresentationMode(state);
  assert.equal(result.selection, undefined);
  // selected flag is also not propagated (only position fields)
  assert.equal(result.devices[0].selected, undefined);
});

test('multiple devices preserved', () => {
  const state = {
    devices: [
      { ref: 'U1', part: '74HC04', x: 50, y: 30 },
      { ref: 'U2', part: '74HC08', x: 100, y: 60 },
      { ref: 'U3', part: '74HC32', x: 150, y: 90 },
    ],
    routes: [], labels: []
  };
  const result = toPresentationMode(state);
  assert.equal(result.devices.length, 3);
  assert.equal(result.devices[2].ref, 'U3');
});

test('handles devices without optional fields', () => {
  const state = { devices: [{ ref: 'U1' }], routes: [], labels: [] };
  const result = toPresentationMode(state);
  assert.equal(result.devices[0].x, 0);
  assert.equal(result.devices[0].y, 0);
  assert.equal(result.devices[0].width, 10);
  assert.equal(result.devices[0].height, 10);
});

test('handles routes without points', () => {
  const state = { devices: [], routes: [{ from: 'A', to: 'B' }], labels: [] };
  const result = toPresentationMode(state);
  assert.deepEqual(result.routes[0].points, []);
});

test('handles labels without fontSize', () => {
  const state = { devices: [], routes: [], labels: [{ text: 'GND', x: 5, y: 5 }] };
  const result = toPresentationMode(state);
  assert.equal(result.labels[0].fontSize, 3);
});

test('result object is frozen', () => {
  const result = toPresentationMode({ devices: [], routes: [], labels: [] });
  assert.throws(() => { result.mode = 'edit'; }, TypeError);
});

test('empty arrays for missing devices/routes/labels', () => {
  const result = toPresentationMode({});
  assert.deepEqual(result.devices, []);
  assert.deepEqual(result.routes, []);
  assert.deepEqual(result.labels, []);
});

test('route color defaults to #007C3D', () => {
  const state = { devices: [], routes: [{ points: [{x:0,y:0}] }], labels: [] };
  const result = toPresentationMode(state);
  assert.equal(result.routes[0].color, '#007C3D');
});

test('label color defaults to #000000', () => {
  const state = { devices: [], routes: [], labels: [{ text: 'X', x: 0, y: 0 }] };
  const result = toPresentationMode(state);
  assert.equal(result.labels[0].color, '#000000');
});

// =============================================================================
// 5.3 COMMAND HISTORY — UNDO/REDO
// =============================================================================

console.log('\ncreateCommandHistory:');

test('creates history with position 0', () => {
  const h = createCommandHistory();
  assert.equal(h.getPosition(), 0);
});

test('empty history: canUndo is false', () => {
  const h = createCommandHistory();
  assert.equal(h.canUndo(), false);
});

test('empty history: canRedo is false', () => {
  const h = createCommandHistory();
  assert.equal(h.canRedo(), false);
});

test('push increments position', () => {
  const h = createCommandHistory();
  h.push({ type: 'place', ref: 'U1' });
  assert.equal(h.getPosition(), 1);
});

test('push multiple commands', () => {
  const h = createCommandHistory();
  h.push({ type: 'place', ref: 'U1' });
  h.push({ type: 'place', ref: 'U2' });
  h.push({ type: 'place', ref: 'U3' });
  assert.equal(h.getPosition(), 3);
});

test('canUndo after push is true', () => {
  const h = createCommandHistory();
  h.push({ type: 'place', ref: 'U1' });
  assert.equal(h.canUndo(), true);
});

test('canRedo after push is false', () => {
  const h = createCommandHistory();
  h.push({ type: 'place', ref: 'U1' });
  assert.equal(h.canRedo(), false);
});

test('undo returns last command', () => {
  const h = createCommandHistory();
  const cmd = { type: 'place', ref: 'U1' };
  h.push(cmd);
  const undone = h.undo();
  assert.deepEqual(undone, cmd);
});

test('undo decrements position', () => {
  const h = createCommandHistory();
  h.push({ type: 'place', ref: 'U1' });
  h.undo();
  assert.equal(h.getPosition(), 0);
});

test('undo at start returns null', () => {
  const h = createCommandHistory();
  assert.equal(h.undo(), null);
});

test('undo at start keeps position at 0', () => {
  const h = createCommandHistory();
  h.undo();
  assert.equal(h.getPosition(), 0);
});

test('canRedo after undo is true', () => {
  const h = createCommandHistory();
  h.push({ type: 'place', ref: 'U1' });
  h.undo();
  assert.equal(h.canRedo(), true);
});

test('redo returns command to replay', () => {
  const h = createCommandHistory();
  const cmd = { type: 'place', ref: 'U1' };
  h.push(cmd);
  h.undo();
  const redone = h.redo();
  assert.deepEqual(redone, cmd);
});

test('redo increments position', () => {
  const h = createCommandHistory();
  h.push({ type: 'place', ref: 'U1' });
  h.undo();
  h.redo();
  assert.equal(h.getPosition(), 1);
});

test('redo at end returns null', () => {
  const h = createCommandHistory();
  h.push({ type: 'place', ref: 'U1' });
  assert.equal(h.redo(), null);
});

test('redo at end keeps position unchanged', () => {
  const h = createCommandHistory();
  h.push({ type: 'place', ref: 'U1' });
  h.redo();
  assert.equal(h.getPosition(), 1);
});

test('push after undo truncates future', () => {
  const h = createCommandHistory();
  h.push({ type: 'place', ref: 'U1' });
  h.push({ type: 'place', ref: 'U2' });
  h.push({ type: 'place', ref: 'U3' });
  h.undo(); // position 2
  h.undo(); // position 1
  h.push({ type: 'move', ref: 'U1' }); // truncates U2, U3
  assert.equal(h.getPosition(), 2);
  assert.equal(h.canRedo(), false);
  const log = h.getLog();
  assert.equal(log.length, 2);
  assert.equal(log[1].type, 'move');
});

test('getLog returns frozen array', () => {
  const h = createCommandHistory();
  h.push({ type: 'place', ref: 'U1' });
  const log = h.getLog();
  assert.throws(() => { log.push('x'); }, TypeError);
});

test('getLog returns copy (not reference)', () => {
  const h = createCommandHistory();
  h.push({ type: 'place', ref: 'U1' });
  const log1 = h.getLog();
  h.push({ type: 'place', ref: 'U2' });
  const log2 = h.getLog();
  assert.equal(log1.length, 1);
  assert.equal(log2.length, 2);
});

test('clear resets everything', () => {
  const h = createCommandHistory();
  h.push({ type: 'place', ref: 'U1' });
  h.push({ type: 'place', ref: 'U2' });
  h.clear();
  assert.equal(h.getPosition(), 0);
  assert.equal(h.canUndo(), false);
  assert.equal(h.canRedo(), false);
  assert.equal(h.getLog().length, 0);
});

test('undo after clear returns null', () => {
  const h = createCommandHistory();
  h.push({ type: 'place', ref: 'U1' });
  h.clear();
  assert.equal(h.undo(), null);
});

test('redo after clear returns null', () => {
  const h = createCommandHistory();
  h.push({ type: 'place', ref: 'U1' });
  h.undo();
  h.clear();
  assert.equal(h.redo(), null);
});

test('multiple undo/redo cycle', () => {
  const h = createCommandHistory();
  h.push({ type: 'A' });
  h.push({ type: 'B' });
  h.push({ type: 'C' });
  assert.equal(h.undo().type, 'C');
  assert.equal(h.undo().type, 'B');
  assert.equal(h.redo().type, 'B');
  assert.equal(h.redo().type, 'C');
  assert.equal(h.redo(), null);
  assert.equal(h.getPosition(), 3);
});

test('undo all then redo all', () => {
  const h = createCommandHistory();
  h.push({ type: 'A' });
  h.push({ type: 'B' });
  h.undo();
  h.undo();
  assert.equal(h.getPosition(), 0);
  assert.equal(h.canUndo(), false);
  h.redo();
  h.redo();
  assert.equal(h.getPosition(), 2);
  assert.equal(h.canRedo(), false);
});

// =============================================================================
// 5.1 FULL PIPELINE INTEGRATION
// =============================================================================

console.log('\nFull Pipeline Integration:');

// --- Sample file content ---
const CIRCUIT_CONTENT = `@page CPU
device U1, digital.74HC04;
device U2, digital.74HC08;
connect U1.1Y -> U2.1A;
@page Memory
device U3, digital.62256;
`;

const BOARD_CONTENT = `@page CPU
paper A4 landscape;
place U1 at (50, 30) rotate 0;
place U2 at (100, 60) rotate 0;
route U1.1Y -> U2.1A via (75, 30) (75, 60);
label "CLK" at (50, 25);
@page Memory
place U3 at (50, 30) rotate 0;
`;

test('parse circuit file extracts pages', () => {
  const file = parseFile(CIRCUIT_CONTENT, FILE_TYPES.CIRCUIT);
  assert.equal(file.pages.length, 2);
  assert.equal(file.pages[0].name, 'CPU');
  assert.equal(file.pages[1].name, 'Memory');
});

test('parse board file extracts placements', () => {
  const file = parseFile(BOARD_CONTENT, FILE_TYPES.BOARD);
  const cpuPage = file.pages[0];
  const placements = cpuPage.lines.filter(l => l.parsed.type === 'place');
  assert.equal(placements.length, 2);
  assert.equal(placements[0].parsed.ref, 'U1');
});

test('create editors from file content', () => {
  const circuitEditor = createEditor(CIRCUIT_CONTENT);
  const boardEditor = createEditor(BOARD_CONTENT);
  assert.ok(circuitEditor.lines.length > 0);
  assert.ok(boardEditor.lines.length > 0);
});

test('sync editors to page', () => {
  const circuitFile = parseFile(CIRCUIT_CONTENT, FILE_TYPES.CIRCUIT);
  const boardFile = parseFile(BOARD_CONTENT, FILE_TYPES.BOARD);
  const circuitEditor = createEditor(CIRCUIT_CONTENT);
  const boardEditor = createEditor(BOARD_CONTENT);
  const synced = syncToPage(circuitFile, boardFile, circuitEditor, boardEditor, 'CPU');
  assert.ok(synced.circuitEditor);
  assert.ok(synced.boardEditor);
});

test('engine runs place command', () => {
  const engine = createEngine({ parser: parseCommand, executor: createExecutor() });
  const r = engine.run('place U1, digital.74HC04 at (50, 30) rotate 0');
  assert.ok(r.success);
});

test('engine state contains placed device', () => {
  const engine = createEngine({ parser: parseCommand, executor: createExecutor() });
  engine.run('place U1, digital.74HC04 at (50, 30) rotate 0');
  const state = engine.getState();
  // devices is an object {ref: {...}}, placements is an object {ref: {...}}
  const hasDevice = Object.keys(state.component.devices).length > 0;
  const hasPlacement = Object.keys(state.board.placements).length > 0;
  assert.ok(hasDevice || hasPlacement);
});

test('generate print preview from board state', () => {
  const boardState = {
    devices: [{ ref: 'U1', x: 50, y: 30, width: 20, height: 10, fill: '#fff', stroke: '#000' }],
    routes: [{ from: 'U1.1Y', to: 'U2.1A', color: '#007C3D', points: [{x:50,y:30},{x:75,y:30},{x:75,y:60}] }],
    labels: [{ text: 'CLK', x: 50, y: 25, fontSize: 3, color: '#000' }],
  };
  const config = {
    paper: { size: 'A4', width_mm: 297, height_mm: 210, margin_mm: { top: 10, bottom: 10, left: 10, right: 10 } },
    grid: { border_tick_mm: 50 },
    title_block: { show: true, project: 'RV8-GR', page_title: 'CPU', author: 'Jo', revision: '1.0' },
    export: { include_title_block: true, include_fold_marks: false },
  };
  const pp = generatePrintPreview(boardState, config);
  assert.equal(pp.paper.width_mm, 297);
  assert.equal(pp.devices.length, 1);
  assert.equal(pp.routes.length, 1);
  assert.equal(pp.labels.length, 1);
});

test('export SVG from print preview', () => {
  const boardState = {
    devices: [{ ref: 'U1', x: 50, y: 30, width: 20, height: 10, fill: '#fff', stroke: '#000' }],
    routes: [],
    labels: [],
  };
  const config = {
    paper: { size: 'A4', width_mm: 297, height_mm: 210, margin_mm: { top: 10, bottom: 10, left: 10, right: 10 } },
    grid: { border_tick_mm: 50 },
    title_block: { show: false },
    export: { include_title_block: false, include_fold_marks: false },
  };
  const pp = generatePrintPreview(boardState, config);
  const svg = exportSVG(pp);
  assert.ok(svg.content.includes('<svg'));
  assert.ok(svg.content.includes('</svg>'));
});

test('SVG contains placed device rect', () => {
  const boardState = {
    devices: [{ ref: 'U1', x: 50, y: 30, width: 20, height: 10, fill: '#ffffff', stroke: '#000000' }],
    routes: [],
    labels: [],
  };
  const config = {
    paper: { size: 'A4', width_mm: 297, height_mm: 210, margin_mm: { top: 10, bottom: 10, left: 10, right: 10 } },
    grid: { border_tick_mm: 50 },
    title_block: { show: false },
    export: { include_title_block: false, include_fold_marks: false },
  };
  const pp = generatePrintPreview(boardState, config);
  const svg = exportSVG(pp);
  assert.ok(svg.content.includes('x="50"'));
  assert.ok(svg.content.includes('y="30"'));
  assert.ok(svg.content.includes('width="20"'));
});

test('full pipeline: file → editor → sync → command → preview → SVG', () => {
  // 1. Parse files
  const circuitFile = parseFile(CIRCUIT_CONTENT, FILE_TYPES.CIRCUIT);
  const boardFile = parseFile(BOARD_CONTENT, FILE_TYPES.BOARD);

  // 2. Create editors
  const circuitEditor = createEditor(CIRCUIT_CONTENT);
  const boardEditor = createEditor(BOARD_CONTENT);

  // 3. Sync to page
  const synced = syncToPage(circuitFile, boardFile, circuitEditor, boardEditor, 'CPU');
  assert.ok(synced.circuitEditor);

  // 4. Engine runs command
  const engine = createEngine({ parser: parseCommand, executor: createExecutor() });
  const r = engine.run('place U1, digital.74HC04 at (50, 30) rotate 0');
  assert.ok(r.success);

  // 5. Build board state for preview
  const boardState = {
    devices: [{ ref: 'U1', x: 50, y: 30, width: 20, height: 10, fill: '#fff', stroke: '#000' }],
    routes: [{ color: '#007C3D', points: [{x:50,y:30},{x:75,y:60}] }],
    labels: [{ text: 'CLK', x: 50, y: 25, fontSize: 3, color: '#000' }],
  };
  const config = {
    paper: { size: 'A4', width_mm: 297, height_mm: 210, margin_mm: { top: 10, bottom: 10, left: 10, right: 10 } },
    grid: { border_tick_mm: 50 },
    title_block: { show: false },
    export: { include_title_block: false },
  };

  // 6. Generate print preview and SVG
  const pp = generatePrintPreview(boardState, config);
  const svg = exportSVG(pp);

  // 7. Verify SVG contains devices
  assert.ok(svg.content.includes('<svg'));
  assert.ok(svg.content.includes('x="50"'));
  assert.ok(svg.content.includes('<path'));
  assert.ok(svg.content.includes('CLK'));
});

test('presentation mode integrates with preview pipeline', () => {
  const fullState = {
    devices: [{ ref: 'U1', part: '74HC04', x: 50, y: 30, width: 20, height: 10 }],
    routes: [{ from: 'U1.1Y', to: 'U2.1A', color: '#007C3D', points: [{x:50,y:30},{x:100,y:60}] }],
    labels: [{ text: 'VCC', x: 10, y: 5, fontSize: 3 }],
    grid: { show: true },
    selection: ['U1'],
    tools: { active: 'select' },
    statusBar: { text: 'Ready' },
  };
  const pres = toPresentationMode(fullState);
  assert.equal(pres.mode, 'presentation');
  assert.equal(pres.devices.length, 1);
  assert.equal(pres.grid, undefined);
  assert.equal(pres.selection, undefined);
});

test('command history integrates with engine commands', () => {
  const history = createCommandHistory();
  const engine = createEngine({ parser: parseCommand, executor: createExecutor() });

  const r1 = engine.run('place U1, digital.74HC04 at (50, 30) rotate 0');
  history.push(r1.parsed);

  const r2 = engine.run('place U2, digital.74HC08 at (100, 60) rotate 90');
  history.push(r2.parsed);

  assert.equal(history.getPosition(), 2);
  const undone = history.undo();
  assert.equal(undone.type, 'place');
  assert.equal(undone.ref, 'U2');
});

test('findDeviceLine works with parsed circuit', () => {
  const file = parseFile(CIRCUIT_CONTENT, FILE_TYPES.CIRCUIT);
  const line = findDeviceLine(file, 'U2');
  assert.ok(line >= 0);
});

test('getPageOffset finds CPU page', () => {
  const file = parseFile(CIRCUIT_CONTENT, FILE_TYPES.CIRCUIT);
  const offset = getPageOffset(file, 'CPU');
  assert.ok(offset >= 0);
});

test('getPageOffset returns -1 for missing page', () => {
  const file = parseFile(CIRCUIT_CONTENT, FILE_TYPES.CIRCUIT);
  const offset = getPageOffset(file, 'Nonexistent');
  assert.equal(offset, -1);
});

// --- Summary ---

console.log(`\n━━━ Results: ${passed} passed, ${failed} failed ━━━\n`);

if (failed > 0) {
  process.exit(1);
}
