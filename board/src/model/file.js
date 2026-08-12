/**
 * Components Board — File Model
 * Phase 2, Task 2.1: Parse/load/save Components:circuit + Components:board + Components:command
 *
 * OWNERSHIP SPLIT (Phase A):
 * ─────────────────────────────────────────────────────────────────────────────
 * This file contains parsing for BOTH circuit and board syntax.
 * Board only owns the board parsing (place/route/label/paper).
 * Circuit parsing (device/connect) exists here ONLY because engine-mock.js
 * imports it. When the real engine replaces the mock (Phase B), all circuit
 * parsing functions will be dead code and can be removed from this file.
 *
 * Sections marked below:
 *   CIRCUIT PARSING (engine-mock only) — Do NOT use from Board code
 *   BOARD PARSING (Board owns)         — Board's canonical syntax
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * Three project files:
 *   Components:circuit  — electrical truth (devices, nets, connections)
 *   Components:board    — visual layout (placements, routes, labels)
 *   Components:command  — command history/log
 *
 * Each file is plain text with @page sections.
 * Pure functions, no side effects, no DOM.
 * ES module syntax, Node.js compatible.
 */

// =============================================================================
// FILE TYPES
// =============================================================================

export const FILE_TYPES = Object.freeze({
  CIRCUIT: 'circuit',
  BOARD: 'board',
  COMMAND: 'command',
});

// Canonical file names
export const FILE_NAMES = Object.freeze({
  [FILE_TYPES.CIRCUIT]: 'Components:circuit',
  [FILE_TYPES.BOARD]: 'Components:board',
  [FILE_TYPES.COMMAND]: 'Components:command',
});

// =============================================================================
// LINE TYPES (for syntax identification)
// =============================================================================

export const LINE_TYPES = Object.freeze({
  PAGE: 'page',
  DEVICE: 'device',
  CONNECT: 'connect',
  PAPER: 'paper',
  PLACE: 'place',
  ROUTE: 'route',
  LABEL: 'label',
  COMMAND_ENTRY: 'command-entry',
  COMMENT: 'comment',
  BLANK: 'blank',
  UNKNOWN: 'unknown',
});

// =============================================================================
// PARSING — SHARED (dispatches to circuit/board/command parsers)
// =============================================================================

/**
 * Parse a file into a structured model with pages.
 * @param {string} text — raw file content
 * @param {string} fileType — one of FILE_TYPES
 * @returns {object} { type, pages: [{ name, startLine, endLine, lines: [...] }], raw }
 */
export function parseFile(text, fileType) {
  const rawLines = text.split('\n');
  const pages = [];
  let currentPage = null;

  for (let i = 0; i < rawLines.length; i++) {
    const raw = rawLines[i];
    const trimmed = raw.trim();

    // Detect @page directive
    const pageMatch = trimmed.match(/^@page\s+(.+)$/);
    if (pageMatch) {
      // Close previous page
      if (currentPage) {
        currentPage.endLine = i - 1;
        pages.push(currentPage);
      }
      currentPage = {
        name: pageMatch[1].trim(),
        startLine: i,
        endLine: -1,
        lines: [],
      };
      continue;
    }

    // Lines before any @page go into a default page
    if (!currentPage) {
      currentPage = {
        name: '',
        startLine: 0,
        endLine: -1,
        lines: [],
      };
    }

    currentPage.lines.push({
      lineNumber: i,
      raw,
      parsed: parseLine(trimmed, fileType),
    });
  }

  // Close final page
  if (currentPage) {
    currentPage.endLine = rawLines.length - 1;
    pages.push(currentPage);
  }

  return {
    type: fileType,
    pages,
    raw: text,
    lineCount: rawLines.length,
  };
}

// =============================================================================
// LINE PARSING (dispatcher)
// =============================================================================

/**
 * Parse a single trimmed line based on file type.
 * @param {string} line — trimmed line content
 * @param {string} fileType
 * @returns {object} { type, ...parsed fields }
 */
