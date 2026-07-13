# Component Desktop Platform Plan

Status: foundation decision for the future desktop client.  This document
adds no updater, plugin loader, or Board editor yet.  It makes their safety
boundaries explicit before a client grows around the Component language.

## Goal

Start on notebooks and desktop computers with a client that feels quick on
ordinary student hardware.  Tablet and browser/PWA support can follow from
the same JSON contracts; they must not force the first desktop client to be
large or slow.

The recommended first shape is:

```text
Tauri desktop shell (Rust)
  -> small TypeScript/Preact screens (React-compatible, no UI framework)
  -> versioned Components JSON requests/results
  -> platform service adapter -> existing Python Components service on desktop
  -> readable .component source and Component libraries
```

Rust owns the small desktop shell, window lifecycle, secure updater boundary,
and local-process lifecycle. Preact/TypeScript owns accessible editor, Board,
and student explanation screens, with plain CSS and SVG/Canvas rather than a
large component/design system. Python remains the desktop behavior, resolver,
and runtime backend until a measured need justifies changing it.

No screen may make UI state, a plugin, or an updater the electrical source
of truth.  The readable Component source and versioned JSON contracts remain
the boundary shared by the text IDE, CLI/API, visual Board, and AI tools.

## Non-negotiable platform and speed requirements

Windows, Linux, and iOS are supported product targets from the beginning.
Android/iPad-specific refinement is optional for the first release, but the
same pointer/touch workspace must not block either later. Tauri v2 has targets
for Windows, Linux, and iOS, so it is a suitable thin shell; each platform
still needs its own tested packaging and service adapter.

The Python process is the local adapter on Windows/Linux. iOS must use the
same versioned JSON service boundary, but cannot be promised an unchanged
desktop Python-sidecar implementation. Before an iOS release, provide and test
an iOS-compatible runtime adapter (native/Rust or an approved service mode)
that gives the same resolver/runtime results. No platform is allowed to have a
different Component language or hidden circuit model.

The client has these hard performance rules:

| Need | Product rule |
| --- | --- |
| Fast launch | Open the last local Component into editable Text/Drawing without network or plugin loading. Measure cold start on reference student hardware. |
| Fast interaction | Selection, pan, zoom, drag, and local visual feedback stay immediate; parse/resolve work is debounced/off the paint path. |
| Small install and memory | No Electron, large UI kit, embedded browser engine, mandatory 3D engine, or eagerly-loaded plugin. Use OS webview, small Preact bundle, and lazy features. |
| Fast Drawing | Use SVG/Canvas for the first Board; virtualize large lists and redraw only changed objects. |
| Offline first | Text editing, autosave, resolver diagnostics, and bounded runtime work without a network. Updates, plugin discovery, and optional integrations are never startup dependencies. |
| Measured budget | Set and continuously test launch, interaction, resolve, memory, and package-size budgets before a public release; regressions block release rather than becoming accepted slowness. |

“Fast” must be measured on modest student hardware, not only a developer
machine. The first implementation records baseline timing before promises are
turned into fixed release numbers.

## Autosave and recovery

Autosave is part of the editing model, not a Save button replacement.

- Keep an in-memory edit journal and write a local recovery draft after a
  short idle period, before a window/app close, and before an update restart.
- Write atomically: retain the last saved source and last valid resolved view
  until a complete replacement is durable.
- Preserve incomplete or invalid Text as a recoverable draft; never discard a
  student's half-written idea just because it cannot resolve yet.
- Restore the workspace layout, active file, cursor/selection, unsent Terminal
  input, and last valid Drawing snapshot after a crash/restart.
- Tell the learner plainly whether a file is saved, a local draft is recovered,
  or a Component needs fixing. Cloud sync is optional and must not replace the
  local recovery path.

## First desktop slice: one three-pane workspace

The first client is deliberately small, but it is a real authoring workspace:

1. **Drawing** — parts and wires which can propose checked source edits;
2. **Component text** — the readable `.component` source; and
3. **Terminal** — real-time bounded source-edit and runtime commands.

All three call the same local Python service to parse, resolve, validate, and run declared tests. A Drawing electrical edit must return an explicit source patch, then redraw from resolved JSON. A Terminal runtime request returns a trace and never changes source. See [`COMPONENT_THREE_PANE_WORKSPACE.md`](COMPONENT_THREE_PANE_WORKSPACE.md) for the synchronization and command boundary.

