// Presentation-only Board profile rules. This module deliberately knows
// nothing about Component source, pins, or electrical behavior.

export const BOARD_PROFILE_SCHEMA = "components.board-profile@1";
export const BOARD_PROFILE_VERSION = 1;

export function isBoardPoint(value) {
  return Boolean(value) && Number.isFinite(value.x) && Number.isFinite(value.y)
    && value.x >= 0 && value.x <= 100 && value.y >= 0 && value.y <= 100;
}

export function checkedBoardPoint(value) {
  if (!isBoardPoint(value)) throw new Error("Board coordinates must be finite values from 0 to 100.");
  return { x: Number(value.x), y: Number(value.y) };
}

export function createBoardProfile({ componentId, digest, title }) {
  return {
    schema: BOARD_PROFILE_SCHEMA, version: BOARD_PROFILE_VERSION,
    topology_ref: { component_id: componentId, schema: "components.resolved-component@1", digest },
    resource_bindings: [], placements: [], routes: [], labels: [], widgets: [], physical_captures: [],
    view: { title, theme: "light" },
  };
}

export function loadBoardProfile(saved, topology) {
  if (!saved) return { status: "missing", profile: createBoardProfile(topology) };
  if (saved.schema !== BOARD_PROFILE_SCHEMA || saved.version !== BOARD_PROFILE_VERSION) return { status: "invalid", profile: createBoardProfile(topology) };
  if (saved.topology_ref?.component_id !== topology.componentId || saved.topology_ref?.digest !== topology.digest) return { status: "stale", profile: createBoardProfile(topology), saved };
  return { status: "current", profile: saved };
}

export function parseRoutePoints(text) {
  const matches = [...text.matchAll(/\(\s*([^,()]+)\s*,\s*([^,()]+)\s*\)/g)];
  const remainder = text.replace(/\(\s*([^,()]+)\s*,\s*([^,()]+)\s*\)/g, "").trim();
  if (!matches.length || remainder) throw new Error("Use only Board coordinates such as (30,40) after via.");
  return matches.map(match => checkedBoardPoint({ x: Number(match[1]), y: Number(match[2]) }));
}

export function advancePen(point, heading, distance) {
  if (!Number.isFinite(heading) || !Number.isFinite(distance)) throw new Error("Pen heading and distance must be finite numbers.");
  const radians = heading * Math.PI / 180;
  return checkedBoardPoint({ x: point.x + Math.cos(radians) * distance, y: point.y + Math.sin(radians) * distance });
}

export function routeRecord({ edgeId, kind, start, vias, end }) {
  if (kind !== "scalar") throw new Error("Board routes are available only for resolved scalar edges; bus routes need their own contract.");
  return { edge_id: edgeId, points: [start, ...vias, end].map(checkedBoardPoint) };
}

export function labelRecord({ id, position, text, fontSize }) {
  if (!/^[A-Za-z_][A-Za-z0-9_-]*$/.test(id)) throw new Error("A Board label needs a simple identifier.");
  if (typeof text !== "string" || !text.trim()) throw new Error("Enter label text before placing it.");
  if (!Number.isFinite(fontSize) || fontSize < 1.5 || fontSize > 8) throw new Error("Label size must be from 1.5 to 8 Board units.");
  return { id, position: checkedBoardPoint(position), text, font_size: Number(fontSize) };
}
