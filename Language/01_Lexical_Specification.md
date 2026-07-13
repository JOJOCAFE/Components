# Lexical Specification v1.0

## Scope

This defines tokens for the future fixed-core Components source language. It
does not yet define a lexer implementation.

## Whitespace and comments

Spaces, tabs, CR, and LF separate tokens and otherwise have no meaning.
Newlines are not statements. Line comments start with `//`; block comments
start with `/*` and end with `*/`. Block comments may not nest. Comments are
discarded before parsing.

## Identifiers and literals

```text
Identifier = [A-Za-z_] [A-Za-z0-9_]*
```

Examples are `LED`, `Counter`, `ROM`, `_RAM`, and `counter123`. Identifiers
are case-sensitive. A pin spelling such as `/OE` is a quoted pin selector, not
an identifier.

| Kind | Form | Examples |
|---|---|---|
| integer | decimal, `0x` hexadecimal, `0b` binary | `12`, `0xFF`, `0b0101` |
| string | double quoted, JSON escapes | `"74HC245"`, `"/OE"` |
| boolean | reserved literal | `true`, `false` |

Numbers have no implicit time, voltage, or width unit. Unit-bearing values are
typed properties in the resolved object model, never guessed from a bare token.

## Keywords and punctuation

Reserved top-level keywords are `component:schema`, `component:component`,
`component:board`, `component:operation`, `use`, `is`, `as`, `device`,
`connect`, `net`, `probe`, `inject`, and `property`. A future grammar may add
domain keywords only through a Schema-defined declaration position.

Punctuation is `{`, `}`, `[`, `]`, `(`, `)`, `,`, `;`, `.`, `:`, `@`.
The connection operator is `->`; range syntax is `..`.

## Lexical errors

An unterminated string/comment, illegal character, malformed numeric prefix,
or invalid escape is a lexical error with source span. The lexer must not
silently repair a token.
