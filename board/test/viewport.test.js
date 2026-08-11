/**
 * Components Board — Viewport Unit Tests
 * Task 1.6: Viewport renderer tests
 * Run: node board/test/viewport.test.js
 */

import assert from 'node:assert/strict';
import { createViewport } from '../src/view/viewport.js';
import { createConfig } from '../src/model/config.js';

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

function approxEqual(a, b, tolerance = 0.001) {
  if (Math.abs(a - b) > tolerance) {
    throw new Error(`Expected ${a} ≈ ${b} (tolerance ${tolerance})`);
  }
}

console.log('\n━━━ Viewport Tests ━━━\n');

// --- Setup ---
const configA4 = createConfig(); // Default A4 landscape
const configA3 = createConfig({ paper: { size: 'A3' } });

// --- createViewport ---

console.log('createViewport:');

test('creates viewport with default config', () => {
  const vp = createViewport(configA4);
  assert.ok(vp);
  assert.equal(typeof vp.getViewState, 'function');
  assert.equal(typeof vp.setZoom, 'function');
  assert.equal(typeof vp.zoomFit, 'function');
  assert.equal(typeof vp.setPan, 'function');
  assert.equal(typeof vp.screenToWorld, 'function');
  assert.equal(typeof vp.worldToScreen, 'function');
  assert.equal(typeof vp.getGridLines, 'function');
  assert.equal(typeof vp.getPaperRect, 'function');
  assert.equal(typeof vp.getMarginRect, 'function');
  assert.equal(typeof vp.getRenderData, 'function');
});

test('getViewState returns correct paper dimensions', () => {
  const vp = createViewport(configA4);
  const state = vp.getViewState();
  assert.equal(state.width_mm, 297);
  assert.equal(state.height_mm, 210);
  assert.equal(state.zoom, 100);
  assert.equal(state.panX, 0);
  assert.equal(state.panY, 0);
});

test('A3 paper produces different dimensions than A4', () => {
  const vpA3 = createViewport(configA3);
  const vpA4 = createViewport(configA4);
  const stateA3 = vpA3.getViewState();
  const stateA4 = vpA4.getViewState();
  assert.equal(stateA3.width_mm, 420);
  assert.equal(stateA3.height_mm, 297);
  assert.notEqual(stateA3.width_mm, stateA4.width_mm);
  assert.notEqual(stateA3.height_mm, stateA4.height_mm);
});

// --- setZoom ---

console.log('\nsetZoom:');

test('setZoom changes zoom level', () => {
  const vp = createViewport(configA4);
  const state = vp.setZoom(200);
  assert.equal(state.zoom, 200);
});

test('setZoom clamps to minimum 10%', () => {
  const vp = createViewport(configA4);
  const state = vp.setZoom(5);
  assert.equal(state.zoom, 10);
});

test('setZoom clamps to maximum 5000%', () => {
  const vp = createViewport(configA4);
  const state = vp.setZoom(6000);
  assert.equal(state.zoom, 5000);
});

test('setZoom accepts boundary values', () => {
  const vp = createViewport(configA4);
  assert.equal(vp.setZoom(10).zoom, 10);
  assert.equal(vp.setZoom(5000).zoom, 5000);
});

// --- setPan ---

console.log('\nsetPan:');

test('setPan updates pan offset', () => {
  const vp = createViewport(configA4);
  const state = vp.setPan(50, -30);
  assert.equal(state.panX, 50);
  assert.equal(state.panY, -30);
});

test('setPan allows negative values', () => {
  const vp = createViewport(configA4);
  const state = vp.setPan(-100, -200);
  assert.equal(state.panX, -100);
  assert.equal(state.panY, -200);
});

// --- screenToWorld ---

console.log('\nscreenToWorld:');

test('screenToWorld at center = (0,0) when no pan', () => {
  const vp = createViewport(configA4);
  const result = vp.screenToWorld(500, 400, 1000, 800);
  approxEqual(result.x, 0);
  approxEqual(result.y, 0);
});

test('screenToWorld with pan offset', () => {
  const vp = createViewport(configA4);
  vp.setPan(10, 20);
  // world = (screen - center) / scale - pan
  // world = (500 - 500) / 1 - 10 = -10
  const result = vp.screenToWorld(500, 400, 1000, 800);
  approxEqual(result.x, -10);
  approxEqual(result.y, -20);
});

