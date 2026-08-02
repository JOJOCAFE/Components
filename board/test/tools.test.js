/**
 * Components Board — Tool Plugin System Tests
 * Run: node board/test/tools.test.js
 */

import assert from 'node:assert/strict';
import { createToolSystem } from '../src/controller/tools.js';

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

console.log('\n━━━ Tool Plugin System Tests ━━━\n');

// =============================================================================
// REGISTRATION
// =============================================================================

console.log('registration:');

test('creates with Phase 1 tools preloaded', () => {
  const tools = createToolSystem();
  const list = tools.list();
  assert.equal(list.length, 8);
});

test('creates empty when preload=false', () => {
  const tools = createToolSystem({ preload: false });
  assert.equal(tools.list().length, 0);
});

test('register a custom tool', () => {
  const tools = createToolSystem({ preload: false });
  tools.register({
    id: 'measure', name: 'Measure', icon: 'ruler', shortcut: 'M',
    commands: ['measure'],
    gestures: { click: 'measure', drag: 'measure-area' }
  });
  assert.equal(tools.list().length, 1);
  assert.equal(tools.get('measure').name, 'Measure');
});

test('register from JSON definition object', () => {
  const tools = createToolSystem({ preload: false });
  const json = JSON.parse(JSON.stringify({
    id: 'pan', name: 'Pan', icon: 'hand', shortcut: 'H',
    commands: ['pan'],
    gestures: { drag: 'pan' }
  }));
  tools.register(json);
  assert.equal(tools.get('pan').id, 'pan');
});

test('reject duplicate registration', () => {
  const tools = createToolSystem({ preload: false });
  tools.register({
    id: 'test', name: 'Test', icon: 'x', shortcut: 'X',
    commands: ['test'], gestures: { click: 'test' }
  });
  assert.throws(() => {
    tools.register({
      id: 'test', name: 'Test2', icon: 'y', shortcut: 'Y',
      commands: ['test2'], gestures: { click: 'test2' }
    });
  }, /already registered/i);
});

test('reject definition without id', () => {
  const tools = createToolSystem({ preload: false });
  assert.throws(() => {
    tools.register({ name: 'Bad', icon: 'x', shortcut: 'X', commands: [], gestures: {} });
  }, /id/i);
});

test('reject definition without name', () => {
  const tools = createToolSystem({ preload: false });
  assert.throws(() => {
    tools.register({ id: 'x', icon: 'x', shortcut: 'X', commands: [], gestures: {} });
  }, /name/i);
});

test('reject definition without icon', () => {
  const tools = createToolSystem({ preload: false });
  assert.throws(() => {
    tools.register({ id: 'x', name: 'X', shortcut: 'X', commands: [], gestures: {} });
  }, /icon/i);
});

test('reject definition without shortcut', () => {
  const tools = createToolSystem({ preload: false });
  assert.throws(() => {
    tools.register({ id: 'x', name: 'X', icon: 'x', commands: [], gestures: {} });
  }, /shortcut/i);
});

test('reject definition without commands array', () => {
  const tools = createToolSystem({ preload: false });
  assert.throws(() => {
    tools.register({ id: 'x', name: 'X', icon: 'x', shortcut: 'X', gestures: {} });
  }, /commands/i);
});

test('reject definition without gestures object', () => {
  const tools = createToolSystem({ preload: false });
  assert.throws(() => {
    tools.register({ id: 'x', name: 'X', icon: 'x', shortcut: 'X', commands: [] });
  }, /gestures/i);
});

// =============================================================================
// ACTIVATION
// =============================================================================

console.log('\nactivation:');

test('default active tool is select', () => {
  const tools = createToolSystem();
  assert.equal(tools.getActive().id, 'select');
});

test('activate a registered tool', () => {
  const tools = createToolSystem();
  const result = tools.activate('connect');
  assert.equal(result.id, 'connect');
  assert.equal(tools.getActive().id, 'connect');
});

test('activate replaces previous active', () => {
  const tools = createToolSystem();
  tools.activate('eraser');
  tools.activate('label');
  assert.equal(tools.getActive().id, 'label');
});

test('activate non-existent tool throws', () => {
  const tools = createToolSystem();
  assert.throws(() => tools.activate('nonexistent'), /unknown tool/i);
});

test('deactivate returns to select', () => {
  const tools = createToolSystem();
  tools.activate('eraser');
  const result = tools.deactivate();
  assert.equal(result.id, 'select');
  assert.equal(tools.getActive().id, 'select');
});

test('getActive returns null when no preload and none activated', () => {
  const tools = createToolSystem({ preload: false });
  assert.equal(tools.getActive(), null);
});

