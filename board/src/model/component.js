/**
 * Components Board — Component Model
 * Task 1.3: Device and connection data model
 *
 * Pure functions, no side effects, no DOM.
 * ES module syntax, Node.js compatible.
 *
 * Model shape:
 *   { devices: { ref: { ref, part } }, connections: [{ from, to, via }] }
 */

/**
 * Create a new empty component model.
 * @returns {object}
 */
export function createComponentModel() {
  return { devices: {}, connections: [] };
}

/**
 * Add a device to the model.
 * @param {object} model
 * @param {string} ref - device reference designator
 * @param {string} part - part identifier (e.g. 'digital.74HC04')
 * @returns {object} updated model
 * @throws {Error} if ref already exists
 */
export function addDevice(model, ref, part) {
  if (model.devices[ref]) {
    throw new Error(`Device "${ref}" already exists`);
  }
  return {
    devices: { ...model.devices, [ref]: { ref, part } },
    connections: model.connections,
  };
}

/**
 * Remove a device and all its connections from the model.
 * @param {object} model
 * @param {string} ref
 * @returns {object} updated model
 * @throws {Error} if ref doesn't exist
 */
export function removeDevice(model, ref) {
  if (!model.devices[ref]) {
    throw new Error(`Device "${ref}" not found`);
  }
  const { [ref]: _removed, ...remainingDevices } = model.devices;
  // Remove connections involving this ref (pin format: ref.pin)
  const prefix = ref + '.';
  const connections = model.connections.filter(
    c => !c.from.startsWith(prefix) && !c.to.startsWith(prefix)
  );
  return { devices: remainingDevices, connections };
}

/**
 * Add a connection between two pins.
 * @param {object} model
 * @param {string} from - pin reference (ref.pin)
 * @param {string} to - pin reference (ref.pin)
 * @param {Array} via - waypoints [{x, y}, ...]
 * @returns {object} updated model
 */
export function addConnection(model, from, to, via = []) {
  const connections = [...model.connections, { from, to, via }];
  return { devices: model.devices, connections };
}

/**
 * Remove a connection between two pins.
 * @param {object} model
 * @param {string} from
 * @param {string} to
 * @returns {object} updated model
 * @throws {Error} if connection not found
 */
export function removeConnection(model, from, to) {
  const idx = model.connections.findIndex(c => c.from === from && c.to === to);
  if (idx < 0) {
    throw new Error(`Connection from "${from}" to "${to}" not found`);
  }
  const connections = [...model.connections.slice(0, idx), ...model.connections.slice(idx + 1)];
  return { devices: model.devices, connections };
}

/**
 * Get a device by ref or null.
 * @param {object} model
 * @param {string} ref
 * @returns {object|null}
 */
export function getDevice(model, ref) {
  return model.devices[ref] || null;
}

/**
 * Get all connections involving a ref (any pin of that device).
 * @param {object} model
 * @param {string} ref
 * @returns {Array}
 */
export function getConnections(model, ref) {
  const prefix = ref + '.';
  return model.connections.filter(
    c => c.from.startsWith(prefix) || c.to.startsWith(prefix)
  );
}
