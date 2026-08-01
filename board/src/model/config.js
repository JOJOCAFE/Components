/**
 * Components Board — Config Model
 * Task 1.1: board-config.json schema and JSON read/write module
 *
 * Pure functions, no side effects, no DOM.
 * ES module syntax, Node.js compatible.
 */

// ISO 216 paper sizes in mm (landscape: width > height)
export const PAPER_SIZES = Object.freeze({
  A4: { width_mm: 297, height_mm: 210 },
  A3: { width_mm: 420, height_mm: 297 },
  A2: { width_mm: 594, height_mm: 420 },
  A1: { width_mm: 841, height_mm: 594 },
  A0: { width_mm: 1189, height_mm: 841 },
});

export const VALID_PAPER_SIZES = Object.keys(PAPER_SIZES);
export const VALID_ORIENTATIONS = ['landscape', 'portrait'];
export const VALID_EXPORT_FORMATS = ['pdf', 'png', 'svg'];
export const SCHEMA_ID = 'components.board-config@1';

export const DEFAULT_CONFIG = Object.freeze({
  schema: SCHEMA_ID,
  paper: {
    size: 'A4',
    width_mm: 297,
    height_mm: 210,
    orientation: 'landscape',
    margin_mm: { top: 10, bottom: 10, left: 10, right: 10 },
  },
  grid: {
    major_mm: 10,
    minor_mm: 2.5,
    snap_mm: 1.25,
    border_tick_mm: 50,
  },
  title_block: {
    show: true,
    project: '',
    page_title: '',
    author: '',
    revision: '1.0',
  },
  export: {
    dpi: 300,
    format: 'pdf',
    monochrome: false,
    include_title_block: true,
    include_fold_marks: false,
  },
  print: {
    scale: '1:1',
    tile_to: 'A4',
    overlap_mm: 15,
  },
});

/**
 * Validate a config object strictly.
 * @param {object} config
 * @returns {{valid: boolean, errors: string[]}}
 */
export function validateConfig(config) {
  const errors = [];

  if (!config || typeof config !== 'object') {
    errors.push('Config must be a non-null object');
    return { valid: false, errors };
  }

  // Schema
  if (config.schema !== SCHEMA_ID) {
    errors.push(`Invalid or missing schema: expected "${SCHEMA_ID}", got "${config.schema}"`);
  }

  // Paper section
  if (!config.paper || typeof config.paper !== 'object') {
    errors.push('Missing "paper" section');
  } else {
    if (!VALID_PAPER_SIZES.includes(config.paper.size)) {
      errors.push(`Invalid paper size "${config.paper.size}". Valid: ${VALID_PAPER_SIZES.join(', ')}`);
    }
    if (!VALID_ORIENTATIONS.includes(config.paper.orientation)) {
      errors.push(`Invalid orientation "${config.paper.orientation}". Valid: ${VALID_ORIENTATIONS.join(', ')}`);
    }
    if (!Number.isFinite(config.paper.width_mm) || config.paper.width_mm <= 0) {
      errors.push('paper.width_mm must be a positive finite number');
    }
    if (!Number.isFinite(config.paper.height_mm) || config.paper.height_mm <= 0) {
      errors.push('paper.height_mm must be a positive finite number');
    }

    // Margins
    if (!config.paper.margin_mm || typeof config.paper.margin_mm !== 'object') {
      errors.push('Missing "paper.margin_mm" section');
    } else {
      for (const side of ['top', 'bottom', 'left', 'right']) {
        const val = config.paper.margin_mm[side];
        if (!Number.isFinite(val) || val < 0) {
          errors.push(`paper.margin_mm.${side} must be a non-negative finite number, got ${val}`);
        }
      }
    }
  }

  // Grid section
  if (!config.grid || typeof config.grid !== 'object') {
    errors.push('Missing "grid" section');
  } else {
    for (const key of ['major_mm', 'minor_mm', 'snap_mm', 'border_tick_mm']) {
      if (!Number.isFinite(config.grid[key]) || config.grid[key] <= 0) {
        errors.push(`grid.${key} must be a positive finite number`);
      }
    }
  }

  // Title block section
  if (!config.title_block || typeof config.title_block !== 'object') {
    errors.push('Missing "title_block" section');
  } else {
    if (typeof config.title_block.show !== 'boolean') {
      errors.push('title_block.show must be a boolean');
    }
    for (const key of ['project', 'page_title', 'author', 'revision']) {
      if (typeof config.title_block[key] !== 'string') {
        errors.push(`title_block.${key} must be a string`);
      }
    }
  }

  // Export section
  if (!config.export || typeof config.export !== 'object') {
    errors.push('Missing "export" section');
  } else {
    if (!Number.isFinite(config.export.dpi) || config.export.dpi <= 0) {
      errors.push('export.dpi must be a positive finite number');
    }
    if (!VALID_EXPORT_FORMATS.includes(config.export.format)) {
      errors.push(`Invalid export format "${config.export.format}". Valid: ${VALID_EXPORT_FORMATS.join(', ')}`);
    }
    if (typeof config.export.monochrome !== 'boolean') {
      errors.push('export.monochrome must be a boolean');
    }
    if (typeof config.export.include_title_block !== 'boolean') {
      errors.push('export.include_title_block must be a boolean');
    }
    if (typeof config.export.include_fold_marks !== 'boolean') {
      errors.push('export.include_fold_marks must be a boolean');
    }
  }

  // Print section
  if (!config.print || typeof config.print !== 'object') {
    errors.push('Missing "print" section');
  } else {
    if (typeof config.print.scale !== 'string') {
      errors.push('print.scale must be a string');
    }
    if (!VALID_PAPER_SIZES.includes(config.print.tile_to)) {
      errors.push(`Invalid print.tile_to "${config.print.tile_to}". Valid: ${VALID_PAPER_SIZES.join(', ')}`);
    }
    if (!Number.isFinite(config.print.overlap_mm) || config.print.overlap_mm < 0) {
      errors.push('print.overlap_mm must be a non-negative finite number');
    }
  }

  return { valid: errors.length === 0, errors };
}

