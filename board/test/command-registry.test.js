/**
 * Components Board — Command Registry Tests
 * OOP-style command system: groups, aliases, completion, help
 */

import {
  createCommandRegistry,
  createFileCommands, createEditCommands, createViewCommands,
  createToolCommands, createPageCommands, createBoardCommands, createCircuitCommands,
} from '../src/controller/command-registry.js';

// =============================================================================
// Test Harness
// =============================================================================
let passed = 0, failed = 0;
const failures = [];
function assert(condition, msg) { if (condition) passed++; else { failed++; failures.push(msg); } }
function eq(a, b, msg) { const pass = JSON.stringify(a) === JSON.stringify(b); if (pass) passed++; else { failed++; failures.push(`${msg}: got ${JSON.stringify(a)}, expected ${JSON.stringify(b)}`); } }
function section(name) { console.log(`  ${name}`); }

// =============================================================================
// BASIC REGISTRY
// =============================================================================

section('Register and execute — dot notation');
{
  const reg = createCommandRegistry();
  let called = null;
  reg.register({
    name: 'test',
    description: 'Test group',
    commands: {
      'hello': { fn: (args) => { called = args; return { success: true, message: 'hi' }; }, description: 'Say hello', alias: 'hi' },
    },
  });
  const r = reg.execute('test.hello world');
  eq(r.success, true, 'dot exec success');
  eq(called, 'world', 'dot exec args passed');
}

section('Execute — space notation');
{
  const reg = createCommandRegistry();
  let called = null;
  reg.register({ name: 'file', commands: { save: { fn: () => { called = true; return { success: true, message: 'ok' }; } } } });
  reg.execute('file save');
  eq(called, true, 'space notation works');
}

section('Execute — alias');
{
  const reg = createCommandRegistry();
  let called = false;
  reg.register({ name: 'file', commands: { save: { fn: () => { called = true; return { success: true, message: '' }; }, alias: 'save' } } });
  reg.execute('save');
  eq(called, true, 'alias "save" resolves to file.save');
}

section('Execute — auto-alias (command name)');
{
  const reg = createCommandRegistry();
  let args = null;
  reg.register({ name: 'edit', commands: { undo: { fn: (a) => { args = a; return { success: true, message: '' }; } } } });
  reg.execute('undo');
  eq(args, '', 'auto-alias undo works');
}

section('Execute — alias with args');
{
  const reg = createCommandRegistry();
  let received = null;
  reg.register({ name: 'file', commands: { open: { fn: (a) => { received = a; return { success: true, message: '' }; }, alias: 'open' } } });
  reg.execute('open "My Project"');
  eq(received, '"My Project"', 'alias passes args');
}

section('Execute — unknown command');
{
  const reg = createCommandRegistry();
  reg.register({ name: 'file', commands: { save: { fn: () => ({ success: true, message: '' }) } } });
  const r = reg.execute('file.unknown');
  eq(r.success, false, 'unknown command fails');
  assert(r.message.includes('Unknown command'), 'error message helpful');
}

section('Execute — unknown group');
{
  const reg = createCommandRegistry();
  const r = reg.execute('xyz.foo');
  eq(r.success, false, 'unknown group fails');
}

section('Execute — fallback handler');
{
  const reg = createCommandRegistry();
  let fallbackText = null;
  reg.setFallback(text => { fallbackText = text; return { success: true, message: 'fallback' }; });
  const r = reg.execute('place U1 at (50, 30)');
  eq(fallbackText, 'place U1 at (50, 30)', 'fallback receives raw text');
  eq(r.message, 'fallback', 'fallback result returned');
}

section('Execute — group name only shows help');
{
  const reg = createCommandRegistry();
  reg.register({ name: 'file', description: 'Files', commands: { save: { fn: () => ({ success: true, message: '' }), description: 'Save' } } });
  const r = reg.execute('file');
  eq(r.success, true, 'group-only is success');
  assert(r.message.includes('file'), 'group help contains name');
  assert(r.message.includes('save'), 'group help lists commands');
}

// =============================================================================
// TAB COMPLETION
// =============================================================================

section('Complete — group names');
{
  const reg = createCommandRegistry();
  reg.register({ name: 'file', commands: {} });
  reg.register({ name: 'filter', commands: {} });
  reg.register({ name: 'edit', commands: {} });
  const c = reg.complete('fi');
  assert(c.includes('file.'), 'completes file.');
  assert(c.includes('filter.'), 'completes filter.');
  assert(!c.includes('edit.'), 'does not complete edit');
}

section('Complete — command names after dot');
{
  const reg = createCommandRegistry();
  reg.register({ name: 'file', commands: { save: {}, 'save-as': {}, open: {} } });
  const c = reg.complete('file.s');
  assert(c.includes('file.save'), 'completes file.save');
  assert(c.includes('file.save-as'), 'completes file.save-as');
  assert(!c.includes('file.open'), 'does not complete open');
}

section('Complete — empty after full match');
{
  const reg = createCommandRegistry();
  reg.register({ name: 'file', commands: { save: {} } });
  const c = reg.complete('file.save');
  eq(c.length, 0, 'no completion when already complete');
}

// =============================================================================
// HELP
// =============================================================================