export function parseLine(line, fileType) {
  if (line === '') return { type: LINE_TYPES.BLANK };
  if (line.startsWith('//') || line.startsWith('#')) {
    return { type: LINE_TYPES.COMMENT, text: line.slice(line.startsWith('//') ? 2 : 1).trim() };
  }

  switch (fileType) {
    case FILE_TYPES.CIRCUIT: return parseCircuitLine(line);
    case FILE_TYPES.BOARD: return parseBoardLine(line);
    case FILE_TYPES.COMMAND: return parseCommandLine(line);
    default: return { type: LINE_TYPES.UNKNOWN, text: line };
  }
}

// =============================================================================
// === CIRCUIT PARSING (engine-mock only) ======================================
// =============================================================================
// These functions parse Components:circuit syntax (device/connect).
// Board does NOT own this syntax — it belongs to the engine.
// Present here only because engine-mock.js imports parseFile + serialize helpers.
// Remove when real engine replaces engine-mock.js (Phase B).
// =============================================================================

/**
 * Parse a circuit file line.
 * Syntax:
 *   device U1, digital.74HC04;
 *   connect U1.1Y -> U2.CLK;
 */
function parseCircuitLine(line) {
  // Remove trailing semicolons for parsing
  const cleaned = line.endsWith(';') ? line.slice(0, -1).trim() : line;

  // device REF, PART
  const deviceMatch = cleaned.match(/^device\s+(\S+)\s*,\s*(.+)$/);
  if (deviceMatch) {
    return {
      type: LINE_TYPES.DEVICE,
      ref: deviceMatch[1],
      part: deviceMatch[2].trim(),
    };
  }

  // instance REF, TYPE — treated as a device for rendering
  const instanceMatch = cleaned.match(/^instance\s+(\S+)\s*,\s*(.+)$/);
  if (instanceMatch) {
    return {
      type: LINE_TYPES.DEVICE,
      ref: instanceMatch[1],
      part: instanceMatch[2].trim(),
    };
  }

  // connect FROM -> TO
  const connectMatch = cleaned.match(/^connect\s+(\S+)\s*->\s*(\S+)$/);
  if (connectMatch) {
    return {
      type: LINE_TYPES.CONNECT,
      from: connectMatch[1],
      to: connectMatch[2],
    };
  }

  return { type: LINE_TYPES.UNKNOWN, text: line };
}

/**
 * Serialize a device statement.
 * (engine-mock only — Board does not use)
 */
export function serializeDevice(ref, part) {
  return `device ${ref}, ${part};`;
}

/**
 * Serialize a connection statement.
 * (engine-mock only — Board does not use)
 */
export function serializeConnect(from, to) {
  return `connect ${from} -> ${to};`;
}

/**
 * Serialize a full circuit file from pages data.
 * (engine-mock only — Board does not use)
 * @param {Array<{name: string, statements: Array}>} pages
 * @returns {string}
 */
export function serializeCircuitFile(pages) {
  const parts = [];
  for (const page of pages) {
    if (page.name) parts.push(`@page ${page.name}`);
    for (const stmt of page.statements) {
      switch (stmt.type) {
        case 'device':
          parts.push(serializeDevice(stmt.ref, stmt.part));
          break;
        case 'connect':
          parts.push(serializeConnect(stmt.from, stmt.to));
          break;
        default:
          if (stmt.raw) parts.push(stmt.raw);
          break;
      }
    }
    parts.push(''); // blank line between pages
  }
  return parts.join('\n').replace(/\n{3,}/g, '\n\n').trim() + '\n';
}

/**
 * Find line number of a device declaration by ref.
 * (engine-mock only — Board does not use)
 * @param {object} file — parsed circuit file
 * @param {string} ref — device reference (e.g. 'U1')
 * @returns {number} 0-based line number, or -1 if not found
 */
