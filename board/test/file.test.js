/**
 * Components Board — File Model Tests
 * Phase 2, Task 2.1: Tests for Components:circuit, Components:board, Components:command parsing
 */

import {
  FILE_TYPES, FILE_NAMES, LINE_TYPES,
  parseFile, parseLine,
  getPageNames, getPage, getPageOffset, getPageRange,
  serializeDevice, serializeConnect, serializePaper, serializePlace,
  serializeRoute, serializeLabel,
  serializeCircuitFile, serializeBoardFile, serializeCommandFile,
  findDeviceLine, findPlacementLine, findDevicePage,
} from '../src/model/file.js';

// =============================================================================
// Test Harness (same pattern as Phase 1)
// =============================================================================

let passed = 0, failed = 0;
const failures = [];

function assert(condition, msg) {
  if (condition) { passed++; }
  else { failed++; failures.push(msg); }
}
function eq(a, b, msg) {
  const pass = JSON.stringify(a) === JSON.stringify(b);
  if (pass) { passed++; }
  else { failed++; failures.push(`${msg}: got ${JSON.stringify(a)}, expected ${JSON.stringify(b)}`); }
}
function section(name) { console.log(`  ${name}`); }

// =============================================================================
// FILE NAMES & TYPES
// =============================================================================

section('File names and types');
eq(FILE_NAMES[FILE_TYPES.CIRCUIT], 'Components:circuit', 'circuit file name');
eq(FILE_NAMES[FILE_TYPES.BOARD], 'Components:board', 'board file name');
eq(FILE_NAMES[FILE_TYPES.COMMAND], 'Components:command', 'command file name');

// =============================================================================
// CIRCUIT FILE PARSING
// =============================================================================

section('Components:circuit — parse device');
{
  const line = parseLine('device U1, digital.74HC04;', FILE_TYPES.CIRCUIT);
  eq(line.type, LINE_TYPES.DEVICE, 'device type');
  eq(line.ref, 'U1', 'device ref');
  eq(line.part, 'digital.74HC04', 'device part');
}

section('Components:circuit — parse device without semicolon');
{
  const line = parseLine('device U2, memory.62256', FILE_TYPES.CIRCUIT);
  eq(line.type, LINE_TYPES.DEVICE, 'device type no semicolon');
  eq(line.ref, 'U2', 'device ref no semicolon');
  eq(line.part, 'memory.62256', 'device part no semicolon');
}

section('Components:circuit — parse connect');
{
  const line = parseLine('connect U1.1Y -> U2.CLK;', FILE_TYPES.CIRCUIT);
  eq(line.type, LINE_TYPES.CONNECT, 'connect type');
  eq(line.from, 'U1.1Y', 'connect from');
  eq(line.to, 'U2.CLK', 'connect to');
}

section('Components:circuit — parse comment');
{
  const line = parseLine('// This is a comment', FILE_TYPES.CIRCUIT);
  eq(line.type, LINE_TYPES.COMMENT, 'comment type');
  eq(line.text, 'This is a comment', 'comment text');
}

section('Components:circuit — parse hash comment');
{
  const line = parseLine('# Another comment', FILE_TYPES.CIRCUIT);
  eq(line.type, LINE_TYPES.COMMENT, 'hash comment type');
  eq(line.text, 'Another comment', 'hash comment text');
}

section('Components:circuit — parse blank');
{
  const line = parseLine('', FILE_TYPES.CIRCUIT);
  eq(line.type, LINE_TYPES.BLANK, 'blank type');
}

section('Components:circuit — parse unknown');
{
  const line = parseLine('something weird', FILE_TYPES.CIRCUIT);
  eq(line.type, LINE_TYPES.UNKNOWN, 'unknown type');
  eq(line.text, 'something weird', 'unknown text preserved');
}

// =============================================================================
// BOARD FILE PARSING
// =============================================================================

section('Components:board — parse paper');
{
  const line = parseLine('paper A4 landscape;', FILE_TYPES.BOARD);
  eq(line.type, LINE_TYPES.PAPER, 'paper type');
  eq(line.size, 'A4', 'paper size');
  eq(line.orientation, 'landscape', 'paper orientation');
}

section('Components:board — parse paper portrait');
{
  const line = parseLine('paper A3 portrait;', FILE_TYPES.BOARD);
  eq(line.type, LINE_TYPES.PAPER, 'paper portrait type');
  eq(line.size, 'A3', 'paper portrait size');
  eq(line.orientation, 'portrait', 'paper portrait orientation');
}

