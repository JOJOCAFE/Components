import assert from "node:assert/strict";
import { CENTERED_WORLD_COORDINATE_SPACE, createBoardProfileV2, validateBoardProfileV2 } from "./profile-v2.js";

const topology = { componentId: "BoardProof", digest: "sha256:" + "a".repeat(64), title: "Board proof" };
const fresh = createBoardProfileV2(topology);
assert.deepEqual(fresh.coordinate_space, CENTERED_WORLD_COORDINATE_SPACE);
assert.deepEqual(validateBoardProfileV2(fresh, topology), fresh);
const drawn = validateBoardProfileV2({ ...fresh, placements: [{ target: { kind: "device-instance", id: "U1" }, origin: { x: -120, y: 80 }, rotation_deg: 90 }], routes: [{ edge_id: "edge:U1.1Y->OUT", points: [{ x: -120, y: 80 }, { x: 40, y: 80 }] }], labels: [{ id: "clock_note", position: { x: 40, y: -60 }, text: "Clock input\nTry 0 then 1", font_size: 3 }] }, topology);
assert.equal(drawn.placements[0].origin.x, -120);
assert.equal(drawn.routes[0].points[1].y, 80);
assert.equal(validateBoardProfileV2({ ...fresh, placements: [{ target: { kind: "net", id: "OUT" }, origin: { x: 200, y: 0 }, rotation_deg: 0 }] }, topology).placements[0].target.kind, "net");
assert.throws(() => validateBoardProfileV2({ ...fresh, coordinate_space: { ...fresh.coordinate_space, y_axis: "down" } }, topology), /y_axis/);
assert.throws(() => validateBoardProfileV2({ ...fresh, coordinate_space: undefined }, topology), /coordinate_space/);
assert.throws(() => validateBoardProfileV2({ ...fresh, source: "component Bad;" }, topology), /electrical field/);
assert.throws(() => validateBoardProfileV2({ ...fresh, view: { ...fresh.view, viewport: { center: { x: 1, y: 1 } } } }, topology), /session-local/);
assert.throws(() => validateBoardProfileV2({ ...fresh, placements: [{ target: { kind: "device-instance", id: "U1" }, origin: { x: Infinity, y: 0 }, rotation_deg: 0 }] }, topology), /World x/);
assert.throws(() => validateBoardProfileV2({ ...fresh, placements: [{ target: { kind: "device-instance", id: "U1" }, origin: { x: 0, y: 0 }, rotation_deg: 45 }] }, topology), /rotation_deg/);
console.log("Board profile @2 contract tests passed");