test('screenToWorld with zoom', () => {
  const vp = createViewport(configA4);
  vp.setZoom(200);
  // world = (600 - 500) / 2 - 0 = 50
  const result = vp.screenToWorld(600, 400, 1000, 800);
  approxEqual(result.x, 50);
  approxEqual(result.y, 0);
});

test('screenToWorld top-left corner gives negative world coords', () => {
  const vp = createViewport(configA4);
  const result = vp.screenToWorld(0, 0, 1000, 800);
  approxEqual(result.x, -500);
  approxEqual(result.y, -400);
});

// --- worldToScreen ---

console.log('\nworldToScreen:');

test('worldToScreen at origin with no pan = screen center', () => {
  const vp = createViewport(configA4);
  const result = vp.worldToScreen(0, 0, 1000, 800);
  approxEqual(result.x, 500);
  approxEqual(result.y, 400);
});

test('worldToScreen with zoom 200% doubles offset from center', () => {
  const vp = createViewport(configA4);
  vp.setZoom(200);
  // screen = (10 + 0) * 2 + 500 = 520
  const result = vp.worldToScreen(10, 0, 1000, 800);
  approxEqual(result.x, 520);
  approxEqual(result.y, 400);
});

test('worldToScreen round-trip (screen→world→screen = original)', () => {
  const vp = createViewport(configA4);
  vp.setZoom(150);
  vp.setPan(25, -15);
  const screenWidth = 1200;
  const screenHeight = 900;
  const origX = 347;
  const origY = 612;

  const world = vp.screenToWorld(origX, origY, screenWidth, screenHeight);
  const back = vp.worldToScreen(world.x, world.y, screenWidth, screenHeight);
  approxEqual(back.x, origX);
  approxEqual(back.y, origY);
});

test('worldToScreen with pan moves result on screen', () => {
  const vp = createViewport(configA4);
  vp.setPan(50, 0);
  // screen = (0 + 50) * 1 + 500 = 550
  const result = vp.worldToScreen(0, 0, 1000, 800);
  approxEqual(result.x, 550);
  approxEqual(result.y, 400);
});

// --- getGridLines ---

console.log('\ngetGridLines:');

test('getGridLines returns major and minor arrays', () => {
  const vp = createViewport(configA4);
  const grid = vp.getGridLines(1000, 800);
  assert.ok(Array.isArray(grid.major));
  assert.ok(Array.isArray(grid.minor));
  assert.ok(Array.isArray(grid.labels));
  assert.ok(grid.major.length > 0);
  assert.ok(grid.minor.length > 0);
});

test('getGridLines major spacing matches config.grid.major_mm', () => {
  const vp = createViewport(configA4);
  const grid = vp.getGridLines(1000, 800);
  // At 100% zoom, major lines should be 10 screen units apart
  // Find vertical major lines (same y span)
  const verticalMajors = grid.major.filter(l => l.x1 === l.x2);
  if (verticalMajors.length >= 2) {
    // Sort by x position
    verticalMajors.sort((a, b) => a.x1 - b.x1);
    const spacing = verticalMajors[1].x1 - verticalMajors[0].x1;
    approxEqual(spacing, 10, 0.01); // major_mm = 10, zoom = 100%
  }
});

test('getGridLines labels show mm values', () => {
  const vp = createViewport(configA4);
  const grid = vp.getGridLines(1000, 800);
  assert.ok(grid.labels.length > 0);
  // Labels should have text, x, y
  const label = grid.labels[0];
  assert.ok('text' in label);
  assert.ok('x' in label);
  assert.ok('y' in label);
  // Text should be a number string (mm value)
  assert.ok(!isNaN(Number(label.text)), `Label text "${label.text}" should be numeric`);
});

test('getGridLines count changes with zoom', () => {
  const vp = createViewport(configA4);
  const gridZoom100 = vp.getGridLines(1000, 800);
  vp.setZoom(50);
  const gridZoom50 = vp.getGridLines(1000, 800);
  // At 50% zoom, more world is visible → more grid lines
  assert.ok(
    gridZoom50.minor.length > gridZoom100.minor.length,
    `Expected more minor lines at 50% zoom (${gridZoom50.minor.length}) than 100% (${gridZoom100.minor.length})`
  );
});