section('Components:board — parse paper default orientation');
{
  const line = parseLine('paper A0;', FILE_TYPES.BOARD);
  eq(line.type, LINE_TYPES.PAPER, 'paper default type');
  eq(line.size, 'A0', 'paper default size');
  eq(line.orientation, 'landscape', 'paper default orientation');
}

section('Components:board — parse place');
{
  const line = parseLine('place U1 at (50, 30) rotate 0;', FILE_TYPES.BOARD);
  eq(line.type, LINE_TYPES.PLACE, 'place type');
  eq(line.ref, 'U1', 'place ref');
  eq(line.x, 50, 'place x');
  eq(line.y, 30, 'place y');
  eq(line.rotation, 0, 'place rotation');
}

section('Components:board — parse place with float coords');
{
  const line = parseLine('place U3 at (42.5, -15.0) rotate 90;', FILE_TYPES.BOARD);
  eq(line.type, LINE_TYPES.PLACE, 'place float type');
  eq(line.ref, 'U3', 'place float ref');
  eq(line.x, 42.5, 'place float x');
  eq(line.y, -15.0, 'place float y');
  eq(line.rotation, 90, 'place float rotation');
}

section('Components:board — parse place without rotate');
{
  const line = parseLine('place U5 at (10, 20);', FILE_TYPES.BOARD);
  eq(line.type, LINE_TYPES.PLACE, 'place no-rotate type');
  eq(line.ref, 'U5', 'place no-rotate ref');
  eq(line.rotation, 0, 'place no-rotate defaults to 0');
}

section('Components:board — parse route');
{
  const line = parseLine('route U1.1Y -> U2.CLK via (85, 30) (85, 45) (120, 45);', FILE_TYPES.BOARD);
  eq(line.type, LINE_TYPES.ROUTE, 'route type');
  eq(line.from, 'U1.1Y', 'route from');
  eq(line.to, 'U2.CLK', 'route to');
  eq(line.via.length, 3, 'route via count');
  eq(line.via[0], { x: 85, y: 30 }, 'route via[0]');
  eq(line.via[1], { x: 85, y: 45 }, 'route via[1]');
  eq(line.via[2], { x: 120, y: 45 }, 'route via[2]');
}

section('Components:board — parse label');
{
  const line = parseLine('label "VCC" at (10, 90);', FILE_TYPES.BOARD);
  eq(line.type, LINE_TYPES.LABEL, 'label type');
  eq(line.text, 'VCC', 'label text');
  eq(line.x, 10, 'label x');
  eq(line.y, 90, 'label y');
}

// =============================================================================
// COMMAND FILE PARSING
// =============================================================================

section('Components:command — parse timestamped entry');
{
  const line = parseLine('[12:01] place U1 at (50, 30)', FILE_TYPES.COMMAND);
  eq(line.type, LINE_TYPES.COMMAND_ENTRY, 'ts entry type');
  eq(line.timestamp, '12:01', 'ts entry timestamp');
  eq(line.command, 'place U1 at (50, 30)', 'ts entry command');
}

section('Components:command — parse timestamped entry with seconds');
{
  const line = parseLine('[14:30:05] connect U1.1Y -> U2.CLK', FILE_TYPES.COMMAND);
  eq(line.type, LINE_TYPES.COMMAND_ENTRY, 'ts seconds type');
  eq(line.timestamp, '14:30:05', 'ts seconds timestamp');
  eq(line.command, 'connect U1.1Y -> U2.CLK', 'ts seconds command');
}

section('Components:command — parse user input');
{
  const line = parseLine('> place U1 at (50, 30)', FILE_TYPES.COMMAND);
  eq(line.type, LINE_TYPES.COMMAND_ENTRY, 'input type');
  eq(line.timestamp, null, 'input no timestamp');
  eq(line.command, 'place U1 at (50, 30)', 'input command');
}

section('Components:command — parse empty input prompt');
{
  const line = parseLine('> ', FILE_TYPES.COMMAND);
  eq(line.type, LINE_TYPES.COMMAND_ENTRY, 'empty input type');
  eq(line.command, '', 'empty input command');
}

// =============================================================================
// MULTI-PAGE FILE PARSING
// =============================================================================

