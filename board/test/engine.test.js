/**
 * Components Board — Engine Module Tests
 * Run: node board/test/engine.test.js
 */

import assert from 'node:assert/strict';
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

console.log('\n━━━ Engine Module Tests ━━━\n');

// --- Basic creation ---

console.log('creation:');

test('creates with default parser and executor', () => {
  const engine = createEngine({ parser: parseCommand, executor: createExecutor() });
  assert.ok(engine);
  assert.equal(typeof engine.run, 'function');
  assert.equal(typeof engine.getState, 'function');
});

test('throws without parser', () => {
  assert.throws(() => createEngine({ executor: createExecutor() }), /parser/i);
});

test('throws without executor', () => {
  assert.throws(() => createEngine({ parser: parseCommand }), /executor/i);
});

// --- Running commands ---

console.log('\nrun commands:');

test('run text command', () => {
  const engine = createEngine({ parser: parseCommand, executor: createExecutor() });
  const r = engine.run('place U1, digital.74HC04 at (50, 30) rotate 0');
  assert.ok(r.success);
  assert.equal(r.parsed.type, 'place');
});

test('run JSON command', () => {
  const engine = createEngine({ parser: parseCommand, executor: createExecutor() });
  const r = engine.run('{"command": "place", "ref": "U1", "part": "digital.74HC04", "x": 50, "y": 30, "rotation": 0}');
  assert.ok(r.success);
  assert.equal(r.parsed.type, 'place');
});

test('text and JSON produce same state', () => {
  const e1 = createEngine({ parser: parseCommand, executor: createExecutor() });
  const e2 = createEngine({ parser: parseCommand, executor: createExecutor() });
  e1.run('place U1, digital.74HC04 at (50, 30) rotate 0');
  e2.run('{"command": "place", "ref": "U1", "part": "digital.74HC04", "x": 50, "y": 30, "rotation": 0}');
  const s1 = e1.getState();
  const s2 = e2.getState();
  assert.deepEqual(s1.component, s2.component);
  assert.deepEqual(s1.board, s2.board);
});

test('invalid command returns error', () => {
  const engine = createEngine({ parser: parseCommand, executor: createExecutor() });
  const r = engine.run('fly away');
  assert.equal(r.success, false);
  assert.ok(r.error);
});

test('failed execution returns error', () => {
  const engine = createEngine({ parser: parseCommand, executor: createExecutor() });
  const r = engine.run('move U99 to (10, 10)');
  assert.equal(r.success, false);
});

// --- Batch ---

console.log('\nbatch:');

test('runBatch executes multiple commands', () => {
  const engine = createEngine({ parser: parseCommand, executor: createExecutor() });
  const results = engine.runBatch([
    'place U1, digital.74HC04 at (50, 30) rotate 0',
    'place U2, digital.74HC161 at (150, 30) rotate 0',
    'connect U1.1Y -> U2.CLK',
  ]);
  assert.equal(results.length, 3);
  assert.ok(results.every(r => r.success));
  assert.equal(engine.getState().component.connections.length, 1);
});

test('runBatch stops on error by default', () => {
  const engine = createEngine({ parser: parseCommand, executor: createExecutor() });
  const results = engine.runBatch([
    'place U1, digital.74HC04 at (50, 30) rotate 0',
    'move U99 to (10, 10)',
    'place U2, digital.74HC161 at (150, 30) rotate 0',
  ]);
  assert.equal(results.length, 2);
});

test('runBatch continues on error with option', () => {
  const engine = createEngine({ parser: parseCommand, executor: createExecutor() });
  const results = engine.runBatch([
    'place U1, digital.74HC04 at (50, 30) rotate 0',
    'move U99 to (10, 10)',
    'place U2, digital.74HC161 at (150, 30) rotate 0',
  ], { continueOnError: true });
  assert.equal(results.length, 3);
});

// --- Log ---

console.log('\nlog:');

test('getLog returns command history', () => {
  const engine = createEngine({ parser: parseCommand, executor: createExecutor() });
  engine.run('place U1, digital.74HC04 at (50, 30) rotate 0');
  engine.run('move U1 to (60, 40)');
  const log = engine.getLog();
  assert.equal(log.length, 2);
  assert.ok(log[0].timestamp);
  assert.equal(log[0].input, 'place U1, digital.74HC04 at (50, 30) rotate 0');
  assert.ok(log[0].result.success);
});

