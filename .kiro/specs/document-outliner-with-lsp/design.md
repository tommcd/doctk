# Design Document: Document Outliner with LSP

## Overview

This design document outlines a phased approach to implementing document outliner and LSP capabilities for doctk. The implementation is split into phases, with Phase 1 focusing on the foundational Python components that enable DSL execution, REPL interaction, and core document operations.

Future phases will add the VS Code extension, LSP server, and visual outliner interface.

## Architecture

### High-Level Structure

```
doctk/
├── src/doctk/
│   ├── dsl/                    # NEW: DSL parser and execution engine
│   │   ├── __init__.py
│   │   ├── lexer.py            # Tokenize DSL syntax
│   │   ├── parser.py           # Parse tokens into AST
│   │   ├── executor.py         # Execute DSL commands
│   │   └── repl.py             # Interactive REPL
│   ├── operations.py           # ENHANCED: Add lift, lower, nest, unnest
│   ├── core.py
│   ├── cli.py                  # ENHANCED: Add repl and run commands
│   └── ...
├── tests/
│   ├── unit/dsl/               # NEW: DSL unit tests
│   ├── e2e/                    # ENHANCED: Add DSL e2e tests
│   └── ...
├── examples/
│   ├── sample.md
│   └── transformations/        # NEW: Example .tk scripts
│       ├── promote-h3.tk
│       ├── nest-sections.tk
│       └── reorder-toc.tk
└── docs/
    ├── user-guide/
    │   └── dsl-reference.md    # NEW: DSL documentation
    └── ...
```

## Phase 1: Core DSL and Execution Engine (Current Spec)

Phase 1 establishes the foundation by implementing:

1. **DSL Syntax Parser** - Parse doctk operation syntax
2. **Structure Operations** - lift, lower, nest, unnest operations
3. **DSL Executor** - Execute parsed DSL commands on documents
4. **REPL** - Interactive command-line interface
5. **Script Execution** - Run .tk files with DSL commands
6. **CLI Integration** - Add `repl` and `run` commands

### 1. DSL Syntax

#### 1.1 DSL Grammar

The doctk DSL uses a pipe-based syntax similar to Unix pipes:

```
# Basic selection and transformation
doc | select heading | where level=3 | promote

# Multiple filters
doc | select heading | where level>2 | where text~="Introduction" | demote

# Structure operations
doc | select heading | where level=2 | lift
doc | select paragraph | where text~="Note:" | nest under previous

# Composition
let promoted = doc | select heading | where level=3 | promote
promoted | where text~="API" | demote
```

**Grammar (EBNF)**:

```ebnf
program      ::= statement+
statement    ::= assignment | pipeline
assignment   ::= "let" IDENTIFIER "=" pipeline
pipeline     ::= source ("|" operation)*
source       ::= "doc" | IDENTIFIER
operation    ::= function_call | method_call
function_call ::= IDENTIFIER ("(" arguments ")")?
arguments    ::= argument ("," argument)*
argument     ::= IDENTIFIER "=" value | value
value        ::= STRING | NUMBER | BOOLEAN | IDENTIFIER
method_call  ::= IDENTIFIER
```

**Examples**:

```doctk
# Simple pipeline
doc | select heading | promote

# With arguments
doc | select heading | where level=3

# With string matching
doc | where text~="Introduction"

# Variable assignment
let headings = doc | select heading
headings | where level=2 | promote
```

#### 1.2 Supported Operations

**Selection Operations**:
- `select <type>` - Select nodes of specific type (heading, paragraph, list, etc.)
- `where <condition>` - Filter nodes by condition

**Transformation Operations**:
- `promote` - Decrease heading level (h3 → h2)
- `demote` - Increase heading level (h2 → h3)
- `lift` - Move section up in hierarchy (sibling of parent)
- `lower` - Move section down in hierarchy (child of previous sibling)
- `nest under <target>` - Nest section under target
- `unnest` - Remove one level of nesting

**Utility Operations**:
- `count` - Count nodes
- `first <n>` - Take first n nodes
- `last <n>` - Take last n nodes

#### 1.3 Condition Syntax

**Comparison Operators**:
- `=` - Equality
- `!=` - Inequality
- `>`, `<`, `>=`, `<=` - Numeric comparison

