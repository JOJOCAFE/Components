/**
 * Components Board — Export Module Unit Tests
 * Run: node test/export.test.js
 */

import assert from 'node:assert/strict';
import {
  toMonochrome,
  generateBorderFrame,
  generateTitleBlock,
  generateFoldMarks,
  generateTiling,
  generatePrintPreview,
  exportSVG,
  exportPNGMeta,
} from '../src/view/export.js';

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

// --- Helper: default config ---
function makeConfig(overrides = {}) {
  const base = {
    paper: { size: 'A4', width_mm: 297, height_mm: 210, orientation: 'landscape', margin_mm: { top: 10, bottom: 10, left: 10, right: 10 } },
    grid: { border_tick_mm: 50 },
    title_block: { show: true, project: 'RV8-GR CPU', page_title: 'CPU', author: 'Jo', revision: '1.0' },
    export: { dpi: 300, format: 'pdf', monochrome: false, include_title_block: true, include_fold_marks: false },
    print: { scale: '1:1', tile_to: 'A4', overlap_mm: 15 },
  };
  return { ...base, ...overrides };
}

console.log('\n━━━ Export Module Tests ━━━\n');

// ━━━ toMonochrome ━━━

console.log('toMonochrome:');

test('pure white stays white', () => {
  assert.equal(toMonochrome('#ffffff'), '#ffffff');
});

test('pure black stays black', () => {
  assert.equal(toMonochrome('#000000'), '#000000');
});

test('pure red → gray (luminance 0.2126*255≈54)', () => {
  const result = toMonochrome('#ff0000');
  assert.equal(result, '#363636');
});

test('pure green → gray (luminance 0.7152*255≈182)', () => {
  const result = toMonochrome('#00ff00');
  assert.equal(result, '#b6b6b6');
});

test('pure blue → gray (luminance 0.0722*255≈18)', () => {
  const result = toMonochrome('#0000ff');
  assert.equal(result, '#121212');
});

test('#007C3D → grayscale (luminance-based)', () => {
  // 0.2126*0 + 0.7152*124 + 0.0722*61 ≈ 93
  const result = toMonochrome('#007C3D');
  // 0*0.2126 + 124*0.7152 + 61*0.0722 = 88.68 + 4.40 = 93.09 → 93 = 0x5D
  assert.equal(result, '#5d5d5d');
});

test('shorthand #abc expands correctly', () => {
  // #aabbcc → r=170,g=187,b=204
  // lum = 0.2126*170 + 0.7152*187 + 0.0722*204 = 36.14+133.74+14.73=184.61→185
  const result = toMonochrome('#abc');
  assert.equal(result, '#b9b9b9');
});

test('null input returns #000000', () => {
  assert.equal(toMonochrome(null), '#000000');
});

test('empty string returns #000000', () => {
  assert.equal(toMonochrome(''), '#000000');
});

test('invalid hex returns #000000', () => {
  assert.equal(toMonochrome('#xyz'), '#000000');
});

test('#808080 (mid-gray) stays approximately gray', () => {
  // 0.2126*128 + 0.7152*128 + 0.0722*128 = 128
  const result = toMonochrome('#808080');
  assert.equal(result, '#808080');
});

// ━━━ generateBorderFrame ━━━

console.log('\ngenerateBorderFrame:');

test('returns rect at margin boundary', () => {
  const frame = generateBorderFrame(297, 210, { top: 10, bottom: 10, left: 10, right: 10 }, 50);
  assert.equal(frame.rect.x, 10);
  assert.equal(frame.rect.y, 10);
  assert.equal(frame.rect.w, 277);
  assert.equal(frame.rect.h, 190);
});

test('ticks at 50mm intervals on top edge', () => {
  const frame = generateBorderFrame(297, 210, { top: 10, bottom: 10, left: 10, right: 10 }, 50);
  const topTicks = frame.ticks.filter(t => t.y1 === 10 && t.y2 > t.y1);
  // inner width 277, so ticks at 50,100,150,200,250 = 5 ticks
  assert.equal(topTicks.length, 5);
  assert.equal(topTicks[0].x1, 60); // margin(10) + 50
  assert.equal(topTicks[0].label, '50');
});

test('ticks at 50mm intervals on left edge', () => {
  const frame = generateBorderFrame(297, 210, { top: 10, bottom: 10, left: 10, right: 10 }, 50);
  const leftTicks = frame.ticks.filter(t => t.x1 === 10 && t.x2 > t.x1);
  // inner height 190, so ticks at 50,100,150 = 3 ticks
  assert.equal(leftTicks.length, 3);
  assert.equal(leftTicks[0].y1, 60);
});

