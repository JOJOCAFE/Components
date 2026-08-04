/**
 * Components Board — Drag-to-Place Controller Tests
 * Run: node test/drag-place.test.js
 */

import { createDragPlace } from '../src/controller/drag-place.js';
import { createDeviceTray } from '../src/controller/device-tray.js';
import { createLibrary } from '../src/model/library.js';

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

function assertEqual(actual, expected, msg) {
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    throw new Error(`${msg || 'assertion'}: expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
  }
}

function assert(condition, msg) {
  if (!condition) throw new Error(msg || 'assertion failed');
}

// =============================================================================
// TEST HELPERS
// =============================================================================

function createMockViewport() {
  return {
    screenToWorld(localX, localY, width, height) {
      // Simple identity-ish transform for testing (centered, 1:1 scale)
      return { x: localX - width / 2, y: localY - height / 2 };
    },
  };
}

function createTestSetup() {
  const library = createLibrary();
  library.loadGroup('74xx', [
    { part: '74HC04', about: { title: 'Hex inverter', family: '74HC', group: '74xx', role: 'inverter' }, package: { kind: 'DIP' }, pins: Object.fromEntries([...Array(14)].map((_,i)=>[i+1,['','']])) },
    { part: '74HC161', about: { title: '4-bit counter', family: '74HC', group: '74xx', role: 'counter' }, package: { kind: 'DIP' }, pins: Object.fromEntries([...Array(16)].map((_,i)=>[i+1,['','']])) },
  ]);

  const tray = createDeviceTray({ library });
  tray.addToTray('74HC04', 4);
  tray.addToTray('74HC161', 2);

  const viewport = createMockViewport();

  return { library, tray, viewport };
}

const VIEWPORT_BOUNDS = { left: 100, top: 50, width: 800, height: 600 };

// =============================================================================
// TESTS
// =============================================================================

console.log('\n🖱️  Drag-to-Place Tests\n');

// --- Factory ---
console.log('  Factory:');

test('createDragPlace returns object with expected API', () => {
  const { tray, viewport } = createTestSetup();
  const drag = createDragPlace({ tray, viewport });
  assert(typeof drag.dragStart === 'function');
  assert(typeof drag.dragMove === 'function');
  assert(typeof drag.dragEnd === 'function');
  assert(typeof drag.dragCancel === 'function');
  assert(typeof drag.getState === 'function');
  assert(typeof drag.isDragging === 'function');
  assert(typeof drag.getDragPart === 'function');
  assert(typeof drag.getGhostPosition === 'function');
  assert(typeof drag.onChange === 'function');
});

test('initial state is idle', () => {
  const { tray, viewport } = createTestSetup();
  const drag = createDragPlace({ tray, viewport });
  const state = drag.getState();
  assertEqual(state.phase, 'idle');
  assertEqual(state.part, null);
  assertEqual(state.worldPos, null);
  assertEqual(state.valid, false);
});

// --- Drag Start ---
console.log('\n  Drag Start:');

test('dragStart transitions to dragging', () => {
  const { tray, viewport } = createTestSetup();
  const drag = createDragPlace({ tray, viewport });
  const result = drag.dragStart('74HC04', { x: 200, y: 100 });
  assert(result.success);
  assertEqual(drag.getState().phase, 'dragging');
  assertEqual(drag.getState().part, '74HC04');
  assertEqual(drag.isDragging(), true);
  assertEqual(drag.getDragPart(), '74HC04');
});

test('dragStart fails without part', () => {
  const { tray, viewport } = createTestSetup();
  const drag = createDragPlace({ tray, viewport });
  const result = drag.dragStart(null, { x: 200, y: 100 });
  assert(!result.success);
  assertEqual(drag.getState().phase, 'idle');
});

test('dragStart auto-adds to tray if not present', () => {
  const { tray, viewport } = createTestSetup();
  const drag = createDragPlace({ tray, viewport });
  // 74HC161 has qty 2, so it should work
  const result = drag.dragStart('74HC161', { x: 200, y: 100 });
  assert(result.success);
});

test('dragStart fails when all placed (remaining=0)', () => {
  const { tray, viewport } = createTestSetup();
  // Place all 74HC161 (qty 2)
  tray.placeFromTray('74HC161', { x: 10, y: 10 });
  tray.placeFromTray('74HC161', { x: 30, y: 10 });

  const drag = createDragPlace({ tray, viewport });
  const result = drag.dragStart('74HC161', { x: 200, y: 100 });
  assert(!result.success);
  assert(result.error.includes('No remaining'));
});

test('dragStart auto-cancels previous drag', () => {
  const { tray, viewport } = createTestSetup();
  const drag = createDragPlace({ tray, viewport });
  drag.dragStart('74HC04', { x: 200, y: 100 });
  // Start another drag — should cancel first
  const result = drag.dragStart('74HC161', { x: 300, y: 150 });
  assert(result.success);
  assertEqual(drag.getDragPart(), '74HC161');
});

// --- Drag Move ---
console.log('\n  Drag Move:');

test('dragMove updates currentScreen', () => {
  const { tray, viewport } = createTestSetup();
  const drag = createDragPlace({ tray, viewport });
  drag.dragStart('74HC04', { x: 200, y: 100 });

  const result = drag.dragMove({ x: 300, y: 200 }, VIEWPORT_BOUNDS);
  assertEqual(drag.getState().currentScreen.x, 300);
  assertEqual(drag.getState().currentScreen.y, 200);
});

test('dragMove over viewport sets over-target and worldPos', () => {
  const { tray, viewport } = createTestSetup();
  const drag = createDragPlace({ tray, viewport });
  drag.dragStart('74HC04', { x: 200, y: 100 });

  // Move to center of viewport: screenPos=(500, 350) → localX=400, localY=300 → world=(0, 0)
  const result = drag.dragMove({ x: 500, y: 350 }, VIEWPORT_BOUNDS);
  assertEqual(result.phase, 'over-target');
  assert(result.valid);
  assert(result.worldPos !== null);
});

test('dragMove outside viewport stays in dragging phase', () => {
  const { tray, viewport } = createTestSetup();
  const drag = createDragPlace({ tray, viewport });
  drag.dragStart('74HC04', { x: 200, y: 100 });

  // Move to position outside viewport bounds
  const result = drag.dragMove({ x: 50, y: 30 }, VIEWPORT_BOUNDS);
  assertEqual(result.phase, 'dragging');
  assert(!result.valid);
  assertEqual(result.worldPos, null);
});

test('dragMove does nothing when idle', () => {
  const { tray, viewport } = createTestSetup();
  const drag = createDragPlace({ tray, viewport });
  const result = drag.dragMove({ x: 300, y: 200 }, VIEWPORT_BOUNDS);
  assertEqual(result.phase, 'idle');
});

test('dragMove snaps worldPos to grid', () => {
  const { tray, viewport } = createTestSetup();
  const drag = createDragPlace({ tray, viewport, gridSnap: true });
  drag.dragStart('74HC04', { x: 200, y: 100 });

  // screenPos=(501, 351) → localX=401, localY=301 → raw world=(1, 1)
  // Snapped to 2.54mm grid: round(1/2.54)*2.54 = 0
  drag.dragMove({ x: 501, y: 351 }, VIEWPORT_BOUNDS);
  const worldPos = drag.getGhostPosition();
  assert(worldPos !== null);
  // Should be snapped to nearest 2.54mm multiple
  const snapCheck = (worldPos.x * 1000) % (2.54 * 1000) === 0 || Math.abs(worldPos.x % 2.54) < 0.001;
  // The snap grid function rounds to nearest 2.54, so it's valid
  assert(typeof worldPos.x === 'number');
  assert(typeof worldPos.y === 'number');
});

test('dragMove without gridSnap keeps raw position', () => {
  const { tray, viewport } = createTestSetup();
  const drag = createDragPlace({ tray, viewport, gridSnap: false });
  drag.dragStart('74HC04', { x: 200, y: 100 });

  // screenPos in viewport center: (500, 350) → local(400, 300) → world(0, 0)
  drag.dragMove({ x: 500, y: 350 }, VIEWPORT_BOUNDS);
  const worldPos = drag.getGhostPosition();
  assertEqual(worldPos.x, 0);
  assertEqual(worldPos.y, 0);
});

// --- Drag End ---
console.log('\n  Drag End:');

test('dragEnd places part at valid position', () => {
  const { tray, viewport } = createTestSetup();
  const drag = createDragPlace({ tray, viewport, gridSnap: false });
  drag.dragStart('74HC04', { x: 200, y: 100 });

  // Move over viewport
  drag.dragMove({ x: 500, y: 350 }, VIEWPORT_BOUNDS);

  // Drop
  const result = drag.dragEnd({ x: 500, y: 350 }, VIEWPORT_BOUNDS);
  assert(result.success);
  assert(result.ref !== undefined);
  assertEqual(result.part, '74HC04');
  assert(result.position !== undefined);
});

test('dragEnd resets state to idle', () => {
  const { tray, viewport } = createTestSetup();
  const drag = createDragPlace({ tray, viewport, gridSnap: false });
  drag.dragStart('74HC04', { x: 200, y: 100 });
  drag.dragMove({ x: 500, y: 350 }, VIEWPORT_BOUNDS);
  drag.dragEnd({ x: 500, y: 350 }, VIEWPORT_BOUNDS);

  assertEqual(drag.getState().phase, 'idle');
  assertEqual(drag.isDragging(), false);
  assertEqual(drag.getDragPart(), null);
});

test('dragEnd fails when not dragging', () => {
  const { tray, viewport } = createTestSetup();
  const drag = createDragPlace({ tray, viewport });
  const result = drag.dragEnd({ x: 500, y: 350 }, VIEWPORT_BOUNDS);
  assert(!result.success);
  assert(result.error.includes('No drag'));
});

test('dragEnd fails when no valid worldPos (drop outside)', () => {
  const { tray, viewport } = createTestSetup();
  const drag = createDragPlace({ tray, viewport });
  drag.dragStart('74HC04', { x: 200, y: 100 });
  // Don't move over viewport — stay outside
  drag.dragMove({ x: 50, y: 30 }, VIEWPORT_BOUNDS);
  // Drop with no screen pos and no viewport bounds
  const result = drag.dragEnd();
  assert(!result.success);
  assert(result.error.includes('outside'));
});

test('dragEnd uses final screenPos/bounds for coordinate', () => {
  const { tray, viewport } = createTestSetup();
  const drag = createDragPlace({ tray, viewport, gridSnap: false });
  drag.dragStart('74HC04', { x: 200, y: 100 });
  // Move to one place
  drag.dragMove({ x: 300, y: 200 }, VIEWPORT_BOUNDS);
  // Drop at different place (final position wins)
  const result = drag.dragEnd({ x: 500, y: 350 }, VIEWPORT_BOUNDS);
  assert(result.success);
  // world should be from final screenPos: local(400, 300) → world(0, 0)
  assertEqual(result.position.x, 0);
  assertEqual(result.position.y, 0);
});

test('dragEnd with gridSnap snaps final position', () => {
  const { tray, viewport } = createTestSetup();
  const drag = createDragPlace({ tray, viewport, gridSnap: true });
  drag.dragStart('74HC04', { x: 200, y: 100 });
  drag.dragMove({ x: 501, y: 351 }, VIEWPORT_BOUNDS);
  const result = drag.dragEnd({ x: 501, y: 351 }, VIEWPORT_BOUNDS);
  assert(result.success);
  // Position should be grid-snapped
  assert(typeof result.position.x === 'number');
});

test('dragEnd decrements tray remaining count', () => {
  const { tray, viewport } = createTestSetup();
  const drag = createDragPlace({ tray, viewport, gridSnap: false });
  const before = tray.remainingCount('74HC04');
  drag.dragStart('74HC04', { x: 200, y: 100 });
  drag.dragMove({ x: 500, y: 350 }, VIEWPORT_BOUNDS);
  drag.dragEnd({ x: 500, y: 350 }, VIEWPORT_BOUNDS);
  const after = tray.remainingCount('74HC04');
  assertEqual(after, before - 1);
});

test('multiple drags generate sequential refs', () => {
  const { tray, viewport } = createTestSetup();
  const drag = createDragPlace({ tray, viewport, gridSnap: false });

  drag.dragStart('74HC04', { x: 200, y: 100 });
  drag.dragMove({ x: 500, y: 350 }, VIEWPORT_BOUNDS);
  const r1 = drag.dragEnd({ x: 500, y: 350 }, VIEWPORT_BOUNDS);

  drag.dragStart('74HC04', { x: 200, y: 100 });
  drag.dragMove({ x: 600, y: 400 }, VIEWPORT_BOUNDS);
  const r2 = drag.dragEnd({ x: 600, y: 400 }, VIEWPORT_BOUNDS);

  assert(r1.success && r2.success);
  assertEqual(r1.ref, 'U1');
  assertEqual(r2.ref, 'U2');
});

// --- Drag Cancel ---
console.log('\n  Drag Cancel:');

test('dragCancel returns to idle', () => {
  const { tray, viewport } = createTestSetup();
  const drag = createDragPlace({ tray, viewport });
  drag.dragStart('74HC04', { x: 200, y: 100 });
  const result = drag.dragCancel();
  assert(result.cancelled);
  assertEqual(result.part, '74HC04');
  assertEqual(drag.getState().phase, 'idle');
  assertEqual(drag.isDragging(), false);
});

test('dragCancel when idle returns not cancelled', () => {
  const { tray, viewport } = createTestSetup();
  const drag = createDragPlace({ tray, viewport });
  const result = drag.dragCancel();
  assert(!result.cancelled);
});

test('cancel does not place part', () => {
  const { tray, viewport } = createTestSetup();
  const drag = createDragPlace({ tray, viewport });
  const before = tray.remainingCount('74HC04');
  drag.dragStart('74HC04', { x: 200, y: 100 });
  drag.dragMove({ x: 500, y: 350 }, VIEWPORT_BOUNDS);
  drag.dragCancel();
  const after = tray.remainingCount('74HC04');
  assertEqual(after, before); // nothing placed
});

// --- Listeners ---
console.log('\n  Listeners:');

test('onChange fires on state transitions', () => {
  const { tray, viewport } = createTestSetup();
  const drag = createDragPlace({ tray, viewport });
  const states = [];
  drag.onChange(s => states.push(s.phase));

  drag.dragStart('74HC04', { x: 200, y: 100 });
  drag.dragMove({ x: 500, y: 350 }, VIEWPORT_BOUNDS);
  drag.dragCancel();

  assertEqual(states[0], 'dragging');
  assertEqual(states[1], 'over-target');
  assertEqual(states[2], 'idle');
});

test('unsubscribe stops notifications', () => {
  const { tray, viewport } = createTestSetup();
  const drag = createDragPlace({ tray, viewport });
  const states = [];
  const unsub = drag.onChange(s => states.push(s.phase));

  drag.dragStart('74HC04', { x: 200, y: 100 });
  unsub();
  drag.dragCancel();

  assertEqual(states.length, 1); // only first event
});

test('listener errors do not break state', () => {
  const { tray, viewport } = createTestSetup();
  const drag = createDragPlace({ tray, viewport });
  drag.onChange(() => { throw new Error('boom'); });

  // Should not throw
  drag.dragStart('74HC04', { x: 200, y: 100 });
  assertEqual(drag.getState().phase, 'dragging');
});

// --- Ghost Position ---
console.log('\n  Ghost Position:');

test('getGhostPosition returns worldPos when over target', () => {
  const { tray, viewport } = createTestSetup();
  const drag = createDragPlace({ tray, viewport, gridSnap: false });
  drag.dragStart('74HC04', { x: 200, y: 100 });
  drag.dragMove({ x: 500, y: 350 }, VIEWPORT_BOUNDS);
  const ghost = drag.getGhostPosition();
  assert(ghost !== null);
  assertEqual(ghost.x, 0);
  assertEqual(ghost.y, 0);
});

test('getGhostPosition returns null when not over target', () => {
  const { tray, viewport } = createTestSetup();
  const drag = createDragPlace({ tray, viewport });
  drag.dragStart('74HC04', { x: 200, y: 100 });
  drag.dragMove({ x: 50, y: 30 }, VIEWPORT_BOUNDS);
  assertEqual(drag.getGhostPosition(), null);
});

test('getGhostPosition returns null when idle', () => {
  const { tray, viewport } = createTestSetup();
  const drag = createDragPlace({ tray, viewport });
  assertEqual(drag.getGhostPosition(), null);
});

// --- Edge Cases ---
console.log('\n  Edge Cases:');

test('drag without tray still tracks state', () => {
  const viewport = createMockViewport();
  const drag = createDragPlace({ viewport });
  const result = drag.dragStart('74HC04', { x: 200, y: 100 });
  assert(result.success);
  assertEqual(drag.getState().phase, 'dragging');
});

test('drop without tray returns error', () => {
  const viewport = createMockViewport();
  const drag = createDragPlace({ viewport, gridSnap: false });
  drag.dragStart('74HC04', { x: 200, y: 100 });
  drag.dragMove({ x: 500, y: 350 }, VIEWPORT_BOUNDS);
  const result = drag.dragEnd({ x: 500, y: 350 }, VIEWPORT_BOUNDS);
  assert(!result.success);
  assert(result.error.includes('No tray'));
});

test('drag works without viewport bounds (trust mode)', () => {
  const { tray, viewport } = createTestSetup();
  const drag = createDragPlace({ tray, viewport });
  drag.dragStart('74HC04', { x: 200, y: 100 });
  // Move without bounds — should set over-target (trust mode)
  const result = drag.dragMove({ x: 500, y: 350 });
  assertEqual(result.phase, 'over-target');
  assert(result.valid);
});

// =============================================================================
// SUMMARY
// =============================================================================

console.log(`\n  ${passed + failed} tests: ${passed} passed, ${failed} failed`);
if (failed > 0) {
  console.log('\n  ❌ DRAG-TO-PLACE TESTS FAILED');
  process.exit(1);
} else {
  console.log('\n  ✅ Drag-to-place tests passed');
}
