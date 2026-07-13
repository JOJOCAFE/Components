# Components Board Visual Design v0.1 (Frozen)

## Purpose

Board is the visual presentation and interaction client for Components
Platform.

Board does not own circuit meaning or simulation logic.

It owns:

-   Presentation
-   Interaction
-   Layout
-   Workspace

Components Platform owns:

-   Parsing
-   Device resolution
-   Validation
-   Simulation
-   State

------------------------------------------------------------------------

# Main Layout

    +--------------------------------------------------------------+
    | Project                                Run  Pause Step Reset |
    +----------------------+---------------------------------------+
    |                      |                                       |
    | Component            | Board                                |
    |                      |                                       |
    |                      |                                       |
    +----------------------+---------------------------------------+
    | Terminal / Timeline / Waveform                              |
    +--------------------------------------------------------------+

Three primary panels:

1.  Component
2.  Board
3.  Terminal

Timeline and Waveform are views inside the bottom panel.

------------------------------------------------------------------------

# Component Panel

Purpose:

Describe the machine.

Contains:

-   Component source
-   Syntax highlight
-   Errors
-   Jump to Board

Never contains presentation information.

------------------------------------------------------------------------

# Board Panel

Purpose:

Present and interact with the machine.

Contains:

-   Device visuals
-   Connections
-   Layout
-   Signal values
-   Pin numbers
-   Port names

Supports:

-   Select
-   Move
-   Connect
-   Pan
-   Zoom
-   Inspect
-   Probe

Board interactions generate Operations.

Board never edits simulation state directly.

------------------------------------------------------------------------

# Terminal Panel

Two logical modes:

Platform Console

-   validate
-   inspect
-   export
-   probe
-   inject

Machine Console

Connected to a TERMINAL Device inside the Component.

Monitor programs belong to the Component.

Board only renders the terminal.

------------------------------------------------------------------------

# Timeline

Timeline is first-class.

Supports:

-   tick
-   time
-   event

Controls:

-   Run
-   Pause
-   Step
-   Reset
-   Speed

------------------------------------------------------------------------

# Waveform

Generated from probe traces.

Supports:

-   zoom
-   pan
-   cursor
-   bus expand/collapse
-   X/Z display

------------------------------------------------------------------------

# Resource Libraries

Board uses Resource Libraries.

Example:

    use standard.resource;
    use breadboard.resource;

Resources define:

-   symbols
-   breadboard views
-   DIP packages
-   widgets
-   icons
-   themes

Resources never redefine Device meaning.

------------------------------------------------------------------------

# Device Rendering

Every Device may have multiple views:

-   compact
-   schematic
-   DIP
-   breadboard
-   educational
-   debug

Switching views never changes topology.

------------------------------------------------------------------------

# Board Workflow

User ↓ Board interaction ↓ Operation ↓ Components Platform ↓ State /
Diagnostics / Trace ↓ Board rendering

------------------------------------------------------------------------

# Board Principles

-   Board is a Workbench, not an editor.
-   Board presents the machine.
-   Board is the user-facing circuit emulator.
-   Component owns machine meaning.
-   Resource Libraries own appearance.
-   Components Platform owns execution.

------------------------------------------------------------------------

# Design Goals

-   Tablet-first
-   Desktop-friendly
-   Minimal UI
-   Readable before learnable
-   Visual synchronized with Component source
-   Timeline always available
-   Professional capability with low entry barrier
