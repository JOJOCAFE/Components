// Board profile @2: persistent presentation in centered Cartesian world units.
// It deliberately contains no Component source, resolved topology, or viewport.

export const BOARD_PROFILE_V2_SCHEMA = "components.board-profile@2";
export const BOARD_PROFILE_V2_VERSION = 2;
export const CENTERED_WORLD_COORDINATE_SPACE = Object.freeze({
  id: "world-centered-cartesian@1", origin: "center", x_axis: "right", y_axis: "up", unit: "world",
});

const ELECTRICAL_FIELDS = new Set(["source", "resolved", "instances", "nets", "buses", "edges", "operations", "drives", "runtime"]);
const TOP_LEVEL_FIELDS = new Set(["schema", "version", "coordinate_space", "topology_ref", "resource_bindings", "placements", "routes", "labels", "widgets", "physical_captures", "view"]);

function object(value, message) {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error(message);
  return value;
}
function array(value, message) { if (!Array.isArray(value)) throw new Error(message); return value; }
function identifier(value, message) { if (typeof value !== "string" || !/^[A-Za-z_][A-Za-z0-9_.:@-]*$/.test(value)) throw new Error(message); return value; }
function finite(value, message) { if (typeof value !== "number" || !Number.isFinite(value)) throw new Error(message); return Number(value); }

export function checkedWorldPoint(value) {
  const point = object(value, "World point must be an x/y object.");
  return { x: finite(point.x, "World x must be finite."), y: finite(point.y, "World y must be finite.") };
}

export function checkedCoordinateSpace(value) {
  const space = object(value, "Board profile @2 requires coordinate_space metadata.");
  for (const [key, expected] of Object.entries(CENTERED_WORLD_COORDINATE_SPACE)) {
    if (space[key] !== expected) throw new Error(`Board profile @2 requires coordinate_space.${key} = ${JSON.stringify(expected)}.`);
  }
  if (Object.keys(space).length !== Object.keys(CENTERED_WORLD_COORDINATE_SPACE).length) throw new Error("Board profile @2 coordinate_space cannot add alternate conventions.");
  return { ...CENTERED_WORLD_COORDINATE_SPACE };
}

function checkedTopologyRef(value, topology) {
  const ref = object(value, "Board profile needs a topology_ref.");
  if (ref.schema !== "components.resolved-component@1") throw new Error("Board profile topology_ref must name components.resolved-component@1.");
  identifier(ref.component_id, "Board profile topology_ref needs a component identifier.");
  if (typeof ref.digest !== "string" || !/^sha256:[0-9a-f]{64}$/.test(ref.digest)) throw new Error("Board profile topology_ref needs a SHA-256 digest.");
  if (topology && (ref.component_id !== topology.componentId || ref.digest !== topology.digest)) throw new Error("Board profile topology reference is stale or wrong.");
  return { component_id: ref.component_id, schema: ref.schema, digest: ref.digest };
}

function checkedRotation(value) {
  const rotation = finite(value, "Placement rotation_deg must be finite.");
  if (![0, 90, 180, 270].includes(rotation)) throw new Error("Placement rotation_deg must be 0, 90, 180, or 270.");
  return rotation;
}

function checkedPlacement(value) {
  const placement = object(value, "Placement must be an object.");
  const target = object(placement.target, "Placement target must be a device instance or net.");
  if (target.kind !== "device-instance" && target.kind !== "net") throw new Error("Placement target must be a device instance or net.");
  return { target: { kind: target.kind, id: identifier(target.id, "Placement target needs an identifier.") }, origin: checkedWorldPoint(placement.origin), rotation_deg: checkedRotation(placement.rotation_deg) };
}

function checkedRoute(value) {
  const route = object(value, "Route must be an object.");
  if (typeof route.edge_id !== "string" || !route.edge_id) throw new Error("Route must name a resolved scalar edge.");
  if (route.edge_id.includes("[") || route.edge_id.startsWith("bus:")) throw new Error("Bus routes need their own contract.");
  return { edge_id: route.edge_id, points: array(route.points, "Route points must be an array.").map(checkedWorldPoint) };
}

function checkedLabel(value) {
  const label = object(value, "Label must be an object.");
  return { id: identifier(label.id, "Label needs an identifier."), position: checkedWorldPoint(label.position), text: typeof label.text === "string" && label.text.trim() ? label.text : (() => { throw new Error("Label needs text."); })(), font_size: finite(label.font_size, "Label font_size must be finite.") };
}

export function createBoardProfileV2({ componentId, digest, title }) {
  return {
    schema: BOARD_PROFILE_V2_SCHEMA, version: BOARD_PROFILE_V2_VERSION, coordinate_space: { ...CENTERED_WORLD_COORDINATE_SPACE },
    topology_ref: { component_id: componentId, schema: "components.resolved-component@1", digest },
    resource_bindings: [], placements: [], routes: [], labels: [], widgets: [], physical_captures: [], view: { title, theme: "light" },
  };
}

export function validateBoardProfileV2(value, topology = null) {
  const profile = object(value, "Board profile @2 must be an object.");
  if (profile.schema !== BOARD_PROFILE_V2_SCHEMA || profile.version !== BOARD_PROFILE_V2_VERSION) throw new Error("Expected components.board-profile@2.");
  for (const key of Object.keys(profile)) {
    if (ELECTRICAL_FIELDS.has(key)) throw new Error(`Board profile cannot contain electrical field ${key}.`);
    if (!TOP_LEVEL_FIELDS.has(key)) throw new Error(`Board profile @2 does not support field ${key}.`);
  }
  const output = {
    schema: BOARD_PROFILE_V2_SCHEMA, version: BOARD_PROFILE_V2_VERSION,
    coordinate_space: checkedCoordinateSpace(profile.coordinate_space),
    topology_ref: checkedTopologyRef(profile.topology_ref, topology),
    resource_bindings: array(profile.resource_bindings, "resource_bindings must be an array."),
    placements: array(profile.placements, "placements must be an array.").map(checkedPlacement),
    routes: array(profile.routes, "routes must be an array.").map(checkedRoute),
    labels: array(profile.labels, "labels must be an array.").map(checkedLabel),
    widgets: array(profile.widgets, "widgets must be an array."),
    physical_captures: array(profile.physical_captures, "physical_captures must be an array."),
  };
  const view = object(profile.view, "view must be an object.");
  if ("viewport" in view || "camera" in view) throw new Error("Viewport state is session-local and cannot be stored in Board profile @2.");
  output.view = { title: typeof view.title === "string" ? view.title : "Components Board", theme: view.theme === "dark" ? "dark" : "light" };
  return output;
}
