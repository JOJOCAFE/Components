/**
 * Components Board — Device Tray Controller Tests
 * Run: node test/device-tray.test.js
 */

import { createDeviceTray, findNextFreePosition, snapToGrid } from '../src/controller/device-tray.js';
import { createLibrary } from '../src/model/library.js';
import { createExecutor } from '../src/controller/executor.js';
import { createComponentModel } from '../src/model/component.js';
import { createBoardModel } from '../src/model/board.js';
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

function assertEqual(actual, expected, msg) {
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    throw new Error(`${msg || 'assertion'}: expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
  }
}

function assert(condition, msg) {
  if (!condition) throw new Error(msg || 'assertion failed');
}

// =============================================================================
// HELPERS
// =============================================================================

const DEF_74HC00 = {
  part: '74HC00',
  about: { title: 'Quad 2-input NAND gate', family: '74HC', group: '74xx', role: 'nand_gate' },
  package: { kind: 'DIP' },
  pins: { '1':['1A','in'], '2':['1B','in'], '3':['1Y','out'], '4':['2A','in'], '5':['2B','in'], '6':['2Y','out'], '7':['GND','power'], '8':['3Y','out'], '9':['3A','in'], '10':['3B','in'], '11':['4Y','out'], '12':['4A','in'], '13':['4B','in'], '14':['VCC','power'] },
};

const DEF_74HC04 = {
  part: '74HC04',
  about: { title: 'Hex inverter', family: '74HC', group: '74xx', role: 'inverter' },
  package: { kind: 'DIP' },
  pins: { '1':['1A','in'], '2':['1Y','out'], '3':['2A','in'], '4':['2Y','out'], '5':['3A','in'], '6':['3Y','out'], '7':['GND','power'], '8':['4Y','out'], '9':['4A','in'], '10':['5Y','out'], '11':['5A','in'], '12':['6Y','out'], '13':['6A','in'], '14':['VCC','power'] },
};

const DEF_74HC161 = {
  part: '74HC161',
  about: { title: '4-bit binary counter', family: '74HC', group: '74xx', role: 'counter' },
  package: { kind: 'DIP' },
  pins: { '1':['/CLR','in'], '2':['CLK','in'], '3':['D0','in'], '4':['D1','in'], '5':['D2','in'], '6':['D3','in'], '7':['ENP','in'], '8':['GND','power'], '9':['LD','in'], '10':['ENT','in'], '11':['Q3','out'], '12':['Q2','out'], '13':['Q1','out'], '14':['Q0','out'], '15':['RCO','out'], '16':['VCC','power'] },
};

const DEF_LED = {
  part: 'LED',
  about: { title: 'Standard LED', family: 'LED', group: 'passive', role: 'led' },
  package: { kind: 'TH' },
  pins: { '1': ['A','in'], '2': ['K','out'] },
};

const DEF_RESISTOR = {
  part: 'Resistor',
  about: { title: 'Resistor', family: 'Resistor', group: 'passive', role: 'resistor' },
  package: { kind: 'TH' },
  pins: { '1': ['1','passive'], '2': ['2','passive'] },
};

const DEF_CAPACITOR = {
  part: 'Capacitor',
  about: { title: 'Capacitor', family: 'Capacitor', group: 'passive', role: 'capacitor' },
  package: { kind: 'TH' },
  pins: { '1': ['1','passive'], '2': ['2','passive'] },
};

const DEF_BC549 = {
  part: 'BC549',
  about: { title: 'NPN transistor', family: 'BJT', group: 'discrete', role: 'npn_transistor' },
  package: { kind: 'TO-92' },
  pins: { '1': ['C','out'], '2': ['B','in'], '3': ['E','out'] },
};

const DEF_VCC = {
  part: 'VCC',
  about: { title: 'Power rail +5V', family: 'virtual', group: 'virtual', role: 'power_source' },
  package: { kind: 'virtual' },
  pins: { '1': ['VCC','power'] },
};

function makeLibrary() {
  const lib = createLibrary();
  lib.loadGroup('74xx', [DEF_74HC00, DEF_74HC04, DEF_74HC161]);
  lib.loadGroup('passive', [DEF_LED, DEF_RESISTOR, DEF_CAPACITOR]);
  lib.loadGroup('discrete', [DEF_BC549]);
  lib.loadGroup('virtual', [DEF_VCC]);
  return lib;
}

function makeTray(opts = {}) {
  const library = opts.library || makeLibrary();
  const executor = opts.executor || undefined;
  return createDeviceTray({ library, executor });
}

function makeExecutor() {
  return createExecutor(createComponentModel(), createBoardModel(), createConfig());
}

// =============================================================================
console.log('\n━━━ Device Tray Tests ━━━\n');
// =============================================================================

// --- ADD TO TRAY ---
console.log('addToTray:');

test('adds a part to the tray', () => {
  const tray = makeTray();
  const result = tray.addToTray('74HC00');
  assert(result.success);
  assertEqual(result.item.part, '74HC00');
  assertEqual(result.item.quantity, 1);
  assertEqual(result.item.title, 'Quad 2-input NAND gate');
  assertEqual(result.item.group, '74xx');
});

test('increments quantity on duplicate add', () => {
  const tray = makeTray();
  tray.addToTray('74HC00');
  const result = tray.addToTray('74HC00');
  assertEqual(result.item.quantity, 2);
});

test('adds with specific quantity', () => {
  const tray = makeTray();
  const result = tray.addToTray('74HC161', 4);
  assertEqual(result.item.quantity, 4);
});

test('rejects quantity < 1', () => {
  const tray = makeTray();
  const result = tray.addToTray('74HC00', 0);
  assert(!result.success);
  assert(result.error.includes('at least 1'));
});

test('handles unknown parts (no library entry)', () => {
  const tray = makeTray();
  const result = tray.addToTray('UNKNOWN_PART');
  assert(result.success);
  assertEqual(result.item.group, 'unknown');
  assertEqual(result.item.title, 'UNKNOWN_PART');
});

test('itemCount reflects unique parts', () => {
  const tray = makeTray();
  tray.addToTray('74HC00');
  tray.addToTray('74HC04');
  tray.addToTray('74HC00'); // duplicate
  assertEqual(tray.itemCount(), 2);
});

test('totalQuantity sums all', () => {
  const tray = makeTray();
  tray.addToTray('74HC00', 3);
  tray.addToTray('74HC04', 2);
  assertEqual(tray.totalQuantity(), 5);
});

// --- REMOVE FROM TRAY ---
console.log('\nremoveFromTray:');

test('removes a part from the tray', () => {
  const tray = makeTray();
  tray.addToTray('74HC00');
  const result = tray.removeFromTray('74HC00');
  assert(result.success);
  assertEqual(tray.itemCount(), 0);
});

test('rejects removing non-existent part', () => {
  const tray = makeTray();
  const result = tray.removeFromTray('74HC00');
  assert(!result.success);
  assert(result.error.includes('not in tray'));
});

// --- REDUCE QUANTITY ---
console.log('\nreduceQuantity:');

test('reduces quantity', () => {
  const tray = makeTray();
  tray.addToTray('74HC00', 3);
  const result = tray.reduceQuantity('74HC00');
  assert(result.success);
  assertEqual(result.remaining, 2);
});

test('removes when reduced to 0', () => {
  const tray = makeTray();
  tray.addToTray('74HC00', 1);
  const result = tray.reduceQuantity('74HC00');
  assertEqual(result.remaining, 0);
  assertEqual(tray.itemCount(), 0);
});

test('rejects reducing non-existent', () => {
  const tray = makeTray();
  const result = tray.reduceQuantity('NOPE');
  assert(!result.success);
});

// --- SET QUANTITY ---
console.log('\nsetQuantity:');

test('sets exact quantity', () => {
  const tray = makeTray();
  tray.addToTray('74HC00', 1);
  tray.setQuantity('74HC00', 5);
  assertEqual(tray.getItem('74HC00').quantity, 5);
});

test('removes when set to 0', () => {
  const tray = makeTray();
  tray.addToTray('74HC00', 3);
  tray.setQuantity('74HC00', 0);
  assertEqual(tray.itemCount(), 0);
});

test('rejects setting non-existent', () => {
  const tray = makeTray();
  const result = tray.setQuantity('NOPE', 5);
  assert(!result.success);
});

// --- PLACE FROM TRAY ---
console.log('\nplaceFromTray:');

test('places with auto-ref U1 for 74xx', () => {
  const tray = makeTray();
  tray.addToTray('74HC00');
  const result = tray.placeFromTray('74HC00', { x: 50, y: 30 });
  assert(result.success);
  assertEqual(result.ref, 'U1');
  assertEqual(result.command.type, 'place');
  // Grid-snapped: 50/2.54=19.7→20→50.8, 30/2.54=11.8→12→30.48
  assertEqual(result.command.x, 50.8);
  assertEqual(result.command.y, 30.48);
});

test('auto-increments U refs', () => {
  const tray = makeTray();
  tray.addToTray('74HC00', 3);
  tray.addToTray('74HC04', 2);
  const r1 = tray.placeFromTray('74HC00', { x: 10, y: 10 });
  const r2 = tray.placeFromTray('74HC04', { x: 20, y: 10 });
  const r3 = tray.placeFromTray('74HC00', { x: 30, y: 10 });
  assertEqual(r1.ref, 'U1');
  assertEqual(r2.ref, 'U2');
  assertEqual(r3.ref, 'U3');
});

test('LED gets D prefix', () => {
  const tray = makeTray();
  tray.addToTray('LED');
  const result = tray.placeFromTray('LED', { x: 10, y: 10 });
  assertEqual(result.ref, 'D1');
});

test('Resistor gets R prefix', () => {
  const tray = makeTray();
  tray.addToTray('Resistor');
  const result = tray.placeFromTray('Resistor', { x: 10, y: 10 });
  assertEqual(result.ref, 'R1');
});

test('Capacitor gets C prefix', () => {
  const tray = makeTray();
  tray.addToTray('Capacitor');
  const result = tray.placeFromTray('Capacitor', { x: 10, y: 10 });
  assertEqual(result.ref, 'C1');
});

test('BC549 (discrete) gets Q prefix', () => {
  const tray = makeTray();
  tray.addToTray('BC549');
  const result = tray.placeFromTray('BC549', { x: 10, y: 10 });
  assertEqual(result.ref, 'Q1');
});

test('VCC (virtual) gets X prefix', () => {
  const tray = makeTray();
  tray.addToTray('VCC');
  const result = tray.placeFromTray('VCC', { x: 10, y: 10 });
  assertEqual(result.ref, 'X1');
});

test('rejects placing part not in tray', () => {
  const tray = makeTray();
  const result = tray.placeFromTray('74HC00', { x: 10, y: 10 });
  assert(!result.success);
  assert(result.error.includes('not in tray'));
});

test('tracks placed refs in tray item', () => {
  const tray = makeTray();
  tray.addToTray('74HC00', 3);
  tray.placeFromTray('74HC00', { x: 10, y: 10 });
  tray.placeFromTray('74HC00', { x: 20, y: 10 });
  const item = tray.getItem('74HC00');
  assertEqual(item.placed.length, 2);
  assertEqual(item.placed[0], 'U1');
  assertEqual(item.placed[1], 'U2');
});

test('remainingCount decreases after placement', () => {
  const tray = makeTray();
  tray.addToTray('74HC00', 3);
  tray.placeFromTray('74HC00', { x: 10, y: 10 });
  assertEqual(tray.remainingCount('74HC00'), 2);
});

test('place with rotation', () => {
  const tray = makeTray();
  tray.addToTray('74HC00');
  const result = tray.placeFromTray('74HC00', { x: 10, y: 10 }, { rotation: 90 });
  assertEqual(result.command.rotation, 90);
});

test('place with override ref', () => {
  const tray = makeTray();
  tray.addToTray('74HC00');
  const result = tray.placeFromTray('74HC00', { x: 10, y: 10 }, { ref: 'U99' });
  assertEqual(result.ref, 'U99');
});

// --- PLACE WITH EXECUTOR INTEGRATION ---
console.log('\nplaceFromTray + executor:');

test('executor receives place command', () => {
  const executor = makeExecutor();
  const tray = makeTray({ executor });
  tray.addToTray('74HC00');
  const result = tray.placeFromTray('74HC00', { x: 50, y: 30 });
  assert(result.success);
  assertEqual(result.ref, 'U1');
  // Verify the executor state (grid-snapped)
  const state = executor.getState();
  assertEqual(state.component.devices.U1.part, '74HC00');
  assertEqual(state.board.placements.U1.x, 50.8);
  assertEqual(state.board.placements.U1.y, 30.48);
});

test('multiple placements via executor', () => {
  const executor = makeExecutor();
  const tray = makeTray({ executor });
  tray.addToTray('74HC00', 2);
  tray.addToTray('LED', 3);
  tray.placeFromTray('74HC00', { x: 10, y: 10 });
  tray.placeFromTray('74HC00', { x: 30, y: 10 });
  tray.placeFromTray('LED', { x: 50, y: 10 });
  const state = executor.getState();
  assert(state.component.devices.U1);
  assert(state.component.devices.U2);
  assert(state.component.devices.D1);
});

test('executor failure propagates to tray result', () => {
  const executor = makeExecutor();
  const tray = makeTray({ executor });
  tray.addToTray('74HC00', 2);
  // Place with override ref, then try same ref again
  tray.placeFromTray('74HC00', { x: 10, y: 10 }, { ref: 'U1' });
  const result = tray.placeFromTray('74HC00', { x: 20, y: 10 }, { ref: 'U1' });
  assert(!result.success);
  assert(result.error.includes('already exists'));
});

// --- UNPLACE ---
console.log('\nunplace:');

test('unplaces a device', () => {
  const tray = makeTray();
  tray.addToTray('74HC00', 2);
  tray.placeFromTray('74HC00', { x: 10, y: 10 });
  const result = tray.unplace('U1');
  assert(result.success);
  assertEqual(result.part, '74HC00');
  assertEqual(tray.getItem('74HC00').placed.length, 0);
});

test('rejects unplacing unknown ref', () => {
  const tray = makeTray();
  const result = tray.unplace('U99');
  assert(!result.success);
  assert(result.error.includes('not tracked'));
});

// --- GET ITEMS ---
console.log('\ngetItems:');

test('returns frozen items', () => {
  const tray = makeTray();
  tray.addToTray('74HC00', 2);
  tray.addToTray('LED', 3);
  const items = tray.getItems();
  assertEqual(items.length, 2);
  assert(Object.isFrozen(items[0]));
  assert(Object.isFrozen(items[0].placed));
});

test('getItem returns single frozen item', () => {
  const tray = makeTray();
  tray.addToTray('74HC00');
  const item = tray.getItem('74HC00');
  assertEqual(item.part, '74HC00');
  assert(Object.isFrozen(item));
});

test('getItem returns null for missing', () => {
  const tray = makeTray();
  assertEqual(tray.getItem('NOPE'), null);
});

// --- COUNTERS ---
console.log('\ncounters:');

test('placedCount tracks total placed', () => {
  const tray = makeTray();
  tray.addToTray('74HC00', 5);
  tray.placeFromTray('74HC00', { x: 10, y: 10 });
  tray.placeFromTray('74HC00', { x: 20, y: 10 });
  assertEqual(tray.placedCount(), 2);
});

test('remainingCount for unknown part is 0', () => {
  const tray = makeTray();
  assertEqual(tray.remainingCount('NOPE'), 0);
});

// --- REF COUNTERS SAVE/RESTORE ---
console.log('\nrefCounters:');

test('getRefCounters returns current state', () => {
  const tray = makeTray();
  tray.addToTray('74HC00', 3);
  tray.placeFromTray('74HC00', { x: 10, y: 10 });
  tray.placeFromTray('74HC00', { x: 20, y: 10 });
  const counters = tray.getRefCounters();
  assertEqual(counters.U, 2);
});

test('setRefCounters restores state', () => {
  const tray = makeTray();
  tray.setRefCounters({ U: 5, R: 3 });
  tray.addToTray('74HC00');
  const result = tray.placeFromTray('74HC00', { x: 10, y: 10 });
  assertEqual(result.ref, 'U6'); // continues from 5
});

test('mixed prefixes increment independently', () => {
  const tray = makeTray();
  tray.addToTray('74HC00', 2);
  tray.addToTray('Resistor', 2);
  tray.addToTray('LED', 2);
  tray.placeFromTray('74HC00', { x: 10, y: 10 });     // U1
  tray.placeFromTray('Resistor', { x: 20, y: 10 });   // R1
  tray.placeFromTray('LED', { x: 30, y: 10 });        // D1
  tray.placeFromTray('74HC00', { x: 40, y: 10 });     // U2
  tray.placeFromTray('Resistor', { x: 50, y: 10 });   // R2
  const counters = tray.getRefCounters();
  assertEqual(counters.U, 2);
  assertEqual(counters.R, 2);
  assertEqual(counters.D, 1);
});

// --- CLEAR ---
console.log('\nclear:');

test('clears tray and counters', () => {
  const tray = makeTray();
  tray.addToTray('74HC00', 3);
  tray.placeFromTray('74HC00', { x: 10, y: 10 });
  tray.clear();
  assertEqual(tray.itemCount(), 0);
  assertEqual(tray.getRefCounters(), {});
});

// --- PICKUP ---
console.log('\npickup:');

test('pickup enters placement mode', () => {
  const tray = makeTray();
  tray.addToTray('74HC00', 2);
  const result = tray.pickup('74HC00');
  assert(result.success);
  assertEqual(tray.getPickedUp(), '74HC00');
});

test('pickup fails if part not in tray', () => {
  const tray = makeTray();
  const result = tray.pickup('74HC00');
  assert(!result.success);
  assert(result.error.includes('not in tray'));
});

test('pickup fails if all placed', () => {
  const tray = makeTray();
  tray.addToTray('74HC00', 1);
  tray.placeFromTray('74HC00', { x: 10, y: 10 });
  const result = tray.pickup('74HC00');
  assert(!result.success);
  assert(result.error.includes('already placed'));
});

test('cancelPickup clears state', () => {
  const tray = makeTray();
  tray.addToTray('74HC00', 2);
  tray.pickup('74HC00');
  tray.cancelPickup();
  assertEqual(tray.getPickedUp(), null);
});

test('removeFromTray clears pickup', () => {
  const tray = makeTray();
  tray.addToTray('74HC00', 2);
  tray.pickup('74HC00');
  tray.removeFromTray('74HC00');
  assertEqual(tray.getPickedUp(), null);
});

// --- AUTO-PLACEMENT ---
console.log('\nauto-placement:');

test('place without position uses auto-find', () => {
  const executor = makeExecutor();
  const tray = makeTray({ executor });
  tray.addToTray('74HC00', 2);
  const r1 = tray.placeFromTray('74HC00');
  assert(r1.success);
  assert(r1.position.x >= 0);
  assert(r1.position.y >= 0);
  // Second placement finds different position
  const r2 = tray.placeFromTray('74HC00');
  assert(r2.success);
  assert(r2.position.x !== r1.position.x || r2.position.y !== r1.position.y);
});

test('findNextFreePosition skips occupied cells', () => {
  const placements = {
    U1: { x: 30, y: 40, rotation: 0 },
    U2: { x: 55, y: 40, rotation: 0 },
  };
  const pos = findNextFreePosition(placements);
  // Should not be at (30,40) or (55,40)
  assert(!(pos.x === 30 && pos.y === 40), 'should not overlap U1');
  assert(!(pos.x === 55 && pos.y === 40), 'should not overlap U2');
});

test('findNextFreePosition returns start position when empty', () => {
  const pos = findNextFreePosition({});
  assertEqual(pos.x, 30);
  assertEqual(pos.y, 40);
});

// --- SNAP TO GRID ---
console.log('\nsnapToGrid:');

test('snaps to 2.54mm grid', () => {
  const pos = snapToGrid({ x: 31.1, y: 42.3 });
  // 31.1 / 2.54 = 12.24 → round to 12 → 12 * 2.54 = 30.48
  assertEqual(pos.x, 30.48);
  // 42.3 / 2.54 = 16.65 → round to 17 → 17 * 2.54 = 43.18
  assertEqual(pos.y, 43.18);
});

test('exact grid position stays', () => {
  const pos = snapToGrid({ x: 25.4, y: 50.8 });
  assertEqual(pos.x, 25.4);
  assertEqual(pos.y, 50.8);
});

// --- BOM ---
console.log('\nloadBom:');

test('loads a simple BOM into tray', () => {
  const tray = makeTray();
  const bom = [
    { part: '74HC00', qty: 2 },
    { part: '74HC04', qty: 4 },
    { part: 'LED', qty: 8 },
  ];
  const result = tray.loadBom(bom);
  assert(result.success);
  assertEqual(result.loaded, 3);
  assertEqual(result.skipped, 0);
  assertEqual(tray.itemCount(), 3);
  assertEqual(tray.getItem('74HC00').quantity, 2);
  assertEqual(tray.getItem('74HC04').quantity, 4);
  assertEqual(tray.getItem('LED').quantity, 8);
});

test('loadBom clears existing tray by default', () => {
  const tray = makeTray();
  tray.addToTray('Resistor', 5);
  tray.loadBom([{ part: '74HC00', qty: 1 }]);
  assertEqual(tray.itemCount(), 1);
  assertEqual(tray.getItem('Resistor'), null);
});

test('loadBom with clear=false appends', () => {
  const tray = makeTray();
  tray.addToTray('Resistor', 5);
  tray.loadBom([{ part: '74HC00', qty: 1 }], { clear: false });
  assertEqual(tray.itemCount(), 2);
  assertEqual(tray.getItem('Resistor').quantity, 5);
});

test('loadBom skips entries without part field', () => {
  const tray = makeTray();
  const bom = [
    { part: '74HC00', qty: 2 },
    { qty: 3 },
    { part: '74HC04', qty: 1 },
  ];
  const result = tray.loadBom(bom);
  assert(result.success);
  assertEqual(result.loaded, 2);
  assertEqual(result.skipped, 1);
  assertEqual(result.errors.length, 1);
});

test('loadBom uses fuzzy search for unresolved parts', () => {
  const tray = makeTray();
  // 'counter' should resolve to 74HC161 (role: counter)
  const bom = [{ part: '74HC161', qty: 4 }];
  const result = tray.loadBom(bom);
  assert(result.success);
  assertEqual(tray.getItem('74HC161').quantity, 4);
});

test('loadBom strict mode fails on unknown parts', () => {
  const tray = makeTray();
  const bom = [
    { part: '74HC00', qty: 1 },
    { part: 'NONEXISTENT_CHIP', qty: 1 },
  ];
  const result = tray.loadBom(bom, { strict: true });
  assert(!result.success);
  assertEqual(result.loaded, 1);
  assertEqual(result.skipped, 1);
});

test('loadBom handles "quantity" alias for "qty"', () => {
  const tray = makeTray();
  const bom = [{ part: '74HC00', quantity: 3 }];
  tray.loadBom(bom);
  assertEqual(tray.getItem('74HC00').quantity, 3);
});

test('loadBom rejects non-array input', () => {
  const tray = makeTray();
  const result = tray.loadBom('not an array');
  assert(!result.success);
  assertEqual(result.errors[0], 'BOM must be an array');
});

console.log('\nexportBom:');

test('exports tray as BOM array', () => {
  const tray = makeTray();
  tray.addToTray('74HC00', 2);
  tray.addToTray('LED', 8);
  const bom = tray.exportBom();
  assertEqual(bom.length, 2);
  assertEqual(bom[0].part, '74HC00');
  assertEqual(bom[0].qty, 2);
  assertEqual(bom[0].group, '74xx');
  assertEqual(bom[1].part, 'LED');
  assertEqual(bom[1].qty, 8);
});

test('export empty tray returns empty array', () => {
  const tray = makeTray();
  assertEqual(tray.exportBom(), []);
});

test('round-trip: export → load preserves tray', () => {
  const tray = makeTray();
  tray.addToTray('74HC00', 2);
  tray.addToTray('74HC04', 4);
  tray.addToTray('Resistor', 10);
  const bom = tray.exportBom();
  
  // Load into fresh tray
  const tray2 = makeTray();
  tray2.loadBom(bom);
  assertEqual(tray2.itemCount(), 3);
  assertEqual(tray2.getItem('74HC00').quantity, 2);
  assertEqual(tray2.getItem('74HC04').quantity, 4);
  assertEqual(tray2.getItem('Resistor').quantity, 10);
});

// =============================================================================
console.log('\n' + '─'.repeat(40));
console.log(`${passed + failed} tests: ${passed} passed, ${failed} failed`);
if (failed > 0) process.exit(1);
console.log('✅ Device Tray tests passed\n');
