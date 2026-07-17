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
  'createBoardProfileV2',
  'migrateBoardProfileV1ToV2',
  'validateBoardProfileV2',
  'checkedWorldPoint(world)',
  'LEGACY_BOARD_PROFILE_KEY',
  'zoomViewportAt(ensureViewport(canvas)',
  'panViewport(ensureViewport(canvas)',
  'View moved. Component source and Board picture are unchanged.',
  'Left-drag any device, net, route bend, or label',
  'endpointScreenPoint',
  'function shouldShowWire(wire)',
  'state.guideFocuses.some(focus =>',
  'state.guideFocuses.push(focus)',
  'selectNode(node, node.kind === "net")',
  'function toggleGuideFocus(focus)',
  'Hid routing guides for ${target}',
  'Showing routing guides for ${target}',
  'Connect node ${anchor.endpoint}',
]) assert.ok(app.includes(required), `missing interaction contract: ${required}`);

assert.ok(!app.includes("projectLegacyPoint"), "Board renderer must not retain the v1 coordinate adapter");

console.log("Board interaction contract checks passed");
