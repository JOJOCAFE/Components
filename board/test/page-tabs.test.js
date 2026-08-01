/**
 * Components Board — Page Tabs Tests
 * Run: node board/test/page-tabs.test.js
 */

import assert from 'node:assert/strict';
import { createPageTabs } from '../src/view/page-tabs.js';
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

/** Helper: create a fresh page tabs with a real engine. */
function makeTabs() {
  const engine = createEngine({ parser: parseCommand, executor: createExecutor() });
  return { tabs: createPageTabs(engine), engine };
}

console.log('\n━━━ Page Tabs Tests ━━━\n');

// --- Creation ---

console.log('creation:');

test('creates with a valid engine', () => {
  const { tabs } = makeTabs();
  assert.ok(tabs);
  assert.equal(typeof tabs.getPages, 'function');
  assert.equal(typeof tabs.getActivePage, 'function');
  assert.equal(typeof tabs.addPage, 'function');
  assert.equal(typeof tabs.switchPage, 'function');
  assert.equal(typeof tabs.renamePage, 'function');
  assert.equal(typeof tabs.deletePage, 'function');
  assert.equal(typeof tabs.canDelete, 'function');
});

test('throws without engine', () => {
  assert.throws(() => createPageTabs(null), /engine/i);
});

test('throws with engine missing run()', () => {
  assert.throws(() => createPageTabs({ getState: () => {} }), /engine/i);
});

// --- getPages ---

console.log('\ngetPages:');

test('getPages returns default page', () => {
  const { tabs } = makeTabs();
  const pages = tabs.getPages();
  assert.equal(pages.length, 1);
  assert.equal(pages[0].name, 'Page 1');
  assert.equal(pages[0].active, true);
});

test('getPages returns multiple pages after add', () => {
  const { tabs } = makeTabs();
  tabs.addPage('Page 2');
  const pages = tabs.getPages();
  assert.equal(pages.length, 2);
  assert.equal(pages[0].name, 'Page 1');
  assert.equal(pages[1].name, 'Page 2');
});

// --- getActivePage ---

console.log('\ngetActivePage:');

test('getActivePage returns first page by default', () => {
  const { tabs } = makeTabs();
  assert.equal(tabs.getActivePage(), 'Page 1');
});

test('getActivePage updates after addPage', () => {
  const { tabs } = makeTabs();
  tabs.addPage('Schematic');
  assert.equal(tabs.getActivePage(), 'Schematic');
});

// --- addPage ---

console.log('\naddPage:');

test('addPage creates new page', () => {
  const { tabs } = makeTabs();
  const result = tabs.addPage('Power');
  assert.equal(result.success, true);
  assert.equal(tabs.getPages().length, 2);
});

test('addPage with duplicate name fails', () => {
  const { tabs } = makeTabs();
  tabs.addPage('Power');
  const result = tabs.addPage('Power');
  assert.equal(result.success, false);
});

test('addPage makes new page active', () => {
  const { tabs } = makeTabs();
  tabs.addPage('Logic');
  assert.equal(tabs.getActivePage(), 'Logic');
});

// --- switchPage ---

console.log('\nswitchPage:');

test('switchPage changes active page', () => {
  const { tabs } = makeTabs();
  tabs.addPage('Page 2');
  const result = tabs.switchPage('Page 1');
  assert.equal(result.success, true);
  assert.equal(tabs.getActivePage(), 'Page 1');
});

test('switchPage to nonexistent fails', () => {
  const { tabs } = makeTabs();
  const result = tabs.switchPage('NoSuchPage');
  assert.equal(result.success, false);
});

// --- renamePage ---

console.log('\nrenamePage:');

test('renamePage works', () => {
  const { tabs } = makeTabs();
  const result = tabs.renamePage('Page 1', 'Main');
  assert.equal(result.success, true);
  assert.equal(tabs.getActivePage(), 'Main');
  assert.equal(tabs.getPages()[0].name, 'Main');
});

test('renamePage nonexistent fails', () => {
  const { tabs } = makeTabs();
  const result = tabs.renamePage('Ghost', 'NewName');
  assert.equal(result.success, false);
});

test('renamePage to existing name fails', () => {
  const { tabs } = makeTabs();
  tabs.addPage('Page 2');
  const result = tabs.renamePage('Page 1', 'Page 2');
  assert.equal(result.success, false);
});

// --- deletePage ---

console.log('\ndeletePage:');

test('deletePage removes page', () => {
  const { tabs } = makeTabs();
  tabs.addPage('Page 2');
  const result = tabs.deletePage('Page 2');
  assert.equal(result.success, true);
  assert.equal(tabs.getPages().length, 1);
});

test('deletePage last page fails', () => {
  const { tabs } = makeTabs();
  const result = tabs.deletePage('Page 1');
  assert.equal(result.success, false);
  assert.equal(tabs.getPages().length, 1);
});

test('deletePage switches active if deleted was active', () => {
  const { tabs } = makeTabs();
  tabs.addPage('Page 2');
  tabs.switchPage('Page 1');
  tabs.deletePage('Page 1');
  assert.equal(tabs.getActivePage(), 'Page 2');
});

// --- canDelete ---

console.log('\ncanDelete:');

test('canDelete returns false with 1 page', () => {
  const { tabs } = makeTabs();
  assert.equal(tabs.canDelete(), false);
});

test('canDelete returns true with 2+ pages', () => {
  const { tabs } = makeTabs();
  tabs.addPage('Page 2');
  assert.equal(tabs.canDelete(), true);
});

test('canDelete returns false after deleting back to 1 page', () => {
  const { tabs } = makeTabs();
  tabs.addPage('Page 2');
  tabs.deletePage('Page 2');
  assert.equal(tabs.canDelete(), false);
});

// --- Order ---

console.log('\norder:');

test('multiple pages maintain insertion order', () => {
  const { tabs } = makeTabs();
  tabs.addPage('Alpha');
  tabs.addPage('Beta');
  tabs.addPage('Gamma');
  const pages = tabs.getPages();
  assert.equal(pages.length, 4);
  assert.equal(pages[0].name, 'Page 1');
  assert.equal(pages[1].name, 'Alpha');
  assert.equal(pages[2].name, 'Beta');
  assert.equal(pages[3].name, 'Gamma');
});

// --- Summary ---

console.log(`\n━━━ Results: ${passed} passed, ${failed} failed ━━━\n`);
if (failed > 0) process.exit(1);
