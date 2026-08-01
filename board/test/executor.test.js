/**
 * Components Board — Executor Unit Tests
 * Task 1.3: Engine executor tests
 *
 * Run with: node board/test/executor.test.js
 */

import { createExecutor } from '../src/controller/executor.js';
import { createComponentModel } from '../src/model/component.js';
import { createBoardModel } from '../src/model/board.js';
import { createConfig } from '../src/model/config.js';

let passed = 0;
let failed = 0;

function assert(condition, message) {
  if (condition) {
    passed++;
    console.log(`  ✓ ${message}`);
  } else {
    failed++;
    console.log(`  ✗ ${message}`);
  }
}

function assertEqual(actual, expected, message) {
  const a = JSON.stringify(actual);
  const e = JSON.stringify(expected);
  if (a === e) {
    passed++;
    console.log(`  ✓ ${message}`);
  } else {
    failed++;
    console.log(`  ✗ ${message}`);
    console.log(`    expected: ${e}`);
    console.log(`    actual:   ${a}`);
  }
}

function freshExecutor() {
  return createExecutor(createComponentModel(), createBoardModel(), createConfig());
}

// Place a device helper
function placeU1(exec) {
  return exec.execute({ type: 'place', ref: 'U1', part: 'digital.74HC04', x: 50, y: 30, rotate: 0 });
}

function placeU2(exec) {
  return exec.execute({ type: 'place', ref: 'U2', part: 'digital.74HC08', x: 100, y: 30, rotate: 0 });
}

// ============================
console.log('\n=== PLACE ===');
// ============================

{
  const exec = freshExecutor();
  const result = placeU1(exec);
  assert(result.success === true, 'place: returns success');
}

{
  const exec = freshExecutor();
  placeU1(exec);
  const state = exec.getState();
  assertEqual(state.component.devices.U1.part, 'digital.74HC04', 'place: device added to component model');
}

{
  const exec = freshExecutor();
  placeU1(exec);
  const state = exec.getState();
  assertEqual(state.board.placements.U1.x, 50, 'place: placement x correct');
  assertEqual(state.board.placements.U1.y, 30, 'place: placement y correct');
  assertEqual(state.board.placements.U1.rotation, 0, 'place: placement rotation correct');
}

{
  const exec = freshExecutor();
  placeU1(exec);
  const result = placeU1(exec);
  assert(result.success === false, 'place: rejects duplicate ref');
  assert(result.error.includes('already exists'), 'place: error message mentions already exists');
}

// ============================
console.log('\n=== MOVE ===');
// ============================

{
  const exec = freshExecutor();
  placeU1(exec);
  const result = exec.execute({ type: 'move', ref: 'U1', x: 75, y: 40 });
  assert(result.success === true, 'move: returns success');
  const state = exec.getState();
  assertEqual(state.board.placements.U1.x, 75, 'move: x updated');
  assertEqual(state.board.placements.U1.y, 40, 'move: y updated');
}

{
  const exec = freshExecutor();
  const result = exec.execute({ type: 'move', ref: 'U99', x: 10, y: 10 });
  assert(result.success === false, 'move: rejects unknown ref');
  assert(result.error.includes('not found'), 'move: error mentions not found');
}

// ============================
console.log('\n=== ROTATE ===');
// ============================

{
  const exec = freshExecutor();
  placeU1(exec);
  const result = exec.execute({ type: 'rotate', ref: 'U1', angle: 90 });
  assert(result.success === true, 'rotate: returns success');
  const state = exec.getState();
  assertEqual(state.board.placements.U1.rotation, 90, 'rotate: rotation updated to 90');
}

{
  const exec = freshExecutor();
  placeU1(exec);
  const result = exec.execute({ type: 'rotate', ref: 'U1', angle: 45 });
  assert(result.success === false, 'rotate: rejects invalid angle 45');
}

{
  const exec = freshExecutor();
  const result = exec.execute({ type: 'rotate', ref: 'U99', angle: 90 });
  assert(result.success === false, 'rotate: rejects unknown ref');
}

// ============================
console.log('\n=== DELETE ===');
// ============================

{
  const exec = freshExecutor();
  placeU1(exec);
  placeU2(exec);
  exec.execute({ type: 'connect', from: 'U1.1Y', to: 'U2.1A', via: [] });
  exec.execute({ type: 'route', from: 'U1.1Y', to: 'U2.1A', via: [{ x: 75, y: 30 }] });

  const result = exec.execute({ type: 'delete', ref: 'U1' });
  assert(result.success === true, 'delete: returns success');

  const state = exec.getState();
  assert(state.component.devices.U1 === undefined, 'delete: device removed');
  assert(state.board.placements.U1 === undefined, 'delete: placement removed');
  assertEqual(state.component.connections.length, 0, 'delete: connections removed');
  assertEqual(state.board.routes.length, 0, 'delete: routes removed');
}

