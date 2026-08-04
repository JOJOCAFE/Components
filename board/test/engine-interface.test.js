/**
 * Tests: Engine Interface + Mock Adapter
 *
 * Verifies the EngineInterface contract and mock behavior:
 * - State reads (devices, edges, sourceText, revisions)
 * - Operations (add-device, connect, disconnect, remove-device)
 * - Revision checking (stale rejection)
 * - Batch operations
 * - Inverse operations (undo path)
 * - State change notifications
 */

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

function makeEngine() {
  const mock = createEngineMock();
  const engine = createEngineInterface(mock);
  return engine;
}

// =============================================================================
// RUN ALL TESTS
// =============================================================================

async function runAll() {

  // ===========================================================================
  section('State queries — empty');
  // ===========================================================================
  {
    const engine = makeEngine();
    const state = engine.getState();

    assert(state !== null, 'getState returns non-null');
    assert(typeof state.sourceRevision === 'string', 'sourceRevision is string');
    assert(typeof state.topologyDigest === 'string', 'topologyDigest is string');
    assert(typeof state.sourceText === 'string', 'sourceText is string');
    assert(Object.keys(state.devices).length === 0, 'empty devices');
    assert(Array.isArray(state.edges) && state.edges.length === 0, 'empty edges');
    assert(Array.isArray(state.diagnostics), 'diagnostics is array');
    assert(Array.isArray(state.probes), 'probes is array');
    assert(Array.isArray(state.displays), 'displays is array');
  }

  // ===========================================================================
  section('Operations — add-device');
  // ===========================================================================
  {
    const engine = makeEngine();

    const result = await engine.submit({
      kind: 'component.add-device',
      target: 'source',
      intent: { ref: 'U1', part: 'digital.74HC04' },
    });

    assert(result.ok === true, 'add-device succeeds');
    assert(typeof result.operationId === 'string', 'has operationId');
    assert(result.newState !== undefined, 'has newState');
    assert(result.newState.devices.U1 !== undefined, 'U1 in newState');
    assert(result.newState.devices.U1.part === 'digital.74HC04', 'U1 part correct');
    assert(result.newState.devices.U1.instanceId === 'inst:U1', 'U1 has instanceId');
    assert(typeof result.inverse === 'object', 'has inverse');
    assert(result.inverse.kind === 'component.remove-device', 'inverse is remove-device');

    // Verify state was updated
    const state = engine.getState();
    assert(state.devices.U1 !== undefined, 'getState reflects U1');
    assert(state.sourceText.includes('device U1'), 'sourceText includes device U1');

    // Duplicate should fail
    const dup = await engine.submit({
      kind: 'component.add-device',
      target: 'source',
      intent: { ref: 'U1', part: 'digital.74HC04' },
    });
    assert(dup.ok === false, 'duplicate add-device fails');
    assert(dup.error.includes('already exists'), 'error mentions already exists');
  }

  // ===========================================================================
  section('Operations — connect');
  // ===========================================================================
  {
    const engine = makeEngine();

    await engine.submit({ kind: 'component.add-device', target: 'source', intent: { ref: 'U1', part: 'digital.74HC04' } });
    await engine.submit({ kind: 'component.add-device', target: 'source', intent: { ref: 'U2', part: 'digital.74HC08' } });

    // Preview (validate without mutation)
    const preview = await engine.submit({
      kind: 'component.connect.preview',
      target: 'source',
      intent: { from: 'U1.1Y', to: 'U2.1A' },
    });
    assert(preview.ok === true, 'connect.preview succeeds');
    const stateAfterPreview = engine.getState();
    assert(stateAfterPreview.edges.length === 0, 'preview does not create edge');

    // Apply
    const apply = await engine.submit({
      kind: 'component.connect.apply',
      target: 'source',
      intent: { from: 'U1.1Y', to: 'U2.1A' },
    });
    assert(apply.ok === true, 'connect.apply succeeds');
    assert(apply.newState.edges.length === 1, 'one edge after connect');
    assert(apply.newState.edges[0].from === 'U1.1Y', 'edge from correct');
    assert(apply.newState.edges[0].to === 'U2.1A', 'edge to correct');
    assert(apply.newState.edges[0].id === 'edge:U1.1Y->U2.1A', 'edge has stable id');
    assert(apply.inverse.kind === 'component.disconnect', 'inverse is disconnect');

    // Duplicate connect should fail
    const dup = await engine.submit({
      kind: 'component.connect.apply',
      target: 'source',
      intent: { from: 'U1.1Y', to: 'U2.1A' },
    });
    assert(dup.ok === false, 'duplicate connect fails');

    // Connect to non-existent device should fail
    const bad = await engine.submit({
      kind: 'component.connect.apply',
      target: 'source',
      intent: { from: 'U1.1Y', to: 'U99.1A' },
    });
    assert(bad.ok === false, 'connect to missing device fails');
  }

  // ===========================================================================
  section('Operations — disconnect');
  // ===========================================================================
  {
    const engine = makeEngine();

    await engine.submit({ kind: 'component.add-device', target: 'source', intent: { ref: 'U1', part: 'digital.74HC04' } });
    await engine.submit({ kind: 'component.add-device', target: 'source', intent: { ref: 'U2', part: 'digital.74HC08' } });
    await engine.submit({ kind: 'component.connect.apply', target: 'source', intent: { from: 'U1.1Y', to: 'U2.1A' } });

    const result = await engine.submit({
      kind: 'component.disconnect',
      target: 'source',
      intent: { from: 'U1.1Y', to: 'U2.1A' },
    });
    assert(result.ok === true, 'disconnect succeeds');
    assert(result.newState.edges.length === 0, 'no edges after disconnect');
    assert(result.inverse.kind === 'component.connect.apply', 'inverse is connect');

    // Disconnect non-existent should fail
    const bad = await engine.submit({
      kind: 'component.disconnect',
      target: 'source',
      intent: { from: 'U1.1Y', to: 'U2.1A' },
    });
    assert(bad.ok === false, 'disconnect non-existent fails');
  }

  // ===========================================================================
  section('Operations — remove-device');
  // ===========================================================================
  {
    const engine = makeEngine();

    await engine.submit({ kind: 'component.add-device', target: 'source', intent: { ref: 'U1', part: 'digital.74HC04' } });
    await engine.submit({ kind: 'component.add-device', target: 'source', intent: { ref: 'U2', part: 'digital.74HC08' } });
    await engine.submit({ kind: 'component.connect.apply', target: 'source', intent: { from: 'U1.1Y', to: 'U2.1A' } });

    const result = await engine.submit({
      kind: 'component.remove-device',
      target: 'source',
      intent: { ref: 'U1' },
    });
    assert(result.ok === true, 'remove-device succeeds');
    assert(result.newState.devices.U1 === undefined, 'U1 gone from state');
    assert(result.newState.edges.length === 0, 'connections involving U1 removed');
    assert(result.inverse.kind === 'component.add-device', 'inverse is add-device');
    assert(result.inverse.intent.ref === 'U1', 'inverse intent has ref');
    assert(result.inverse.intent.part === 'digital.74HC04', 'inverse intent has part');

    // Remove non-existent should fail
    const bad = await engine.submit({
      kind: 'component.remove-device',
      target: 'source',
      intent: { ref: 'U99' },
    });
    assert(bad.ok === false, 'remove non-existent fails');
  }

  // ===========================================================================
  section('Revision checking — stale detection');
  // ===========================================================================
  {
    const engine = makeEngine();

    const rev0 = engine.getSourceRevision();
    const digest0 = engine.getTopologyDigest();

    await engine.submit({ kind: 'component.add-device', target: 'source', intent: { ref: 'U1', part: 'digital.74HC04' } });

    const rev1 = engine.getSourceRevision();
    assert(rev1 !== rev0, 'revision changed after add-device');

    // Submit with OLD revision — should be rejected
    const stale = await engine.submit({
      kind: 'component.add-device',
      target: 'source',
      source_revision: rev0,
      topology_digest: digest0,
      intent: { ref: 'U2', part: 'digital.74HC08' },
    });
    assert(stale.ok === false, 'stale revision rejected');
    assert(stale.error.includes('Stale'), 'error says stale');

    // Submit with CURRENT revision — should succeed
    const fresh = await engine.submit({
      kind: 'component.add-device',
      target: 'source',
      source_revision: rev1,
      topology_digest: engine.getTopologyDigest(),
      intent: { ref: 'U2', part: 'digital.74HC08' },
    });
    assert(fresh.ok === true, 'fresh revision accepted');
  }

  // ===========================================================================
  section('Batch operations');
  // ===========================================================================
  {
    const engine = makeEngine();

    const batch = await engine.submitBatch([
      { kind: 'component.add-device', target: 'source', intent: { ref: 'U1', part: 'digital.74HC04' } },
      { kind: 'component.add-device', target: 'source', intent: { ref: 'U2', part: 'digital.74HC08' } },
      { kind: 'component.connect.apply', target: 'source', intent: { from: 'U1.1Y', to: 'U2.1A' } },
    ]);

    assert(batch.ok === true, 'batch all succeed');
    assert(batch.results.length === 3, 'batch has 3 results');
    assert(batch.results.every(r => r.ok), 'all results ok');

    const state = engine.getState();
    assert(Object.keys(state.devices).length === 2, 'batch created 2 devices');
    assert(state.edges.length === 1, 'batch created 1 edge');
  }

  // ===========================================================================
  section('Batch — failure blocks subsequent ops');
  // ===========================================================================
  {
    const engine = makeEngine();

    const batch = await engine.submitBatch([
      { kind: 'component.add-device', target: 'source', intent: { ref: 'U1', part: 'digital.74HC04' } },
      { kind: 'component.connect.apply', target: 'source', intent: { from: 'U1.1Y', to: 'U99.1A' } },
      { kind: 'component.add-device', target: 'source', intent: { ref: 'U2', part: 'digital.74HC08' } },
    ]);

    assert(batch.ok === false, 'batch fails');
    assert(batch.results[0].ok === true, 'first op succeeded');
    assert(batch.results[1].ok === false, 'second op failed (U99 missing)');
    assert(batch.results[2].ok === false, 'third op blocked');
    assert(batch.results[2].error.includes('Blocked'), 'blocked error message');
  }

  // ===========================================================================
  section('State change notifications');
  // ===========================================================================
  {
    const engine = makeEngine();
    let notifyCount = 0;
    let lastState = null;

    const unsub = engine.onStateChange((state) => {
      notifyCount++;
      lastState = state;
    });

    await engine.submit({ kind: 'component.add-device', target: 'source', intent: { ref: 'U1', part: 'digital.74HC04' } });
    assert(notifyCount === 1, 'notified once after submit');
    assert(lastState.devices.U1 !== undefined, 'notification has updated state');

    // Failed operations should NOT notify
    await engine.submit({ kind: 'component.add-device', target: 'source', intent: { ref: 'U1', part: 'digital.74HC04' } });
    assert(notifyCount === 1, 'no notification on failed submit');

    // Unsubscribe
    unsub();
    await engine.submit({ kind: 'component.add-device', target: 'source', intent: { ref: 'U2', part: 'digital.74HC08' } });
    assert(notifyCount === 1, 'no notification after unsubscribe');
  }

  // ===========================================================================
  section('Source text and topology digest');
  // ===========================================================================
  {
    const engine = makeEngine();

    await engine.submit({ kind: 'component.add-device', target: 'source', intent: { ref: 'U1', part: 'digital.74HC04' } });
    await engine.submit({ kind: 'component.add-device', target: 'source', intent: { ref: 'U2', part: 'digital.74HC08' } });
    await engine.submit({ kind: 'component.connect.apply', target: 'source', intent: { from: 'U1.1Y', to: 'U2.1A' } });

    const text = engine.getSourceText();
    assert(text.includes('device U1, digital.74HC04'), 'sourceText has U1');
    assert(text.includes('device U2, digital.74HC08'), 'sourceText has U2');
    assert(text.includes('connect U1.1Y -> U2.1A'), 'sourceText has connection');

    // Digest should be stable for same topology
    const d1 = engine.getTopologyDigest();
    const d2 = engine.getTopologyDigest();
    assert(d1 === d2, 'digest is stable');
  }

  // ===========================================================================
  section('Pin inference from connections');
  // ===========================================================================
  {
    const engine = makeEngine();

    await engine.submit({ kind: 'component.add-device', target: 'source', intent: { ref: 'U1', part: 'digital.74HC04' } });
    await engine.submit({ kind: 'component.add-device', target: 'source', intent: { ref: 'U2', part: 'digital.74HC08' } });
    await engine.submit({ kind: 'component.connect.apply', target: 'source', intent: { from: 'U1.1Y', to: 'U2.1A' } });

    const devices = engine.getDevices();
    assert(devices.U1.pins['1Y'] !== undefined, 'U1 has pin 1Y');
    assert(devices.U1.pins['1Y'].direction === 'output', 'U1.1Y is output (from)');
    assert(devices.U2.pins['1A'] !== undefined, 'U2 has pin 1A');
    assert(devices.U2.pins['1A'].direction === 'input', 'U2.1A is input (to)');
  }

  // ===========================================================================
  section('Unknown operation kind');
  // ===========================================================================
  {
    const engine = makeEngine();

    const result = await engine.submit({
      kind: 'unknown.garbage',
      target: 'source',
      intent: {},
    });
    assert(result.ok === false, 'unknown kind rejected');
    assert(result.error.includes('Unknown'), 'error mentions unknown');
  }

  // ===========================================================================
  // SUMMARY
  // ===========================================================================

  console.log(`\n  engine-interface: ${passed} passed, ${failed} failed\n`);
  if (failed > 0) process.exit(1);
}

runAll().catch(err => {
  console.error(err);
  process.exit(1);
});