**Text Matching**:
- `~=` - Regex match
- `^=` - Starts with
- `$=` - Ends with
- `*=` - Contains

**Examples**:
```
where level=3
where level>2
where text~="Introduction"
where text^="Chapter"
```

### 2. Structure Operations

#### 2.1 Lift Operation

**Purpose**: Move a section up in the hierarchy (make it a sibling of its parent)

**Before**:
```
# Chapter 1
## Section 1.1
### Subsection 1.1.1
```

**After `doc | select heading | where level=3 | lift`**:
```
# Chapter 1
## Section 1.1
## Subsection 1.1.1  (promoted from h3 to h2, became sibling of parent)
```

**Implementation**:
```python
def lift() -> Operation:
    """Move section up in hierarchy (sibling of parent)."""
    def transform(doc: Document) -> Document:
        result_nodes = []
        for node in doc.nodes:
            if isinstance(node, Heading):
                # Decrease level (promote) and maintain sibling relationship
                result_nodes.append(node.promote())
            else:
                result_nodes.append(node)
        return Document(nodes=result_nodes)
    return transform
```

#### 2.2 Lower Operation

**Purpose**: Move a section down in the hierarchy (make it a child of the previous sibling)

**Before**:
```
## Section 1
## Section 2
```

**After `doc | select heading | where text="Section 2" | lower`**:
```
## Section 1
### Section 2  (demoted from h2 to h3, became child of previous sibling)
```

**Implementation**:
```python
def lower() -> Operation:
    """Move section down in hierarchy (child of previous sibling)."""
    def transform(doc: Document) -> Document:
        result_nodes = []
        for node in doc.nodes:
            if isinstance(node, Heading):
                # Increase level (demote) to become child
                result_nodes.append(node.demote())
            else:
                result_nodes.append(node)
        return Document(nodes=result_nodes)
    return transform
```

#### 2.3 Nest Operation

**Purpose**: Nest selected sections under a target section

**Syntax**: `nest under <selector>`

**Example**:
```
doc | select heading | where level=2 | nest under (where text="Parent")
```

#### 2.4 Unnest Operation

**Purpose**: Remove one level of nesting

**Example**:
```
doc | select heading | where level=3 | unnest
```

### 3. DSL Parser

#### 3.1 Lexer

**Purpose**: Tokenize DSL source code into tokens

**Location**: `src/doctk/dsl/lexer.py`

**Token Types**:
```python
from enum import Enum, auto

class TokenType(Enum):
    # Literals
    IDENTIFIER = auto()  # variable names, operation names
    STRING = auto()      # "text"
    NUMBER = auto()      # 123, 3.14
    BOOLEAN = auto()     # true, false

    # Operators
    PIPE = auto()        # |
    EQUALS = auto()      # =
    TILDE = auto()       # ~

    # Keywords
    LET = auto()         # let
    DOC = auto()         # doc
    WHERE = auto()       # where
    SELECT = auto()      # select

    # Delimiters
    LPAREN = auto()      # (
    RPAREN = auto()      # )
    COMMA = auto()       # ,

    # Special
    EOF = auto()
    NEWLINE = auto()
```

**Lexer Class**:
```python
@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1

    def next_token(self) -> Token:
        """Get next token from source."""
        # Skip whitespace
        # Tokenize identifiers, strings, numbers, operators
        # Return Token
        ...

    def tokenize(self) -> list[Token]:
        """Tokenize entire source."""
        tokens = []
        while True:
            token = self.next_token()
            tokens.append(token)
            if token.type == TokenType.EOF:
                break
        return tokens
```

#### 3.2 Parser

**Purpose**: Parse tokens into Abstract Syntax Tree (AST)

**Location**: `src/doctk/dsl/parser.py`

**AST Node Types**:
```python
from dataclasses import dataclass
from abc import ABC, abstractmethod

class ASTNode(ABC):
    """Base class for AST nodes."""
    @abstractmethod
    def accept(self, visitor: "ASTVisitor") -> Any:
        pass

@dataclass
class Pipeline(ASTNode):
    source: "Source"
    operations: list["Operation"]

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_pipeline(self)

@dataclass
class Source(ASTNode):
    name: str  # "doc" or variable name

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_source(self)

@dataclass
class FunctionCall(ASTNode):
    name: str
    arguments: dict[str, Any]

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_function_call(self)

@dataclass
class Assignment(ASTNode):
    variable: str
    pipeline: Pipeline

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_assignment(self)
```

