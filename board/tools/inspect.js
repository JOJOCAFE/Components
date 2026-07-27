/**
 * Inspect tool — click a component or wire to view its properties.
 */
export function createInspectTool() {
  return {
    id: 'inspect',
    label: 'Inspect',
    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="9" cy="9" r="5"/><line x1="13" y1="13" x2="18" y2="18"/></svg>',

    onActivate(state) {
      // Set cursor to help; prepare info panel
      return 'Activate inspect mode: cursor=help, show info panel';
    },

    onDeactivate(state) {
      // Hide info panel; reset cursor
      return 'Deactivate inspect mode: hide info panel, reset cursor';
    },

    onCanvasClick(event, state) {
      // Hit-test at position; if component/wire found, populate info panel
      // with properties (id, type, connections, value)
      return 'Click: show properties panel for component/wire at position';
    },

    onCanvasPointerDown(event, state) {
      // No drag behavior for inspect tool
      return 'PointerDown: no-op for inspect tool';
    },
  };
}