{
  const exec = freshExecutor();
  const result = exec.execute({ type: 'delete', ref: 'U99' });
  assert(result.success === false, 'delete: rejects unknown ref');
}

// ============================
console.log('\n=== CONNECT ===');
// ============================

{
  const exec = freshExecutor();
  placeU1(exec);
  placeU2(exec);
  const result = exec.execute({ type: 'connect', from: 'U1.1Y', to: 'U2.1A', via: [] });
  assert(result.success === true, 'connect: returns success');
  const state = exec.getState();
  assertEqual(state.component.connections.length, 1, 'connect: connection added');
  assertEqual(state.component.connections[0].from, 'U1.1Y', 'connect: from pin correct');
  assertEqual(state.component.connections[0].to, 'U2.1A', 'connect: to pin correct');
}

{
  const exec = freshExecutor();
  placeU1(exec);
  placeU2(exec);
  const result = exec.execute({ type: 'connect', from: 'U1.1Y', to: 'U2.1A', via: [{ x: 85, y: 30 }] });
  assert(result.success === true, 'connect: with via points succeeds');
  const state = exec.getState();
  assertEqual(state.board.routes.length, 1, 'connect: route auto-created from via');
}

{
  const exec = freshExecutor();
  placeU1(exec);
  const result = exec.execute({ type: 'connect', from: 'U1.1Y', to: 'U99.1A', via: [] });
  assert(result.success === false, 'connect: rejects if to-device missing');
}

{
  const exec = freshExecutor();
  const result = exec.execute({ type: 'connect', from: 'U99.1Y', to: 'U1.1A', via: [] });
  assert(result.success === false, 'connect: rejects if from-device missing');
}

// ============================
console.log('\n=== DISCONNECT ===');
// ============================

{
  const exec = freshExecutor();
  placeU1(exec);
  placeU2(exec);
  exec.execute({ type: 'connect', from: 'U1.1Y', to: 'U2.1A', via: [{ x: 85, y: 30 }] });

  const result = exec.execute({ type: 'disconnect', from: 'U1.1Y', to: 'U2.1A' });
  assert(result.success === true, 'disconnect: returns success');
  const state = exec.getState();
  assertEqual(state.component.connections.length, 0, 'disconnect: connection removed');
  assertEqual(state.board.routes.length, 0, 'disconnect: route also removed');
}

{
  const exec = freshExecutor();
  const result = exec.execute({ type: 'disconnect', from: 'U1.1Y', to: 'U2.1A' });
  assert(result.success === false, 'disconnect: rejects if connection not found');
}

// ============================
console.log('\n=== ROUTE ===');
// ============================

{
  const exec = freshExecutor();
  placeU1(exec);
  placeU2(exec);
  exec.execute({ type: 'connect', from: 'U1.1Y', to: 'U2.1A', via: [] });

  const result = exec.execute({ type: 'route', from: 'U1.1Y', to: 'U2.1A', via: [{ x: 85, y: 30 }, { x: 85, y: 60 }] });
  assert(result.success === true, 'route: returns success');
  const state = exec.getState();
  assertEqual(state.board.routes.length, 1, 'route: route added');
  assertEqual(state.board.routes[0].via.length, 2, 'route: 2 waypoints stored');
}

{
  const exec = freshExecutor();
  const result = exec.execute({ type: 'route', from: 'U1.1Y', to: 'U2.1A', via: [{ x: 50, y: 50 }] });
  assert(result.success === false, 'route: rejects if connection does not exist');
}

// ============================
console.log('\n=== LABEL ===');
// ============================

{
  const exec = freshExecutor();
  const result = exec.execute({ type: 'label', text: 'Clock', x: 100, y: 50 });
  assert(result.success === true, 'label: returns success');
  const state = exec.getState();
  assertEqual(state.board.labels.length, 1, 'label: label added');
  assertEqual(state.board.labels[0].text, 'Clock', 'label: text correct');
  assert(state.board.labels[0].id.startsWith('label_'), 'label: auto-id generated');
}

// ============================
console.log('\n=== SELECT / DESELECT ===');
// ============================

