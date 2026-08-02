/**
 * Components Board — Twin Sync Tests
 * Bidirectional: Visual ↔ Components:circuit ↔ Components:board
 */

import {
  stateToCircuit, stateToBoard,
  circuitTextToCommands, boardTextToCommands,
  syncStateToText, syncTextToEngine,
} from '../src/controller/twin-sync.js';

// =============================================================================
// Test Harness
// =============================================================================
let passed = 0, failed = 0;
const failures = [];
function assert(condition, msg) { if (condition) passed++; else { failed++; failures.push(msg); } }
function eq(a, b, msg) { const pass = JSON.stringify(a) === JSON.stringify(b); if (pass) passed++; else { failed++; failures.push(`${msg}: got ${JSON.stringify(a)}, expected ${JSON.stringify(b)}`); } }
function includes(str, sub, msg) { if (str.includes(sub)) passed++; else { failed++; failures.push(`${msg}: "${sub}" not found in output`); } }
function section(name) { console.log(`  ${name}`); }

// =============================================================================
// MOCK ENGINE STATE
// =============================================================================
const MOCK_STATE = {
  pages: [{ name: 'CPU' }, { name: 'Memory' }],
  component: {
    devices: {
      'U1': { part: 'digital.74HC04', page: 'CPU' },
      'U2': { part: 'digital.74HC161', page: 'CPU' },
      'U3': { part: 'memory.62256', page: 'Memory' },
    },
    connections: [
      { from: 'U1.1Y', to: 'U2.CLK' },
      { from: 'U2.QA', to: 'U3.A0' },
    ],
  },
  board: {
    placements: {
      'U1': { x: 30, y: 40, rotation: 0, page: 'CPU' },
      'U2': { x: 100, y: 40, rotation: 0, page: 'CPU' },
      'U3': { x: 60, y: 30, rotation: 0, page: 'Memory' },
    },
    routes: [
      { from: 'U1.1Y', to: 'U2.CLK', via: [{ x: 65, y: 40 }, { x: 65, y: 30 }] },
    ],
    labels: [
      { text: 'CLK', x: 65, y: 25, page: 'CPU' },
    ],
  },
  config: { paper: { size: 'A4', orientation: 'landscape' } },
};

// =============================================================================
// STATE → CIRCUIT TEXT
// =============================================================================

section('stateToCircuit — generates valid text');
{
  const text = stateToCircuit(MOCK_STATE);
  includes(text, '@page CPU', 'has CPU page');
  includes(text, '@page Memory', 'has Memory page');
  includes(text, 'device U1, digital.74HC04;', 'has U1 device');
  includes(text, 'device U2, digital.74HC161;', 'has U2 device');
  includes(text, 'device U3, memory.62256;', 'has U3 device');
  includes(text, 'connect U1.1Y -> U2.CLK;', 'has connection');
}

section('stateToCircuit — devices on correct pages');
{
  const text = stateToCircuit(MOCK_STATE);
  const lines = text.split('\n');
  const cpuIdx = lines.findIndex(l => l.includes('@page CPU'));
  const memIdx = lines.findIndex(l => l.includes('@page Memory'));
  const u1Idx = lines.findIndex(l => l.includes('device U1'));
  const u3Idx = lines.findIndex(l => l.includes('device U3'));
  assert(u1Idx > cpuIdx && u1Idx < memIdx, 'U1 between CPU and Memory headers');
  assert(u3Idx > memIdx, 'U3 after Memory header');
}

// =============================================================================
// STATE → BOARD TEXT
// =============================================================================

section('stateToBoard — generates valid text');
{
  const text = stateToBoard(MOCK_STATE);
  includes(text, '@page CPU', 'board has CPU page');
  includes(text, '@page Memory', 'board has Memory page');
  includes(text, 'paper A4 landscape;', 'board has paper');
  includes(text, 'place U1 at (30, 40) rotate 0;', 'board has U1 placement');
  includes(text, 'place U2 at (100, 40) rotate 0;', 'board has U2 placement');
  includes(text, 'place U3 at (60, 30) rotate 0;', 'board has U3 placement');
  includes(text, 'route U1.1Y -> U2.CLK via (65, 40) (65, 30);', 'board has route');
  includes(text, 'label "CLK" at (65, 25);', 'board has label');
}

// =============================================================================
// CIRCUIT TEXT → COMMANDS (add device)
// =============================================================================

section('circuitTextToCommands — new device → place command');
{
  const newText = `@page CPU
device U1, digital.74HC04;
device U2, digital.74HC161;
device U6, digital.74HC00;
connect U1.1Y -> U2.CLK;

@page Memory
device U3, memory.62256;
connect U2.QA -> U3.A0;
`;
  const cmds = circuitTextToCommands(newText, MOCK_STATE);
  assert(cmds.some(c => c.includes('place U6') && c.includes('74HC00')), 'new device U6 generates place command');
}

