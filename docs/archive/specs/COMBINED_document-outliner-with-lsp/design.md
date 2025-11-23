# Design Document: Document Outliner with LSP

## Overview

This design document describes the architecture and implementation approach for a Document Outliner with Language Server Protocol (LSP) support for the doctk project. The system consists of three main components:

1. **VS Code Extension (Outliner UI)** - Provides a tree-based visual interface for document structure manipulation
1. **Language Server** - Provides intelligent code completion, validation, and documentation for the doctk DSL
1. **Core Integration Layer** - Bridges the UI and LSP components with the existing doctk core API

The design follows a pluggable architecture pattern, separating interface concerns from core document manipulation logic. This enables future support for additional interfaces (e.g., JupyterLab) without rewriting core functionality.

### Design Principles

- **Separation of Concerns**: UI logic is decoupled from document manipulation logic
- **Reusability**: Core doctk API is the single source of truth for all operations
- **Extensibility**: Pluggable architecture supports multiple interface implementations
- **Performance**: Optimized for documents with up to 1000 headings
- **Resilience**: Graceful error handling and automatic recovery mechanisms

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     VS Code Extension                        │
│  ┌──────────────────┐         ┌─────────────────────────┐  │
│  │  Outliner View   │         │   Language Client       │  │
│  │  (Tree Provider) │         │   (LSP Client)          │  │
│  └────────┬─────────┘         └──────────┬──────────────┘  │
│           │                               │                  │
│           │                               │                  │
└───────────┼───────────────────────────────┼──────────────────┘
            │                               │
            │                               │ JSON-RPC
            │                               │
            │                               │
            │                               ▼
            │                    ┌─────────────────────┐
            │                    │  Language Server    │
            │                    │  (Python Process)   │
            │                    └──────────┬──────────┘
            │                               │
            ▼                               │
┌───────────────────────────────────────────┼──────────────────┐
│              doctk Core Integration       │                  │
│  ┌────────────────────────────────────────▼───────────────┐ │
│  │           Document Manipulation API                     │ │
│  │  (Operations: promote, demote, nest, unnest, etc.)     │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              doctk Core (Existing)                      │ │
│  │  - Document/Node abstractions                           │ │
│  │  - UDAST representation                                 │ │
│  │  - Markdown parser/serializer                           │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

#### VS Code Extension

- Renders tree view of document structure
- Handles user interactions (drag-drop, context menus, keyboard shortcuts)
- Manages document synchronization between tree view and editor
- Hosts the Language Client for LSP communication
- Provides command palette integration

#### Language Server

- Validates doctk DSL syntax in real-time
- Provides auto-completion for operations and arguments
- Supplies hover documentation for operations
- Exposes structured information for AI agents
- Maintains document state for validation context

#### Core Integration Layer

- Translates UI operations to doctk API calls
- Manages document state and change tracking
- Handles undo/redo integration with VS Code
- Provides operation metadata for LSP
- Ensures consistency across all interfaces

## Components and Interfaces

### 1. VS Code Extension (TypeScript)

#### Tree Data Provider

The tree view is implemented using VS Code's `TreeDataProvider` API.

```typescript
interface OutlineNode {
  id: string;              // Unique identifier for the node
  label: string;           // Heading text
  level: number;           // Heading level (1-6)
  range: Range;            // Position in document
  children: OutlineNode[]; // Child nodes
  parent?: OutlineNode;    // Parent reference
}

class DocumentOutlineProvider implements TreeDataProvider<OutlineNode>, TreeDragAndDropController<OutlineNode> {
  // TreeDataProvider methods
  getTreeItem(element: OutlineNode): TreeItem;
  getChildren(element?: OutlineNode): OutlineNode[];
  getParent(element: OutlineNode): OutlineNode | undefined;

  // Drag and drop support
  handleDrag(source: OutlineNode[], dataTransfer: DataTransfer): void;
  handleDrop(target: OutlineNode, dataTransfer: DataTransfer, token: CancellationToken): void;

  // Custom methods
  refresh(): void;
  updateFromDocument(document: TextDocument): void;
  applyOperation(node: OutlineNode, operation: Operation): Promise<void>;
}
```

**Design Rationale**: Using VS Code's native `TreeDataProvider` ensures consistency with other VS Code tree views and provides built-in support for drag-and-drop, which is a core requirement.

#### Document Synchronization Manager

Manages bidirectional synchronization between the tree view and editor.

```typescript
class DocumentSyncManager {
  private debounceTimer: NodeJS.Timeout | null = null;
  private readonly DEBOUNCE_DELAY = 300; // milliseconds

  onDocumentChange(document: TextDocument): void;
  onTreeViewChange(operation: TreeOperation): Promise<void>;
  applyEdit(edit: WorkspaceEdit): Promise<boolean>;

  private debounceUpdate(callback: () => void): void;
}
```