test('getGridLines line objects have correct shape', () => {
  const vp = createViewport(configA4);
  const grid = vp.getGridLines(1000, 800);
  const line = grid.major[0];
  assert.ok('x1' in line);
  assert.ok('y1' in line);
  assert.ok('x2' in line);
  assert.ok('y2' in line);
});

// --- getPaperRect ---

console.log('\ngetPaperRect:');

test('getPaperRect at 100% zoom, no pan', () => {
  const vp = createViewport(configA4);
  const rect = vp.getPaperRect(1000, 800);
  // Paper: 297×210, center at screen (500,400)
  // topLeft world = (-148.5, -105) → screen = (351.5, 295)
  approxEqual(rect.x, 500 - 148.5);
  approxEqual(rect.y, 400 - 105);
  approxEqual(rect.width, 297);
  approxEqual(rect.height, 210);
});

test('getPaperRect changes with zoom', () => {
  const vp = createViewport(configA4);
  vp.setZoom(200);
  const rect = vp.getPaperRect(1000, 800);
  // At 200%, paper should be 297*2 = 594 pixels wide
  approxEqual(rect.width, 594);
  approxEqual(rect.height, 420);
});

test('getPaperRect changes with pan', () => {
  const vp = createViewport(configA4);
  vp.setPan(50, 0);
  const rect = vp.getPaperRect(1000, 800);
  // Pan shifts paper on screen
  // topLeft world = (-148.5, -105), with panX=50:
  // screenX = (-148.5 + 50) * 1 + 500 = 401.5
  approxEqual(rect.x, 401.5);
  approxEqual(rect.width, 297);
});

// --- getMarginRect ---

console.log('\ngetMarginRect:');

test('getMarginRect is smaller than paper by margin amounts', () => {
  const vp = createViewport(configA4);
  const paper = vp.getPaperRect(1000, 800);
  const margin = vp.getMarginRect(1000, 800);
  // Margins: 10mm all sides, at 100% zoom = 10px
  approxEqual(margin.x, paper.x + 10);
  approxEqual(margin.y, paper.y + 10);
  approxEqual(margin.width, paper.width - 20); // left + right
  approxEqual(margin.height, paper.height - 20); // top + bottom
});

test('getMarginRect scales with zoom', () => {
  const vp = createViewport(configA4);
  vp.setZoom(200);
  const paper = vp.getPaperRect(1000, 800);
  const margin = vp.getMarginRect(1000, 800);
  // At 200%, margins are 10*2=20 screen pixels
  approxEqual(margin.x, paper.x + 20);
  approxEqual(margin.y, paper.y + 20);
  approxEqual(margin.width, paper.width - 40);
  approxEqual(margin.height, paper.height - 40);
});

// --- zoomFit ---

console.log('\nzoomFit:');

test('zoomFit calculates correct zoom to show full paper', () => {
  const vp = createViewport(configA4);
  const state = vp.zoomFit(1000, 800);
  // Paper is 297×210. Screen is 1000×800.
  // zoomX = (1000/297)*100*0.95 ≈ 319.87
  // zoomY = (800/210)*100*0.95 ≈ 361.90
  // Min = 319.87 → paper fits width-wise
  const expectedZoom = (1000 / 297) * 100 * 0.95;
  approxEqual(state.zoom, expectedZoom, 0.01);
  assert.equal(state.panX, 0);
  assert.equal(state.panY, 0);
});

test('zoomFit on tall screen constrains by height', () => {
  const vp = createViewport(configA4);
  const state = vp.zoomFit(2000, 300);
  // zoomX = (2000/297)*100*0.95 ≈ 639.73
  // zoomY = (300/210)*100*0.95 ≈ 135.71
  // Min = zoomY
  const expectedZoom = (300 / 210) * 100 * 0.95;
  approxEqual(state.zoom, expectedZoom, 0.01);
});

test('zoomFit resets pan to zero', () => {
  const vp = createViewport(configA4);
  vp.setPan(100, 200);
  const state = vp.zoomFit(1000, 800);
  assert.equal(state.panX, 0);
  assert.equal(state.panY, 0);
});

// --- getRenderData ---

console.log('\ngetRenderData:');

