/**
 * Components Board — Library Model Tests
 * Run: node test/library.test.js
 */

import { createLibrary, createCatalogEntry, GROUPS } from '../src/model/library.js';

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
// SAMPLE DEFINITIONS (mirrors lib/standard structure)
// =============================================================================

const DEF_74HC00 = {
  part: '74HC00',
  about: { title: 'Quad 2-input NAND gate', family: '74HC', group: '74xx', role: 'nand_gate', manufacturer: 'Texas Instruments' },
  package: { kind: 'DIP' },
  pins: { '1': ['1A','in'], '2': ['1B','in'], '3': ['1Y','out'], '4': ['2A','in'], '5': ['2B','in'], '6': ['2Y','out'], '7': ['GND','power'], '8': ['3Y','out'], '9': ['3A','in'], '10': ['3B','in'], '11': ['4Y','out'], '12': ['4A','in'], '13': ['4B','in'], '14': ['VCC','power'] },
};

const DEF_74HC04 = {
  part: '74HC04',
  about: { title: 'Hex inverter', family: '74HC', group: '74xx', role: 'inverter', manufacturer: 'Texas Instruments' },
  package: { kind: 'DIP' },
  pins: { '1': ['1A','in'], '2': ['1Y','out'], '3': ['2A','in'], '4': ['2Y','out'], '5': ['3A','in'], '6': ['3Y','out'], '7': ['GND','power'], '8': ['4Y','out'], '9': ['4A','in'], '10': ['5Y','out'], '11': ['5A','in'], '12': ['6Y','out'], '13': ['6A','in'], '14': ['VCC','power'] },
};

const DEF_74HC161 = {
  part: '74HC161',
  about: { title: '4-bit binary counter', family: '74HC', group: '74xx', role: 'counter', manufacturer: 'Texas Instruments' },
  package: { kind: 'DIP' },
  pins: { '1': ['/CLR','in'], '2': ['CLK','in'], '3': ['D0','in'], '4': ['D1','in'], '5': ['D2','in'], '6': ['D3','in'], '7': ['ENP','in'], '8': ['GND','power'], '9': ['LD','in'], '10': ['ENT','in'], '11': ['Q3','out'], '12': ['Q2','out'], '13': ['Q1','out'], '14': ['Q0','out'], '15': ['RCO','out'], '16': ['VCC','power'] },
};

const DEF_74HC574 = {
  part: '74HC574',
  about: { title: 'Octal D flip-flop (3-state)', family: '74HC', group: '74xx', role: 'register', manufacturer: 'Texas Instruments' },
  package: { kind: 'DIP' },
  pins: { '1': ['/OE','in'], '2': ['D0','in'], '3': ['D1','in'], '4': ['D2','in'], '5': ['D3','in'], '6': ['D4','in'], '7': ['D5','in'], '8': ['D6','in'], '9': ['D7','in'], '10': ['GND','power'], '11': ['CLK','in'], '12': ['Q7','out'], '13': ['Q6','out'], '14': ['Q5','out'], '15': ['Q4','out'], '16': ['Q3','out'], '17': ['Q2','out'], '18': ['Q1','out'], '19': ['Q0','out'], '20': ['VCC','power'] },
};

const DEF_AT28C256 = {
  part: 'AT28C256',
  about: { title: '32KB parallel EEPROM', family: 'AT28', group: 'memory', role: 'eeprom', manufacturer: 'Microchip' },
  package: { kind: 'DIP' },
  pins: { '1':['A14','in'], '2':['A12','in'], '3':['A7','in'], '4':['A6','in'], '5':['A5','in'], '6':['A4','in'], '7':['A3','in'], '8':['A2','in'], '9':['A1','in'], '10':['A0','in'], '11':['D0','io'], '12':['D1','io'], '13':['D2','io'], '14':['GND','power'], '15':['D3','io'], '16':['D4','io'], '17':['D5','io'], '18':['D6','io'], '19':['D7','io'], '20':['/CE','in'], '21':['A10','in'], '22':['/OE','in'], '23':['A11','in'], '24':['A9','in'], '25':['A8','in'], '26':['A13','in'], '27':['/WE','in'], '28':['VCC','power'] },
};

