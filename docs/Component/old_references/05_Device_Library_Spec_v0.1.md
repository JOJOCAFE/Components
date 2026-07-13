# 05 Device Library Specification v0.1

**Status:** Frozen for Prototype v0.1\
**Primary library:** `standard.lib`

## 1. Purpose

A Device Library defines the reusable Devices that may be instantiated
inside a `component:component`.

The Device Library is the authoritative source for:

-   Device identity
-   logical ports
-   physical pins
-   packages
-   electrical characteristics
-   simulation behavior
-   timing behavior
-   default state
-   validation metadata
-   source evidence
-   test vectors

The Device Library does not define Board layout or visual presentation.

Visual presentation belongs to Resource Libraries.

------------------------------------------------------------------------

# 2. Core Relationship

``` text
component:component
        ↓ uses
Device Library
        ↓ provides
Device Type
        ↓ instantiated as
Device
```

Example:

``` component
component:component CounterDemo {
    use standard.lib;

    device Counter is 74HC161;
}
```

Meaning:

``` text
standard.lib::74HC161
        ↓
Device instance: Counter
```

------------------------------------------------------------------------

# 3. Standard Device Library

The first Device Library is:

``` text
standard.lib
```

It is the default verified library supplied with Components.

It may contain:

## Physical Devices

``` text
74HC00
74HC04
74HC08
74HC14
74HC74
74HC138
74HC157
74HC161
74HC245
74HC273
74HC283
74HC541
74HC574
74HC595
74HC688
AT28C256
62256
RESISTOR
CAPACITOR
LED
BUTTON
SWITCH
CONNECTOR
```

## Virtual Devices

``` text
VCC
GND
CLOCK
OSCILLATOR
PROBE
TERMINAL
DISPLAY
LOGIC_ANALYZER
NOISE
DELAY
ROM_MATRIX
CONSTANT_HIGH
CONSTANT_LOW
```

Physical and virtual Devices use the same Device Type model.

------------------------------------------------------------------------

# 4. Device Type Identity

Every Device Type must have a stable canonical identity.

Example:

``` json
{
  "library": "standard.lib",
  "device_type": "74HC161",
  "version": "0.1.0"
}
```

Canonical reference:

``` text
standard.lib::74HC161
```

The display name may differ from the canonical identity, but the
canonical identity must remain stable.

Recommended fields:

``` json
{
  "id": "standard.lib::74HC161",
  "name": "74HC161",
  "version": "0.1.0",
  "category": "counter",
  "description": "4-bit synchronous binary counter"
}
```

------------------------------------------------------------------------

# 5. Device Type Categories

Version 0.1 recognizes broad categories for organization only.

``` text
logic
gate
buffer
register
counter
decoder
multiplexer
memory
clock
power
passive
indicator
input
output
interface
debug
virtual
composite
```

Categories do not change parser semantics.

------------------------------------------------------------------------

# 6. Port Model

A Port is a logical endpoint owned by a Device Type.

Examples:

``` text
CLK
Q0
Q1
/CS
/OE
1
2
A
K
pos
neg
```

The Device Library owns port names.

Component Language preserves those names exactly.

Examples:

``` component
Counter.CLK
RAM./CS
R.1
LED.K
```

Minimum Port fields:

``` json
{
  "name": "CLK",
  "direction": "input",
  "pin": 2
}
```

Recommended fields:

``` json
{
  "name": "CLK",
  "direction": "input",
  "pin": 2,
  "signal_type": "digital",
  "active": "high",
  "edge": "rising",
  "electrical": "cmos_input"
}
```

------------------------------------------------------------------------

# 7. Port Direction

Supported directions:

``` text
input
output
bidirectional
passive
power_in
power_out
reference
event_in
event_out
```

Direction is validation metadata.

It does not prevent the parser from building topology.

------------------------------------------------------------------------

# 8. Electrical Types

Version 0.1 should support at least:

``` text
push_pull
tri_state
open_drain
open_collector
passive
high_impedance
power
ground
clock
analog
unknown
```

Example:

``` json
{
  "name": "Q0",
  "direction": "output",
  "electrical": "push_pull"
}
```

Tri-state example:

``` json
{
  "name": "A0",
  "direction": "bidirectional",
  "electrical": "tri_state",
  "enable_port": "/OE"
}
```

Open-drain example:

``` json
{
  "name": "Y",
  "direction": "output",
  "electrical": "open_drain",
  "requires_pullup": true
}
```

------------------------------------------------------------------------

# 9. Active-Level Metadata

Port names remain faithful to the Device definition.

Examples:

``` text
/CS
/OE
/WE
/Y0
```

Active-level metadata may also be stored:

``` json
{
  "name": "/CS",
  "active": "low"
}
```