**Design Rationale**: Debouncing prevents excessive updates during rapid typing or multiple operations. The 300ms delay balances responsiveness (500ms requirement) with performance.

#### Operation Handler

Translates user actions into doctk operations.

```typescript
interface Operation {
  type: 'promote' | 'demote' | 'move_up' | 'move_down' | 'nest' | 'unnest' | 'delete';
  targetNode: OutlineNode;
  params?: Record<string, any>;
}

class OperationHandler {
  async executeOperation(operation: Operation): Promise<OperationResult>;
  async executeWithUndo(operation: Operation): Promise<void>;

  private async callDoctkAPI(operation: Operation): Promise<string>;
  private createWorkspaceEdit(oldText: string, newText: string): WorkspaceEdit;
}
```

**Design Rationale**: The operation handler abstracts the complexity of calling the Python doctk API and converting results back to VS Code edits. This separation allows for easier testing and future optimization (e.g., batching operations).

#### Language Client Setup

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

### 2. Language Server (Python)

The language server is implemented using the `pygls` (Python Generic Language Server) library.

#### Server Architecture

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

#### Operation Registry

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

**Design Rationale**: Dynamic operation loading ensures the LSP automatically supports new operations added to doctk core without manual updates. This satisfies Requirement 20 (Integration with doctk Core API).

#### DSL Parser and Validator

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

#### Completion Provider

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

### 3. Core Integration Layer (Python)

#### Document Manipulation API

Provides a high-level interface for document operations used by both the extension and LSP.

```python
from doctk import Document, Node
from typing import Protocol

class DocumentOperation(Protocol):
    """Protocol for all document operations."""
    def execute(self, doc: Document, target: Node) -> Document:
        ...

    def validate(self, doc: Document, target: Node) -> ValidationResult:
        ...

class StructureOperations:
    """High-level operations for document structure manipulation."""

    @staticmethod
    def promote(doc: Document, node_id: str) -> Document:
        """Decrease heading level by one."""
        node = doc.find_node(node_id)
        if node.level > 1:
            return doc.update_node(node_id, level=node.level - 1)
        return doc

    @staticmethod
    def demote(doc: Document, node_id: str) -> Document:
        """Increase heading level by one."""
        node = doc.find_node(node_id)
        if node.level < 6:
            return doc.update_node(node_id, level=node.level + 1)
        return doc

    @staticmethod
    def move_up(doc: Document, node_id: str) -> Document:
        """Move node up in sibling order."""
        pass

    @staticmethod
    def move_down(doc: Document, node_id: str) -> Document:
        """Move node down in sibling order."""
        pass

    @staticmethod
    def nest(doc: Document, node_id: str, parent_id: str) -> Document:
        """Nest node under a new parent."""
        pass

    @staticmethod
    def unnest(doc: Document, node_id: str) -> Document:
        """Move node up one level in hierarchy."""
        pass
```

**Design Rationale**: Immutable document operations (returning new Document instances) simplify undo/redo implementation and prevent state inconsistencies. This aligns with functional programming principles used in doctk core.

#### Bridge API for Extension

Provides a simple interface for the TypeScript extension to call Python operations.

```python
class ExtensionBridge:
    """Bridge between VS Code extension and doctk core."""

    def __init__(self):
        self.operations = StructureOperations()

    def execute_operation(
        self,
        operation_type: str,
        document_text: str,
        node_id: str,
        params: Optional[Dict[str, Any]] = None
    ) -> OperationResult:
        """Execute an operation and return the modified document."""
        try:
            doc = Document.from_markdown(document_text)

            operation_map = {
                'promote': self.operations.promote,
                'demote': self.operations.demote,
                'move_up': self.operations.move_up,
                'move_down': self.operations.move_down,
                'nest': self.operations.nest,
                'unnest': self.operations.unnest,
            }

            operation = operation_map.get(operation_type)
            if not operation:
                return OperationResult(success=False, error=f"Unknown operation: {operation_type}")

            result_doc = operation(doc, node_id, **(params or {}))
            return OperationResult(
                success=True,
                document=result_doc.to_markdown(),
                modified_ranges=self._compute_diff(doc, result_doc)
            )
        except Exception as e:
            return OperationResult(success=False, error=str(e))

@dataclass
class OperationResult:
    success: bool
    document: Optional[str] = None
    modified_ranges: Optional[List[Range]] = None
    error: Optional[str] = None
```

**Design Rationale**: The bridge API provides a simple, JSON-serializable interface that can be called from TypeScript via child process or HTTP. Computing diffs allows the extension to apply minimal edits, improving performance and preserving cursor position.

## Data Models

### Document Tree Representation

The outliner uses a tree structure that mirrors the document's heading hierarchy.

