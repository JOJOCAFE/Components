// Reusable semantic operation for transient Board routing-guide visibility.
// It does not alter Component source, topology, or the persisted Board profile.

export const GUIDE_OPERATION_SCHEMA = "components.operation@1";
export const GUIDE_OPERATION_KIND = "board.guide.toggle";
export const GUIDE_OPERATION_AUTHORITY = "board_session";

function requiredString(value, message) {
  if (typeof value !== "string" || !value) throw new Error(message);
  return value;
}

export function guideFocusKey(focus) {
  if (focus?.kind === "pin") return `pin:${requiredString(focus.endpoint, "Guide pin focus needs an endpoint.")}`;
  if (focus?.kind === "device" || focus?.kind === "net") return `${focus.kind}:${requiredString(focus.id, "Guide node focus needs an id.")}`;
  throw new Error("Guide focus must name a device, net, or pin.");
}

export function wireMatchesGuideFocus(wire, focus) {
  if (focus.kind === "pin") return wire.from === focus.endpoint || wire.to === focus.endpoint;
  if (focus.kind === "net") return wire.from === focus.id || wire.to === focus.id;
  const prefix = `${focus.id}.`;
  return wire.from.startsWith(prefix) || wire.to.startsWith(prefix);
}

export function createGuideToggleOperation({ focus, topology }) {
  const key = guideFocusKey(focus);
  const componentId = requiredString(topology?.componentId, "Guide operation needs a Component id.");
  const digest = requiredString(topology?.digest, "Guide operation needs a topology digest.");
  return {
    schema: GUIDE_OPERATION_SCHEMA,
    version: 1,
    id: `board.guide.toggle:${key}`,
    kind: GUIDE_OPERATION_KIND,
    authority: GUIDE_OPERATION_AUTHORITY,
    target: focus.kind === "pin" ? { kind: "device-pin", endpoint: focus.endpoint } : { kind: focus.kind === "device" ? "device-instance" : "net", id: focus.id },
    topology_ref: { component_id: componentId, schema: "components.resolved-component@1", digest },
  };
}

export function applyGuideToggleOperation(operation, { wires, visibleEdgeIds }) {
  if (operation?.schema !== GUIDE_OPERATION_SCHEMA || operation?.version !== 1 || operation?.kind !== GUIDE_OPERATION_KIND || operation?.authority !== GUIDE_OPERATION_AUTHORITY) throw new Error("Unsupported guide operation.");
  const target = operation.target || {};
  const focus = target.kind === "device-pin" ? { kind: "pin", endpoint: requiredString(target.endpoint, "Guide pin target needs an endpoint.") } : target.kind === "device-instance" ? { kind: "device", id: requiredString(target.id, "Guide device target needs an id.") } : target.kind === "net" ? { kind: "net", id: requiredString(target.id, "Guide net target needs an id.") } : (() => { throw new Error("Guide operation target must be a device, net, or pin."); })();
  if (!Array.isArray(wires) || !Array.isArray(visibleEdgeIds)) throw new Error("Guide operation needs wires and visible edge ids.");
  const matching = wires.filter(wire => wireMatchesGuideFocus(wire, focus));
  const edgeIds = matching.map(wire => requiredString(wire.id, "Guide wire needs an id."));
  const visible = new Set(visibleEdgeIds);
  const allVisible = edgeIds.length > 0 && edgeIds.every(id => visible.has(id));
  if (allVisible) edgeIds.forEach(id => visible.delete(id));
  else edgeIds.forEach(id => visible.add(id));
  return { focus, edgeIds, visibleEdgeIds: [...visibleEdgeIds.filter(id => visible.has(id)), ...edgeIds.filter(id => visible.has(id) && !visibleEdgeIds.includes(id))], visible: !allVisible && edgeIds.length > 0 };
}
