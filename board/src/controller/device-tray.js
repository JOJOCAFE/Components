/**
 * Components Board — Device Tray Controller
 * 
 * The Project Tray is a working set of parts for the current project.
 * Operations:
 *   add(part, qty)   — add device from library to tray
 *   remove(part)     — remove from tray
 *   pickup(part)     — pick up a part (enter placement mode)
 *   place(part, pos) — place on board at position (or auto-find location)
 *
 * Auto-placement: if no position given, finds first free spot.
 * If default position occupied, shifts right/down until clear.
 *
 * Library tree: groups → members (mirrors lib/standard/ structure)
 * Definitions in lib/ map to board assets (SVG chip frames).
 *
 * DOM-free. Pure state management.
 * ES module syntax, Node.js compatible.
 */

// =============================================================================
// REF PREFIX MAP
// =============================================================================

const REF_PREFIX_MAP = Object.freeze({
  '74xx': 'U',
  memory: 'U',
  support: 'U',
  discrete: 'Q',
  passive: 'R',
  virtual: 'X',
});

const ROLE_PREFIX = Object.freeze({
  resistor: 'R',
  capacitor: 'C',
  led: 'D',
  crystal: 'Y',
  oscillator: 'Y',
});

// =============================================================================
// AUTO-PLACEMENT
// =============================================================================

// Default placement grid (2.54mm = breadboard pitch, chips spaced wider)
const GRID = 2.54;
const CHIP_SPACING_X = 25;  // mm between chips horizontally
const CHIP_SPACING_Y = 20;  // mm between chips vertically
const START_X = 30;
const START_Y = 40;
const MAX_COLS = 8;  // wrap after this many columns

/**
 * Find next available position that doesn't overlap existing placements.
 * Scans grid positions left→right, top→bottom.
 *
 * @param {object} existingPlacements — { ref: { x, y, rotation } }
 * @param {number} [pinCount=14] — used to estimate chip size
 * @returns {{ x: number, y: number }}
 */
export function findNextFreePosition(existingPlacements, pinCount = 14) {
  const occupied = new Set();
  // Build a set of occupied grid cells (quantized to chip spacing)
  for (const p of Object.values(existingPlacements || {})) {
    const col = Math.round((p.x - START_X) / CHIP_SPACING_X);
    const row = Math.round((p.y - START_Y) / CHIP_SPACING_Y);
    occupied.add(`${col},${row}`);
  }

  // Scan for first free cell
  for (let row = 0; row < 50; row++) {
    for (let col = 0; col < MAX_COLS; col++) {
      if (!occupied.has(`${col},${row}`)) {
        return {
          x: START_X + col * CHIP_SPACING_X,
          y: START_Y + row * CHIP_SPACING_Y,
        };
      }
    }
  }
  // Fallback (very full board)
  return { x: START_X, y: START_Y + 50 * CHIP_SPACING_Y };
}

/**
 * Snap a position to grid.
 * @param {{ x: number, y: number }} pos
 * @returns {{ x: number, y: number }}
 */
export function snapToGrid(pos) {
  return {
    x: Math.round(pos.x / GRID) * GRID,
    y: Math.round(pos.y / GRID) * GRID,
  };
}

// =============================================================================
// DEVICE TRAY FACTORY
// =============================================================================

/**
 * Create a device tray instance.
 *
 * @param {object} options
 * @param {object} options.library — library instance (from createLibrary)
 * @param {object} [options.executor] — executor instance (optional)
 * @returns {object} device tray API
 */