// =============================================================================
// SHORTCUT DISPATCH
// =============================================================================

console.log('\nshortcut dispatch:');

test('shortcut V activates select', () => {
  const tools = createToolSystem();
  tools.activate('eraser');
  const result = tools.dispatchShortcut('V');
  assert.equal(result.id, 'select');
});

test('shortcut W activates connect', () => {
  const tools = createToolSystem();
  const result = tools.dispatchShortcut('W');
  assert.equal(result.id, 'connect');
});

test('shortcut E activates eraser', () => {
  const tools = createToolSystem();
  const result = tools.dispatchShortcut('E');
  assert.equal(result.id, 'eraser');
});

test('shortcut L activates tray', () => {
  const tools = createToolSystem();
  const result = tools.dispatchShortcut('L');
  assert.equal(result.id, 'tray');
});

test('shortcut G activates guide', () => {
  const tools = createToolSystem();
  const result = tools.dispatchShortcut('G');
  assert.equal(result.id, 'guide');
});

test('shortcut T activates label', () => {
  const tools = createToolSystem();
  const result = tools.dispatchShortcut('T');
  assert.equal(result.id, 'label');
});

test('shortcut I activates inspect', () => {
  const tools = createToolSystem();
  const result = tools.dispatchShortcut('I');
  assert.equal(result.id, 'inspect');
});

test('shortcut . activates more', () => {
  const tools = createToolSystem();
  const result = tools.dispatchShortcut('.');
  assert.equal(result.id, 'more');
});

test('shortcut is case-insensitive', () => {
  const tools = createToolSystem();
  const result = tools.dispatchShortcut('w');
  assert.equal(result.id, 'connect');
});

test('unknown shortcut returns null', () => {
  const tools = createToolSystem();
  const result = tools.dispatchShortcut('Z');
  assert.equal(result, null);
});

test('Escape returns to select', () => {
  const tools = createToolSystem();
  tools.activate('connect');
  const result = tools.dispatchShortcut('Escape');
  assert.equal(result.id, 'select');
});

test('escape (lowercase) returns to select', () => {
  const tools = createToolSystem();
  tools.activate('eraser');
  const result = tools.dispatchShortcut('escape');
  assert.equal(result.id, 'select');
});

// =============================================================================
// GESTURE DISPATCH
// =============================================================================

console.log('\ngesture dispatch:');

test('select tool click → select command', () => {
  const tools = createToolSystem();
  tools.activate('select');
  assert.equal(tools.dispatchGesture('click'), 'select');
});

test('select tool drag → move command', () => {
  const tools = createToolSystem();
  tools.activate('select');
  assert.equal(tools.dispatchGesture('drag'), 'move');
});

test('select tool escape → deselect command', () => {
  const tools = createToolSystem();
  tools.activate('select');
  assert.equal(tools.dispatchGesture('escape'), 'deselect');
});

test('connect tool click → start-wire', () => {
  const tools = createToolSystem();
  tools.activate('connect');
  assert.equal(tools.dispatchGesture('click'), 'start-wire');
});

test('connect tool drag → end-wire', () => {
  const tools = createToolSystem();
  tools.activate('connect');
  assert.equal(tools.dispatchGesture('drag'), 'end-wire');
});

test('connect tool escape → cancel-wire', () => {
  const tools = createToolSystem();
  tools.activate('connect');
  assert.equal(tools.dispatchGesture('escape'), 'cancel-wire');
});

test('eraser tool click → erase', () => {
  const tools = createToolSystem();
  tools.activate('eraser');
  assert.equal(tools.dispatchGesture('click'), 'erase');
});

test('eraser tool drag → erase', () => {
  const tools = createToolSystem();
  tools.activate('eraser');
  assert.equal(tools.dispatchGesture('drag'), 'erase');
});

test('label tool click → add-label', () => {
  const tools = createToolSystem();
  tools.activate('label');
  assert.equal(tools.dispatchGesture('click'), 'add-label');
});

test('label tool dblclick → edit-label', () => {
  const tools = createToolSystem();
  tools.activate('label');
  assert.equal(tools.dispatchGesture('dblclick'), 'edit-label');
});

test('inspect tool click → inspect', () => {
  const tools = createToolSystem();
  tools.activate('inspect');
  assert.equal(tools.dispatchGesture('click'), 'inspect');
});

test('guide tool dblclick → remove-guide', () => {
  const tools = createToolSystem();
  tools.activate('guide');
  assert.equal(tools.dispatchGesture('dblclick'), 'remove-guide');
});

