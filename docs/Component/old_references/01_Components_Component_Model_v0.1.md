# Components Component Model v0.1 (Parser & Interpreter Foundation)

**Status:** Frozen for Prototype v0.1

## Goals

-   Human-readable before machine-readable.
-   Low entry barrier, high learning ceiling.
-   One language from beginner to professional.
-   Component describes the machine.
-   Board describes presentation and interaction.
-   Components Platform is the authoritative parser, validator,
    interpreter, and simulator.

------------------------------------------------------------------------

# Top-level objects

``` text
component:component
component:board
component:operation
component:schema
```

## Responsibilities

-   **component** -- circuit topology, devices, monitor program,
    firmware, probes.
-   **board** -- layout, presentation, panels, interaction, emulator UI.
-   **operation** -- commands, requests, simulation, inject, probe,
    validate.
-   **schema** -- contracts and object definitions.

------------------------------------------------------------------------

# Libraries

## Device Library

Example:

``` text
use standard.lib;
```

Owns:

-   Device types
-   Ports
-   Physical pins
-   Simulation
-   Timing
-   Electrical behaviour

## Resource Library

Example:

``` text
use standard.resource;
```

Owns:

-   Symbols
-   DIP/Breadboard views
-   Icons
-   Widgets
-   Waveform renderer
-   Terminal renderer
-   Themes

Device Library defines **meaning**.

Resource Library defines **presentation**.

------------------------------------------------------------------------

# Language Keywords

    use
    component
    device
    connect
    group
    module
    net
    bus
    probe
    watch
    inject
    is
    as

Reserved for future:

    :

------------------------------------------------------------------------

# Punctuation

    .      logical member
    .@     physical pin
    []     collection
    {}     block
    ()     parameters
    ->     connection
    ..     range
    ,      list
    ;      statement end

    //     single line comment
    /* */  multi-line comment

------------------------------------------------------------------------

# Device

``` text
device Counter is 74HC161;

device LED[4] is LED;
```

`[4]` in declaration means **count**.

------------------------------------------------------------------------

# References

Logical:

``` text
Counter.CLK
Counter.Q0
RAM./CS
LED.A
R.1
```

Physical:

``` text
Counter.@2
RAM.@20
```

------------------------------------------------------------------------

# Collections

Selection:

``` text
LED[0..3]
Counter.Q[0..3]
```

User-defined collection:

``` text
Counter[Q0,Q1,Q2,Q3]
    as Counter.Q[0..3];
```

------------------------------------------------------------------------

# Connectivity

    connect source -> target;

Rules:

-   1 → 1
-   1 → N (fan-out)
-   N → 1 (join)
-   N → N (pairwise)
-   N → M (M≠N) ⇒ error

Topology first.

Validation later.

------------------------------------------------------------------------

# Validation Pipeline

    Parser
    ↓
    Resolver
    ↓
    Topology
    ↓
    Device
    ↓
    Signal
    ↓
    Timing
    ↓
    Simulation
    ↓
    Education

Parser never performs electrical validation.

------------------------------------------------------------------------

# Time Model

First-class concepts:

    tick
    time
    event

Example:

``` text
connect tick(120) -> Reset.IN;
```

------------------------------------------------------------------------

# Inject

Single keyword for external state/stimulus.

Examples:

``` text
inject noise into Clock.OUT;

inject boot.bin into ROM;

inject rom_matrix into Decoder;
```

Structured forms are represented canonically as JSON operations.

------------------------------------------------------------------------

# Probe

    probe Counter.Q[0..3];
    watch Counter.Q[0..3];

Probe records history.

Watch shows live state.

------------------------------------------------------------------------

# Native Simulation

    Component
    ↓
    Topology
    ↓
    Signal Graph
    ↓
    Event Simulator
    ↓
    Trace
    ↓
    Board

No Verilog required for normal execution.

------------------------------------------------------------------------

# Board

Board is the presentation and interaction layer.

It contains:

-   Component view
-   Board view
-   Terminal
-   Timeline
-   Waveform

Board sends:

-   Component
-   Operations

Components returns:

-   State
-   Diagnostics
-   Trace
-   Results

------------------------------------------------------------------------

# JSON Philosophy

Component notation and JSON represent the same canonical object model.

JSON must remain readable by humans.

------------------------------------------------------------------------

# Core Principles

1.  Read before learn.
2.  Human first.
3.  Low barrier.
4.  High ceiling.
5.  Grow libraries, not the language.
6.  Device Libraries own behaviour.
7.  Resource Libraries own presentation.
8.  Component owns machine meaning.
9.  Board owns presentation.
10. Components Platform owns execution.
