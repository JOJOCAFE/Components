/**
 * Editor view — pure functions for the source editor pane.
 */

/**
 * Extract the first diagnostic message from a resolve result.
 * @param {object} result - resolve result with diagnostics array
 * @returns {string|null} first message or null if none
 */
export function firstDiagnostic(result) {
  if (!result || !Array.isArray(result.diagnostics) || result.diagnostics.length === 0) {
    return null;
  }
  return result.diagnostics[0].message || result.diagnostics[0] || null;
}

/**
 * Convert a component ID (e.g. "my-widget") to a friendly display name.
 * @param {string} name - component ID
 * @returns {string} friendly title
 */
export function friendlyTitle(name) {
  if (!name) return '';
  return name
    .replace(/[-_]+/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase());
}

/**
 * Select matching text in the textarea element.
 * @param {HTMLTextAreaElement} textareaEl - target textarea
 * @param {string} text - text to find and highlight
 */
export function highlightSource(textareaEl, text) {
  if (!textareaEl || !text) return;
  const value = textareaEl.value || '';
  const start = value.indexOf(text);
  if (start === -1) return;
  textareaEl.focus();
  textareaEl.setSelectionRange(start, start + text.length);
}