The metadata does not replace or rename the canonical port name.

------------------------------------------------------------------------

# 10. Physical Pin Model

A Physical Pin belongs to a package.

Physical reference syntax:

``` component
Counter.@2
RAM.@20
```

Minimum Pin fields:

``` json
{
  "number": 2,
  "port": "CLK"
}
```

A pin may have:

-   one logical port
-   no logical port
-   multiple aliases
-   package-specific meaning

A Device Type may support several packages with different pin mappings.

------------------------------------------------------------------------

# 11. Package Model

Example:

``` json
{
  "packages": {
    "DIP16": {
      "pins": [
        {
          "number": 1,
          "port": "/CLR"
        },
        {
          "number": 2,
          "port": "CLK"
        }
      ]
    }
  }
}
```

Supported package metadata may include:

``` text
name
pin_count
pin_numbering
orientation
dimensions
manufacturer_package
source
```

Package geometry belongs primarily to Resource Libraries.

Device Library owns the authoritative pin mapping.

------------------------------------------------------------------------

# 12. Port Aliases

A Device Type may define aliases for search, import, or compatibility.

Example:

``` json
{
  "name": "/CS",
  "aliases": [
    "CS#",
    "CS_BAR"
  ]
}
```

Aliases must not silently replace the canonical name when serializing
Component source.

Canonical output should preserve:

``` component
RAM./CS
```

------------------------------------------------------------------------

# 13. Port Collections

A Device Library may define ordered port collections.

Example:

``` json
{
  "port_collections": {
    "Q": [
      "Q0",
      "Q1",
      "Q2",
      "Q3"
    ]
  }
}
```

This allows:

``` component
Counter.Q[0..3]
```

A user may also define a collection locally:

``` component
Counter[Q0, Q1, Q2, Q3]
    as Counter.Q[0..3];
```

Library-defined collections are reusable defaults.

User-defined collections are local views.

------------------------------------------------------------------------

# 14. Parameters

Some Device Types require parameters.

Example:

``` component
device R is RESISTOR;
```

Canonical model:

``` json
{
  "name": "R",
  "type": "RESISTOR",
  "parameters": {
    "resistance": "1k"
  }
}
```

Possible parameter types:

``` text
integer
number
boolean
string
unit_value
enumeration
file
matrix
```

Version 0.1 may use Device Library defaults when parameters are omitted.

------------------------------------------------------------------------

# 15. Units

Recommended unit-bearing strings:

``` text
1k
220ohm
10pf
100nf
5v
10ns
1mhz
```

The parser or resolver should normalize these into structured values.

Example:

``` json
{
  "value": 1000,
  "unit": "ohm"
}
```

Exact unit grammar may remain provisional in v0.1.

------------------------------------------------------------------------

# 16. Initial State

Sequential and memory Devices may define initial state rules.

Examples:

``` json
{
  "initial_state": {
    "Q": "X"
  }
}
```

``` json
{
  "initial_state": {
    "memory": "undefined"
  }
}
```

Possible initial-state policies:

``` text
zero
one
x
z
undefined
device_default
from_injection
```

Power-on reset behavior should be defined explicitly where known.

------------------------------------------------------------------------

# 17. Simulation Model

Every simulatable Device Type must provide a behavior model.

The model may be implemented as:

``` text
native declarative model
truth table
state machine
Python provider
Rust provider
WASM provider
external simulator adapter
composite Component
```

The Device Library manifest must identify the model type.

Example:

``` json
{
  "simulation": {
    "model": "native",
    "provider": "standard.logic.counter_74hc161"
  }
}
```

------------------------------------------------------------------------

# 18. Combinational Model

A combinational Device may use:

-   truth tables
-   Boolean expressions
-   native provider functions

Example conceptual truth table:

``` json
{
  "simulation": {
    "kind": "truth_table",
    "inputs": [
      "A",
      "B"
    ],
    "outputs": [
      "Y"
    ],
    "rows": [
      {
        "A": 0,
        "B": 0,
        "Y": 0
      },
      {
        "A": 0,
        "B": 1,
        "Y": 0
      },
      {
        "A": 1,
        "B": 0,
        "Y": 0
      },
      {
        "A": 1,
        "B": 1,
        "Y": 1
      }
    ]
  }
}
```

------------------------------------------------------------------------

# 19. Sequential Model

A sequential Device must define:

``` text
state
clock or event sensitivity
asynchronous controls
next-state behavior
output behavior
timing
```

Example conceptual model:

``` json
{
  "simulation": {
    "kind": "state_machine",
    "clock": {
      "port": "CLK",
      "edge": "rising"
    },
    "asynchronous": [
      "/CLR"
    ],
    "state": [
      "Q0",
      "Q1",
      "Q2",
      "Q3"
    ]
  }
}
```

