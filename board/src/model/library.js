/**
 * Components Board — Library Model
 * Device catalog loader: read lib/standard structure, search, filter, browse.
 *
 * DOM-free. Pure functions + factory pattern.
 * ES module syntax, Node.js compatible.
 *
 * Catalog structure (mirrors lib/standard/):
 *   groups: [ { id, title, parts: [ { part, title, group, pins, package } ] } ]
 *
 * Usage:
 *   import { createLibrary } from './library.js';
 *   const lib = createLibrary();
 *   lib.loadGroup('74xx', [...definitions]);
 *   lib.search('counter');
 *   lib.getByPart('74HC161');
 *   lib.listGroups();
 *   lib.listParts('74xx');
 */

// =============================================================================
// CONSTANTS
// =============================================================================

export const GROUPS = Object.freeze([
  { id: '74xx', title: '74xx and 74HC logic ICs' },
  { id: 'memory', title: 'Memory ICs' },
  { id: 'support', title: 'Support ICs' },
  { id: 'virtual', title: 'Simulation-only sources, rails, and probes' },
  { id: 'passive', title: 'Passive physical parts' },
  { id: 'discrete', title: 'Discrete semiconductor parts' },
]);

// =============================================================================
// CATALOG ENTRY
// =============================================================================

/**
 * Create a normalized catalog entry from a definition.json object.
 * @param {object} def — raw definition.json
 * @param {string} groupId — which group this belongs to
 * @returns {object} catalog entry
 */
export function createCatalogEntry(def, groupId) {
  const pinCount = def.pins ? Object.keys(def.pins).length : 0;
  const pkgKind = def.package?.kind || 'DIP';
  const title = def.about?.title || def.part || 'Unknown';
  const role = def.about?.role || '';
  const family = def.about?.family || '';
  const manufacturer = def.about?.manufacturer || '';

  return Object.freeze({
    part: def.part,
    title,
    group: groupId,
    role,
    family,
    manufacturer,
    pinCount,
    package: pkgKind,
    // Keep minimal searchable fields (not full definition)
    _keywords: buildKeywords(def.part, title, role, family, groupId),
  });
}

/**
 * Build a lowercase keyword string for search.
 */
function buildKeywords(...fields) {
  return fields.filter(Boolean).join(' ').toLowerCase();
}

// =============================================================================
// LIBRARY FACTORY
// =============================================================================

/**
 * Create a library instance.
 * @returns {object} library API
 */
