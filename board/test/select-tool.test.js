/**
 * Components Board — Select Tool Tests
 * Run: node test/select-tool.test.js
 */

import assert from 'node:assert/strict';
import { createSelectTool } from '../src/controller/select-tool.js';

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

console.log('\n━━━ Select Tool Tests ━━━\n');

// =============================================================================
// CLICK
// =============================================================================

console.log('click:');

test('click on device ref returns select command', () => {
  const tool = createSelectTool();
  const cmd = tool.click({ x: 10, y: 20 }, 'U1');
  assert.deepEqual(cmd, { type: 'select', ref: 'U1' });
});

test('click on empty space returns deselect command', () => {
  const tool = createSelectTool();
  const cmd = tool.click({ x: 5, y: 5 }, null);
  assert.deepEqual(cmd, { type: 'deselect' });
});

test('click preserves full ref string', () => {
  const tool = createSelectTool();
  const cmd = tool.click({ x: 0, y: 0 }, 'R47');
  assert.equal(cmd.ref, 'R47');
});

test('click with empty string ref returns deselect', () => {
  const tool = createSelectTool();
  const cmd = tool.click({ x: 0, y: 0 }, '');
  assert.deepEqual(cmd, { type: 'deselect' });
});

test('click with undefined hitRef returns deselect', () => {
  const tool = createSelectTool();
  const cmd = tool.click({ x: 0, y: 0 }, undefined);
  assert.deepEqual(cmd, { type: 'deselect' });
});

// =============================================================================
// DRAG
// =============================================================================

console.log('\ndrag:');

test('drag returns move command with delta', () => {
  const tool = createSelectTool();
  const cmd = tool.drag({ x: 10, y: 20 }, { x: 15, y: 25 }, 'U1');
  assert.deepEqual(cmd, { type: 'move', ref: 'U1', dx: 5, dy: 5 });
});

test('drag with negative delta', () => {
  const tool = createSelectTool();
  const cmd = tool.drag({ x: 20, y: 30 }, { x: 10, y: 15 }, 'C3');
  assert.deepEqual(cmd, { type: 'move', ref: 'C3', dx: -10, dy: -15 });
});

test('drag with zero delta', () => {
  const tool = createSelectTool();
  const cmd = tool.drag({ x: 5, y: 5 }, { x: 5, y: 5 }, 'U2');
  assert.deepEqual(cmd, { type: 'move', ref: 'U2', dx: 0, dy: 0 });
});

test('drag with no ref returns null', () => {
  const tool = createSelectTool();
  const cmd = tool.drag({ x: 0, y: 0 }, { x: 10, y: 10 }, null);
  assert.equal(cmd, null);
});

test('drag with empty string ref returns null', () => {
  const tool = createSelectTool();
  const cmd = tool.drag({ x: 0, y: 0 }, { x: 10, y: 10 }, '');
  assert.equal(cmd, null);
});

test('drag with fractional mm coordinates', () => {
  const tool = createSelectTool();
  const cmd = tool.drag({ x: 2.54, y: 1.27 }, { x: 5.08, y: 3.81 }, 'U1');
  assert.equal(cmd.type, 'move');
  assert.ok(Math.abs(cmd.dx - 2.54) < 1e-10);
  assert.ok(Math.abs(cmd.dy - 2.54) < 1e-10);
});

// =============================================================================
// KEY
// =============================================================================

console.log('\nkey:');

test('R with selected ref returns rotate command', () => {
  const tool = createSelectTool();
  const cmd = tool.key('R', 'U1');
  assert.deepEqual(cmd, { type: 'rotate', ref: 'U1', angle: 90 });
});

test('r (lowercase) with selected ref returns rotate command', () => {
  const tool = createSelectTool();
  const cmd = tool.key('r', 'U1');
  assert.deepEqual(cmd, { type: 'rotate', ref: 'U1', angle: 90 });
});

test('R with no selection returns null', () => {
  const tool = createSelectTool();
  const cmd = tool.key('R', null);
  assert.equal(cmd, null);
});

test('Delete with selected ref returns delete command', () => {
  const tool = createSelectTool();
  const cmd = tool.key('Delete', 'C2');
  assert.deepEqual(cmd, { type: 'delete', ref: 'C2' });
});

test('Delete with no selection returns null', () => {
  const tool = createSelectTool();
  const cmd = tool.key('Delete', null);
  assert.equal(cmd, null);
});

