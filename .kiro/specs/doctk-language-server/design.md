# Design Document: doctk Language Server

## Overview

This design document describes the architecture and implementation approach for a Language Server Protocol (LSP) implementation for the doctk DSL. The language server provides intelligent code completion, validation, and documentation for doctk transformation scripts, ensuring that both human users and AI agents can effectively work with the doctk DSL.

The language server follows the LSP standard, ensuring compatibility with multiple editors and providing a well-tested communication layer. It offers real-time syntax validation, context-aware auto-completion, hover documentation, and structured information exposure for AI consumption.

### Design Principles

- **LSP Standard Compliance**: Full adherence to LSP protocol for editor compatibility
- **Performance**: Sub-200ms response times for completions and hover
- **Extensibility**: Dynamic operation loading from doctk core
- **AI-Friendly**: Structured information exposure for programmatic access
- **Resilience**: Graceful error handling and automatic recovery

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     VS Code Extension                        │
│                  ┌─────────────────────────┐                │
│                  │   Language Client       │                │
│                  │   (LSP Client)          │                │
│                  └──────────┬──────────────┘                │
└─────────────────────────────┼────────────────────────────────┘
                              │ JSON-RPC over stdio
                              │
                              ▼
                   ┌─────────────────────┐
                   │  Language Server    │
                   │  (Python Process)   │
                   └──────────┬──────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  DSL Parser  │    │  Operation   │    │  Completion  │
│  & Validator │    │  Registry    │    │  Provider    │
└──────────────┘    └──────────────┘    └──────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │  doctk Core API     │
                   └─────────────────────┘
```

### Component Responsibilities

#### Language Server (DoctkLanguageServer)

- Manages LSP lifecycle and communication
- Coordinates between parser, validator, and providers
- Maintains document state
- Handles error recovery

#### DSL Parser & Validator

- Parses doctk DSL syntax into AST
- Validates operations and arguments
- Generates diagnostic messages
- Supports partial parsing for error recovery

#### Operation Registry

- Dynamically loads operations from doctk core
- Maintains operation metadata (signatures, docs, examples)
- Provides operation lookup and search
- Supports AI agent queries

#### Completion Provider

- Analyzes cursor context
- Generates context-aware completions
- Caches results for performance
- Provides snippet support

#### Hover Provider

- Extracts documentation for operations
- Formats hover information
- Includes examples and type information

## Components and Interfaces

### Language Server Architecture

The language server is implemented using the `pygls` (Python Generic Language Server) library.

```python
from pygls.server import LanguageServer
from pygls.lsp.types import (
    CompletionParams, CompletionList, CompletionItem,
    Hover, HoverParams,
    Diagnostic, DiagnosticSeverity,
    DidOpenTextDocumentParams, DidChangeTextDocumentParams
)

class DoctkLanguageServer(LanguageServer):
    def __init__(self):
        super().__init__('doctk-lsp', 'v0.1.0')
        self.documents: Dict[str, DocumentState] = {}
        self.operation_registry = OperationRegistry()

    def parse_document(self, uri: str, text: str) -> DocumentState:
        """Parse doctk DSL and maintain document state."""
        pass

    def validate_syntax(self, uri: str) -> List[Diagnostic]:
        """Validate DSL syntax and return diagnostics."""
        pass
```

**Design Rationale**: `pygls` provides a robust foundation for LSP implementation with built-in support for all LSP features. It handles JSON-RPC communication, allowing us to focus on doctk-specific logic.

### Operation Registry

Maintains metadata about all available doctk operations.

```python
@dataclass
class OperationMetadata:
    name: str
    description: str
    parameters: List[ParameterInfo]
    return_type: str
    examples: List[str]
    category: str  # e.g., "structure", "selection", "transformation"

class OperationRegistry:
    def __init__(self):
        self.operations: Dict[str, OperationMetadata] = {}
        self._load_operations_from_doctk()

    def _load_operations_from_doctk(self):
        """Dynamically load operations from doctk core API."""
        # Introspect doctk module to discover operations
        pass

    def get_operation(self, name: str) -> Optional[OperationMetadata]:
        pass

    def get_completions(self, context: CompletionContext) -> List[CompletionItem]:
        pass