test('getRenderData with empty state', () => {
  const vp = createViewport(configA4);
  const state = { component: { devices: {}, connections: [] }, board: { placements: {}, routes: [], labels: [] } };
  const rd = vp.getRenderData(state, 1000, 800);
  assert.ok(rd.paper);
  assert.ok(rd.margin);
  assert.ok(rd.grid);
  assert.deepEqual(rd.devices, []);
  assert.deepEqual(rd.connections, []);
  assert.deepEqual(rd.routes, []);
  assert.deepEqual(rd.labels, []);
});

test('getRenderData includes devices at correct screen positions', () => {
  const vp = createViewport(configA4);
  const state = {
    component: { devices: { U1: { ref: 'U1', part: 'digital.74HC04' } }, connections: [] },
    board: { placements: { U1: { ref: 'U1', x: 50, y: 30, rotation: 90 } }, routes: [], labels: [] },
  };
  const rd = vp.getRenderData(state, 1000, 800);
  assert.equal(rd.devices.length, 1);
  const d = rd.devices[0];
  assert.equal(d.ref, 'U1');
  assert.equal(d.part, 'digital.74HC04');
  assert.equal(d.x, 50);
  assert.equal(d.y, 30);
  assert.equal(d.rotation, 90);
  // At 100% zoom, no pan: screenX = (50+0)*1 + 500 = 550
  approxEqual(d.screenX, 550);
  approxEqual(d.screenY, 430);
});

test('getRenderData includes connections', () => {
  const vp = createViewport(configA4);
  const state = {
    component: {
      devices: { U1: { ref: 'U1', part: 'a' }, U2: { ref: 'U2', part: 'b' } },
      connections: [{ from: 'U1.1', to: 'U2.2', via: [{ x: 10, y: 20 }] }],
    },
    board: { placements: {}, routes: [], labels: [] },
  };
  const rd = vp.getRenderData(state, 1000, 800);
  assert.equal(rd.connections.length, 1);
  const conn = rd.connections[0];
  assert.equal(conn.from, 'U1.1');
  assert.equal(conn.to, 'U2.2');
  assert.equal(conn.via.length, 1);
  approxEqual(conn.via[0].screenX, 510);
  approxEqual(conn.via[0].screenY, 420);
});

test('getRenderData includes routes with screen-converted via points', () => {
  const vp = createViewport(configA4);
  const state = {
    component: { devices: {}, connections: [] },
    board: {
      placements: {},
      routes: [{ from: 'U1.1', to: 'U2.2', via: [{ x: -20, y: 40 }, { x: 60, y: 40 }] }],
      labels: [],
    },
  };
  const rd = vp.getRenderData(state, 1000, 800);
  assert.equal(rd.routes.length, 1);
  const route = rd.routes[0];
  assert.equal(route.from, 'U1.1');
  assert.equal(route.to, 'U2.2');
  assert.equal(route.via.length, 2);
  approxEqual(route.via[0].screenX, 480); // (-20+0)*1 + 500
  approxEqual(route.via[0].screenY, 440); // (40+0)*1 + 400
  approxEqual(route.via[1].screenX, 560); // (60+0)*1 + 500
});

test('getRenderData includes labels at screen positions', () => {
  const vp = createViewport(configA4);
  const state = {
    component: { devices: {}, connections: [] },
    board: {
      placements: {},
      routes: [],
      labels: [{ id: 'L1', text: 'Hello', x: 100, y: -50 }],
    },
  };
  const rd = vp.getRenderData(state, 1000, 800);
  assert.equal(rd.labels.length, 1);
  const lbl = rd.labels[0];
  assert.equal(lbl.id, 'L1');
  assert.equal(lbl.text, 'Hello');
  assert.equal(lbl.x, 100);
  assert.equal(lbl.y, -50);
  approxEqual(lbl.screenX, 600); // (100+0)*1 + 500
  approxEqual(lbl.screenY, 350); // (-50+0)*1 + 400
});

test('getRenderData device without placement defaults to (0,0)', () => {
  const vp = createViewport(configA4);
  const state = {
    component: { devices: { U1: { ref: 'U1', part: 'test' } }, connections: [] },
    board: { placements: {}, routes: [], labels: [] },
  };
  const rd = vp.getRenderData(state, 1000, 800);
  assert.equal(rd.devices.length, 1);
  assert.equal(rd.devices[0].x, 0);
  assert.equal(rd.devices[0].y, 0);
  approxEqual(rd.devices[0].screenX, 500);
  approxEqual(rd.devices[0].screenY, 400);
});