test('Escape returns deselect regardless of selection', () => {
  const tool = createSelectTool();
  const cmd = tool.key('Escape', 'U1');
  assert.deepEqual(cmd, { type: 'deselect' });
});

test('Escape with no selection still returns deselect', () => {
  const tool = createSelectTool();
  const cmd = tool.key('Escape', null);
  assert.deepEqual(cmd, { type: 'deselect' });
});

test('unknown key returns null', () => {
  const tool = createSelectTool();
  const cmd = tool.key('x', 'U1');
  assert.equal(cmd, null);
});

test('unknown key with no selection returns null', () => {
  const tool = createSelectTool();
  const cmd = tool.key('z', null);
  assert.equal(cmd, null);
});

// =============================================================================
// BOX SELECT
// =============================================================================

console.log('\nbox select:');

test('box select returns normalized coordinates', () => {
  const tool = createSelectTool();
  const cmd = tool.boxSelect({ x: 10, y: 20 }, { x: 30, y: 40 });
  assert.deepEqual(cmd, { type: 'select', box: { x1: 10, y1: 20, x2: 30, y2: 40 } });
});

test('box select normalizes when start > end', () => {
  const tool = createSelectTool();
  const cmd = tool.boxSelect({ x: 30, y: 40 }, { x: 10, y: 20 });
  assert.deepEqual(cmd, { type: 'select', box: { x1: 10, y1: 20, x2: 30, y2: 40 } });
});

test('box select normalizes mixed corners', () => {
  const tool = createSelectTool();
  const cmd = tool.boxSelect({ x: 30, y: 10 }, { x: 5, y: 50 });
  assert.deepEqual(cmd, { type: 'select', box: { x1: 5, y1: 10, x2: 30, y2: 50 } });
});

test('box select with zero-area (single point)', () => {
  const tool = createSelectTool();
  const cmd = tool.boxSelect({ x: 15, y: 15 }, { x: 15, y: 15 });
  assert.deepEqual(cmd, { type: 'select', box: { x1: 15, y1: 15, x2: 15, y2: 15 } });
});

test('box select with fractional coordinates', () => {
  const tool = createSelectTool();
  const cmd = tool.boxSelect({ x: 2.54, y: 1.27 }, { x: 7.62, y: 5.08 });
  assert.deepEqual(cmd, { type: 'select', box: { x1: 2.54, y1: 1.27, x2: 7.62, y2: 5.08 } });
});

// =============================================================================
// EDGE CASES
// =============================================================================

console.log('\nedge cases:');

test('tool methods are independent (no shared state)', () => {
  const tool = createSelectTool();
  tool.click({ x: 0, y: 0 }, 'U1');
  const cmd = tool.click({ x: 5, y: 5 }, null);
  assert.deepEqual(cmd, { type: 'deselect' });
});

test('multiple tool instances are independent', () => {
  const tool1 = createSelectTool();
  const tool2 = createSelectTool();
  const cmd1 = tool1.click({ x: 0, y: 0 }, 'U1');
  const cmd2 = tool2.click({ x: 0, y: 0 }, null);
  assert.deepEqual(cmd1, { type: 'select', ref: 'U1' });
  assert.deepEqual(cmd2, { type: 'deselect' });
});

test('drag large distances', () => {
  const tool = createSelectTool();
  const cmd = tool.drag({ x: 0, y: 0 }, { x: 1000, y: 500 }, 'U1');
  assert.equal(cmd.dx, 1000);
  assert.equal(cmd.dy, 500);
});

test('rotate angle is always 90', () => {
  const tool = createSelectTool();
  const cmd = tool.key('R', 'U1');
  assert.equal(cmd.angle, 90);
});

test('all commands have a type property', () => {
  const tool = createSelectTool();
  const cmds = [
    tool.click({ x: 0, y: 0 }, 'U1'),
    tool.click({ x: 0, y: 0 }, null),
    tool.drag({ x: 0, y: 0 }, { x: 1, y: 1 }, 'U1'),
    tool.key('R', 'U1'),
    tool.key('Delete', 'U1'),
    tool.key('Escape', null),
    tool.boxSelect({ x: 0, y: 0 }, { x: 10, y: 10 }),
  ];
  for (const cmd of cmds) {
    assert.ok(cmd.type, 'command must have type');
  }
});

// =============================================================================
// SUMMARY
// =============================================================================

console.log(`\n━━━ Results: ${passed} passed, ${failed} failed ━━━\n`);
if (failed > 0) process.exit(1);