export function createLibrary() {
  /** @type {Map<string, object[]>} groupId → catalog entries */
  const catalog = new Map();

  /** @type {Map<string, object>} part → catalog entry (global index) */
  const byPart = new Map();

  // ---------------------------------------------------------------------------
  // LOADING
  // ---------------------------------------------------------------------------

  /**
   * Load a group of component definitions into the catalog.
   * @param {string} groupId — group identifier (e.g. '74xx')
   * @param {object[]} definitions — array of definition.json objects
   * @returns {number} count of entries loaded
   */
  function loadGroup(groupId, definitions) {
    const entries = [];
    for (const def of definitions) {
      if (!def.part) continue; // skip invalid
      const entry = createCatalogEntry(def, groupId);
      entries.push(entry);
      byPart.set(entry.part, entry);
    }
    const existing = catalog.get(groupId) || [];
    catalog.set(groupId, [...existing, ...entries]);
    return entries.length;
  }

  /**
   * Load a single definition into the catalog.
   * @param {string} groupId
   * @param {object} def — definition.json object
   * @returns {object} catalog entry
   */
  function loadOne(groupId, def) {
    const entry = createCatalogEntry(def, groupId);
    const existing = catalog.get(groupId) || [];
    catalog.set(groupId, [...existing, entry]);
    byPart.set(entry.part, entry);
    return entry;
  }

  // ---------------------------------------------------------------------------
  // QUERYING
  // ---------------------------------------------------------------------------

  /**
   * Get a catalog entry by part name.
   * @param {string} part
   * @returns {object|null}
   */
  function getByPart(part) {
    return byPart.get(part) || null;
  }

  /**
   * List all available groups with counts.
   * @returns {object[]} [ { id, title, count } ]
   */
  function listGroups() {
    return GROUPS.map(g => ({
      id: g.id,
      title: g.title,
      count: (catalog.get(g.id) || []).length,
    }));
  }

  /**
   * List all parts in a group, optionally sorted.
   * @param {string} groupId
   * @param {object} [options]
   * @param {string} [options.sortBy='part'] — 'part' | 'title' | 'pinCount'
   * @returns {object[]} array of catalog entries
   */
  function listParts(groupId, options = {}) {
    const { sortBy = 'part' } = options;
    const entries = catalog.get(groupId) || [];
    const sorted = [...entries];
    sorted.sort((a, b) => {
      if (sortBy === 'pinCount') return a.pinCount - b.pinCount;
      const av = a[sortBy] || '';
      const bv = b[sortBy] || '';
      return av.localeCompare(bv, undefined, { numeric: true });
    });
    return sorted;
  }

  /**
   * List all parts in the library across all groups.
   * @returns {object[]}
   */
  function listAll() {
    const all = [];
    for (const entries of catalog.values()) {
      all.push(...entries);
    }
    return all;
  }

  /**
   * Search parts by keyword (fuzzy match on part, title, role, group).
   * @param {string} query — search term
   * @param {object} [options]
   * @param {string} [options.group] — filter to a specific group
   * @param {number} [options.limit=50] — max results
   * @returns {object[]} matching catalog entries, best matches first
   */
  function search(query, options = {}) {
    const { group, limit = 50 } = options;
    const q = query.toLowerCase().trim();
    if (!q) return [];

    const tokens = q.split(/\s+/);
    const results = [];
    const source = group ? (catalog.get(group) || []) : listAll();

    for (const entry of source) {
      let score = 0;
      const kw = entry._keywords;

      // Score: exact part match = highest
      if (entry.part.toLowerCase() === q) {
        score += 100;
      } else if (entry.part.toLowerCase().includes(q)) {
        score += 50;
      }

      // Multi-token matching
      let allMatch = true;
      for (const token of tokens) {
        if (kw.includes(token)) {
          score += 10;
        } else {
          allMatch = false;
        }
      }
      if (!allMatch) continue; // All tokens must match
      if (score === 0) continue;

      results.push({ entry, score });
    }

    results.sort((a, b) => b.score - a.score);
    return results.slice(0, limit).map(r => r.entry);
  }

  /**
   * Filter parts by criteria.
   * @param {object} criteria
   * @param {string} [criteria.group]
   * @param {string} [criteria.family]
   * @param {string} [criteria.package]
   * @param {number} [criteria.minPins]
   * @param {number} [criteria.maxPins]
   * @param {string} [criteria.role]
   * @returns {object[]}
   */
  function filter(criteria = {}) {
    const { group, family, package: pkg, minPins, maxPins, role } = criteria;
    let source = group ? (catalog.get(group) || []) : listAll();

    if (family) {
      const f = family.toLowerCase();
      source = source.filter(e => e.family.toLowerCase() === f);
    }
    if (pkg) {
      const p = pkg.toLowerCase();
      source = source.filter(e => e.package.toLowerCase() === p);
    }
    if (minPins !== undefined) {
      source = source.filter(e => e.pinCount >= minPins);
    }
    if (maxPins !== undefined) {
      source = source.filter(e => e.pinCount <= maxPins);
    }
    if (role) {
      const r = role.toLowerCase();
      source = source.filter(e => e.role.toLowerCase().includes(r));
    }
    return source;
  }

  /**
   * Get total number of parts in library.
   * @returns {number}
   */
  function count() {
    let total = 0;
    for (const entries of catalog.values()) {
      total += entries.length;
    }
    return total;
  }

  /**
   * Clear all loaded data.
   */
  function clear() {
    catalog.clear();
    byPart.clear();
  }

  // ---------------------------------------------------------------------------
  // PUBLIC API
  // ---------------------------------------------------------------------------

  return {
    loadGroup,
    loadOne,
    getByPart,
    listGroups,
    listParts,
    listAll,
    search,
    filter,
    count,
    clear,
  };
}
