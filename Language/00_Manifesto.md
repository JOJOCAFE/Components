# Components Language Manifesto v1.0

## Status

This is the frozen architectural boundary for the first Components language
implementation. It is AST-first: syntax or parser strategy may change only if
it preserves the AST, resolved object model, topology, and execution contracts.

Components describes machines that people can inspect, simulate, validate, and
present. It is not a drawing program with incidental simulation.

## Core statements

> Schema defines what may be described.
>
> Component describes what exists.
>
> Device Library defines what it means and how it behaves.
>
> Operation defines what is done to it.
>
> Resource Library defines how it is presented or mapped.
>
> Board lets people see and interact with it.

```text
Source -> Lexer -> Parser -> AST -> Resolver -> Topology -> Interpreter
```

The interpreter executes resolved topology, never source text or raw AST.

## Ownership

| Layer | Owns | Does not own |
|---|---|---|
| Schema | structural language rules | device behavior or resources |
| Device Library | ports, pins, behavior, timing, evidence | placement or drawing |
| Resource Library | symbol, footprint, board-view mappings | behavior, timing, truth status |
| Component | instances and explicit connections | copied library behavior |
| Board | presentation and interaction bindings | new behavior or hidden wiring |
| Operation | requested actions on a resolved machine | implicit topology |

This language preserves the package-level boundaries in
[`docs/DEFINITION_OWNERSHIP_V0_1.md`](../docs/DEFINITION_OWNERSHIP_V0_1.md).
It does not replace current JSON package and circuit contracts.

## v1 non-goals

Language v1 does **not** implement a parser, editor, Board/UI, graphical
layout, schema-authored parser generator, analog solver, firmware language, or
new simulation semantics. It does not migrate Device or Resource files and
does not change `python/chiplib` behavior. A later implementation must first
pass the contracts in this directory.
