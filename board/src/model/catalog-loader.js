/**
 * Components Board — Catalog Auto-Loader
 * Fetches definition.json files from lib/standard/ at startup.
 *
 * Two modes:
 *   1. Browser: uses fetch() against the HTTP server serving lib/standard/
 *   2. Node.js: uses fs.readFile for testing
 *
 * DOM-free. Pure functions + factory pattern.
 * ES module syntax, Node.js compatible.
 *
 * Usage (browser):
 *   import { createCatalogLoader } from './catalog-loader.js';
 *   const loader = createCatalogLoader({ basePath: '../lib/standard' });
 *   const { loaded, errors } = await loader.loadAll(library);
 *
 * Usage (Node.js test):
 *   import { createCatalogLoader } from './catalog-loader.js';
 *   const loader = createCatalogLoader({ basePath: '/abs/path/to/lib/standard', reader: fsReader });
 *   const { loaded, errors } = await loader.loadAll(library);
 */

// =============================================================================
// CONSTANTS
// =============================================================================

/** Default group order (same as lib/standard/index.json) */
export const DEFAULT_GROUPS = Object.freeze([
  '74xx', 'memory', 'support', 'virtual', 'passive', 'discrete',
]);

// =============================================================================
// READERS (pluggable fetch strategy)
// =============================================================================

/**
 * Browser fetch reader — uses fetch() API.
 * @param {string} url — relative or absolute URL
 * @returns {Promise<object|null>} parsed JSON or null on failure
 */
export function fetchReader(url) {
  return fetch(url)
    .then(res => {
      if (!res.ok) return null;
      return res.json();
    })
    .catch(() => null);
}

/**
 * Create a Node.js fs reader for testing.
 * @param {object} fs — node:fs/promises module
 * @returns {function} reader function
 */
export function createFsReader(fs) {
  return async function fsReader(path) {
    try {
      const content = await fs.readFile(path, 'utf-8');
      return JSON.parse(content);
    } catch {
      return null;
    }
  };
}

/**
 * Create a Node.js directory scanner (for groups without components list).
 * @param {object} fs — node:fs/promises module
 * @returns {function} scanner(dirPath) → string[]
 */
export function createDirScanner(fs) {
  return async function dirScanner(dirPath) {
    try {
      const entries = await fs.readdir(dirPath, { withFileTypes: true });
      return entries
        .filter(e => e.isDirectory())
        .map(e => e.name)
        .sort();
    } catch {
      return [];
    }
  };
}

// =============================================================================
// CATALOG LOADER FACTORY
// =============================================================================

/**
 * Create a catalog loader.
 *
 * @param {object} options
 * @param {string} options.basePath — base path to lib/standard/ (no trailing slash)
 * @param {function} [options.reader] — async function(url) → JSON|null (defaults to fetchReader)
 * @param {function} [options.dirScanner] — async function(dirPath) → string[] (for groups without components list)
 * @param {string[]} [options.groups] — group IDs to load (defaults to all)
 * @returns {object} loader API
 */