------------------------------------------------------------------------

# 20. Memory Model

Memory Devices must define:

``` text
address ports
data ports
control ports
capacity
word width
read behavior
write behavior
initialization policy
timing
```

Example:

``` json
{
  "memory": {
    "address": "A[0..14]",
    "data": "D[0..7]",
    "words": 32768,
    "word_width": 8,
    "read_only": false
  }
}
```

Memory content may be supplied by `inject`.

------------------------------------------------------------------------

# 21. Timing Model

Timing metadata may include:

``` text
propagation delay
setup time
hold time
pulse width
enable delay
disable delay
rise time
fall time
```

Example:

``` json
{
  "timing": {
    "propagation": {
      "CLK->Q": "18ns"
    },
    "setup": {
      "D->CLK": "10ns"
    },
    "hold": {
      "D->CLK": "5ns"
    }
  }
}
```

Version 0.1 may support simplified nominal delays before full
min/typ/max models.

------------------------------------------------------------------------

# 22. Validation Metadata

Device Types may declare rules used by validators.

Examples:

``` json
{
  "validation": {
    "unused_inputs": "warning",
    "power_required": true,
    "current_limit": {
      "output": "6ma"
    }
  }
}
```

Educational rules may include:

``` json
{
  "education": {
    "suggestions": [
      {
        "when": "LED directly connected to push_pull output",
        "message": "LED may require a current-limiting resistor."
      }
    ]
  }
}
```

Educational guidance must not alter simulation semantics.

------------------------------------------------------------------------

# 23. Virtual Devices

Virtual Devices use the same structure as physical Devices but may omit
packages and physical pins.

Example CLOCK:

``` json
{
  "id": "standard.lib::CLOCK",
  "name": "CLOCK",
  "category": "virtual",
  "ports": [
    {
      "name": "OUT",
      "direction": "event_out",
      "electrical": "clock"
    }
  ],
  "simulation": {
    "model": "native",
    "provider": "standard.virtual.clock"
  }
}
```

Virtual Devices may have interactive Resource mappings.

------------------------------------------------------------------------

# 24. Composite Devices

A composite Device may be defined by an internal Component.

Example:

``` text
RV8_PC16
    composed from
    74HC161 x4
    74HC157 x4
```

Conceptual model:

``` json
{
  "id": "rv8.lib::RV8_PC16",
  "implementation": {
    "kind": "component",
    "source": "rv8_pc16.component"
  }
}
```

Composite and leaf Devices use the same external Device interface.

------------------------------------------------------------------------

# 25. Source Evidence

Verified physical Devices should retain source evidence.

Example:

``` json
{
  "sources": [
    {
      "type": "datasheet",
      "vendor": "Texas Instruments",
      "file": "Source/74HC161_TI_SN74HC161.pdf",
      "verified": true
    }
  ]
}
```

Source evidence may support:

-   pin mapping
-   timing
-   voltage limits
-   truth tables
-   package availability

------------------------------------------------------------------------

# 26. Tests

Every Device Type should include tests.

Minimum test categories:

``` text
schema validation
port resolution
pin resolution
truth table
state transition
timing
unknown-state behavior
tri-state behavior
serialization
```

Example:

``` json
{
  "tests": [
    {
      "name": "count_on_rising_edge",
      "fixture": "tests/74hc161_count.json"
    }
  ]
}
```

------------------------------------------------------------------------

# 27. Library Manifest

A Device Library should have a manifest.

Example:

``` json
{
  "device_library": {
    "name": "standard.lib",
    "version": "0.1.0",
    "devices": [
      "74HC161",
      "74HC245",
      "LED",
      "RESISTOR",
      "CLOCK",
      "VCC",
      "GND"
    ]
  }
}
```

Recommended file structure:

``` text
standard.lib/
├── library.json
├── devices/
│   ├── 74HC161.json
│   ├── LED.json
│   └── CLOCK.json
├── models/
├── tests/
├── docs/
└── sources/
```

The existing repository DB may remain the physical storage during
migration.

`standard.lib` is the logical library identity.

------------------------------------------------------------------------

# 28. Library Resolution

Resolver input:

``` component
use standard.lib;
```

Resolver responsibilities:

``` text
locate library
load manifest
verify version
index Device Types
resolve aliases
load simulation providers
load tests and metadata when required
```

Resolution must fail clearly.

Example:

``` text
DEVICE_NOT_FOUND

Device type "74HC999" was not found in standard.lib.
```

The resolver must not guess a Device Type silently.

------------------------------------------------------------------------

# 29. Versioning

Recommended version format:

``` text
major.minor.patch
```

Versioning should distinguish:

