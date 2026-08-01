/**
 * Components Board — Command Parser
 * Task 1.2: Engine command parser
 *
 * Pure function, no side effects, no model access.
 * ES module syntax, Node.js compatible.
 */

export const COMMAND_TYPES = Object.freeze({
  PLACE: 'place',
  MOVE: 'move',
  ROTATE: 'rotate',
  DELETE: 'delete',
  CONNECT: 'connect',
  DISCONNECT: 'disconnect',
  ROUTE: 'route',
  LABEL: 'label',
  SELECT: 'select',
  DESELECT: 'deselect',
  ZOOM: 'zoom',
  PAN: 'pan',
  UNDO: 'undo',
  REDO: 'redo',
  NEW_PAGE: 'new-page',
  SWITCH_PAGE: 'switch-page',
  RENAME_PAGE: 'rename-page',
  DELETE_PAGE: 'delete-page',
  SET_CONFIG: 'set-config',
  ERROR: 'error',
});

const VALID_ANGLES = [0, 90, 180, 270];

// Helpers

function error(message, input) {
  return { type: COMMAND_TYPES.ERROR, message, input };
}

/**
 * Parse a quoted string starting at position i (which must point to the opening ").
 * Returns { value, end } where end is the index after the closing quote,
 * or null if no valid quoted string is found.
 */
function parseQuotedString(text, i) {
  if (text[i] !== '"') return null;
  let result = '';
  let j = i + 1;
  while (j < text.length) {
    if (text[j] === '\\') {
      j++;
      if (j >= text.length) return null;
      if (text[j] === '"') result += '"';
      else if (text[j] === '\\') result += '\\';
      else { result += '\\' + text[j]; }
      j++;
    } else if (text[j] === '"') {
      return { value: result, end: j + 1 };
    } else {
      result += text[j];
      j++;
    }
  }
  return null;
}

/**
 * Parse a coordinate pair like (x, y) starting from position i.
 * Returns { x, y, end } or null.
 */
function parseCoord(text, i) {
  // Skip whitespace
  while (i < text.length && /\s/.test(text[i])) i++;
  if (text[i] !== '(') return null;
  i++;

  // Parse x
  while (i < text.length && /\s/.test(text[i])) i++;
  const xMatch = text.slice(i).match(/^-?\d+(\.\d+)?/);
  if (!xMatch) return null;
  const x = parseFloat(xMatch[0]);
  i += xMatch[0].length;

  // Skip whitespace and comma
  while (i < text.length && /\s/.test(text[i])) i++;
  if (text[i] !== ',') return null;
  i++;

  // Parse y
  while (i < text.length && /\s/.test(text[i])) i++;
  const yMatch = text.slice(i).match(/^-?\d+(\.\d+)?/);
  if (!yMatch) return null;
  const y = parseFloat(yMatch[0]);
  i += yMatch[0].length;

  // Skip whitespace and closing paren
  while (i < text.length && /\s/.test(text[i])) i++;
  if (text[i] !== ')') return null;
  i++;

  return { x, y, end: i };
}

/**
 * Parse multiple coordinate pairs from position i.
 * Returns { points: [{x, y}, ...], end }.
 */
function parseCoordList(text, i) {
  const points = [];
  while (i < text.length) {
    while (i < text.length && /\s/.test(text[i])) i++;
    if (i >= text.length || text[i] !== '(') break;
    const coord = parseCoord(text, i);
    if (!coord) break;
    points.push({ x: coord.x, y: coord.y });
    i = coord.end;
  }
  return { points, end: i };
}

/**
 * Check if a ref is valid (alphanumeric + underscore, at least 1 char).
 */
function isValidRef(ref) {
  return /^[A-Za-z0-9_]+$/.test(ref);
}

/**
 * Check if a pin reference is valid: ref.pin where pin allows alphanumeric, underscore, and @.
 */
function isValidPin(pin) {
  return /^[A-Za-z0-9_]+\.[A-Za-z0-9_@]+$/.test(pin);
}

/**
 * Parse a command text string into a structured operation object.
 * @param {string} text - The command string to parse
 * @returns {object} Structured command object with type and params, or error
 */
