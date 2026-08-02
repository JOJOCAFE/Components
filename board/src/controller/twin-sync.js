/**
 * Components Board — Bidirectional Sync (Twin Model)
 *
 * THREE TWINS: Visual (Viewport) ↔ Components:circuit ↔ Components:board
 *
 * Like MakeCode's block↔text: change one, the other updates automatically.
 * The engine state is the single source of truth. All three views are projections.
 *
 * Flow:
 *   User action (any of 3 surfaces) → Engine command → Engine state updates
 *   → Regenerate :circuit text from state
 *   → Regenerate :board text from state  
 *   → Re-render viewport from state
 *
 * Reverse flow (text edit):
 *   User edits :circuit text → parse → diff against engine state → emit commands
 *   User edits :board text → parse → diff against engine state → emit commands
 *
 * Pure functions, no DOM, ES module.
 */

import { parseFile, FILE_TYPES, LINE_TYPES, serializeDevice, serializeConnect, serializePaper, serializePlace, serializeRoute, serializeLabel } from '../model/file.js';

// =============================================================================
// ENGINE STATE → TEXT (generate text from engine state)
// =============================================================================

/**
 * Generate Components:circuit text from engine state.
 * @param {object} engineState — from engine.getState()
 * @returns {string} complete circuit file text
 */
export function stateToCircuit(engineState) {
  const pages = engineState.pages || [{ name: 'Page 1' }];
  const devices = engineState.component?.devices || {};
  const connections = engineState.component?.connections || [];

  const lines = [];
  for (const page of pages) {
    lines.push(`@page ${page.name}`);
    // Devices on this page
    for (const [ref, dev] of Object.entries(devices)) {
      if ((dev.page || pages[0]?.name) === page.name) {
        lines.push(serializeDevice(ref, dev.part));
      }
    }
    // Connections involving devices on this page
    for (const conn of connections) {
      const fromRef = conn.from.split('.')[0];
      const fromDev = devices[fromRef];
      if ((fromDev?.page || pages[0]?.name) === page.name) {
        lines.push(serializeConnect(conn.from, conn.to));
      }
    }
    lines.push('');
  }
  return lines.join('\n').replace(/\n{3,}/g, '\n\n').trim() + '\n';
}

/**
 * Generate Components:board text from engine state.
 * @param {object} engineState — from engine.getState()
 * @returns {string} complete board file text
 */
export function stateToBoard(engineState) {
  const pages = engineState.pages || [{ name: 'Page 1' }];
  const placements = engineState.board?.placements || {};
  const routes = engineState.board?.routes || [];
  const labels = engineState.board?.labels || [];
  const config = engineState.config;

  const lines = [];
  for (const page of pages) {
    lines.push(`@page ${page.name}`);
    // Paper config
    const paperSize = page.paper?.size || config?.paper?.size || 'A4';
    const paperOrient = page.paper?.orientation || config?.paper?.orientation || 'landscape';
    lines.push(serializePaper(paperSize, paperOrient));
    // Placements on this page
    for (const [ref, pl] of Object.entries(placements)) {
      if ((pl.page || pages[0]?.name) === page.name) {
        lines.push(serializePlace(ref, pl.x, pl.y, pl.rotation || 0));
      }
    }
    // Routes on this page
    for (const route of routes) {
      const fromRef = route.from.split('.')[0];
      const fromPl = placements[fromRef];
      if ((fromPl?.page || pages[0]?.name) === page.name) {
        lines.push(serializeRoute(route.from, route.to, route.via || []));
      }
    }
    // Labels on this page
    for (const label of labels) {
      if ((label.page || pages[0]?.name) === page.name) {
        lines.push(serializeLabel(label.text, label.x, label.y));
      }
    }
    lines.push('');
  }
  return lines.join('\n').replace(/\n{3,}/g, '\n\n').trim() + '\n';
}

// =============================================================================
// TEXT → COMMANDS (parse text edits into engine commands)
// =============================================================================

