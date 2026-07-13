# 06 Resource Library Specification v0.1

**Status:** Frozen for Prototype v0.1\
**Primary resource library:** `standard.resource`

## 1. Purpose

A Resource Library defines how Devices, signals, traces, terminals,
displays and other Board-visible objects are presented and interacted
with.

A Resource Library is presentation-only.

It must not redefine:

-   Device identity
-   logical ports
-   physical pin mappings
-   electrical behavior
-   timing behavior
-   simulation state rules
-   validation semantics

Those belong to Device Libraries and Components Platform.

------------------------------------------------------------------------

# 2. Core Relationship

``` text
Device Library
    defines meaning

Resource Library
    defines presentation

Component
    defines the machine

Board
    selects and arranges resources

Components Platform
    resolves state and executes behavior
```

Example:

``` component
component:component CounterDemo {
    use standard.lib;

    device Counter is 74HC161;
}
```

``` component
component:board MainBoard {
    use CounterDemo;
    use standard.resource;
}
```

------------------------------------------------------------------------

# 3. Standard Resource Library

The first Resource Library is:

``` text
standard.resource
```

It provides default presentation resources for Devices in
`standard.lib`.

Possible contents:

``` text
Device symbols
DIP package views
breadboard views
compact block views
teaching views
debug views
terminal widgets
display widgets
waveform widgets
probe markers
clock controls
wire styles
bus styles
icons
labels
animations
themes
```

------------------------------------------------------------------------

# 4. Resource Identity

Every resource must have a stable canonical identity.

Example:

``` json
{
  "id": "standard.resource::74HC161.default",
  "name": "74HC161.default",
  "version": "0.1.0",
  "maps": "standard.lib::74HC161"
}
```

Recommended canonical form:

``` text
resource_library::resource_name
```

Examples:

``` text
standard.resource::74HC161.default
standard.resource::74HC161.dip16
standard.resource::LED.default
standard.resource::CLOCK.control
standard.resource::TERMINAL.widget
```

------------------------------------------------------------------------

# 5. Resource Categories

Version 0.1 recognizes these broad categories:

``` text
device_visual
package_visual
symbol
widget
panel
wire_style
bus_style
label_style
timeline_renderer
waveform_renderer
terminal_renderer
display_renderer
theme
annotation
interaction
```

Categories are organizational metadata.

They do not change Device semantics.

------------------------------------------------------------------------

# 6. Device-to-Resource Mapping

A Resource may map one Device Type.

Example:

``` json
{
  "resource": {
    "id": "standard.resource::74HC161.dip16",
    "maps": "standard.lib::74HC161",
    "view": "dip",
    "package": "DIP16"
  }
}
```

One Device Type may have multiple visual resources:

``` text
standard.lib::74HC161
├── standard.resource::74HC161.default
├── standard.resource::74HC161.compact
├── standard.resource::74HC161.dip16
├── breadboard.resource::74HC161.breadboard
├── classroom.resource::74HC161.teaching
└── debug.resource::74HC161.debug
```

All are views of the same Device instance.

------------------------------------------------------------------------

# 7. Multiple Resource Libraries

A Board may use several Resource Libraries.

``` component
component:board MainBoard {
    use CounterDemo;

    use standard.resource;
    use breadboard.resource;
    use classroom.resource;
}
```

Possible libraries:

``` text
standard.resource
breadboard.resource
schematic.resource
classroom.resource
retro.resource
rv8.resource
accessibility.resource
debug.resource
```

Resource Libraries may map Devices from one or more Device Libraries.

------------------------------------------------------------------------

# 8. Resolution Precedence

When several Resource Libraries provide a matching resource, the Board
resolver uses this precedence:

``` text
1. Explicit resource selection
2. Board-local override
3. Last matching imported Resource Library
4. Earlier matching imported Resource Library
5. Device Library fallback metadata
6. Generic unknown-Device visual
```

Example:

``` component
use standard.resource;
use classroom.resource;
```

If both provide a default view for `74HC161`, `classroom.resource` wins
unless the Board selects another resource explicitly.