/**
 * Deep clone helper (structured clone alternative for plain objects).
 */
function deepClone(obj) {
  return JSON.parse(JSON.stringify(obj));
}

/**
 * Deep merge source into target (target is mutated).
 */
function deepMerge(target, source) {
  for (const key of Object.keys(source)) {
    if (
      source[key] !== null &&
      typeof source[key] === 'object' &&
      !Array.isArray(source[key]) &&
      typeof target[key] === 'object' &&
      target[key] !== null
    ) {
      deepMerge(target[key], source[key]);
    } else {
      target[key] = source[key];
    }
  }
  return target;
}

/**
 * Create a config object with defaults merged with overrides.
 * If paper.size is overridden, dimensions auto-adjust from PAPER_SIZES.
 * @param {object} [overrides]
 * @returns {object}
 */
export function createConfig(overrides = {}) {
  const config = deepClone(DEFAULT_CONFIG);
  deepMerge(config, deepClone(overrides));

  // Auto-adjust dimensions when paper size changes
  if (overrides.paper && overrides.paper.size && PAPER_SIZES[config.paper.size]) {
    const dims = PAPER_SIZES[config.paper.size];
    // Only auto-set if user didn't explicitly provide dimensions
    if (!overrides.paper.width_mm) {
      config.paper.width_mm = dims.width_mm;
    }
    if (!overrides.paper.height_mm) {
      config.paper.height_mm = dims.height_mm;
    }
  }

  // Apply orientation swap if needed
  if (config.paper.orientation === 'portrait') {
    const w = config.paper.width_mm;
    const h = config.paper.height_mm;
    config.paper.width_mm = Math.min(w, h);
    config.paper.height_mm = Math.max(w, h);
  } else {
    const w = config.paper.width_mm;
    const h = config.paper.height_mm;
    config.paper.width_mm = Math.max(w, h);
    config.paper.height_mm = Math.min(w, h);
  }

  return config;
}

/**
 * Parse JSON string, validate, return config or throw.
 * @param {string} jsonString
 * @returns {object}
 * @throws {Error} on parse or validation failure
 */
export function loadConfig(jsonString) {
  let parsed;
  try {
    parsed = JSON.parse(jsonString);
  } catch (err) {
    throw new Error(`Config JSON parse error: ${err.message}`);
  }

  const { valid, errors } = validateConfig(parsed);
  if (!valid) {
    throw new Error(`Config validation failed:\n  - ${errors.join('\n  - ')}`);
  }

  return parsed;
}

/**
 * Validate and serialize config to JSON string.
 * @param {object} config
 * @returns {string}
 * @throws {Error} on validation failure
 */
export function saveConfig(config) {
  const { valid, errors } = validateConfig(config);
  if (!valid) {
    throw new Error(`Cannot save invalid config:\n  - ${errors.join('\n  - ')}`);
  }

  return JSON.stringify(config, null, 2);
}

/**
 * Get effective paper dimensions accounting for orientation.
 * @param {object} config
 * @returns {{width_mm: number, height_mm: number}}
 */
export function getPaperDimensions(config) {
  const dims = PAPER_SIZES[config.paper.size];
  if (!dims) {
    throw new Error(`Unknown paper size: ${config.paper.size}`);
  }

  if (config.paper.orientation === 'portrait') {
    return {
      width_mm: Math.min(dims.width_mm, dims.height_mm),
      height_mm: Math.max(dims.width_mm, dims.height_mm),
    };
  }

  // landscape (default)
  return {
    width_mm: Math.max(dims.width_mm, dims.height_mm),
    height_mm: Math.min(dims.width_mm, dims.height_mm),
  };
}
