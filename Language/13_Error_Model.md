# 13 — Error Model

Status: Language Specification v1.0 — diagnostic contract.

Every diagnostic has a stable `code`, severity (`error`, `warning`, `info`),
human-readable beginner-safe message, primary source span, and optional
related spans/fix hints. Diagnostics never silently repair an ambiguous design.

| Phase | Examples |
|---|---|
| Lexer/parser | unexpected token, unterminated string, expected identifier |
| Schema | missing required field, forbidden field, invalid literal |
| Resolver | unknown Device/port, duplicate symbol, unresolved reference, alias cycle |
| Type/topology | width mismatch, incompatible direction, floating required input, power short |
| Interpreter | output contention, undefined state, unsupported model, oscillation, timeout |
| Resource | unknown Device mapping, presentation pin mismatch, missing artifact |

`error` prevents the affected phase from producing a trusted result. `warning`
allows it with visible uncertainty. A runtime contention reports the drivers,
net, value, and time/delta. A parser error reports a recovery location when
possible, but recovered AST nodes are marked invalid and cannot be interpreted.

Physical-risk statements (for example no hardware timing signoff) are warnings
or documentation boundaries, never fabricated simulation errors.