export function createDeviceTray(options = {}) {
  const { library, executor } = options;

  /**
   * Tray items: Map<part, { part, quantity, group, title, pinCount, placed: [] }>
   */
  const items = new Map();

  /** Ref counters: Map<prefix, number> */
  const refCounters = new Map();

  /** Currently picked-up part (null = not in placement mode) */
  let pickedUp = null;

  // ---------------------------------------------------------------------------
  // REF GENERATION
  // ---------------------------------------------------------------------------

  function getRefPrefix(entry) {
    if (entry && entry.role) {
      for (const [pattern, prefix] of Object.entries(ROLE_PREFIX)) {
        if (entry.role.toLowerCase().includes(pattern)) return prefix;
      }
    }
    if (entry && entry.part) {
      const p = entry.part.toLowerCase();
      if (p.includes('led')) return 'D';
      if (p.includes('resistor')) return 'R';
      if (p.includes('capacitor')) return 'C';
      if (p.includes('crystal') || p.includes('oscillator')) return 'Y';
    }
    return REF_PREFIX_MAP[entry?.group] || 'U';
  }

  function nextRef(prefix) {
    const n = (refCounters.get(prefix) || 0) + 1;
    refCounters.set(prefix, n);
    return `${prefix}${n}`;
  }

  // ---------------------------------------------------------------------------
  // ADD / REMOVE
  // ---------------------------------------------------------------------------

  /**
   * Add a device from library to the tray.
   * @param {string} part — part identifier
   * @param {number} [quantity=1]
   * @returns {object} { success, item?, error? }
   */
  function addToTray(part, quantity = 1) {
    if (quantity < 1) return { success: false, error: 'Quantity must be at least 1' };

    let entry = library ? library.getByPart(part) : null;

    if (items.has(part)) {
      const item = items.get(part);
      const updated = { ...item, quantity: item.quantity + quantity };
      items.set(part, updated);
      return { success: true, item: frozen(updated) };
    }

    const newItem = {
      part,
      quantity,
      group: entry?.group || 'unknown',
      title: entry?.title || part,
      pinCount: entry?.pinCount || 0,
      placed: [],
    };
    items.set(part, newItem);
    return { success: true, item: frozen(newItem) };
  }

  /**
   * Remove a part from the tray entirely.
   * @param {string} part
   * @returns {object} { success, error? }
   */
  function removeFromTray(part) {
    if (!items.has(part)) return { success: false, error: `Part "${part}" not in tray` };
    items.delete(part);
    if (pickedUp === part) pickedUp = null;
    return { success: true };
  }

  /**
   * Reduce quantity.
   * @param {string} part
   * @param {number} [amount=1]
   * @returns {object} { success, remaining?, error? }
   */
  function reduceQuantity(part, amount = 1) {
    if (!items.has(part)) return { success: false, error: `Part "${part}" not in tray` };
    const item = items.get(part);
    const remaining = item.quantity - amount;
    if (remaining <= 0) { items.delete(part); return { success: true, remaining: 0 }; }
    items.set(part, { ...item, quantity: remaining });
    return { success: true, remaining };
  }

  /**
   * Set exact quantity.
   * @param {string} part
   * @param {number} quantity
   * @returns {object} { success, error? }
   */
  function setQuantity(part, quantity) {
    if (!items.has(part)) return { success: false, error: `Part "${part}" not in tray` };
    if (quantity < 1) { items.delete(part); return { success: true }; }
    items.set(part, { ...items.get(part), quantity });
    return { success: true };
  }

  // ---------------------------------------------------------------------------
  // PICKUP / PLACE
  // ---------------------------------------------------------------------------

  /**
   * Pick up a part from the tray (enter placement mode).
   * The UI shows the part following the cursor until placed.
   * @param {string} part
   * @returns {object} { success, part?, error? }
   */
  function pickup(part) {
    if (!items.has(part)) return { success: false, error: `Part "${part}" not in tray. Add it first.` };
    if (deviceTrayRemainingCount(part) <= 0) return { success: false, error: `All ${part} already placed` };
    pickedUp = part;
    return { success: true, part };
  }

  /**
   * Cancel pickup (drop without placing).
   */
  function cancelPickup() {
    pickedUp = null;
  }

  /**
   * Get currently picked-up part (null if not in placement mode).
   * @returns {string|null}
   */
  function getPickedUp() {
    return pickedUp;
  }

  /**
   * Place a part on the board.
   * - If pos given: place at pos (snapped to grid)
   * - If no pos: auto-find next free position
   * - If default position occupied: shift to next free spot
   *
   * @param {string} part
   * @param {object} [pos] — { x, y } position in mm (optional)
   * @param {object} [opts]
   * @param {number} [opts.rotation=0]
   * @param {string} [opts.ref] — override auto-ref
   * @returns {object} { success, ref?, command?, error? }
   */
  function placeFromTray(part, pos, opts = {}) {
    const { rotation = 0 } = opts;

    if (!items.has(part)) return { success: false, error: `Part "${part}" not in tray. Add it first.` };

    // Resolve position
    let finalPos;
    if (pos && (pos.x !== undefined && pos.y !== undefined)) {
      finalPos = snapToGrid(pos);
    } else {
      // Auto-find position based on existing placements
      const existingPlacements = executor ? executor.getState().board.placements : {};
      const item = items.get(part);
      finalPos = findNextFreePosition(existingPlacements, item.pinCount);
    }

    // Generate ref
    const entry = library ? library.getByPart(part) : null;
    const prefix = entry ? getRefPrefix(entry) : 'U';
    const ref = opts.ref || nextRef(prefix);

    // Build command
    const command = { type: 'place', ref, part, x: finalPos.x, y: finalPos.y, rotation };

    // Execute if executor provided
    if (executor) {
      const result = executor.execute(command);
      if (!result.success) return { success: false, error: result.error, command };
    }

    // Track placement
    const item = items.get(part);
    items.set(part, { ...item, placed: [...item.placed, ref] });

    // Clear pickup if this was the picked-up part
    if (pickedUp === part && deviceTrayRemainingCount(part) <= 0) {
      pickedUp = null;
    }

    return { success: true, ref, command, position: finalPos };
  }

  /**
   * Remove a placed device tracking.
   * @param {string} ref
   * @returns {object} { success, part?, error? }
   */
  function unplace(ref) {
    for (const [part, item] of items.entries()) {
      const idx = item.placed.indexOf(ref);
      if (idx >= 0) {
        const placed = [...item.placed.slice(0, idx), ...item.placed.slice(idx + 1)];
        items.set(part, { ...item, placed });
        return { success: true, part };
      }
    }
    return { success: false, error: `Ref "${ref}" not tracked in tray` };
  }

  // ---------------------------------------------------------------------------
  // QUERIES
  // ---------------------------------------------------------------------------

  function deviceTrayRemainingCount(part) {
    const item = items.get(part);
    if (!item) return 0;
    return Math.max(0, item.quantity - item.placed.length);
  }

  function getItems() {
    return Array.from(items.values()).map(frozen);
  }

  function getItem(part) {
    const item = items.get(part);
    return item ? frozen(item) : null;
  }

  function itemCount() { return items.size; }

  function totalQuantity() {
    let sum = 0;
    for (const item of items.values()) sum += item.quantity;
    return sum;
  }

  function placedCount() {
    let sum = 0;
    for (const item of items.values()) sum += item.placed.length;
    return sum;
  }

  function remainingCount(part) { return deviceTrayRemainingCount(part); }

  function clear() { items.clear(); refCounters.clear(); pickedUp = null; }

  function setRefCounters(counters) {
    refCounters.clear();
    for (const [prefix, n] of Object.entries(counters)) refCounters.set(prefix, n);
  }

  function getRefCounters() {
    const obj = {};
    for (const [prefix, n] of refCounters.entries()) obj[prefix] = n;
    return obj;
  }

  function frozen(item) {
    return Object.freeze({ ...item, placed: Object.freeze([...item.placed]) });
  }

  // ---------------------------------------------------------------------------
  // BOM (Bill of Materials)
  // ---------------------------------------------------------------------------

  /**
   * Load a BOM into the tray. Each BOM entry maps to a library part.
   * Clears existing tray items first (full BOM replace).
   *
   * BOM format (JSON array):
   *   [
   *     { "part": "74HC04", "qty": 4 },
   *     { "part": "74HC161", "qty": 4 },
   *     { "part": "AT28C256", "qty": 1 },
   *     { "part": "Resistor", "qty": 10 },
   *     { "part": "LED", "qty": 8 }
   *   ]
   *
   * Each entry:
   *   - part: must match a library part name (exact match first, then search)
   *   - qty: quantity to add (default 1)
   *   - ref (optional): override ref prefix
   *
   * @param {Array} bom — array of BOM entries
   * @param {object} [options]
   * @param {boolean} [options.clear=true] — clear tray before loading
   * @param {boolean} [options.strict=false] — fail on unknown parts
   * @returns {object} { success, loaded, skipped, errors[] }
   */
  function loadBom(bom, options = {}) {
    const { clear: doClear = true, strict = false } = options;

    if (!Array.isArray(bom)) {
      return { success: false, loaded: 0, skipped: 0, errors: ['BOM must be an array'] };
    }

    if (doClear) clear();

    let loaded = 0;
    let skipped = 0;
    const errors = [];

    for (const entry of bom) {
      if (!entry || !entry.part) {
        skipped++;
        errors.push('Entry missing "part" field');
        continue;
      }

      const part = entry.part;
      const qty = entry.qty || entry.quantity || 1;

      // Try exact match in library
      let found = library ? library.getByPart(part) : null;

      // If not found, try search (fuzzy match first result)
      if (!found && library) {
        const results = library.search(part, { limit: 1 });
        if (results.length > 0) {
          found = results[0];
        }
      }

      if (!found && strict) {
        skipped++;
        errors.push(`Part "${part}" not found in library`);
        continue;
      }

      // Add to tray (use found.part if search resolved a different name)
      const resolvedPart = found ? found.part : part;
      addToTray(resolvedPart, qty);
      loaded++;
    }

    return {
      success: errors.length === 0 || !strict,
      loaded,
      skipped,
      errors,
    };
  }

  /**
   * Export current tray as a BOM (JSON-serializable array).
   * @returns {Array} [ { part, qty, group, title } ]
   */
  function exportBom() {
    const result = [];
    for (const item of items.values()) {
      result.push({
        part: item.part,
        qty: item.quantity,
        group: item.group,
        title: item.title,
      });
    }
    return result;
  }

  // ---------------------------------------------------------------------------
  // TO OPERATION (EngineInterface-compatible operation objects)
  // ---------------------------------------------------------------------------

  /**
   * Convert a place command to engine-compatible operation objects.
   * Use this when submitting through EngineInterface instead of executor.
   *
   * The place action is hybrid: engine handles device creation,
   * board handles placement (position/rotation).
   *
   * @param {object} command — the { type: 'place', ref, part, x, y, rotation } command
   * @returns {object} { circuitOp, boardCmd } — circuitOp for engine, boardCmd for local executor
   */
  function toOperation(command) {
    if (!command || command.type !== 'place') return null;

    return {
      circuitOp: {
        kind: 'component.add-device',
        target: 'source',
        intent: { ref: command.ref, part: command.part },
      },
      boardCmd: {
        type: 'place',
        ref: command.ref,
        part: command.part,
        x: command.x,
        y: command.y,
        rotation: command.rotation || 0,
      },
    };
  }

  /**
   * Convert a device removal to engine-compatible operation.
   * @param {string} ref — device reference to remove
   * @returns {object} { circuitOp } — operation for engine
   */
  function toRemoveOperation(ref) {
    return {
      circuitOp: {
        kind: 'component.remove-device',
        target: 'source',
        intent: { ref },
      },
    };
  }

  // ---------------------------------------------------------------------------
  // PUBLIC API
  // ---------------------------------------------------------------------------

  return {
    addToTray,
    removeFromTray,
    reduceQuantity,
    setQuantity,
    pickup,
    cancelPickup,
    getPickedUp,
    placeFromTray,
    unplace,
    loadBom,
    exportBom,
    getItems,
    getItem,
    itemCount,
    totalQuantity,
    placedCount,
    remainingCount,
    clear,
    setRefCounters,
    getRefCounters,
    toOperation,
    toRemoveOperation,
  };
}