/**
 * Parse a JSON-formatted command (structured style for AI/tools/API).
 * Accepts: {"command": "<type>", ...params}
 * Returns the same internal operation object as text parsing.
 */
function parseJsonCommand(jsonText, originalInput) {
  let obj;
  try {
    obj = JSON.parse(jsonText);
  } catch (err) {
    return error(`Invalid JSON command: ${err.message}`, originalInput);
  }

  if (!obj || typeof obj !== 'object' || !obj.command) {
    return error('JSON command must have a "command" field', originalInput);
  }

  const type = obj.command.toLowerCase();
  const VALID_COMMANDS = Object.values(COMMAND_TYPES).filter(t => t !== 'error');

  if (!VALID_COMMANDS.includes(type)) {
    return error(`Unknown command "${obj.command}". Valid: ${VALID_COMMANDS.join(', ')}`, originalInput);
  }

  // Map JSON fields to internal operation format
  switch (type) {
    case 'place':
      if (!obj.ref || !obj.part) return error('place requires "ref" and "part"', originalInput);
      return { type: 'place', ref: obj.ref, part: obj.part, x: obj.x || 0, y: obj.y || 0, rotation: obj.rotation || 0 };
    case 'move':
      if (!obj.ref) return error('move requires "ref"', originalInput);
      return { type: 'move', ref: obj.ref, x: obj.x ?? 0, y: obj.y ?? 0 };
    case 'rotate':
      if (!obj.ref) return error('rotate requires "ref"', originalInput);
      if (![0, 90, 180, 270].includes(obj.degrees)) return error('rotate degrees must be 0, 90, 180, or 270', originalInput);
      return { type: 'rotate', ref: obj.ref, degrees: obj.degrees };
    case 'delete':
      if (!obj.ref) return error('delete requires "ref"', originalInput);
      return { type: 'delete', ref: obj.ref };
    case 'connect':
      if (!obj.from || !obj.to) return error('connect requires "from" and "to"', originalInput);
      return { type: 'connect', from: obj.from, to: obj.to, via: Array.isArray(obj.via) ? obj.via : [] };
    case 'disconnect':
      if (!obj.from || !obj.to) return error('disconnect requires "from" and "to"', originalInput);
      return { type: 'disconnect', from: obj.from, to: obj.to };
    case 'route':
      if (!obj.from || !obj.to) return error('route requires "from" and "to"', originalInput);
      return { type: 'route', from: obj.from, to: obj.to, via: Array.isArray(obj.via) ? obj.via : [] };
    case 'label':
      if (!obj.text) return error('label requires "text"', originalInput);
      return { type: 'label', text: obj.text, x: obj.x || 0, y: obj.y || 0 };
    case 'select':
      if (!obj.ref) return error('select requires "ref"', originalInput);
      return { type: 'select', ref: obj.ref };
    case 'deselect':
      return { type: 'deselect' };
    case 'zoom':
      return { type: 'zoom', value: obj.value ?? 100 };
    case 'pan':
      return { type: 'pan', dx: obj.dx || 0, dy: obj.dy || 0 };
    case 'undo':
      return { type: 'undo' };
    case 'redo':
      return { type: 'redo' };
    case 'new-page':
      if (!obj.name) return error('new-page requires "name"', originalInput);
      return { type: 'new-page', name: obj.name, paper_size: obj.paper_size || 'A4', orientation: obj.orientation || 'landscape' };
    case 'switch-page':
      if (!obj.name) return error('switch-page requires "name"', originalInput);
      return { type: 'switch-page', name: obj.name };
    case 'rename-page':
      if (!obj.old_name || !obj.new_name) return error('rename-page requires "old_name" and "new_name"', originalInput);
      return { type: 'rename-page', old_name: obj.old_name, new_name: obj.new_name };
    case 'delete-page':
      if (!obj.name) return error('delete-page requires "name"', originalInput);
      return { type: 'delete-page', name: obj.name };
    case 'set-config':
      if (!obj.path) return error('set-config requires "path"', originalInput);
      return { type: 'set-config', path: obj.path, value: obj.value };
    default:
      return error(`Unhandled JSON command type: ${type}`, originalInput);
  }
}

