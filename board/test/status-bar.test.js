/**
 * Components Board — Status Bar Tests
 * Run: node board/test/status-bar.test.js
 */

import assert from 'node:assert/strict';
import { createStatusBar } from '../src/view/status-bar.js';
import { createEngine } from '../src/controller/engine.js';
import { parseCommand } from '../src/controller/parser.js';
import { createExecutor } from '../src/controller/executor.js';
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

/** Helper: create a fresh status bar with real engine + viewport. */
function makeStatusBar(configOverrides = {}) {
  const config = createConfig(configOverrides);
  const executor = createExecutor(undefined, undefined, config);
  const engine = createEngine({ parser: parseCommand, executor });
  const viewport = createViewport(config);
  return { statusBar: createStatusBar(engine, viewport), engine, viewport };
}

console.log('\n━━━ Status Bar Tests ━━━\n');

// --- Creation ---

console.log('creation:');

test('creates with valid engine and viewport', () => {
  const { statusBar } = makeStatusBar();
  assert.ok(statusBar);
  assert.equal(typeof statusBar.getState, 'function');
  assert.equal(typeof statusBar.setTool, 'function');
  assert.equal(typeof statusBar.setCursor, 'function');
  assert.equal(typeof statusBar.getFormattedCursor, 'function');
  assert.equal(typeof statusBar.getFormattedZoom, 'function');
  assert.equal(typeof statusBar.getFormattedPaper, 'function');
  assert.equal(typeof statusBar.setModified, 'function');
});

test('throws without engine', () => {
  const config = createConfig();
  const viewport = createViewport(config);
  assert.throws(() => createStatusBar(null, viewport), /engine/i);
});

test('throws without viewport', () => {
  const executor = createExecutor();
  const engine = createEngine({ parser: parseCommand, executor });
  assert.throws(() => createStatusBar(engine, null), /viewport/i);
});

// --- getState ---

console.log('\ngetState:');

test('getState returns default values', () => {
  const { statusBar } = makeStatusBar();
  const state = statusBar.getState();
  assert.equal(state.tool, 'select');
  assert.equal(state.cursorX, 0);
  assert.equal(state.cursorY, 0);
  assert.equal(state.zoom, 100);
  assert.equal(state.paperSize, 'A4');
  assert.equal(state.orientation, 'landscape');
  assert.equal(state.modified, false);
});

test('getState reflects A3 portrait config', () => {
  const { statusBar } = makeStatusBar({ paper: { size: 'A3', orientation: 'portrait' } });
  const state = statusBar.getState();
  assert.equal(state.paperSize, 'A3');
  assert.equal(state.orientation, 'portrait');
});

// --- setTool ---

console.log('\nsetTool:');

test('setTool updates tool name', () => {
  const { statusBar } = makeStatusBar();
  statusBar.setTool('wire');
  assert.equal(statusBar.getState().tool, 'wire');
});

test('setTool to different tools', () => {
  const { statusBar } = makeStatusBar();
  statusBar.setTool('place');
  assert.equal(statusBar.getState().tool, 'place');
  statusBar.setTool('move');
  assert.equal(statusBar.getState().tool, 'move');
});

// --- setCursor ---

console.log('\nsetCursor:');

test('setCursor updates position', () => {
  const { statusBar } = makeStatusBar();
  statusBar.setCursor(42.5, -15.0);
  const state = statusBar.getState();
  assert.equal(state.cursorX, 42.5);
  assert.equal(state.cursorY, -15.0);
});

test('setCursor with zero values', () => {
  const { statusBar } = makeStatusBar();
  statusBar.setCursor(0, 0);
  const state = statusBar.getState();
  assert.equal(state.cursorX, 0);
  assert.equal(state.cursorY, 0);
});

// --- getFormattedCursor ---

console.log('\ngetFormattedCursor:');

test('getFormattedCursor formats positive values', () => {
  const { statusBar } = makeStatusBar();
  statusBar.setCursor(42.5, 15.0);
  assert.equal(statusBar.getFormattedCursor(), 'x: 42.5  y: 15.0 mm');
});

test('getFormattedCursor formats negative values', () => {
  const { statusBar } = makeStatusBar();
  statusBar.setCursor(-10.3, -25.7);
  assert.equal(statusBar.getFormattedCursor(), 'x: -10.3  y: -25.7 mm');
});

test('getFormattedCursor formats integers with decimal', () => {
  const { statusBar } = makeStatusBar();
  statusBar.setCursor(100, -50);
  assert.equal(statusBar.getFormattedCursor(), 'x: 100.0  y: -50.0 mm');
});

test('getFormattedCursor formats zero', () => {
  const { statusBar } = makeStatusBar();
  statusBar.setCursor(0, 0);
  assert.equal(statusBar.getFormattedCursor(), 'x: 0.0  y: 0.0 mm');
});

// --- getFormattedZoom ---

console.log('\ngetFormattedZoom:');

test('getFormattedZoom shows default 100%', () => {
  const { statusBar } = makeStatusBar();
  assert.equal(statusBar.getFormattedZoom(), '100%');
});

test('getFormattedZoom reflects viewport zoom change', () => {
  const { statusBar, viewport } = makeStatusBar();
  viewport.setZoom(200);
  assert.equal(statusBar.getFormattedZoom(), '200%');
});

test('getFormattedZoom reflects 50% zoom', () => {
  const { statusBar, viewport } = makeStatusBar();
  viewport.setZoom(50);
  assert.equal(statusBar.getFormattedZoom(), '50%');
});

// --- getFormattedPaper ---

console.log('\ngetFormattedPaper:');

test('getFormattedPaper shows A4 L for landscape', () => {
  const { statusBar } = makeStatusBar();
  assert.equal(statusBar.getFormattedPaper(), 'A4 L');
});

test('getFormattedPaper shows A3 P for portrait', () => {
  const { statusBar } = makeStatusBar({ paper: { size: 'A3', orientation: 'portrait' } });
  assert.equal(statusBar.getFormattedPaper(), 'A3 P');
});

test('getFormattedPaper shows A2 L for A2 landscape', () => {
  const { statusBar } = makeStatusBar({ paper: { size: 'A2', orientation: 'landscape' } });
  assert.equal(statusBar.getFormattedPaper(), 'A2 L');
});

// --- setModified ---

console.log('\nsetModified:');

test('setModified to true', () => {
  const { statusBar } = makeStatusBar();
  statusBar.setModified(true);
  assert.equal(statusBar.getState().modified, true);
});

test('setModified to false after true', () => {
  const { statusBar } = makeStatusBar();
  statusBar.setModified(true);
  statusBar.setModified(false);
  assert.equal(statusBar.getState().modified, false);
});

// --- Integration ---

console.log('\nintegration:');

test('zoom from viewport reflects in status bar getState', () => {
  const { statusBar, viewport } = makeStatusBar();
  viewport.setZoom(75);
  const state = statusBar.getState();
  assert.equal(state.zoom, 75);
});

// --- Summary ---

console.log(`\n━━━ Results: ${passed} passed, ${failed} failed ━━━\n`);
if (failed > 0) process.exit(1);