const DEF_LED = {
  part: 'LED',
  about: { title: 'Standard LED', family: 'LED', group: 'passive', role: 'led', manufacturer: 'Generic' },
  package: { kind: 'TH' },
  pins: { '1': ['A','in'], '2': ['K','out'] },
};

const DEF_RESISTOR = {
  part: 'Resistor',
  about: { title: 'Resistor', family: 'Resistor', group: 'passive', role: 'resistor', manufacturer: 'Generic' },
  package: { kind: 'TH' },
  pins: { '1': ['1','passive'], '2': ['2','passive'] },
};

const DEF_NE555 = {
  part: 'NE555',
  about: { title: 'Timer IC', family: 'NE555', group: 'support', role: 'timer', manufacturer: 'Texas Instruments' },
  package: { kind: 'DIP' },
  pins: { '1':['GND','power'], '2':['TRIG','in'], '3':['OUT','out'], '4':['/RST','in'], '5':['CTRL','in'], '6':['THR','in'], '7':['DIS','out'], '8':['VCC','power'] },
};

const DEF_VCC = {
  part: 'VCC',
  about: { title: 'Power rail +5V', family: 'virtual', group: 'virtual', role: 'power_source', manufacturer: '' },
  package: { kind: 'virtual' },
  pins: { '1': ['VCC','power'] },
};

const DEF_BC549 = {
  part: 'BC549',
  about: { title: 'NPN transistor', family: 'BJT', group: 'discrete', role: 'npn_transistor', manufacturer: 'ON Semiconductor' },
  package: { kind: 'TO-92' },
  pins: { '1': ['C','out'], '2': ['B','in'], '3': ['E','out'] },
};

// =============================================================================
console.log('\n━━━ Library Model Tests ━━━\n');
// =============================================================================

// --- GROUPS constant ---
console.log('GROUPS:');
test('GROUPS has 6 entries', () => {
  assertEqual(GROUPS.length, 6);
});
test('GROUPS includes 74xx', () => {
  assert(GROUPS.some(g => g.id === '74xx'));
});

// --- createCatalogEntry ---
console.log('\ncreateEntry:');
test('creates entry from 74HC00 definition', () => {
  const entry = createCatalogEntry(DEF_74HC00, '74xx');
  assertEqual(entry.part, '74HC00');
  assertEqual(entry.title, 'Quad 2-input NAND gate');
  assertEqual(entry.group, '74xx');
  assertEqual(entry.pinCount, 14);
  assertEqual(entry.package, 'DIP');
  assertEqual(entry.role, 'nand_gate');
  assertEqual(entry.family, '74HC');
});

test('entry is frozen', () => {
  const entry = createCatalogEntry(DEF_74HC00, '74xx');
  assert(Object.isFrozen(entry), 'entry should be frozen');
});

test('entry has _keywords for search', () => {
  const entry = createCatalogEntry(DEF_74HC00, '74xx');
  assert(entry._keywords.includes('74hc00'), 'keywords include part');
  assert(entry._keywords.includes('nand'), 'keywords include role');
});

test('handles missing fields gracefully', () => {
  const entry = createCatalogEntry({ part: 'TEST' }, 'virtual');
  assertEqual(entry.part, 'TEST');
  assertEqual(entry.title, 'TEST');
  assertEqual(entry.pinCount, 0);
  assertEqual(entry.group, 'virtual');
});

// --- createLibrary ---
console.log('\ncreateLibrary:');
test('creates empty library', () => {
  const lib = createLibrary();
  assertEqual(lib.count(), 0);
});

// --- loadGroup ---
console.log('\nloadGroup:');
test('loads a group of definitions', () => {
  const lib = createLibrary();
  const count = lib.loadGroup('74xx', [DEF_74HC00, DEF_74HC04, DEF_74HC161, DEF_74HC574]);
  assertEqual(count, 4);
  assertEqual(lib.count(), 4);
});

test('skips definitions without part field', () => {
  const lib = createLibrary();
  const count = lib.loadGroup('74xx', [DEF_74HC00, { about: { title: 'no part field' } }]);
  assertEqual(count, 1);
});

test('can load multiple groups', () => {
  const lib = createLibrary();
  lib.loadGroup('74xx', [DEF_74HC00, DEF_74HC04]);
  lib.loadGroup('memory', [DEF_AT28C256]);
  lib.loadGroup('passive', [DEF_LED, DEF_RESISTOR]);
  assertEqual(lib.count(), 5);
});