export function parseCommand(text) {
  if (typeof text !== 'string') {
    return error('Command must be a string', String(text));
  }

  const trimmed = text.trim();
  if (!trimmed) {
    return error('Empty command', text);
  }

  // JSON format: AI/tools can send structured commands as JSON objects
  // e.g. {"command": "place", "ref": "U1", "part": "digital.74HC04", "x": 50, "y": 30, "rotation": 0}
  if (trimmed.startsWith('{')) {
    return parseJsonCommand(trimmed, text);
  }

  // Tokenize: split on whitespace but respect quoted strings and parens
  // Use regex to get the first keyword
  const keywordMatch = trimmed.match(/^(\S+)/);
  if (!keywordMatch) return error('Empty command', text);

  const keyword = keywordMatch[1].toLowerCase();
  const rest = trimmed.slice(keywordMatch[0].length);

  switch (keyword) {
    case 'place': return parsePlaceCommand(rest, text);
    case 'move': return parseMoveCommand(rest, text);
    case 'rotate': return parseRotateCommand(rest, text);
    case 'delete': return parseDeleteCommand(rest, text);
    case 'connect': return parseConnectCommand(rest, text);
    case 'disconnect': return parseDisconnectCommand(rest, text);
    case 'route': return parseRouteCommand(rest, text);
    case 'label': return parseLabelCommand(rest, text);
    case 'select': return parseSelectCommand(rest, text);
    case 'deselect': return parseDeselectCommand(rest, text);
    case 'zoom': return parseZoomCommand(rest, text);
    case 'pan': return parsePanCommand(rest, text);
    case 'undo': return { type: COMMAND_TYPES.UNDO };
    case 'redo': return { type: COMMAND_TYPES.REDO };
    case 'new-page': return parseNewPageCommand(rest, text);
    case 'switch-page': return parseSwitchPageCommand(rest, text);
    case 'rename-page': return parseRenamePageCommand(rest, text);
    case 'delete-page': return parseDeletePageCommand(rest, text);
    case 'set-config': return parseSetConfigCommand(rest, text);
    default:
      return error(`Unknown command "${keywordMatch[1]}". Available: place, move, rotate, delete, connect, disconnect, route, label, select, deselect, zoom, pan, undo, redo, new-page, switch-page, rename-page, delete-page, set-config`, text);
  }
}

// --- Individual parsers ---

function parsePlaceCommand(rest, input) {
  // place <ref>, <part> at (<x>, <y>) rotate <deg>
  // Find comma separating ref from part
  const commaIdx = rest.indexOf(',');
  if (commaIdx < 0) return error('place: expected format "place <ref>, <part> at (<x>, <y>) rotate <deg>"', input);

  const ref = rest.slice(0, commaIdx).trim();
  if (!ref || !isValidRef(ref)) return error(`place: invalid ref "${ref}". Refs must be alphanumeric + underscore`, input);

  const afterComma = rest.slice(commaIdx + 1);

  // Find "at" keyword (case-insensitive)
  const atMatch = afterComma.match(/^(.*?)\s+at\s+/i);
  if (!atMatch) return error('place: expected "at" keyword after part name', input);

  const part = atMatch[1].trim();
  if (!part) return error('place: part name cannot be empty', input);

  const afterAt = afterComma.slice(atMatch[0].length);

  // Parse coordinate
  const coord = parseCoord(afterAt, 0);
  if (!coord) return error('place: expected coordinate like (x, y) after "at"', input);

  // Parse "rotate <deg>"
  const afterCoord = afterAt.slice(coord.end);
  const rotMatch = afterCoord.match(/^\s+rotate\s+(-?\d+(\.\d+)?)\s*$/i);
  if (!rotMatch) return error('place: expected "rotate <deg>" after coordinate', input);

  const angle = parseFloat(rotMatch[1]);
  if (!VALID_ANGLES.includes(angle)) {
    return error(`place: invalid angle ${angle}. Valid angles: ${VALID_ANGLES.join(', ')}`, input);
  }

  return {
    type: COMMAND_TYPES.PLACE,
    ref,
    part,
    x: coord.x,
    y: coord.y,
    rotate: angle,
  };
}

