const $ = (selector) => document.querySelector(selector);
const state = { source: "", revision: "", resolved: null, board: null, selected: null, drives: [], timer: null };
const STORAGE_KEY = "components.board.not-gate.source.v1";
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
  try {
    const result = await request("component-language-resolve", { source: state.source, source_name: "Board draft" });
    state.resolved = result;
    state.revision = await sha256(state.source);
    if (!result.ok) { status(firstDiagnostic(result), true); return; }
    state.board = await request("component-language-board-view", { source: state.source, source_name: "Board draft" });
    $("#component-name").textContent = friendlyTitle(result.component_id);
    status("Looks good. Click a part or wire to read it, then try one action.");
    renderBoard();
  } catch (error) { status(error.message, true); }
}

function firstDiagnostic(result) { const item = result.diagnostics?.[0]; return item ? `${item.message} (line ${item.span?.line || "?"})` : "The text needs fixing before the Drawing can update."; }
function friendlyTitle(name) { return name === "DigitalInverterFixture" ? "A NOT gate" : name || "Components Board"; }
async function sha256(text) { const bytes = new TextEncoder().encode(text); const hash = await crypto.subtle.digest("SHA-256", bytes); return "sha256:" + [...new Uint8Array(hash)].map(x => x.toString(16).padStart(2, "0")).join(""); }

function renderBoard() {
  const canvas = $("#board-canvas"); canvas.replaceChildren();
  const blocks = state.board?.blocks || [];
  const devices = blocks.filter(item => item.type === "device");
  const nets = state.board?.nets || [];
  const nodes = [];
  devices.forEach((item, index) => nodes.push({ id: item.id, label: item.id === "U1" ? "U1\nNOT gate" : item.id, x: 18 + index * (64 / Math.max(1, devices.length - 1)), y: 36, kind: "device", part: item.part }));
  nets.filter(item => item.kind !== "power").forEach((item, index) => nodes.push({ id: item.id, label: item.id, x: 18 + index * (64 / Math.max(1, nets.filter(n => n.kind !== "power").length - 1)), y: 72, kind: "net" }));
  const lookup = Object.fromEntries(nodes.map(item => [item.id, item]));
  (state.board?.wires || []).forEach(wire => {
    const left = lookup[wire.from.split(".")[0]] || lookup[wire.from]; const right = lookup[wire.to.split(".")[0]] || lookup[wire.to];
    if (left && right) drawEdge(canvas, left, right, wire);
  });
  nodes.forEach(node => drawNode(canvas, node));
}

function drawEdge(canvas, from, to, wire) {
  const edge = document.createElement("button"); edge.className = "edge"; edge.title = `${wire.from} → ${wire.to}`;
  const dx = to.x - from.x, dy = to.y - from.y, length = Math.sqrt(dx * dx + dy * dy);
  edge.style.left = `${from.x}%`; edge.style.top = `${from.y}%`; edge.style.width = `${length}%`; edge.style.transform = `rotate(${Math.atan2(dy, dx)}rad)`;
  edge.addEventListener("click", () => selectWire(wire)); canvas.append(edge);
}

function drawNode(canvas, node) {
  const button = document.createElement("button"); button.className = `node ${node.kind}` + (state.selected?.id === node.id ? " selected" : "");
  button.style.left = `${node.x}%`; button.style.top = `${node.y}%`; button.textContent = node.label; button.addEventListener("click", () => selectNode(node)); canvas.append(button);
}

function selectNode(node) {
  state.selected = node; renderBoard();
  const technical = node.kind === "device" ? `${node.part} Device` : "Wire (net)";
  const sentence = node.id === "U1" ? "This NOT gate changes 0 into 1, and 1 into 0." : node.kind === "net" ? "This wire carries a named signal between declared parts." : "This is a declared part in this small machine.";
  $("#lens").innerHTML = `<strong>${node.kind === "device" ? "Part" : "Wire"}: ${node.id}</strong><p>${sentence}</p><small>Real name: ${technical}</small>`;
  highlightSource(node.id);
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
    if (command === "help") { log("Try: run inversion | drive Clock.CLK 0 | watch inverted_level | connect U1.1Y to OUT"); return; }
    let match = command.match(/^run\s+([A-Za-z_][A-Za-z0-9_]*)$/);
    if (match) { const result = await request("component-language-run", { source: state.source, drives: state.drives }, { test: match[1] }); log(`Passed ${match[1]}. ${probeSentence(result.probes.probes)}`); return; }
    match = command.match(/^drive\s+([^\s]+)\s+([01ZX])$/i);
    if (match) { state.drives = state.drives.filter(item => item.target !== match[1]); state.drives.push({ target: match[1], value: match[2].toUpperCase() }); const result = await request("component-language-run", { source: state.source, drives: state.drives }); log(`Drove ${match[1]} = ${match[2].toUpperCase()}. ${probeSentence(result.probes.probes)}`); return; }
    match = command.match(/^watch\s+([A-Za-z_][A-Za-z0-9_]*)$/);
    if (match) { const result = await request("component-language-run", { source: state.source, drives: state.drives, probe: match[1] }); log(probeSentence(result.probes.probes)); return; }
    match = command.match(/^connect\s+([^\s]+)\s+to\s+([^\s]+)$/);
    if (match) { await editConnection("connect", match[1], match[2]); return; }
    match = command.match(/^disconnect\s+([^\s]+)\s+from\s+([^\s]+)$/);
    if (match) { await editConnection("disconnect", match[1], match[2]); return; }
    log("I know run, drive, watch, connect, disconnect, and help. This is not an operating-system shell.");
  } catch (error) { status(error.message, true); log(`Could not run that: ${error.message}`); }
}

function probeSentence(probes) { const values = Object.entries(probes || {}).map(([name, value]) => `${name} is ${Array.isArray(value) ? value.join("") : value}`); return values.length ? values.join("; ") : "No declared watch value yet."; }

$("#source").addEventListener("input", () => { state.source = $("#source").value; $("#save-state").textContent = "Saving draft…"; clearTimeout(state.timer); state.timer = setTimeout(() => { saveDraft(); resolve(); }, 350); });
$("#run-test").onclick = () => runCommand("run inversion");
$("#watch-output").onclick = () => runCommand("watch inverted_level");
$("#terminal-form").addEventListener("submit", event => { event.preventDefault(); runCommand($("#terminal-input").value); });
$(".suggestions").addEventListener("click", event => { if (event.target.dataset.command) runCommand(event.target.dataset.command); });
$("#terminal-expand").onclick = () => { $("#terminal-pane").classList.toggle("expanded"); $("#terminal-expand").textContent = $("#terminal-pane").classList.contains("expanded") ? "Collapse" : "Expand"; };
$("#reset-layout").onclick = () => { document.querySelectorAll(".fullscreen").forEach(item => item.classList.remove("fullscreen")); };
document.querySelectorAll(".pane-toggle").forEach(button => button.onclick = () => document.getElementById(button.dataset.pane).classList.toggle("fullscreen"));
document.querySelectorAll(".tool").forEach(button => button.onclick = () => { document.querySelectorAll(".tool").forEach(item => item.classList.remove("selected")); button.classList.add("selected"); $("#connect-form").classList.toggle("hidden", button.dataset.tool !== "connect"); });
$("#close-connect").onclick = () => $("#connect-form").classList.add("hidden");
$("#connect-form").addEventListener("submit", event => { event.preventDefault(); editConnection("connect", $("#connect-from").value.trim(), $("#connect-to").value.trim()); });

loadExample().catch(error => status(`Start the local Components API first: ${error.message}`, true));
