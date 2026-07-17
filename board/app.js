import { checkedWorldPoint, createBoardProfileV2, migrateBoardProfileV1ToV2, validateBoardProfileV2 } from "./profile-v2.js";
import { adaptiveGrid, panViewport, screenToWorld, viewport, worldToScreen, zoomViewportAt } from "./viewport.js";

const $ = (selector) => document.querySelector(selector);
const state = { source: "", revision: "", resolved: null, board: null, selected: null, drives: [], timer: null, resolveGeneration: 0, pinGesture: null, guide: null, boardProfile: null, staleBoardProfile: false, topologyDigest: "", drag: null, viewportDrag: null, viewport: null, nodePositions: {}, suppressClick: false, pen: null, labelDraft: null };
// v2 intentionally starts from a valid Component example instead of retaining
// older workbench drafts that may contain Terminal commands such as `run`.
const STORAGE_KEY = "components.board.not-gate.source.v2";
const BOARD_PROFILE_KEY = "components.board.not-gate.profile.v2";
const LEGACY_BOARD_PROFILE_KEY = "components.board.not-gate.profile.v1";
const started = performance.now();

async function request(command, input = {}, options = {}) {
  const response = await fetch("/", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ command, input, options }) });
  const data = await response.json();
  if (!data.ok) throw new Error(data.error?.message || "The local Components service did not accept that request.");
  return data.result;
}

function log(message) { const line = document.createElement("div"); line.textContent = message; $("#terminal-log").prepend(line); }
function status(message, error = false) { const target = $("#diagnostics"); target.textContent = message; target.classList.toggle("error", error); }
function saveDraft() { localStorage.setItem(STORAGE_KEY, state.source); $("#save-state").textContent = "Saved on this device"; }

async function loadExample() {
  const draft = localStorage.getItem(STORAGE_KEY);
  if (draft) { state.source = draft; log("Recovered your local draft."); }
  else state.source = (await request("component-language-example")).source;
  $("#source").value = state.source;
  await resolve();
  $("#save-state").textContent = `Ready in ${Math.round(performance.now() - started)} ms`;
}

async function resolve() {
  const generation = ++state.resolveGeneration;
  const source = state.source;
  try {
    const result = await request("component-language-resolve", { source, source_name: "Board draft" });
    if (generation !== state.resolveGeneration) return;
    state.resolved = result;
    state.revision = await sha256(source);
    if (generation !== state.resolveGeneration) return;
    if (!result.ok) { status(`${firstDiagnostic(result)} Showing the last valid version.`, true); return; }
    state.topologyDigest = await digestResolvedTopology(result);
    if (generation !== state.resolveGeneration) return;
    loadBoardProfile(result);
    state.board = await request("component-language-board-view", { source, source_name: "Board draft" });
    if (generation !== state.resolveGeneration) return;
    $("#component-name").textContent = friendlyTitle(result.component_id);
    status("Looks good. Click a part or wire to read it, then try one action.");
    renderBoard();
  } catch (error) { if (generation === state.resolveGeneration) status(error.message, true); }
}

