/**
 * Components Board — Command Viewport Tests
 * Run: node board/test/command-viewport.test.js
 */

import assert from 'node:assert/strict';
import { createCommandViewport } from '../src/view/command-viewport.js';
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

/** Helper: create a fresh viewport with a real engine. */
function makeViewport() {
  const engine = createEngine({ parser: parseCommand, executor: createExecutor() });
  return createCommandViewport(engine);
}

console.log('\n━━━ Command Viewport Tests ━━━\n');

// --- Creation ---

console.log('creation:');

test('creates with a valid engine', () => {
  const vp = makeViewport();
  assert.ok(vp);
  assert.equal(typeof vp.submit, 'function');
  assert.equal(typeof vp.getLog, 'function');
  assert.equal(typeof vp.getHistory, 'function');
  assert.equal(typeof vp.historyUp, 'function');
  assert.equal(typeof vp.historyDown, 'function');
  assert.equal(typeof vp.clear, 'function');
  assert.equal(typeof vp.getSuggestions, 'function');
});

test('throws without engine', () => {
  assert.throws(() => createCommandViewport(null), /engine/i);
});

test('throws with engine missing run()', () => {
  assert.throws(() => createCommandViewport({ notRun: true }), /engine/i);
});

// --- Submit ---

console.log('\nsubmit:');

test('submit valid text command → success in log', () => {
  const vp = makeViewport();
  const result = vp.submit('place U1, digital.74HC04 at (50, 30) rotate 0');
  assert.equal(result.success, true);
  assert.equal(result.type, 'place');
  assert.ok(result.message.length > 0);
});

test('submit valid JSON command → success in log', () => {
  const vp = makeViewport();
  const result = vp.submit('{"command": "place", "ref": "U2", "part": "digital.74HC08", "x": 10, "y": 20, "rotation": 90}');
  assert.equal(result.success, true);
  assert.equal(result.type, 'place');
});

test('submit invalid command → error in log', () => {
  const vp = makeViewport();
  const result = vp.submit('nonsense blah blah');
  assert.equal(result.success, false);
  assert.equal(result.type, 'error');
  assert.ok(result.message.length > 0);
});

test('submit empty string → error in log', () => {
  const vp = makeViewport();
  const result = vp.submit('');
  assert.equal(result.success, false);
  assert.equal(result.type, 'error');
  assert.equal(result.message, 'Empty command');
});

test('submit returns the result object', () => {
  const vp = makeViewport();
  const result = vp.submit('place U1, digital.74HC04 at (0, 0) rotate 0');
  assert.ok(result);
  assert.ok('timestamp' in result);
  assert.ok('input' in result);
  assert.ok('success' in result);
  assert.ok('message' in result);
  assert.ok('type' in result);
});

test('submit whitespace-only → error', () => {
  const vp = makeViewport();
  const result = vp.submit('   ');
  assert.equal(result.success, false);
  assert.equal(result.type, 'error');
});

// --- Log ---

console.log('\nlog:');

test('getLog returns entries in order', () => {
  const vp = makeViewport();
  vp.submit('place U1, digital.74HC04 at (10, 20) rotate 0');
  vp.submit('place U2, digital.74HC08 at (30, 40) rotate 90');
  const log = vp.getLog();
  assert.equal(log.length, 2);
  assert.ok(log[0].input.includes('U1'));
  assert.ok(log[1].input.includes('U2'));
});

test('log entries have correct type field', () => {
  const vp = makeViewport();
  vp.submit('place U1, digital.74HC04 at (10, 20) rotate 0');
  vp.submit('select U1');
  vp.submit('deselect');
  const log = vp.getLog();
  assert.equal(log[0].type, 'place');
  assert.equal(log[1].type, 'select');
  assert.equal(log[2].type, 'deselect');
});

test('log entries have timestamps', () => {
  const vp = makeViewport();
  const before = Date.now();
  vp.submit('place U1, digital.74HC04 at (0, 0) rotate 0');
  const after = Date.now();
  const log = vp.getLog();
  assert.ok(log[0].timestamp >= before);
  assert.ok(log[0].timestamp <= after);
});

test('clear empties the log', () => {
  const vp = makeViewport();
  vp.submit('place U1, digital.74HC04 at (0, 0) rotate 0');
  vp.submit('select U1');
  assert.equal(vp.getLog().length, 2);
  vp.clear();
  assert.equal(vp.getLog().length, 0);
});

test('multiple commands in sequence', () => {
  const vp = makeViewport();
  vp.submit('place U1, digital.74HC04 at (10, 20) rotate 0');
  vp.submit('place U2, digital.74HC08 at (30, 40) rotate 90');
  vp.submit('connect U1.1Y -> U2.1A');
  const log = vp.getLog();
  assert.equal(log.length, 3);
  assert.equal(log[0].success, true);
  assert.equal(log[1].success, true);
  assert.equal(log[2].success, true);
});

// --- Undo/Redo ---

console.log('\nundo/redo:');

test('undo via submit("undo")', () => {
  const vp = makeViewport();
  vp.submit('place U1, digital.74HC04 at (10, 20) rotate 0');
  const result = vp.submit('undo');
  assert.equal(result.success, true);
  assert.equal(result.type, 'undo');
  assert.ok(result.message.toLowerCase().includes('undo'));
});

