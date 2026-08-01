/**
 * Components Board — Command Parser Unit Tests
 * Run: node board/test/parser.test.js
 */

import assert from 'node:assert/strict';
import { parseCommand, COMMAND_TYPES } from '../src/controller/parser.js';

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

console.log('\n━━━ Command Parser Tests ━━━\n');

// --- COMMAND_TYPES ---

console.log('COMMAND_TYPES:');

test('is a frozen object', () => {
  assert.ok(Object.isFrozen(COMMAND_TYPES));
});

test('has all expected command types', () => {
  const expected = [
    'place', 'move', 'rotate', 'delete', 'connect', 'disconnect',
    'route', 'label', 'select', 'deselect', 'zoom', 'pan',
    'undo', 'redo', 'new-page', 'switch-page', 'rename-page',
    'delete-page', 'set-config', 'error',
  ];
  const values = Object.values(COMMAND_TYPES);
  for (const t of expected) {
    assert.ok(values.includes(t), `Missing type: ${t}`);
  }
});

// --- place ---

console.log('\nplace:');

test('basic place command', () => {
  const result = parseCommand('place U1, digital.74HC04 at (10, 20) rotate 90');
  assert.equal(result.type, 'place');
  assert.equal(result.ref, 'U1');
  assert.equal(result.part, 'digital.74HC04');
  assert.equal(result.x, 10);
  assert.equal(result.y, 20);
  assert.equal(result.rotate, 90);
});

test('place with dotted part name', () => {
  const result = parseCommand('place IC3, lib.memory.AT28C256 at (50.5, 100) rotate 0');
  assert.equal(result.type, 'place');
  assert.equal(result.ref, 'IC3');
  assert.equal(result.part, 'lib.memory.AT28C256');
  assert.equal(result.x, 50.5);
  assert.equal(result.y, 100);
  assert.equal(result.rotate, 0);
});

test('place with negative coordinates', () => {
  const result = parseCommand('place R3, passive.resistor at (-5, -10.5) rotate 270');
  assert.equal(result.type, 'place');
  assert.equal(result.ref, 'R3');
  assert.equal(result.x, -5);
  assert.equal(result.y, -10.5);
  assert.equal(result.rotate, 270);
});

test('place with 180 degree rotation', () => {
  const result = parseCommand('place OUT, connector.header at (0, 0) rotate 180');
  assert.equal(result.type, 'place');
  assert.equal(result.ref, 'OUT');
  assert.equal(result.rotate, 180);
});

test('place rejects invalid angle (45)', () => {
  const result = parseCommand('place U1, digital.74HC04 at (10, 20) rotate 45');
  assert.equal(result.type, 'error');
  assert.ok(result.message.includes('angle'));
});

test('place rejects missing "at"', () => {
  const result = parseCommand('place U1, digital.74HC04 (10, 20) rotate 90');
  assert.equal(result.type, 'error');
});

// --- move ---

console.log('\nmove:');

test('basic move with positive coordinates', () => {
  const result = parseCommand('move U1 to (30, 40)');
  assert.equal(result.type, 'move');
  assert.equal(result.ref, 'U1');
  assert.equal(result.x, 30);
  assert.equal(result.y, 40);
});

test('move with negative coordinates', () => {
  const result = parseCommand('move R3 to (-15.5, -20)');
  assert.equal(result.type, 'move');
  assert.equal(result.ref, 'R3');
  assert.equal(result.x, -15.5);
  assert.equal(result.y, -20);
});

test('move with zero coordinates', () => {
  const result = parseCommand('move IC1 to (0, 0)');
  assert.equal(result.type, 'move');
  assert.equal(result.x, 0);
  assert.equal(result.y, 0);
});

test('move rejects missing "to"', () => {
  const result = parseCommand('move U1 (30, 40)');
  assert.equal(result.type, 'error');
});

// --- rotate ---

console.log('\nrotate:');

test('rotate 0', () => {
  const result = parseCommand('rotate U1 0');
  assert.equal(result.type, 'rotate');
  assert.equal(result.ref, 'U1');
  assert.equal(result.angle, 0);
});

