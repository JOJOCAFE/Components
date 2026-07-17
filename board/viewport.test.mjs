import assert from "node:assert/strict";
import { adaptiveGrid, panViewport, screenToWorld, snapWorldPoint, viewport, worldBounds, worldToScreen, zoomViewportAt } from "./viewport.js";

const rect = { width: 1000, height: 600 };
const initial = viewport({ center: { x: 0, y: 0 }, pixelsPerWorld: 2 });

assert.deepEqual(screenToWorld(initial, { x: 500, y: 300 }, rect), { x: 0, y: 0 });
assert.deepEqual(screenToWorld(initial, { x: 700, y: 200 }, rect), { x: 100, y: 50 });
assert.deepEqual(worldToScreen(initial, { x: 100, y: 50 }, rect), { x: 700, y: 200 });

const panned = panViewport(initial, { x: 80, y: -40 });
assert.deepEqual(panned.center, { x: -40, y: -20 });

const anchor = { x: 700, y: 200 }, before = screenToWorld(initial, anchor, rect);
const zoomed = zoomViewportAt(initial, 3, anchor, rect);
assert.deepEqual(screenToWorld(zoomed, anchor, rect), before);
assert.deepEqual(worldBounds(initial, rect), { minX: -250, maxX: 250, minY: -150, maxY: 150 });

const grid = adaptiveGrid(initial);
assert.equal(grid.majorWorldUnits, 50);
assert.equal(grid.majorPixels, 100);
assert.deepEqual(snapWorldPoint({ x: 74, y: -76 }, grid), { x: 50, y: -100 });
assert.equal(adaptiveGrid(viewport({ pixelsPerWorld: .5 })).majorWorldUnits, 100);

assert.throws(() => viewport({ pixelsPerWorld: 0 }), /outside viewport limits/);
assert.throws(() => screenToWorld(initial, { x: NaN, y: 0 }, rect), /finite/);
assert.throws(() => snapWorldPoint({ x: 0, y: 0 }, 0), /positive/);
console.log("Board viewport transform tests passed");