**Parser Class**:
```python
class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> list[ASTNode]:
        """Parse tokens into AST."""
        statements = []
        while not self.is_at_end():
            statements.append(self.parse_statement())
        return statements

    def parse_statement(self) -> ASTNode:
        """Parse a single statement."""
        if self.match(TokenType.LET):
            return self.parse_assignment()
        return self.parse_pipeline()

    def parse_pipeline(self) -> Pipeline:
        """Parse a pipeline expression."""
        source = self.parse_source()
        operations = []
        while self.match(TokenType.PIPE):
            operations.append(self.parse_operation())
        return Pipeline(source, operations)

    def parse_operation(self) -> FunctionCall:
        """Parse an operation (function call)."""
        name = self.consume(TokenType.IDENTIFIER)
        arguments = {}
        if self.match(TokenType.LPAREN):
            arguments = self.parse_arguments()
            self.consume(TokenType.RPAREN)
        return FunctionCall(name.value, arguments)
```

#### 3.3 Executor

**Purpose**: Execute parsed AST against documents

**Location**: `src/doctk/dsl/executor.py`

**Executor Class**:
```python
class Executor:
    def __init__(self, document: Document):
        self.document = document
        self.variables: dict[str, Document] = {"doc": document}

    def execute(self, ast: list[ASTNode]) -> Document:
        """Execute AST statements."""
        result = self.document
        for node in ast:
            if isinstance(node, Assignment):
                self.execute_assignment(node)
            elif isinstance(node, Pipeline):
                result = self.execute_pipeline(node)
        return result

    def execute_pipeline(self, pipeline: Pipeline) -> Document:
        """Execute a pipeline."""
        # Get source document
        doc = self.variables.get(pipeline.source.name, self.document)

        # Apply operations in sequence
        for op in pipeline.operations:
            operation_fn = self.get_operation(op.name, op.arguments)
            doc = operation_fn(doc)

        return doc

    def get_operation(self, name: str, args: dict[str, Any]) -> Operation:
        """Get operation function by name."""
        # Import from doctk.operations
        from doctk.operations import (
            select, where, promote, demote, lift, lower, nest, unnest
        )

        operation_map = {
            "select": lambda: select(self.get_predicate(args.get("type"))),
            "where": lambda: where(**args),
            "promote": lambda: promote(),
            "demote": lambda: demote(),
            "lift": lambda: lift(),
            "lower": lambda: lower(),
            "nest": lambda: nest(**args),
            "unnest": lambda: unnest(),
        }

        if name not in operation_map:
            raise ValueError(f"Unknown operation: {name}")

        return operation_map[name]()
```

### 4. REPL

#### 4.1 REPL Interface

**Purpose**: Provide interactive command-line interface for DSL

**Location**: `src/doctk/dsl/repl.py`

**REPL Class**:
```python
class REPL:
    def __init__(self):
        self.document: Document | None = None
        self.history: list[str] = []

    def start(self):
        """Start REPL loop."""
        console.print("[bold]doctk REPL[/bold]")
        console.print("Type 'help' for commands, 'exit' to quit\n")

        while True:
            try:
                # Read input
                line = input("doctk> ")
                if not line.strip():
                    continue

                # Handle special commands
                if line == "exit":
                    break
                elif line == "help":
                    self.show_help()
                    continue
                elif line.startswith("load "):
                    self.load_document(line[5:].strip())
                    continue
                elif line.startswith("save "):
                    self.save_document(line[5:].strip())
                    continue

                # Execute DSL command
                self.execute(line)

            except KeyboardInterrupt:
                console.print("\nUse 'exit' to quit")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

    def execute(self, source: str):
        """Execute DSL source."""
        if not self.document:
            console.print("[yellow]No document loaded. Use 'load <file>'[/yellow]")
            return

        # Parse and execute
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        executor = Executor(self.document)
        result = executor.execute(ast)

        # Update document
        self.document = result

        # Show result
        console.print(f"[green]✓[/green] Result: {len(result.nodes)} nodes")

    def load_document(self, path: str):
        """Load document from file."""
        self.document = Document.from_file(path)
        console.print(f"[green]✓[/green] Loaded {path}")

    def save_document(self, path: str):
        """Save document to file."""
        if not self.document:
            console.print("[yellow]No document to save[/yellow]")
            return
        self.document.to_file(path)
        console.print(f"[green]✓[/green] Saved to {path}")

    def show_help(self):
        """Show help message."""
        console.print("""
[bold]Commands:[/bold]
  load <file>     - Load a document
  save <file>     - Save the current document
  help            - Show this help
  exit            - Exit REPL

[bold]DSL Syntax:[/bold]
  doc | select heading | where level=3 | promote
  doc | select heading | where text~="Chapter" | demote
  let headings = doc | select heading
  headings | where level=2 | lift

[bold]Operations:[/bold]
  select <type>   - Select nodes by type
  where <cond>    - Filter by condition
  promote         - Decrease heading level
  demote          - Increase heading level
  lift            - Move up in hierarchy
  lower           - Move down in hierarchy
        """)
```

