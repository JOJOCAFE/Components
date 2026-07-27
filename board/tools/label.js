/**
 * Label tool — place and edit text labels on the board.
 */
export function createLabelTool() {
  return {
    id: 'label',
    label: 'Label',
    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5"><text x="3" y="15" font-size="14" font-family="monospace" fill="currentColor">A</text></svg>',

    onActivate(state) {
      // Set cursor to text; prepare for label placement
      return 'Activate label mode: cursor=text, ready for placement';
    },

    onDeactivate(state) {
      // Commit any in-progress label edit; reset cursor
      return 'Deactivate label mode: commit pending edits, reset cursor';
    },

    onCanvasClick(event, state) {
      // If clicking existing label: enter edit mode
      // If clicking empty space: create new label at position
      return 'Click: create new label or edit existing label at position';
    },

    onCanvasPointerDown(event, state) {
      // Begin drag to reposition an existing label
      return 'PointerDown: begin label drag for repositioning';
    },
  };
}
