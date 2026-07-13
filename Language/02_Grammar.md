# Grammar v1.0

## Scope

This is a deliberately small fixed core. Schema declarations constrain the
contents of declarations; they do not generate new top-level syntax in v1.
The normative stable contract is the AST in [03_AST_Model.md](03_AST_Model.md).

## EBNF

```ebnf
File              = UseStatement* , TopLevel* , EOF ;
UseStatement      = "use" , QualifiedName , ( "as" , Identifier )? , ";" ;
TopLevel          = SchemaDecl | ComponentDecl | BoardDecl | OperationDecl ;
SchemaDecl        = "component:schema" , Identifier , SchemaBody ;
ComponentDecl     = "component:component" , Identifier , ( "is" , QualifiedName )? , ComponentBody ;
BoardDecl         = "component:board" , Identifier , BoardBody ;
OperationDecl     = "component:operation" , Identifier , OperationBody ;
QualifiedName     = Identifier , ( "." , Identifier )* ;
SchemaBody        = "{" , DeclarationStatement* , "}" ;
ComponentBody     = "{" , ComponentStatement* , "}" ;
BoardBody         = "{" , DeclarationStatement* , "}" ;
OperationBody     = "{" , DeclarationStatement* , "}" ;
DeclarationStatement = Identifier , ArgumentList? , ";" ;
ComponentStatement = ConnectStatement | DeclarationStatement ;
ConnectStatement   = "connect" , Reference , "->" , Reference , ";" ;
ArgumentList      = Value , ( "," , Value )* ;
Value             = Integer | String | Boolean | Reference | Array | Object ;
Reference         = Identifier , ( "." , Identifier | "@" , Integer )* ;
Array             = "[" , ( Value , ( "," , Value )* )? , "]" ;
Object            = "{" , ( String , ":" , Value , ( "," , String , ":" , Value )* )? , "}" ;
```

`DeclarationStatement` is intentionally generic. Its keyword and argument
shape are allowed only when the governing Schema permits them.

## Core example

```component
use standard.digital as std;
component:component AdderLab {
  device U1, std.74HC283;
  connect Input.A -> U1.A;
  probe U1.S;
}
component:operation TestAdder {
  inject AdderLab.Input.A, 3;
  inject AdderLab.Input.B, 5;
  probe AdderLab.U1.S;
}
```

`component:board` is syntactically reserved but semantically deferred; see
the non-goal boundary in [00_Manifesto.md](00_Manifesto.md).