test('unmapped gesture returns null', () => {
  const tools = createToolSystem();
  tools.activate('inspect');
  assert.equal(tools.dispatchGesture('drag'), null);
});

test('gesture dispatch with no active tool returns null', () => {
  const tools = createToolSystem({ preload: false });
  assert.equal(tools.dispatchGesture('click'), null);
});

// =============================================================================
// LIST TOOLS
// =============================================================================

console.log('\nlist tools:');

test('list returns all tools in registration order', () => {
  const tools = createToolSystem();
  const list = tools.list();
  assert.equal(list[0].id, 'select');
  assert.equal(list[1].id, 'tray');
  assert.equal(list[2].id, 'guide');
  assert.equal(list[3].id, 'connect');
  assert.equal(list[4].id, 'eraser');
  assert.equal(list[5].id, 'label');
  assert.equal(list[6].id, 'inspect');
  assert.equal(list[7].id, 'more');
});

test('list returns frozen definitions', () => {
  const tools = createToolSystem();
  const list = tools.list();
  assert.throws(() => { list[0].id = 'hacked'; }, /Cannot assign/i);
});

test('get returns specific tool by id', () => {
  const tools = createToolSystem();
  const tool = tools.get('connect');
  assert.equal(tool.name, 'Connect');
  assert.equal(tool.icon, 'wire');
  assert.equal(tool.shortcut, 'W');
  assert.deepEqual(tool.commands, ['start-wire', 'end-wire', 'cancel-wire']);
});

test('get returns null for unknown id', () => {
  const tools = createToolSystem();
  assert.equal(tools.get('nonexistent'), null);
});

test('list includes custom-registered tools', () => {
  const tools = createToolSystem();
  tools.register({
    id: 'zoom', name: 'Zoom', icon: 'magnify', shortcut: 'Z',
    commands: ['zoom-in', 'zoom-out'],
    gestures: { click: 'zoom-in', drag: 'zoom-out' }
  });
  assert.equal(tools.list().length, 9);
  assert.equal(tools.list()[8].id, 'zoom');
});

// =============================================================================
// PLUGIN LOADING (JSON)
// =============================================================================

console.log('\nplugin loading:');

test('load tool from parsed JSON', () => {
  const tools = createToolSystem({ preload: false });
  const json = `{
    "id": "select", "name": "Select", "icon": "arrow", "shortcut": "V",
    "commands": ["select", "move", "rotate", "delete"],
    "gestures": {"click": "select", "drag": "move", "escape": "deselect"}
  }`;
  tools.register(JSON.parse(json));
  assert.equal(tools.get('select').id, 'select');
  assert.equal(tools.get('select').commands.length, 4);
});

test('load multiple tools from JSON array', () => {
  const tools = createToolSystem({ preload: false });
  const defs = JSON.parse(`[
    {"id": "a", "name": "A", "icon": "a", "shortcut": "A", "commands": ["a"], "gestures": {"click": "a"}},
    {"id": "b", "name": "B", "icon": "b", "shortcut": "B", "commands": ["b"], "gestures": {"click": "b"}}
  ]`);
  for (const def of defs) tools.register(def);
  assert.equal(tools.list().length, 2);
});

// =============================================================================
// EDGE CASES
// =============================================================================

console.log('\nedge cases:');

test('shortcut stored as uppercase', () => {
  const tools = createToolSystem({ preload: false });
  tools.register({
    id: 'test', name: 'Test', icon: 'x', shortcut: 'x',
    commands: ['test'], gestures: { click: 'test' }
  });
  assert.equal(tools.get('test').shortcut, 'X');
});

test('Phase 1 tools have correct shortcuts', () => {
  const tools = createToolSystem();
  assert.equal(tools.get('select').shortcut, 'V');
  assert.equal(tools.get('tray').shortcut, 'L');
  assert.equal(tools.get('guide').shortcut, 'G');
  assert.equal(tools.get('connect').shortcut, 'W');
  assert.equal(tools.get('eraser').shortcut, 'E');
  assert.equal(tools.get('label').shortcut, 'T');
  assert.equal(tools.get('inspect').shortcut, 'I');
  assert.equal(tools.get('more').shortcut, '.');
});

test('multiple activations dont corrupt state', () => {
  const tools = createToolSystem();
  tools.activate('eraser');
  tools.activate('connect');
  tools.activate('label');
  tools.activate('select');
  assert.equal(tools.getActive().id, 'select');
  assert.equal(tools.list().length, 8);
});

// =============================================================================
// SUMMARY
// =============================================================================

console.log(`\n━━━ Results: ${passed} passed, ${failed} failed ━━━\n`);
if (failed > 0) process.exit(1);