section('Multi-page circuit file');
{
  const text = `@page CPU
device U1, digital.74HC04;
device U2, digital.74HC161;
connect U1.1Y -> U2.CLK;

@page Memory
device U3, memory.62256;
connect U2.QA -> U3.A0;
`;
  const file = parseFile(text, FILE_TYPES.CIRCUIT);
  eq(file.type, FILE_TYPES.CIRCUIT, 'file type');
  eq(file.pages.length, 2, 'page count');
  eq(file.pages[0].name, 'CPU', 'page 0 name');
  eq(file.pages[1].name, 'Memory', 'page 1 name');

  // CPU page has 4 content lines (2 devices + 1 connect + 1 blank)
  const cpuDevices = file.pages[0].lines.filter(l => l.parsed.type === LINE_TYPES.DEVICE);
  eq(cpuDevices.length, 2, 'CPU device count');
  eq(cpuDevices[0].parsed.ref, 'U1', 'CPU device 0 ref');
  eq(cpuDevices[1].parsed.ref, 'U2', 'CPU device 1 ref');

  const cpuConns = file.pages[0].lines.filter(l => l.parsed.type === LINE_TYPES.CONNECT);
  eq(cpuConns.length, 1, 'CPU connect count');

  // Memory page
  const memDevices = file.pages[1].lines.filter(l => l.parsed.type === LINE_TYPES.DEVICE);
  eq(memDevices.length, 1, 'Memory device count');
  eq(memDevices[0].parsed.ref, 'U3', 'Memory device ref');
}

section('Multi-page board file');
{
  const text = `@page CPU
paper A4 landscape;
place U1 at (50, 30) rotate 0;
place U2 at (120, 30) rotate 0;
route U1.1Y -> U2.CLK via (85, 30) (85, 45) (120, 45);

@page Memory
paper A3 landscape;
place U3 at (80, 50) rotate 0;
`;
  const file = parseFile(text, FILE_TYPES.BOARD);
  eq(file.pages.length, 2, 'board page count');
  eq(file.pages[0].name, 'CPU', 'board page 0 name');
  eq(file.pages[1].name, 'Memory', 'board page 1 name');

  const cpuPlacements = file.pages[0].lines.filter(l => l.parsed.type === LINE_TYPES.PLACE);
  eq(cpuPlacements.length, 2, 'CPU placements');

  const cpuRoutes = file.pages[0].lines.filter(l => l.parsed.type === LINE_TYPES.ROUTE);
  eq(cpuRoutes.length, 1, 'CPU routes');

  const memPaper = file.pages[1].lines.filter(l => l.parsed.type === LINE_TYPES.PAPER);
  eq(memPaper.length, 1, 'Memory paper');
  eq(memPaper[0].parsed.size, 'A3', 'Memory paper A3');
}

section('File with no @page (default page)');
{
  const text = `device U1, digital.74HC04;
connect U1.1A -> U1.1Y;
`;
  const file = parseFile(text, FILE_TYPES.CIRCUIT);
  eq(file.pages.length, 1, 'single default page');
  eq(file.pages[0].name, '', 'default page has empty name');
  const devices = file.pages[0].lines.filter(l => l.parsed.type === LINE_TYPES.DEVICE);
  eq(devices.length, 1, 'default page devices');
}

section('Empty file');
{
  const file = parseFile('', FILE_TYPES.CIRCUIT);
  eq(file.pages.length, 1, 'empty file has 1 default page');
  // ''.split('\n') = [''] → 1 blank line
  eq(file.pages[0].lines.length, 1, 'empty file has 1 blank line');
  eq(file.pages[0].lines[0].parsed.type, LINE_TYPES.BLANK, 'empty file line is blank');
}

// =============================================================================
// PAGE UTILITIES
// =============================================================================

section('getPageNames');
{
  const text = `@page CPU
device U1, digital.74HC04;
@page Memory
device U2, memory.62256;
@page ALU
device U3, digital.74HC283;
`;
  const file = parseFile(text, FILE_TYPES.CIRCUIT);
  eq(getPageNames(file), ['CPU', 'Memory', 'ALU'], 'page names');
}

section('getPage');
{
  const text = `@page CPU
device U1, digital.74HC04;
@page Memory
device U2, memory.62256;
`;
  const file = parseFile(text, FILE_TYPES.CIRCUIT);
  const mem = getPage(file, 'Memory');
  assert(mem !== null, 'getPage found Memory');
  eq(mem.name, 'Memory', 'getPage name');
  assert(getPage(file, 'NonExistent') === null, 'getPage returns null for missing');
}