test('clearLog empties the log', () => {
  const engine = createEngine({ parser: parseCommand, executor: createExecutor() });
  engine.run('place U1, digital.74HC04 at (50, 30) rotate 0');
  engine.clearLog();
  assert.equal(engine.getLog().length, 0);
});

// --- Undo/Redo ---

console.log('\nundo/redo:');

test('undo reverses last command', () => {
  const engine = createEngine({ parser: parseCommand, executor: createExecutor() });
  engine.run('place U1, digital.74HC04 at (50, 30) rotate 0');
  assert.ok(engine.getState().component.devices['U1']);
  engine.undo();
  assert.equal(engine.getState().component.devices['U1'], undefined);
});

test('redo re-applies undone command', () => {
  const engine = createEngine({ parser: parseCommand, executor: createExecutor() });
  engine.run('place U1, digital.74HC04 at (50, 30) rotate 0');
  engine.undo();
  engine.redo();
  assert.ok(engine.getState().component.devices['U1']);
});

// --- Pluggable parser ---

console.log('\npluggable parser:');

test('custom parser works', () => {
  const myParser = (text) => {
    if (text === 'nuke') return { type: 'delete', ref: 'U1' };
    return { type: 'error', message: 'unknown', input: text };
  };
  const engine = createEngine({ parser: myParser, executor: createExecutor() });
  engine.run('place U1, digital.74HC04 at (50, 30) rotate 0'); // will fail with custom parser
  // But the custom parser doesn't know 'place', so:
  const r = engine.run('nuke');
  // U1 doesn't exist so delete fails, but parser worked
  assert.equal(r.parsed.type, 'delete');
});

test('setParser hot-swaps parser', () => {
  const engine = createEngine({ parser: parseCommand, executor: createExecutor() });
  engine.run('place U1, digital.74HC04 at (50, 30) rotate 0');
  assert.ok(engine.getState().component.devices['U1']);

  // Swap to a parser that translates 'nuke' to delete
  engine.setParser((text) => {
    if (text === 'nuke U1') return { type: 'delete', ref: 'U1' };
    return parseCommand(text);
  });

  engine.run('nuke U1');
  assert.equal(engine.getState().component.devices['U1'], undefined);
});

// --- Middleware ---

console.log('\nmiddleware:');

test('before middleware can block commands', () => {
  const blocker = {
    name: 'readonly-guard',
    before: (parsed, state) => {
      if (parsed.type === 'delete') return { reason: 'Deletion blocked by readonly mode' };
      return null;
    }
  };
  const engine = createEngine({ parser: parseCommand, executor: createExecutor(), middleware: [blocker] });
  engine.run('place U1, digital.74HC04 at (50, 30) rotate 0');
  const r = engine.run('delete U1');
  assert.equal(r.success, false);
  assert.ok(r.error.includes('readonly'));
  assert.ok(engine.getState().component.devices['U1']); // still exists
});

test('after middleware gets notified', () => {
  let notified = null;
  const logger = {
    name: 'test-logger',
    after: (parsed, result, state) => { notified = { parsed, result }; }
  };
  const engine = createEngine({ parser: parseCommand, executor: createExecutor(), middleware: [logger] });
  engine.run('place U1, digital.74HC04 at (50, 30) rotate 0');
  assert.ok(notified);
  assert.equal(notified.parsed.type, 'place');
  assert.ok(notified.result.success);
});

test('addMiddleware adds at runtime', () => {
  const engine = createEngine({ parser: parseCommand, executor: createExecutor() });
  engine.run('place U1, digital.74HC04 at (50, 30) rotate 0');

  let blocked = false;
  engine.addMiddleware({
    name: 'late-guard',
    before: (parsed) => {
      if (parsed.type === 'delete') { blocked = true; return { reason: 'blocked' }; }
      return null;
    }
  });

  engine.run('delete U1');
  assert.ok(blocked);
  assert.ok(engine.getState().component.devices['U1']);
});

// --- Module info ---

console.log('\nmodule info:');

test('getModules returns parser and executor info', () => {
  const engine = createEngine({ parser: parseCommand, executor: createExecutor() });
  const info = engine.getModules();
  assert.equal(info.parser, 'parseCommand');
  assert.ok(Array.isArray(info.middleware));
});

// --- Summary ---

console.log(`\n━━━ Results: ${passed} passed, ${failed} failed ━━━\n`);
if (failed > 0) process.exit(1);
