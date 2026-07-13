# Components Language Specification v1.0

This directory freezes the AST-first Language Core before Board/UI work.
It defines a fixed small core grammar plus a schema layer; it does not yet
implement a parser or replace existing JSON/DB consumers.

Reading order:

1. `Architecture.md` — source-of-truth pipeline and ownership map.
2. `00_Manifesto.md`
3. `03_AST_Model.md`, `05_Object_Model.md`, `06_Component_Model.md`
4. `01_Lexical_Specification.md`, `02_Grammar.md`, `04_Name_Resolution.md`, `07_Type_System.md`
5. `08_Topology_Model.md` through `13_Error_Model.md`
6. `14_Parser_Implementation_Guide.md`, `15_Interpreter_Implementation_Guide.md`

The frozen v1.0 set ends at document 15.  Later documents are explicitly
labelled proposals: `16_Operation_and_Trace_Protocol.md` and
`18_Runtime_Model.md` define the additive runtime boundary, while
`17_Component_Language_Model_v1_1.md` defines the
first executable `component:component` source profile.  Neither amends the
fixed v1 grammar until its resolver and conformance tests are approved.

[`../docs/Component/Component_Model.md`](../docs/Component/Component_Model.md)
is the public human-first Component-model draft built from that profile.  It
selects the readable `device Name is Library.Device;` surface syntax and
provides checked source/JSON fixtures.  It remains a draft until a real
parser/resolver passes its conformance suite.

Boundary: Schema defines structure; Device Library defines meaning and
behavior; Resource Library defines presentation/physical mapping; Component
describes a machine and resolves against Components; a future Components
Runtime executes it; Operation acts on that runtime. Board/UI is explicitly
deferred.  Board/UI is explicitly deferred from the frozen language core.

Later presentation proposals are separate from the frozen core:
`21_Resource_Binding_Contract.md` selects presentation for resolved targets,
`22_Board_Profile_Contract.md` stores an optional Board view, and
`23_Resource_Definition_Contract.md` describes text, 2D, 3D, and future
Resource views without redefining electrical truth.