section('getPageOffset');
{
  const text = `@page CPU
device U1, digital.74HC04;
device U2, digital.74HC161;

@page Memory
device U3, memory.62256;
`;
  const file = parseFile(text, FILE_TYPES.CIRCUIT);
  eq(getPageOffset(file, 'CPU'), 0, 'CPU offset at line 0');
  eq(getPageOffset(file, 'Memory'), 4, 'Memory offset at line 4');
  eq(getPageOffset(file, 'Missing'), -1, 'missing page offset -1');
}

section('getPageRange');
{
  const text = `@page CPU
device U1, digital.74HC04;
device U2, digital.74HC161;
@page Memory
device U3, memory.62256;
`;
  // Lines: 0=@page CPU, 1=device U1, 2=device U2, 3=@page Memory, 4=device U3, 5=(empty from trailing \n)
  const file = parseFile(text, FILE_TYPES.CIRCUIT);
  const cpuRange = getPageRange(file, 'CPU');
  eq(cpuRange.start, 0, 'CPU range start');
  eq(cpuRange.end, 2, 'CPU range end');
  const memRange = getPageRange(file, 'Memory');
  eq(memRange.start, 3, 'Memory range start');
  eq(memRange.end, 5, 'Memory range end');
  assert(getPageRange(file, 'X') === null, 'missing range null');
}

// =============================================================================
// SERIALIZATION
// =============================================================================

section('Serialize individual statements');
{
  eq(serializeDevice('U1', 'digital.74HC04'), 'device U1, digital.74HC04;', 'serialize device');
  eq(serializeConnect('U1.1Y', 'U2.CLK'), 'connect U1.1Y -> U2.CLK;', 'serialize connect');
  eq(serializePaper('A4', 'landscape'), 'paper A4 landscape;', 'serialize paper');
  eq(serializePlace('U1', 50, 30, 0), 'place U1 at (50, 30) rotate 0;', 'serialize place');
  eq(serializePlace('U2', 42.5, -15, 90), 'place U2 at (42.5, -15) rotate 90;', 'serialize place float');
  eq(
    serializeRoute('U1.1Y', 'U2.CLK', [{ x: 85, y: 30 }, { x: 85, y: 45 }]),
    'route U1.1Y -> U2.CLK via (85, 30) (85, 45);',
    'serialize route'
  );
  eq(serializeLabel('VCC', 10, 90), 'label "VCC" at (10, 90);', 'serialize label');
}

section('Serialize circuit file');
{
  const pages = [
    { name: 'CPU', statements: [
      { type: 'device', ref: 'U1', part: 'digital.74HC04' },
      { type: 'connect', from: 'U1.1Y', to: 'U2.CLK' },
    ]},
    { name: 'Memory', statements: [
      { type: 'device', ref: 'U3', part: 'memory.62256' },
    ]},
  ];
  const text = serializeCircuitFile(pages);
  assert(text.includes('@page CPU'), 'circuit file has CPU page');
  assert(text.includes('device U1, digital.74HC04;'), 'circuit file has device');
  assert(text.includes('connect U1.1Y -> U2.CLK;'), 'circuit file has connect');
  assert(text.includes('@page Memory'), 'circuit file has Memory page');
  assert(text.includes('device U3, memory.62256;'), 'circuit file has U3');
}

section('Serialize board file');
{
  const pages = [
    { name: 'CPU', statements: [
      { type: 'paper', size: 'A4', orientation: 'landscape' },
      { type: 'place', ref: 'U1', x: 50, y: 30, rotation: 0 },
      { type: 'route', from: 'U1.1Y', to: 'U2.CLK', via: [{ x: 85, y: 30 }] },
    ]},
  ];
  const text = serializeBoardFile(pages);
  assert(text.includes('@page CPU'), 'board file has CPU page');
  assert(text.includes('paper A4 landscape;'), 'board file has paper');
  assert(text.includes('place U1 at (50, 30) rotate 0;'), 'board file has place');
  assert(text.includes('route U1.1Y -> U2.CLK via (85, 30);'), 'board file has route');
}

