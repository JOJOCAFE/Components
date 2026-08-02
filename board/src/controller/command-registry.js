/**
 * Components Board — Command Registry
 *
 * OOP-style command system. Commands organized by group (namespace).
 * Groups are loadable at runtime — plug in new command libraries.
 *
 * Architecture:
 *   registry.register('file', fileCommands)
 *   registry.execute('file.save')       // dot-notation
 *   registry.execute('save')            // short alias lookup
 *   registry.complete('file.')          // tab completion
 *   registry.help('file')              // group help
 *
 * Each command group is an object:
 *   {
 *     name: 'file',
 *     description: 'File operations',
 *     commands: {
 *       save: { fn, description, alias, args },
 *       open: { fn, description, alias, args },
 *     }
 *   }
 *
 * Pure module, no DOM, ES module, Node.js compatible.
 */

// =============================================================================
// COMMAND REGISTRY
// =============================================================================

export function createCommandRegistry() {
  const groups = {};       // { groupName: { name, description, commands: {} } }
  const aliases = {};      // { shortName: 'group.command' }
  let fallback = null;     // fn(text) — called when no match found

  return {
    /**
     * Register a command group.
     * @param {object} group — { name, description, commands: { cmd: {fn, description, alias?, args?} } }
     */
    register(group) {
      if (!group.name) throw new Error('Command group must have a name');
      groups[group.name] = group;
      // Register aliases
      for (const [cmd, def] of Object.entries(group.commands || {})) {
        if (def.alias) {
          const aliasList = Array.isArray(def.alias) ? def.alias : [def.alias];
          for (const a of aliasList) {
            aliases[a.toLowerCase()] = `${group.name}.${cmd}`;
          }
        }
        // Auto-alias: command name itself is a short form
        if (!aliases[cmd.toLowerCase()]) {
          aliases[cmd.toLowerCase()] = `${group.name}.${cmd}`;
        }
      }
    },

    /**
     * Set fallback handler for unmatched commands.
     * @param {function} fn — (text) => { success, message }
     */
    setFallback(fn) {
      fallback = fn;
    },

    /**
     * Execute a command string.
     * Supports: "file.save", "file save", "save", "save-as 'name'"
     * @param {string} text — raw command input
     * @returns {{ success: boolean, message: string }}
     */
    execute(text) {
      const raw = text.trim();
      if (!raw) return { success: false, message: 'Empty command' };

      // Try dot-notation: "file.save args"
      const dotMatch = raw.match(/^(\w+)\.(\S+)\s*(.*)?$/);
      if (dotMatch) {
        const [, groupName, cmdName, args] = dotMatch;
        return this._dispatch(groupName.toLowerCase(), cmdName.toLowerCase(), (args || '').trim(), raw);
      }

      // Try space-notation: "file save args"
      const spaceMatch = raw.match(/^(\w+)\s+(\S+)\s*(.*)?$/);
      if (spaceMatch) {
        const [, first, second, rest] = spaceMatch;
        // Check if first word is a group name
        if (groups[first.toLowerCase()]) {
          return this._dispatch(first.toLowerCase(), second.toLowerCase(), (rest || '').trim(), raw);
        }
      }

      // Try alias: "save", "undo", "new"
      const firstWord = raw.split(/\s+/)[0].toLowerCase();
      const aliasTarget = aliases[firstWord];
      if (aliasTarget) {
        const [groupName, cmdName] = aliasTarget.split('.');
        const args = raw.slice(firstWord.length).trim();
        return this._dispatch(groupName, cmdName, args, raw);
      }

      // Try group-only (no action): "file" → show help
      if (groups[firstWord]) {
        return { success: true, message: this.help(firstWord) };
      }

      // Fallback
      if (fallback) return fallback(raw);
      return { success: false, message: `Unknown command: ${raw}` };
    },

    /** @private */
    _dispatch(groupName, cmdName, args, raw) {
      const group = groups[groupName];
      if (!group) return { success: false, message: `Unknown group: ${groupName}` };
      const cmd = group.commands[cmdName];
      if (!cmd) {
        // Check if cmdName+args is a combined thing (e.g. "save-as")
        const combined = `${cmdName}-${args.split(/\s+/)[0]}`.toLowerCase();
        const combinedCmd = group.commands[combined];
        if (combinedCmd) {
          const remainingArgs = args.slice(args.split(/\s+/)[0].length).trim();
          return combinedCmd.fn(remainingArgs, raw);
        }
        return { success: false, message: `Unknown command: ${groupName}.${cmdName}. Type "help ${groupName}" for options.` };
      }
      return cmd.fn(args, raw);
    },

    /**
     * Get completion suggestions.
     * @param {string} partial — what user typed so far
     * @returns {string[]} list of completions
     */
    complete(partial) {
      const lower = partial.toLowerCase();

      // Complete group names: "fi" → ["file."]
      if (!lower.includes('.') && !lower.includes(' ')) {
        return Object.keys(groups)
          .filter(g => g.startsWith(lower) && g !== lower)
          .map(g => g + '.');
      }

      // Complete after dot: "file.s" → ["file.save", "file.save-as"]
      const dotIdx = lower.indexOf('.');
      if (dotIdx > 0) {
        const groupName = lower.slice(0, dotIdx);
        const sub = lower.slice(dotIdx + 1);
        const group = groups[groupName];
        if (!group) return [];
        return Object.keys(group.commands)
          .filter(c => c.startsWith(sub) && c !== sub)
          .map(c => `${groupName}.${c}`);
      }

      return [];
    },

    /**
     * Get help text for a group (or all groups).
     * @param {string} [groupName] — specific group, or omit for overview
     * @returns {string} formatted help text
     */
    help(groupName) {
      if (groupName && groups[groupName]) {
        const group = groups[groupName];
        const lines = [`── ${group.name}: ${group.description || ''} ──`];
        for (const [cmd, def] of Object.entries(group.commands)) {
          const aliasStr = def.alias ? ` (${Array.isArray(def.alias) ? def.alias.join(', ') : def.alias})` : '';
          const argsStr = def.args ? ` ${def.args}` : '';
          lines.push(`  ${group.name}.${cmd}${argsStr} — ${def.description || ''}${aliasStr}`);
        }
        return lines.join('\n');
      }

      // Overview
      const lines = ['╭─ Command Groups ─────────────────────────────╮'];
      for (const [name, group] of Object.entries(groups)) {
        const cmds = Object.keys(group.commands).join(', ');
        lines.push(`│ ${name.padEnd(8)} ${(group.description || '').padEnd(20)} ${cmds}`);
      }
      lines.push('├───────────────────────────────────────────────┤');
      lines.push('│ Short form works: save, undo, open "name"     │');
      lines.push('│ Dot form works:   file.save, edit.undo        │');
      lines.push('│ Tab completes:    file.⇥ → file.save          │');
      lines.push('│ help GROUP:       help file → show file.*     │');
      lines.push('╰───────────────────────────────────────────────╯');
      return lines.join('\n');
    },

    /**
     * List all registered groups.
     * @returns {string[]}
     */
    listGroups() {
      return Object.keys(groups);
    },

    /**
     * List commands in a group.
     * @param {string} groupName
     * @returns {Array<{name, description, alias, args}>}
     */
    listCommands(groupName) {
      const group = groups[groupName];
      if (!group) return [];
      return Object.entries(group.commands).map(([name, def]) => ({
        name: `${groupName}.${name}`,
        description: def.description || '',
        alias: def.alias || null,
        args: def.args || null,
      }));
    },

    /**
     * Get all aliases (for display).
     * @returns {object} { alias: 'group.command' }
     */
    getAliases() {
      return { ...aliases };
    },
  };
}

