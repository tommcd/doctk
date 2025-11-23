# DSL API Reference

**Module**: `doctk.dsl`
**Version**: 0.2.0
**Status**: Stable

## Overview

The doctk DSL (Domain-Specific Language) provides a pipeline-based syntax for document manipulation. The DSL supports:

- **Pipeline Operations**: Chain operations using `|` operator
- **REPL**: Interactive command-line interface
- **Script Execution**: Run `.tk` script files
- **Code Block Execution**: Execute DSL code blocks in Markdown files
- **Variable Assignment**: Store intermediate results

## DSL Syntax

### Basic Pipeline

```doctk
doc | promote h2-0
```

### Chained Operations

```doctk
doc | promote h2-0 | demote h3-1 | nest h2-2 h1-0
```

### Variable Assignment

```doctk
let updated = doc | promote h2-0
updated | move_up h2-1
```

### Operations

| Operation | Syntax | Description |
|-----------|--------|-------------|
| `promote` | `promote <node_id>` | Decrease heading level (h3 → h2) |
| `demote` | `demote <node_id>` | Increase heading level (h2 → h3) |
| `move_up` | `move_up <node_id>` | Move section up among siblings |
| `move_down` | `move_down <node_id>` | Move section down among siblings |
| `nest` | `nest <node_id> <under_id>` | Nest section under another |
| `unnest` | `unnest <node_id>` | Un-nest section to parent level |

______________________________________________________________________

## Module Structure

```
src/doctk/dsl/
├── __init__.py       # Public API exports
├── lexer.py          # Tokenization
├── parser.py         # AST generation
├── executor.py       # DSL execution
├── repl.py           # Interactive REPL
└── codeblock.py      # Markdown code block execution
```

______________________________________________________________________

## Core Classes

### Lexer

**Location**: `doctk.dsl.lexer.Lexer`

Tokenizes DSL source code into tokens.

#### Constructor

```python
Lexer(source: str)
```

**Parameters:**

- `source`: DSL source code to tokenize

#### Methods

##### `tokenize() -> list[Token]`

Tokenize the source code.

**Returns:** List of Token objects

**Raises:** `LexerError` if invalid syntax is encountered

**Example:**

```python
from doctk.dsl.lexer import Lexer

lexer = Lexer("doc | promote h2-0")
tokens = lexer.tokenize()

for token in tokens:
    print(f"{token.type.name}: {token.value}")
```

#### Token Types

```python
class TokenType(Enum):
    # Literals
    IDENTIFIER = auto()    # Variable or operation name
    STRING = auto()        # "text" or 'text'
    NUMBER = auto()        # 123, 3.14
    BOOLEAN = auto()       # true, false

    # Operators
    PIPE = auto()          # |
    EQUALS = auto()        # =
    NOT_EQUALS = auto()    # !=
    GREATER = auto()       # >
    LESS = auto()          # <
    GREATER_EQUAL = auto() # >=
    LESS_EQUAL = auto()    # <=
    TILDE_EQUALS = auto()  # ~= (regex match)
    CARET_EQUALS = auto()  # ^= (starts with)
    DOLLAR_EQUALS = auto() # $= (ends with)
    STAR_EQUALS = auto()   # *= (contains)

    # Keywords
    LET = auto()           # let
    DOC = auto()           # doc
    WHERE = auto()         # where
    SELECT = auto()        # select
    TRUE = auto()          # true
    FALSE = auto()         # false

    # Delimiters
    LPAREN = auto()        # (
    RPAREN = auto()        # )
    COMMA = auto()         # ,
    NEWLINE = auto()       # Line break
    EOF = auto()           # End of file
```

______________________________________________________________________

### Parser

**Location**: `doctk.dsl.parser.Parser`

Parses tokens into an Abstract Syntax Tree (AST).

#### Constructor

```python
Parser(tokens: list[Token])
```

**Parameters:**

- `tokens`: List of tokens from Lexer

#### Methods

##### `parse() -> list[ASTNode]`

Parse tokens into AST.

**Returns:** List of AST nodes (statements)

**Raises:** `ParseError` if syntax is invalid

**Example:**

```python
from doctk.dsl.lexer import Lexer
from doctk.dsl.parser import Parser

lexer = Lexer("doc | promote h2-0")
tokens = lexer.tokenize()

parser = Parser(tokens)
ast = parser.parse()

for node in ast:
    print(f"Statement: {type(node).__name__}")
```