test('rotate 90', () => {
  const result = parseCommand('rotate U1 90');
  assert.equal(result.type, 'rotate');
  assert.equal(result.angle, 90);
});

test('rotate 180', () => {
  const result = parseCommand('rotate R3 180');
  assert.equal(result.type, 'rotate');
  assert.equal(result.angle, 180);
});

test('rotate 270', () => {
  const result = parseCommand('rotate IC2 270');
  assert.equal(result.type, 'rotate');
  assert.equal(result.angle, 270);
});

test('rotate rejects invalid angle 45', () => {
  const result = parseCommand('rotate U1 45');
  assert.equal(result.type, 'error');
  assert.ok(result.message.includes('angle'));
});

test('rotate rejects invalid angle 360', () => {
  const result = parseCommand('rotate U1 360');
  assert.equal(result.type, 'error');
});

// --- delete ---

console.log('\ndelete:');

test('delete simple ref', () => {
  const result = parseCommand('delete U1');
  assert.equal(result.type, 'delete');
  assert.equal(result.ref, 'U1');
});

test('delete ref with underscore', () => {
  const result = parseCommand('delete NET_1');
  assert.equal(result.type, 'delete');
  assert.equal(result.ref, 'NET_1');
});

test('delete rejects empty ref', () => {
  const result = parseCommand('delete');
  assert.equal(result.type, 'error');
});

// --- connect ---

console.log('\nconnect:');

test('connect two pins', () => {
  const result = parseCommand('connect U1.1Y -> U2.1A');
  assert.equal(result.type, 'connect');
  assert.equal(result.from, 'U1.1Y');
  assert.equal(result.to, 'U2.1A');
  assert.equal(result.via, undefined);
});

test('connect with @ pin format', () => {
  const result = parseCommand('connect U1.@2 -> R3.@1');
  assert.equal(result.type, 'connect');
  assert.equal(result.from, 'U1.@2');
  assert.equal(result.to, 'R3.@1');
});

test('connect with via points', () => {
  const result = parseCommand('connect U1.1Y -> U2.1A via (10, 20) (30, 40)');
  assert.equal(result.type, 'connect');
  assert.equal(result.from, 'U1.1Y');
  assert.equal(result.to, 'U2.1A');
  assert.deepEqual(result.via, [{ x: 10, y: 20 }, { x: 30, y: 40 }]);
});

test('connect with single via point', () => {
  const result = parseCommand('connect U1.OUT -> U2.IN via (50, 60)');
  assert.equal(result.type, 'connect');
  assert.deepEqual(result.via, [{ x: 50, y: 60 }]);
});

test('connect rejects missing arrow', () => {
  const result = parseCommand('connect U1.1Y U2.1A');
  assert.equal(result.type, 'error');
});

// --- disconnect ---

console.log('\ndisconnect:');

test('disconnect two pins', () => {
  const result = parseCommand('disconnect U1.1Y -> U2.1A');
  assert.equal(result.type, 'disconnect');
  assert.equal(result.from, 'U1.1Y');
  assert.equal(result.to, 'U2.1A');
});

test('disconnect rejects invalid pin format', () => {
  const result = parseCommand('disconnect U1 -> U2');
  assert.equal(result.type, 'error');
});

// --- route ---

console.log('\nroute:');

test('route with via points', () => {
  const result = parseCommand('route U1.1Y -> U3.2A via (10, 20) (15, 20) (15, 30)');
  assert.equal(result.type, 'route');
  assert.equal(result.from, 'U1.1Y');
  assert.equal(result.to, 'U3.2A');
  assert.deepEqual(result.via, [
    { x: 10, y: 20 },
    { x: 15, y: 20 },
    { x: 15, y: 30 },
  ]);
});

test('route requires via keyword', () => {
  const result = parseCommand('route U1.1Y -> U3.2A');
  assert.equal(result.type, 'error');
  assert.ok(result.message.includes('via'));
});

// --- label ---

console.log('\nlabel:');

test('basic label', () => {
  const result = parseCommand('label "VCC" at (100, 5)');
  assert.equal(result.type, 'label');
  assert.equal(result.text, 'VCC');
  assert.equal(result.x, 100);
  assert.equal(result.y, 5);
});

