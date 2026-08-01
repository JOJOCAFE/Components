/**
 * Components Board — Page Tabs
 * Task 1.8: DOM-free page tabs state manager.
 *
 * Manages multi-page navigation: add, switch, rename, delete pages.
 * Sends commands to the engine for state changes.
 * A thin DOM adapter renders the tab bar.
 *
 * ES module syntax, Node.js compatible, no browser APIs.
 */

/**
 * Create a page tabs controller.
 * @param {object} engine - The engine instance (from createEngine)
 * @returns {object} Page tabs API
 */
export function createPageTabs(engine) {
  if (!engine || typeof engine.run !== 'function') {
    throw new Error('PageTabs requires an engine with run() method');
  }

  /**
   * Get all pages with active state.
   * @returns {Array<{name: string, active: boolean}>}
   */
  function getPages() {
    const state = engine.getState();
    const pages = state.pages;
    return pages.list.map(name => ({
      name,
      active: name === pages.active,
    }));
  }

  /**
   * Get the name of the currently active page.
   * @returns {string}
   */
  function getActivePage() {
    const state = engine.getState();
    return state.pages.active;
  }

  /**
   * Add a new page via engine command.
   * @param {string} name - New page name
   * @returns {object} Engine result {success, message|error}
   */
  function addPage(name) {
    return engine.run(JSON.stringify({ command: 'new-page', name }));
  }

  /**
   * Switch to a page via engine command.
   * @param {string} name - Target page name
   * @returns {object} Engine result {success, message|error}
   */
  function switchPage(name) {
    return engine.run(JSON.stringify({ command: 'switch-page', name }));
  }

  /**
   * Rename a page via engine command.
   * @param {string} oldName - Current page name
   * @param {string} newName - New page name
   * @returns {object} Engine result {success, message|error}
   */
  function renamePage(oldName, newName) {
    return engine.run(JSON.stringify({ command: 'rename-page', old_name: oldName, new_name: newName }));
  }

  /**
   * Delete a page via engine command.
   * @param {string} name - Page to delete
   * @returns {object} Engine result {success, message|error}
   */
  function deletePage(name) {
    return engine.run(JSON.stringify({ command: 'delete-page', name }));
  }

  /**
   * Check if deletion is possible (more than 1 page exists).
   * @returns {boolean}
   */
  function canDelete() {
    const state = engine.getState();
    return state.pages.list.length > 1;
  }

  return Object.freeze({
    getPages,
    getActivePage,
    addPage,
    switchPage,
    renamePage,
    deletePage,
    canDelete,
  });
}
