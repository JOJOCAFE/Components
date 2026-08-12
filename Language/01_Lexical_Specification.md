# Lexical Specification v1.0

## Scope

This defines tokens for the future fixed-core Components source language. It
does not yet define a lexer implementation.

## Whitespace and comments

Spaces, tabs, CR, and LF separate tokens and otherwise have no meaning.
Newlines are not statements. Line comments start with `//` or `--`; block
comments start with `/*` and end with `*/`. Block comments may not nest.
Comments are discarded before parsing.

The `--` line-comment form is an Ada-style alternative for readability in
circuit descriptions where `//` might be visually confused with parallel
symbols or pin names.

## Identifiers and literals

```text
Identifier      = [A-Za-z_] [A-Za-z0-9_]*
PortIdentifier  = [A-Za-z_/] [A-Za-z0-9_/]*
```

Standard identifiers (device names, net names, aliases) use the base
Identifier rule. Port identifiers extend this with `/` to support
datasheet-authentic active-low signal names like `/OE`, `/CLR`, `/1PRE`
directly in source text without requiring quotes.

Examples: `LED`, `Counter`, `ROM`, `/OE`, `/CLR`, `/1PRE`, `A/B`.

Identifiers are case-sensitive. When a port name contains characters beyond
the PortIdentifier set (such as `I/O0`), it must be quoted: `U1."I/O0"`.

| Kind | Form | Examples |
|---|---|---|
| integer | decimal, `0x` hexadecimal, `0b` binary | `12`, `0xFF`, `0b0101` |
| string | double quoted, JSON escapes | `"74HC245"`, `"/OE"` |
| boolean | reserved literal | TRUE`, `FALSE` | reserved constant use capital letters first (lowercase is optional)

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
