/**
 * Tests: Engine Delegation — Architecture Boundary Verification
 *
 * Verifies that Board modules correctly produce and delegate operations
 * to the EngineInterface, proving the new architecture boundaries work:
 *
 * 1. executor.js with engineInterface — place delegates add-device
 * 2. executor.js with engineInterface — connect delegates connect.apply
 * 3. executor.js with engineInterface — delete delegates remove-device
 * 4. connect-tool toOperations — correct operation format
 * 5. device-tray toOperation — correct operation format
 * 6. device-tray toRemoveOperation — correct operation format
 */

import { createExecutor } from '../src/controller/executor.js';
import { createConnectTool } from '../src/controller/connect-tool.js';
import { createDeviceTray } from '../src/controller/device-tray.js';
import { createEngineInterface } from '../src/engine-interface.js';
import { createEngineMock } from '../src/engine-mock.js';

let passed = 0;
let failed = 0;

function assert(cond, msg) {
  if (cond) { passed++; }
  else { failed++; console.error(`  FAIL: ${msg}`); }
}

function section(name) {
  console.log(`\n  ${name}`);
}

/**
 * Create an executor wired to a real engine mock, with a spy on submit.
 */
function makeExecutorWithEngine() {
  const mock = createEngineMock();
  const engine = createEngineInterface(mock);

  // Spy: wrap submit to capture calls
  const submitted = [];
  const originalSubmit = engine.submit.bind(engine);
  const spyEngine = {
    ...engine,
    submit(op) {
      submitted.push(op);
      return originalSubmit(op);
    },
  };

  // Rebuild interface with spy (the executor uses the interface's submit directly)
  // Since createEngineInterface returns a frozen object, we create a proxy interface
  const engineProxy = {
    getState: engine.getState,
    getDevices: engine.getDevices,
    getEdges: engine.getEdges,
    getSourceText: engine.getSourceText,
    getSourceRevision: engine.getSourceRevision,
    getTopologyDigest: engine.getTopologyDigest,
    getDiagnostics: engine.getDiagnostics,
    submit(op) {
      submitted.push(op);
      return originalSubmit(op);
    },
    submitBatch: engine.submitBatch,
    onChange: engine.onChange,
  };

  const executor = createExecutor(undefined, undefined, undefined, {
    engineInterface: engineProxy,
  });

  return { executor, submitted, engine };
}

// =============================================================================
// RUN ALL TESTS
// =============================================================================