test('getRenderData respects current zoom and pan', () => {
  const vp = createViewport(configA4);
  vp.setZoom(200);
  vp.setPan(10, -5);
  const state = {
    component: { devices: { R1: { ref: 'R1', part: 'resistor' } }, connections: [] },
    board: { placements: { R1: { ref: 'R1', x: 20, y: 30, rotation: 0 } }, routes: [], labels: [] },
  };
  const rd = vp.getRenderData(state, 1000, 800);
  const d = rd.devices[0];
  // screenX = (20 + 10) * 2 + 500 = 560
  // screenY = (30 + (-5)) * 2 + 400 = 450
  approxEqual(d.screenX, 560);
  approxEqual(d.screenY, 450);
});

// --- panByScreenDelta ---

console.log('\npanByScreenDelta:');

test('panByScreenDelta moves view at zoom 100%', () => {
  const vp = createViewport(configA4);
  vp.panByScreenDelta(100, -50);
  const vs = vp.getViewState();
  approxEqual(vs.panX, 100); // 100px / scale(1.0) = 100mm
  approxEqual(vs.panY, -50);
});

test('panByScreenDelta accounts for zoom level', () => {
  const vp = createViewport(configA4);
  vp.setZoom(200); // scale = 2.0
  vp.panByScreenDelta(100, -50);
  const vs = vp.getViewState();
  approxEqual(vs.panX, 50); // 100px / 2.0 = 50mm
  approxEqual(vs.panY, -25);
});

test('panByScreenDelta accumulates', () => {
  const vp = createViewport(configA4);
  vp.panByScreenDelta(30, 20);
  vp.panByScreenDelta(10, -5);
  const vs = vp.getViewState();
  approxEqual(vs.panX, 40);
  approxEqual(vs.panY, 15);
});

test('panByScreenDelta with zero does nothing', () => {
  const vp = createViewport(configA4);
  vp.setPan(10, 20);
  vp.panByScreenDelta(0, 0);
  const vs = vp.getViewState();
  approxEqual(vs.panX, 10);
  approxEqual(vs.panY, 20);
});

// --- zoomAtPoint ---

console.log('\nzoomAtPoint:');

test('zoomAtPoint at screen center behaves like setZoom', () => {
  const vp = createViewport(configA4);
  vp.zoomAtPoint(2.0, 500, 400, 1000, 800); // center of 1000×800 screen
  const vs = vp.getViewState();
  approxEqual(vs.zoom, 200);
  // Pan should stay ~0 since we zoomed at center with no prior pan
  approxEqual(vs.panX, 0, 0.01);
  approxEqual(vs.panY, 0, 0.01);
});

test('zoomAtPoint keeps world point under pointer fixed', () => {
  const vp = createViewport(configA4);
  const screenW = 1000, screenH = 800;
  const pointerX = 700, pointerY = 300;

  // Get world point under pointer before zoom
  const worldBefore = vp.screenToWorld(pointerX, pointerY, screenW, screenH);

  // Zoom in 2x at pointer
  vp.zoomAtPoint(2.0, pointerX, pointerY, screenW, screenH);

  // Get world point under same screen position after zoom
  const worldAfter = vp.screenToWorld(pointerX, pointerY, screenW, screenH);

  approxEqual(worldAfter.x, worldBefore.x, 0.01);
  approxEqual(worldAfter.y, worldBefore.y, 0.01);
});

test('zoomAtPoint zoom out keeps point fixed', () => {
  const vp = createViewport(configA4);
  vp.setZoom(200);
  const screenW = 1000, screenH = 800;
  const pointerX = 250, pointerY = 600;

  const worldBefore = vp.screenToWorld(pointerX, pointerY, screenW, screenH);
  vp.zoomAtPoint(0.5, pointerX, pointerY, screenW, screenH);
  const worldAfter = vp.screenToWorld(pointerX, pointerY, screenW, screenH);

  approxEqual(worldAfter.x, worldBefore.x, 0.01);
  approxEqual(worldAfter.y, worldBefore.y, 0.01);
});

