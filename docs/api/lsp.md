# Language Server Protocol (LSP) API Reference

This document provides a complete API reference for the doctk Language Server implementation.

## Overview

The doctk Language Server provides intelligent code completion, syntax validation, hover documentation, and AI-friendly features for the doctk DSL. It implements the Language Server Protocol (LSP) standard for editor integration.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    VS Code Extension                      │
│                  (TypeScript Client)                      │
└───────────────────────┬──────────────────────────────────┘
                        │
                        │ JSON-RPC over stdio
                        │
┌───────────────────────▼──────────────────────────────────┐
│              DoctkLanguageServer                          │
│                  (Python Server)                          │
│                                                           │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │  Registry   │  │  Completion  │  │     Hover      │  │
│  │             │  │   Provider   │  │   Provider     │  │
│  └─────────────┘  └──────────────┘  └────────────────┘  │
│                                                           │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ AI Support  │  │   Config     │  │  Diagnostics   │  │
│  │             │  │              │  │                │  │
│  └─────────────┘  └──────────────┘  └────────────────┘  │
└───────────────────────────────────────────────────────────┘
```

## Core Components

### DoctkLanguageServer

The main language server class that coordinates all LSP features.

**Location:** `src/doctk/lsp/server.py`

```python
from doctk.lsp.server import DoctkLanguageServer

# Initialize server
server = DoctkLanguageServer()

# The server automatically registers handlers for:
# - textDocument/didOpen
# - textDocument/didChange
# - textDocument/didClose
# - textDocument/completion
# - textDocument/hover
# - textDocument/signatureHelp
# - textDocument/documentSymbol
# - workspace/didChangeConfiguration
```

**Key Methods:**

- `validate_syntax(text: str) -> list[Diagnostic]` - Validate DSL syntax
- `provide_signature_help(text: str, position: Position) -> SignatureHelp | None` - Get signature help
- `extract_document_symbols(text: str) -> list[DocumentSymbol]` - Extract document symbols

### OperationRegistry

Central registry for all doctk operations with metadata.

**Location:** `src/doctk/lsp/registry.py`

```python
from doctk.lsp.registry import OperationRegistry

registry = OperationRegistry()

# Get all operations
operations = registry.get_all_operations()

# Get specific operation
select_op = registry.get_operation("select")

# Search operations
search_results = registry.search_operations("head")
```

**Key Methods:**

- `get_operation(name: str) -> OperationMetadata | None` - Get operation metadata
- `get_all_operations() -> list[OperationMetadata]` - Get all operations
- `search_operations(query: str) -> list[OperationMetadata]` - Search operations
- `get_operations_by_category(category: str) -> list[OperationMetadata]` - Filter by category

**OperationMetadata Structure:**

```python
@dataclass
class OperationMetadata:
    name: str                          # Operation name
    description: str                   # Human-readable description
    parameters: list[ParameterInfo]    # Parameter information
    return_type: str                   # Return type
    examples: list[str]                # Usage examples
    category: str                      # Category (selection, structure, etc.)
```

### CompletionProvider

Provides intelligent code completion suggestions.

**Location:** `src/doctk/lsp/completion.py`

```python
from doctk.lsp.completion import CompletionProvider
from lsprotocol.types import Position

provider = CompletionProvider(registry)

# Get completions at cursor position
text = "doc | "
position = Position(line=0, character=6)
completions = provider.provide_completions(text, position)

# Access completion items
for item in completions.items:
    print(f"{item.label}: {item.detail}")
```

**Features:**

- Context-aware completions (after pipe, in operation, etc.)
- Operation suggestions with descriptions
- Parameter completions
- Caching with TTL (default: 5 seconds)
- Performance: < 200ms response time

**CompletionContext Enum:**

- `START_OF_LINE` - Beginning of line
- `AFTER_PIPE` - After `|` operator
- `IN_OPERATION` - Inside operation parameters
- `UNKNOWN` - Unknown context

### HoverProvider

Provides hover documentation for operations and parameters.

**Location:** `src/doctk/lsp/hover.py`

```python
from doctk.lsp.hover import HoverProvider
from lsprotocol.types import Position

provider = HoverProvider(registry)

# Get hover information
text = "doc | select heading"
position = Position(line=0, character=8)  # On "select"
hover = provider.provide_hover(text, position)

if hover:
    print(hover.contents)
```

**Features:**

- Operation documentation with examples
- Parameter documentation
- Type information
- Caching with TTL (default: 5 seconds)
- Performance: < 200ms response time

### AIAgentSupport

Provides structured information for AI agents.

**Location:** `src/doctk/lsp/ai_support.py`

```python
from doctk.lsp.ai_support import AIAgentSupport

ai_support = AIAgentSupport(registry)

# Get complete operation catalog
catalog = ai_support.get_operation_catalog()
# Returns: dict[str, dict[str, Any]]

# Get structured documentation for specific operation
docs = ai_support.get_structured_docs("select")
# Returns: StructuredDocumentation dataclass
```

**StructuredDocumentation:**

```python
@dataclass
class StructuredDocumentation:
    operation: str                              # Operation name
    summary: str                                # Brief summary
    description: str                            # Full description
    parameters: list[dict[str, Any]]            # Parameter details
    returns: dict[str, str]                     # Return type and description
    examples: list[dict[str, str]]              # Code examples with descriptions
    related_operations: list[str]               # Related operations
    category: str                               # Operation category
