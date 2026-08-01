/**
 * Components Board — Config Model Unit Tests
 * Run: node board/test/config.test.js
 */

import assert from 'node:assert/strict';
import {
  PAPER_SIZES,
  VALID_PAPER_SIZES,
  DEFAULT_CONFIG,
  SCHEMA_ID,
  validateConfig,
  createConfig,
  loadConfig,
  saveConfig,
  getPaperDimensions,
} from '../src/model/config.js';

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

console.log('\n━━━ Config Model Tests ━━━\n');

// --- PAPER_SIZES ---

console.log('PAPER_SIZES:');

test('has all 5 ISO sizes (A4, A3, A2, A1, A0)', () => {
  const expected = ['A4', 'A3', 'A2', 'A1', 'A0'];
  for (const size of expected) {
    assert.ok(PAPER_SIZES[size], `Missing size: ${size}`);
  }
  assert.equal(Object.keys(PAPER_SIZES).length, 5);
});

test('A4 is 297×210 mm (landscape)', () => {
  assert.equal(PAPER_SIZES.A4.width_mm, 297);
  assert.equal(PAPER_SIZES.A4.height_mm, 210);
});

test('A3 is 420×297 mm (landscape)', () => {
  assert.equal(PAPER_SIZES.A3.width_mm, 420);
  assert.equal(PAPER_SIZES.A3.height_mm, 297);
});

test('A2 is 594×420 mm (landscape)', () => {
  assert.equal(PAPER_SIZES.A2.width_mm, 594);
  assert.equal(PAPER_SIZES.A2.height_mm, 420);
});

test('A1 is 841×594 mm (landscape)', () => {
  assert.equal(PAPER_SIZES.A1.width_mm, 841);
  assert.equal(PAPER_SIZES.A1.height_mm, 594);
});

test('A0 is 1189×841 mm (landscape)', () => {
  assert.equal(PAPER_SIZES.A0.width_mm, 1189);
  assert.equal(PAPER_SIZES.A0.height_mm, 841);
});

// --- createConfig ---

console.log('\ncreateConfig:');

test('returns valid default config with no arguments', () => {
  const cfg = createConfig();
  const { valid, errors } = validateConfig(cfg);
  assert.ok(valid, `Default config invalid: ${errors.join(', ')}`);
});

test('default matches expected schema', () => {
  const cfg = createConfig();
  assert.equal(cfg.schema, SCHEMA_ID);
  assert.equal(cfg.paper.size, 'A4');
  assert.equal(cfg.paper.width_mm, 297);
  assert.equal(cfg.paper.height_mm, 210);
  assert.equal(cfg.paper.orientation, 'landscape');
});

test('overriding paper.size to A3 adjusts dimensions', () => {
  const cfg = createConfig({ paper: { size: 'A3' } });
  assert.equal(cfg.paper.size, 'A3');
  assert.equal(cfg.paper.width_mm, 420);
  assert.equal(cfg.paper.height_mm, 297);
});

test('overriding paper.size to A0 adjusts dimensions', () => {
  const cfg = createConfig({ paper: { size: 'A0' } });
  assert.equal(cfg.paper.size, 'A0');
  assert.equal(cfg.paper.width_mm, 1189);
  assert.equal(cfg.paper.height_mm, 841);
});

test('overriding orientation to portrait swaps dimensions', () => {
  const cfg = createConfig({ paper: { orientation: 'portrait' } });
  assert.equal(cfg.paper.width_mm, 210);
  assert.equal(cfg.paper.height_mm, 297);
});

// --- validateConfig ---

console.log('\nvalidateConfig:');

test('accepts valid default config', () => {
  const { valid, errors } = validateConfig(createConfig());
  assert.ok(valid, `Errors: ${errors.join(', ')}`);
});

test('rejects missing schema field', () => {
  const cfg = createConfig();
  delete cfg.schema;
  const { valid, errors } = validateConfig(cfg);
  assert.ok(!valid);
  assert.ok(errors.some(e => e.includes('schema')));
});

