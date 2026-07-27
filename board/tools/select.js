/**
 * Select/Move tool — pick and drag components on the board.
 */
export function createSelectTool() {
  return {
    id: 'select',
    label: 'Select',
    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 2l10 8-4 1-2 5-2-5-4-1z"/></svg>',

    onActivate(state) {
      // Set cursor to pointer; enable hit-testing on components
      return 'Activate select mode: cursor=pointer, enable component hit-test';
    },

    onDeactivate(state) {
      // Clear any selection highlight; reset cursor
      return 'Deactivate select mode: clear selection, reset cursor';
    },

    onCanvasClick(event, state) {
      // Hit-test at (event.x, event.y); if component found, mark selected
      // If empty space, deselect all
      return 'Click: hit-test components, toggle selection';
    },

    onCanvasPointerDown(event, state) {
      // Begin drag if pointer is over a selected component
      // Track delta for move operation
      return 'PointerDown: begin drag on selected component';
    },
  };
}