test('label with escaped quote', () => {
  const result = parseCommand('label "Pin \\"A\\"" at (50, 50)');
  assert.equal(result.type, 'label');
  assert.equal(result.text, 'Pin "A"');
});

test('label with escaped backslash', () => {
  const result = parseCommand('label "path\\\\dir" at (0, 0)');
  assert.equal(result.type, 'label');
  assert.equal(result.text, 'path\\dir');
});

test('label with spaces in text', () => {
  const result = parseCommand('label "Data Bus D0-D7" at (200, 50)');
  assert.equal(result.type, 'label');
  assert.equal(result.text, 'Data Bus D0-D7');
});

test('label rejects missing quotes', () => {
  const result = parseCommand('label VCC at (100, 5)');
  assert.equal(result.type, 'error');
});

// --- select / deselect ---

console.log('\nselect / deselect:');

test('select a ref', () => {
  const result = parseCommand('select U1');
  assert.equal(result.type, 'select');
  assert.equal(result.ref, 'U1');
});

test('select ref with underscore', () => {
  const result = parseCommand('select NET_GND');
  assert.equal(result.type, 'select');
  assert.equal(result.ref, 'NET_GND');
});

test('deselect (no args)', () => {
  const result = parseCommand('deselect');
  assert.equal(result.type, 'deselect');
});

test('deselect rejects extra args', () => {
  const result = parseCommand('deselect U1');
  assert.equal(result.type, 'error');
});

// --- zoom ---

console.log('\nzoom:');

test('zoom with percent', () => {
  const result = parseCommand('zoom 150%');
  assert.equal(result.type, 'zoom');
  assert.equal(result.mode, 'percent');
  assert.equal(result.percent, 150);
});

test('zoom 100%', () => {
  const result = parseCommand('zoom 100%');
  assert.equal(result.type, 'zoom');
  assert.equal(result.percent, 100);
});

test('zoom fit', () => {
  const result = parseCommand('zoom fit');
  assert.equal(result.type, 'zoom');
  assert.equal(result.mode, 'fit');
});

test('zoom rejects no argument', () => {
  const result = parseCommand('zoom');
  assert.equal(result.type, 'error');
});

test('zoom rejects invalid format', () => {
  const result = parseCommand('zoom big');
  assert.equal(result.type, 'error');
});

// --- pan ---

console.log('\npan:');

test('pan with positive delta', () => {
  const result = parseCommand('pan (10, 20)');
  assert.equal(result.type, 'pan');
  assert.equal(result.dx, 10);
  assert.equal(result.dy, 20);
});

test('pan with negative delta', () => {
  const result = parseCommand('pan (-5, -15.5)');
  assert.equal(result.type, 'pan');
  assert.equal(result.dx, -5);
  assert.equal(result.dy, -15.5);
});

// --- undo / redo ---

console.log('\nundo / redo:');

test('undo', () => {
  const result = parseCommand('undo');
  assert.equal(result.type, 'undo');
});

test('redo', () => {
  const result = parseCommand('redo');
  assert.equal(result.type, 'redo');
});

// --- new-page ---

console.log('\nnew-page:');

test('new-page with all params', () => {
  const result = parseCommand('new-page "Page 2" paper A3 landscape');
  assert.equal(result.type, 'new-page');
  assert.equal(result.name, 'Page 2');
  assert.equal(result.paper, 'A3');
  assert.equal(result.orientation, 'landscape');
});

test('new-page portrait', () => {
  const result = parseCommand('new-page "Schematic" paper A4 portrait');
  assert.equal(result.type, 'new-page');
  assert.equal(result.name, 'Schematic');
  assert.equal(result.paper, 'A4');
  assert.equal(result.orientation, 'portrait');
});

test('new-page rejects missing name', () => {
  const result = parseCommand('new-page paper A4 landscape');
  assert.equal(result.type, 'error');
});

// --- switch-page ---

console.log('\nswitch-page:');

test('switch-page', () => {
  const result = parseCommand('switch-page "Page 2"');
  assert.equal(result.type, 'switch-page');
  assert.equal(result.name, 'Page 2');
});

