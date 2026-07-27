/**
 * Connect tool — draw wires between component pins.
 */
export function createConnectTool() {
  return {
    id: 'connect',
    label: 'Connect',
    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="4" cy="16" r="2"/><circle cx="16" cy="4" r="2"/><path d="M6 14L14 6"/></svg>',

    onActivate(state) {
      // Set cursor to crosshair; highlight available pins
      return 'Activate connect mode: cursor=crosshair, show pin targets';
    },

    onDeactivate(state) {
      // Cancel any in-progress wire; hide pin highlights
      return 'Deactivate connect mode: cancel pending wire, hide pins';
    },

    onCanvasClick(event, state) {
      // If no wire started: snap to nearest pin, begin wire
      // If wire in progress: snap to target pin, commit connection
      return 'Click: start or complete wire connection at nearest pin';
    },

    onCanvasPointerDown(event, state) {
      // Alternative: begin wire drawing on pointer down for drag-style wiring
      return 'PointerDown: begin drag-wire from pin';
    },
  };
}