/**
 * Diff circuit text against current engine state and produce commands.
 * @param {string} newText — edited Components:circuit content
 * @param {object} engineState — current engine state
 * @returns {string[]} array of command strings to execute
 */
export function circuitTextToCommands(newText, engineState) {
  const file = parseFile(newText, FILE_TYPES.CIRCUIT);
  const currentDevices = engineState.component?.devices || {};
  const currentConnections = engineState.component?.connections || [];
  const commands = [];

  // Collect all devices and connections from parsed text
  const parsedDevices = {};
  const parsedConnections = [];

  for (const page of file.pages) {
    for (const line of page.lines) {
      if (line.parsed.type === LINE_TYPES.DEVICE) {
        parsedDevices[line.parsed.ref] = { part: line.parsed.part, page: page.name };
      }
      if (line.parsed.type === LINE_TYPES.CONNECT) {
        parsedConnections.push({ from: line.parsed.from, to: line.parsed.to });
      }
    }
  }

  // Devices added (in text but not in state)
  for (const [ref, dev] of Object.entries(parsedDevices)) {
    if (!currentDevices[ref]) {
      commands.push(`place ${ref}, ${dev.part} at (50, 50) rotate 0`);
    }
  }

  // Devices removed (in state but not in text)
  for (const ref of Object.keys(currentDevices)) {
    if (!parsedDevices[ref]) {
      commands.push(`delete ${ref}`);
    }
  }

  // Connections added
  for (const conn of parsedConnections) {
    const exists = currentConnections.some(c => c.from === conn.from && c.to === conn.to);
    if (!exists) {
      commands.push(`connect ${conn.from} -> ${conn.to}`);
    }
  }

  // Connections removed
  for (const conn of currentConnections) {
    const exists = parsedConnections.some(c => c.from === conn.from && c.to === conn.to);
    if (!exists) {
      commands.push(`disconnect ${conn.from} -> ${conn.to}`);
    }
  }

  return commands;
}

/**
 * Diff board text against current engine state and produce commands.
 * @param {string} newText — edited Components:board content
 * @param {object} engineState — current engine state
 * @returns {string[]} array of command strings to execute
 */
export function boardTextToCommands(newText, engineState) {
  const file = parseFile(newText, FILE_TYPES.BOARD);
  const currentPlacements = engineState.board?.placements || {};
  const commands = [];

  // Collect placements from text
  const parsedPlacements = {};
  for (const page of file.pages) {
    for (const line of page.lines) {
      if (line.parsed.type === LINE_TYPES.PLACE) {
        parsedPlacements[line.parsed.ref] = {
          x: line.parsed.x, y: line.parsed.y,
          rotation: line.parsed.rotation, page: page.name,
        };
      }
    }
  }

  // Placements moved or rotated
  for (const [ref, pl] of Object.entries(parsedPlacements)) {
    const current = currentPlacements[ref];
    if (current) {
      if (current.x !== pl.x || current.y !== pl.y) {
        commands.push(`move ${ref} to (${pl.x}, ${pl.y})`);
      }
      if ((current.rotation || 0) !== pl.rotation) {
        commands.push(`rotate ${ref} ${pl.rotation}`);
      }
    }
  }

  return commands;
}

// =============================================================================
// FULL SYNC CYCLE
// =============================================================================

/**
 * Perform a full sync from engine state to both text files.
 * Call this after any engine command to keep texts up-to-date.
 * @param {object} engineState
 * @returns {{ circuit: string, board: string }}
 */
export function syncStateToText(engineState) {
  return {
    circuit: stateToCircuit(engineState),
    board: stateToBoard(engineState),
  };
}

/**
 * Determine which text was edited and produce commands to sync the other.
 * @param {'circuit'|'board'} editedSide — which file the user edited
 * @param {string} newText — the new text content
 * @param {object} engineState — current engine state
 * @returns {string[]} commands to execute
 */
export function syncTextToEngine(editedSide, newText, engineState) {
  if (editedSide === 'circuit') {
    return circuitTextToCommands(newText, engineState);
  } else {
    return boardTextToCommands(newText, engineState);
  }
}
