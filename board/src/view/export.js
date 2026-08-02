/**
 * Components Board — Print & Export Module
 * Phase 4: DOM-free export module generating print-ready output data.
 *
 * All functions are pure — no DOM, no side effects.
 * Coordinates in mm unless stated otherwise.
 */

import { PAPER_SIZES } from '../model/config.js';

// --- 4.7 Monochrome ---

/**
 * Convert a hex color to grayscale equivalent using luminance weighting.
 * @param {string} color - Hex color string (e.g. '#007C3D' or '#abc')
 * @returns {string} Grayscale hex color
 */
export function toMonochrome(color) {
  if (!color || typeof color !== 'string') return '#000000';
  let hex = color.replace('#', '');
  // Expand shorthand (#abc → aabbcc)
  if (hex.length === 3) {
    hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
  }
  if (hex.length !== 6) return '#000000';
  // Validate hex chars
  if (!/^[0-9a-fA-F]{6}$/.test(hex)) return '#000000';
  const r = parseInt(hex.slice(0, 2), 16);
  const g = parseInt(hex.slice(2, 4), 16);
  const b = parseInt(hex.slice(4, 6), 16);
  // ITU-R BT.709 luminance
  const lum = Math.round(0.2126 * r + 0.7152 * g + 0.0722 * b);
  const gray = Math.max(0, Math.min(255, lum));
  const grayHex = gray.toString(16).padStart(2, '0');
  return `#${grayHex}${grayHex}${grayHex}`;
}

// --- 4.8 Border Frame ---

/**
 * Generate border frame with tick marks at regular intervals.
 * @param {number} width_mm - Paper width in mm
 * @param {number} height_mm - Paper height in mm
 * @param {object} margins - {top, bottom, left, right} in mm
 * @param {number} [tick_mm=50] - Tick interval in mm
 * @returns {object} { rect: {x,y,w,h}, ticks: [{x1,y1,x2,y2,label}...] }
 */
export function generateBorderFrame(width_mm, height_mm, margins, tick_mm = 50) {
  const m = margins || { top: 0, bottom: 0, left: 0, right: 0 };
  const x = m.left;
  const y = m.top;
  const w = width_mm - m.left - m.right;
  const h = height_mm - m.top - m.bottom;
  const tickLen = 3; // mm

  const ticks = [];

  // Top edge ticks (pointing inward = downward)
  for (let pos = tick_mm; pos < w; pos += tick_mm) {
    ticks.push({
      x1: x + pos, y1: y,
      x2: x + pos, y2: y + tickLen,
      label: `${Math.round(pos)}`,
    });
  }

  // Bottom edge ticks (pointing inward = upward)
  for (let pos = tick_mm; pos < w; pos += tick_mm) {
    ticks.push({
      x1: x + pos, y1: y + h,
      x2: x + pos, y2: y + h - tickLen,
      label: `${Math.round(pos)}`,
    });
  }

  // Left edge ticks (pointing inward = rightward)
  for (let pos = tick_mm; pos < h; pos += tick_mm) {
    ticks.push({
      x1: x, y1: y + pos,
      x2: x + tickLen, y2: y + pos,
      label: `${Math.round(pos)}`,
    });
  }

  // Right edge ticks (pointing inward = leftward)
  for (let pos = tick_mm; pos < h; pos += tick_mm) {
    ticks.push({
      x1: x + w, y1: y + pos,
      x2: x + w - tickLen, y2: y + pos,
      label: `${Math.round(pos)}`,
    });
  }

  return { rect: { x, y, w, h }, ticks };
}

// --- 4.4 Title Block ---

/**
 * Generate title block positioned at bottom-right corner.
 * @param {object} config - Board config object
 * @param {string} [pageTitle] - Override page title
 * @returns {object} { x, y, width, height, fields: [{label, value, x, y}...] }
 */
export function generateTitleBlock(config, pageTitle) {
  const paper = config.paper || {};
  const margins = paper.margin_mm || { top: 10, bottom: 10, left: 10, right: 10 };
  const width_mm = paper.width_mm || 297;
  const height_mm = paper.height_mm || 210;
  const tb = config.title_block || {};

  // Standard title block: 180×30 for A4, proportional for larger
  const sizeRatio = width_mm / 297;
  const blockWidth = Math.round(180 * Math.min(sizeRatio, 1.5));
  const blockHeight = 30;

  // Position: bottom-right corner, inside margin
  const x = width_mm - margins.right - blockWidth;
  const y = height_mm - margins.bottom - blockHeight;

  const date = new Date().toISOString().slice(0, 10);
  const scale = (config.print && config.print.scale) || '1:1';

  const fields = [
    { label: 'Project', value: tb.project || '', x: x + 5, y: y + 6 },
    { label: 'Page', value: pageTitle || tb.page_title || '', x: x + 5, y: y + 12 },
    { label: 'Author', value: tb.author || '', x: x + 5, y: y + 18 },
    { label: 'Date', value: date, x: x + 5, y: y + 24 },
    { label: 'Revision', value: tb.revision || '1.0', x: x + blockWidth / 2, y: y + 6 },
    { label: 'Paper', value: paper.size || 'A4', x: x + blockWidth / 2, y: y + 12 },
    { label: 'Scale', value: scale, x: x + blockWidth / 2, y: y + 18 },
  ];

  return { x, y, width: blockWidth, height: blockHeight, fields };
}