#### 4.2 CLI Integration

**Purpose**: Add REPL and script execution to CLI

**Location**: `src/doctk/cli.py`

**New Commands**:
```python
@app.command()
def repl() -> None:
    """
    Start interactive REPL for doctk commands.

    The REPL provides an interactive environment for experimenting
    with document transformations using the doctk DSL.
    """
    from doctk.dsl.repl import REPL

    repl = REPL()
    repl.start()

@app.command()
def run(
    script_path: str = typer.Argument(..., help="Path to .tk script file"),
    input_path: str = typer.Argument(..., help="Input document path"),
    output_path: str = typer.Option(None, "--output", "-o", help="Output path"),
) -> None:
    """
    Execute a .tk script file on a document.

    Args:
        script_path: Path to .tk file with DSL commands
        input_path: Path to input Markdown document
        output_path: Path to save output (default: overwrite input)
    """
    try:
        # Load document
        doc = Document.from_file(input_path)

        # Read script
        with open(script_path) as f:
            source = f.read()

        # Parse and execute
        from doctk.dsl.lexer import Lexer
        from doctk.dsl.parser import Parser
        from doctk.dsl.executor import Executor

        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        executor = Executor(doc)
        result = executor.execute(ast)

        # Save result
        output = output_path or input_path
        result.to_file(output)

        console.print(f"[green]✓[/green] Executed {script_path}")
        console.print(f"[green]✓[/green] Saved to {output}")

    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        raise typer.Exit(1)
```

### 5. Example Scripts

#### 5.1 promote-h3.tk

```doctk
# Promote all h3 headings to h2
doc | select heading | where level=3 | promote
```

#### 5.2 nest-sections.tk

```doctk
# Nest all "Note:" paragraphs under the previous heading
doc | select paragraph | where text^="Note:" | nest under previous
```

#### 5.3 reorder-toc.tk

```doctk
# Reorder table of contents
let toc = doc | select heading | where level=2
toc | where text~="Introduction" | lift
toc | where text~="Conclusion" | lower
```

## Phase 2: LSP Server (Future)

Phase 2 will implement the Language Server Protocol server:

1. **LSP Server** (TypeScript) - Implement language server
2. **Syntax Validation** - Real-time error checking
3. **Auto-Completion** - Context-aware suggestions
4. **Hover Documentation** - Inline help
5. **Signature Help** - Parameter hints

**Technologies**:
- TypeScript
- vscode-languageserver
- vscode-languageclient

## Phase 3: VS Code Extension (Future)

Phase 3 will implement the VS Code extension with outliner:

1. **Tree View** - Document structure visualization
2. **Drag-and-Drop** - Interactive restructuring
3. **Context Menu** - Operation shortcuts
4. **Inline Editing** - Edit headings in tree
5. **Keyboard Shortcuts** - Power user features
6. **Document Sync** - Bidirectional updates

**Technologies**:
- TypeScript
- VS Code Extension API
- Tree View API

## Data Models

### DSL AST Nodes

