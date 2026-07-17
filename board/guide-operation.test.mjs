import assert from "node:assert/strict";
import { GUIDE_OPERATION_AUTHORITY, createGuideToggleOperation, applyGuideToggleOperation } from "./guide-operation.js";

const topology = { componentId: "GuideProof", digest: "sha256:" + "a".repeat(64) };
const wires = [
  { id: "edge:U1.1Y->OUT", from: "U1.1Y", to: "OUT" },
  { id: "edge:U1.2Y->NEXT", from: "U1.2Y", to: "NEXT" },
];
const device = createGuideToggleOperation({ focus: { kind: "device", id: "U1" }, topology });
assert.equal(device.authority, GUIDE_OPERATION_AUTHORITY);
assert.deepEqual(device.target, { kind: "device-instance", id: "U1" });
assert.equal("pointer" in device, false);
let state = applyGuideToggleOperation(device, { wires, visibleEdgeIds: [] });
assert.deepEqual(state.visibleEdgeIds, wires.map(wire => wire.id));
state = applyGuideToggleOperation(createGuideToggleOperation({ focus: { kind: "pin", endpoint: "U1.1Y" }, topology }), { wires, visibleEdgeIds: state.visibleEdgeIds });
assert.deepEqual(state.visibleEdgeIds, ["edge:U1.2Y->NEXT"]);
state = applyGuideToggleOperation(device, { wires, visibleEdgeIds: state.visibleEdgeIds });
assert.deepEqual(state.visibleEdgeIds, ["edge:U1.2Y->NEXT", "edge:U1.1Y->OUT"]);
state = applyGuideToggleOperation(device, { wires, visibleEdgeIds: state.visibleEdgeIds });
assert.deepEqual(state.visibleEdgeIds, []);
assert.throws(() => applyGuideToggleOperation({ ...device, authority: "component_source" }, { wires, visibleEdgeIds: [] }), /Unsupported guide operation/);
console.log("Board guide operation tests passed");