function firstDiagnostic(result) {
  const item = result.diagnostics?.[0];
  if (!item) return "The text needs fixing before the Drawing can update.";
  if (/unsupported Component statement:\s*['"]run['"]/i.test(item.message || "")) return "`run` is a Board action, not Component code. Use Try inversion instead.";
  return `${item.message} (line ${item.span?.line || "?"})`;
}
function friendlyTitle(name) { return name === "DigitalInverterFixture" ? "A NOT gate" : name || "Components Board"; }
async function sha256(text) { const bytes = new TextEncoder().encode(text); const hash = await crypto.subtle.digest("SHA-256", bytes); return "sha256:" + [...new Uint8Array(hash)].map(x => x.toString(16).padStart(2, "0")).join(""); }
function canonicalJson(value) {
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  if (value && typeof value === "object") return `{${Object.keys(value).sort().map(key => `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(",")}}`;
  return JSON.stringify(value);
}
async function digestResolvedTopology(resolved) { return sha256(canonicalJson(resolved)); }

function boardTopology(resolved) { return { componentId: resolved.component_id, digest: state.topologyDigest, title: friendlyTitle(resolved.component_id) }; }
function freshBoardProfile(resolved) { return createBoardProfileV2(boardTopology(resolved)); }
function loadBoardProfile(resolved) {
  let saved = null;
  try { saved = JSON.parse(localStorage.getItem(BOARD_PROFILE_KEY) || localStorage.getItem(LEGACY_BOARD_PROFILE_KEY) || "null"); } catch (_) { /* start clean */ }
  if (!saved) { state.boardProfile = freshBoardProfile(resolved); state.staleBoardProfile = false; return; }
  try {
    const migrated = saved.schema === "components.board-profile@1" ? migrateBoardProfileV1ToV2(saved, boardTopology(resolved)) : null;
    state.boardProfile = migrated?.profile || validateBoardProfileV2(saved, boardTopology(resolved));
    state.staleBoardProfile = false;
    if (migrated) { localStorage.setItem(BOARD_PROFILE_KEY, JSON.stringify(state.boardProfile)); localStorage.removeItem(LEGACY_BOARD_PROFILE_KEY); log("Migrated your saved Board picture to world coordinates."); }
  } catch (error) {
    state.boardProfile = freshBoardProfile(resolved);
    state.staleBoardProfile = /stale or wrong/i.test(error.message);
    log(state.staleBoardProfile ? "Saved Board picture is stale and was not reused. Type 'discard board profile' to start a new picture." : "Saved Board picture has an unsupported format and was not reused.");
  }
}
function saveBoardProfile(command) {
  if (!state.boardProfile) return;
  if (state.staleBoardProfile) { status("This Board picture is stale. Type 'discard board profile' before saving a new one.", true); return; }
  localStorage.setItem(BOARD_PROFILE_KEY, JSON.stringify(state.boardProfile));
  log(command);
  $("#save-state").textContent = "Board picture saved on this device";
}
function placementFor(id, kind = "device-instance") { return state.boardProfile?.placements.find(item => item.target?.kind === kind && item.target.id === id); }
function routeFor(edgeId) { return state.boardProfile?.routes.find(item => item.edge_id === edgeId); }
function edgeId(wire) { return wire.id || `edge:${wire.from}->${wire.to}`; }
function pointText(point) { return `(${Number(point.x).toFixed(1)}, ${Number(point.y).toFixed(1)})`; }
function parseWorldRoutePoints(text) {
  const matches = [...text.matchAll(/\(\s*([^,()]+)\s*,\s*([^,()]+)\s*\)/g)];
  const remainder = text.replace(/\(\s*([^,()]+)\s*,\s*([^,()]+)\s*\)/g, "").trim();
  if (!matches.length || remainder) throw new Error("Use only world coordinates such as (-120,80) after via.");
  return matches.map(match => checkedWorldPoint({ x: Number(match[1]), y: Number(match[2]) }));
}
function canvasRect(canvas) { return { width: Math.max(1, canvas.clientWidth), height: Math.max(1, canvas.clientHeight) }; }
function ensureViewport(canvas) {
  if (!state.viewport) {
    const rect = canvasRect(canvas);
    state.viewport = viewport({ center: { x: 0, y: 0 }, pixelsPerWorld: Math.max(.1, Math.min(rect.width, rect.height) / 600) });
  }
  return state.viewport;
}
function projectWorldPoint(canvas, point) { return worldToScreen(ensureViewport(canvas), point, canvasRect(canvas)); }
function updateGrid(canvas) {
  const view = ensureViewport(canvas); const grid = adaptiveGrid(view); const screen = canvasRect(canvas);
  const origin = worldToScreen(view, { x: 0, y: 0 }, screen);
  canvas.style.setProperty("--grid-major-px", `${grid.majorPixels}px`);
  canvas.style.setProperty("--grid-minor-px", `${grid.majorPixels / 5}px`);
  canvas.style.setProperty("--grid-origin-x", `${origin.x}px`);
  canvas.style.setProperty("--grid-origin-y", `${origin.y}px`);
}

function renderBoard() {
  const canvas = $("#board-canvas"); canvas.replaceChildren();
  const screen = canvasRect(canvas); ensureViewport(canvas); updateGrid(canvas);
  const blocks = state.board?.blocks || [];
  const devices = blocks.filter(item => item.type === "device");
  const nets = state.board?.nets || [];
  const nodes = [];
  devices.forEach((item, index) => {
    const fallback = { x: devices.length === 1 ? 0 : -138 + index * (276 / (devices.length - 1)), y: 84 };
    const placement = placementFor(item.id);
    nodes.push({ id: item.id, label: item.id === "U1" ? "U1\nNOT gate" : item.id, x: placement?.origin?.x ?? fallback.x, y: placement?.origin?.y ?? fallback.y, kind: "device", part: item.part, pinAnchors: item.pin_anchors || [], resource: item.resource });
  });
  nets.filter(item => item.kind !== "power").forEach((item, index) => {
    const fallback = { x: -192 + index * (384 / Math.max(1, nets.filter(n => n.kind !== "power").length - 1)), y: -132 };
    const placement = placementFor(item.id, "net");
    nodes.push({ id: item.id, label: item.id, x: placement?.origin?.x ?? fallback.x, y: placement?.origin?.y ?? fallback.y, kind: "net" });
  });
  nodes.forEach(node => { node.screen = projectWorldPoint(canvas, node); });
  const lookup = Object.fromEntries(nodes.map(item => [item.id, item]));
  state.nodePositions = Object.fromEntries(nodes.map(item => [item.id, { x: item.x, y: item.y }]));
  const vectors = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  vectors.classList.add("board-vectors"); vectors.setAttribute("viewBox", `0 0 ${screen.width} ${screen.height}`); vectors.setAttribute("preserveAspectRatio", "none");
  canvas.append(vectors);
  (state.board?.wires || []).forEach(wire => {
    const left = lookup[wire.from.split(".")[0]] || lookup[wire.from]; const right = lookup[wire.to.split(".")[0]] || lookup[wire.to];
    if (left && right) drawEdge(vectors, left, right, wire);
  });
  drawLabels(vectors);
  nodes.forEach(node => drawNode(canvas, node));
  if (state.guide) requestAnimationFrame(() => drawPinGuide(canvas));
  if (state.pen) requestAnimationFrame(() => drawPenPreview(canvas));
}

function drawEdge(vectors, from, to, wire) {
  const savedRoute = routeFor(edgeId(wire));
  const worldPoints = savedRoute?.points?.length > 2 ? [{ x: from.x, y: from.y }, ...savedRoute.points.slice(1, -1), { x: to.x, y: to.y }] : [{ x: from.x, y: from.y }, { x: to.x, y: to.y }];
  const canvas = $("#board-canvas"); const points = worldPoints.map(point => projectWorldPoint(canvas, point));
  const edge = document.createElementNS("http://www.w3.org/2000/svg", "path");
  edge.classList.add("board-edge", savedRoute?.points?.length > 2 ? "routed" : "connection-guide");
  edge.setAttribute("d", `M ${points.map(point => `${point.x} ${point.y}`).join(" L ")}`);
  edge.setAttribute("aria-label", `${wire.from} to ${wire.to}. ${savedRoute ? "Visual route." : "Connection guide: draw a route."}`);
  edge.addEventListener("pointerdown", event => { if (isSelectTool()) beginRouteDrag(event, wire); });
  edge.addEventListener("click", event => { event.stopPropagation(); if (state.suppressClick) return; selectWire(wire); });
  vectors.append(edge);
  points.slice(1, -1).forEach((via, index) => {
    const handle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    handle.classList.add("route-handle"); handle.setAttribute("cx", via.x); handle.setAttribute("cy", via.y); handle.setAttribute("r", "5");
    handle.setAttribute("aria-label", "Drag to move this visual route bend.");
    handle.addEventListener("pointerdown", event => { if (isSelectTool()) beginRouteDrag(event, wire, index + 1); }); vectors.append(handle);
  });
}

function drawLabels(vectors) {
  const canvas = $("#board-canvas"); const scale = ensureViewport(canvas).pixelsPerWorld;
  for (const label of state.boardProfile?.labels || []) {
    const position = projectWorldPoint(canvas, label.position);
    const fontSize = Math.max(12, label.font_size * scale * 1.5);
    const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
    text.classList.add("board-label"); text.setAttribute("x", position.x); text.setAttribute("y", position.y); text.setAttribute("font-size", fontSize);
    text.setAttribute("tabindex", "0"); text.setAttribute("role", "button"); text.setAttribute("aria-label", `Edit label: ${label.text}`);
    label.text.split("\n").forEach((line, index) => {
      const span = document.createElementNS("http://www.w3.org/2000/svg", "tspan");
      span.setAttribute("x", position.x); span.setAttribute("dy", index === 0 ? "0" : String(fontSize * 1.25)); span.textContent = line; text.append(span);
    });
    text.addEventListener("pointerdown", event => {
      if (!isSelectTool()) return;
      event.preventDefault(); event.stopPropagation();
      state.drag = { kind: "label", id: label.id, moved: false, start: boardPoint(event) };
    });
    const edit = event => { event.stopPropagation(); if (!isSelectTool()) beginLabel(label.position, label); };
    text.addEventListener("click", edit); text.addEventListener("keydown", event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); edit(event); } });
    vectors.append(text);
  }
}

function drawNode(canvas, node) {
  if (node.kind === "device" && node.resource?.asset) {
    const device = document.createElement("section");
    device.className = "board-device" + (state.selected?.id === node.id ? " selected" : "");
    device.style.left = `${node.screen.x}px`; device.style.top = `${node.screen.y}px`;
    device.innerHTML = `<div class="board-device-title"><button class="board-device-label" type="button">${node.label}</button><button class="gate-move" type="button" aria-label="Move ${node.id}" title="Drag to move this gate">✋</button></div>${chipFrame(node, true)}`;
    const label = device.querySelector(".board-device-label");
    label.addEventListener("click", event => { event.stopPropagation(); if (state.suppressClick) return; selectNode(node); });
    device.addEventListener("pointerdown", event => {
      if (!isSelectTool() || event.target.closest(".pin-anchor, .gate-move")) return;
      beginObjectDrag(event, node);
    });
    const move = device.querySelector(".gate-move");
    move.addEventListener("pointerdown", event => beginChipDrag(event, node));
    canvas.append(device);
    return;
  }
  const button = document.createElement("button"); button.className = `node ${node.kind}` + (state.selected?.id === node.id ? " selected" : "");
  button.style.left = `${node.screen.x}px`; button.style.top = `${node.screen.y}px`; button.textContent = node.label;
  button.addEventListener("pointerdown", event => { if (isSelectTool()) beginObjectDrag(event, node); });
  button.addEventListener("click", () => { if (!state.suppressClick) selectNode(node); }); canvas.append(button);
}

function boardPoint(event) {
  const canvas = $("#board-canvas"); const box = canvas.getBoundingClientRect();
  const world = screenToWorld(ensureViewport(canvas), { x: event.clientX - box.left, y: event.clientY - box.top }, canvasRect(canvas));
  return checkedWorldPoint(world);
}
function setPlacement(id, point, kind = "device-instance") {
  const placements = state.boardProfile.placements;
  const existing = placementFor(id, kind);
  const record = { target: { kind, id }, origin: checkedWorldPoint(point), rotation_deg: 0 };
  if (existing) Object.assign(existing, record); else placements.push(record);
}
function setRoutePoints(wire, vias) {
  const id = edgeId(wire); const routes = state.boardProfile.routes;
  const existing = routeFor(id);
  const start = state.nodePositions[wire.from.split(".")[0]] || state.nodePositions[wire.from] || { x: 0, y: 0 };
  const end = state.nodePositions[wire.to.split(".")[0]] || state.nodePositions[wire.to] || { x: 0, y: 0 };
  if (wire.kind !== "scalar") throw new Error("Board routes are available only for resolved scalar edges; bus routes need their own contract.");
  const record = { edge_id: id, points: [start, ...vias, end].map(checkedWorldPoint) };
  if (existing) Object.assign(existing, record); else routes.push(record);
}
function setRoute(wire, via, viaIndex = 1) {
  const current = routeFor(edgeId(wire));
  const vias = current?.points?.slice(1, -1) || [];
  vias[Math.max(0, viaIndex - 1)] = via;
  setRoutePoints(wire, vias);
}
function beginLabel(position, existing = null) {
  state.labelDraft = { position, existing };
  $("#label-text").value = existing?.text || "";
  $("#label-size").value = existing?.font_size || 3;
  $("#label-form").classList.remove("hidden");
  $("#label-text").focus();
  status(existing ? "Edit the label text or size, then apply it." : "Type a label. Use Enter for another line.");
}
function saveLabelDraft() {
  const draft = state.labelDraft;
  if (!draft || !state.boardProfile) return;
  try {
    const id = draft.existing?.id || `label-${(state.boardProfile.labels?.length || 0) + 1}`;
    const text = $("#label-text").value; const fontSize = Number($("#label-size").value);
    if (!/^[A-Za-z_][A-Za-z0-9_-]*$/.test(id) || !text.trim() || !Number.isFinite(fontSize) || fontSize < 1.5 || fontSize > 8) throw new Error("Label needs an identifier, text, and a size from 1.5 to 8.");
    const label = { id, position: checkedWorldPoint(draft.position), text, font_size: fontSize };
    state.boardProfile.labels ||= [];
    const existingIndex = state.boardProfile.labels.findIndex(item => item.id === id);
    if (existingIndex >= 0) state.boardProfile.labels[existingIndex] = label; else state.boardProfile.labels.push(label);
    state.labelDraft = null; $("#label-form").classList.add("hidden");
    saveBoardProfile(`component:board label ${id} at ${pointText(label.position)} size ${label.font_size};`);
    renderBoard(); status("Saved a visual label. Component wiring is unchanged.");
  } catch (error) { status(error.message, true); }
}
function cancelLabelDraft() {
  state.labelDraft = null; $("#label-form").classList.add("hidden");
}
function beginChipDrag(event, node) {
  event.preventDefault(); event.stopPropagation();
  state.drag = { kind: "node", nodeKind: "device-instance", id: node.id, moved: false, start: boardPoint(event) };
}
function isSelectTool() { return document.querySelector('.tool.selected')?.dataset.tool === "select"; }
function beginObjectDrag(event, node) {
  if (event.button !== 0) return;
  event.preventDefault(); event.stopPropagation();
  state.selected = node;
  state.drag = { kind: "node", nodeKind: node.kind === "device" ? "device-instance" : "net", id: node.id, moved: false, start: boardPoint(event) };
}
function beginRouteDrag(event, wire, viaIndex = 1) {
  event.preventDefault(); event.stopPropagation();
  state.drag = { kind: "route", wire, viaIndex, moved: false, start: boardPoint(event) };
}
function moveBoardDrag(event) {
  if (!state.drag || !state.boardProfile) return;
  const point = boardPoint(event);
  if (Math.abs(point.x - state.drag.start.x) > .25 || Math.abs(point.y - state.drag.start.y) > .25) state.drag.moved = true;
  if (state.drag.kind === "node") setPlacement(state.drag.id, point, state.drag.nodeKind);
  else if (state.drag.kind === "label") {
    const label = state.boardProfile.labels?.find(item => item.id === state.drag.id);
    if (label) label.position = point;
  } else setRoute(state.drag.wire, point, state.drag.viaIndex);
  renderBoard();
}
function finishBoardDrag() {
  const drag = state.drag; if (!drag) return;
  state.drag = null;
  if (!drag.moved) return;
  state.suppressClick = true;
  setTimeout(() => { state.suppressClick = false; }, 0);
  if (drag.kind === "node") {
    const placement = placementFor(drag.id, drag.nodeKind);
    saveBoardProfile(`component:board place ${drag.id} at ${pointText(placement.origin)};`);
    status(`Moved ${drag.id}. This changed only its Board picture, not Component wiring.`);
  } else if (drag.kind === "label") {
    const label = state.boardProfile.labels?.find(item => item.id === drag.id);
    saveBoardProfile(`component:board label ${drag.id} at ${pointText(label.position)} size ${label.font_size};`);
    status(`Moved label ${drag.id}. Component wiring is unchanged.`);
  } else {
    const route = routeFor(edgeId(drag.wire)); const vias = route.points.slice(1, -1).map(pointText).join(" -> ");
    saveBoardProfile(`component:board route ${route.edge_id} via ${vias};`);
    status(`Moved the visual route for ${drag.wire.from} → ${drag.wire.to}. Component wiring is unchanged.`);
  }
}

function wireForEndpoints(from, to) {
  return (state.board?.wires || []).find(wire => wire.from === from && wire.to === to) || null;
}
function endpointBoardPoint(endpoint) {
  const anchor = guideAnchor(endpoint);
  if (!anchor) return state.nodePositions[endpoint] || null;
  const instance = endpoint.split(".")[0]; const center = state.nodePositions[instance];
  if (!center) return null;
  const pinCount = (state.board?.blocks || []).find(item => item.id === instance)?.pin_anchors?.length || 2;
  const sideCount = Math.max(1, pinCount / 2);
  return {
    x: center.x + (anchor.dip_side === "left" ? -10 : 10),
    y: center.y + ((anchor.dip_order - (sideCount + 1) / 2) * (22 / sideCount)),
  };
}
function routeVisualConnection(from, to, vias) {
  const wire = wireForEndpoints(from, to);
  if (!wire) {
    status(`No resolved connection ${from} → ${to}. Use connect first; a Board route cannot create a circuit wire.`, true);
    return false;
  }
  try { setRoutePoints(wire, vias); } catch (error) { status(error.message, true); return false; }
  saveBoardProfile(`component:board route ${edgeId(wire)} via ${vias.map(pointText).join(" -> ")};`);
  renderBoard();
  status(`Saved a visual route for existing connection ${from} → ${to}. Component source is unchanged.`);
  return true;
}
function beginPenRoute(from, to) {
  const wire = wireForEndpoints(from, to); const start = endpointBoardPoint(from);
  if (!wire || !start) {
    status(`No resolved connection ${from} → ${to}. Use connect first, then route the existing line.`, true);
    return false;
  }
  state.pen = { wire, from, to, position: start, heading: 0, down: false, vias: [] };
  status(`Pen is at ${from}. Use pd, fd <distance>, rt/lt <degrees>, bk <distance>, then pen to ${to}.`);
  return true;
}
function movePen(distance) {
  if (!state.pen) { status("Start with route from <chip.pin> to <chip.pin>.", true); return; }
  if (!Number.isFinite(distance) || !Number.isFinite(state.pen.heading)) { status("Pen heading and distance must be finite numbers.", true); return; }
  const radians = state.pen.heading * Math.PI / 180;
  state.pen.position = checkedWorldPoint({ x: state.pen.position.x + Math.cos(radians) * distance, y: state.pen.position.y + Math.sin(radians) * distance });
  if (state.pen.down) state.pen.vias.push({ ...state.pen.position });
  renderBoard();
  status(`Pen at ${pointText(state.pen.position)}${state.pen.down ? "; route point added." : "."}`);
}
function finishPenAt(target) {
  if (!state.pen) { status("Start with route from <chip.pin> to <chip.pin>.", true); return; }
  if (target !== state.pen.to) { status(`This pen route must finish at ${state.pen.to}; it cannot retarget an electrical edge.`, true); return; }
  const pen = state.pen; state.pen = null;
  routeVisualConnection(pen.from, pen.to, pen.vias);
}
function selectNode(node) {
  state.selected = node; renderBoard();
  const technical = node.kind === "device" ? `${node.part} Device` : "Wire (net)";
  const sentence = node.id === "U1" ? "This NOT gate changes 0 into 1, and 1 into 0." : node.kind === "net" ? "This wire carries a named signal between declared parts." : "This is a declared part in this small machine.";
  const artwork = node.kind === "device" && node.resource?.asset
    ? chipFrame(node)
    : "";
  $("#lens").innerHTML = `<strong>${node.kind === "device" ? "Part" : "Wire"}: ${node.id}</strong><p>${sentence}</p><small>Real name: ${technical}</small>${artwork}`;
  highlightSource(node.id);
  installPinGesture();
}

function chipFrame(node, compact = false) {
  const anchors = node.pinAnchors.map(anchor => {
    const sidePinCount = Math.max(1, node.pinAnchors.length / 2);
    const top = 6 + (Number(anchor.dip_order) - .5) * (88 / sidePinCount);
    return `<button class="pin-anchor ${anchor.dip_side}" type="button" data-anchor-id="${anchor.id}" data-endpoint="${anchor.endpoint}" data-direction="${anchor.direction}" data-pin-number="${anchor.physical_pin}" data-pin-name="${anchor.port}" data-component-selector="@${anchor.physical_pin}" style="top:${top}%" aria-label="${anchor.endpoint}, physical pin ${anchor.physical_pin}, ${anchor.direction} pin"></button>`;
  }).join("");
  const caption = compact ? "" : "<figcaption>Drag from one visible pin to another to propose a checked source edit. This frame owns no wiring state.</figcaption>";
  return `<figure class="pinout-art chip-frame${compact ? " compact" : ""}" data-frame-device="${node.id}"><img src="${node.resource.asset}" alt="${node.part} DIP pin frame" draggable="false"><div class="pin-anchor-layer" aria-label="Definition-owned ${node.part} pins">${anchors}</div>${caption}</figure>`;
}

function installPinGesture() {
  document.querySelectorAll(".pin-anchor").forEach(anchor => {
    anchor.addEventListener("pointerdown", event => {
      event.preventDefault();
      beginPinGesture(anchor, "Release on a second pin to propose it.");
    });
    anchor.addEventListener("pointerup", event => {
      event.preventDefault();
      finishPinGesture(anchor);
    });
    anchor.addEventListener("keydown", event => {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      if (!state.pinGesture) beginPinGesture(anchor, "Press Enter or Space on a second pin to propose it.");
      else finishPinGesture(anchor);
    });
  });
}

function anchorIntent(anchor) { return { id: anchor.dataset.anchorId, endpoint: anchor.dataset.endpoint, direction: anchor.dataset.direction }; }
function beginPinGesture(anchor, instruction) {
  state.pinGesture = anchorIntent(anchor);
  status(`Connection start: ${state.pinGesture.endpoint}. ${instruction}`);
}
function finishPinGesture(anchor) {
  const start = state.pinGesture;
  state.pinGesture = null;
  if (!start) return;
  const end = anchorIntent(anchor);
  if (start.id === end.id) { status("Connection cancelled. Choose two different pins when you are ready."); return; }
  clearPinGuide();
  proposePinConnection(start, end);
}

function cancelPendingInteraction(message = "Cancelled. Component source and Board picture are unchanged.") {
  const hadPending = Boolean(state.pinGesture || state.guide || state.pen || !$("#connect-form").classList.contains("hidden"));
  state.pinGesture = null;
  state.pen = null;
  clearPinGuide();
  $("#connect-form").classList.add("hidden");
  if (hadPending) { renderBoard(); status(message); log(message); }
}

function guideAnchor(endpoint) {
  const match = endpoint.match(/^([A-Za-z_][A-Za-z0-9_]*)\.(?:@(\d+)|([^\s]+))$/);
  if (!match) return null;
  const block = (state.board?.blocks || []).find(item => item.id === match[1] && item.type === "device");
  if (!block) return null;
  return (block.pin_anchors || []).find(anchor => (
    match[2] ? Number(anchor.physical_pin) === Number(match[2]) : anchor.port === match[3]
  )) || null;
}

function showPinGuide(from, to) {
  const start = guideAnchor(from); const end = guideAnchor(to);
  if (!start || !end) return false;
  state.guide = { from: start.endpoint, to: end.endpoint, startId: start.id, endId: end.id };
  renderBoard();
  status(`Blue guide: ${state.guide.from} → ${state.guide.to}. Drag from the first blue pin to the second; no source has changed.`);
  log(`Guide shown: ${state.guide.from} → ${state.guide.to}`);
  return true;
}

function clearPinGuide() {
  if (!state.guide) return;
  state.guide = null;
  document.querySelector(".pin-guide")?.remove();
}

function drawPinGuide(canvas) {
  const start = canvas.querySelector(`[data-anchor-id="${CSS.escape(state.guide.startId)}"]`);
  const end = canvas.querySelector(`[data-anchor-id="${CSS.escape(state.guide.endId)}"]`);
  if (!start || !end) return;
  const canvasBox = canvas.getBoundingClientRect();
  const startBox = start.getBoundingClientRect(); const endBox = end.getBoundingClientRect();
  const x1 = startBox.left + startBox.width / 2 - canvasBox.left + canvas.scrollLeft;
  const y1 = startBox.top + startBox.height / 2 - canvasBox.top + canvas.scrollTop;
  const x2 = endBox.left + endBox.width / 2 - canvasBox.left + canvas.scrollLeft;
  const y2 = endBox.top + endBox.height / 2 - canvasBox.top + canvas.scrollTop;
  const namespace = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(namespace, "svg"); svg.classList.add("pin-guide");
  const line = document.createElementNS(namespace, "line");
  line.setAttribute("x1", x1); line.setAttribute("y1", y1); line.setAttribute("x2", x2); line.setAttribute("y2", y2);
  const label = document.createElementNS(namespace, "text");
  label.setAttribute("x", (x1 + x2) / 2); label.setAttribute("y", (y1 + y2) / 2 - 8); label.textContent = `${state.guide.from} → ${state.guide.to}`;
  svg.append(line, label); canvas.prepend(svg);
}

function drawPenPreview(canvas) {
  const start = endpointBoardPoint(state.pen.from); if (!start) return;
  const points = [start, ...state.pen.vias, state.pen.position];
  const namespace = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(namespace, "svg"); svg.classList.add("pen-preview");
  const polyline = document.createElementNS(namespace, "polyline");
  polyline.setAttribute("points", points.map(point => {
    const screen = projectWorldPoint(canvas, point);
    return `${screen.x},${screen.y}`;
  }).join(" "));
  svg.append(polyline); canvas.prepend(svg);
}

async function proposePinConnection(start, end) {
  let from = start.endpoint;
  let to = end.endpoint;
  if (start.direction === "input" && end.direction === "output") [from, to] = [to, from];
  try {
    const preview = await request("component-language-edit-preview", { source: state.source, source_revision: state.revision, edit: { kind: "connect", from, to }, source_name: "Board draft" });
    if (!preview.ok) {
      status(firstDiagnostic(preview), true);
      log(`Not proposed: ${preview.student.message}`);
      return;
    }
    $("#connect-from").value = from;
    $("#connect-to").value = to;
    $("#connect-form").classList.remove("hidden");
    status(`Proposed ${preview.patch.added_line} (${preview.resolved_digest}). Review it, then use Apply checked connection; source and topology are unchanged.`);
    log(`Preview passed: ${preview.patch.added_line}`);
  } catch (error) { status(error.message, true); }
}

function selectWire(wire) {
  state.selected = { id: `${wire.from}->${wire.to}` };
  $("#lens").innerHTML = `<strong>Connection</strong><p>This sends the signal from <b>${wire.from}</b> to <b>${wire.to}</b>.</p><button id="disconnect-wire">Disconnect this wire</button>`;
  $("#disconnect-wire").onclick = () => editConnection("disconnect", wire.from, wire.to);
  highlightSource(`connect ${wire.from} -> ${wire.to};`);
}

function highlightSource(text) { const area = $("#source"); const position = area.value.indexOf(text); if (position >= 0) { area.focus(); area.setSelectionRange(position, position + text.length); } }

async function editConnection(kind, from, to) {
  try {
    const result = await request("component-language-edit", { source: state.source, source_revision: state.revision, edit: { kind, from, to }, source_name: "Board draft" });
    if (!result.ok) { status(firstDiagnostic(result), true); log(`Not changed: ${result.student.message}`); return; }
    state.source = result.source; state.revision = result.source_revision; $("#source").value = state.source; saveDraft(); log(result.student.message); await resolve();
  } catch (error) { status(error.message, true); }
}

async function runCommand(text) {
  const command = text.trim(); if (!command) return;
  log(`> ${command}`); $("#terminal-input").value = "";
  try {
    if (command === "help") { log("Circuit: connect U1.1Y to U2.1A. Board route: route U1.1Y to U2.1A via (30,40) (60,40). Pen: route from U1.1Y to U2.1A; pd; fd 20; rt 90; fd 20; pen to U2.1A. Escape or cancel route discards a preview."); return; }
    if (command === "board") { log(JSON.stringify(state.boardProfile, null, 2)); return; }
    if (command === "discard board profile") {
      state.boardProfile = freshBoardProfile(state.resolved);
      state.staleBoardProfile = false;
      localStorage.removeItem(BOARD_PROFILE_KEY);
      renderBoard();
      status("Discarded the stale Board picture. Component source and topology are unchanged.");
      log("Discarded Board profile.");
      return;
    }
    if (command === "cancel route") { cancelPendingInteraction(); return; }
    let match = command.match(/^route\s+from\s+(\S+)\s+to\s+(\S+)$/);
    if (match) { beginPenRoute(match[1], match[2]); return; }
    match = command.match(/^route\s+(\S+)\s*(?:to|->)\s*(\S+)\s+via\s+(.+)$/);
    if (match) { const points = parseWorldRoutePoints(match[3]); if (!points.length) { status("Use world coordinates such as (-120,80) after via.", true); return; } routeVisualConnection(match[1], match[2], points); return; }
    match = command.match(/^(?:pen|move pen)\s+to\s+(\S+)$/);
    if (match) {
      if (state.pen) { finishPenAt(match[1]); return; }
      const point = endpointBoardPoint(match[1]);
      if (!point) { status(`I cannot find visible endpoint ${match[1]}.`, true); return; }
      state.pen = { from: match[1], to: match[1], position: point, heading: 0, down: false, vias: [] };
      renderBoard(); status(`Pen moved to ${match[1]} at ${pointText(point)}. Start a route from an existing connection to draw.`); return;
    }
    if (command === "pd") { if (!state.pen) { status("Move the pen to a pin first.", true); return; } state.pen.down = true; status("Pen down: forward moves add Board route points."); return; }
    if (command === "pu") { if (!state.pen) { status("Move the pen to a pin first.", true); return; } state.pen.down = false; status("Pen up: forward moves do not add route points."); return; }
    match = command.match(/^(fd|bk)\s+(-?\d+(?:\.\d+)?)$/i);
    if (match) { movePen((match[1].toLowerCase() === "bk" ? -1 : 1) * Number(match[2])); return; }
    match = command.match(/^(rt|lt)\s+(-?\d+(?:\.\d+)?)$/i);
    if (match) { if (!state.pen) { status("Move the pen to a pin first.", true); return; } state.pen.heading += (match[1].toLowerCase() === "rt" ? 1 : -1) * Number(match[2]); status(`Pen heading ${state.pen.heading.toFixed(1)} degrees.`); return; }
    match = command.match(/^run\s+([A-Za-z_][A-Za-z0-9_]*)$/);
    if (match) { const result = await request("component-language-run", { source: state.source, drives: state.drives }, { test: match[1] }); log(`Passed ${match[1]}. ${probeSentence(result.probes.probes)}`); return; }
    match = command.match(/^drive\s+([^\s]+)\s+([01ZX])$/i);
    if (match) { const drives = state.drives.filter(item => item.target !== match[1]); drives.push({ target: match[1], value: match[2].toUpperCase() }); const result = await request("component-language-run", { source: state.source, drives }); state.drives = drives; log(`Drove ${match[1]} = ${match[2].toUpperCase()}. ${probeSentence(result.probes.probes)}`); return; }
    match = command.match(/^watch\s+([A-Za-z_][A-Za-z0-9_]*)$/);
    if (match) { const result = await request("component-language-run", { source: state.source, drives: state.drives, probe: match[1] }); log(probeSentence(result.probes.probes)); return; }
    match = command.match(/^connect\s+([^\s]+)\s+to\s+([^\s]+)$/);
    if (match) {
      const start = guideAnchor(match[1]); const end = guideAnchor(match[2]);
      if (start && end) { showPinGuide(match[1], match[2]); await proposePinConnection(start, end); return; }
      await editConnection("connect", match[1], match[2]); return;
    }
    match = command.match(/^disconnect\s+([^\s]+)\s+from\s+([^\s]+)$/);
    if (match) { await editConnection("disconnect", match[1], match[2]); return; }
    log("I know circuit connect/disconnect, Board route, pen/pd/pu/fd/bk/rt/lt, run, drive, watch, board, and help. This is not an operating-system shell.");
  } catch (error) { status(error.message, true); log(`Could not run that: ${error.message}`); }
}

function probeSentence(probes) { const values = Object.entries(probes || {}).map(([name, value]) => `${name} is ${Array.isArray(value) ? value.join("") : value}`); return values.length ? values.join("; ") : "No declared watch value yet."; }

$("#source").addEventListener("input", () => { state.source = $("#source").value; $("#save-state").textContent = "Saving draft…"; clearTimeout(state.timer); state.timer = setTimeout(() => { saveDraft(); resolve(); }, 350); });
$("#run-test").onclick = () => runCommand("run inversion");
$("#watch-output").onclick = () => runCommand("watch inverted_level");
$("#terminal-form").addEventListener("submit", event => { event.preventDefault(); runCommand($("#terminal-input").value); });
$(".suggestions").addEventListener("click", event => { if (event.target.dataset.command) runCommand(event.target.dataset.command); });
$("#terminal-expand").onclick = () => { $("#terminal-pane").classList.toggle("expanded"); $("#terminal-expand").textContent = $("#terminal-pane").classList.contains("expanded") ? "Collapse" : "Expand"; };
$("#reset-layout").onclick = () => {
  document.querySelectorAll(".fullscreen").forEach(item => item.classList.remove("fullscreen"));
  const canvas = $("#board-canvas");
  state.viewport = viewport({ center: { x: 0, y: 0 }, pixelsPerWorld: Math.max(.1, Math.min(canvas.clientWidth, canvas.clientHeight) / 600) });
  renderBoard(); status("View reset. Component source and Board picture are unchanged.");
};
document.querySelectorAll(".pane-toggle").forEach(button => button.onclick = () => document.getElementById(button.dataset.pane).classList.toggle("fullscreen"));
document.querySelectorAll(".tool").forEach(button => button.onclick = () => {
  document.querySelectorAll(".tool").forEach(item => item.classList.remove("selected")); button.classList.add("selected");
  $("#connect-form").classList.toggle("hidden", button.dataset.tool !== "connect"); if (button.dataset.tool !== "label") cancelLabelDraft();
  if (button.dataset.tool === "select") status("Select is active. Left-drag any device, net, route bend, or label to move its Board picture.");
});
$("#close-connect").onclick = () => cancelPendingInteraction();
$("#connect-form").addEventListener("submit", event => { event.preventDefault(); editConnection("connect", $("#connect-from").value.trim(), $("#connect-to").value.trim()); });
$("#close-label").onclick = () => cancelLabelDraft();
$("#label-form").addEventListener("submit", event => { event.preventDefault(); saveLabelDraft(); });
$("#board-canvas").addEventListener("click", event => {
  if (!document.querySelector('.tool.selected[data-tool="label"]') || (event.target !== $("#board-canvas") && !event.target.classList.contains("board-vectors"))) return;
  beginLabel(boardPoint(event));
});
$("#board-canvas").addEventListener("wheel", event => {
  event.preventDefault();
  const canvas = $("#board-canvas"); const box = canvas.getBoundingClientRect();
  state.viewport = zoomViewportAt(ensureViewport(canvas), event.deltaY < 0 ? 1.12 : 1 / 1.12, { x: event.clientX - box.left, y: event.clientY - box.top }, canvasRect(canvas));
  renderBoard();
}, { passive: false });
$("#board-canvas").addEventListener("pointerdown", event => {
  const canvas = $("#board-canvas");
  if (event.button !== 1 && !event.shiftKey) return;
  if (event.target !== canvas && !event.target.classList.contains("board-vectors")) return;
  event.preventDefault();
  state.viewportDrag = { x: event.clientX, y: event.clientY };
  canvas.classList.add("panning");
});

document.addEventListener("keydown", event => {
  if (event.key !== "Escape") return;
  if (state.labelDraft) { cancelLabelDraft(); status("Label cancelled. Component source and Board picture are unchanged."); return; }
  cancelPendingInteraction();
});

document.addEventListener("pointermove", event => {
  if (state.viewportDrag) {
    const canvas = $("#board-canvas");
    const last = state.viewportDrag;
    state.viewport = panViewport(ensureViewport(canvas), { x: event.clientX - last.x, y: event.clientY - last.y });
    state.viewportDrag = { x: event.clientX, y: event.clientY };
    renderBoard();
    return;
  }
  moveBoardDrag(event);
});
document.addEventListener("pointerup", () => {
  if (state.viewportDrag) {
    state.viewportDrag = null; $("#board-canvas").classList.remove("panning");
    status("View moved. Component source and Board picture are unchanged.");
    return;
  }
  finishBoardDrag(); if (state.pinGesture) { state.pinGesture = null; clearPinGuide(); status("Connection cancelled. Component source is unchanged."); }
});
window.addEventListener("resize", () => { if (state.board) renderBoard(); });

loadExample().catch(error => status(`Start the local Components API first: ${error.message}`, true));