```

**Design Rationale**: Dynamic operation loading ensures the LSP automatically supports new operations added to doctk core without manual updates. This satisfies the integration requirement with doctk Core API.

### DSL Parser and Validator

```python
class DSLParser:
    def parse(self, text: str) -> ParseResult:
        """Parse doctk DSL into an AST."""
        pass

    def validate(self, ast: DSLNode) -> List[ValidationError]:
        """Validate AST against operation signatures."""
        pass

@dataclass
class ParseResult:
    ast: Optional[DSLNode]
    errors: List[ParseError]

@dataclass
class ValidationError:
    line: int
    column: int
    message: str
    severity: DiagnosticSeverity
```

**Design Rationale**: Separating parsing from validation allows for partial parsing when syntax errors exist, enabling better error recovery and more helpful diagnostics.

### Completion Provider

```python
class CompletionProvider:
    def __init__(self, registry: OperationRegistry):
        self.registry = registry

    def provide_completions(
        self,
        document: str,
        position: Position
    ) -> CompletionList:
        context = self._analyze_context(document, position)

        if context.after_pipe:
            return self._operation_completions(context)
        elif context.in_operation:
            return self._parameter_completions(context)
        else:
            return self._keyword_completions(context)

    def _analyze_context(self, document: str, position: Position) -> CompletionContext:
        """Analyze cursor position to determine completion context."""
        pass
```

**Design Rationale**: Context-aware completions provide relevant suggestions based on cursor position, improving usability and meeting the 200ms response time requirement through targeted filtering.

### Hover Provider

````python
class HoverProvider:
    def __init__(self, registry: OperationRegistry):
        self.registry = registry

    def provide_hover(
        self,
        document: str,
        position: Position
    ) -> Optional[Hover]:
        """Provide hover information for operation at position."""
        operation = self._identify_operation_at_position(document, position)

        if not operation:
            return None

        metadata = self.registry.get_operation(operation)
        return self._format_hover(metadata)

    def _format_hover(self, metadata: OperationMetadata) -> Hover:
        """Format operation metadata as hover content."""
        content = f"**{metadata.name}**\n\n"
        content += f"{metadata.description}\n\n"
        content += f"**Parameters:**\n"
        for param in metadata.parameters:
            content += f"- `{param.name}`: {param.type} - {param.description}\n"
        content += f"\n**Returns:** {metadata.return_type}\n"

        if metadata.examples:
            content += f"\n**Examples:**\n```doctk\n{metadata.examples[0]}\n```"

        return Hover(contents=MarkupContent(kind=MarkupKind.Markdown, value=content))
````

**Design Rationale**: Rich markdown formatting provides clear, readable documentation. Including examples helps users understand operation usage quickly.

## Data Models

### DSL Abstract Syntax Tree

```python
@dataclass
class DSLNode:
    type: str  # 'operation', 'pipe', 'argument', etc.
    value: Any
    children: List['DSLNode']
    range: Range

@dataclass
class OperationNode(DSLNode):
    operation_name: str
    arguments: Dict[str, Any]

@dataclass
class PipelineNode(DSLNode):
    operations: List[OperationNode]
```

**Design Rationale**: A simple AST structure is sufficient for the doctk DSL, which has a linear pipeline structure. This keeps parsing fast and validation straightforward.

### Document State

```python
@dataclass
class DocumentState:
    uri: str
    text: str
    version: int
    ast: Optional[DSLNode]
    diagnostics: List[Diagnostic]
    last_modified: float
```

**Design Rationale**: Maintaining document state allows incremental updates and caching, improving performance for large documents.

## Error Handling

### Language Server Error Handling

```python
class DoctkLanguageServer(LanguageServer):
    def __init__(self):
        super().__init__('doctk-lsp', 'v0.1.0')
        self.setup_error_handlers()

    def setup_error_handlers(self):
        @self.feature(TEXT_DOCUMENT_DID_OPEN)
        async def did_open(ls: LanguageServer, params: DidOpenTextDocumentParams):
            try:
                uri = params.text_document.uri
                text = params.text_document.text
                await self.parse_and_validate(uri, text)
            except Exception as e:
                self.show_message(f"Error parsing document: {str(e)}", MessageType.Error)
                self.log_error(e)

    def log_error(self, error: Exception):
        """Log detailed error information for troubleshooting."""
        import traceback
        self.show_message_log(
            f"Error: {str(error)}\n{traceback.format_exc()}",
            MessageType.Log
        )