// =============================================================================
// BUILT-IN COMMAND GROUP FACTORIES
// =============================================================================

/**
 * Create the 'file' command group.
 * @param {object} handlers — { onNew, onOpen, onSave, onSaveAs, onDownload, onRecent }
 */
export function createFileCommands(handlers) {
  return {
    name: 'file',
    description: 'Project files',
    commands: {
      'new': {
        fn: () => { handlers.onNew(); return { success: true, message: 'New project created' }; },
        description: 'Create empty project',
        alias: 'new',
        args: null,
      },
      'open': {
        fn: (args) => { handlers.onOpen(unquote(args)); return { success: true, message: args ? `Opened "${unquote(args)}"` : 'Open dialog' }; },
        description: 'Open project',
        alias: 'open',
        args: '[name]',
      },
      'save': {
        fn: () => { handlers.onSave(); return { success: true, message: 'Saved' }; },
        description: 'Save project',
        alias: 'save',
        args: null,
      },
      'save-as': {
        fn: (args) => { handlers.onSaveAs(unquote(args)); return { success: true, message: `Saved as "${unquote(args)}"` }; },
        description: 'Save with new name',
        alias: ['save-as', 'saveas'],
        args: '"name"',
      },
      'download': {
        fn: (args) => { handlers.onDownload(args.toLowerCase()); return { success: true, message: `Downloaded ${args}` }; },
        description: 'Download file',
        alias: 'download',
        args: 'circuit|board',
      },
      'recent': {
        fn: () => { const list = handlers.onRecent(); return { success: true, message: list.length ? list.join('\n') : 'No recent projects' }; },
        description: 'Show recent projects',
        alias: 'recent',
        args: null,
      },
    },
  };
}