test('zero margins: frame fills entire paper', () => {
  const frame = generateBorderFrame(297, 210, { top: 0, bottom: 0, left: 0, right: 0 }, 50);
  assert.equal(frame.rect.x, 0);
  assert.equal(frame.rect.y, 0);
  assert.equal(frame.rect.w, 297);
  assert.equal(frame.rect.h, 210);
});

test('custom tick interval (25mm)', () => {
  const frame = generateBorderFrame(297, 210, { top: 10, bottom: 10, left: 10, right: 10 }, 25);
  const topTicks = frame.ticks.filter(t => t.y1 === 10 && t.y2 > t.y1);
  // inner width 277, ticks at 25,50,...275 = 11 ticks
  assert.equal(topTicks.length, 11);
});

test('portrait orientation (210×297)', () => {
  const frame = generateBorderFrame(210, 297, { top: 10, bottom: 10, left: 10, right: 10 }, 50);
  assert.equal(frame.rect.w, 190);
  assert.equal(frame.rect.h, 277);
});

test('ticks have string labels', () => {
  const frame = generateBorderFrame(297, 210, { top: 10, bottom: 10, left: 10, right: 10 }, 50);
  for (const tick of frame.ticks) {
    assert.equal(typeof tick.label, 'string');
  }
});

// ━━━ generateTitleBlock ━━━

console.log('\ngenerateTitleBlock:');

test('positioned at bottom-right inside margin', () => {
  const cfg = makeConfig();
  const tb = generateTitleBlock(cfg);
  // x + width should equal paper_width - right_margin
  assert.equal(tb.x + tb.width, 297 - 10);
  // y + height should equal paper_height - bottom_margin
  assert.equal(tb.y + tb.height, 210 - 10);
});

test('has 7 fields', () => {
  const cfg = makeConfig();
  const tb = generateTitleBlock(cfg);
  assert.equal(tb.fields.length, 7);
});

test('includes Project field with config value', () => {
  const cfg = makeConfig();
  const tb = generateTitleBlock(cfg);
  const proj = tb.fields.find(f => f.label === 'Project');
  assert.ok(proj);
  assert.equal(proj.value, 'RV8-GR CPU');
});

test('includes Author field', () => {
  const cfg = makeConfig();
  const tb = generateTitleBlock(cfg);
  const auth = tb.fields.find(f => f.label === 'Author');
  assert.ok(auth);
  assert.equal(auth.value, 'Jo');
});

test('includes Revision field', () => {
  const cfg = makeConfig();
  const tb = generateTitleBlock(cfg);
  const rev = tb.fields.find(f => f.label === 'Revision');
  assert.ok(rev);
  assert.equal(rev.value, '1.0');
});

test('pageTitle override works', () => {
  const cfg = makeConfig();
  const tb = generateTitleBlock(cfg, 'Power Supply');
  const page = tb.fields.find(f => f.label === 'Page');
  assert.equal(page.value, 'Power Supply');
});

test('Date field is ISO format', () => {
  const cfg = makeConfig();
  const tb = generateTitleBlock(cfg);
  const date = tb.fields.find(f => f.label === 'Date');
  assert.ok(date);
  assert.match(date.value, /^\d{4}-\d{2}-\d{2}$/);
});

test('width is 180mm for A4', () => {
  const cfg = makeConfig();
  const tb = generateTitleBlock(cfg);
  assert.equal(tb.width, 180);
});

test('height is 30mm', () => {
  const cfg = makeConfig();
  const tb = generateTitleBlock(cfg);
  assert.equal(tb.height, 30);
});

// ━━━ generateFoldMarks ━━━

console.log('\ngenerateFoldMarks:');

test('A4 returns null (no folds needed)', () => {
  const result = generateFoldMarks('A4', 297, 210);
  assert.equal(result, null);
});

test('A3 returns null (no folds needed)', () => {
  const result = generateFoldMarks('A3', 420, 297);
  assert.equal(result, null);
});

test('A2 returns fold marks', () => {
  const result = generateFoldMarks('A2', 594, 420);
  assert.ok(result);
  assert.ok(result.marks.length > 0);
});

test('A1 returns fold marks', () => {
  const result = generateFoldMarks('A1', 841, 594);
  assert.ok(result);
  assert.ok(result.marks.length > 0);
});

