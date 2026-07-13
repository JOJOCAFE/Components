# 14 — Parser Implementation Guide

Status: Language Specification v1.0 — implementation guidance.

Implement the fixed small Core Language first:

```text
source -> lexer -> token stream -> parser -> AST -> structural validation
```

The parser recognizes only the frozen universal top-level forms and syntax
defined in [01 Lexical Specification](01_Lexical_Specification.md) and
[02 Grammar](02_Grammar.md). Schema declarations constrain permitted fields
and domain declarations after parsing; they do not generate a new lexer or
make parser behavior depend on installed Devices.

Parser output is the typed AST of [03 AST Model](03_AST_Model.md), with exact
spans and recoverable error nodes. It must not load Device Libraries, evaluate
logic, derive topology, choose symbols, or run operations. Those belong to the
resolver/interpreter.

Recommended tests: token fixtures; valid/invalid grammar fixtures; AST golden
JSON; span/error recovery tests; and schema structural-validation tests. Keep
Board/UI parsing deferred: accept no Board-specific layout extensions beyond
the frozen top-level placeholder until a later separately versioned proposal.