export function createCatalogLoader(options = {}) {
  const {
    basePath = '../lib/standard',
    reader = fetchReader,
    dirScanner = null,
    groups = DEFAULT_GROUPS,
  } = options;

  /** Track loading state */
  let loading = false;
  let lastResult = null;

  /**
   * Discover parts in a group by reading its index.json.
   * Falls back to the "components" array in index.json.
   * If no components list, falls back to dirScanner if available.
   *
   * @param {string} groupId
   * @returns {Promise<string[]>} array of part names
   */
  async function discoverParts(groupId) {
    const indexUrl = `${basePath}/${groupId}/index.json`;
    const index = await reader(indexUrl);

    // index.json may have a "components" array listing part names
    if (index && Array.isArray(index.components)) {
      return index.components;
    }

    // Fallback: scan directory for subdirectories (Node.js only)
    if (dirScanner) {
      const groupDir = `${basePath}/${groupId}`;
      return dirScanner(groupDir);
    }

    // No discovery possible
    return [];
  }

  /**
   * Load a single part definition.
   * Path: basePath/{group}/{part}/definition/definition.json
   *
   * @param {string} groupId
   * @param {string} partName
   * @returns {Promise<object|null>} definition or null
   */
  async function loadDefinition(groupId, partName) {
    const url = `${basePath}/${groupId}/${partName}/definition/definition.json`;
    return reader(url);
  }

  /**
   * Load all parts in a single group.
   *
   * @param {string} groupId
   * @param {object} library — library instance to load into
   * @returns {Promise<{ loaded: number, errors: string[] }>}
   */
  async function loadGroup(groupId, library) {
    const errors = [];
    const parts = await discoverParts(groupId);

    if (parts.length === 0) {
      errors.push(`Group "${groupId}": no parts discovered (no components list and no directory scanner)`);
      return { loaded: 0, errors };
    }

    // Load all definitions in parallel (batch of 10 to avoid overwhelming)
    const BATCH_SIZE = 10;
    let loaded = 0;

    for (let i = 0; i < parts.length; i += BATCH_SIZE) {
      const batch = parts.slice(i, i + BATCH_SIZE);
      const results = await Promise.all(
        batch.map(part => loadDefinition(groupId, part))
      );

      for (let j = 0; j < results.length; j++) {
        const def = results[j];
        const partName = batch[j];
        if (def && def.part) {
          library.loadOne(groupId, def);
          loaded++;
        } else if (def && !def.part) {
          errors.push(`Group "${groupId}": "${partName}" definition missing "part" field`);
        } else {
          errors.push(`Group "${groupId}": "${partName}" definition not found`);
        }
      }
    }

    return { loaded, errors };
  }

  /**
   * Load all groups into the library.
   * This is the main entry point — call at startup.
   *
   * @param {object} library — library instance (from createLibrary)
   * @param {object} [opts]
   * @param {function} [opts.onProgress] — callback({ group, loaded, total })
   * @returns {Promise<{ loaded: number, errors: string[], groups: object }>}
   */
  async function loadAll(library, opts = {}) {
    const { onProgress } = opts;

    if (loading) {
      return { loaded: 0, errors: ['Load already in progress'], groups: {} };
    }

    loading = true;
    let totalLoaded = 0;
    const allErrors = [];
    const groupResults = {};

    for (const groupId of groups) {
      const result = await loadGroup(groupId, library);
      totalLoaded += result.loaded;
      allErrors.push(...result.errors);
      groupResults[groupId] = result.loaded;

      if (onProgress) {
        onProgress({
          group: groupId,
          loaded: result.loaded,
          total: totalLoaded,
        });
      }
    }

    loading = false;
    lastResult = { loaded: totalLoaded, errors: allErrors, groups: groupResults };
    return lastResult;
  }

  /**
   * Load a specific list of groups (subset).
   *
   * @param {string[]} groupIds
   * @param {object} library
   * @returns {Promise<{ loaded: number, errors: string[] }>}
   */
  async function loadGroups(groupIds, library) {
    let totalLoaded = 0;
    const allErrors = [];

    for (const groupId of groupIds) {
      const result = await loadGroup(groupId, library);
      totalLoaded += result.loaded;
      allErrors.push(...result.errors);
    }

    return { loaded: totalLoaded, errors: allErrors };
  }

  /**
   * Check if loading is in progress.
   * @returns {boolean}
   */
  function isLoading() {
    return loading;
  }

  /**
   * Get the result of the last loadAll call.
   * @returns {object|null}
   */
  function getLastResult() {
    return lastResult;
  }

  // ---------------------------------------------------------------------------
  // PUBLIC API
  // ---------------------------------------------------------------------------

  return {
    discoverParts,
    loadDefinition,
    loadGroup,
    loadGroups,
    loadAll,
    isLoading,
    getLastResult,
  };
}
