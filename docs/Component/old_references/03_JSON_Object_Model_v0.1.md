# 03 JSON Object Model v0.1

## Purpose

This document defines the canonical machine-readable object model used
by Components Platform.

All front-ends (Board, CLI, AI, REST, Python, MCP) communicate through
this model.

Textual Component notation and JSON represent the same underlying object
model.

------------------------------------------------------------------------

# Principles

-   Human-readable before machine-readable.
-   Stable canonical representation.
-   Explicit field names.
-   No positional arguments.
-   Readable without opening the schema.

------------------------------------------------------------------------

# Root Objects

Every payload contains exactly one top-level object.

``` json
{
  "component:component": {}
}
```

Supported root objects:

-   component:component
-   component:board
-   component:operation
-   component:schema

------------------------------------------------------------------------

# Component

``` json
{
  "component:component": {
    "name": "CounterDemo",
    "libraries": [
      "standard.lib"
    ],
    "devices": [
      {
        "name": "Counter",
        "type": "74HC161"
      },
      {
        "name": "LED",
        "count": 4,
        "type": "LED"
      }
    ],
    "connections": [
      {
        "from": "Counter.Q[0..3]",
        "to": "LED[0..3].A"
      },
      {
        "from": "LED[0..3].K",
        "to": "GND"
      }
    ]
  }
}
```

------------------------------------------------------------------------

# Board

``` json
{
  "component:board": {
    "name": "MainBoard",
    "uses": "CounterDemo",
    "resources": [
      "standard.resource"
    ],
    "panels": [
      "component",
      "board",
      "terminal"
    ],
    "placements": [
      {
        "target": "Counter",
        "x": 320,
        "y": 180
      }
    ]
  }
}
```

------------------------------------------------------------------------

# Operation

``` json
{
  "component:operation": {
    "run": {
      "during": {
        "tick": "0..200"
      }
    }
  }
}
```

Example inspect:

``` json
{
  "component:operation": {
    "inspect": {
      "target": "Counter.@2"
    }
  }
}
```

Example connect:

``` json
{
  "component:operation": {
    "connect": {
      "from": "Counter.Q[0..3]",
      "to": "LED[0..3].A"
    }
  }
}
```

Example inject:

``` json
{
  "component:operation": {
    "inject": {
      "noise": {
        "into": "Clock.OUT",
        "during": {
          "tick": "50..100"
        }
      }
    }
  }
}
```

Example ROM programming:

``` json
{
  "component:operation": {
    "inject": {
      "rom": {
        "into": "ROM",
        "from_file": "boot.bin"
      }
    }
  }
}
```

Example probe:

``` json
{
  "component:operation": {
    "probe": {
      "target": "Counter.Q[0..3]"
    }
  }
}
```

------------------------------------------------------------------------

# Result

``` json
{
  "result": {
    "status": "ok",
    "revision": 12,
    "diagnostics": [],
    "signals": [],
    "traces": []
  }
}
```

------------------------------------------------------------------------

# Diagnostics

``` json
{
  "severity": "warning",
  "code": "floating_input",
  "target": "Counter.ENP",
  "message": "Counter.ENP is not connected."
}
```

Severity:

-   info
-   warning
-   error
-   fatal

------------------------------------------------------------------------

# Trace

``` json
{
  "target": "Counter.Q[0..3]",
  "coordinate": "tick",
  "transitions": [
    {
      "at": 0,
      "value": "0000"
    },
    {
      "at": 1,
      "value": "0001"
    }
  ]
}
```

------------------------------------------------------------------------

# Time Coordinates

Supported:

-   tick
-   time
-   event

------------------------------------------------------------------------

# Canonical Rules

-   Text notation and JSON must describe the same object model.
-   JSON field names should read like English.
-   Do not abbreviate names unnecessarily.
-   Grow operations, not the protocol.
-   Grow libraries, not the language.

------------------------------------------------------------------------

# Responsibilities

Board sends:

-   Component
-   Operations

Components returns:

-   Result
-   Diagnostics
-   State
-   Trace

JSON is the canonical exchange protocol for Components Platform.