------------------------------------------------------------------------

# 9. Explicit Resource Selection

A Board may select a resource for a specific Device.

Provisional notation:

``` component
show Counter as classroom.resource::74HC161.teaching;
```

Or canonical JSON:

``` json
{
  "target": "Counter",
  "resource": "classroom.resource::74HC161.teaching"
}
```

The exact text grammar may evolve after the first Board prototype.

The object model is frozen:

``` text
target
resource identity
view variant
optional package
optional state
```

------------------------------------------------------------------------

# 10. Resource Manifest

A Resource Library should contain a manifest.

Example:

``` json
{
  "resource_library": {
    "name": "standard.resource",
    "version": "0.1.0",
    "resources": [
      "74HC161.default",
      "74HC161.dip16",
      "LED.default",
      "CLOCK.control",
      "PROBE.marker",
      "TERMINAL.widget"
    ]
  }
}
```

Recommended structure:

``` text
standard.resource/
├── resource.json
├── devices/
├── packages/
├── widgets/
├── renderers/
├── styles/
├── themes/
├── icons/
├── animations/
├── tests/
└── docs/
```

------------------------------------------------------------------------

# 11. Device Visual Model

A Device visual should define at least:

``` text
resource identity
mapped Device Type
view name
bounds
anchors
port visuals
pin visuals
labels
state bindings
interaction bindings
```

Example:

``` json
{
  "resource": {
    "id": "standard.resource::74HC161.default",
    "maps": "standard.lib::74HC161",
    "view": "default",
    "bounds": {
      "width": 240,
      "height": 180
    },
    "labels": {
      "show_instance_name": true,
      "show_device_type": true
    }
  }
}
```

------------------------------------------------------------------------

# 12. Port Visuals

Port visuals map Device ports to visual anchors.

Example:

``` json
{
  "ports": [
    {
      "port": "/CLR",
      "side": "left",
      "order": 0,
      "label": "/CLR",
      "show_pin_number": true
    },
    {
      "port": "CLK",
      "side": "left",
      "order": 1,
      "label": "CLK",
      "show_pin_number": true
    },
    {
      "port": "Q0",
      "side": "right",
      "order": 0,
      "label": "Q0",
      "show_pin_number": true
    }
  ]
}
```

A Resource Library may place ports visually.

It must not alter their identity or physical pin mapping.

------------------------------------------------------------------------

# 13. Physical Package Visuals

A package visual represents the physical package.

Example:

``` json
{
  "resource": {
    "id": "standard.resource::74HC161.dip16",
    "maps": "standard.lib::74HC161",
    "view": "dip",
    "package": "DIP16",
    "orientation": "top"
  }
}
```

The Device Library owns:

``` text
pin 1 -> /CLR
pin 2 -> CLK
...
```

The Resource Library owns:

``` text
pin geometry
package outline
notch
orientation marker
label placement
```

------------------------------------------------------------------------

# 14. Compact and Educational Views

A compact view may collapse rarely used ports.

An educational view may expose more explanation.

Example educational metadata:

``` json
{
  "annotations": [
    {
      "target": "CLK",
      "text": "Counts on the rising edge."
    },
    {
      "target": "/CLR",
      "text": "Active-low asynchronous clear."
    }
  ]
}
```

Annotations must not alter simulation.

------------------------------------------------------------------------

# 15. Signal-State Binding

A visual may bind its appearance to simulation state.

Example:

``` json
{
  "state_bindings": [
    {
      "source": "Q0",
      "property": "indicator",
      "values": {
        "0": "off",
        "1": "on",
        "X": "unknown",
        "Z": "high_impedance"
      }
    }
  ]
}
```

Supported digital states:

``` text
0
1
X
Z
```

The Board receives state from Components Platform.

The Resource only defines how that state is rendered.

------------------------------------------------------------------------

# 16. Virtual Device Resources

Virtual Devices may have interactive resources.

Examples:

``` text
CLOCK
    step button
    run/pause control
    frequency control

PROBE
    probe marker
    value badge

TERMINAL
    text input/output widget

DISPLAY
    display surface

LOGIC_ANALYZER
    waveform panel

VCC
    power symbol

GND
    ground symbol
```

Behavior remains in the Device Library.

Interaction is converted into Operations.

------------------------------------------------------------------------

# 17. Interaction Model

A Resource may declare interaction events.

Example:

``` json
{
  "interactions": [
    {
      "event": "press",
      "target": "CLOCK",
      "operation": {
        "step": {
          "target": "CLOCK"
        }
      }
    }
  ]
}
```

Interaction flow:

``` text
User interaction
    ↓
Resource emits interaction intent
    ↓
Board creates Operation
    ↓
Components Platform executes
    ↓
Board receives new state
    ↓
Resource renders the new state
```

A Resource must never mutate simulation state directly.

------------------------------------------------------------------------

# 18. Board Placement Model

Board placement belongs to `component:board`.

Example:

``` json
{
  "placement": {
    "target": "Counter",
    "x": 320,
    "y": 180,
    "rotation": 0,
    "resource": "standard.resource::74HC161.default"
  }
}
```

Possible placement fields:

``` text
target
x
y
rotation
scale
z_order
resource
group
locked
visible
```

------------------------------------------------------------------------

# 19. Collection Placement

Collections may be arranged as groups.

Example conceptual JSON:

``` json
{
  "layout": {
    "targets": "LED[0..3]",
    "mode": "stack",
    "direction": "vertical",
    "gap": 24,
    "origin": {
      "x": 760,
      "y": 100
    }
  }
}
```

Supported prototype modes:

``` text
free
stack
row
column
grid
```

Advanced automatic layout is outside v0.1.

------------------------------------------------------------------------

# 20. Connection Presentation

Component owns connectivity.

Board owns how connectivity is shown.

Possible presentations:

``` text
direct wire
orthogonal wire
curved wire
bus
net label
portal
hidden
```

Example:

``` json
{
  "route": {
    "connection": "Clock.OUT->Counter.CLK",
    "style": "orthogonal"
  }
}
```

A route must reference an existing Component connection.

It must not create new topology.

------------------------------------------------------------------------

# 21. Wire and Bus Styles

Wire styles may define:

``` text
thickness
dash pattern
junction appearance
arrow visibility
state display
label placement
crossing behavior
```

Bus styles may define:

``` text
collapsed line
width label
expand control
member labels
fan-out presentation
```

Signal values may be displayed without relying on color alone.

------------------------------------------------------------------------

# 22. Panels

Board may present several panels:

``` text
component
board
terminal
timeline
waveform
inspector
library
resources
```

Prototype primary layout:

``` text
Component | Board
-----------------
Terminal / Timeline / Waveform
```

Panel layout belongs to the Board document.

Panel content may be rendered by Resource widgets.

------------------------------------------------------------------------

# 23. Terminal Resources

A Terminal Device is part of the Component.

A terminal renderer belongs to a Resource Library.

Example:

``` json
{
  "resource": {
    "id": "standard.resource::TERMINAL.widget",
    "maps": "standard.lib::TERMINAL",
    "category": "terminal_renderer"
  }
}
```

Board may connect the visible terminal to:

``` text
Components console
machine UART
monitor program
user-defined console Device
```

The machine monitor remains part of the Component.

------------------------------------------------------------------------

# 24. Display Resources

Display Devices may include:

``` text
LED
LED_PANEL
SEVEN_SEGMENT
LCD
OLED
VGA_DISPLAY
TEXT_DISPLAY
GRAPHICS_DISPLAY
```

The Resource Library renders their state.

No `print` or `display` keyword is required.

------------------------------------------------------------------------

# 25. Timeline Renderer

Timeline resources present:

``` text
tick
time
event
injection regions
probe regions
simulation cursor
run state
```

Minimum controls:

``` text
run
pause
step
reset
speed
cursor
zoom
pan
```

The timeline renderer does not advance simulation itself.

It sends Operations to Components Platform.