function parseMoveCommand(rest, input) {
  // move <ref> to (<x>, <y>)
  const toMatch = rest.match(/^\s*(\S+)\s+to\s+/i);
  if (!toMatch) return error('move: expected format "move <ref> to (<x>, <y>)"', input);

  const ref = toMatch[1];
  if (!isValidRef(ref)) return error(`move: invalid ref "${ref}". Refs must be alphanumeric + underscore`, input);

  const afterTo = rest.slice(toMatch[0].length);
  const coord = parseCoord(afterTo, 0);
  if (!coord) return error('move: expected coordinate like (x, y) after "to"', input);

  // Check nothing meaningful after the coordinate
  const trailing = afterTo.slice(coord.end).trim();
  if (trailing) return error('move: unexpected content after coordinate', input);

  return {
    type: COMMAND_TYPES.MOVE,
    ref,
    x: coord.x,
    y: coord.y,
  };
}

function parseRotateCommand(rest, input) {
  // rotate <ref> <deg>
  const match = rest.match(/^\s*(\S+)\s+(-?\d+(\.\d+)?)\s*$/);
  if (!match) return error('rotate: expected format "rotate <ref> <deg>"', input);

  const ref = match[1];
  if (!isValidRef(ref)) return error(`rotate: invalid ref "${ref}". Refs must be alphanumeric + underscore`, input);

  const angle = parseFloat(match[2]);
  if (!VALID_ANGLES.includes(angle)) {
    return error(`rotate: invalid angle ${angle}. Valid angles: ${VALID_ANGLES.join(', ')}`, input);
  }

  return {
    type: COMMAND_TYPES.ROTATE,
    ref,
    angle,
  };
}

function parseDeleteCommand(rest, input) {
  // delete <ref>
  const ref = rest.trim();
  if (!ref) return error('delete: expected a ref to delete', input);
  if (!isValidRef(ref)) return error(`delete: invalid ref "${ref}". Refs must be alphanumeric + underscore`, input);

  return {
    type: COMMAND_TYPES.DELETE,
    ref,
  };
}

function parseConnectCommand(rest, input) {
  // connect <pin> -> <pin>
  // connect <pin> -> <pin> via (<x>, <y>) (<x>, <y>) ...
  const arrowIdx = rest.indexOf('->');
  if (arrowIdx < 0) return error('connect: expected format "connect <pin> -> <pin> [via ...]"', input);

  const fromPin = rest.slice(0, arrowIdx).trim();
  if (!fromPin || !isValidPin(fromPin)) return error(`connect: invalid from-pin "${fromPin}". Pin format: <ref>.<pin>`, input);

  const afterArrow = rest.slice(arrowIdx + 2);

  // Check for "via"
  const viaMatch = afterArrow.match(/^(.*?)\s+via\s+/i);
  if (viaMatch) {
    const toPin = viaMatch[1].trim();
    if (!toPin || !isValidPin(toPin)) return error(`connect: invalid to-pin "${toPin}". Pin format: <ref>.<pin>`, input);

    const afterVia = afterArrow.slice(viaMatch[0].length);
    const { points } = parseCoordList(afterVia, 0);
    if (points.length === 0) return error('connect: "via" requires at least one coordinate point', input);

    return {
      type: COMMAND_TYPES.CONNECT,
      from: fromPin,
      to: toPin,
      via: points,
    };
  }

  const toPin = afterArrow.trim();
  if (!toPin || !isValidPin(toPin)) return error(`connect: invalid to-pin "${toPin}". Pin format: <ref>.<pin>`, input);

  return {
    type: COMMAND_TYPES.CONNECT,
    from: fromPin,
    to: toPin,
  };
}

function parseDisconnectCommand(rest, input) {
  // disconnect <pin> -> <pin>
  const arrowIdx = rest.indexOf('->');
  if (arrowIdx < 0) return error('disconnect: expected format "disconnect <pin> -> <pin>"', input);

  const fromPin = rest.slice(0, arrowIdx).trim();
  if (!fromPin || !isValidPin(fromPin)) return error(`disconnect: invalid from-pin "${fromPin}". Pin format: <ref>.<pin>`, input);

  const toPin = rest.slice(arrowIdx + 2).trim();
  if (!toPin || !isValidPin(toPin)) return error(`disconnect: invalid to-pin "${toPin}". Pin format: <ref>.<pin>`, input);

  return {
    type: COMMAND_TYPES.DISCONNECT,
    from: fromPin,
    to: toPin,
  };
}