test('A0 returns fold marks', () => {
  const result = generateFoldMarks('A0', 1189, 841);
  assert.ok(result);
  assert.ok(result.marks.length > 0);
});

test('A0 first vertical fold at width-210 from right', () => {
  const result = generateFoldMarks('A0', 1189, 841);
  const firstFold = result.marks.find(m => m.type === 'fold-line' && m.y === 0);
  // First fold at 1189-210 = 979
  assert.ok(firstFold);
  assert.equal(firstFold.x, 979);
});

test('A2 has horizontal folds (height 420 > 297)', () => {
  const result = generateFoldMarks('A2', 594, 420);
  const hFolds = result.marks.filter(m => m.x === 0 && m.type === 'fold-line');
  assert.ok(hFolds.length > 0);
});

test('marks include fold-line type', () => {
  const result = generateFoldMarks('A0', 1189, 841);
  const foldLines = result.marks.filter(m => m.type === 'fold-line');
  assert.ok(foldLines.length > 0);
});

test('marks include cut-mark type', () => {
  const result = generateFoldMarks('A0', 1189, 841);
  const cutMarks = result.marks.filter(m => m.type === 'cut-mark');
  assert.ok(cutMarks.length > 0);
});

test('marks include alignment type', () => {
  const result = generateFoldMarks('A0', 1189, 841);
  const alignments = result.marks.filter(m => m.type === 'alignment');
  assert.ok(alignments.length > 0);
});

// ━━━ generateTiling ━━━

console.log('\ngenerateTiling:');

test('A4 into A4 = 1 tile', () => {
  const result = generateTiling(297, 210, { width_mm: 297, height_mm: 210 }, 15);
  assert.equal(result.tiles.length, 1);
  assert.equal(result.rows, 1);
  assert.equal(result.cols, 1);
});

test('A0 into A4 tiles with 15mm overlap', () => {
  const result = generateTiling(1189, 841, { width_mm: 297, height_mm: 210 }, 15);
  // cols: ceil((1189-15)/(297-15)) = ceil(1174/282) = ceil(4.16) = 5
  // rows: ceil((841-15)/(210-15)) = ceil(826/195) = ceil(4.23) = 5
  assert.ok(result.cols >= 4);
  assert.ok(result.rows >= 4);
  assert.equal(result.tiles.length, result.rows * result.cols);
});

test('each tile has row and col', () => {
  const result = generateTiling(594, 420, { width_mm: 297, height_mm: 210 }, 15);
  for (const tile of result.tiles) {
    assert.ok(typeof tile.row === 'number');
    assert.ok(typeof tile.col === 'number');
  }
});

test('tiles have x, y, width, height', () => {
  const result = generateTiling(594, 420, { width_mm: 297, height_mm: 210 }, 15);
  for (const tile of result.tiles) {
    assert.ok(typeof tile.x === 'number');
    assert.ok(typeof tile.y === 'number');
    assert.ok(tile.width > 0);
    assert.ok(tile.height > 0);
  }
});

test('first tile starts at (0,0)', () => {
  const result = generateTiling(594, 420, { width_mm: 297, height_mm: 210 }, 15);
  const first = result.tiles[0];
  assert.equal(first.x, 0);
  assert.equal(first.y, 0);
  assert.equal(first.row, 0);
  assert.equal(first.col, 0);
});

test('tile width does not exceed target', () => {
  const result = generateTiling(1189, 841, { width_mm: 297, height_mm: 210 }, 15);
  for (const tile of result.tiles) {
    assert.ok(tile.width <= 297);
    assert.ok(tile.height <= 210);
  }
});

test('overlap 0 produces non-overlapping tiles', () => {
  const result = generateTiling(600, 400, { width_mm: 300, height_mm: 200 }, 0);
  assert.equal(result.cols, 2);
  assert.equal(result.rows, 2);
});

// ━━━ generatePrintPreview ━━━

console.log('\ngeneratePrintPreview:');

test('returns paper dimensions', () => {
  const cfg = makeConfig();
  const pp = generatePrintPreview({}, cfg);
  assert.equal(pp.paper.width_mm, 297);
  assert.equal(pp.paper.height_mm, 210);
});

test('returns margins', () => {
  const cfg = makeConfig();
  const pp = generatePrintPreview({}, cfg);
  assert.deepEqual(pp.margins, { top: 10, bottom: 10, left: 10, right: 10 });
});

