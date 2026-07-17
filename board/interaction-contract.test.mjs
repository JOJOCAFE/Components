import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const app = await readFile(new URL("./app.js", import.meta.url), "utf8");

// A real browser remains necessary for final learner observation. These
// checks keep the declared interaction paths from disappearing in refactors.
for (const required of [
  'function cancelPendingInteraction(',
  'document.addEventListener("keydown"',
  'event.key !== "Escape"',
  'anchor.addEventListener("keydown"',
  'event.key !== "Enter" && event.key !== " "',
  'await proposePinConnection(start, end);',
  'if (command === "cancel route")',
  'Component source and Board picture are unchanged.',
  'vectors.classList.add("board-vectors")',
  'function drawLabels(vectors)',
  'function beginLabel(position, existing = null)',
  'labelRecord({ id, position: draft.position',
  'zoomViewportAt(ensureViewport(canvas)',
  'panViewport(ensureViewport(canvas)',
  'function legacyToWorld(point)',
  'View moved. Component source and Board picture are unchanged.',
]) assert.ok(app.includes(required), `missing interaction contract: ${required}`);

console.log("Board interaction contract checks passed");