test('zoomAtPoint clamps at MIN_ZOOM (10%)', () => {
  const vp = createViewport(configA4);
  vp.setZoom(15);
  vp.zoomAtPoint(0.1, 500, 400, 1000, 800); // 15 * 0.1 = 1.5 → clamped to 10
  const vs = vp.getViewState();
  approxEqual(vs.zoom, 10);
});

test('zoomAtPoint clamps at MAX_ZOOM (5000%)', () => {
  const vp = createViewport(configA4);
  vp.setZoom(4000);
  vp.zoomAtPoint(2.0, 500, 400, 1000, 800); // 4000 * 2 = 8000 → clamped to 5000
  const vs = vp.getViewState();
  approxEqual(vs.zoom, 5000);
});

test('zoomAtPoint returns unchanged state when already at limit', () => {
  const vp = createViewport(configA4);
  vp.setZoom(10);
  const before = vp.getViewState();
  vp.zoomAtPoint(0.5, 500, 400, 1000, 800); // 10 * 0.5 = 5 → clamped to 10
  const after = vp.getViewState();
  approxEqual(after.zoom, 10);
  approxEqual(after.panX, before.panX, 0.01);
  approxEqual(after.panY, before.panY, 0.01);
});

test('zoomAtPoint with existing pan keeps pointer world point', () => {
  const vp = createViewport(configA4);
  vp.setPan(50, -30);
  const screenW = 1000, screenH = 800;
  const pointerX = 400, pointerY = 500;

  const worldBefore = vp.screenToWorld(pointerX, pointerY, screenW, screenH);
  vp.zoomAtPoint(1.5, pointerX, pointerY, screenW, screenH);
  const worldAfter = vp.screenToWorld(pointerX, pointerY, screenW, screenH);

  approxEqual(worldAfter.x, worldBefore.x, 0.01);
  approxEqual(worldAfter.y, worldBefore.y, 0.01);
});

test('zoomAtPoint multiple steps preserve anchor', () => {
  const vp = createViewport(configA4);
  const screenW = 1000, screenH = 800;
  const pointerX = 300, pointerY = 200;

  const worldStart = vp.screenToWorld(pointerX, pointerY, screenW, screenH);

  // Simulate 5 scroll steps
  for (let i = 0; i < 5; i++) {
    vp.zoomAtPoint(1.1, pointerX, pointerY, screenW, screenH);
  }

  const worldEnd = vp.screenToWorld(pointerX, pointerY, screenW, screenH);
  approxEqual(worldEnd.x, worldStart.x, 0.1);
  approxEqual(worldEnd.y, worldStart.y, 0.1);
});

// --- Combined zoom + pan ---

console.log('\nZoom + Pan combined:');

test('pan then zoom at corner preserves point', () => {
  const vp = createViewport(configA4);
  const screenW = 1000, screenH = 800;

  vp.panByScreenDelta(200, -100); // pan first
  const pointerX = 800, pointerY = 100;

  const worldBefore = vp.screenToWorld(pointerX, pointerY, screenW, screenH);
  vp.zoomAtPoint(1.5, pointerX, pointerY, screenW, screenH);
  const worldAfter = vp.screenToWorld(pointerX, pointerY, screenW, screenH);

  approxEqual(worldAfter.x, worldBefore.x, 0.01);
  approxEqual(worldAfter.y, worldBefore.y, 0.01);
});

test('zoom then pan then zoom preserves second anchor', () => {
  const vp = createViewport(configA4);
  const screenW = 1000, screenH = 800;

  vp.zoomAtPoint(1.5, 500, 400, screenW, screenH);
  vp.panByScreenDelta(100, 50);

  const pointerX = 600, pointerY = 350;
  const worldBefore = vp.screenToWorld(pointerX, pointerY, screenW, screenH);
  vp.zoomAtPoint(0.8, pointerX, pointerY, screenW, screenH);
  const worldAfter = vp.screenToWorld(pointerX, pointerY, screenW, screenH);

  approxEqual(worldAfter.x, worldBefore.x, 0.01);
  approxEqual(worldAfter.y, worldBefore.y, 0.01);
});

// --- Summary ---
console.log(`\n━━━ Results: ${passed} passed, ${failed} failed ━━━\n`);
if (failed > 0) process.exit(1);