#### AST Node Types

```python
@dataclass
class Pipeline:
    """Pipeline expression: source | op1 | op2"""
    source: str
    operations: list[FunctionCall]

@dataclass
class FunctionCall:
    """Function call: name(arg1, arg2, key1=val1)"""
    name: str
    args: list[Any]  # Positional arguments
    kwargs: dict[str, Any]  # Keyword arguments

@dataclass
class Assignment:
    """Variable assignment: let var = pipeline"""
    variable: str
    pipeline: Pipeline
```

______________________________________________________________________

### Executor

**Location**: `doctk.dsl.executor.Executor`

Executes AST against documents.

#### Constructor

```python
Executor(document: Document[Any])
```

**Parameters:**

- `document`: Initial document to operate on

#### Methods

##### `execute(ast: list[ASTNode]) -> Document[Any]`

Execute AST statements.

**Parameters:**

- `ast`: List of AST nodes from Parser

**Returns:** Resulting document after executing all statements

**Raises:** `ExecutionError` if execution fails

**Example:**

```python
from doctk import Document
from doctk.dsl.lexer import Lexer
from doctk.dsl.parser import Parser
from doctk.dsl.executor import Executor

# Load document
doc = Document.from_file("example.md")

# Parse DSL
lexer = Lexer("doc | promote h2-0 | demote h3-1")
tokens = lexer.tokenize()
parser = Parser(tokens)
ast = parser.parse()

# Execute
executor = Executor(doc)
result_doc = executor.execute(ast)

# Save result
result_doc.to_file("output.md")
```

______________________________________________________________________

### REPL

**Location**: `doctk.dsl.repl.DoctkREPL`

Interactive Read-Eval-Print Loop for DSL.

#### Constructor

```python
DoctkREPL()
```

#### Methods

##### `run() -> None`

Start the REPL (blocks until user exits).

**Example:**

```python
from doctk.dsl.repl import DoctkREPL

repl = DoctkREPL()
repl.run()  # Interactive session
```

#### REPL Commands

| Command | Description | Example |
|---------|-------------|---------|
| `load <file>` | Load a document | `load example.md` |
| `save <file>` | Save current document | `save output.md` |
| `tree` | Show document tree | `tree` |
| `list` | List all nodes | `list` |
| `help` | Show help | `help` |
| `exit` | Exit REPL | `exit` |
| *operation* | Execute operation | `promote h2-0` |

**Session Example:**

```
doctk> load example.md
Loaded document with 45 nodes

doctk> tree
Document
├── h1-0: Introduction
│   ├── h2-0: Overview
│   └── h2-1: Goals

doctk> promote h2-0
Operation successful

doctk> save output.md
Saved to output.md

doctk> exit
Goodbye!
```

______________________________________________________________________

### ScriptExecutor

**Location**: `doctk.dsl.executor.ScriptExecutor`

Execute DSL scripts from files.

#### Static Methods

##### `execute_file(script_path: str | Path, document_path: str | Path) -> Document[Any]`

Execute a script file on a document.

**Note:** This is an **instance method** - you must create a `ScriptExecutor` first.

**Parameters:**

- `script_path`: Path to `.tk` script file
- `document_path`: Path to document to transform

**Returns:** Resulting document

**Raises:** `ExecutionError` if execution fails

**Example:**

```python
from pathlib import Path
from doctk import Document
from doctk.dsl.executor import ScriptExecutor

# Create executor (needs a document)
doc = Document.from_file("example.md")
executor = ScriptExecutor(doc)

# Execute script file on a document
result = executor.execute_file(
    script_path=Path("script.tk"),
    document_path=Path("example.md")
)

result.to_file("output.md")
```

**Script File Example** (`script.tk`):

```doctk
# Promote all h2 headings
doc | promote h2-0 | promote h2-1 | promote h2-2

# Nest a section
doc | nest h2-3 h1-0
```

##### `execute_file_and_save(script_path, doc_path, output_path) -> None`

Execute script and save result (convenience method).

**Parameters:**

- `script_path`: Path to script file
- `doc_path`: Path to input document
- `output_path`: Path to save result

**Example:**

```python
ScriptExecutor.execute_file_and_save(
    script_path="transform.tk",
    doc_path="input.md",
    output_path="output.md"
)
```

______________________________________________________________________

### CodeBlockExecutor

**Location**: `doctk.dsl.codeblock.CodeBlockExecutor`

Execute DSL code blocks in Markdown documents.