{
  const exec = freshExecutor();
  placeU1(exec);
  const result = exec.execute({ type: 'select', ref: 'U1' });
  assert(result.success === true, 'select: returns success');
  assertEqual(exec.getState().selection, 'U1', 'select: selection updated');
}

{
  const exec = freshExecutor();
  const result = exec.execute({ type: 'select', ref: 'U99' });
  assert(result.success === false, 'select: rejects unknown ref');
}

{
  const exec = freshExecutor();
  placeU1(exec);
  exec.execute({ type: 'select', ref: 'U1' });
  const result = exec.execute({ type: 'deselect' });
  assert(result.success === true, 'deselect: returns success');
  assertEqual(exec.getState().selection, null, 'deselect: selection cleared');
}

// ============================
console.log('\n=== ZOOM / PAN ===');
// ============================

{
  const exec = freshExecutor();
  const result = exec.execute({ type: 'zoom', mode: 'percent', percent: 150 });
  assert(result.success === true, 'zoom percent: returns success');
  assertEqual(exec.getState().viewport.zoom, 150, 'zoom percent: viewport updated');
}

{
  const exec = freshExecutor();
  const result = exec.execute({ type: 'zoom', mode: 'fit' });
  assert(result.success === true, 'zoom fit: returns success');
  assertEqual(exec.getState().viewport.zoom, 'fit', 'zoom fit: viewport set to fit');
}

{
  const exec = freshExecutor();
  const result = exec.execute({ type: 'pan', dx: 10, dy: -20 });
  assert(result.success === true, 'pan: returns success');
  assertEqual(exec.getState().viewport.panX, 10, 'pan: panX updated');
  assertEqual(exec.getState().viewport.panY, -20, 'pan: panY updated');
}

{
  const exec = freshExecutor();
  exec.execute({ type: 'pan', dx: 5, dy: 5 });
  exec.execute({ type: 'pan', dx: 3, dy: -2 });
  const state = exec.getState();
  assertEqual(state.viewport.panX, 8, 'pan: cumulative panX');
  assertEqual(state.viewport.panY, 3, 'pan: cumulative panY');
}

// ============================
console.log('\n=== UNDO / REDO ===');
// ============================

{
  const exec = freshExecutor();
  placeU1(exec);
  const undoResult = exec.undo();
  assert(undoResult.success === true, 'undo: returns success');
  const state = exec.getState();
  assert(state.component.devices.U1 === undefined, 'undo: place reverted');
}

{
  const exec = freshExecutor();
  placeU1(exec);
  exec.undo();
  const redoResult = exec.redo();
  assert(redoResult.success === true, 'redo: returns success');
  const state = exec.getState();
  assertEqual(state.component.devices.U1.part, 'digital.74HC04', 'redo: place re-applied');
}

{
  const exec = freshExecutor();
  const result = exec.undo();
  assert(result.success === false, 'undo: fails when nothing to undo');
}

{
  const exec = freshExecutor();
  const result = exec.redo();
  assert(result.success === false, 'redo: fails when nothing to redo');
}

{
  const exec = freshExecutor();
  placeU1(exec);
  exec.undo();
  // New command after undo clears redo stack
  placeU2(exec);
  const result = exec.redo();
  assert(result.success === false, 'redo: cleared after new command');
}

// ============================
console.log('\n=== UNDO/REDO via execute() ===');
// ============================

{
  const exec = freshExecutor();
  placeU1(exec);
  const result = exec.execute({ type: 'undo' });
  assert(result.success === true, 'execute(undo): works through execute()');
  assert(exec.getState().component.devices.U1 === undefined, 'execute(undo): reverted');
}

{
  const exec = freshExecutor();
  placeU1(exec);
  exec.execute({ type: 'undo' });
  const result = exec.execute({ type: 'redo' });
  assert(result.success === true, 'execute(redo): works through execute()');
  assertEqual(exec.getState().component.devices.U1.part, 'digital.74HC04', 'execute(redo): re-applied');
}

// ============================
console.log('\n=== PAGE MANAGEMENT ===');
// ============================

{
  const exec = freshExecutor();
  const result = exec.execute({ type: 'new-page', name: 'Memory', paper: 'A3', orientation: 'landscape' });
  assert(result.success === true, 'new-page: returns success');
  const state = exec.getState();
  assert(state.pages.list.includes('Memory'), 'new-page: page added to list');
  assertEqual(state.pages.active, 'Memory', 'new-page: switches to new page');
}