test('switch-page rejects missing quotes', () => {
  const result = parseCommand('switch-page Page 2');
  assert.equal(result.type, 'error');
});

// --- rename-page ---

console.log('\nrename-page:');

test('rename-page', () => {
  const result = parseCommand('rename-page "Old Name" "New Name"');
  assert.equal(result.type, 'rename-page');
  assert.equal(result.oldName, 'Old Name');
  assert.equal(result.newName, 'New Name');
});

test('rename-page rejects single arg', () => {
  const result = parseCommand('rename-page "Only One"');
  assert.equal(result.type, 'error');
});

// --- delete-page ---

console.log('\ndelete-page:');

test('delete-page', () => {
  const result = parseCommand('delete-page "Scratch"');
  assert.equal(result.type, 'delete-page');
  assert.equal(result.name, 'Scratch');
});

// --- set-config ---

console.log('\nset-config:');

test('set-config with numeric value', () => {
  const result = parseCommand('set-config grid.snap_mm 2.5');
  assert.equal(result.type, 'set-config');
  assert.equal(result.path, 'grid.snap_mm');
  assert.equal(result.value, 2.5);
});

test('set-config with boolean true', () => {
  const result = parseCommand('set-config export.monochrome true');
  assert.equal(result.type, 'set-config');
  assert.equal(result.path, 'export.monochrome');
  assert.equal(result.value, true);
});

test('set-config with boolean false', () => {
  const result = parseCommand('set-config title_block.show false');
  assert.equal(result.type, 'set-config');
  assert.equal(result.value, false);
});

test('set-config with string value', () => {
  const result = parseCommand('set-config paper.size A3');
  assert.equal(result.type, 'set-config');
  assert.equal(result.path, 'paper.size');
  assert.equal(result.value, 'A3');
});

test('set-config with quoted string value', () => {
  const result = parseCommand('set-config title_block.project "My Project"');
  assert.equal(result.type, 'set-config');
  assert.equal(result.value, 'My Project');
});

// --- error cases ---

console.log('\nerror cases:');

test('unknown command', () => {
  const result = parseCommand('explode U1');
  assert.equal(result.type, 'error');
  assert.ok(result.message.includes('Unknown command'));
  assert.ok(result.message.includes('explode'));
  assert.equal(result.input, 'explode U1');
});

test('empty string', () => {
  const result = parseCommand('');
  assert.equal(result.type, 'error');
  assert.ok(result.message.includes('Empty'));
});

test('whitespace only', () => {
  const result = parseCommand('   ');
  assert.equal(result.type, 'error');
});

test('non-string input', () => {
  const result = parseCommand(42);
  assert.equal(result.type, 'error');
});

test('malformed place (no ref)', () => {
  const result = parseCommand('place , digital.74HC04 at (10, 20) rotate 90');
  assert.equal(result.type, 'error');
});

// --- case insensitivity ---

console.log('\ncase insensitivity:');

test('PLACE keyword (uppercase)', () => {
  const result = parseCommand('PLACE U1, digital.74HC04 at (10, 20) rotate 90');
  assert.equal(result.type, 'place');
  assert.equal(result.ref, 'U1');
});

test('Move keyword (mixed case)', () => {
  const result = parseCommand('Move U1 to (30, 40)');
  assert.equal(result.type, 'move');
});

test('ZOOM FIT (all caps)', () => {
  const result = parseCommand('ZOOM FIT');
  assert.equal(result.type, 'zoom');
  assert.equal(result.mode, 'fit');
});

test('Undo mixed case', () => {
  const result = parseCommand('UNDO');
  assert.equal(result.type, 'undo');
});

test('AT keyword case insensitive in place', () => {
  const result = parseCommand('place U1, part AT (5, 5) ROTATE 90');
  assert.equal(result.type, 'place');
  assert.equal(result.x, 5);
  assert.equal(result.rotate, 90);
});

test('refs remain case-sensitive', () => {
  const r1 = parseCommand('select MyRef');
  const r2 = parseCommand('select myref');
  assert.equal(r1.ref, 'MyRef');
  assert.equal(r2.ref, 'myref');
});

// --- whitespace tolerance ---

console.log('\nwhitespace tolerance:');

