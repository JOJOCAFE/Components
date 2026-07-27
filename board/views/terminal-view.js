// terminal-view.js — Command parser for board terminal
// Pure parsing module. No DOM, no fetch. Execution stays in app.js.

/**
 * Parse a terminal command string into a structured action object.
 * @param {string} text - Raw command text from the terminal input
 * @returns {{ type: string, [key: string]: any }} Parsed action object
 */
export function parseCommand(text) {
  const raw = (text || '').trim();
  if (!raw) return { type: 'unknown' };

  const parts = raw.split(/\s+/);
  const cmd = parts[0].toLowerCase();

  switch (cmd) {
    case 'help':
      return { type: 'help' };

    case 'board':
      return { type: 'board' };

    case 'discard-profile':
      return { type: 'discard-profile' };

    case 'cancel-route':
      return { type: 'cancel-route' };

    case 'route-pen-start':
      // route-pen-start <from> <to>
      return { type: 'route-pen-start', from: parts[1] || '', to: parts[2] || '' };

    case 'route-via':
      // route-via <from> <to> <point1> <point2> ...
      return {
        type: 'route-via',
        from: parts[1] || '',
        to: parts[2] || '',
        points: parts.slice(3)
      };

    case 'pen-to':
      // pen-to <target>
      return { type: 'pen-to', target: parts[1] || '' };

    case 'pen-down':
      return { type: 'pen-down' };

    case 'pen-up':
      return { type: 'pen-up' };

    case 'fd':
    case 'bk':
      // fd <distance> | bk <distance>
      return { type: 'pen-move', direction: cmd, distance: parseNumber(parts[1]) };

    case 'rt':
    case 'lt':
      // rt <degrees> | lt <degrees>
      return { type: 'pen-turn', direction: cmd, degrees: parseNumber(parts[1]) };

    case 'run':
      // run <test>
      return { type: 'run', test: parts[1] || '' };

    case 'drive':
      // drive <target> <value>
      return { type: 'drive', target: parts[1] || '', value: parts[2] || '' };

    case 'watch':
      // watch <probe>
      return { type: 'watch', probe: parts[1] || '' };

    case 'connect':
      // connect <from> <to>
      return { type: 'connect', from: parts[1] || '', to: parts[2] || '' };

    case 'disconnect':
      // disconnect <from> <to>
      return { type: 'disconnect', from: parts[1] || '', to: parts[2] || '' };

    default:
      return { type: 'unknown' };
  }
}

/**
 * Format probe results into a readable sentence.
 * @param {Array<{ name: string, value: any }>} probes - Array of probe readings
 * @returns {string} Human-readable summary of probe values
 */
export function probeSentence(probes) {
  if (!probes || probes.length === 0) return 'No probes active.';

  const items = probes.map(p => `${p.name} = ${formatValue(p.value)}`);

  if (items.length === 1) return items[0];
  if (items.length === 2) return `${items[0]} and ${items[1]}`;

  return items.slice(0, -1).join(', ') + ', and ' + items[items.length - 1];
}

// --- Internal helpers ---

function parseNumber(str) {
  const n = Number(str);
  return Number.isFinite(n) ? n : 0;
}

function formatValue(value) {
  if (value === undefined || value === null) return '?';
  if (typeof value === 'number') return String(value);
  if (typeof value === 'boolean') return value ? 'HIGH' : 'LOW';
  return String(value);
}