export function findDeviceLine(file, ref) {
  for (const page of file.pages) {
    for (const line of page.lines) {
      if (line.parsed.type === LINE_TYPES.DEVICE && line.parsed.ref === ref) {
        return line.lineNumber;
      }
    }
  }
  return -1;
}

/**
 * Find which page a device belongs to.
 * (engine-mock only — Board does not use)
 * @param {object} file — parsed circuit file
 * @param {string} ref
 * @returns {string|null} page name or null
 */
export function findDevicePage(file, ref) {
  for (const page of file.pages) {
    for (const line of page.lines) {
      if (line.parsed.type === LINE_TYPES.DEVICE && line.parsed.ref === ref) {
        return page.name;
      }
    }
  }
  return null;
}

// =============================================================================
// === BOARD PARSING (Board owns) ==============================================
// =============================================================================
// These functions parse Components:board syntax (paper/place/route/label).
// This is Board's canonical file format.
// =============================================================================

/**
 * Parse a board file line.
 * Syntax:
 *   paper A4 landscape;
 *   place U1 at (50, 30) rotate 0;
 *   route U1.1Y -> U2.CLK via (85, 30) (85, 45) (120, 45);
 *   label "VCC" at (10, 90);
 */
function parseBoardLine(line) {
  const cleaned = line.endsWith(';') ? line.slice(0, -1).trim() : line;

  // paper SIZE ORIENTATION
  const paperMatch = cleaned.match(/^paper\s+(\S+)\s*(landscape|portrait)?$/i);
  if (paperMatch) {
    return {
      type: LINE_TYPES.PAPER,
      size: paperMatch[1],
      orientation: (paperMatch[2] || 'landscape').toLowerCase(),
    };
  }

  // place REF at (X, Y) rotate ANGLE
  const placeMatch = cleaned.match(
    /^place\s+(\S+)\s+at\s*\(\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\)\s*(?:rotate\s+(\d+))?$/
  );
  if (placeMatch) {
    return {
      type: LINE_TYPES.PLACE,
      ref: placeMatch[1],
      x: parseFloat(placeMatch[2]),
      y: parseFloat(placeMatch[3]),
      rotation: placeMatch[4] ? parseInt(placeMatch[4], 10) : 0,
    };
  }

  // route FROM -> TO via (x,y) (x,y) ...
  const routeMatch = cleaned.match(/^route\s+(\S+)\s*->\s*(\S+)\s+via\s+(.+)$/);
  if (routeMatch) {
    const points = [];
    const pointRegex = /\(\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\)/g;
    let m;
    while ((m = pointRegex.exec(routeMatch[3])) !== null) {
      points.push({ x: parseFloat(m[1]), y: parseFloat(m[2]) });
    }
    return {
      type: LINE_TYPES.ROUTE,
      from: routeMatch[1],
      to: routeMatch[2],
      via: points,
    };
  }

  // label "TEXT" at (X, Y)
  const labelMatch = cleaned.match(/^label\s+"([^"]+)"\s+at\s*\(\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\)$/);
  if (labelMatch) {
    return {
      type: LINE_TYPES.LABEL,
      text: labelMatch[1],
      x: parseFloat(labelMatch[2]),
      y: parseFloat(labelMatch[3]),
    };
  }

  return { type: LINE_TYPES.UNKNOWN, text: line };
}

/**
 * Serialize a paper statement.
 */
export function serializePaper(size, orientation) {
  return `paper ${size} ${orientation};`;
}

/**
 * Serialize a placement statement.
 */
export function serializePlace(ref, x, y, rotation = 0) {
  return `place ${ref} at (${x}, ${y}) rotate ${rotation};`;
}

/**
 * Serialize a route statement.
 */
export function serializeRoute(from, to, via) {
  const pts = via.map(p => `(${p.x}, ${p.y})`).join(' ');
  return `route ${from} -> ${to} via ${pts};`;
}

/**
 * Serialize a label statement.
 */
export function serializeLabel(text, x, y) {
  return `label "${text}" at (${x}, ${y});`;
}