```typescript
// TypeScript (Extension)
interface DocumentTree {
  root: OutlineNode;
  nodeMap: Map<string, OutlineNode>;  // Fast lookup by ID
  version: number;                     // For change tracking
}

interface OutlineNode {
  id: string;              // Unique identifier (e.g., "h1-0", "h2-3")
  label: string;           // Heading text
  level: number;           // 1-6 for headings
  range: Range;            // Start/end position in document
  children: OutlineNode[];
  parent?: OutlineNode;
  metadata?: NodeMetadata;
}

interface NodeMetadata {
  hasContent: boolean;     // Whether node has body content
  contentLength: number;   // Character count of content
  lastModified: number;    // Timestamp
}
```

**Design Rationale**: The `nodeMap` provides O(1) lookup for operations, critical for performance with large documents. The `version` field enables optimistic concurrency control for synchronization.

### DSL Abstract Syntax Tree

```python
# Python (Language Server)
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

### Configuration Schema

```typescript
interface DoctkConfiguration {
  outliner: {
    autoRefresh: boolean;
    refreshDelay: number;        // milliseconds
    showContentPreview: boolean;
    maxPreviewLength: number;
  };

  keybindings: {
    promote: string;
    demote: string;
    moveUp: string;
    moveDown: string;
    delete: string;
  };

  lsp: {
    enabled: boolean;
    trace: 'off' | 'messages' | 'verbose';
    maxCompletionItems: number;
  };

  performance: {
    largeDocumentThreshold: number;  // Number of headings
    enableVirtualization: boolean;
  };
}
```

**Design Rationale**: Comprehensive configuration allows users to tune performance and behavior. The `largeDocumentThreshold` enables automatic optimization strategies for large documents (Requirement 17).

## Error Handling

### Error Recovery Strategy

The system implements a multi-layered error handling approach:

1. **Graceful Degradation**: When parsing fails, display partial tree view with available structure
1. **Automatic Retry**: Network/file system errors retry up to 3 times with exponential backoff
1. **Server Recovery**: Language server crashes trigger automatic restart within 5 seconds
1. **User Notification**: Critical errors display actionable messages with recovery options

```typescript
class ErrorHandler {
  async handleOperationError(error: Error, operation: Operation): Promise<void> {
    if (error instanceof NetworkError) {
      await this.retryWithBackoff(operation, 3);
    } else if (error instanceof ValidationError) {
      this.showValidationMessage(error);
    } else {
      this.logError(error);
      this.showGenericError(operation.type);
    }
  }

  private async retryWithBackoff(
    operation: Operation,
    maxRetries: number
  ): Promise<void> {
    for (let i = 0; i < maxRetries; i++) {
      try {
        await this.executeOperation(operation);
        return;
      } catch (error) {
        if (i === maxRetries - 1) throw error;
        await this.delay(Math.pow(2, i) * 1000);
      }
    }
  }
}
```

**Design Rationale**: Exponential backoff prevents overwhelming the system during transient failures. Distinguishing error types enables appropriate recovery strategies.

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

## Testing Strategy

### Unit Testing

Each component has isolated unit tests:

- **Extension**: Mock VS Code API, test tree provider logic
- **Language Server**: Test parsing, validation, and completion logic
- **Core Integration**: Test operation execution and document transformations

```typescript
// Example: Tree Provider Tests
describe('DocumentOutlineProvider', () => {
  it('should build tree from markdown headings', () => {
    const markdown = '# Title\n## Section\n### Subsection';
    const provider = new DocumentOutlineProvider();
    const tree = provider.buildTree(markdown);

    expect(tree.root.children).toHaveLength(1);
    expect(tree.root.children[0].level).toBe(1);
    expect(tree.root.children[0].children[0].level).toBe(2);
  });

  it('should handle drag-drop reordering', async () => {
    const provider = new DocumentOutlineProvider();
    const result = await provider.handleDrop(targetNode, sourceNode);

    expect(result.success).toBe(true);
    expect(result.newOrder).toEqual(['node1', 'node3', 'node2']);
  });
});
```

```python
# Example: Language Server Tests
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

### Integration Testing

Test interactions between components:

- Extension ↔ Core Integration: Test operation execution end-to-end
- Language Server ↔ Core Integration: Test operation metadata loading
- Extension ↔ Language Server: Test LSP communication

```typescript
describe('Extension Integration', () => {
  it('should execute promote operation and update document', async () => {
    const doc = await workspace.openTextDocument(testFile);
    const provider = new DocumentOutlineProvider();
    const node = provider.getNodeAtLine(2);

    await provider.applyOperation(node, { type: 'promote' });

    const updatedDoc = workspace.textDocuments.find(d => d.uri === doc.uri);
    expect(updatedDoc.getText()).toContain('# Promoted Heading');
  });
});
```

### End-to-End Testing

Automated tests simulating real user workflows:

