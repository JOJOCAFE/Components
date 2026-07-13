# Archived Components references

Everything in this directory is retained as historical input only.  The active
Component-model document is now the sole Markdown document at
[`../Component_Model.md`](../Component_Model.md).  Do not treat any archived
grammar, Board, Device, Resource, JSON, RFC, DOCX, PDF, or Windows-zone sidecar
as the current implementation contract.

## Authority hierarchy

When documents disagree, use this order:

1. [`../../Language/README.md`](../../Language/README.md) and the numbered
   `Language/` specifications are the frozen Language Core v1.0.
2. [`../DEFINITION_OWNERSHIP_V0_1.md`](../DEFINITION_OWNERSHIP_V0_1.md) is
   authoritative for Schema, Device, Resource, Component, Board, Operation,
   and Generated-data ownership.
3. [`../DEFINITION_MIGRATION_STATUS.md`](../DEFINITION_MIGRATION_STATUS.md),
   compact-definition specifications, schemas, resolver code, and tests are
   authoritative for the current package migration contract.
4. The files in this directory are proposal, historical, or deferred material
   unless a later normative document explicitly adopts a section.

In particular, the frozen boundary is:

```text
Schema     defines structure and validation rules.
Device     defines identity, pins/ports, behavior, timing, and evidence.
Resource   defines presentation and physical/view mapping.
Component  describes an instantiated machine and its topology.
Operation  acts on a resolved machine.
Board      presents and controls a machine.
Generated  contains resolver/audit output only.
```

Board/UI implementation is deferred.  Board documents may guide later design,
but they neither define Device behavior nor authorize a Board implementation.

## Imported Markdown inventory

| Imported source | Classification | Crosswalk |
| --- | --- | --- |
| `00_Manifesto_v0.1.md` | Reference | Historical expression of the vision.  `Language/00_Manifesto.md` is its normative successor. |
| `01_Components_Component_Model_v0.1.md` | Superseded | Its model is reconciled and frozen across `Language/03_AST_Model.md`, `05_Object_Model.md`, and `06_Component_Model.md`. |
| `02_Component_Grammar_v0.1.md` | Superseded | `Language/01_Lexical_Specification.md` and `Language/02_Grammar.md` define the current fixed core grammar. |
| `03_JSON_Object_Model_v0.1.md` | Superseded | `Language/11_JSON_Model.md` is the normative JSON-model successor; package JSON ownership is governed by `../DEFINITION_OWNERSHIP_V0_1.md`. |
| `04_Components_Board_Visual_Design_v0.1.md` | Deferred | Useful Board/UI proposal only.  Board/UI is outside the frozen Language Core and has no implementation authorization. |
| `05_Device_Library_Spec_v0.1.md` | Reference | Its Device/Resource separation is useful input; the normative ownership boundary is `../DEFINITION_OWNERSHIP_V0_1.md`. |
| `06_Resource_Library_Spec_v0.1.md` | Reference | Useful presentation-only proposal; current Resource rules and migration proof are in `../DEFINITION_OWNERSHIP_V0_1.md`. |
| `07_Interpreter_Architecture_v0.1.md` | Superseded | `Language/08_Topology_Model.md` through `Language/10_Execution_Model.md` and `Language/15_Interpreter_Implementation_Guide.md` are normative. |
| `ComponetsRFC.md` | Reference | Imported RFC index only; it is not an adopted RFC registry or implementation plan. |

## Imported DOCX/PDF inventory

Each DOCX/PDF pair is the same imported proposal in editable and rendered
forms.  Neither form is normative; preserve both until a later, separately
reviewed archive decision.

| Imported pair | Classification | Crosswalk |
| --- | --- | --- |
| `The Components Manifesto.docx` / `The Components Manifesto.pdf` | Reference | Historical manifesto; normative successor: `Language/00_Manifesto.md`. |
| `Components Architecture Constitution.docx` / `Components Architecture Constitution.pdf` | Reference | Architecture background; current authority is the Language Core plus definition ownership contract. |
| `RFC-0001 — Components Vision and Terminology.docx` / `.pdf` | Reference | Vision and terminology input; current vocabulary follows `Language/README.md`. |
| `RFC-0002 — Component Language Philosophy.docx` / `.pdf` | Reference | Language philosophy input; AST-first Language Core is normative. |
| `RFC-0003 — Component Model.docx` / `.pdf` | Superseded | Normative successors: `Language/03_AST_Model.md`, `05_Object_Model.md`, and `06_Component_Model.md`. |
| `Component Document Model v0.1 Amendment.docx` / `.pdf` | Superseded | Normative successor: `Language/11_JSON_Model.md`; package ownership also follows `../DEFINITION_OWNERSHIP_V0_1.md`. |
| `Resource Model v0.1 Amendment.docx` / `.pdf` | Reference | Resource-design input; presentation-only ownership is defined by `../DEFINITION_OWNERSHIP_V0_1.md`. |

## Windows metadata sidecars

Every imported `*:Zone.Identifier` file is classified as **superseded
metadata**, not as a design source.  These files record Windows download-zone
information and have no role in parsing, simulation, migration, or language
specification.  They are intentionally retained for this checkpoint.  Remove
them only in a dedicated cleanup change after confirming repository policy and
history requirements.

This classification applies to the sidecar beside every Markdown, DOCX, and
PDF item listed above, including `ComponetsRFC.md` if a sidecar is added later.

## Archive rule

- Read it only for context and proposal recovery.
- Do not copy a legacy rule into implementation without reconciling it with
  the authority hierarchy above and the active Component model.
- Do not treat “Frozen for Prototype v0.1” inside an archived file as a
  current repository freeze.