section('Serialize command file');
{
  const entries = [
    { timestamp: '12:01', command: 'place U1 at (50, 30)' },
    { timestamp: null, command: 'connect U1.1Y -> U2.CLK' },
    { timestamp: '12:02', command: 'undo' },
  ];
  const text = serializeCommandFile(entries);
  assert(text.includes('[12:01] place U1 at (50, 30)'), 'command file ts entry');
  assert(text.includes('> connect U1.1Y -> U2.CLK'), 'command file user input');
  assert(text.includes('[12:02] undo'), 'command file undo entry');
}

// =============================================================================
// ROUND-TRIP: parse → serialize → parse
// =============================================================================

section('Round-trip: circuit file');
{
  const original = `@page CPU
device U1, digital.74HC04;
device U2, digital.74HC161;
connect U1.1Y -> U2.CLK;

@page Memory
device U3, memory.62256;
connect U2.QA -> U3.A0;
`;
  const file = parseFile(original, FILE_TYPES.CIRCUIT);
  // Re-serialize from parsed data
  const pages = file.pages.map(p => ({
    name: p.name,
    statements: p.lines
      .filter(l => l.parsed.type !== LINE_TYPES.BLANK && l.parsed.type !== LINE_TYPES.COMMENT)
      .map(l => l.parsed),
  }));
  const reserialized = serializeCircuitFile(pages);
  const reparsed = parseFile(reserialized, FILE_TYPES.CIRCUIT);
  eq(getPageNames(reparsed), ['CPU', 'Memory'], 'round-trip preserves pages');
  const devices = reparsed.pages[0].lines.filter(l => l.parsed.type === LINE_TYPES.DEVICE);
  eq(devices.length, 2, 'round-trip preserves devices');
  eq(devices[0].parsed.ref, 'U1', 'round-trip preserves U1');
}

section('Round-trip: board file');
{
  const original = `@page CPU
paper A4 landscape;
place U1 at (50, 30) rotate 0;
route U1.1Y -> U2.CLK via (85, 30) (85, 45);
`;
  const file = parseFile(original, FILE_TYPES.BOARD);
  const pages = file.pages.map(p => ({
    name: p.name,
    statements: p.lines
      .filter(l => l.parsed.type !== LINE_TYPES.BLANK)
      .map(l => l.parsed),
  }));
  const reserialized = serializeBoardFile(pages);
  const reparsed = parseFile(reserialized, FILE_TYPES.BOARD);
  const placements = reparsed.pages[0].lines.filter(l => l.parsed.type === LINE_TYPES.PLACE);
  eq(placements.length, 1, 'round-trip board placements');
  eq(placements[0].parsed.ref, 'U1', 'round-trip board ref');
  eq(placements[0].parsed.x, 50, 'round-trip board x');
}

// =============================================================================
// FIND UTILITIES
// =============================================================================

section('findDeviceLine');
{
  const text = `@page CPU
device U1, digital.74HC04;
device U2, digital.74HC161;
@page Memory
device U3, memory.62256;
`;
  const file = parseFile(text, FILE_TYPES.CIRCUIT);
  eq(findDeviceLine(file, 'U1'), 1, 'find U1 at line 1');
  eq(findDeviceLine(file, 'U2'), 2, 'find U2 at line 2');
  eq(findDeviceLine(file, 'U3'), 4, 'find U3 at line 4');
  eq(findDeviceLine(file, 'U99'), -1, 'find missing device -1');
}

section('findPlacementLine');
{
  const text = `@page CPU
place U1 at (50, 30) rotate 0;
place U2 at (120, 30) rotate 0;
@page Memory
place U3 at (80, 50) rotate 0;
`;
  const file = parseFile(text, FILE_TYPES.BOARD);
  eq(findPlacementLine(file, 'U1'), 1, 'find placement U1 line 1');
  eq(findPlacementLine(file, 'U3'), 4, 'find placement U3 line 4');
  eq(findPlacementLine(file, 'U99'), -1, 'find missing placement -1');
}

section('findDevicePage');
{
  const text = `@page CPU
device U1, digital.74HC04;
@page Memory
device U3, memory.62256;
`;
  const file = parseFile(text, FILE_TYPES.CIRCUIT);
  eq(findDevicePage(file, 'U1'), 'CPU', 'U1 on CPU page');
  eq(findDevicePage(file, 'U3'), 'Memory', 'U3 on Memory page');
  eq(findDevicePage(file, 'U99'), null, 'missing device null page');
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