The default layout puts Drawing on the left, readable Text upper-right, and a
shallow Terminal lower-right. Panes can be collapsed, resized, detached, or
made full-screen. The interaction is pointer/stylus-first with a tiny
contextual tool row, not a permanent menu/ribbon interface.

Multi-window support may be added after this slice.  One local session owns
the active source and runtime request; other windows receive immutable
snapshots.  An unsaved source edit is never silently replaced by another
window, an update, or a plugin.

## Auto-update contract

Auto-update means *the application can safely offer a verified replacement*.
It never means changing a student's work without a clear choice.

| Rule | Required behavior |
| --- | --- |
| Signed release | The shell accepts only a release manifest and package verified by the trusted updater key. |
| Compatibility gate | A release declares its desktop, Python-service, JSON schema, and plugin-API compatibility. The client refuses an incompatible combination with a plain explanation. |
| Student control | Downloading may be automatic only after opt-in. Applying an update always says “Restart to update”; it waits for a safe point and protects unsaved work. |
| Safe point | Never restart while a test/runtime request is active. Save or recover editor drafts before replacing the app. |
| Channels | `stable` is default. `beta` and `development` are explicit opt-in channels, visibly labelled as such. |
| Recovery | Keep the prior known-good application until the new version starts successfully. A failed launch offers rollback and preserves Component files and local settings. |
| Clear message | Show version, short student-readable changes, source/release date, and whether a restart is needed. |

Updater implementation is deferred until the first desktop slice runs.  Its
release format, signing key rotation procedure, and rollback test must be
checked before any public update endpoint is enabled.

## Plugin contract

Plugins add optional views or integrations.  They cannot quietly become a
second Component language, a new circuit simulator, or a way around library
truth.

### Plugin kinds

| Kind | Examples | Electrical authority |
| --- | --- | --- |
| View plugin | trace timeline, datasheet reader, text/2D/3D Resource viewer | none; consumes immutable JSON snapshots |
| Integration plugin | export, import, classroom/LMS adapter | no direct model mutation; submits versioned requests through the public API |
| Operation plugin (later) | approved physical-lab bridge | only explicit bounded Operation requests, consent, trace, and policy checks |

The first desktop slice has **no third-party plugin execution**.  It only
reserves these contracts so a later host can be added without breaking the
core client.

### Required manifest

Every plugin will have a signed, versioned manifest containing at least:

```json
{
  "schema": "components.desktop-plugin@1",
  "id": "org.example.trace-view",
  "version": "1.0.0",
  "engine_compatibility": {"desktop": "^1", "plugin_api": "^1"},
  "kind": "view",
  "capabilities": ["read:resolved-component", "read:runtime-trace"],
  "entrypoints": {"panel": "dist/panel.js"},
  "integrity": {"algorithm": "sha256", "digest": "..."}
}
```

The public plugin API is typed, versioned JSON.  A plugin receives only the
snapshots and capabilities listed in its manifest.  It receives no direct
access to Device definitions, Python objects, source files, arbitrary shell
commands, or network/filesystem access by default.

The host must provide:

- explicit install/remove/enable controls and a visible plugin publisher;
- compatibility and integrity verification before loading;
- one-click disable plus a **safe mode** that loads no third-party plugin;
- lazy loading so unneeded 3D or integration code does not slow the editor;
- a traceable permission prompt before an operation or external integration;
- a strict rule that plugin data is presentation/interchange data, never a
  hidden electrical mutation.

Text, diagram, and 3D Resource viewers will rely on the future Resource
Definition contract.  A missing visual or 3D asset falls back to readable
text and real pin facts; it never blocks simulation or changes a Component.

## Decisions deliberately postponed

- Exact Tauri/React package versions and build tooling.
- The release host, trusted signing-key custody, and key-rotation ceremony.
- Whether community plugins are supported, or plugins initially come only
  from a Components-maintained registry.
- Sandboxing mechanism for third-party UI code.
- Tablet-specific interaction and PWA packaging.

These need an implemented first desktop slice and a Resource Definition
contract to test against.  They are not reasons to delay the text IDE, CLI,
or Component runtime.

## Acceptance before enabling either feature

1. A fresh desktop client works with plugins disabled and no network.
2. A deliberately incompatible backend/schema/plugin is rejected with a
   clear diagnostic and no partial load.
3. A tampered update and a tampered plugin are rejected.
4. Restart/update preserves an unsaved draft through recovery and never
   interrupts an active runtime request.
5. Safe mode opens a Component and its readable diagnostics even if every
   optional plugin fails.