// --- loadOne ---
console.log('\nloadOne:');
test('loads a single definition', () => {
  const lib = createLibrary();
  const entry = lib.loadOne('74xx', DEF_74HC00);
  assertEqual(entry.part, '74HC00');
  assertEqual(lib.count(), 1);
});

// --- getByPart ---
console.log('\ngetByPart:');
test('retrieves loaded part', () => {
  const lib = createLibrary();
  lib.loadGroup('74xx', [DEF_74HC00, DEF_74HC04]);
  const entry = lib.getByPart('74HC04');
  assertEqual(entry.part, '74HC04');
  assertEqual(entry.title, 'Hex inverter');
});

test('returns null for unknown part', () => {
  const lib = createLibrary();
  assertEqual(lib.getByPart('FAKE'), null);
});

// --- listGroups ---
console.log('\nlistGroups:');
test('lists all groups with counts', () => {
  const lib = createLibrary();
  lib.loadGroup('74xx', [DEF_74HC00, DEF_74HC04]);
  lib.loadGroup('memory', [DEF_AT28C256]);
  const groups = lib.listGroups();
  const g74 = groups.find(g => g.id === '74xx');
  assertEqual(g74.count, 2);
  const gMem = groups.find(g => g.id === 'memory');
  assertEqual(gMem.count, 1);
  const gVirt = groups.find(g => g.id === 'virtual');
  assertEqual(gVirt.count, 0);
});

// --- listParts ---
console.log('\nlistParts:');
test('lists parts in a group sorted by part name', () => {
  const lib = createLibrary();
  lib.loadGroup('74xx', [DEF_74HC574, DEF_74HC00, DEF_74HC161, DEF_74HC04]);
  const parts = lib.listParts('74xx');
  assertEqual(parts.length, 4);
  assertEqual(parts[0].part, '74HC00');
  assertEqual(parts[1].part, '74HC04');
  assertEqual(parts[2].part, '74HC161');
  assertEqual(parts[3].part, '74HC574');
});

test('sorts by pinCount', () => {
  const lib = createLibrary();
  lib.loadGroup('74xx', [DEF_74HC574, DEF_74HC00]);
  const parts = lib.listParts('74xx', { sortBy: 'pinCount' });
  assertEqual(parts[0].part, '74HC00'); // 14 pins
  assertEqual(parts[1].part, '74HC574'); // 20 pins
});

test('returns empty for unknown group', () => {
  const lib = createLibrary();
  assertEqual(lib.listParts('nonexistent'), []);
});

// --- search ---
console.log('\nsearch:');
test('finds by exact part name', () => {
  const lib = createLibrary();
  lib.loadGroup('74xx', [DEF_74HC00, DEF_74HC04, DEF_74HC161]);
  const results = lib.search('74HC161');
  assertEqual(results.length, 1);
  assertEqual(results[0].part, '74HC161');
});

test('finds by partial part name', () => {
  const lib = createLibrary();
  lib.loadGroup('74xx', [DEF_74HC00, DEF_74HC04, DEF_74HC161]);
  const results = lib.search('HC0');
  assertEqual(results.length, 2);
});

test('finds by title keyword', () => {
  const lib = createLibrary();
  lib.loadGroup('74xx', [DEF_74HC00, DEF_74HC04, DEF_74HC161]);
  const results = lib.search('counter');
  assertEqual(results.length, 1);
  assertEqual(results[0].part, '74HC161');
});

test('finds by role', () => {
  const lib = createLibrary();
  lib.loadGroup('74xx', [DEF_74HC00, DEF_74HC04, DEF_74HC161]);
  const results = lib.search('inverter');
  assertEqual(results.length, 1);
  assertEqual(results[0].part, '74HC04');
});

test('multi-token search (AND)', () => {
  const lib = createLibrary();
  lib.loadGroup('74xx', [DEF_74HC00, DEF_74HC04, DEF_74HC161, DEF_74HC574]);
  const results = lib.search('74hc register');
  assertEqual(results.length, 1);
  assertEqual(results[0].part, '74HC574');
});

test('case insensitive', () => {
  const lib = createLibrary();
  lib.loadGroup('74xx', [DEF_74HC00]);
  const results = lib.search('NAND');
  assertEqual(results.length, 1);
});