/**
 * Create the 'edit' command group.
 * @param {object} handlers — { onUndo, onRedo, onSelect, onDeselect }
 */
export function createEditCommands(handlers) {
  return {
    name: 'edit',
    description: 'Edit operations',
    commands: {
      'undo': {
        fn: () => { handlers.onUndo(); return { success: true, message: 'Undo' }; },
        description: 'Undo last action',
        alias: 'undo',
      },
      'redo': {
        fn: () => { handlers.onRedo(); return { success: true, message: 'Redo' }; },
        description: 'Redo',
        alias: 'redo',
      },
      'select': {
        fn: (args) => { handlers.onSelect(args); return { success: true, message: `Selected ${args}` }; },
        description: 'Select device',
        args: 'REF',
      },
      'deselect': {
        fn: () => { handlers.onDeselect(); return { success: true, message: 'Deselected' }; },
        description: 'Clear selection',
        alias: 'deselect',
      },
    },
  };
}

/**
 * Create the 'view' command group.
 * @param {object} handlers — { onCollapse, onExpand, onZoom, onPan }
 */
export function createViewCommands(handlers) {
  return {
    name: 'view',
    description: 'Viewport control',
    commands: {
      'collapse': {
        fn: () => { handlers.onCollapse(); return { success: true, message: 'Panel collapsed' }; },
        description: 'Hide right panel',
        alias: 'collapse',
      },
      'expand': {
        fn: () => { handlers.onExpand(); return { success: true, message: 'Panel expanded' }; },
        description: 'Show right panel',
        alias: 'expand',
      },
      'zoom': {
        fn: (args) => { handlers.onZoom(args); return { success: true, message: `Zoom: ${args}` }; },
        description: 'Set zoom level',
        args: 'N%|fit',
      },
      'pan': {
        fn: (args) => { handlers.onPan(args); return { success: true, message: `Pan: ${args}` }; },
        description: 'Pan viewport',
        args: '(x, y)',
      },
    },
  };
}

/**
 * Create the 'tool' command group.
 * @param {object} handlers — { onActivate, listTools }
 */