```python
@dataclass
class Pipeline(ASTNode):
    source: Source
    operations: list[FunctionCall]

@dataclass
class Source(ASTNode):
    name: str  # "doc" or variable name

@dataclass
class FunctionCall(ASTNode):
    name: str
    arguments: dict[str, Any]

@dataclass
class Assignment(ASTNode):
    variable: str
    pipeline: Pipeline
```

### Execution Context

```python
@dataclass
class ExecutionContext:
    document: Document
    variables: dict[str, Document]
    history: list[Document]  # For undo
```

## Error Handling

### Parse Errors

**Strategy**: Provide helpful error messages with line/column positions

**Example**:
```
Error at line 2, column 15:
  doc | select heading | where level=
                                     ^
Expected: value after '='
```

### Runtime Errors

**Strategy**: Catch exceptions and provide context

**Example**:
```
Runtime Error in 'where level=3':
  No nodes match the condition
```

### File Errors

**Strategy**: Validate file existence and format

**Example**:
```
Error: Cannot read file 'document.md'
  File does not exist
```

## Testing Strategy

### Unit Tests

**Scope**: Test individual DSL components

**Examples**:
- Test Lexer.tokenize() with various inputs
- Test Parser.parse() with valid/invalid syntax
- Test Executor.execute() with different operations
- Test lift/lower/nest/unnest operations

### E2E Tests

**Scope**: Test complete DSL workflows

**Examples**:
- Parse and execute complete .tk script
- Test REPL command execution
- Test CLI `run` command

### Integration Tests

**Scope**: Test DSL with real documents

**Examples**:
- Execute transformation on sample.md
- Verify output matches expected structure
- Test error handling with malformed documents

## Performance Considerations

### Parser Performance

**Optimization**: Use recursive descent parser (fast for simple grammars)

**Expected**: Parse 1000-line script in <100ms

### Executor Performance

**Optimization**: Apply operations in single pass where possible

**Expected**: Execute 100 operations on 1000-node document in <1s

### REPL Responsiveness

**Optimization**: Parse and execute immediately (no batching needed)

**Expected**: Execute simple command in <50ms

## Security Considerations

### Script Execution

**Risk**: Malicious .tk scripts could delete or modify important documents

**Mitigation**:
1. DSL is sandboxed (no system commands)
2. Only operates on specified input files
3. No automatic file writing without explicit output path
4. Preview mode available (--dry-run)

### Input Validation

**Risk**: Malformed documents could cause crashes

**Mitigation**:
1. Validate document format before parsing
2. Catch and handle parse errors gracefully
3. Limit document size to prevent memory exhaustion

## Future Enhancements

### Phase 1 Enhancements

- **Syntax Highlighting**: Add syntax highlighting for .tk files in editors
- **DSL Debugger**: Step through DSL execution
- **Performance Profiling**: Identify slow operations
- **Macro System**: Define reusable transformation patterns

### Phase 2: LSP Server

- **Real-time Validation**: Syntax errors as you type
- **Auto-Completion**: Context-aware suggestions
- **Refactoring**: Rename variables, extract pipelines
- **Code Formatting**: Auto-format DSL code

### Phase 3: VS Code Extension

- **Visual Outliner**: Tree view of document structure
- **Drag-and-Drop**: Interactive restructuring
- **Diff View**: Compare before/after transformations
- **Collaborative Editing**: Multi-user document editing

## Migration Path

### Phase 1 Implementation Plan

1. **Week 1**: DSL lexer and parser
   - Implement Lexer class
   - Implement Parser class
   - Write unit tests

2. **Week 2**: Structure operations
   - Implement lift/lower/nest/unnest
   - Write operation tests
   - Update operations.py

3. **Week 3**: DSL executor
   - Implement Executor class
   - Integrate with operations
   - Write e2e tests

4. **Week 4**: REPL and CLI
   - Implement REPL class
   - Add CLI commands
   - Write documentation

## References

- **Language Server Protocol**: https://microsoft.github.io/language-server-protocol/
- **VS Code Extension API**: https://code.visualstudio.com/api
- **Parser Combinators**: https://en.wikipedia.org/wiki/Parser_combinator
- **Abstract Syntax Tree**: https://en.wikipedia.org/wiki/Abstract_syntax_tree
- **REPL**: https://en.wikipedia.org/wiki/Read%E2%80%93eval%E2%80%93print_loop
