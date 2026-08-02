/**
 * Components Board — Connect Tool Tests
 * Run: node test/connect-tool.test.js
 */

import assert from 'node:assert/strict';
import { createConnectTool } from '../src/controller/connect-tool.js';

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

console.log('\n━━━ Connect Tool Tests ━━━\n');

// =============================================================================
// START CONNECTION
// =============================================================================

console.log('start connection:');

test('clickPin when not active starts connection, returns null', () => {
  const tool = createConnectTool();
  const result = tool.clickPin('U1.1Y');
  assert.equal(result, null);
});

test('clickPin when not active sets tool to active', () => {
  const tool = createConnectTool();
  tool.clickPin('U1.1Y');
  assert.equal(tool.isActive(), true);
});

test('isActive is false initially', () => {
  const tool = createConnectTool();
  assert.equal(tool.isActive(), false);
});

// =============================================================================
// ADD TURNING POINTS
// =============================================================================

console.log('\nadd turning points:');

test('clickPoint when active adds turning point', () => {
  const tool = createConnectTool();
  tool.clickPin('U1.1Y');
  tool.clickPoint({ x: 10, y: 5 });
  const preview = tool.getPreview();
  assert.equal(preview.points.length, 1);
  assert.deepEqual(preview.points[0], { x: 10, y: 5 });
});

test('clickPoint when not active returns null and does nothing', () => {
  const tool = createConnectTool();
  const result = tool.clickPoint({ x: 10, y: 5 });
  assert.equal(result, null);
  assert.equal(tool.isActive(), false);
});

test('clickPoint always returns null', () => {
  const tool = createConnectTool();
  tool.clickPin('U1.1Y');
  const result = tool.clickPoint({ x: 10, y: 5 });
  assert.equal(result, null);
});

test('multiple turning points are accumulated', () => {
  const tool = createConnectTool();
  tool.clickPin('U1.1Y');
  tool.clickPoint({ x: 10, y: 0 });
  tool.clickPoint({ x: 10, y: 20 });
  tool.clickPoint({ x: 30, y: 20 });
  const preview = tool.getPreview();
  assert.equal(preview.points.length, 3);
});

// =============================================================================
// ORTHOGONAL ENFORCEMENT
// =============================================================================

console.log('\northogonal enforcement:');

test('first point is accepted as-is (no previous reference)', () => {
  const tool = createConnectTool();
  tool.clickPin('U1.1Y');
  tool.clickPoint({ x: 7, y: 3 });
  const preview = tool.getPreview();
  assert.deepEqual(preview.points[0], { x: 7, y: 3 });
});

test('aligned horizontal point is kept unchanged', () => {
  const tool = createConnectTool();
  tool.clickPin('U1.1Y');
  tool.clickPoint({ x: 10, y: 5 });
  tool.clickPoint({ x: 20, y: 5 }); // same Y = horizontal
  const preview = tool.getPreview();
  assert.deepEqual(preview.points[1], { x: 20, y: 5 });
});

test('aligned vertical point is kept unchanged', () => {
  const tool = createConnectTool();
  tool.clickPin('U1.1Y');
  tool.clickPoint({ x: 10, y: 5 });
  tool.clickPoint({ x: 10, y: 25 }); // same X = vertical
  const preview = tool.getPreview();
  assert.deepEqual(preview.points[1], { x: 10, y: 25 });
});

test('diagonal snap: smaller dx → snap X to prev (vertical segment)', () => {
  const tool = createConnectTool();
  tool.clickPin('U1.1Y');
  tool.clickPoint({ x: 10, y: 5 });
  // dx=2, dy=15 → dx is smaller, snap X to 10, keep Y
  tool.clickPoint({ x: 12, y: 20 });
  const preview = tool.getPreview();
  assert.deepEqual(preview.points[1], { x: 10, y: 20 });
});

test('diagonal snap: smaller dy → snap Y to prev (horizontal segment)', () => {
  const tool = createConnectTool();
  tool.clickPin('U1.1Y');
  tool.clickPoint({ x: 10, y: 5 });
  // dx=20, dy=3 → dy is smaller, snap Y to 5, keep X
  tool.clickPoint({ x: 30, y: 8 });
  const preview = tool.getPreview();
  assert.deepEqual(preview.points[1], { x: 30, y: 5 });
});

test('diagonal snap: equal dx and dy → snap X (vertical preference)', () => {
  const tool = createConnectTool();
  tool.clickPin('U1.1Y');
  tool.clickPoint({ x: 10, y: 10 });
  // dx=5, dy=5 → equal, dx<=dy so snap X to prev
  tool.clickPoint({ x: 15, y: 15 });
  const preview = tool.getPreview();
  assert.deepEqual(preview.points[1], { x: 10, y: 15 });
});