``` text
schema compatibility
behavior compatibility
timing data updates
visual resource updates
source evidence updates
```

Resource Library versions are independent from Device Library versions.

------------------------------------------------------------------------

# 30. Resource Mapping Contract

Resource Libraries may map a Device Type by canonical ID.

Example:

``` json
{
  "maps": "standard.lib::74HC161",
  "resource": "standard.resource::74HC161.default"
}
```

A Resource Library must not redefine:

-   ports
-   physical pin mapping
-   behavior
-   timing
-   state
-   validation rules

It may define:

-   visual shape
-   labels
-   pin placement
-   widgets
-   animations
-   teaching overlays
-   interaction surfaces

------------------------------------------------------------------------

# 31. Canonical Device Type Example

``` json
{
  "device_type": {
    "id": "standard.lib::74HC161",
    "name": "74HC161",
    "version": "0.1.0",
    "category": "counter",
    "description": "4-bit synchronous binary counter",
    "ports": [
      {
        "name": "/CLR",
        "direction": "input",
        "pin": 1,
        "active": "low",
        "electrical": "cmos_input"
      },
      {
        "name": "CLK",
        "direction": "input",
        "pin": 2,
        "edge": "rising",
        "electrical": "clock"
      },
      {
        "name": "Q0",
        "direction": "output",
        "pin": 14,
        "electrical": "push_pull"
      }
    ],
    "port_collections": {
      "Q": [
        "Q0",
        "Q1",
        "Q2",
        "Q3"
      ]
    },
    "packages": {
      "DIP16": {
        "pin_count": 16
      }
    },
    "simulation": {
      "model": "native",
      "provider": "standard.logic.counter_74hc161"
    },
    "timing": {
      "mode": "nominal"
    }
  }
}
```

------------------------------------------------------------------------

# 32. Canonical Virtual Device Example

``` json
{
  "device_type": {
    "id": "standard.lib::PROBE",
    "name": "PROBE",
    "version": "0.1.0",
    "category": "debug",
    "ports": [
      {
        "name": "IN",
        "direction": "input",
        "signal_type": "digital"
      }
    ],
    "simulation": {
      "model": "native",
      "provider": "standard.virtual.probe"
    }
  }
}
```

------------------------------------------------------------------------

# 33. Parser and Interpreter Boundary

The Component parser reads:

``` component
device Counter is 74HC161;
```

It produces an unresolved Device declaration.

The Device Library Resolver transforms it into:

``` json
{
  "instance": "Counter",
  "device_type": "standard.lib::74HC161"
}
```

The interpreter then creates Device runtime state from the resolved
Device Type.

The parser must not embed Device definitions.

------------------------------------------------------------------------

# 34. Frozen v0.1 Rules

1.  `standard.lib` is the first Standard Device Library.
2.  Device Libraries own Device meaning.
3.  Device Types have stable canonical identities.
4.  Port names are preserved exactly.
5.  Physical pin mappings are package-specific.
6.  Physical and virtual Devices use the same model.
7.  Device behavior belongs to simulation providers.
8.  Component source references Device Types but does not redefine them.
9.  Resource Libraries may present Devices but may not redefine meaning.
10. Device resolution must never guess silently.
11. Validation metadata is separate from parsing.
12. Timing metadata is separate from topology.
13. Memory contents may be supplied through `inject`.
14. Composite Devices may use Components as implementations.
15. Source evidence and tests are part of a verified Device Library.

------------------------------------------------------------------------

# 35. Prototype Implementation Order

## Stage 1

Create `standard.lib` logical manifest over the existing DB.

## Stage 2

Implement Device Type lookup.

## Stage 3

Implement Port and Physical Pin resolution.

## Stage 4

Implement Device collections and port collections.

## Stage 5

Implement core virtual Devices:

``` text
VCC
GND
CLOCK
PROBE
```

## Stage 6

Implement first physical Devices:

``` text
74HC161
RESISTOR
LED
```

## Stage 7

Implement validation metadata.

## Stage 8

Implement timing and event models.

## Stage 9

Implement memory Devices and ROM injection.

## Stage 10

Add Resource Library mappings.

------------------------------------------------------------------------

# 36. Definition of Success

The Device Library v0.1 implementation succeeds when:

1.  `use standard.lib;` resolves.
2.  `74HC161`, `RESISTOR`, `LED`, `CLOCK`, `VCC`, `GND`, and `PROBE`
    resolve.
3.  Logical port references resolve.
4.  Physical pin references resolve.
5.  Active-low names such as `/CLR` resolve.
6.  Device collections instantiate correctly.
7.  Port collections expand correctly.
8.  Simulation providers load.
9.  Validation metadata is available.
10. Board Resource Libraries can map the resolved Device Types.
