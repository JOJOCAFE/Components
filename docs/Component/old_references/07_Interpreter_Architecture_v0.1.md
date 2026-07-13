# 07 Interpreter Architecture v0.1

**Status:** Frozen for Prototype

## Purpose

This document defines the runtime architecture of Components Platform.

The interpreter is the authoritative execution engine.

Board is only a client.

------------------------------------------------------------------------

# Overall Pipeline

``` text
Component Source
        ↓
Lexer
        ↓
Parser
        ↓
AST
        ↓
Resolver
        ↓
Resolved Component Model
        ↓
Topology Builder
        ↓
Signal Graph
        ↓
Validator
        ↓
Simulation Engine
        ↓
Trace Store
        ↓
Result
```

------------------------------------------------------------------------

# Responsibilities

## Lexer

Produces tokens.

Does not understand circuits.

------------------------------------------------------------------------

## Parser

Builds AST.

Reports syntax errors only.

Does not resolve Devices.

------------------------------------------------------------------------

## Resolver

Loads Device Libraries.

Expands:

-   Device instances
-   collections
-   aliases
-   logical ports
-   physical pins

Produces the canonical Component Model.

------------------------------------------------------------------------

## Topology Builder

Creates electrical connectivity.

Expands:

-   1→1
-   1→N
-   N→1
-   N→N

Produces Net Graph.

No electrical validation occurs here.

------------------------------------------------------------------------

## Validator

Runs independent validation passes.

Suggested order:

1.  topology
2.  device
3.  signal
4.  timing
5.  simulation readiness
6.  education

Produces diagnostics.

------------------------------------------------------------------------

## Signal Graph

Represents executable connectivity.

Nodes:

-   Device Ports
-   Nets
-   Signals

Edges:

-   Connectivity
-   Driver relationships

Signal values:

    0
    1
    X
    Z

------------------------------------------------------------------------

## Simulation Engine

Event-driven.

Supports:

-   combinational propagation
-   sequential Devices
-   propagation delay
-   clock
-   tick
-   event scheduling
-   memory
-   probes

Simulation owns runtime state.

------------------------------------------------------------------------

## Event Queue

Each event contains:

``` text
coordinate
device
endpoint
old value
new value
cause
```

Coordinates may be:

-   tick
-   time
-   event

------------------------------------------------------------------------

## Trace Store

Stores transition history.

Probe records transitions.

Board renders traces.

Board never reconstructs history.

------------------------------------------------------------------------

# Runtime Objects

Persistent:

-   Component
-   Device
-   Net
-   Signal

Runtime:

-   Device State
-   Event Queue
-   Trace Store
-   Diagnostics

------------------------------------------------------------------------

# Operations

Interpreter accepts Operations.

Examples:

-   load
-   connect
-   validate
-   inspect
-   inject
-   probe
-   watch
-   run
-   step
-   pause
-   reset
-   export

Operations are independent from Board.

------------------------------------------------------------------------

# Board Relationship

Board sends:

-   Component
-   Operation

Interpreter returns:

-   Result
-   Diagnostics
-   State
-   Trace

Board never owns execution state.

------------------------------------------------------------------------

# Native Simulation

Components executes Components directly.

External HDL tools are optional compatibility targets.

------------------------------------------------------------------------

# Time Model

Simulation coordinates:

``` text
tick
time
event
```

Tick is deterministic.

Time supports physical delay.

Events support asynchronous execution.

------------------------------------------------------------------------

# Inject

Inject modifies runtime state.

Examples:

-   ROM image
-   noise
-   glitch
-   delay
-   fault
-   matrix stimulus

Inject never changes topology.

------------------------------------------------------------------------

# Monitor Program

Monitor belongs to Component.

Interpreter executes it.

Board displays it through TERMINAL resources.

------------------------------------------------------------------------

# Resource Interaction

Interactive Resources emit Operations.

Interpreter executes Operations.

Resources receive updated state.

------------------------------------------------------------------------

# JSON Contract

Interpreter communicates through canonical JSON object model.

Text and JSON describe the same object model.

------------------------------------------------------------------------

# Design Rules

1.  Parser never validates signals.
2.  Resolver never simulates.
3.  Validator never mutates topology.
4.  Board never mutates simulation state.
5.  Interpreter is authoritative.
6.  Simulation is event-driven.
7.  Grow interpreters and libraries, not language syntax.

------------------------------------------------------------------------

# Definition of Success

Prototype succeeds when:

1.  Component loads.
2.  Device Libraries resolve.
3.  Resource Libraries resolve.
4.  Topology builds.
5.  Validation reports diagnostics.
6.  Clock steps.
7.  Signals propagate.
8.  Probe records traces.
9.  Board updates live.
10. JSON operations execute deterministically.