#### Constructor

```python
CodeBlockExecutor(document: Document[Any])
```

#### Methods

##### `find_code_blocks(markdown_text: str) -> list[CodeBlock]`

Find all doctk code blocks in Markdown.

**Parameters:**

- `markdown_text`: Markdown source text

**Returns:** List of CodeBlock objects

**Example:**

````python
from doctk.dsl.codeblock import CodeBlockExecutor

markdown = '''
# Document

Some text.

```doctk
doc | promote h2-0
````

More text.

```doctk
doc | nest h2-1 h1-0
```

'''

executor = CodeBlockExecutor(doc)
blocks = executor.find_code_blocks(markdown)
print(f"Found {len(blocks)} doctk code blocks")

````

##### `execute_block(code_block: CodeBlock) -> Document[Any]`

Execute a single code block.

**Parameters:**
- `code_block`: CodeBlock to execute

**Returns:** Resulting document

##### `execute_all_blocks(markdown_text: str) -> Document[Any]`

Execute all code blocks sequentially.

**Parameters:**
- `markdown_text`: Markdown source with doctk code blocks

**Returns:** Document after executing all blocks

**Example:**
```python
# Execute all blocks in a Markdown file
with open("document.md") as f:
    markdown = f.read()

doc = Document.from_file("input.md")
executor = CodeBlockExecutor(doc)
result = executor.execute_all_blocks(markdown)
result.to_file("output.md")
````

##### `execute_file(markdown_path, block_index=0) -> Document`

Execute a specific code block from a Markdown file.

**Note:** This is an **instance method** - you must create a `CodeBlockExecutor` with a document first.

**Parameters:**

- `markdown_path`: Path to Markdown file with code blocks
- `block_index`: Index of code block to execute (0-based, default: 0)

**Returns:** Resulting document

**Example:**

```python
from pathlib import Path
from doctk import Document
from doctk.dsl.codeblock import CodeBlockExecutor

# Load the document to transform
doc = Document.from_file("document.md")

# Create executor
executor = CodeBlockExecutor(doc)

# Execute specific block (index 0)
result = executor.execute_file(
    markdown_path=Path("instructions.md"),
    block_index=0
)

# Execute all blocks sequentially (using execute_all_blocks)
markdown_text = Path("instructions.md").read_text()
result = executor.execute_all_blocks(markdown_text)
```

______________________________________________________________________

## Data Types

### Token

**Location**: `doctk.dsl.lexer.Token`

A token produced by the lexer.

**Fields:**

- `type: TokenType` - Token type
- `value: str` - Token value
- `line: int` - Line number (1-indexed)
- `column: int` - Column number (1-indexed)

### CodeBlock

**Location**: `doctk.dsl.codeblock.CodeBlock`

A doctk code block found in Markdown.

**Fields:**

- `code: str` - DSL code content
- `line_number: int` - Starting line in Markdown

______________________________________________________________________

## Error Handling

### LexerError

Raised when tokenization fails due to invalid characters or syntax.

**Attributes:**

- `message: str` - Error description
- `line: int | None` - Line number
- `column: int | None` - Column number

**Example:**

```python
from doctk.dsl.lexer import Lexer, LexerError

try:
    lexer = Lexer("doc | @invalid")
    tokens = lexer.tokenize()
except LexerError as e:
    print(f"Lexer error at line {e.line}, column {e.column}: {e.message}")
```

### ParseError

Raised when parsing fails due to invalid syntax.

**Attributes:**

- `message: str` - Error description
- `token: Token` - Token where error occurred

**Example:**

```python
from doctk.dsl.parser import Parser, ParseError

try:
    parser = Parser(tokens)
    ast = parser.parse()
except ParseError as e:
    print(f"Parse error at line {e.token.line}: {e.message}")
```

### ExecutionError

Raised when DSL execution fails.

**Attributes:**

- `message: str` - Error description
- `line: int | None` - Line number in script
- `column: int | None` - Column number in script

**Example:**

```python
from doctk.dsl.executor import Executor, ExecutionError

try:
    executor = Executor(doc)
    result = executor.execute(ast)
except ExecutionError as e:
    print(f"Execution error at line {e.line}: {e.message}")