// --- 4.5 Fold Marks (ISO 5457) ---

/**
 * Generate fold marks for large paper sizes.
 * ISO 5457: A0/A1/A2 fold to A4 size (210×297).
 * @param {string} paper_size - Paper size name (A0, A1, etc.)
 * @param {number} width_mm - Paper width in mm
 * @param {number} height_mm - Paper height in mm
 * @returns {object|null} { marks: [{x, y, type}...] } or null if paper <= A3
 */
export function generateFoldMarks(paper_size, width_mm, height_mm) {
  // Only A0, A1, A2 get fold marks
  const foldSizes = ['A0', 'A1', 'A2'];
  if (!foldSizes.includes(paper_size)) return null;

  const marks = [];
  const targetW = 210; // A4 width (portrait fold target)
  const targetH = 297; // A4 height

  // Vertical fold marks: first fold at 210mm from RIGHT edge,
  // then every 190mm going left
  const firstFold = width_mm - targetW;
  marks.push({ x: firstFold, y: 0, type: 'fold-line' });
  marks.push({ x: firstFold, y: height_mm, type: 'alignment' });

  // Subsequent vertical folds every 190mm from right
  let pos = firstFold - 190;
  while (pos > 0) {
    marks.push({ x: pos, y: 0, type: 'fold-line' });
    marks.push({ x: pos, y: height_mm, type: 'alignment' });
    pos -= 190;
  }

  // Horizontal fold marks: fold at 297mm from bottom edge for tall papers
  if (height_mm > targetH) {
    let hPos = height_mm - targetH;
    while (hPos > 0) {
      marks.push({ x: 0, y: hPos, type: 'fold-line' });
      marks.push({ x: width_mm, y: hPos, type: 'alignment' });
      hPos -= targetH;
    }
  }

  // Cut marks at corners where folds intersect the paper edge
  marks.push({ x: 0, y: 0, type: 'cut-mark' });
  marks.push({ x: width_mm, y: 0, type: 'cut-mark' });

  return { marks };
}

// --- 4.6 Multi-page Tiling ---

/**
 * Split large paper into target-sized tiles with overlap.
 * @param {number} width_mm - Total width in mm
 * @param {number} height_mm - Total height in mm
 * @param {object} targetSize - { width_mm, height_mm } of each tile
 * @param {number} [overlap_mm=15] - Overlap between tiles in mm
 * @returns {object} { tiles: [{x, y, width, height, row, col}...], rows, cols }
 */
export function generateTiling(width_mm, height_mm, targetSize, overlap_mm = 15) {
  const tw = targetSize.width_mm;
  const th = targetSize.height_mm;
  const stepW = tw - overlap_mm;
  const stepH = th - overlap_mm;

  const cols = Math.max(1, Math.ceil((width_mm - overlap_mm) / stepW));
  const rows = Math.max(1, Math.ceil((height_mm - overlap_mm) / stepH));

  const tiles = [];
  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < cols; col++) {
      const x = col * stepW;
      const y = row * stepH;
      tiles.push({
        x,
        y,
        width: Math.min(tw, width_mm - x),
        height: Math.min(th, height_mm - y),
        row,
        col,
      });
    }
  }

  return { tiles, rows, cols };
}

// --- 4.1 Print Preview ---

/**
 * Generate a print preview data structure from board state and config.
 * @param {object} boardState - { devices, routes, labels }
 * @param {object} config - Board config object
 * @returns {object} Print-ready data structure
 */
export function generatePrintPreview(boardState, config) {
  const paper = config.paper || {};
  const width_mm = paper.width_mm || 297;
  const height_mm = paper.height_mm || 210;
  const margins = paper.margin_mm || { top: 10, bottom: 10, left: 10, right: 10 };
  const exportCfg = config.export || {};
  const gridCfg = config.grid || {};
  const tick_mm = gridCfg.border_tick_mm || 50;

  // Title block
  const titleBlock = (exportCfg.include_title_block !== false && config.title_block && config.title_block.show !== false)
    ? generateTitleBlock(config)
    : null;

  // Border frame
  const borderFrame = generateBorderFrame(width_mm, height_mm, margins, tick_mm);

  // Fold marks
  const foldMarks = exportCfg.include_fold_marks
    ? generateFoldMarks(paper.size || 'A4', width_mm, height_mm)
    : null;

  // Devices, routes, labels from board state (pass through, no grid/selection)
  const devices = (boardState && boardState.devices) || [];
  const routes = (boardState && boardState.routes) || [];
  const labels = (boardState && boardState.labels) || [];

  return {
    paper: { width_mm, height_mm },
    margins,
    titleBlock,
    borderFrame,
    foldMarks,
    devices,
    routes,
    labels,
  };
}

// --- 4.2 SVG Export ---