section('circuitTextToCommands — removed device → delete command');
{
  const newText = `@page CPU
device U1, digital.74HC04;
connect U1.1Y -> U2.CLK;

@page Memory
device U3, memory.62256;
connect U2.QA -> U3.A0;
`;
  const cmds = circuitTextToCommands(newText, MOCK_STATE);
  assert(cmds.some(c => c.includes('delete U2')), 'removed U2 generates delete command');
}

section('circuitTextToCommands — new connection → connect command');
{
  const newText = `@page CPU
device U1, digital.74HC04;
device U2, digital.74HC161;
connect U1.1Y -> U2.CLK;
connect U1.2Y -> U2.ENP;

@page Memory
device U3, memory.62256;
connect U2.QA -> U3.A0;
`;
  const cmds = circuitTextToCommands(newText, MOCK_STATE);
  assert(cmds.some(c => c.includes('connect U1.2Y -> U2.ENP')), 'new connection generates connect command');
}

section('circuitTextToCommands — removed connection → disconnect command');
{
  const newText = `@page CPU
device U1, digital.74HC04;
device U2, digital.74HC161;

@page Memory
device U3, memory.62256;
connect U2.QA -> U3.A0;
`;
  const cmds = circuitTextToCommands(newText, MOCK_STATE);
  assert(cmds.some(c => c.includes('disconnect U1.1Y -> U2.CLK')), 'removed connection generates disconnect');
}

section('circuitTextToCommands — no change → no commands');
{
  const text = stateToCircuit(MOCK_STATE);
  const cmds = circuitTextToCommands(text, MOCK_STATE);
  eq(cmds.length, 0, 'no change = no commands');
}

// =============================================================================
// BOARD TEXT → COMMANDS (move/rotate)
// =============================================================================

section('boardTextToCommands — move device → move command');
{
  const newText = `@page CPU
paper A4 landscape;
place U1 at (50, 60) rotate 0;
place U2 at (100, 40) rotate 0;

@page Memory
paper A4 landscape;
place U3 at (60, 30) rotate 0;
`;
  const cmds = boardTextToCommands(newText, MOCK_STATE);
  assert(cmds.some(c => c.includes('move U1 to (50, 60)')), 'moved U1 generates move command');
}

section('boardTextToCommands — rotate device → rotate command');
{
  const newText = `@page CPU
paper A4 landscape;
place U1 at (30, 40) rotate 90;
place U2 at (100, 40) rotate 0;

@page Memory
paper A4 landscape;
place U3 at (60, 30) rotate 0;
`;
  const cmds = boardTextToCommands(newText, MOCK_STATE);
  assert(cmds.some(c => c.includes('rotate U1 90')), 'rotated U1 generates rotate command');
}

section('boardTextToCommands — no change → no commands');
{
  const text = stateToBoard(MOCK_STATE);
  const cmds = boardTextToCommands(text, MOCK_STATE);
  eq(cmds.length, 0, 'no board change = no commands');
}

// =============================================================================
// FULL SYNC CYCLE
// =============================================================================

section('syncStateToText — returns both files');
{
  const result = syncStateToText(MOCK_STATE);
  assert(typeof result.circuit === 'string', 'circuit is string');
  assert(typeof result.board === 'string', 'board is string');
  includes(result.circuit, 'device U1', 'circuit has U1');
  includes(result.board, 'place U1', 'board has U1');
}

section('syncTextToEngine — circuit side');
{
  const newCircuit = stateToCircuit(MOCK_STATE) + 'device U7, digital.74HC32;\n';
  const cmds = syncTextToEngine('circuit', newCircuit, MOCK_STATE);
  assert(cmds.some(c => c.includes('U7')), 'circuit edit produces U7 command');
}

section('syncTextToEngine — board side');
{
  // Move U1 in board text
  const boardText = stateToBoard(MOCK_STATE).replace('place U1 at (30, 40)', 'place U1 at (80, 80)');
  const cmds = syncTextToEngine('board', boardText, MOCK_STATE);
  assert(cmds.some(c => c.includes('move U1')), 'board edit produces move command');
}

// =============================================================================
// ROUND-TRIP: state → text → commands → should be empty (stable)
// =============================================================================

section('Round-trip stability: state → text → parse → commands = empty');
{
  const circuitText = stateToCircuit(MOCK_STATE);
  const boardText = stateToBoard(MOCK_STATE);
  const circuitCmds = circuitTextToCommands(circuitText, MOCK_STATE);
  const boardCmds = boardTextToCommands(boardText, MOCK_STATE);
  eq(circuitCmds.length, 0, 'circuit round-trip stable');
  eq(boardCmds.length, 0, 'board round-trip stable');
}

// =============================================================================
// RESULTS
// =============================================================================
console.log();
if (failed > 0) {
  console.log(`━━━ Results: ${passed} passed, ${failed} FAILED ━━━`);
  failures.forEach(f => console.log(`  ✗ ${f}`));
  process.exit(1);
} else {
  console.log(`━━━ Results: ${passed} passed, 0 failed ━━━`);
}
