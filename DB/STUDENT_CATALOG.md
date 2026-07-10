# Student Catalog View

Learner-facing DB view for tools, examples, and classroom UIs.

The student catalog does not create a second source of truth. It is a smaller
view synthesized from package definitions so students see the useful fields
first: what the part is, whether it can simulate, whether it can export to
Verilog, which pins matter first, and what warnings should be shown before
building.

Audience: students around ages 10-15, still useful for older learners.

## Groups

Valid group filters:

- `74xx`
- `memory`
- `virtual`
- `passive`
- `discrete`

## CLI

Run from the repo root:

```sh
PYTHONPATH=python python3 -m chiplib.cli db --student
PYTHONPATH=python python3 -m chiplib.cli db --student --group 74xx
PYTHONPATH=python python3 -m chiplib.cli db --student --group virtual
PYTHONPATH=python python3 -m chiplib.cli db --student --group discrete
```

## Python

```python
from chiplib.db import student_component_catalog

catalog = student_component_catalog(group="74xx")
card = catalog["components"][0]
print(card["part"], card["readiness"], card["student_note"])
```

## Service Command

HTTP and stdio adapters use the same command:

```json
{"command": "student-component-catalog", "options": {"group": "virtual"}}
```

The response uses:

```json
{"format": "components.db.student_catalog"}
```

## Component Card

Example shape:

```json
{
  "part": "Probe",
  "title": "Single logic probe",
  "group": "virtual",
  "kind": "virtual",
  "role": "probe",
  "readiness": "usable",
  "capabilities": {
    "can_simulate": true,
    "can_export_verilog": false,
    "has_verified_pinout": false,
    "has_datasheet": false
  },
  "pins": {
    "count": 1,
    "preview": [
      {"number": 1, "name": "IN", "direction": "input"}
    ]
  },
  "files": {
    "db": "DB/Virtual/Probe/definition/definition.json",
    "verilog": ""
  },
  "status": {
    "datasheet": "not_applicable",
    "pinout": "modeled",
    "python_behavior": "modeled",
    "verilog_model": "not_applicable",
    "verilog_export": "not_applicable",
    "tests": "modeled"
  },
  "student_note": "Usable as a probe; check the status fields before using advanced outputs.",
  "warnings": []
}
```

## Readiness

- `ready`: good for examples and simulations.
- `usable`: usable, but advanced output or evidence may be missing.
- `needs_info`: visible in the catalog, but tools should show missing data
  before students build with it.

## Boundary

This is a view only. Behavior models, Verilog models, pin evidence, tests, and
package definitions stay in their package folders. UI code should display the
student catalog, then link back to the package definition when a learner needs
the full evidence.