```

**Design Rationale**: Comprehensive logging ensures errors can be diagnosed without disrupting the user experience. The LSP continues functioning even when individual operations fail.

### Graceful Degradation

```python
class DSLParser:
    def parse(self, text: str) -> ParseResult:
        """Parse with error recovery."""
        try:
            ast = self._parse_full(text)
            return ParseResult(ast=ast, errors=[])
        except ParseError as e:
            # Attempt partial parsing
            partial_ast = self._parse_partial(text, e)
            return ParseResult(ast=partial_ast, errors=[e])
```

**Design Rationale**: Partial parsing allows the language server to provide some features even when syntax errors exist, improving the development experience.

## Performance Optimization

### Caching Strategy

```python
class CachingCompletionProvider:
    def __init__(self):
        self.completion_cache: Dict[str, CompletionList] = {}
        self.cache_ttl = 5000  # milliseconds

    def provide_completions(self, context: CompletionContext) -> CompletionList:
        cache_key = self._compute_cache_key(context)

        if cache_key in self.completion_cache:
            cached = self.completion_cache[cache_key]
            if not self._is_expired(cached):
                return cached

        completions = self._compute_completions(context)
        self.completion_cache[cache_key] = completions
        return completions
```

**Design Rationale**: Caching completions reduces computation for repeated queries. A 5-second TTL balances freshness with performance, ensuring the 200ms response time requirement is met.

### Memory Management

```python
class DocumentStateManager:
    def __init__(self, max_memory_mb: int = 500):
        self.documents: Dict[str, DocumentState] = {}
        self.max_memory = max_memory_mb * 1024 * 1024
        self.lru_cache = LRUCache(maxsize=100)

    def get_document(self, uri: str) -> DocumentState:
        if uri in self.lru_cache:
            return self.lru_cache[uri]

        if self._memory_usage() > self.max_memory:
            self._evict_least_recently_used()

        doc = self._load_document(uri)
        self.lru_cache[uri] = doc
        return doc

    def _evict_least_recently_used(self):
        """Remove least recently used documents to free memory."""
        evicted = self.lru_cache.popitem(last=False)
        del self.documents[evicted[0]]
```

**Design Rationale**: LRU caching with memory limits prevents unbounded memory growth. The 500MB threshold triggers optimization before system resources are exhausted.

## AI Agent Support

### Structured Information Exposure

The language server exposes structured information specifically designed for AI consumption:

```python
class AIAgentSupport:
    """Provides structured information for AI agents."""

    def get_operation_catalog(self) -> Dict[str, OperationMetadata]:
        """Return complete catalog of available operations."""
        return {
            op.name: {
                'description': op.description,
                'parameters': [
                    {
                        'name': p.name,
                        'type': p.type,
                        'required': p.required,
                        'description': p.description
                    }
                    for p in op.parameters
                ],
                'return_type': op.return_type,
                'examples': op.examples
            }
            for op in self.registry.operations.values()
        }

    def get_context_aware_suggestions(
        self,
        document_state: DocumentState,
        intent: str
    ) -> List[OperationSuggestion]:
        """Suggest operations based on document state and user intent."""
        pass
```

**Design Rationale**: Providing a complete operation catalog allows AI agents to discover capabilities programmatically. Context-aware suggestions help agents generate more relevant code.

### Machine-Readable Documentation

```python
@dataclass
class StructuredDocumentation:
    """Machine-readable documentation format."""
    operation: str
    summary: str
    description: str
    parameters: List[ParameterDoc]
    returns: ReturnDoc
    examples: List[Example]
    related_operations: List[str]

@dataclass
class Example:
    description: str
    input: str
    output: str
    explanation: str