```

______________________________________________________________________

## CLI Integration

The DSL can be executed via the doctk CLI:

### Execute Script File

```bash
uv run doctk execute script.tk document.md -o output.md
```

### Execute Code Block

```bash
uv run doctk execute-block instructions.md document.md --block 0
```

### Start REPL

```bash
uv run doctk repl
```

______________________________________________________________________

## Usage Examples

### End-to-End Pipeline

```python
from doctk import Document
from doctk.dsl.lexer import Lexer
from doctk.dsl.parser import Parser
from doctk.dsl.executor import Executor

# 1. Load document
doc = Document.from_file("example.md")

# 2. Define DSL script
script = """
doc | promote h2-0 | promote h2-1
doc | nest h2-2 h1-0
"""

# 3. Lex + Parse + Execute
lexer = Lexer(script)
tokens = lexer.tokenize()

parser = Parser(tokens)
ast = parser.parse()

executor = Executor(doc)
result = executor.execute(ast)

# 4. Save result
result.to_file("output.md")
```

### REPL Usage

```python
from doctk.dsl.repl import DoctkREPL

# Start interactive session
repl = DoctkREPL()
repl.run()
```

### Script File Execution

```python
from pathlib import Path
from doctk import Document
from doctk.dsl.executor import ScriptExecutor

# Create executor
doc = Document.from_file("input.md")
executor = ScriptExecutor(doc)

# Execute script file
result = executor.execute_file(
    script_path=Path("transform.tk"),
    document_path=Path("input.md")
)
result.to_file("output.md")
```

### Code Block Execution

```python
from pathlib import Path
from doctk import Document
from doctk.dsl.codeblock import CodeBlockExecutor

# Load document
doc = Document.from_file("document.md")

# Create executor and execute code blocks
executor = CodeBlockExecutor(doc)

# Execute specific block
result = executor.execute_file(Path("instructions.md"), block_index=0)
result.to_file("transformed.md")

# Or execute all blocks sequentially
markdown_text = Path("instructions.md").read_text()
result = executor.execute_all_blocks(markdown_text)
result.to_file("transformed.md")
```

______________________________________________________________________

## Performance Characteristics

### Lexer

- **Time Complexity**: O(n) where n = source length
- **Space Complexity**: O(t) where t = number of tokens

### Parser

- **Time Complexity**: O(t) where t = number of tokens
- **Space Complexity**: O(a) where a = AST size

### Executor

- **Time Complexity**: O(a × d) where a = AST size, d = document size
- **Space Complexity**: O(d) for document copies (immutability)

______________________________________________________________________

## Language Grammar

### EBNF Grammar

```ebnf
program        = { statement } ;
statement      = assignment | pipeline ;
assignment     = "let" identifier "=" pipeline ;
pipeline       = source { "|" operation } ;
source         = "doc" | identifier ;
operation      = identifier { argument } ;
argument       = identifier | number | string ;
identifier     = letter { letter | digit | "_" | "-" } ;
number         = digit { digit } ;
string         = '"' { character } '"' ;
```

### Precedence Rules

1. `let` bindings (lowest)
1. `|` pipeline operator
1. Function calls (highest)

______________________________________________________________________

## Extension Points

### Adding New Operations

To add a new DSL operation:

1. **Add to StructureOperations** in `integration/operations.py`
1. **Add to Executor dispatch table** in `dsl/executor.py`
1. **Update this documentation**

**Example:**

```python
# In Executor.__init__
self._operation_dispatch = {
    # ... existing operations ...
    "my_operation": (self._exec_my_operation, 1),  # 1 argument
}

def _exec_my_operation(self, node_id: str) -> Document[Any]:
    """Execute my_operation."""
    result = self.operations.my_operation(self.document, node_id)
    if not result.success:
        raise ExecutionError(result.error or "Operation failed")
    return Document.from_string(result.document)
```

______________________________________________________________________

## Testing

See `tests/unit/test_dsl_*.py` for comprehensive test examples:

- Lexer tests: Token generation, error handling
- Parser tests: AST generation, syntax errors
- Executor tests: Operation execution, variable binding
- REPL tests: Command handling, state management
- Script execution tests: File execution, error reporting
- Code block tests: Block detection, sequential execution

Run tests:

```bash
uv run pytest tests/unit/test_dsl*.py     # All DSL tests
uv run pytest tests/e2e/test_script*.py   # E2E script tests
```

______________________________________________________________________

## See Also

- [Core Integration API](./core-integration.md)
- [LSP API Reference](./lsp.md)
- Pluggable Architecture (see `docs/design/02-pluggable-architecture.md` in repository)
- [CLI Documentation](../getting-started/quick-start.md)