test('redo via submit("redo")', () => {
  const vp = makeViewport();
  vp.submit('place U1, digital.74HC04 at (10, 20) rotate 0');
  vp.submit('undo');
  const result = vp.submit('redo');
  assert.equal(result.success, true);
  assert.equal(result.type, 'redo');
  assert.ok(result.message.toLowerCase().includes('redo'));
});

test('undo with nothing to undo → failure', () => {
  const vp = makeViewport();
  const result = vp.submit('undo');
  assert.equal(result.success, false);
  assert.equal(result.type, 'undo');
});

// --- History ---

console.log('\nhistory:');

test('getHistory returns past inputs', () => {
  const vp = makeViewport();
  vp.submit('place U1, digital.74HC04 at (0, 0) rotate 0');
  vp.submit('select U1');
  const hist = vp.getHistory();
  assert.equal(hist.length, 2);
  assert.ok(hist[0].includes('place'));
  assert.ok(hist[1].includes('select'));
});

test('historyUp/historyDown navigates correctly', () => {
  const vp = makeViewport();
  vp.submit('place U1, digital.74HC04 at (0, 0) rotate 0');
  vp.submit('select U1');
  vp.submit('deselect');

  // Navigate up from the end
  const last = vp.historyUp();
  assert.equal(last, 'deselect');
  const mid = vp.historyUp();
  assert.equal(mid, 'select U1');
  const first = vp.historyUp();
  assert.ok(first.includes('place'));
});

test('historyUp at beginning returns null', () => {
  const vp = makeViewport();
  vp.submit('place U1, digital.74HC04 at (0, 0) rotate 0');
  vp.submit('select U1');

  // Navigate to beginning
  vp.historyUp(); // select U1
  vp.historyUp(); // place U1...
  const result = vp.historyUp(); // already at beginning
  assert.equal(result, null);
});

test('historyDown at end returns null', () => {
  const vp = makeViewport();
  vp.submit('place U1, digital.74HC04 at (0, 0) rotate 0');
  vp.submit('select U1');

  // Navigate up once then down past end
  vp.historyUp(); // select U1
  vp.historyDown(); // null (back to end)
  const result = vp.historyDown(); // still null
  assert.equal(result, null);
});

test('historyDown without navigating returns null', () => {
  const vp = makeViewport();
  vp.submit('place U1, digital.74HC04 at (0, 0) rotate 0');
  const result = vp.historyDown();
  assert.equal(result, null);
});

test('historyUp on empty history returns null', () => {
  const vp = makeViewport();
  const result = vp.historyUp();
  assert.equal(result, null);
});

test('history resets cursor on new submit', () => {
  const vp = makeViewport();
  vp.submit('place U1, digital.74HC04 at (0, 0) rotate 0');
  vp.submit('select U1');

  // Navigate up
  vp.historyUp(); // select U1
  vp.historyUp(); // place U1...

  // Submit new command — cursor resets
  vp.submit('deselect');

  // historyUp should now start from the end (deselect)
  const result = vp.historyUp();
  assert.equal(result, 'deselect');
});

test('history includes failed commands', () => {
  const vp = makeViewport();
  vp.submit('nonsense');
  const hist = vp.getHistory();
  assert.equal(hist.length, 1);
  assert.equal(hist[0], 'nonsense');
});

// --- Suggestions ---

console.log('\nsuggestions:');

test('getSuggestions("pl") returns ["place"]', () => {
  const vp = makeViewport();
  const s = vp.getSuggestions('pl');
  assert.deepEqual(s, ['place']);
});

test('getSuggestions("con") returns ["connect"]', () => {
  const vp = makeViewport();
  const s = vp.getSuggestions('con');
  assert.deepEqual(s, ['connect']);
});

test('getSuggestions("") returns all commands', () => {
  const vp = makeViewport();
  const s = vp.getSuggestions('');
  assert.equal(s.length, 19);
  assert.ok(s.includes('place'));
  assert.ok(s.includes('undo'));
  assert.ok(s.includes('set-config'));
});

test('getSuggestions for unknown returns empty', () => {
  const vp = makeViewport();
  const s = vp.getSuggestions('xyz');
  assert.deepEqual(s, []);
});

test('getSuggestions("de") returns delete and deselect and delete-page', () => {
  const vp = makeViewport();
  const s = vp.getSuggestions('de');
  assert.ok(s.includes('delete'));
  assert.ok(s.includes('deselect'));
  assert.ok(s.includes('delete-page'));
  assert.equal(s.length, 3);
});

test('getSuggestions is case-insensitive', () => {
  const vp = makeViewport();
  const s = vp.getSuggestions('PL');
  assert.deepEqual(s, ['place']);
});

test('getSuggestions with whitespace is trimmed', () => {
  const vp = makeViewport();
  const s = vp.getSuggestions('  ro  ');
  assert.deepEqual(s, ['rotate', 'route']);
});

// --- Summary ---

console.log(`\n━━━ Results: ${passed} passed, ${failed} failed ━━━\n`);
process.exit(failed > 0 ? 1 : 0);