test('snap applies relative to previous turning point, not origin', () => {
  const tool = createConnectTool();
  tool.clickPin('U1.1Y');
  tool.clickPoint({ x: 10, y: 5 });
  tool.clickPoint({ x: 10, y: 20 }); // vertical (aligned)
  // Now prev is (10,20), attempt diagonal (13,35): dx=3, dy=15 → snap X
  tool.clickPoint({ x: 13, y: 35 });
  const preview = tool.getPreview();
  assert.deepEqual(preview.points[2], { x: 10, y: 35 });
});

// =============================================================================
// COMPLETE CONNECTION
// =============================================================================

console.log('\ncomplete connection:');

test('clickPin when active completes connection, returns two commands', () => {
  const tool = createConnectTool();
  tool.clickPin('U1.1Y');
  tool.clickPoint({ x: 10, y: 5 });
  const cmds = tool.clickPin('U2.1A');
  assert.equal(Array.isArray(cmds), true);
  assert.equal(cmds.length, 2);
});

test('first command is connect with from/to', () => {
  const tool = createConnectTool();
  tool.clickPin('U1.1Y');
  tool.clickPoint({ x: 10, y: 5 });
  const cmds = tool.clickPin('U2.1A');
  assert.deepEqual(cmds[0], { type: 'connect', from: 'U1.1Y', to: 'U2.1A' });
});

test('second command is route with from/to/via', () => {
  const tool = createConnectTool();
  tool.clickPin('U1.1Y');
  tool.clickPoint({ x: 10, y: 5 });
  tool.clickPoint({ x: 10, y: 20 });
  const cmds = tool.clickPin('U2.1A');
  assert.deepEqual(cmds[1], {
    type: 'route',
    from: 'U1.1Y',
    to: 'U2.1A',
    via: [{ x: 10, y: 5 }, { x: 10, y: 20 }]
  });
});

test('complete resets state to inactive', () => {
  const tool = createConnectTool();
  tool.clickPin('U1.1Y');
  tool.clickPoint({ x: 10, y: 5 });
  tool.clickPin('U2.1A');
  assert.equal(tool.isActive(), false);
});

test('complete with no turning points returns empty via array', () => {
  const tool = createConnectTool();
  tool.clickPin('U1.1Y');
  const cmds = tool.clickPin('U2.1A');
  assert.deepEqual(cmds[0], { type: 'connect', from: 'U1.1Y', to: 'U2.1A' });
  assert.deepEqual(cmds[1], { type: 'route', from: 'U1.1Y', to: 'U2.1A', via: [] });
});

test('click same pin twice completes with self-connection', () => {
  const tool = createConnectTool();
  tool.clickPin('U1.1Y');
  const cmds = tool.clickPin('U1.1Y');
  assert.deepEqual(cmds[0], { type: 'connect', from: 'U1.1Y', to: 'U1.1Y' });
  assert.deepEqual(cmds[1], { type: 'route', from: 'U1.1Y', to: 'U1.1Y', via: [] });
});

// =============================================================================
// CANCEL (ESCAPE)
// =============================================================================

console.log('\ncancel (escape):');

test('escape returns cancel-connect command', () => {
  const tool = createConnectTool();
  tool.clickPin('U1.1Y');
  const cmd = tool.escape();
  assert.deepEqual(cmd, { type: 'cancel-connect' });
});

test('escape resets tool to inactive', () => {
  const tool = createConnectTool();
  tool.clickPin('U1.1Y');
  tool.clickPoint({ x: 10, y: 5 });
  tool.escape();
  assert.equal(tool.isActive(), false);
});

test('escape when not active still returns cancel-connect', () => {
  const tool = createConnectTool();
  const cmd = tool.escape();
  assert.deepEqual(cmd, { type: 'cancel-connect' });
});

test('escape clears preview points', () => {
  const tool = createConnectTool();
  tool.clickPin('U1.1Y');
  tool.clickPoint({ x: 10, y: 5 });
  tool.escape();
  const preview = tool.getPreview();
  assert.equal(preview.from, null);
  assert.deepEqual(preview.points, []);
  assert.equal(preview.active, false);
});

// =============================================================================
// MULTIPLE SEQUENTIAL CONNECTIONS
// =============================================================================

console.log('\nmultiple sequential connections:');

test('can start new connection after completing one', () => {
  const tool = createConnectTool();
  // First connection
  tool.clickPin('U1.1Y');
  tool.clickPin('U2.1A');
  // Second connection
  const result = tool.clickPin('U3.2B');
  assert.equal(result, null);
  assert.equal(tool.isActive(), true);
});

