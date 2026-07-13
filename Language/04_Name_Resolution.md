# Name Resolution v1.0

## Purpose

Resolution turns AST names into immutable symbols and typed references. It does
not simulate, place resources, or infer a connection from matching names.

## Scopes and order

1. File imports introduce library aliases.
2. Top-level declarations introduce unique file symbols.
3. A Component body introduces local instance, net, probe, and metadata symbols
   in source order, subject to its Schema.
4. A Device instance resolves through its imported Device Library entry.
5. Port and physical-pin selectors resolve only against that Device's resolved
   Device definition.

Duplicate declarations in one scope are errors. A local name never silently
shadows an imported alias.

## Selectors

| Source | Meaning after resolution |
|---|---|
| `Counter.Q0` | named port `Q0` of `Counter` |
| `Counter.@3` | physical pin 3 of `Counter` |
| `RAM."/CS"` | named active-low port `/CS` of `RAM` |

Pin aliases, bus slices, and package mappings are supplied by the Device
Library; they are not guessed from spelling. Missing or ambiguous selectors are
resolution errors.

## Outputs and boundary

Resolver output includes a symbol table, typed references, imported Device
definitions, and an explicit Component object model. It may apply declared
Schema/profile defaults, but records their origin. It must not alter authored
Device truth or allow a Resource map to supply behavior or timing.

Direction compatibility, width, power, and output ownership are semantic
checks after resolution; see [07_Type_System.md](07_Type_System.md) and the
topology model.