async function runAll() {

  // ===========================================================================
  section('Executor + engineInterface — place delegates add-device');
  // ===========================================================================
  {
    const { executor, submitted } = makeExecutorWithEngine();

    const result = executor.execute({ type: 'place', ref: 'U1', part: 'digital.74HC04', x: 30, y: 40, rotation: 0 });

    assert(result.success === true, 'place command succeeds');
    assert(submitted.length === 1, 'one operation submitted to engine');

    const op = submitted[0];
    assert(op.kind === 'component.add-device', 'op.kind is component.add-device');
    assert(op.target === 'source', 'op.target is source');
    assert(op.intent !== undefined, 'op has intent');
    assert(op.intent.ref === 'U1', 'intent.ref is U1');
    assert(op.intent.part === 'digital.74HC04', 'intent.part is digital.74HC04');
  }

  // ===========================================================================
  section('Executor + engineInterface — connect delegates connect.apply');
  // ===========================================================================
  {
    const { executor, submitted } = makeExecutorWithEngine();

    // Place two devices first
    executor.execute({ type: 'place', ref: 'U1', part: 'digital.74HC04', x: 30, y: 40, rotation: 0 });
    executor.execute({ type: 'place', ref: 'U2', part: 'digital.74HC08', x: 80, y: 40, rotation: 0 });
    submitted.length = 0; // clear add-device submissions

    const result = executor.execute({ type: 'connect', from: 'U1.1Y', to: 'U2.1A', via: [] });

    assert(result.success === true, 'connect command succeeds');
    assert(submitted.length === 1, 'one operation submitted for connect');

    const op = submitted[0];
    assert(op.kind === 'component.connect.apply', 'op.kind is component.connect.apply');
    assert(op.target === 'source', 'op.target is source');
    assert(op.intent !== undefined, 'op has intent');
    assert(op.intent.from === 'U1.1Y', 'intent.from is U1.1Y');
    assert(op.intent.to === 'U2.1A', 'intent.to is U2.1A');
  }

  // ===========================================================================
  section('Executor + engineInterface — delete delegates remove-device');
  // ===========================================================================
  {
    const { executor, submitted } = makeExecutorWithEngine();

    // Place a device first
    executor.execute({ type: 'place', ref: 'U1', part: 'digital.74HC04', x: 30, y: 40, rotation: 0 });
    submitted.length = 0; // clear add-device submission

    const result = executor.execute({ type: 'delete', ref: 'U1' });

    assert(result.success === true, 'delete command succeeds');
    assert(submitted.length === 1, 'one operation submitted for delete');

    const op = submitted[0];
    assert(op.kind === 'component.remove-device', 'op.kind is component.remove-device');
    assert(op.target === 'source', 'op.target is source');
    assert(op.intent !== undefined, 'op has intent');
    assert(op.intent.ref === 'U1', 'intent.ref is U1');
  }

  // ===========================================================================
  section('connect-tool toOperations — correct format');
  // ===========================================================================
  {
    const tool = createConnectTool();

    // Simulate a connection: click source pin, then target pin
    tool.clickPin('U1.1Y');
    tool.clickPoint({ x: 50, y: 40 });
    const commands = tool.clickPin('U2.1A');

    assert(commands !== null, 'clickPin returns commands on completion');
    assert(commands.length === 2, 'returns connect + route commands');

    const ops = tool.toOperations(commands);
    assert(ops !== null, 'toOperations returns non-null');

    // Verify circuitOp format
    assert(ops.circuitOp !== undefined, 'has circuitOp');
    assert(ops.circuitOp.kind === 'component.connect.apply', 'circuitOp.kind is connect.apply');
    assert(ops.circuitOp.target === 'source', 'circuitOp.target is source');
    assert(ops.circuitOp.intent !== undefined, 'circuitOp has intent');
    assert(ops.circuitOp.intent.from === 'U1.1Y', 'circuitOp.intent.from correct');
    assert(ops.circuitOp.intent.to === 'U2.1A', 'circuitOp.intent.to correct');

    // Verify boardCmd format
    assert(ops.boardCmd !== undefined, 'has boardCmd');
    assert(ops.boardCmd.type === 'route', 'boardCmd.type is route');
    assert(ops.boardCmd.from === 'U1.1Y', 'boardCmd.from correct');
    assert(ops.boardCmd.to === 'U2.1A', 'boardCmd.to correct');
    assert(Array.isArray(ops.boardCmd.via), 'boardCmd.via is array');
    assert(ops.boardCmd.via.length === 1, 'boardCmd.via has one turning point');
  }

  // ===========================================================================
  section('device-tray toOperation — correct format');
  // ===========================================================================
  {
    const tray = createDeviceTray({ library: null });

    const placeCmd = { type: 'place', ref: 'U3', part: 'digital.74HC161', x: 55, y: 40, rotation: 90 };
    const ops = tray.toOperation(placeCmd);

    assert(ops !== null, 'toOperation returns non-null');

    // Verify circuitOp format
    assert(ops.circuitOp !== undefined, 'has circuitOp');
    assert(ops.circuitOp.kind === 'component.add-device', 'circuitOp.kind is add-device');
    assert(ops.circuitOp.target === 'source', 'circuitOp.target is source');
    assert(ops.circuitOp.intent !== undefined, 'circuitOp has intent');
    assert(ops.circuitOp.intent.ref === 'U3', 'circuitOp.intent.ref correct');
    assert(ops.circuitOp.intent.part === 'digital.74HC161', 'circuitOp.intent.part correct');

    // Verify boardCmd format
    assert(ops.boardCmd !== undefined, 'has boardCmd');
    assert(ops.boardCmd.type === 'place', 'boardCmd.type is place');
    assert(ops.boardCmd.ref === 'U3', 'boardCmd.ref correct');
    assert(ops.boardCmd.part === 'digital.74HC161', 'boardCmd.part correct');
    assert(ops.boardCmd.x === 55, 'boardCmd.x correct');
    assert(ops.boardCmd.y === 40, 'boardCmd.y correct');
    assert(ops.boardCmd.rotation === 90, 'boardCmd.rotation correct');
  }

  // ===========================================================================
  section('device-tray toRemoveOperation — correct format');
  // ===========================================================================
  {
    const tray = createDeviceTray({ library: null });

    const ops = tray.toRemoveOperation('U5');

    assert(ops !== null, 'toRemoveOperation returns non-null');

    // Verify circuitOp format
    assert(ops.circuitOp !== undefined, 'has circuitOp');
    assert(ops.circuitOp.kind === 'component.remove-device', 'circuitOp.kind is remove-device');
    assert(ops.circuitOp.target === 'source', 'circuitOp.target is source');
    assert(ops.circuitOp.intent !== undefined, 'circuitOp has intent');
    assert(ops.circuitOp.intent.ref === 'U5', 'circuitOp.intent.ref is U5');

    // Verify no boardCmd (removal doesn't need one — executor handles board cleanup)
    assert(ops.boardCmd === undefined, 'no boardCmd for remove (executor handles board cleanup)');
  }

  // ===========================================================================
  section('Contract format verification — all operations have kind, target, intent');
  // ===========================================================================
  {
    // Collect all circuitOps from different sources
    const tray = createDeviceTray({ library: null });
    const tool = createConnectTool();

    const addOp = tray.toOperation({ type: 'place', ref: 'U1', part: 'digital.74HC04', x: 0, y: 0, rotation: 0 });
    const removeOp = tray.toRemoveOperation('U1');

    tool.clickPin('U1.1Y');
    const cmds = tool.clickPin('U2.1A');
    const connectOps = tool.toOperations(cmds);

    const allOps = [addOp.circuitOp, removeOp.circuitOp, connectOps.circuitOp];

    for (const op of allOps) {
      assert(typeof op.kind === 'string' && op.kind.length > 0, `op has non-empty kind: ${op.kind}`);
      assert(op.target === 'source', `op.target is "source" (got ${op.target})`);
      assert(typeof op.intent === 'object' && op.intent !== null, `op has intent object`);
    }

    // All kinds start with 'component.'
    for (const op of allOps) {
      assert(op.kind.startsWith('component.'), `kind starts with component.: ${op.kind}`);
    }
  }

  // ===========================================================================
  // SUMMARY
  // ===========================================================================

  console.log(`\n  engine-delegation: ${passed} passed, ${failed} failed\n`);
  if (failed > 0) process.exit(1);
}

runAll().catch(err => {
  console.error(err);
  process.exit(1);
});