test('second connection is independent of first', () => {
  const tool = createConnectTool();
  // First connection
  tool.clickPin('U1.1Y');
  tool.clickPoint({ x: 50, y: 50 });
  tool.clickPin('U2.1A');
  // Second connection
  tool.clickPin('U3.2B');
  tool.clickPoint({ x: 5, y: 5 });
  const cmds = tool.clickPin('U4.3C');
  assert.deepEqual(cmds[0], { type: 'connect', from: 'U3.2B', to: 'U4.3C' });
  assert.deepEqual(cmds[1].via, [{ x: 5, y: 5 }]);
});

test('can start new connection after cancel', () => {
  const tool = createConnectTool();
  tool.clickPin('U1.1Y');
  tool.escape();
  tool.clickPin('U2.1A');
  assert.equal(tool.isActive(), true);
  const preview = tool.getPreview();
  assert.equal(preview.from, 'U2.1A');
});

// =============================================================================
// GET PREVIEW
// =============================================================================

console.log('\ngetPreview:');

test('preview when inactive shows null from and empty points', () => {
  const tool = createConnectTool();
  const preview = tool.getPreview();
  assert.equal(preview.from, null);
  assert.deepEqual(preview.points, []);
  assert.equal(preview.active, false);
});

test('preview when active shows source pin', () => {
  const tool = createConnectTool();
  tool.clickPin('U1.1Y');
  const preview = tool.getPreview();
  assert.equal(preview.from, 'U1.1Y');
  assert.equal(preview.active, true);
});

test('preview points reflect all added turning points', () => {
  const tool = createConnectTool();
  tool.clickPin('U1.1Y');
  tool.clickPoint({ x: 10, y: 0 });
  tool.clickPoint({ x: 10, y: 20 });
  tool.clickPoint({ x: 30, y: 20 });
  const preview = tool.getPreview();
  assert.equal(preview.points.length, 3);
  assert.deepEqual(preview.points[0], { x: 10, y: 0 });
  assert.deepEqual(preview.points[1], { x: 10, y: 20 });
  assert.deepEqual(preview.points[2], { x: 30, y: 20 });
});

test('preview returns a copy (not internal reference)', () => {
  const tool = createConnectTool();
  tool.clickPin('U1.1Y');
  tool.clickPoint({ x: 10, y: 5 });
  const preview1 = tool.getPreview();
  preview1.points.push({ x: 99, y: 99 }); // mutate returned copy
  const preview2 = tool.getPreview();
  assert.equal(preview2.points.length, 1); // internal state unchanged
});

// =============================================================================
// EDGE CASES
// =============================================================================

console.log('\nedge cases:');

test('multiple tool instances are independent', () => {
  const tool1 = createConnectTool();
  const tool2 = createConnectTool();
  tool1.clickPin('U1.1Y');
  assert.equal(tool1.isActive(), true);
  assert.equal(tool2.isActive(), false);
});

test('clickPoint with zero offset from prev is accepted (degenerate segment)', () => {
  const tool = createConnectTool();
  tool.clickPin('U1.1Y');
  tool.clickPoint({ x: 10, y: 5 });
  tool.clickPoint({ x: 10, y: 5 }); // same point
  const preview = tool.getPreview();
  assert.equal(preview.points.length, 2);
  assert.deepEqual(preview.points[1], { x: 10, y: 5 });
});

test('pin ids with dots and numbers are preserved exactly', () => {
  const tool = createConnectTool();
  tool.clickPin('U33.1A');
  const cmds = tool.clickPin('U7.4Y');
  assert.equal(cmds[0].from, 'U33.1A');
  assert.equal(cmds[0].to, 'U7.4Y');
});

test('fractional coordinates are preserved', () => {
  const tool = createConnectTool();
  tool.clickPin('U1.1Y');
  tool.clickPoint({ x: 2.54, y: 1.27 });
  const preview = tool.getPreview();
  assert.equal(preview.points[0].x, 2.54);
  assert.equal(preview.points[0].y, 1.27);
});

test('negative coordinates work', () => {
  const tool = createConnectTool();
  tool.clickPin('U1.1Y');
  tool.clickPoint({ x: -5, y: -10 });
  tool.clickPoint({ x: -5, y: 20 }); // vertical (aligned)
  const preview = tool.getPreview();
  assert.deepEqual(preview.points[0], { x: -5, y: -10 });
  assert.deepEqual(preview.points[1], { x: -5, y: 20 });
});

test('all returned commands have a type property', () => {
  const tool = createConnectTool();
  tool.clickPin('U1.1Y');
  tool.clickPoint({ x: 10, y: 5 });
  const cmds = tool.clickPin('U2.1A');
  for (const cmd of cmds) {
    assert.ok(cmd.type, 'command must have type');
  }
  const cancel = tool.escape();
  assert.ok(cancel.type, 'cancel must have type');
});

// =============================================================================
// SUMMARY
// =============================================================================

console.log(`\n━━━ Results: ${passed} passed, ${failed} failed ━━━\n`);
if (failed > 0) process.exit(1);
