/**
 * Components Board — Board Model
 * Task 1.3: Visual layout data model (placements, routes, labels)
 *
 * Pure functions, no side effects, no DOM.
 * ES module syntax, Node.js compatible.
 *
 * Model shape:
 *   {
 *     placements: { ref: { ref, x, y, rotation } },
 *     routes: [{ from, to, via }],
 *     labels: [{ id, text, x, y }]
 *   }
 */

let _labelCounter = 0;

/**
 * Create a new empty board model.
 * @returns {object}
 */
export function createBoardModel() {
  return { placements: {}, routes: [], labels: [] };
}

/**
 * Set or update a device placement on the board.
 * @param {object} model
 * @param {string} ref
 * @param {number} x
 * @param {number} y
 * @param {number} rotation
 * @returns {object} updated model
 */
export function setPlacement(model, ref, x, y, rotation) {
  return {
    placements: { ...model.placements, [ref]: { ref, x, y, rotation } },
    routes: model.routes,
    labels: model.labels,
  };
}

/**
 * Remove a placement from the board.
 * @param {object} model
 * @param {string} ref
 * @returns {object} updated model
 * @throws {Error} if placement doesn't exist
 */
export function removePlacement(model, ref) {
  if (!model.placements[ref]) {
    throw new Error(`Placement "${ref}" not found`);
  }
  const { [ref]: _removed, ...remainingPlacements } = model.placements;
  return {
    placements: remainingPlacements,
    routes: model.routes,
    labels: model.labels,
  };
}

/**
 * Get a placement by ref or null.
 * @param {object} model
 * @param {string} ref
 * @returns {object|null}
 */
export function getPlacement(model, ref) {
  return model.placements[ref] || null;
}

/**
 * Set or update a route for a connection.
 * @param {object} model
 * @param {string} from - pin ref
 * @param {string} to - pin ref
 * @param {Array} via - waypoints [{x, y}, ...]
 * @returns {object} updated model
 */
export function setRoute(model, from, to, via) {
  // Replace existing route for same from->to, or add new
  const idx = model.routes.findIndex(r => r.from === from && r.to === to);
  let routes;
  if (idx >= 0) {
    routes = [...model.routes];
    routes[idx] = { from, to, via };
  } else {
    routes = [...model.routes, { from, to, via }];
  }
  return {
    placements: model.placements,
    routes,
    labels: model.labels,
  };
}

/**
 * Remove a route between two pins.
 * @param {object} model
 * @param {string} from
 * @param {string} to
 * @returns {object} updated model
 * @throws {Error} if route not found
 */
export function removeRoute(model, from, to) {
  const idx = model.routes.findIndex(r => r.from === from && r.to === to);
  if (idx < 0) {
    throw new Error(`Route from "${from}" to "${to}" not found`);
  }
  const routes = [...model.routes.slice(0, idx), ...model.routes.slice(idx + 1)];
  return {
    placements: model.placements,
    routes,
    labels: model.labels,
  };
}

/**
 * Add a label to the board.
 * @param {object} model
 * @param {string|null} id - label id (auto-generated if null/undefined)
 * @param {string} text
 * @param {number} x
 * @param {number} y
 * @returns {object} updated model
 */
export function addLabel(model, id, text, x, y) {
  const labelId = id || `label_${++_labelCounter}`;
  const labels = [...model.labels, { id: labelId, text, x, y }];
  return {
    placements: model.placements,
    routes: model.routes,
    labels,
  };
}

/**
 * Remove a label by id.
 * @param {object} model
 * @param {string} id
 * @returns {object} updated model
 * @throws {Error} if label not found
 */
export function removeLabel(model, id) {
  const idx = model.labels.findIndex(l => l.id === id);
  if (idx < 0) {
    throw new Error(`Label "${id}" not found`);
  }
  const labels = [...model.labels.slice(0, idx), ...model.labels.slice(idx + 1)];
  return {
    placements: model.placements,
    routes: model.routes,
    labels,
  };
}

/**
 * Get all labels.
 * @param {object} model
 * @returns {Array}
 */
export function getLabels(model) {
  return model.labels;
}

/**
 * Remove all routes involving a device ref (prefix match).
 * @param {object} model
 * @param {string} ref
 * @returns {object} updated model
 */
export function removeRoutesForDevice(model, ref) {
  const prefix = ref + '.';
  const routes = model.routes.filter(
    r => !r.from.startsWith(prefix) && !r.to.startsWith(prefix)
  );
  return {
    placements: model.placements,
    routes,
    labels: model.labels,
  };
}
