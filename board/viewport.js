/** Pure Board v2 coordinate transforms. No DOM, parser, or profile mutation. */
export const VIEWPORT_SCHEMA = "components.board-viewport@1";

function finite(value, name) {
  if (typeof value !== "number" || !Number.isFinite(value)) throw new TypeError(`${name} must be a finite number`);
  return value;
}

export function viewport({ center = { x: 0, y: 0 }, pixelsPerWorld = 1, minPixelsPerWorld = .1, maxPixelsPerWorld = 64 } = {}) {
  const min = finite(minPixelsPerWorld, "minPixelsPerWorld");
  const max = finite(maxPixelsPerWorld, "maxPixelsPerWorld");
  const scale = finite(pixelsPerWorld, "pixelsPerWorld");
  if (min <= 0 || max < min || scale < min || scale > max) throw new RangeError("pixelsPerWorld is outside viewport limits");
  return Object.freeze({ schema: VIEWPORT_SCHEMA, center: Object.freeze({ x: finite(center.x, "center.x"), y: finite(center.y, "center.y") }), pixelsPerWorld: scale, minPixelsPerWorld: min, maxPixelsPerWorld: max });
}

function rect(value) {
  const width = finite(value?.width, "screen.width");
  const height = finite(value?.height, "screen.height");
  if (width <= 0 || height <= 0) throw new RangeError("screen dimensions must be positive");
  return { width, height };
}

function point(value, prefix) { return { x: finite(value?.x, `${prefix}.x`), y: finite(value?.y, `${prefix}.y`) }; }

/** Screen pixels have y down; World coordinates have y up. */
export function screenToWorld(view, screen, screenRect) {
  const current = viewport(view), p = point(screen, "screen"), r = rect(screenRect);
  return { x: current.center.x + (p.x - r.width / 2) / current.pixelsPerWorld, y: current.center.y - (p.y - r.height / 2) / current.pixelsPerWorld };
}

export function worldToScreen(view, world, screenRect) {
  const current = viewport(view), p = point(world, "world"), r = rect(screenRect);
  return { x: r.width / 2 + (p.x - current.center.x) * current.pixelsPerWorld, y: r.height / 2 - (p.y - current.center.y) * current.pixelsPerWorld };
}

/** Pan follows the content under a pointer/stylus drag. */
export function panViewport(view, deltaScreen) {
  const current = viewport(view), delta = point(deltaScreen, "deltaScreen");
  return viewport({ ...current, center: { x: current.center.x - delta.x / current.pixelsPerWorld, y: current.center.y + delta.y / current.pixelsPerWorld } });
}

/** Zoom around a screen anchor without moving the anchored world point. */
export function zoomViewportAt(view, factor, anchorScreen, screenRect) {
  const current = viewport(view), multiplier = finite(factor, "zoomFactor");
  if (multiplier <= 0) throw new RangeError("zoomFactor must be positive");
  const anchorWorld = screenToWorld(current, anchorScreen, screenRect);
  const scale = Math.max(current.minPixelsPerWorld, Math.min(current.maxPixelsPerWorld, current.pixelsPerWorld * multiplier));
  const r = rect(screenRect), anchor = point(anchorScreen, "anchorScreen");
  return viewport({ ...current, pixelsPerWorld: scale, center: { x: anchorWorld.x - (anchor.x - r.width / 2) / scale, y: anchorWorld.y + (anchor.y - r.height / 2) / scale } });
}

export function worldBounds(view, screenRect) {
  const current = viewport(view), r = rect(screenRect), halfWidth = r.width / current.pixelsPerWorld / 2, halfHeight = r.height / current.pixelsPerWorld / 2;
  return { minX: current.center.x - halfWidth, maxX: current.center.x + halfWidth, minY: current.center.y - halfHeight, maxY: current.center.y + halfHeight };
}

/** Choose a readable 1/2/5 world-unit grid whose major spacing stays on screen. */
export function adaptiveGrid(view, { targetPixels = 72, minPixels = 48, maxPixels = 108 } = {}) {
  const current = viewport(view), target = finite(targetPixels, "targetPixels"), minimum = finite(minPixels, "minPixels"), maximum = finite(maxPixels, "maxPixels");
  if (target <= 0 || minimum <= 0 || maximum < minimum) throw new RangeError("grid pixel limits are invalid");
  const desired = target / current.pixelsPerWorld;
  const exponent = Math.floor(Math.log10(desired));
  const candidates = [];
  for (let power = exponent - 1; power <= exponent + 1; power += 1) for (const unit of [1, 2, 5]) candidates.push(unit * 10 ** power);
  const allowed = candidates.filter(spacing => spacing * current.pixelsPerWorld >= minimum && spacing * current.pixelsPerWorld <= maximum);
  const spacing = (allowed.length ? allowed : candidates).sort((a, b) => Math.abs(a * current.pixelsPerWorld - target) - Math.abs(b * current.pixelsPerWorld - target))[0];
  return { majorWorldUnits: spacing, minorWorldUnits: spacing / 5, majorPixels: spacing * current.pixelsPerWorld };
}

/** Snap is a Board presentation aid; callers retain the unsnapped input if needed. */
export function snapWorldPoint(value, grid) {
  const p = point(value, "world"), spacing = finite(grid?.majorWorldUnits ?? grid, "grid.majorWorldUnits");
  if (spacing <= 0) throw new RangeError("grid.majorWorldUnits must be positive");
  return { x: Math.round(p.x / spacing) * spacing, y: Math.round(p.y / spacing) * spacing };
}