------------------------------------------------------------------------

# 26. Waveform Renderer

Waveform resources present probe traces.

Minimum v0.1 capabilities:

``` text
multiple signals
0, 1, X, Z
bus display
bus expand/collapse
zoom
pan
cursor
transition markers
injection regions
```

Trace data comes from Components Platform.

The renderer must not infer missing signal history.

------------------------------------------------------------------------

# 27. Theme Model

Themes may define:

``` text
surface appearance
typography
spacing
device card style
wire appearance
focus state
selection state
diagnostic appearance
```

Themes must preserve accessibility and meaning.

A theme must not encode critical state using color alone.

------------------------------------------------------------------------

# 28. Accessibility

Resource Libraries should support:

``` text
scalable labels
high contrast
keyboard navigation
touch targets
screen reader labels
non-color state indicators
reduced motion
```

Board is tablet-first but must remain desktop-friendly.

------------------------------------------------------------------------

# 29. Resource Data Types

Resources may contain:

``` text
JSON metadata
SVG
PNG
WebP
vector paths
fonts referenced by name
animation definitions
shader definitions
widget code
WASM renderers
documentation
```

Resource packages must not distribute proprietary fonts without proper
licensing.

------------------------------------------------------------------------

# 30. Executable Resources

Interactive widgets may require executable code.

Allowed providers may include:

``` text
native Board widget
JavaScript module
WASM module
Flutter widget provider
web component
platform plugin
```

Executable resources must run in a restricted interface.

They may:

``` text
render state
emit interaction intent
request Operations
receive Results
```

They may not:

``` text
mutate simulator memory directly
bypass Operations
redefine Device behavior
access unrestricted system resources
```

------------------------------------------------------------------------

# 31. Resource Dependencies

A Resource Library may depend on other Resource Libraries.

Example:

``` json
{
  "resource_library": {
    "name": "classroom.resource",
    "version": "0.1.0",
    "uses": [
      "standard.resource"
    ]
  }
}
```

Circular dependencies should be rejected.

------------------------------------------------------------------------

# 32. Compatibility

A Resource mapping may specify compatibility.

Example:

``` json
{
  "maps": {
    "device": "standard.lib::74HC161",
    "device_version": ">=0.1.0",
    "package": "DIP16"
  }
}
```

Compatibility checks may include:

``` text
Device Type ID
Device version
package
required ports
optional features
Board capability
renderer capability
```

------------------------------------------------------------------------

# 33. Missing Resource Behavior

If no matching resource exists, Board must use a generic fallback.

The fallback should show:

``` text
Device instance name
Device Type
logical ports
physical pin numbers when known
current values
missing-resource diagnostic
```

A missing visual resource must not prevent simulation.

------------------------------------------------------------------------

# 34. Resource Validation

Resource validation should check:

``` text
mapped Device exists
referenced ports exist
package matches
pin anchors are valid
state bindings are valid
interaction operations are permitted
assets exist
dependencies resolve
```

Example diagnostic:

``` text
RESOURCE_PORT_NOT_FOUND

Resource standard.resource::74HC161.default
references port "Q4",
but standard.lib::74HC161 does not define that port.
```

------------------------------------------------------------------------

# 35. Resource Tests

Each Resource should support tests for:

``` text
manifest validation
Device mapping
port anchor mapping
package mapping
state rendering
interaction emission
fallback behavior
accessibility
serialization
```

Golden-image tests may be used for rendering, but semantic tests remain
primary.

------------------------------------------------------------------------

# 36. Canonical Resource Example

``` json
{
  "resource": {
    "id": "standard.resource::LED.default",
    "name": "LED.default",
    "version": "0.1.0",
    "maps": "standard.lib::LED",
    "category": "device_visual",
    "view": "default",
    "bounds": {
      "width": 48,
      "height": 72
    },
    "ports": [
      {
        "port": "A",
        "anchor": {
          "x": 24,
          "y": 0
        }
      },
      {
        "port": "K",
        "anchor": {
          "x": 24,
          "y": 72
        }
      }
    ],
    "state_bindings": [
      {
        "source": "A,K",
        "property": "light",
        "values": {
          "off": "off",
          "on": "on",
          "unknown": "unknown"
        }
      }
    ]
  }
}
```