export function createToolCommands(handlers) {
  return {
    name: 'tool',
    description: 'Tool selection',
    commands: {
      'select': { fn: () => { handlers.onActivate('select'); return { success: true, message: 'Tool: Select' }; }, description: 'Select tool (V)' },
      'connect': { fn: () => { handlers.onActivate('connect'); return { success: true, message: 'Tool: Connect' }; }, description: 'Connect tool (W)' },
      'eraser': { fn: () => { handlers.onActivate('eraser'); return { success: true, message: 'Tool: Eraser' }; }, description: 'Eraser tool (E)' },
      'tray': { fn: () => { handlers.onActivate('tray'); return { success: true, message: 'Tool: Tray' }; }, description: 'Project Tray (L)' },
      'guide': { fn: () => { handlers.onActivate('guide'); return { success: true, message: 'Tool: Guide' }; }, description: 'Guide tool (G)' },
      'label': { fn: () => { handlers.onActivate('label'); return { success: true, message: 'Tool: Label' }; }, description: 'Label tool (T)' },
      'inspect': { fn: () => { handlers.onActivate('inspect'); return { success: true, message: 'Tool: Inspect' }; }, description: 'Inspect tool (I)' },
    },
  };
}

/**
 * Create the 'page' command group.
 * @param {object} handlers — { onNew, onSwitch, onDelete }
 */
export function createPageCommands(handlers) {
  return {
    name: 'page',
    description: 'Page management',
    commands: {
      'new': {
        fn: (args) => { handlers.onNew(unquote(args)); return { success: true, message: `Page: ${unquote(args)}` }; },
        description: 'Create new page',
        args: '"name"',
      },
      'switch': {
        fn: (args) => { handlers.onSwitch(unquote(args)); return { success: true, message: `Page: ${unquote(args)}` }; },
        description: 'Switch to page',
        args: '"name"',
      },
      'delete': {
        fn: (args) => { handlers.onDelete(unquote(args)); return { success: true, message: `Deleted page: ${unquote(args)}` }; },
        description: 'Delete page',
        args: '"name"',
      },
    },
  };
}

/**
 * Create the 'board' command group (pass-through to engine).
 * @param {object} handlers — { runEngine }
 */
export function createBoardCommands(handlers) {
  return {
    name: 'board',
    description: 'Visual layout',
    commands: {
      'place': { fn: (a, raw) => handlers.runEngine(raw.replace(/^board[\s.]/, '')), description: 'Place device', args: 'REF, PART at (X,Y) rotate A' },
      'move': { fn: (a, raw) => handlers.runEngine(raw.replace(/^board[\s.]/, '')), description: 'Move device', args: 'REF to (X,Y)' },
      'rotate': { fn: (a, raw) => handlers.runEngine(raw.replace(/^board[\s.]/, '')), description: 'Rotate device', args: 'REF ANGLE' },
      'delete': { fn: (a, raw) => handlers.runEngine(raw.replace(/^board[\s.]/, '')), description: 'Delete device', args: 'REF' },
      'label': { fn: (a, raw) => handlers.runEngine(raw.replace(/^board[\s.]/, '')), description: 'Add label', args: '"text" at (X,Y)' },
      'route': { fn: (a, raw) => handlers.runEngine(raw.replace(/^board[\s.]/, '')), description: 'Add route', args: 'FROM -> TO via (X,Y)...' },
    },
  };
}

/**
 * Create the 'circuit' command group (pass-through to engine).
 * @param {object} handlers — { runEngine }
 */
export function createCircuitCommands(handlers) {
  return {
    name: 'circuit',
    description: 'Electrical net',
    commands: {
      'device': { fn: (a, raw) => handlers.runEngine('place ' + a), description: 'Add device', args: 'REF, PART at (X,Y)' },
      'connect': { fn: (a, raw) => handlers.runEngine('connect ' + a), description: 'Connect pins', args: 'FROM -> TO' },
      'disconnect': { fn: (a, raw) => handlers.runEngine('disconnect ' + a), description: 'Disconnect pins', args: 'FROM -> TO' },
    },
  };
}

// =============================================================================
// HELPERS
// =============================================================================

function unquote(s) {
  if (!s) return '';
  return s.replace(/^["']|["']$/g, '').trim();
}