function parseRouteCommand(rest, input) {
  // route <pin> -> <pin> via (<x>, <y>) (<x>, <y>) ...
  const arrowIdx = rest.indexOf('->');
  if (arrowIdx < 0) return error('route: expected format "route <pin> -> <pin> via (<x>, <y>) ..."', input);

  const fromPin = rest.slice(0, arrowIdx).trim();
  if (!fromPin || !isValidPin(fromPin)) return error(`route: invalid from-pin "${fromPin}". Pin format: <ref>.<pin>`, input);

  const afterArrow = rest.slice(arrowIdx + 2);

  const viaMatch = afterArrow.match(/^(.*?)\s+via\s+/i);
  if (!viaMatch) return error('route: expected "via" keyword with waypoints', input);

  const toPin = viaMatch[1].trim();
  if (!toPin || !isValidPin(toPin)) return error(`route: invalid to-pin "${toPin}". Pin format: <ref>.<pin>`, input);

  const afterVia = afterArrow.slice(viaMatch[0].length);
  const { points } = parseCoordList(afterVia, 0);
  if (points.length === 0) return error('route: "via" requires at least one coordinate point', input);

  return {
    type: COMMAND_TYPES.ROUTE,
    from: fromPin,
    to: toPin,
    via: points,
  };
}

function parseLabelCommand(rest, input) {
  // label "<text>" at (<x>, <y>)
  let i = 0;
  // Skip whitespace
  while (i < rest.length && /\s/.test(rest[i])) i++;

  const quoted = parseQuotedString(rest, i);
  if (!quoted) return error('label: expected quoted text like "my label"', input);

  i = quoted.end;

  // Expect "at"
  const atMatch = rest.slice(i).match(/^\s+at\s+/i);
  if (!atMatch) return error('label: expected "at" keyword after text', input);
  i += atMatch[0].length;

  const coord = parseCoord(rest, i);
  if (!coord) return error('label: expected coordinate like (x, y) after "at"', input);

  const trailing = rest.slice(coord.end).trim();
  if (trailing) return error('label: unexpected content after coordinate', input);

  return {
    type: COMMAND_TYPES.LABEL,
    text: quoted.value,
    x: coord.x,
    y: coord.y,
  };
}

function parseSelectCommand(rest, input) {
  // select <ref>
  const ref = rest.trim();
  if (!ref) return error('select: expected a ref to select', input);
  if (!isValidRef(ref)) return error(`select: invalid ref "${ref}". Refs must be alphanumeric + underscore`, input);

  return {
    type: COMMAND_TYPES.SELECT,
    ref,
  };
}

function parseDeselectCommand(rest, input) {
  // deselect (no args)
  const trailing = rest.trim();
  if (trailing) return error('deselect: command takes no arguments', input);

  return {
    type: COMMAND_TYPES.DESELECT,
  };
}

function parseZoomCommand(rest, input) {
  // zoom <percent>%
  // zoom fit
  const trimmedRest = rest.trim();

  // Check for "fit" (case-insensitive)
  if (trimmedRest.toLowerCase() === 'fit') {
    return {
      type: COMMAND_TYPES.ZOOM,
      mode: 'fit',
    };
  }

  // Check for percentage
  const percentMatch = trimmedRest.match(/^(\d+(\.\d+)?)%$/);
  if (!percentMatch) return error('zoom: expected "zoom <percent>%" or "zoom fit"', input);

  const percent = parseFloat(percentMatch[1]);
  if (percent <= 0) return error('zoom: percent must be positive', input);

  return {
    type: COMMAND_TYPES.ZOOM,
    mode: 'percent',
    percent,
  };
}