section('Help — overview');
{
  const reg = createCommandRegistry();
  reg.register({ name: 'file', description: 'Files', commands: { save: { description: 'Save' } } });
  reg.register({ name: 'edit', description: 'Edit', commands: { undo: { description: 'Undo' } } });
  const h = reg.help();
  assert(h.includes('file'), 'overview has file');
  assert(h.includes('edit'), 'overview has edit');
}

section('Help — specific group');
{
  const reg = createCommandRegistry();
  reg.register({ name: 'file', description: 'Files', commands: {
    save: { description: 'Save project', alias: 'save', args: null },
    open: { description: 'Open project', alias: 'open', args: '[name]' },
  }});
  const h = reg.help('file');
  assert(h.includes('file.save'), 'group help has file.save');
  assert(h.includes('file.open'), 'group help has file.open');
  assert(h.includes('[name]'), 'group help shows args');
  assert(h.includes('(save)'), 'group help shows alias');
}

// =============================================================================
// BUILT-IN GROUP FACTORIES
// =============================================================================

section('createFileCommands — integrates');
{
  const reg = createCommandRegistry();
  let newCalled = false, saveCalled = false, openName = null;
  const fileGroup = createFileCommands({
    onNew: () => { newCalled = true; },
    onOpen: (name) => { openName = name; },
    onSave: () => { saveCalled = true; },
    onSaveAs: () => {},
    onDownload: () => {},
    onRecent: () => [],
  });
  reg.register(fileGroup);

  reg.execute('file.new');
  eq(newCalled, true, 'file.new calls handler');

  reg.execute('save');
  eq(saveCalled, true, 'alias "save" calls handler');

  reg.execute('open "Test Project"');
  eq(openName, 'Test Project', 'open with quoted name');
}

section('createEditCommands — integrates');
{
  const reg = createCommandRegistry();
  let undone = false;
  reg.register(createEditCommands({
    onUndo: () => { undone = true; },
    onRedo: () => {},
    onSelect: () => {},
    onDeselect: () => {},
  }));
  reg.execute('undo');
  eq(undone, true, 'undo alias works');
}

section('createToolCommands — integrates');
{
  const reg = createCommandRegistry();
  let activated = null;
  reg.register(createToolCommands({
    onActivate: (id) => { activated = id; },
    listTools: () => [],
  }));
  reg.execute('tool.connect');
  eq(activated, 'connect', 'tool.connect activates');
}

section('createPageCommands — integrates');
{
  const reg = createCommandRegistry();
  let pageName = null;
  reg.register(createPageCommands({
    onNew: (name) => { pageName = name; },
    onSwitch: () => {},
    onDelete: () => {},
  }));
  reg.execute('page.new "ALU"');
  eq(pageName, 'ALU', 'page.new passes name');
}

section('createBoardCommands — pass-through');
{
  const reg = createCommandRegistry();
  let engineCmd = null;
  reg.register(createBoardCommands({
    runEngine: (cmd) => { engineCmd = cmd; return { success: true, message: '' }; },
  }));
  reg.execute('board.place U1, digital.74HC04 at (50, 30) rotate 0');
  assert(engineCmd && engineCmd.includes('place U1'), 'board.place passes to engine');
}

section('createCircuitCommands — translates');
{
  const reg = createCommandRegistry();
  let engineCmd = null;
  reg.register(createCircuitCommands({
    runEngine: (cmd) => { engineCmd = cmd; return { success: true, message: '' }; },
  }));
  reg.execute('circuit.connect U1.1Y -> U2.CLK');
  eq(engineCmd, 'connect U1.1Y -> U2.CLK', 'circuit.connect passes connect cmd');
}

// =============================================================================
// MULTIPLE ALIASES
// =============================================================================

section('Multiple aliases for one command');
{
  const reg = createCommandRegistry();
  let count = 0;
  reg.register({ name: 'file', commands: { 'save-as': { fn: () => { count++; return { success: true, message: '' }; }, alias: ['save-as', 'saveas', 'sa'] } } });
  reg.execute('save-as "x"');
  reg.execute('saveas "y"');
  reg.execute('sa "z"');
  eq(count, 3, 'all 3 aliases work');
}

// =============================================================================
// LIST
// =============================================================================

section('listGroups');
{
  const reg = createCommandRegistry();
  reg.register({ name: 'file', commands: {} });
  reg.register({ name: 'edit', commands: {} });
  eq(reg.listGroups(), ['file', 'edit'], 'lists groups');
}

section('listCommands');
{
  const reg = createCommandRegistry();
  reg.register({ name: 'file', commands: { save: { description: 'Save', args: null }, open: { description: 'Open', args: '[name]' } } });
  const cmds = reg.listCommands('file');
  eq(cmds.length, 2, '2 commands');
  eq(cmds[0].name, 'file.save', 'full qualified name');
  eq(cmds[1].args, '[name]', 'args preserved');
}

// =============================================================================
// RESULTS
// =============================================================================
console.log();
if (failed > 0) {
  console.log(`━━━ Results: ${passed} passed, ${failed} FAILED ━━━`);
  failures.forEach(f => console.log(`  ✗ ${f}`));
  process.exit(1);
} else {
  console.log(`━━━ Results: ${passed} passed, 0 failed ━━━`);
}