```

### LSPConfiguration

Configuration settings for the language server.

**Location:** `src/doctk/lsp/config.py`

```python
from doctk.lsp.config import LSPConfiguration, TraceLevel

config = LSPConfiguration()

# Access settings
print(config.trace)                    # TraceLevel.OFF
print(config.max_completion_items)     # 50
print(config.enabled)                  # True

# Update configuration
config.update_from_dict({
    "trace": "verbose",
    "maxCompletionItems": 100
})

# Configuration persists across operations
```

**TraceLevel Enum:**

- `OFF` - No tracing
- `MESSAGES` - Log messages only
- `VERBOSE` - Detailed tracing

**Configuration Fields:**

- `trace: TraceLevel` - LSP trace level (default: OFF)
- `max_completion_items: int` - Max completion items (default: 50)
- `enabled: bool` - Enable/disable LSP (default: True)
- `python_command: str` - Python command (default: "python3")

## Usage Examples

### Basic Server Setup

```python
from doctk.lsp.server import DoctkLanguageServer

# Initialize server
server = DoctkLanguageServer()

# Server is ready to handle LSP requests
# Handlers are automatically registered
```

### Syntax Validation

```python
from doctk.lsp.server import DoctkLanguageServer

server = DoctkLanguageServer()

# Validate DSL syntax
text = "doc | select heading | promote"
diagnostics = server.validate_syntax(text)

if len(diagnostics) == 0:
    print("✓ Syntax is valid")
else:
    for diag in diagnostics:
        print(f"Error at line {diag.range.start.line}: {diag.message}")
```

### Code Completion

```python
from doctk.lsp.server import DoctkLanguageServer
from lsprotocol.types import Position

server = DoctkLanguageServer()

# Get completions after typing "doc | "
text = "doc | "
position = Position(line=0, character=6)

completions = server.completion_provider.provide_completions(text, position)

print(f"Found {len(completions.items)} completion suggestions:")
for item in completions.items:
    print(f"  - {item.label}: {item.detail}")
```

### Hover Documentation

```python
from doctk.lsp.server import DoctkLanguageServer
from lsprotocol.types import Position

server = DoctkLanguageServer()

# Get hover info when cursor is on "select"
text = "doc | select heading"
position = Position(line=0, character=8)

hover = server.hover_provider.provide_hover(text, position)

if hover:
    print("Hover Documentation:")
    print(hover.contents)
```

### AI Agent Integration

```python
from doctk.lsp.server import DoctkLanguageServer

server = DoctkLanguageServer()

# Get operation catalog for AI
catalog = server.ai_support.get_operation_catalog()

print(f"Available operations: {len(catalog)}")
for op_name, op_info in catalog.items():
    print(f"  - {op_name}: {op_info['description']}")

# Get detailed docs for specific operation
docs = server.ai_support.get_structured_docs("select")
print(f"\nOperation: {docs.operation}")
print(f"Summary: {docs.summary}")
print(f"Examples:")
for example in docs.examples:
    print(f"  {example['code']}")
```

## Performance Characteristics

All LSP features meet strict performance requirements:

| Feature | Requirement | Typical Performance |
|---------|-------------|---------------------|
| Server initialization | < 2 seconds | ~0.5 seconds |
| Completion | < 200ms | 5-50ms |
| Hover | < 200ms | 5-30ms |
| Syntax validation | < 500ms | 10-100ms |
| Document symbols | < 500ms | 20-80ms |

## Error Handling

The language server implements comprehensive error recovery:

- **Parsing errors**: Returns partial diagnostics with available information
- **Invalid positions**: Returns None gracefully (no crashes)
- **Configuration errors**: Falls back to default values
- **Resource errors**: Logs detailed diagnostics for troubleshooting

## Extension Points

### Adding New Operations

Operations are automatically discovered from the `doctk.operations` module. To add a new operation:

1. Implement the operation in `src/doctk/operations.py`
2. Add type hints and docstring
3. The registry will automatically discover it on server startup

```python
def my_new_operation(param: str) -> Operation:
    """
    Description of my operation.

    Args:
        param: Parameter description

    Returns:
        Document transformation

    Example:
        >>> doc | my_new_operation("value")
    """
    def transform(doc: Document) -> Document:
        # Implementation
        return doc
    return transform
```

### Custom Completion Providers

Extend `CompletionProvider` to add custom completion logic:

```python
from doctk.lsp.completion import CompletionProvider

class CustomCompletionProvider(CompletionProvider):
    def _custom_completions(self, analysis):
        # Add custom completion logic
        return []
```

### Custom Hover Providers

Extend `HoverProvider` to customize hover information:

```python
from doctk.lsp.hover import HoverProvider

class CustomHoverProvider(HoverProvider):
    def _create_custom_hover(self, word):
        # Add custom hover logic
        return None
```

## Testing

The LSP includes comprehensive test coverage:

- **Unit tests**: Test individual components in isolation
- **E2E tests**: Test complete LSP workflows
- **Performance tests**: Verify response time requirements

Run LSP tests:

```bash
# Run all LSP tests
uv run pytest tests/unit/test_lsp*.py tests/e2e/test_lsp*.py -v

# Run specific test
uv run pytest tests/unit/test_lsp_server.py::test_completion -v

# Run with coverage
uv run pytest tests/unit/test_lsp*.py --cov=src/doctk/lsp
```

## See Also

- [DSL API Reference](./dsl.md) - doctk DSL language specification
- [Core Integration API](./core-integration.md) - Integration layer documentation