------------------------------------------------------------------------

# 37. Canonical Interactive Resource Example

``` json
{
  "resource": {
    "id": "standard.resource::CLOCK.control",
    "name": "CLOCK.control",
    "version": "0.1.0",
    "maps": "standard.lib::CLOCK",
    "category": "widget",
    "view": "control",
    "interactions": [
      {
        "event": "step",
        "operation": {
          "step": {
            "target": "$device"
          }
        }
      },
      {
        "event": "run",
        "operation": {
          "run": {
            "target": "$device"
          }
        }
      },
      {
        "event": "pause",
        "operation": {
          "pause": {
            "target": "$device"
          }
        }
      }
    ]
  }
}
```

------------------------------------------------------------------------

# 38. Board Example

``` component
component:board MainBoard {
    use CounterDemo;

    use standard.resource;
    use classroom.resource;

    place Counter at 320, 180;
    place R[0..3] at 560, 100;
    place LED[0..3] at 760, 100;

    show port_name;
    show pin_number;
    show signal_value;
}
```

The exact Board layout grammar remains provisional.

The ownership model is frozen.

------------------------------------------------------------------------

# 39. Parser and Runtime Boundary

The Board parser reads:

``` component
use standard.resource;
```

It produces unresolved Resource Library references.

The Resource Resolver:

``` text
loads manifests
resolves mappings
selects variants
checks compatibility
loads assets
loads renderers
```

The Board runtime:

``` text
renders resources
emits interaction intent
receives state and Results
updates presentation
```

The simulator does not load visual resources.

------------------------------------------------------------------------

# 40. Frozen v0.1 Rules

1.  `standard.resource` is the first Standard Resource Library.
2.  Resource Libraries own presentation, not Device meaning.
3.  One Device Type may have multiple Resource views.
4.  One Board may use multiple Resource Libraries.
5.  Explicit selection overrides automatic resolution.
6.  Later imported Resource Libraries may override earlier ones.
7.  Resource switching must not change topology or simulation.
8.  Device Library owns ports and physical pin mappings.
9.  Board owns placement and presentation choices.
10. Interactive Resources emit Operations.
11. Interactive Resources never mutate simulation state directly.
12. Missing resources must fall back gracefully.
13. Virtual and physical Devices both use Resource mappings.
14. Timeline and waveform renderers consume Platform results.
15. Resource Libraries may grow independently from Device Libraries.

------------------------------------------------------------------------

# 41. Prototype Implementation Order

## Stage 1

Create `standard.resource` manifest.

## Stage 2

Implement generic Device fallback renderer.

## Stage 3

Implement resources for:

``` text
74HC161
RESISTOR
LED
CLOCK
VCC
GND
PROBE
```

## Stage 4

Implement logical port and physical pin labels.

## Stage 5

Implement Device placement and movement.

## Stage 6

Implement direct and orthogonal connection rendering.

## Stage 7

Implement signal value rendering for:

``` text
0
1
X
Z
```

## Stage 8

Implement CLOCK interactive control.

## Stage 9

Implement PROBE and waveform rendering.

## Stage 10

Implement TERMINAL widget and panel layout.

------------------------------------------------------------------------

# 42. Definition of Success

Resource Library v0.1 succeeds when:

1.  `use standard.resource;` resolves.
2.  Board renders every Device through a selected or fallback resource.
3.  `74HC161`, `RESISTOR`, `LED`, `CLOCK`, `VCC`, `GND`, and `PROBE`
    have usable resources.
4.  Logical port names display correctly.
5.  Physical pin numbers display correctly.
6.  Device state updates without changing topology.
7.  CLOCK interaction creates Operations.
8.  Probe traces display as waveform.
9.  Missing resources do not stop simulation.
10. Switching between standard and classroom resources preserves
    Component state.
