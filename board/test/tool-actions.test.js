/**
 * Components Board — Tool Actions Tests
 * Run: node test/tool-actions.test.js
 */

import assert from 'node:assert/strict';
import {
  trayPick, trayPlace, trayRemove, trayList,
  guideToggle, guideClear,
  eraserClick, eraserShiftClick, eraserClickNothing,
  labelCreate, labelEdit, labelMove, labelDelete,
  inspect, inspectClear,
} from '../src/controller/tool-actions.js';

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

console.log('\n━━━ Tool Actions Tests ━━━\n');

// =============================================================================
// 3.3 PROJECT TRAY
// =============================================================================

console.log('tray:');

test('trayPick returns tray-pick command', () => {
  const cmd = trayPick('74HC00');
  assert.deepEqual(cmd, { type: 'tray-pick', part: '74HC00' });
});

test('trayPick with empty string', () => {
  const cmd = trayPick('');
  assert.deepEqual(cmd, { type: 'tray-pick', part: '' });
});

test('trayPlace returns place command with ref:null', () => {
  const cmd = trayPlace('74HC00', { x: 10, y: 20 });
  assert.deepEqual(cmd, { type: 'place', ref: null, part: '74HC00', x: 10, y: 20, rotation: 0 });
});

test('trayPlace with rotation', () => {
  const cmd = trayPlace('74HC04', { x: 5, y: 15 }, 90);
  assert.deepEqual(cmd, { type: 'place', ref: null, part: '74HC04', x: 5, y: 15, rotation: 90 });
});

test('trayPlace at zero position', () => {
  const cmd = trayPlace('R100', { x: 0, y: 0 }, 0);
  assert.deepEqual(cmd, { type: 'place', ref: null, part: 'R100', x: 0, y: 0, rotation: 0 });
});

test('trayRemove returns tray-remove command', () => {
  const cmd = trayRemove('74HC08');
  assert.deepEqual(cmd, { type: 'tray-remove', part: '74HC08' });
});

test('trayRemove with empty string', () => {
  const cmd = trayRemove('');
  assert.deepEqual(cmd, { type: 'tray-remove', part: '' });
});

test('trayList returns frozen copy', () => {
  const items = ['74HC00', '74HC04', '74HC08'];
  const result = trayList(items);
  assert.deepEqual(result, ['74HC00', '74HC04', '74HC08']);
  assert.ok(Object.isFrozen(result));
});

test('trayList does not mutate original', () => {
  const items = ['A', 'B'];
  const result = trayList(items);
  items.push('C');
  assert.equal(result.length, 2);
});

test('trayList with empty array', () => {
  const result = trayList([]);
  assert.deepEqual(result, []);
  assert.ok(Object.isFrozen(result));
});

test('trayList frozen copy cannot be mutated', () => {
  const result = trayList(['X']);
  assert.throws(() => { result.push('Y'); }, TypeError);
});

// =============================================================================
// 3.4 GUIDE
// =============================================================================

console.log('\nguide:');

test('guideToggle hides when currentState=true', () => {
  const cmd = guideToggle('U1.1Y', true);
  assert.deepEqual(cmd, { type: 'guide-hide', pin: 'U1.1Y' });
});

test('guideToggle shows when currentState=false', () => {
  const cmd = guideToggle('U2.3A', false);
  assert.deepEqual(cmd, { type: 'guide-show', pin: 'U2.3A' });
});

test('guideToggle with empty pinId', () => {
  const cmd = guideToggle('', false);
  assert.deepEqual(cmd, { type: 'guide-show', pin: '' });
});

test('guideClear returns guide-clear command', () => {
  const cmd = guideClear();
  assert.deepEqual(cmd, { type: 'guide-clear' });
});

// =============================================================================
// 3.6 ERASER
// =============================================================================

console.log('\neraser:');

test('eraserClick returns delete command', () => {
  const cmd = eraserClick('U1');
  assert.deepEqual(cmd, { type: 'delete', ref: 'U1' });
});

test('eraserClick with null ref', () => {
  const cmd = eraserClick(null);
  assert.deepEqual(cmd, { type: 'delete', ref: null });
});

test('eraserClick with empty string ref', () => {
  const cmd = eraserClick('');
  assert.deepEqual(cmd, { type: 'delete', ref: '' });
});

test('eraserShiftClick returns delete-net command', () => {
  const cmd = eraserShiftClick('NET_VCC');
  assert.deepEqual(cmd, { type: 'delete-net', net: 'NET_VCC' });
});

test('eraserShiftClick with empty netId', () => {
  const cmd = eraserShiftClick('');
  assert.deepEqual(cmd, { type: 'delete-net', net: '' });
});

test('eraserClickNothing returns null', () => {
  const result = eraserClickNothing();
  assert.equal(result, null);
});

// =============================================================================
// 3.7 LABEL
// =============================================================================

console.log('\nlabel:');