function parsePanCommand(rest, input) {
  // pan (<dx>, <dy>)
  const coord = parseCoord(rest, 0);
  if (!coord) return error('pan: expected coordinate like (dx, dy)', input);

  const trailing = rest.slice(coord.end).trim();
  if (trailing) return error('pan: unexpected content after coordinate', input);

  return {
    type: COMMAND_TYPES.PAN,
    dx: coord.x,
    dy: coord.y,
  };
}

function parseNewPageCommand(rest, input) {
  // new-page "<name>" paper <size> <orientation>
  let i = 0;
  while (i < rest.length && /\s/.test(rest[i])) i++;

  const quoted = parseQuotedString(rest, i);
  if (!quoted) return error('new-page: expected quoted page name like "Page 2"', input);
  i = quoted.end;

  // Expect "paper"
  const paperMatch = rest.slice(i).match(/^\s+paper\s+/i);
  if (!paperMatch) return error('new-page: expected "paper" keyword after name', input);
  i += paperMatch[0].length;

  // Parse size and orientation
  const sizeOrientMatch = rest.slice(i).match(/^(\S+)\s+(\S+)\s*$/);
  if (!sizeOrientMatch) return error('new-page: expected "<size> <orientation>" after "paper"', input);

  const size = sizeOrientMatch[1].toUpperCase();
  const orientation = sizeOrientMatch[2].toLowerCase();

  return {
    type: COMMAND_TYPES.NEW_PAGE,
    name: quoted.value,
    paper: size,
    orientation,
  };
}

function parseSwitchPageCommand(rest, input) {
  // switch-page "<name>"
  let i = 0;
  while (i < rest.length && /\s/.test(rest[i])) i++;

  const quoted = parseQuotedString(rest, i);
  if (!quoted) return error('switch-page: expected quoted page name', input);

  const trailing = rest.slice(quoted.end).trim();
  if (trailing) return error('switch-page: unexpected content after page name', input);

  return {
    type: COMMAND_TYPES.SWITCH_PAGE,
    name: quoted.value,
  };
}

function parseRenamePageCommand(rest, input) {
  // rename-page "<old>" "<new>"
  let i = 0;
  while (i < rest.length && /\s/.test(rest[i])) i++;

  const oldQuoted = parseQuotedString(rest, i);
  if (!oldQuoted) return error('rename-page: expected quoted old page name', input);
  i = oldQuoted.end;

  while (i < rest.length && /\s/.test(rest[i])) i++;

  const newQuoted = parseQuotedString(rest, i);
  if (!newQuoted) return error('rename-page: expected quoted new page name', input);

  const trailing = rest.slice(newQuoted.end).trim();
  if (trailing) return error('rename-page: unexpected content after new name', input);

  return {
    type: COMMAND_TYPES.RENAME_PAGE,
    oldName: oldQuoted.value,
    newName: newQuoted.value,
  };
}

function parseDeletePageCommand(rest, input) {
  // delete-page "<name>"
  let i = 0;
  while (i < rest.length && /\s/.test(rest[i])) i++;

  const quoted = parseQuotedString(rest, i);
  if (!quoted) return error('delete-page: expected quoted page name', input);

  const trailing = rest.slice(quoted.end).trim();
  if (trailing) return error('delete-page: unexpected content after page name', input);

  return {
    type: COMMAND_TYPES.DELETE_PAGE,
    name: quoted.value,
  };
}

function parseSetConfigCommand(rest, input) {
  // set-config <path> <value>
  const match = rest.match(/^\s*(\S+)\s+(.+)$/);
  if (!match) return error('set-config: expected format "set-config <path> <value>"', input);

  const path = match[1];
  const rawValue = match[2].trim();

  // Try to parse value as JSON-like
  let value;
  if (rawValue === 'true') value = true;
  else if (rawValue === 'false') value = false;
  else if (rawValue === 'null') value = null;
  else if (/^-?\d+(\.\d+)?$/.test(rawValue)) value = parseFloat(rawValue);
  else if (rawValue.startsWith('"') && rawValue.endsWith('"')) {
    const parsed = parseQuotedString(rawValue, 0);
    value = parsed ? parsed.value : rawValue;
  } else {
    // Treat as raw string value
    value = rawValue;
  }

  return {
    type: COMMAND_TYPES.SET_CONFIG,
    path,
    value,
  };
}