/**
 * Serialize a full board file from pages data.
 * @param {Array<{name: string, statements: Array}>} pages
 * @returns {string}
 */
export function serializeBoardFile(pages) {
  const parts = [];
  for (const page of pages) {
    if (page.name) parts.push(`@page ${page.name}`);
    for (const stmt of page.statements) {
      switch (stmt.type) {
        case 'paper':
          parts.push(serializePaper(stmt.size, stmt.orientation));
          break;
        case 'place':
          parts.push(serializePlace(stmt.ref, stmt.x, stmt.y, stmt.rotation));
          break;
        case 'route':
          parts.push(serializeRoute(stmt.from, stmt.to, stmt.via));
          break;
        case 'label':
          parts.push(serializeLabel(stmt.text, stmt.x, stmt.y));
          break;
        default:
          if (stmt.raw) parts.push(stmt.raw);
          break;
      }
    }
    parts.push('');
  }
  return parts.join('\n').replace(/\n{3,}/g, '\n\n').trim() + '\n';
}

/**
 * Find line number of a placement by ref.
 * @param {object} file — parsed board file
 * @param {string} ref
 * @returns {number} 0-based line number, or -1
 */
export function findPlacementLine(file, ref) {
  for (const page of file.pages) {
    for (const line of page.lines) {
      if (line.parsed.type === LINE_TYPES.PLACE && line.parsed.ref === ref) {
        return line.lineNumber;
      }
    }
  }
  return -1;
}

// =============================================================================
// === COMMAND PARSING (shared utility) ========================================
// =============================================================================

/**
 * Parse a command log line.
 * Syntax:
 *   [HH:MM:SS] command text
 *   > user input
 */
function parseCommandLine(line) {
  // Timestamped entry: [12:01:30] place U1 at (50, 30)
  const tsMatch = line.match(/^\[(\d{2}:\d{2}(?::\d{2})?)\]\s*(.+)$/);
  if (tsMatch) {
    return {
      type: LINE_TYPES.COMMAND_ENTRY,
      timestamp: tsMatch[1],
      command: tsMatch[2],
    };
  }

  // User input: > place U1 at (50, 30)
  const inputMatch = line.match(/^>\s*(.*)$/);
  if (inputMatch) {
    return {
      type: LINE_TYPES.COMMAND_ENTRY,
      timestamp: null,
      command: inputMatch[1],
    };
  }

  return { type: LINE_TYPES.UNKNOWN, text: line };
}

/**
 * Serialize a command log file.
 * @param {Array<{timestamp: string|null, command: string}>} entries
 * @returns {string}
 */
export function serializeCommandFile(entries) {
  return entries
    .map(e => e.timestamp ? `[${e.timestamp}] ${e.command}` : `> ${e.command}`)
    .join('\n') + '\n';
}

// =============================================================================
// PAGE UTILITIES
// =============================================================================

/**
 * Get all page names from a parsed file.
 * @param {object} file — parsed file model
 * @returns {string[]}
 */
export function getPageNames(file) {
  return file.pages.map(p => p.name).filter(n => n !== '');
}

/**
 * Find page by name. Returns page object or null.
 * @param {object} file
 * @param {string} name
 * @returns {object|null}
 */
export function getPage(file, name) {
  return file.pages.find(p => p.name === name) || null;
}

/**
 * Get the line offset (0-based) where a page starts.
 * Returns the line AFTER the @page directive (first content line).
 * @param {object} file
 * @param {string} pageName
 * @returns {number} line number, or -1 if not found
 */
export function getPageOffset(file, pageName) {
  const page = getPage(file, pageName);
  if (!page) return -1;
  // startLine is the @page line itself; content starts at startLine + 1
  return page.startLine;
}

/**
 * Get line range for a page (inclusive).
 * @param {object} file
 * @param {string} pageName
 * @returns {{start: number, end: number}|null}
 */
export function getPageRange(file, pageName) {
  const page = getPage(file, pageName);
  if (!page) return null;
  return { start: page.startLine, end: page.endLine };
}