test('empty query returns empty', () => {
  const lib = createLibrary();
  lib.loadGroup('74xx', [DEF_74HC00]);
  assertEqual(lib.search(''), []);
  assertEqual(lib.search('   '), []);
});

test('no match returns empty', () => {
  const lib = createLibrary();
  lib.loadGroup('74xx', [DEF_74HC00]);
  assertEqual(lib.search('zzzzz'), []);
});

test('search within group', () => {
  const lib = createLibrary();
  lib.loadGroup('74xx', [DEF_74HC00, DEF_74HC04]);
  lib.loadGroup('memory', [DEF_AT28C256]);
  const results = lib.search('74', { group: '74xx' });
  assertEqual(results.length, 2);
});

test('search respects limit', () => {
  const lib = createLibrary();
  lib.loadGroup('74xx', [DEF_74HC00, DEF_74HC04, DEF_74HC161, DEF_74HC574]);
  const results = lib.search('74hc', { limit: 2 });
  assertEqual(results.length, 2);
});

test('exact match scores highest', () => {
  const lib = createLibrary();
  lib.loadGroup('74xx', [DEF_74HC00, DEF_74HC04, DEF_74HC161]);
  const results = lib.search('74HC04');
  assertEqual(results[0].part, '74HC04');
});

// --- filter ---
console.log('\nfilter:');
test('filter by group', () => {
  const lib = createLibrary();
  lib.loadGroup('74xx', [DEF_74HC00, DEF_74HC04]);
  lib.loadGroup('memory', [DEF_AT28C256]);
  const results = lib.filter({ group: '74xx' });
  assertEqual(results.length, 2);
});

test('filter by family', () => {
  const lib = createLibrary();
  lib.loadGroup('74xx', [DEF_74HC00, DEF_74HC04]);
  lib.loadGroup('memory', [DEF_AT28C256]);
  const results = lib.filter({ family: 'AT28' });
  assertEqual(results.length, 1);
  assertEqual(results[0].part, 'AT28C256');
});

test('filter by pin range', () => {
  const lib = createLibrary();
  lib.loadGroup('74xx', [DEF_74HC00, DEF_74HC04, DEF_74HC161, DEF_74HC574]);
  const results = lib.filter({ minPins: 16, maxPins: 20 });
  assertEqual(results.length, 2); // 74HC161=16, 74HC574=20
});

test('filter by package', () => {
  const lib = createLibrary();
  lib.loadGroup('74xx', [DEF_74HC00]);
  lib.loadGroup('passive', [DEF_LED]);
  const results = lib.filter({ package: 'DIP' });
  assertEqual(results.length, 1);
  assertEqual(results[0].part, '74HC00');
});

test('filter by role', () => {
  const lib = createLibrary();
  lib.loadGroup('74xx', [DEF_74HC00, DEF_74HC04, DEF_74HC161]);
  const results = lib.filter({ role: 'counter' });
  assertEqual(results.length, 1);
  assertEqual(results[0].part, '74HC161');
});

test('filter combined criteria', () => {
  const lib = createLibrary();
  lib.loadGroup('74xx', [DEF_74HC00, DEF_74HC04, DEF_74HC161, DEF_74HC574]);
  const results = lib.filter({ group: '74xx', minPins: 16 });
  assertEqual(results.length, 2); // 161 (16pin) + 574 (20pin)
});

// --- listAll ---
console.log('\nlistAll:');
test('returns all entries across groups', () => {
  const lib = createLibrary();
  lib.loadGroup('74xx', [DEF_74HC00, DEF_74HC04]);
  lib.loadGroup('memory', [DEF_AT28C256]);
  lib.loadGroup('passive', [DEF_LED]);
  const all = lib.listAll();
  assertEqual(all.length, 4);
});

// --- clear ---
console.log('\nclear:');
test('clears all data', () => {
  const lib = createLibrary();
  lib.loadGroup('74xx', [DEF_74HC00, DEF_74HC04]);
  assertEqual(lib.count(), 2);
  lib.clear();
  assertEqual(lib.count(), 0);
  assertEqual(lib.getByPart('74HC00'), null);
});

// =============================================================================
console.log('\n' + '─'.repeat(40));
console.log(`${passed + failed} tests: ${passed} passed, ${failed} failed`);
if (failed > 0) process.exit(1);
console.log('✅ Library tests passed\n');