test('includes title block when enabled', () => {
  const cfg = makeConfig();
  const pp = generatePrintPreview({}, cfg);
  assert.ok(pp.titleBlock);
  assert.ok(pp.titleBlock.fields.length > 0);
});

test('no title block when include_title_block=false', () => {
  const cfg = makeConfig({ export: { include_title_block: false, include_fold_marks: false } });
  const pp = generatePrintPreview({}, cfg);
  assert.equal(pp.titleBlock, null);
});

test('no title block when title_block.show=false', () => {
  const cfg = makeConfig();
  cfg.title_block.show = false;
  const pp = generatePrintPreview({}, cfg);
  assert.equal(pp.titleBlock, null);
});

test('includes border frame', () => {
  const cfg = makeConfig();
  const pp = generatePrintPreview({}, cfg);
  assert.ok(pp.borderFrame);
  assert.ok(pp.borderFrame.rect);
  assert.ok(pp.borderFrame.ticks.length > 0);
});

test('no fold marks when include_fold_marks=false', () => {
  const cfg = makeConfig();
  const pp = generatePrintPreview({}, cfg);
  assert.equal(pp.foldMarks, null);
});

test('fold marks present for A0 with include_fold_marks=true', () => {
  const cfg = makeConfig({
    paper: { size: 'A0', width_mm: 1189, height_mm: 841, orientation: 'landscape', margin_mm: { top: 10, bottom: 10, left: 10, right: 10 } },
    export: { include_fold_marks: true, include_title_block: true },
  });
  const pp = generatePrintPreview({}, cfg);
  assert.ok(pp.foldMarks);
  assert.ok(pp.foldMarks.marks.length > 0);
});

test('passes through devices from boardState', () => {
  const cfg = makeConfig();
  const state = { devices: [{ id: 'u1', x: 50, y: 30 }], routes: [], labels: [] };
  const pp = generatePrintPreview(state, cfg);
  assert.equal(pp.devices.length, 1);
  assert.equal(pp.devices[0].id, 'u1');
});

test('passes through routes from boardState', () => {
  const cfg = makeConfig();
  const state = { devices: [], routes: [{ id: 'r1', points: [{x:0,y:0},{x:10,y:10}] }], labels: [] };
  const pp = generatePrintPreview(state, cfg);
  assert.equal(pp.routes.length, 1);
});

test('passes through labels from boardState', () => {
  const cfg = makeConfig();
  const state = { devices: [], routes: [], labels: [{ text: 'VCC', x: 5, y: 5 }] };
  const pp = generatePrintPreview(state, cfg);
  assert.equal(pp.labels.length, 1);
});

// ━━━ exportSVG ━━━

console.log('\nexportSVG:');

test('returns valid SVG string', () => {
  const cfg = makeConfig();
  const pp = generatePrintPreview({}, cfg);
  const svg = exportSVG(pp);
  assert.ok(svg.content.startsWith('<svg'));
  assert.ok(svg.content.endsWith('</svg>'));
});

test('SVG has correct viewBox', () => {
  const cfg = makeConfig();
  const pp = generatePrintPreview({}, cfg);
  const svg = exportSVG(pp);
  assert.ok(svg.content.includes('viewBox="0 0 297 210"'));
});

test('SVG has xmlns attribute', () => {
  const cfg = makeConfig();
  const pp = generatePrintPreview({}, cfg);
  const svg = exportSVG(pp);
  assert.ok(svg.content.includes('xmlns="http://www.w3.org/2000/svg"'));
});

test('returns width_mm and height_mm', () => {
  const cfg = makeConfig();
  const pp = generatePrintPreview({}, cfg);
  const svg = exportSVG(pp);
  assert.equal(svg.width_mm, 297);
  assert.equal(svg.height_mm, 210);
});

test('includes clip path for paper boundary', () => {
  const cfg = makeConfig();
  const pp = generatePrintPreview({}, cfg);
  const svg = exportSVG(pp);
  assert.ok(svg.content.includes('clipPath'));
  assert.ok(svg.content.includes('paper-clip'));
});

test('monochrome option converts colors', () => {
  const cfg = makeConfig();
  const state = { devices: [{ x: 10, y: 10, fill: '#ff0000', stroke: '#00ff00' }], routes: [], labels: [] };
  const pp = generatePrintPreview(state, cfg);
  const svg = exportSVG(pp, { monochrome: true });
  // Red fill → #363636, Green stroke → #b6b6b6
  assert.ok(svg.content.includes('#363636'));
  assert.ok(svg.content.includes('#b6b6b6'));
});

