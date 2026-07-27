/** Canvas-view: pure/DOM-minimal rendering helpers for the Board controller.
 *  No event listeners. No state mutation. Import from app.js and call as needed.
 */
import { viewport, worldToScreen, screenToWorld, adaptiveGrid } from "../viewport.js";
import { checkedWorldPoint } from "../profile-v2.js";

// ─── 1. canvasRect ──────────────────────────────────────────────────────────────
/** Returns the usable pixel dimensions of the canvas element. */
export function canvasRect(canvas) {
  return { width: Math.max(1, canvas.clientWidth), height: Math.max(1, canvas.clientHeight) };
}

// ─── 2. ensureViewport ──────────────────────────────────────────────────────────
/** Creates a viewport on state if missing; returns the current viewport. */
export function ensureViewport(state, canvas) {
  if (!state.viewport) {
    const rect = canvasRect(canvas);
    state.viewport = viewport({
      center: { x: 0, y: 0 },
      pixelsPerWorld: Math.max(0.1, Math.min(rect.width, rect.height) / 600),
    });
  }
  return state.viewport;
}

// ─── 3. projectWorldPoint ───────────────────────────────────────────────────────
/** Converts a world-coordinate point to screen pixels relative to the canvas. */
export function projectWorldPoint(state, canvas, point) {
  return worldToScreen(ensureViewport(state, canvas), point, canvasRect(canvas));
}

// ─── 4. updateGrid ──────────────────────────────────────────────────────────────
/** Sets CSS custom properties on the canvas for grid rendering. */
export function updateGrid(state, canvas) {
  const view = ensureViewport(state, canvas);
  const grid = adaptiveGrid(view);
  const screen = canvasRect(canvas);
  const origin = worldToScreen(view, { x: 0, y: 0 }, screen);
  canvas.style.setProperty("--grid-major-px", `${grid.majorPixels}px`);
  canvas.style.setProperty("--grid-minor-px", `${grid.majorPixels / 5}px`);
  canvas.style.setProperty("--grid-origin-x", `${origin.x}px`);
  canvas.style.setProperty("--grid-origin-y", `${origin.y}px`);
}

// ─── 5. endpointScreenPoint ─────────────────────────────────────────────────────
/** Finds the screen position of a pin anchor element within the canvas.
 *  Returns {x, y} or null if the anchor is not rendered.
 */
export function endpointScreenPoint(canvas, endpoint) {
  const anchor = canvas.querySelector(`[data-endpoint="${CSS.escape(endpoint)}"]`);
  if (!anchor) return null;
  const canvasBox = canvas.getBoundingClientRect();
  const box = anchor.getBoundingClientRect();
  return {
    x: box.left + box.width / 2 - canvasBox.left,
    y: box.top + box.height / 2 - canvasBox.top,
  };
}

// ─── 6. shouldShowWire ──────────────────────────────────────────────────────────
/** Determines whether a wire should be displayed based on saved routes and guide state. */
export function shouldShowWire(state, wire) {
  const id = wire.id || `edge:${wire.from}->${wire.to}`;
  const routes = state.boardProfile?.routes || [];
  if (routes.some((r) => r.edge_id === id)) return true;
  return (state.guideVisibleEdges || []).includes(id);
}

// ─── 7. chipFrame ───────────────────────────────────────────────────────────────
/** Returns an HTML string for a chip frame with pin anchors positioned by DIP order. */
export function chipFrame(node, compact = false) {
  const anchors = (node.pinAnchors || [])
    .map((anchor) => {
      const top = ((100 + (Number(anchor.dip_order) - 1) * 100) / 940) * 100;
      return `<button class="pin-anchor ${anchor.dip_side}" type="button" data-anchor-id="${anchor.id}" data-endpoint="${anchor.endpoint}" data-direction="${anchor.direction}" data-pin-number="${anchor.physical_pin}" data-pin-name="${anchor.port}" data-component-selector="@${anchor.physical_pin}" style="top:${top}%" aria-label="Connect node ${anchor.endpoint}, ${anchor.direction}"></button>`;
    })
    .join("");
  const caption = compact
    ? ""
    : "<figcaption>Drag from one visible pin to another to propose a checked source edit. This frame owns no wiring state.</figcaption>";
  return `<figure class="pinout-art chip-frame${compact ? " compact" : ""}" data-frame-device="${node.id}"><img src="${node.resource.asset}" alt="${node.part} logic symbol" draggable="false"><div class="pin-anchor-layer" aria-label="Definition-owned ${node.part} connect nodes">${anchors}</div>${caption}</figure>`;
}

// ─── 8. genericAnchorMarkup ─────────────────────────────────────────────────────
/** Returns an HTML string for generic (non-chip) anchor buttons. */
export function genericAnchorMarkup(node) {
  const anchors = node.pinAnchors || [];
  return anchors
    .map((anchor) => {
      const side = anchor.dip_side === "left" ? "left" : "right";
      const sideAnchors = anchors.filter(
        (item) => (item.dip_side === "left" ? "left" : "right") === side,
      );
      const sideIndex = sideAnchors.indexOf(anchor);
      const top =
        sideAnchors.length === 1
          ? 50
          : 18 + sideIndex * (64 / (sideAnchors.length - 1));
      const pinNumber = anchor.physical_pin ?? "";
      const pinName = anchor.port ?? anchor.endpoint;
      return `<button class="pin-anchor generic-anchor ${side}" type="button" data-anchor-id="${anchor.id}" data-endpoint="${anchor.endpoint}" data-direction="${anchor.direction}" data-pin-number="${pinNumber}" data-pin-name="${pinName}" data-component-selector="${pinNumber ? `@${pinNumber}` : ""}" style="top:${top}%" aria-label="Connect node ${anchor.endpoint}, ${anchor.direction}"></button>`;
    })
    .join("");
}

// ─── 9. boardPoint ──────────────────────────────────────────────────────────────
/** Converts a pointer event to validated world coordinates relative to the canvas. */
export function boardPoint(state, event, canvas) {
  const box = canvas.getBoundingClientRect();
  const world = screenToWorld(
    ensureViewport(state, canvas),
    { x: event.clientX - box.left, y: event.clientY - box.top },
    canvasRect(canvas),
  );
  return checkedWorldPoint(world);
}