{
  const exec = freshExecutor();
  exec.execute({ type: 'new-page', name: 'Memory', paper: 'A3', orientation: 'landscape' });
  const result = exec.execute({ type: 'new-page', name: 'Memory', paper: 'A4', orientation: 'portrait' });
  assert(result.success === false, 'new-page: rejects duplicate name');
}

{
  const exec = freshExecutor();
  exec.execute({ type: 'new-page', name: 'Memory', paper: 'A3', orientation: 'landscape' });
  const result = exec.execute({ type: 'switch-page', name: 'Page 1' });
  assert(result.success === true, 'switch-page: returns success');
  assertEqual(exec.getState().pages.active, 'Page 1', 'switch-page: active page changed');
}

{
  const exec = freshExecutor();
  const result = exec.execute({ type: 'switch-page', name: 'NonExistent' });
  assert(result.success === false, 'switch-page: rejects unknown page');
}

{
  const exec = freshExecutor();
  const result = exec.execute({ type: 'rename-page', oldName: 'Page 1', newName: 'CPU' });
  assert(result.success === true, 'rename-page: returns success');
  const state = exec.getState();
  assert(!state.pages.list.includes('Page 1'), 'rename-page: old name removed');
  assert(state.pages.list.includes('CPU'), 'rename-page: new name present');
  assertEqual(state.pages.active, 'CPU', 'rename-page: active page renamed');
}

{
  const exec = freshExecutor();
  exec.execute({ type: 'new-page', name: 'Memory', paper: 'A3', orientation: 'landscape' });
  const result = exec.execute({ type: 'delete-page', name: 'Memory' });
  assert(result.success === true, 'delete-page: returns success');
  assert(!exec.getState().pages.list.includes('Memory'), 'delete-page: page removed');
}

{
  const exec = freshExecutor();
  const result = exec.execute({ type: 'delete-page', name: 'Page 1' });
  assert(result.success === false, 'delete-page: cannot delete last page');
}

// ============================
console.log('\n=== SET-CONFIG ===');
// ============================

{
  const exec = freshExecutor();
  const result = exec.execute({ type: 'set-config', path: 'grid.major_mm', value: 5 });
  assert(result.success === true, 'set-config: returns success');
  assertEqual(exec.getState().config.grid.major_mm, 5, 'set-config: value updated');
}

{
  const exec = freshExecutor();
  exec.execute({ type: 'set-config', path: 'title_block.project', value: 'RV8' });
  assertEqual(exec.getState().config.title_block.project, 'RV8', 'set-config: string value');
}

// ============================
console.log('\n=== ERROR COMMAND ===');
// ============================

{
  const exec = freshExecutor();
  const result = exec.execute({ type: 'error', message: 'parse failed' });
  assert(result.success === false, 'error command: returns failure');
  assert(result.error.includes('parse failed'), 'error command: passes message through');
}

{
  const exec = freshExecutor();
  const result = exec.execute({ type: 'unknown-type' });
  assert(result.success === false, 'unknown type: returns failure');
}

{
  const exec = freshExecutor();
  const result = exec.execute(null);
  assert(result.success === false, 'null command: returns failure');
}

// ============================
console.log('\n=== GETSTATE ===');
// ============================

{
  const exec = freshExecutor();
  const state = exec.getState();
  assert(state.component !== undefined, 'getState: has component');
  assert(state.board !== undefined, 'getState: has board');
  assert(state.config !== undefined, 'getState: has config');
  assertEqual(state.selection, null, 'getState: selection is null initially');
  assertEqual(state.viewport.zoom, 100, 'getState: viewport zoom starts at 100');
  assertEqual(state.history.undoCount, 0, 'getState: undoCount starts at 0');
  assertEqual(state.history.redoCount, 0, 'getState: redoCount starts at 0');
  assert(Array.isArray(state.pages.list), 'getState: pages.list is array');
  assertEqual(state.pages.active, 'Page 1', 'getState: active page is Page 1');
}

// ============================
console.log('\n=== DELETE CLEARS SELECTION ===');
// ============================

{
  const exec = freshExecutor();
  placeU1(exec);
  exec.execute({ type: 'select', ref: 'U1' });
  exec.execute({ type: 'delete', ref: 'U1' });
  assertEqual(exec.getState().selection, null, 'delete: clears selection if deleted device was selected');
}

// ============================
// Summary
// ============================

console.log(`\n${'='.repeat(40)}`);
console.log(`Results: ${passed} passed, ${failed} failed, ${passed + failed} total`);
console.log(`${'='.repeat(40)}\n`);

if (failed > 0) {
  process.exit(1);
}