test('non-monochrome preserves colors', () => {
  const cfg = makeConfig();
  const state = { devices: [{ x: 10, y: 10, fill: '#ff0000', stroke: '#00ff00' }], routes: [], labels: [] };
  const pp = generatePrintPreview(state, cfg);
  const svg = exportSVG(pp, { monochrome: false });
  assert.ok(svg.content.includes('#ff0000'));
  assert.ok(svg.content.includes('#00ff00'));
});

test('SVG includes title block rect', () => {
  const cfg = makeConfig();
  const pp = generatePrintPreview({}, cfg);
  const svg = exportSVG(pp);
  // Title block rendered as rect
  assert.ok(svg.content.includes('Project'));
});

test('SVG renders routes as paths', () => {
  const cfg = makeConfig();
  const state = { devices: [], routes: [{ color: '#007C3D', points: [{x:10,y:20},{x:30,y:40}] }], labels: [] };
  const pp = generatePrintPreview(state, cfg);
  const svg = exportSVG(pp);
  assert.ok(svg.content.includes('<path'));
  assert.ok(svg.content.includes('M10 20'));
});

test('SVG renders labels as text', () => {
  const cfg = makeConfig();
  const state = { devices: [], routes: [], labels: [{ text: 'GND', x: 5, y: 5, color: '#000000' }] };
  const pp = generatePrintPreview(state, cfg);
  const svg = exportSVG(pp);
  assert.ok(svg.content.includes('GND'));
});

test('SVG escapes XML special characters', () => {
  const cfg = makeConfig();
  const state = { devices: [], routes: [], labels: [{ text: 'A<B&C', x: 5, y: 5 }] };
  const pp = generatePrintPreview(state, cfg);
  const svg = exportSVG(pp);
  assert.ok(svg.content.includes('A&lt;B&amp;C'));
});

// ━━━ exportPNGMeta ━━━

console.log('\nexportPNGMeta:');

test('default DPI is 300', () => {
  const cfg = makeConfig();
  const pp = generatePrintPreview({}, cfg);
  const meta = exportPNGMeta(pp);
  assert.equal(meta.dpi, 300);
});

test('A4 at 300 DPI → correct pixel dimensions', () => {
  const cfg = makeConfig();
  const pp = generatePrintPreview({}, cfg);
  const meta = exportPNGMeta(pp);
  // 297mm / 25.4 * 300 = 3508
  // 210mm / 25.4 * 300 = 2480
  assert.equal(meta.width_px, 3508);
  assert.equal(meta.height_px, 2480);
});

test('custom DPI (600) doubles pixel dimensions', () => {
  const cfg = makeConfig();
  const pp = generatePrintPreview({}, cfg);
  const meta = exportPNGMeta(pp, { dpi: 600 });
  assert.equal(meta.dpi, 600);
  // 297/25.4*600 = 7016
  assert.equal(meta.width_px, 7016);
  assert.equal(meta.height_px, 4961);
});

test('72 DPI (screen)', () => {
  const cfg = makeConfig();
  const pp = generatePrintPreview({}, cfg);
  const meta = exportPNGMeta(pp, { dpi: 72 });
  assert.equal(meta.dpi, 72);
  // 297/25.4*72 = 842
  assert.equal(meta.width_px, 842);
});

test('returns scale (pixels per mm)', () => {
  const cfg = makeConfig();
  const pp = generatePrintPreview({}, cfg);
  const meta = exportPNGMeta(pp);
  // 300 / 25.4 ≈ 11.81
  assert.ok(Math.abs(meta.scale - 300 / 25.4) < 0.01);
});

test('returns viewBox string', () => {
  const cfg = makeConfig();
  const pp = generatePrintPreview({}, cfg);
  const meta = exportPNGMeta(pp);
  assert.equal(meta.viewBox, '0 0 297 210');
});

test('portrait A4 at 300 DPI', () => {
  const cfg = makeConfig({
    paper: { size: 'A4', width_mm: 210, height_mm: 297, orientation: 'portrait', margin_mm: { top: 10, bottom: 10, left: 10, right: 10 } },
  });
  const pp = generatePrintPreview({}, cfg);
  const meta = exportPNGMeta(pp);
  assert.equal(meta.width_px, 2480);
  assert.equal(meta.height_px, 3508);
});

// --- Summary ---

console.log(`\n━━━ Results: ${passed} passed, ${failed} failed ━━━\n`);

if (failed > 0) {
  process.exit(1);
}