test('labelCreate returns label command', () => {
  const cmd = labelCreate('VCC', { x: 10, y: 5 });
  assert.deepEqual(cmd, { type: 'label', text: 'VCC', x: 10, y: 5 });
});

test('labelCreate with empty text', () => {
  const cmd = labelCreate('', { x: 0, y: 0 });
  assert.deepEqual(cmd, { type: 'label', text: '', x: 0, y: 0 });
});

test('labelCreate at zero position', () => {
  const cmd = labelCreate('GND', { x: 0, y: 0 });
  assert.deepEqual(cmd, { type: 'label', text: 'GND', x: 0, y: 0 });
});

test('labelEdit returns label-edit command', () => {
  const cmd = labelEdit('lbl_1', 'DATA BUS');
  assert.deepEqual(cmd, { type: 'label-edit', id: 'lbl_1', text: 'DATA BUS' });
});

test('labelEdit with empty newText', () => {
  const cmd = labelEdit('lbl_2', '');
  assert.deepEqual(cmd, { type: 'label-edit', id: 'lbl_2', text: '' });
});

test('labelMove returns label-move command', () => {
  const cmd = labelMove('lbl_1', { x: 30, y: 40 });
  assert.deepEqual(cmd, { type: 'label-move', id: 'lbl_1', x: 30, y: 40 });
});

test('labelMove to zero position', () => {
  const cmd = labelMove('lbl_3', { x: 0, y: 0 });
  assert.deepEqual(cmd, { type: 'label-move', id: 'lbl_3', x: 0, y: 0 });
});

test('labelDelete returns label-delete command', () => {
  const cmd = labelDelete('lbl_1');
  assert.deepEqual(cmd, { type: 'label-delete', id: 'lbl_1' });
});

test('labelDelete with empty id', () => {
  const cmd = labelDelete('');
  assert.deepEqual(cmd, { type: 'label-delete', id: '' });
});

// =============================================================================
// 3.8 INSPECT
// =============================================================================

console.log('\ninspect:');

test('inspect returns inspect command with frozen info', () => {
  const def = { part: '74HC00', pins: ['1A', '1B', '1Y'], description: 'Quad NAND' };
  const cmd = inspect('U1', def);
  assert.equal(cmd.type, 'inspect');
  assert.equal(cmd.ref, 'U1');
  assert.deepEqual(cmd.info, { part: '74HC00', pins: ['1A', '1B', '1Y'], description: 'Quad NAND' });
});

test('inspect info is frozen (cannot mutate)', () => {
  const def = { part: '74HC04', pins: ['1A', '1Y'], description: 'Hex Inverter' };
  const cmd = inspect('U2', def);
  assert.ok(Object.isFrozen(cmd.info));
  assert.throws(() => { cmd.info.part = 'HACK'; }, TypeError);
});

test('inspect does not mutate original definition', () => {
  const def = { part: '74HC08', pins: ['1A', '1B', '1Y'], description: 'Quad AND' };
  const cmd = inspect('U3', def);
  def.part = 'CHANGED';
  assert.equal(cmd.info.part, '74HC08');
});

test('inspect with null ref', () => {
  const def = { part: '74HC00', pins: [], description: '' };
  const cmd = inspect(null, def);
  assert.equal(cmd.type, 'inspect');
  assert.equal(cmd.ref, null);
});

test('inspect with empty definition fields', () => {
  const def = { part: '', pins: [], description: '' };
  const cmd = inspect('U5', def);
  assert.deepEqual(cmd.info, { part: '', pins: [], description: '' });
});

test('inspectClear returns inspect-clear command', () => {
  const cmd = inspectClear();
  assert.deepEqual(cmd, { type: 'inspect-clear' });
});

// =============================================================================
// CROSS-CUTTING: ALL COMMANDS HAVE TYPE
// =============================================================================

console.log('\ncross-cutting:');

test('all non-null commands have a type property', () => {
  const commands = [
    trayPick('X'),
    trayPlace('X', { x: 0, y: 0 }),
    trayRemove('X'),
    guideToggle('p', true),
    guideToggle('p', false),
    guideClear(),
    eraserClick('U1'),
    eraserShiftClick('N1'),
    labelCreate('T', { x: 0, y: 0 }),
    labelEdit('id', 'T'),
    labelMove('id', { x: 0, y: 0 }),
    labelDelete('id'),
    inspect('U1', { part: 'X', pins: [], description: '' }),
    inspectClear(),
  ];
  for (const cmd of commands) {
    assert.ok(cmd.type, `command must have type: ${JSON.stringify(cmd)}`);
  }
});

test('eraserClickNothing is the only function that returns null', () => {
  assert.equal(eraserClickNothing(), null);
});

// =============================================================================
// SUMMARY
// =============================================================================

console.log(`\n━━━ Results: ${passed} passed, ${failed} failed ━━━\n`);
if (failed > 0) process.exit(1);