test('extra spaces in move command', () => {
  const result = parseCommand('move   U1   to   (  30 ,  40  )');
  assert.equal(result.type, 'move');
  assert.equal(result.ref, 'U1');
  assert.equal(result.x, 30);
  assert.equal(result.y, 40);
});

test('leading and trailing whitespace', () => {
  const result = parseCommand('   undo   ');
  assert.equal(result.type, 'undo');
});

test('extra spaces in connect', () => {
  const result = parseCommand('connect  U1.1Y  ->  U2.1A');
  assert.equal(result.type, 'connect');
  assert.equal(result.from, 'U1.1Y');
  assert.equal(result.to, 'U2.1A');
});

test('extra spaces in coordinates', () => {
  const result = parseCommand('pan (  -10  ,  25.5  )');
  assert.equal(result.type, 'pan');
  assert.equal(result.dx, -10);
  assert.equal(result.dy, 25.5);
});

// --- Summary ---


// --- JSON format (structured commands for AI/tools/API) ---

console.log('\nJSON format (structured commands):');

test('JSON place command', () => {
  const r = parseCommand('{"command": "place", "ref": "U1", "part": "digital.74HC04", "x": 50, "y": 30, "rotation": 0}');
  assert.equal(r.type, 'place');
  assert.equal(r.ref, 'U1');
  assert.equal(r.part, 'digital.74HC04');
  assert.equal(r.x, 50);
  assert.equal(r.y, 30);
  assert.equal(r.rotation, 0);
});

test('JSON connect command', () => {
  const r = parseCommand('{"command": "connect", "from": "U1.1Y", "to": "U2.1A", "via": [{"x": 85, "y": 30}]}');
  assert.equal(r.type, 'connect');
  assert.equal(r.from, 'U1.1Y');
  assert.equal(r.to, 'U2.1A');
  assert.deepEqual(r.via, [{x: 85, y: 30}]);
});

test('JSON move command', () => {
  const r = parseCommand('{"command": "move", "ref": "U1", "x": 75.5, "y": -20}');
  assert.equal(r.type, 'move');
  assert.equal(r.ref, 'U1');
  assert.equal(r.x, 75.5);
  assert.equal(r.y, -20);
});

test('JSON zoom command', () => {
  const r = parseCommand('{"command": "zoom", "value": "fit"}');
  assert.equal(r.type, 'zoom');
  assert.equal(r.value, 'fit');
});

test('JSON new-page command', () => {
  const r = parseCommand('{"command": "new-page", "name": "Memory", "paper_size": "A3", "orientation": "landscape"}');
  assert.equal(r.type, 'new-page');
  assert.equal(r.name, 'Memory');
  assert.equal(r.paper_size, 'A3');
});

test('JSON undo command', () => {
  const r = parseCommand('{"command": "undo"}');
  assert.equal(r.type, 'undo');
});

test('JSON rejects missing command field', () => {
  const r = parseCommand('{"ref": "U1"}');
  assert.equal(r.type, 'error');
  assert.ok(r.message.includes('command'));
});

test('JSON rejects unknown command', () => {
  const r = parseCommand('{"command": "fly"}');
  assert.equal(r.type, 'error');
  assert.ok(r.message.includes('Unknown'));
});

test('JSON rejects invalid JSON', () => {
  const r = parseCommand('{not valid json}');
  assert.equal(r.type, 'error');
  assert.ok(r.message.includes('Invalid JSON'));
});

test('JSON rejects place without ref', () => {
  const r = parseCommand('{"command": "place", "part": "digital.74HC04"}');
  assert.equal(r.type, 'error');
  assert.ok(r.message.includes('ref'));
});

test('JSON and text produce same result for connect', () => {
  const text = parseCommand('connect U1.1Y -> U2.1A');
  const json = parseCommand('{"command": "connect", "from": "U1.1Y", "to": "U2.1A"}');
  assert.equal(text.type, json.type);
  assert.equal(text.from, json.from);
  assert.equal(text.to, json.to);
});

console.log(`\n━━━ Results: ${passed} passed, ${failed} failed ━━━\n`);

if (failed > 0) {
  process.exit(1);
}