/**
 * Export print preview as SVG string.
 * @param {object} printPreview - Output from generatePrintPreview
 * @param {object} [options] - { monochrome: boolean }
 * @returns {object} { content: string, width_mm, height_mm }
 */
export function exportSVG(printPreview, options = {}) {
  const { paper, margins, titleBlock, borderFrame, foldMarks, devices, routes, labels } = printPreview;
  const { width_mm, height_mm } = paper;
  const mono = options.monochrome || false;

  const parts = [];

  // SVG header
  parts.push(`<svg xmlns="http://www.w3.org/2000/svg" width="${width_mm}mm" height="${height_mm}mm" viewBox="0 0 ${width_mm} ${height_mm}">`);

  // Clip to paper boundary
  parts.push(`<defs><clipPath id="paper-clip"><rect x="0" y="0" width="${width_mm}" height="${height_mm}"/></clipPath></defs>`);
  parts.push(`<g clip-path="url(#paper-clip)">`);

  // Border frame
  if (borderFrame) {
    const { rect, ticks } = borderFrame;
    const stroke = mono ? toMonochrome('#000000') : '#000000';
    parts.push(`<rect x="${rect.x}" y="${rect.y}" width="${rect.w}" height="${rect.h}" fill="none" stroke="${stroke}" stroke-width="0.5"/>`);
    for (const tick of ticks) {
      parts.push(`<line x1="${tick.x1}" y1="${tick.y1}" x2="${tick.x2}" y2="${tick.y2}" stroke="${stroke}" stroke-width="0.25"/>`);
    }
  }

  // Fold marks
  if (foldMarks) {
    const stroke = mono ? toMonochrome('#666666') : '#666666';
    for (const mark of foldMarks.marks) {
      if (mark.type === 'fold-line') {
        parts.push(`<circle cx="${mark.x}" cy="${mark.y}" r="1" fill="none" stroke="${stroke}" stroke-width="0.25" stroke-dasharray="2 2"/>`);
      } else if (mark.type === 'cut-mark') {
        parts.push(`<line x1="${mark.x - 2}" y1="${mark.y}" x2="${mark.x + 2}" y2="${mark.y}" stroke="${stroke}" stroke-width="0.25"/>`);
      } else {
        parts.push(`<circle cx="${mark.x}" cy="${mark.y}" r="0.5" fill="${stroke}"/>`);
      }
    }
  }

  // Devices
  for (const dev of devices) {
    const fill = mono ? toMonochrome(dev.fill || '#ffffff') : (dev.fill || '#ffffff');
    const stroke = mono ? toMonochrome(dev.stroke || '#000000') : (dev.stroke || '#000000');
    parts.push(`<rect x="${dev.x}" y="${dev.y}" width="${dev.width || 10}" height="${dev.height || 10}" fill="${fill}" stroke="${stroke}" stroke-width="0.3"/>`);
  }

  // Routes
  for (const route of routes) {
    const stroke = mono ? toMonochrome(route.color || '#007C3D') : (route.color || '#007C3D');
    if (route.points && route.points.length >= 2) {
      const d = route.points.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x} ${p.y}`).join(' ');
      parts.push(`<path d="${d}" fill="none" stroke="${stroke}" stroke-width="0.3"/>`);
    }
  }

  // Labels
  for (const label of labels) {
    const fill = mono ? toMonochrome(label.color || '#000000') : (label.color || '#000000');
    parts.push(`<text x="${label.x}" y="${label.y}" font-size="${label.fontSize || 3}" fill="${fill}">${escapeXml(label.text || '')}</text>`);
  }

  // Title block
  if (titleBlock) {
    const stroke = mono ? toMonochrome('#000000') : '#000000';
    parts.push(`<rect x="${titleBlock.x}" y="${titleBlock.y}" width="${titleBlock.width}" height="${titleBlock.height}" fill="none" stroke="${stroke}" stroke-width="0.4"/>`);
    for (const field of titleBlock.fields) {
      parts.push(`<text x="${field.x}" y="${field.y}" font-size="2.5" fill="${stroke}">${escapeXml(field.label)}: ${escapeXml(field.value)}</text>`);
    }
  }

  parts.push(`</g>`);
  parts.push(`</svg>`);

  return {
    content: parts.join('\n'),
    width_mm,
    height_mm,
  };
}

/**
 * Escape XML special characters.
 */
function escapeXml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

// --- 4.3 PNG Export Metadata ---

/**
 * Calculate PNG export metadata (dimensions, DPI).
 * @param {object} printPreview - Output from generatePrintPreview
 * @param {object} [options] - { dpi: number }
 * @returns {object} { width_px, height_px, dpi, scale, viewBox }
 */
export function exportPNGMeta(printPreview, options = {}) {
  const { paper } = printPreview;
  const dpi = options.dpi || 300;
  const { width_mm, height_mm } = paper;

  // 1 inch = 25.4 mm
  const width_px = Math.round((width_mm / 25.4) * dpi);
  const height_px = Math.round((height_mm / 25.4) * dpi);
  const scale = dpi / 25.4; // pixels per mm

  return {
    width_px,
    height_px,
    dpi,
    scale,
    viewBox: `0 0 ${width_mm} ${height_mm}`,
  };
}