- Open document → View outliner → Drag-drop → Verify changes
- Type DSL code → Trigger completion → Accept suggestion → Validate syntax
- Execute operation → Undo → Redo → Verify state

**Design Rationale**: Comprehensive testing at all levels ensures reliability. E2E tests catch integration issues that unit tests might miss, particularly around synchronization and state management.

## Performance Optimization

### Large Document Handling

For documents exceeding 1000 headings, the system implements several optimizations:

1. **Virtual Scrolling**: Only render visible tree nodes
1. **Lazy Loading**: Load child nodes on expansion
1. **Incremental Parsing**: Parse only changed sections
1. **Debounced Updates**: Batch rapid changes

```typescript
class VirtualTreeRenderer {
  private visibleRange: { start: number; end: number };
  private nodeHeight = 22; // pixels

  render(nodes: OutlineNode[], scrollTop: number, viewportHeight: number): void {
    const startIndex = Math.floor(scrollTop / this.nodeHeight);
    const endIndex = Math.ceil((scrollTop + viewportHeight) / this.nodeHeight);

    this.visibleRange = { start: startIndex, end: endIndex };
    const visibleNodes = nodes.slice(startIndex, endIndex);

    this.renderNodes(visibleNodes, startIndex);
  }
}
```

**Design Rationale**: Virtual scrolling is essential for maintaining responsiveness with large documents. Rendering only visible nodes keeps memory usage constant regardless of document size.

### Language Server Performance

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

**Design Rationale**: LRU caching with memory limits prevents unbounded memory growth. The 500MB threshold (Requirement 17) triggers optimization before system resources are exhausted.

## Communication Protocols

### Extension ↔ Python Bridge

The extension communicates with Python operations via a simple JSON-RPC interface over stdin/stdout.

```typescript
class PythonBridge {
  private process: ChildProcess;

  async call(method: string, params: any): Promise<any> {
    const request = {
      jsonrpc: '2.0',
      id: this.nextId++,
      method,
      params
    };

    this.process.stdin.write(JSON.stringify(request) + '\n');

    return new Promise((resolve, reject) => {
      this.pendingRequests.set(request.id, { resolve, reject });
    });
  }
}
```

**Design Rationale**: JSON-RPC over stdio is simple, reliable, and doesn't require network configuration. It's the same protocol used by LSP, providing consistency.

### Language Server Protocol

The language server implements standard LSP methods:

- `textDocument/completion`: Provide completions
- `textDocument/hover`: Provide hover information
- `textDocument/didOpen`: Document opened
- `textDocument/didChange`: Document changed
- `textDocument/publishDiagnostics`: Send validation errors

**Design Rationale**: Using standard LSP ensures compatibility with any LSP client and enables future support for other editors (e.g., Neovim, Emacs).

## Undo/Redo Implementation

### Strategy

The extension integrates with VS Code's native undo stack by using `WorkspaceEdit` for all document modifications.

```typescript
class UndoableOperationHandler {
  async executeWithUndo(operation: Operation): Promise<void> {
    const document = this.getCurrentDocument();
    const originalText = document.getText();

    // Execute operation
    const result = await this.bridge.executeOperation(operation);

    if (!result.success) {
      throw new Error(result.error);
    }

    // Create workspace edit
    const edit = new WorkspaceEdit();
    const fullRange = new Range(
      document.positionAt(0),
      document.positionAt(originalText.length)
    );
    edit.replace(document.uri, fullRange, result.document);

    // Apply edit (automatically adds to undo stack)
    await workspace.applyEdit(edit);

    // Refresh tree view
    this.treeProvider.refresh();
  }
}
```

**Design Rationale**: Using `WorkspaceEdit` ensures undo/redo works consistently with other VS Code operations. The editor's undo stack handles all the complexity of state management.

### Optimized Edits (CRITICAL IMPROVEMENT)

