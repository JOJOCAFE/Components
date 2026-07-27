/**
 * Guide tool — toggle alignment guides and grid overlay.
 */
export function createGuideTool() {
  return {
    id: 'guide',
    label: 'Guides',
    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5"><line x1="10" y1="0" x2="10" y2="20"/><line x1="0" y1="10" x2="20" y2="10"/><rect x="2" y="2" width="16" height="16" stroke-dasharray="2 2"/></svg>',

    onActivate(state) {
      // Toggle guide visibility; this tool acts as a toggle button
      // After toggling, revert to previous tool
      return 'Activate guides: toggle grid/alignment overlay visibility';
    },

    onDeactivate(state) {
      // No cleanup needed — guides persist independently of active tool
      return 'Deactivate guides: no-op (guides stay visible if toggled on)';
    },

    onCanvasClick(event, state) {
      // Guides tool doesn't handle canvas clicks
      return 'Click: no-op for guide tool';
    },
  };
}
