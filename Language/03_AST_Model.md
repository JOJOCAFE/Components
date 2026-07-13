# AST Model v1.0

## Authority

The AST is the stable parser-to-resolver contract. Every node carries a source
`span`, optional `leading_comments`, and no runtime Device, Resource, pin, or
simulation object. Parser output is AST only.

## File and declarations

```text
FileNode
  uses: UseNode[]
  declarations: TopLevelNode[]

UseNode
  library: QualifiedNameNode
  alias: IdentifierNode?

SchemaNode | ComponentNode | BoardNode | OperationNode
  name: IdentifierNode
  body: StatementNode[]

ComponentNode
  base_schema: QualifiedNameNode?
```

`BoardNode` exists so source can parse without loss, but v1 does not resolve or
execute it.

## Statements and values

```text
StatementNode
  keyword: IdentifierNode
  arguments: ValueNode[]

ValueNode = IntegerNode | StringNode | BooleanNode | ReferenceNode
          | ArrayNode | ObjectNode

ReferenceNode
  root: IdentifierNode
  segments: NameSegmentNode | PinNumberSegmentNode[]

NameSegmentNode       { name: IdentifierNode }
PinNumberSegmentNode  { number: IntegerNode }   // Device.@3
```

The parser records `connect A -> B;` as a `StatementNode(keyword="connect")`
with two `ReferenceNode` arguments. It does not decide whether either name is
a Device, port, net, or valid connection.

## Invariants

1. Node ordering equals source ordering.
2. Every identifier and literal retains its source span.
3. Syntax errors prevent a valid AST; recovery nodes may serve diagnostics but
   cannot reach resolution.
4. AST has no inferred widths, aliases, defaults, topology edges, or Device
   behavior; those are resolver output.
5. AST may represent unknown Schema statements; validation decides whether they
   are allowed.

The JSON interchange model is a resolved object model, not serialized AST.