class DocumentationProvider:
    def get_structured_docs(self, operation: str) -> StructuredDocumentation:
        """Return documentation in machine-readable format."""
        metadata = self.registry.get_operation(operation)

        return StructuredDocumentation(
            operation=operation,
            summary=metadata.description,
            description=self._get_detailed_description(operation),
            parameters=self._format_parameters(metadata.parameters),
            returns=self._format_return_type(metadata.return_type),
            examples=self._get_examples(operation),
            related_operations=self._find_related(operation)
        )
```

**Design Rationale**: Structured documentation enables AI agents to understand operations deeply, including relationships between operations and usage patterns.

## Language Client Setup

### VS Code Integration

```typescript
class DoctkLanguageClient {
  private client: LanguageClient | null = null;

  async activate(context: ExtensionContext): Promise<void> {
    const serverModule = context.asAbsolutePath(
      path.join('server', 'doctk_lsp.py')
    );

    const serverOptions: ServerOptions = {
      command: 'uv',
      args: ['run', 'python', serverModule],
      options: { cwd: workspaceRoot }
    };

    const clientOptions: LanguageClientOptions = {
      documentSelector: [
        { scheme: 'file', language: 'doctk' },
        { scheme: 'file', pattern: '**/*.tk' }
      ],
      synchronize: {
        fileEvents: workspace.createFileSystemWatcher('**/*.tk')
      }
    };

    this.client = new LanguageClient(
      'doctkLanguageServer',
      'doctk Language Server',
      serverOptions,
      clientOptions
    );

    await this.client.start();
  }

  async deactivate(): Promise<void> {
    if (this.client) {
      await this.client.stop();
    }
  }
}
```

**Design Rationale**: Using `uv run` ensures the language server runs in the correct Python environment with all dependencies available. The client activates for both `.tk` files and `doctk` language identifiers in code blocks.

## Testing Strategy

### Unit Testing

```python
def test_completion_after_pipe():
    server = DoctkLanguageServer()
    text = "select heading |"
    position = Position(line=0, character=17)

    completions = server.provide_completions(text, position)

    assert len(completions.items) > 0
    assert any(item.label == 'promote' for item in completions.items)
    assert any(item.label == 'demote' for item in completions.items)

def test_validation_unknown_operation():
    server = DoctkLanguageServer()
    text = "select heading | invalid_op"

    diagnostics = server.validate(text)

    assert len(diagnostics) == 1
    assert 'unknown operation' in diagnostics[0].message.lower()
```

**Design Rationale**: Comprehensive unit tests ensure each component works correctly in isolation. Testing edge cases like unknown operations ensures robust error handling.

## Python Dependencies

The language server uses `uv` for dependency management:

```toml
[project]
name = "doctk-lsp"
version = "0.1.0"
dependencies = [
    "pygls>=1.0.0",
    "doctk>=0.1.0",
]

[tool.uv]
dev-dependencies = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
]
```

**Design Rationale**: Using `uv` aligns with the project's existing tooling and ensures reproducible builds. The language server has minimal dependencies, reducing installation complexity.

## Design Decisions Summary

### Key Architectural Decisions

1. **LSP Standard**: Using standard LSP protocol ensures compatibility with multiple editors and provides a well-tested communication layer.

1. **Dynamic Operation Loading**: The language server introspects doctk core to discover operations, ensuring automatic support for new operations without manual updates.

1. **Caching Strategy**: LRU cache with TTL for completions balances memory usage with performance, meeting response time requirements.

1. **Graceful Degradation**: Partial parsing allows the LSP to provide features even when syntax errors exist.

1. **AI-Friendly Design**: Structured information exposure enables programmatic access for AI agents.

### Trade-offs

1. **Client-Side vs. Server-Side Parsing**

   - **Decision**: Server-side parsing in language server
   - **Rationale**: Centralizes logic, reduces duplication, easier to maintain

1. **Caching Strategy**

   - **Decision**: LRU cache with TTL for completions
   - **Rationale**: Balances memory usage with performance, meets response time requirements

### Requirements Coverage

This design addresses the following requirements:

- **Requirements 7-11**: Language server features (activation, validation, completion, hover, AI support)
- **Requirement 18**: Error recovery and resilience
- **Requirement 19**: Configuration and customization (LSP-specific settings)