**Problem**: The current implementation (as of PR #6) replaces the entire document on every operation, which:

- Clears the undo/redo stack
- Loses cursor position and text selections
- Has poor performance for large documents

**Solution**: Implement granular edits by having the Python backend return specific ranges that were modified, then apply only those changes.

#### Backend Changes

```python
@dataclass
class ModifiedRange:
    """Represents a range of text that was modified."""
    start_line: int
    start_column: int
    end_line: int
    end_column: int
    new_text: str

@dataclass
class OperationResult:
    success: bool
    document: Optional[str] = None  # Full document for fallback
    modified_ranges: Optional[List[ModifiedRange]] = None  # Granular edits
    error: Optional[str] = None

class StructureOperations:
    @staticmethod
    def promote(doc: Document, node_id: str) -> OperationResult:
        """Execute promote and compute modified ranges."""
        # ... existing logic ...

        # Compute specific ranges that changed
        modified_ranges = DiffComputer.compute_ranges(
            original_doc=doc,
            modified_doc=new_document,
            affected_node_ids=[node_id]
        )

        return OperationResult(
            success=True,
            document=new_document.to_string(),
            modified_ranges=modified_ranges
        )
```

#### Frontend Changes

```typescript
class OperationHandler {
  async executeOperation(operation: Operation): Promise<void> {
    const document = this.getCurrentDocument();
    const result = await this.bridge.executeOperation(operation);

    if (!result.success) {
      throw new Error(result.error);
    }

    const edit = new WorkspaceEdit();

    // Use granular edits if available
    if (result.modifiedRanges && result.modifiedRanges.length > 0) {
      for (const range of result.modifiedRanges) {
        const vsRange = new Range(
          new Position(range.start_line, range.start_column),
          new Position(range.end_line, range.end_column)
        );
        edit.replace(document.uri, vsRange, range.new_text);
      }
    } else {
      // Fallback to full document replacement
      const fullRange = new Range(
        document.positionAt(0),
        document.positionAt(document.getText().length)
      );
      edit.replace(document.uri, fullRange, result.document);
    }

    await workspace.applyEdit(edit);
    this.treeProvider.refresh();
  }
}
```

**Design Rationale**: Granular edits preserve cursor position, maintain undo/redo stack, and provide better performance. The backend computes which ranges changed, allowing the frontend to apply minimal updates. Fallback to full document replacement ensures backward compatibility and handles edge cases.

### Centralized Node ID Generation (MEDIUM PRIORITY)

**Problem**: Node ID generation logic is duplicated in:

- Frontend: `outlineProvider.ts` lines 157-160
- Backend: `operations.py` DocumentTreeBuilder class

This creates tight coupling and maintenance issues - any change to the ID scheme must be synchronized in both places.

**Solution**: Make the Python backend the single source of truth for document structure and node IDs.

#### Implementation Approach

```python
@dataclass
class TreeNode:
    """Complete tree node with ID generated by backend."""
    id: str
    label: str
    level: int
    line: int
    column: int
    children: List['TreeNode']

class DocumentTreeBuilder:
    def build_tree_with_ids(self, document: Document) -> TreeNode:
        """Build complete tree structure with IDs assigned."""
        # Existing ID generation logic - single source of truth
        heading_counter: Dict[int, int] = {}

        for node in document.nodes:
            if isinstance(node, Heading):
                level = node.level
                heading_counter[level] = heading_counter.get(level, 0) + 1
                node_id = f"h{level}-{heading_counter[level] - 1}"
                # ... build tree structure ...

        return tree_root

class ExtensionBridge:
    def get_document_tree(self, document_text: str) -> Dict[str, Any]:
        """Return complete tree structure with IDs."""
        doc = Document.from_string(document_text)
        tree_builder = DocumentTreeBuilder(doc)
        tree = tree_builder.build_tree_with_ids(doc)

        return {
            'root': self._serialize_tree_node(tree),
            'version': int(time.time() * 1000)
        }
```

```typescript
class DocumentOutlineProvider {
  async updateFromDocument(document: TextDocument): Promise<void> {
    // Request tree structure from backend instead of parsing locally
    const result = await this.bridge.getDocumentTree(document.getText());

    // Use backend-provided IDs and structure
    this.root = this.deserializeTreeNode(result.root);
    this.version = result.version;

    this._onDidChangeTreeData.fire();
  }

  private deserializeTreeNode(data: any): OutlineNode {
    // Convert backend tree structure to frontend nodes
    // IDs come from backend, no local ID generation
    return {
      id: data.id,  // Backend-generated ID
      label: data.label,
      level: data.level,
      // ...
      children: data.children.map(child => this.deserializeTreeNode(child))
    };
  }
}
```

**Design Rationale**: Making the backend the single source of truth for document structure and IDs eliminates synchronization issues, reduces code duplication, and ensures consistency. The backend-driven tree structure provides complete node information (IDs, parent-child relationships, ranges) with only one additional RPC call. This improves overall architecture by centralizing all parsing and ID generation logic in one place.

## Pluggable Architecture

### Interface Abstraction

The core integration layer defines interfaces that any UI can implement:

```python
from abc import ABC, abstractmethod

class DocumentInterface(ABC):
    """Abstract interface for document manipulation UIs."""

    @abstractmethod
    def display_tree(self, tree: DocumentTree) -> None:
        """Display document structure as a tree."""
        pass

    @abstractmethod
    def get_user_selection(self) -> Optional[NodeSelection]:
        """Get currently selected node(s)."""
        pass

    @abstractmethod
    def apply_operation(self, operation: Operation) -> OperationResult:
        """Apply an operation and update the display."""
        pass

    @abstractmethod
    def show_error(self, message: str) -> None:
        """Display error message to user."""
        pass

class VSCodeInterface(DocumentInterface):
    """VS Code implementation of document interface."""
    # Implementation specific to VS Code
    pass

class JupyterLabInterface(DocumentInterface):
    """Future JupyterLab implementation."""
    # To be implemented
    pass
```

**Design Rationale**: The abstract interface ensures all UI implementations provide the same core functionality. New interfaces only need to implement display and interaction logic, reusing all document manipulation code.

### Shared Core

All interfaces share the same core components:

- Document manipulation API (operations)
- Language server (LSP)
- Operation registry
- Validation logic

```
┌─────────────────────────────────────────────────────────┐
│                    UI Layer (Pluggable)                  │
│  ┌──────────────────┐         ┌──────────────────────┐ │
│  │  VS Code         │         │  JupyterLab          │ │
│  │  Interface       │         │  Interface (Future)  │ │
│  └────────┬─────────┘         └──────────┬───────────┘ │
└───────────┼────────────────────────────────┼────────────┘
            │                                │
            └────────────┬───────────────────┘
                         │
            ┌────────────▼─────────────┐
            │   Shared Core Layer      │
            │  - Operations API        │
            │  - Language Server       │
            │  - Validation            │
            └──────────────────────────┘
```

**Design Rationale**: This architecture satisfies Requirement 15 (Pluggable Interface Architecture) by ensuring new interfaces can be added without modifying core logic.

## REPL and Script Execution

### Interactive REPL

The REPL provides an interactive command-line interface for experimenting with doctk operations.

```python
class DoctkREPL:
    def __init__(self):
        self.document: Optional[Document] = None
        self.history: List[str] = []
        self.parser = DSLParser()

    def run(self):
        print("doctk REPL v0.1.0")
        print("Type 'help' for available commands")

        while True:
            try:
                command = input("doctk> ")
                if command == 'exit':
                    break
                elif command == 'help':
                    self.show_help()
                elif command.startswith('load '):
                    self.load_document(command[5:])
                else:
                    self.execute_command(command)
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit")
            except Exception as e:
                print(f"Error: {e}")

    def execute_command(self, command: str):
        if not self.document:
            print("No document loaded. Use 'load <file>' first.")
            return

        result = self.parser.parse(command)
        if result.errors:
            for error in result.errors:
                print(f"Syntax error: {error.message}")
            return

        # Execute operation pipeline
        self.document = self.execute_pipeline(result.ast, self.document)
        print("Operation completed successfully")
        self.history.append(command)
```

**Design Rationale**: The REPL maintains document state across commands, allowing users to build up transformations incrementally. This supports exploratory workflows and rapid prototyping.

### Script File Execution

```python
class ScriptExecutor:
    def __init__(self):
        self.parser = DSLParser()

    def execute_file(self, script_path: str, document_path: str) -> ExecutionResult:
        with open(script_path, 'r') as f:
            script = f.read()

        document = Document.from_file(document_path)

        result = self.parser.parse(script)
        if result.errors:
            return ExecutionResult(
                success=False,
                errors=[f"Line {e.line}: {e.message}" for e in result.errors]
            )

        try:
            transformed = self.execute_pipeline(result.ast, document)
            transformed.save(document_path)
            return ExecutionResult(success=True, document=transformed)
        except Exception as e:
            return ExecutionResult(success=False, errors=[str(e)])
```

**Design Rationale**: Script execution is stateless (unlike REPL), making it suitable for automation and batch processing. Error reporting includes line numbers for easy debugging.

### Code Block Execution in Markdown

````typescript
class CodeBlockExecutor {
  async executeCodeBlock(document: TextDocument, range: Range): Promise<void> {
    const codeBlock = document.getText(range);
    const code = this.extractCode(codeBlock);

    if (!code) {
      window.showErrorMessage('No doctk code found in selection');
      return;
    }

    const result = await this.bridge.executeScript(code, document.getText());

    if (result.success) {
      // Apply transformation to document
      const edit = new WorkspaceEdit();
      edit.replace(
        document.uri,
        new Range(document.positionAt(0), document.positionAt(document.getText().length)),
        result.document
      );
      await workspace.applyEdit(edit);
      window.showInformationMessage('Code block executed successfully');
    } else {
      this.outputChannel.appendLine(`Execution failed: ${result.error}`);
      this.outputChannel.show();
    }
  }

  private extractCode(codeBlock: string): string | null {
    const match = codeBlock.match(/```doctk\n([\s\S]*?)\n```/);
    return match ? match[1] : null;
  }
}
````

**Design Rationale**: Code block execution enables literate programming workflows where documentation and transformation scripts coexist. This is particularly useful for documenting complex document processing pipelines.

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

**Design Rationale**: Structured documentation enables AI agents to understand operations deeply, including relationships between operations and usage patterns. This supports Requirement 11 (AI-Friendly Language Server).

## Security Considerations

### Input Validation

All user inputs are validated before processing:

```python
class InputValidator:
    def validate_operation_params(
        self,
        operation: str,
        params: Dict[str, Any]
    ) -> ValidationResult:
        """Validate operation parameters against schema."""
        schema = self.registry.get_operation(operation).parameter_schema

        try:
            jsonschema.validate(params, schema)
            return ValidationResult(valid=True)
        except jsonschema.ValidationError as e:
            return ValidationResult(valid=False, error=str(e))
```

**Design Rationale**: Schema-based validation prevents injection attacks and ensures type safety. Using JSON Schema provides a standard, well-tested validation mechanism.

### Sandboxing

Script execution runs in a controlled environment:

```python
class SandboxedExecutor:
    def __init__(self):
        self.allowed_operations = set(self.registry.operations.keys())
        self.max_execution_time = 30  # seconds

    def execute(self, script: str, document: Document) -> Document:
        # Parse and validate before execution
        ast = self.parser.parse(script)
        self._validate_operations(ast)

        # Execute with timeout
        with timeout(self.max_execution_time):
            return self._execute_ast(ast, document)
```

**Design Rationale**: Limiting execution time and validating operations prevents malicious scripts from causing harm. This is essential for a system that executes user-provided code.

## Deployment and Distribution

### VS Code Extension Packaging

The extension is packaged as a `.vsix` file containing:

- TypeScript extension code (compiled to JavaScript)
- Python language server and dependencies
- Package manifest (`package.json`)
- README and documentation

```json
{
  "name": "doctk-outliner",
  "displayName": "doctk Document Outliner",
  "description": "Tree-based document outliner with LSP support",
  "version": "0.1.0",
  "engines": {
    "vscode": "^1.80.0"
  },
  "activationEvents": [
    "onLanguage:markdown",
    "onLanguage:doctk"
  ],
  "main": "./out/extension.js",
  "contributes": {
    "views": {
      "explorer": [
        {
          "id": "doctkOutline",
          "name": "Document Outline"
        }
      ]
    },
    "commands": [
      {
        "command": "doctk.promote",
        "title": "Promote Section"
      },
      {
        "command": "doctk.demote",
        "title": "Demote Section"
      }
    ],
    "keybindings": [
      {
        "command": "doctk.promote",
        "key": "ctrl+shift+up",
        "when": "doctkOutlineView.focused"
      }
    ],
    "languages": [
      {
        "id": "doctk",
        "extensions": [".tk"],
        "aliases": ["doctk", "DocTK"]
      }
    ]
  }
}
```

**Design Rationale**: Standard VS Code extension packaging ensures easy installation via the marketplace. Including Python dependencies in the package eliminates external setup requirements.

### Python Dependencies

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

**Design Rationale**: Using `uv` aligns with the project's existing tooling (per workspace rules) and ensures reproducible builds. The language server has minimal dependencies, reducing installation complexity.

## Future Enhancements

### Phase 2: Advanced Features

After the initial implementation, the following enhancements are planned:

1. **Multi-document Operations**: Apply operations across multiple documents
1. **Custom Operation Definitions**: Allow users to define custom operations
1. **Visual Diff View**: Show before/after comparison for operations
1. **Collaborative Editing**: Real-time synchronization for multiple users
1. **Operation Macros**: Record and replay sequences of operations

### JupyterLab Integration

The pluggable architecture enables future JupyterLab support:

```python
class JupyterLabInterface(DocumentInterface):
    """JupyterLab implementation using ipywidgets."""

    def __init__(self):
        self.tree_widget = TreeWidget()
        self.operations = StructureOperations()

    def display_tree(self, tree: DocumentTree) -> None:
        self.tree_widget.update(tree)
        display(self.tree_widget)

    def apply_operation(self, operation: Operation) -> OperationResult:
        # Execute operation and update notebook cell
        pass
```

**Design Rationale**: JupyterLab integration would enable document manipulation within computational notebooks, supporting data-driven document generation workflows.

### Performance Monitoring

Built-in telemetry for performance tracking:

```typescript
class PerformanceMonitor {
  private metrics: Map<string, Metric[]> = new Map();

  recordOperation(operation: string, duration: number): void {
    if (!this.metrics.has(operation)) {
      this.metrics.set(operation, []);
    }
    this.metrics.get(operation)!.push({
      timestamp: Date.now(),
      duration
    });
  }

  getAverageTime(operation: string): number {
    const metrics = this.metrics.get(operation) || [];
    return metrics.reduce((sum, m) => sum + m.duration, 0) / metrics.length;
  }

  reportSlowOperations(): void {
    for (const [operation, metrics] of this.metrics) {
      const avg = this.getAverageTime(operation);
      if (avg > 500) {  // Threshold from requirements
        console.warn(`Operation ${operation} averaging ${avg}ms`);
      }
    }
  }
}
```

**Design Rationale**: Performance monitoring helps identify bottlenecks and ensures the system meets performance requirements over time.

## Implementation Phases

### Phase 1: Core Outliner (Weeks 1-3)

**Goal**: Basic tree view with manual operations

- Implement tree data provider
- Add context menu operations (promote, demote, move)
- Integrate with doctk core API
- Basic document synchronization

**Success Criteria**:

- Tree view displays document structure
- Context menu operations work correctly
- Changes reflect in both tree and editor

### Phase 2: Drag-and-Drop (Week 4)

**Goal**: Interactive drag-and-drop reordering

- Implement drag-and-drop controller
- Add visual feedback for valid drop targets
- Handle edge cases (invalid drops, nested operations)

**Success Criteria**:

- Users can drag sections to reorder
- Visual feedback is clear and responsive
- Invalid operations are prevented

### Phase 3: Language Server Foundation (Weeks 5-6)

**Goal**: Basic LSP with syntax validation

- Set up pygls server
- Implement DSL parser
- Add syntax validation
- Connect to VS Code extension

**Success Criteria**:

- Language server starts and connects
- Syntax errors are highlighted
- Diagnostics update in real-time

### Phase 4: LSP Features (Weeks 7-8)

**Goal**: Completion and hover support

- Implement completion provider
- Add hover documentation
- Create operation registry
- Support AI agent queries

**Success Criteria**:

- Completions appear after typing
- Hover shows operation documentation
- AI agents can query operation metadata

### Phase 5: Advanced Features (Weeks 9-10)

**Goal**: REPL, scripts, and optimization

- Implement interactive REPL
- Add script file execution
- Optimize for large documents
- Add performance monitoring

**Success Criteria**:

- REPL accepts and executes commands
- Script files can be executed
- Large documents remain responsive

### Phase 6: Polish and Testing (Weeks 11-12)

**Goal**: Production-ready release

- Comprehensive testing
- Error handling improvements
- Documentation
- Performance tuning

**Success Criteria**:

- All requirements met
- Test coverage > 80%
- Documentation complete
- Performance benchmarks passed

## Design Decisions Summary

### Key Architectural Decisions

1. **Pluggable Architecture**: Separating UI from core logic enables future interface implementations (JupyterLab, web) without code duplication.

1. **Immutable Operations**: Document operations return new instances rather than mutating in place, simplifying undo/redo and preventing state inconsistencies.

1. **LSP Standard**: Using standard LSP protocol ensures compatibility with multiple editors and provides a well-tested communication layer.

1. **Dynamic Operation Loading**: The language server introspects doctk core to discover operations, ensuring automatic support for new operations without manual updates.

1. **Virtual Scrolling**: For large documents, only rendering visible nodes maintains constant memory usage and ensures responsiveness.

1. **Debounced Synchronization**: Batching rapid changes prevents excessive updates while maintaining the appearance of real-time synchronization.

1. **JSON-RPC Bridge**: Using JSON-RPC for extension-to-Python communication provides a simple, reliable protocol that's easy to debug.

1. **Schema-Based Validation**: Using JSON Schema for parameter validation provides type safety and prevents injection attacks.

### Trade-offs

1. **Full Document Replacement vs. Incremental Edits**

   - **Decision**: Compute minimal edits when possible
   - **Rationale**: Better cursor preservation and performance, worth the complexity

1. **Synchronous vs. Asynchronous Operations**

   - **Decision**: All operations are asynchronous
   - **Rationale**: Prevents UI blocking, essential for large documents

1. **Client-Side vs. Server-Side Parsing**

   - **Decision**: Server-side parsing in language server
   - **Rationale**: Centralizes logic, reduces duplication, easier to maintain

1. **Caching Strategy**

   - **Decision**: LRU cache with TTL for completions
   - **Rationale**: Balances memory usage with performance, meets response time requirements

1. **Error Recovery Approach**

   - **Decision**: Graceful degradation with automatic retry
   - **Rationale**: Provides best user experience while maintaining system stability

### Requirements Coverage

This design addresses all 20 requirements specified in the requirements document:

- **Requirements 1-6**: Outliner UI features (tree view, drag-drop, context menu, editing, keyboard shortcuts, undo/redo)
- **Requirements 7-11**: Language server features (activation, validation, completion, hover, AI support)
- **Requirements 12-14**: Script execution (REPL, files, code blocks)
- **Requirement 15**: Pluggable architecture
- **Requirement 16**: Document synchronization
- **Requirement 17**: Performance for large documents
- **Requirement 18**: Error recovery and resilience
- **Requirement 19**: Configuration and customization
- **Requirement 20**: Integration with doctk core API

Each component and interface has been designed to satisfy specific requirements while maintaining architectural coherence and extensibility.
