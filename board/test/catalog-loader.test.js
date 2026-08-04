/**
 * Components Board — Catalog Auto-Loader Tests
 * Run: node test/catalog-loader.test.js
 */

import { createCatalogLoader, DEFAULT_GROUPS, createFsReader, createDirScanner } from '../src/model/catalog-loader.js';
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

async function asyncTest(name, fn) {
  try {
    await fn();
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
// MOCK DATA
// =============================================================================

const MOCK_INDEX_74XX = {
  schema: 'db.group', version: 1, id: '74xx',
  title: '74xx and 74HC logic ICs',
  components: ['74HC00', '74HC04', '74HC161'],
};

const MOCK_INDEX_MEMORY = {
  schema: 'db.group', version: 1, id: 'memory',
  title: 'Memory ICs',
  components: ['AT28C256', '62256'],
};

const MOCK_INDEX_PASSIVE = {
  schema: 'db.group', version: 1, id: 'passive',
  components: ['Resistor', 'LED'],
};

const MOCK_INDEX_VIRTUAL = {
  schema: 'db.group', version: 1, id: 'virtual',
  components: ['VCC', 'GND'],
};

const MOCK_INDEX_SUPPORT = {
  schema: 'db.group', version: 1, id: 'support',
  components: ['NE555'],
};

const MOCK_INDEX_DISCRETE = {
  schema: 'db.group', version: 1, id: 'discrete',
  components: ['NPN'],
};

const MOCK_DEFS = {
  '74HC00': {
    part: '74HC00',
    about: { title: 'Quad 2-input NAND gate', family: '74HC', group: '74xx', role: 'nand_gate', manufacturer: 'TI' },
    package: { kind: 'DIP' },
    pins: { '1': ['1A','in'], '2': ['1B','in'], '3': ['1Y','out'], '7': ['GND','power'], '14': ['VCC','power'] },
  },
  '74HC04': {
    part: '74HC04',
    about: { title: 'Hex inverter', family: '74HC', group: '74xx', role: 'inverter', manufacturer: 'TI' },
    package: { kind: 'DIP' },
    pins: { '1': ['1A','in'], '2': ['1Y','out'], '7': ['GND','power'], '14': ['VCC','power'] },
  },
  '74HC161': {
    part: '74HC161',
    about: { title: '4-bit binary counter', family: '74HC', group: '74xx', role: 'counter', manufacturer: 'TI' },
    package: { kind: 'DIP' },
    pins: Object.fromEntries([...Array(16)].map((_,i)=>[i+1,['','']])),
  },
  'AT28C256': {
    part: 'AT28C256',
    about: { title: '32KB parallel EEPROM', family: 'AT28', group: 'memory', role: 'eeprom' },
    package: { kind: 'DIP' },
    pins: Object.fromEntries([...Array(28)].map((_,i)=>[i+1,['','']])),
  },
  '62256': {
    part: '62256',
    about: { title: '32KB static RAM', family: '62256', group: 'memory', role: 'sram' },
    package: { kind: 'DIP' },
    pins: Object.fromEntries([...Array(28)].map((_,i)=>[i+1,['','']])),
  },
  'Resistor': {
    part: 'Resistor',
    about: { title: 'Resistor', family: 'Resistor', group: 'passive', role: 'resistor' },
    package: { kind: 'TH' },
    pins: { '1': ['1',''], '2': ['2',''] },
  },
  'LED': {
    part: 'LED',
    about: { title: 'Standard LED', family: 'LED', group: 'passive', role: 'led' },
    package: { kind: 'TH' },
    pins: { '1': ['A',''], '2': ['K',''] },
  },
  'VCC': {
    part: 'VCC',
    about: { title: 'Power rail +5V', family: 'virtual', group: 'virtual', role: 'power_source' },
    package: { kind: 'virtual' },
    pins: { '1': ['VCC',''] },
  },
  'GND': {
    part: 'GND',
    about: { title: 'Ground rail', family: 'virtual', group: 'virtual', role: 'power_source' },
    package: { kind: 'virtual' },
    pins: { '1': ['GND',''] },
  },
  'NE555': {
    part: 'NE555',
    about: { title: 'Timer IC', family: 'NE555', group: 'support', role: 'timer' },
    package: { kind: 'DIP' },
    pins: Object.fromEntries([...Array(8)].map((_,i)=>[i+1,['','']])),
  },
  'NPN': {
    part: 'NPN',
    about: { title: 'NPN transistor', family: 'NPN', group: 'discrete', role: 'transistor' },
    package: { kind: 'TO-92' },
    pins: { '1': ['E',''], '2': ['B',''], '3': ['C',''] },
  },
};

// =============================================================================
// MOCK READER
// =============================================================================

function createMockReader(indices, defs, failPaths = []) {
  const calls = [];

  function mockReader(url) {
    calls.push(url);

    if (failPaths.some(p => url.includes(p))) {
      return Promise.resolve(null);
    }

    // Match index.json requests
    for (const [groupId, index] of Object.entries(indices)) {
      if (url.endsWith(`/${groupId}/index.json`)) {
        return Promise.resolve(index);
      }
    }

    // Match definition.json requests
    for (const [part, def] of Object.entries(defs)) {
      if (url.includes(`/${part}/definition/definition.json`)) {
        return Promise.resolve(def);
      }
    }

    return Promise.resolve(null);
  }

  mockReader.getCalls = () => [...calls];
  mockReader.reset = () => { calls.length = 0; };
  return mockReader;
}

// =============================================================================
// TESTS
// =============================================================================

console.log('\n📚 Catalog Auto-Loader Tests\n');

// --- Factory ---
console.log('  Factory:');

test('createCatalogLoader returns object with expected API', () => {
  const loader = createCatalogLoader({ basePath: '/test' });
  assert(typeof loader.loadAll === 'function');
  assert(typeof loader.loadGroup === 'function');
  assert(typeof loader.loadGroups === 'function');
  assert(typeof loader.discoverParts === 'function');
  assert(typeof loader.loadDefinition === 'function');
  assert(typeof loader.isLoading === 'function');
  assert(typeof loader.getLastResult === 'function');
});

test('DEFAULT_GROUPS has 6 groups', () => {
  assertEqual(DEFAULT_GROUPS.length, 6);
  assert(DEFAULT_GROUPS.includes('74xx'));
  assert(DEFAULT_GROUPS.includes('memory'));
  assert(DEFAULT_GROUPS.includes('passive'));
  assert(DEFAULT_GROUPS.includes('virtual'));
  assert(DEFAULT_GROUPS.includes('support'));
  assert(DEFAULT_GROUPS.includes('discrete'));
});

// --- Discovery ---
console.log('\n  Discovery:');

await asyncTest('discoverParts reads group index.json', async () => {
  const reader = createMockReader({ '74xx': MOCK_INDEX_74XX }, {});
  const loader = createCatalogLoader({ basePath: '/lib/standard', reader });
  const parts = await loader.discoverParts('74xx');
  assertEqual(parts, ['74HC00', '74HC04', '74HC161']);
});

await asyncTest('discoverParts returns empty for missing index', async () => {
  const reader = createMockReader({}, {});
  const loader = createCatalogLoader({ basePath: '/lib/standard', reader });
  const parts = await loader.discoverParts('missing');
  assertEqual(parts, []);
});

await asyncTest('discoverParts returns empty for index without components', async () => {
  const reader = createMockReader({ '74xx': { schema: 'db.group', version: 1 } }, {});
  const loader = createCatalogLoader({ basePath: '/lib/standard', reader });
  const parts = await loader.discoverParts('74xx');
  assertEqual(parts, []);
});

// --- Load Definition ---
console.log('\n  Load Definition:');

await asyncTest('loadDefinition fetches correct path', async () => {
  const reader = createMockReader({}, MOCK_DEFS);
  const loader = createCatalogLoader({ basePath: '/lib/standard', reader });
  const def = await loader.loadDefinition('74xx', '74HC04');
  assertEqual(def.part, '74HC04');
  assertEqual(def.about.title, 'Hex inverter');
});

await asyncTest('loadDefinition returns null for missing part', async () => {
  const reader = createMockReader({}, {});
  const loader = createCatalogLoader({ basePath: '/lib/standard', reader });
  const def = await loader.loadDefinition('74xx', 'MISSING');
  assertEqual(def, null);
});

// --- Load Group ---
console.log('\n  Load Group:');

await asyncTest('loadGroup loads all parts from group', async () => {
  const reader = createMockReader({ '74xx': MOCK_INDEX_74XX }, MOCK_DEFS);
  const loader = createCatalogLoader({ basePath: '/lib/standard', reader });
  const library = createLibrary();
  const result = await loader.loadGroup('74xx', library);
  assertEqual(result.loaded, 3);
  assertEqual(result.errors.length, 0);
  assert(library.getByPart('74HC00') !== null);
  assert(library.getByPart('74HC04') !== null);
  assert(library.getByPart('74HC161') !== null);
});

await asyncTest('loadGroup reports errors for missing definitions', async () => {
  const reader = createMockReader(
    { '74xx': { components: ['74HC00', 'MISSING'] } },
    MOCK_DEFS,
  );
  const loader = createCatalogLoader({ basePath: '/lib/standard', reader });
  const library = createLibrary();
  const result = await loader.loadGroup('74xx', library);
  assertEqual(result.loaded, 1);
  assertEqual(result.errors.length, 1);
  assert(result.errors[0].includes('MISSING'));
});

await asyncTest('loadGroup reports error for empty group', async () => {
  const reader = createMockReader({}, {});
  const loader = createCatalogLoader({ basePath: '/lib/standard', reader });
  const library = createLibrary();
  const result = await loader.loadGroup('empty', library);
  assertEqual(result.loaded, 0);
  assert(result.errors.length > 0);
  assert(result.errors[0].includes('no parts discovered'));
});

await asyncTest('loadGroup handles definition without part field', async () => {
  const badDef = { about: { title: 'No part field' } };
  const reader = createMockReader(
    { '74xx': { components: ['BadChip'] } },
    { 'BadChip': badDef },
  );
  const loader = createCatalogLoader({ basePath: '/lib/standard', reader });
  const library = createLibrary();
  const result = await loader.loadGroup('74xx', library);
  assertEqual(result.loaded, 0);
  assert(result.errors[0].includes('missing "part" field'));
});

// --- Load All ---
console.log('\n  Load All:');

await asyncTest('loadAll loads all groups into library', async () => {
  const indices = {
    '74xx': MOCK_INDEX_74XX,
    'memory': MOCK_INDEX_MEMORY,
    'passive': MOCK_INDEX_PASSIVE,
    'virtual': MOCK_INDEX_VIRTUAL,
    'support': MOCK_INDEX_SUPPORT,
    'discrete': MOCK_INDEX_DISCRETE,
  };
  const reader = createMockReader(indices, MOCK_DEFS);
  const loader = createCatalogLoader({ basePath: '/lib/standard', reader });
  const library = createLibrary();
  const result = await loader.loadAll(library);

  assertEqual(result.loaded, 11); // 3+2+2+2+1+1
  assertEqual(result.errors.length, 0);
  assertEqual(result.groups['74xx'], 3);
  assertEqual(result.groups['memory'], 2);
  assertEqual(result.groups['passive'], 2);
  assertEqual(result.groups['virtual'], 2);
  assertEqual(result.groups['support'], 1);
  assertEqual(result.groups['discrete'], 1);
  assertEqual(library.count(), 11);
});

await asyncTest('loadAll calls onProgress for each group', async () => {
  const indices = { '74xx': MOCK_INDEX_74XX, 'memory': MOCK_INDEX_MEMORY };
  const reader = createMockReader(indices, MOCK_DEFS);
  const loader = createCatalogLoader({
    basePath: '/lib/standard',
    reader,
    groups: ['74xx', 'memory'],
  });
  const library = createLibrary();
  const progress = [];
  await loader.loadAll(library, {
    onProgress: (p) => progress.push(p),
  });
  assertEqual(progress.length, 2);
  assertEqual(progress[0].group, '74xx');
  assertEqual(progress[0].loaded, 3);
  assertEqual(progress[1].group, 'memory');
  assertEqual(progress[1].loaded, 2);
});

await asyncTest('loadAll sets lastResult', async () => {
  const reader = createMockReader({ '74xx': MOCK_INDEX_74XX }, MOCK_DEFS);
  const loader = createCatalogLoader({ basePath: '/lib/standard', reader, groups: ['74xx'] });
  const library = createLibrary();
  assertEqual(loader.getLastResult(), null);
  await loader.loadAll(library);
  const last = loader.getLastResult();
  assert(last !== null);
  assertEqual(last.loaded, 3);
});

await asyncTest('loadAll prevents concurrent loads', async () => {
  const reader = createMockReader({ '74xx': MOCK_INDEX_74XX }, MOCK_DEFS);
  const loader = createCatalogLoader({ basePath: '/lib/standard', reader, groups: ['74xx'] });
  const library = createLibrary();

  // Start first load (don't await)
  const p1 = loader.loadAll(library);
  // Try second load immediately
  const p2 = loader.loadAll(library);

  const [r1, r2] = await Promise.all([p1, p2]);
  assert(r1.loaded === 3 || r2.loaded === 3);
  // One of them should report "already in progress"
  assert(r2.errors.length > 0 || r1.errors.length > 0 || (r1.loaded + r2.loaded === 3));
});

// --- Load Groups (subset) ---
console.log('\n  Load Groups (subset):');

await asyncTest('loadGroups loads only specified groups', async () => {
  const indices = { '74xx': MOCK_INDEX_74XX, 'memory': MOCK_INDEX_MEMORY };
  const reader = createMockReader(indices, MOCK_DEFS);
  const loader = createCatalogLoader({ basePath: '/lib/standard', reader });
  const library = createLibrary();
  const result = await loader.loadGroups(['memory'], library);
  assertEqual(result.loaded, 2);
  assert(library.getByPart('AT28C256') !== null);
  assert(library.getByPart('74HC00') === null); // not loaded
});

// --- URL Construction ---
console.log('\n  URL Construction:');

await asyncTest('reader receives correct URLs', async () => {
  const reader = createMockReader({ '74xx': { components: ['74HC04'] } }, MOCK_DEFS);
  const loader = createCatalogLoader({ basePath: '/base/lib/standard', reader, groups: ['74xx'] });
  const library = createLibrary();
  await loader.loadAll(library);

  const calls = reader.getCalls();
  assert(calls.includes('/base/lib/standard/74xx/index.json'));
  assert(calls.includes('/base/lib/standard/74xx/74HC04/definition/definition.json'));
});

// --- Error Resilience ---
console.log('\n  Error Resilience:');

await asyncTest('partial failures still load available parts', async () => {
  const reader = createMockReader(
    { '74xx': { components: ['74HC00', '74HC04', 'BROKEN'] } },
    MOCK_DEFS,
    ['BROKEN'],
  );
  const loader = createCatalogLoader({ basePath: '/lib/standard', reader, groups: ['74xx'] });
  const library = createLibrary();
  const result = await loader.loadAll(library);
  assertEqual(result.loaded, 2);
  assertEqual(result.errors.length, 1);
  assert(library.getByPart('74HC00') !== null);
  assert(library.getByPart('74HC04') !== null);
});

await asyncTest('all groups failing still returns structured result', async () => {
  const reader = () => Promise.resolve(null);
  const loader = createCatalogLoader({ basePath: '/lib/standard', reader, groups: ['74xx', 'memory'] });
  const library = createLibrary();
  const result = await loader.loadAll(library);
  assertEqual(result.loaded, 0);
  assert(result.errors.length > 0);
  assertEqual(library.count(), 0);
});

// --- isLoading ---
console.log('\n  Loading State:');

await asyncTest('isLoading is false before and after load', async () => {
  const reader = createMockReader({ '74xx': MOCK_INDEX_74XX }, MOCK_DEFS);
  const loader = createCatalogLoader({ basePath: '/lib/standard', reader, groups: ['74xx'] });
  const library = createLibrary();
  assert(!loader.isLoading());
  await loader.loadAll(library);
  assert(!loader.isLoading());
});

// --- Real filesystem test (integration) ---
console.log('\n  Integration (real lib/standard):');

await asyncTest('loads real 74xx definitions from disk', async () => {
  const fs = await import('node:fs/promises');
  const path = await import('node:path');
  const url = await import('node:url');
  const __dirname = path.dirname(url.fileURLToPath(import.meta.url));
  const libPath = path.resolve(__dirname, '../../lib/standard');

  // Check if lib/standard exists
  try {
    await fs.access(libPath);
  } catch {
    console.log('    (skipped — lib/standard not accessible)');
    passed--; // undo pass count
    return;
  }

  const reader = createFsReader(fs);
  const scanner = createDirScanner(fs);
  const loader = createCatalogLoader({ basePath: libPath, reader, dirScanner: scanner, groups: ['74xx'] });
  const library = createLibrary();
  const result = await loader.loadAll(library);

  // 74xx group should have the parts listed in its index.json
  assert(result.loaded > 0, `Expected some 74xx parts loaded, got ${result.loaded}`);
  // Check a known part
  const hc04 = library.getByPart('74HC04');
  assert(hc04 !== null, '74HC04 should be in library');
  assertEqual(hc04.title, 'Hex inverter');
  assertEqual(hc04.pinCount, 14);
});

await asyncTest('loads all real groups from disk', async () => {
  const fs = await import('node:fs/promises');
  const path = await import('node:path');
  const url = await import('node:url');
  const __dirname = path.dirname(url.fileURLToPath(import.meta.url));
  const libPath = path.resolve(__dirname, '../../lib/standard');

  try {
    await fs.access(libPath);
  } catch {
    console.log('    (skipped — lib/standard not accessible)');
    passed--;
    return;
  }

  const reader = createFsReader(fs);
  const scanner = createDirScanner(fs);
  const loader = createCatalogLoader({ basePath: libPath, reader, dirScanner: scanner });
  const library = createLibrary();
  const result = await loader.loadAll(library);

  assert(result.loaded > 10, `Expected >10 parts total, got ${result.loaded}`);
  assert(result.groups['74xx'] > 0, '74xx should have parts');
  assert(result.groups['memory'] > 0, 'memory should have parts');
  // Library count matches
  assertEqual(library.count(), result.loaded);
});

// =============================================================================
// SUMMARY
// =============================================================================

console.log(`\n  ${passed + failed} tests: ${passed} passed, ${failed} failed`);
if (failed > 0) {
  console.log('\n  ❌ CATALOG LOADER TESTS FAILED');
  process.exit(1);
} else {
  console.log('\n  ✅ Catalog loader tests passed');
}