test('rejects wrong schema value', () => {
  const cfg = createConfig();
  cfg.schema = 'wrong@2';
  const { valid, errors } = validateConfig(cfg);
  assert.ok(!valid);
  assert.ok(errors.some(e => e.includes('schema')));
});

test('rejects invalid paper size', () => {
  const cfg = createConfig();
  cfg.paper.size = 'B5';
  const { valid, errors } = validateConfig(cfg);
  assert.ok(!valid);
  assert.ok(errors.some(e => e.includes('paper size') || e.includes('B5')));
});

test('rejects non-finite margin values (NaN)', () => {
  const cfg = createConfig();
  cfg.paper.margin_mm.top = NaN;
  const { valid, errors } = validateConfig(cfg);
  assert.ok(!valid);
  assert.ok(errors.some(e => e.includes('margin_mm.top')));
});

test('rejects non-finite margin values (Infinity)', () => {
  const cfg = createConfig();
  cfg.paper.margin_mm.left = Infinity;
  const { valid, errors } = validateConfig(cfg);
  assert.ok(!valid);
  assert.ok(errors.some(e => e.includes('margin_mm.left')));
});

test('rejects negative margin values', () => {
  const cfg = createConfig();
  cfg.paper.margin_mm.bottom = -5;
  const { valid, errors } = validateConfig(cfg);
  assert.ok(!valid);
  assert.ok(errors.some(e => e.includes('margin_mm.bottom')));
});

test('rejects null config', () => {
  const { valid, errors } = validateConfig(null);
  assert.ok(!valid);
  assert.ok(errors.length > 0);
});

// --- loadConfig / saveConfig ---

console.log('\nloadConfig / saveConfig:');

test('round-trip preserves data', () => {
  const original = createConfig({ title_block: { project: 'Test', author: 'Bam' } });
  const json = saveConfig(original);
  const restored = loadConfig(json);
  assert.deepEqual(restored, original);
});

test('round-trip with custom values', () => {
  const original = createConfig({
    paper: { size: 'A1', orientation: 'portrait' },
    grid: { major_mm: 5 },
    export: { dpi: 600, monochrome: true },
  });
  const json = saveConfig(original);
  const restored = loadConfig(json);
  assert.deepEqual(restored, original);
});

test('loadConfig throws on invalid JSON', () => {
  assert.throws(() => loadConfig('not json {{{'), /parse error/i);
});

test('loadConfig throws on invalid config', () => {
  assert.throws(() => loadConfig('{"foo": "bar"}'), /validation failed/i);
});

test('saveConfig throws on invalid config', () => {
  assert.throws(() => saveConfig({ broken: true }), /invalid config/i);
});

// --- getPaperDimensions ---

console.log('\ngetPaperDimensions:');

test('returns landscape dimensions for A4 landscape', () => {
  const cfg = createConfig();
  const dims = getPaperDimensions(cfg);
  assert.equal(dims.width_mm, 297);
  assert.equal(dims.height_mm, 210);
});

test('returns portrait dimensions (swapped) for A4 portrait', () => {
  const cfg = createConfig({ paper: { orientation: 'portrait' } });
  const dims = getPaperDimensions(cfg);
  assert.equal(dims.width_mm, 210);
  assert.equal(dims.height_mm, 297);
});

test('returns correct A3 landscape dimensions', () => {
  const cfg = createConfig({ paper: { size: 'A3' } });
  const dims = getPaperDimensions(cfg);
  assert.equal(dims.width_mm, 420);
  assert.equal(dims.height_mm, 297);
});

test('returns correct A3 portrait dimensions', () => {
  const cfg = createConfig({ paper: { size: 'A3', orientation: 'portrait' } });
  const dims = getPaperDimensions(cfg);
  assert.equal(dims.width_mm, 297);
  assert.equal(dims.height_mm, 420);
});

test('throws on unknown paper size', () => {
  const cfg = createConfig();
  cfg.paper.size = 'B5';
  assert.throws(() => getPaperDimensions(cfg), /unknown paper size/i);
});

// --- Summary ---

console.log(`\n━━━ Results: ${passed} passed, ${failed} failed ━━━\n`);

if (failed > 0) {
  process.exit(1);
}
