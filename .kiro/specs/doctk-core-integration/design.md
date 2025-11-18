# Design Document: doctk Core Integration & Execution

## Overview

This design document describes the architecture and implementation approach for the core integration layer and execution capabilities of the doctk system. This includes:

1. **Pluggable Architecture** - Bridges UI components with the doctk core API
1. **Document Manipulation API** - High-level operations for structure manipulation
1. **Script Execution** - REPL, file execution, and code block execution
1. **Performance Optimization** - Strategies for large documents
1. **Integration Layer** - Ensures consistency across all interfaces

The design follows a pluggable architecture pattern, separating interface concerns from core document manipulation logic. This enables future support for additional interfaces (e.g., JupyterLab) without rewriting core functionality.

### Design Principles

- **Separation of Concerns**: UI logic is decoupled from document manipulation logic
- **Reusability**: Core doctk API is the single source of truth for all operations
- **Extensibility**: Pluggable architecture supports multiple interface implementations
- **Performance**: Optimized for documents with up to 1000 headings
- **Consistency**: All interfaces use the same core operations

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Interface Layer                          │
│  ┌──────────────────┐         ┌─────────────────────────┐  │
│  │  VS Code         │         │   Language Server       │  │
│  │  Extension       │         │   (LSP)                 │  │
│  └────────┬─────────┘         └──────────┬──────────────┘  │
│           │                               │                  │
└───────────┼───────────────────────────────┼──────────────────┘
            │                               │
            │                               │
            └────────────┬──────────────────┘
                         │
            ┌────────────▼─────────────┐
            │   Core Integration       │
            │   Layer                  │
            └────────────┬─────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Document    │  │  Extension   │  │  Script      │
│  Operations  │  │  Bridge      │  │  Executor    │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └─────────────────┼─────────────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │  doctk Core API     │
              │  - Document/Node    │
              │  - UDAST            │
              │  - Parser           │
              └─────────────────────┘
```

### Component Responsibilities

#### Document Manipulation API

- Provides high-level operations (promote, demote, nest, unnest, move)
- Translates operations to doctk core API calls
- Computes modified ranges for granular edits
- Validates operations before execution

#### Extension Bridge

- Provides JSON-RPC interface for TypeScript-Python communication
- Manages request/response serialization
- Handles error propagation
- Coordinates between operations and interfaces

#### Script Executor

- Executes DSL scripts from REPL, files, and code blocks
- Maintains execution context and state
- Provides progress reporting
- Handles execution errors

#### Performance Manager

- Implements optimization strategies for large documents
- Manages memory usage and caching
- Provides virtual scrolling support
- Monitors performance metrics

## Core Integration Layer

### Document Manipulation API

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

### Bridge API for Extension

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

### Granular Edit Computation

**Backend Changes** (from PR #6 review):

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

class DiffComputer:
    """Computes modified ranges between documents."""

    @staticmethod
    def compute_ranges(
        original_doc: Document,
        modified_doc: Document,
        affected_node_ids: List[str]
    ) -> List[ModifiedRange]:
        """Compute specific ranges that changed."""
        ranges = []

        for node_id in affected_node_ids:
            orig_node = original_doc.find_node(node_id)
            mod_node = modified_doc.find_node(node_id)

            if orig_node and mod_node:
                # Compute line/column positions
                range = ModifiedRange(
                    start_line=orig_node.line,
                    start_column=orig_node.column,
                    end_line=orig_node.end_line,
                    end_column=orig_node.end_column,
                    new_text=mod_node.to_string()
                )
                ranges.append(range)

        return ranges

class StructureOperations:
    @staticmethod
    def promote(doc: Document, node_id: str) -> OperationResult:
        """Execute promote and compute modified ranges."""
        original_doc = doc
        new_document = doc.update_node(node_id, level=doc.find_node(node_id).level - 1)

        # Compute specific ranges that changed
        modified_ranges = DiffComputer.compute_ranges(
            original_doc=original_doc,
            modified_doc=new_document,
            affected_node_ids=[node_id]
        )

        return OperationResult(
            success=True,
            document=new_document.to_string(),
            modified_ranges=modified_ranges
        )
```

**Design Rationale**: Granular edits preserve cursor position, maintain undo/redo stack, and provide better performance. The backend computes which ranges changed, allowing the frontend to apply minimal updates.

### Centralized Node ID Generation

**Backend Changes** (from PR #6 review):

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

**Design Rationale**: Making the backend the single source of truth for document structure and IDs eliminates synchronization issues, reduces code duplication, and ensures consistency.

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

**Design Rationale**: This architecture satisfies the pluggable interface requirement by ensuring new interfaces can be added without modifying core logic.

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

## Performance Optimization

### Large Document Handling

For documents exceeding 1000 headings, the system implements several optimizations:

1. **Virtual Scrolling**: Only render visible tree nodes
1. **Lazy Loading**: Load child nodes on expansion
1. **Incremental Parsing**: Parse only changed sections
1. **Debounced Updates**: Batch rapid changes

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

### Performance Monitoring

Built-in telemetry for performance tracking:

```python
class PerformanceMonitor:
    def __init__(self):
        self.metrics: Dict[str, List[Metric]] = {}

    def record_operation(self, operation: str, duration: float):
        if operation not in self.metrics:
            self.metrics[operation] = []

        self.metrics[operation].append(Metric(
            timestamp=time.time(),
            duration=duration
        ))

    def get_average_time(self, operation: str) -> float:
        metrics = self.metrics.get(operation, [])
        if not metrics:
            return 0.0
        return sum(m.duration for m in metrics) / len(metrics)

    def report_slow_operations(self):
        for operation, metrics in self.metrics.items():
            avg = self.get_average_time(operation)
            if avg > 0.5:  # 500ms threshold
                print(f"Warning: Operation {operation} averaging {avg*1000:.0f}ms")
```

**Design Rationale**: Performance monitoring helps identify bottlenecks and ensures the system meets performance requirements over time.

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

## Testing Strategy

### Unit Testing

```python
def test_promote_operation():
    doc = Document.from_markdown("## Heading")
    result = StructureOperations.promote(doc, "h2-0")

    assert result.success
    assert "# Heading" in result.document

def test_granular_edits():
    doc = Document.from_markdown("## Heading\nContent")
    result = StructureOperations.promote(doc, "h2-0")

    assert result.modified_ranges is not None
    assert len(result.modified_ranges) == 1
    assert result.modified_ranges[0].start_line == 0
```

### Integration Testing

```python
def test_repl_execution():
    repl = DoctkREPL()
    repl.load_document("test.md")
    repl.execute_command("select heading | promote")

    assert repl.document is not None
    assert len(repl.history) == 1

def test_script_execution():
    executor = ScriptExecutor()
    result = executor.execute_file("script.tk", "document.md")

    assert result.success
    assert result.document is not None
```

**Design Rationale**: Comprehensive testing at all levels ensures reliability. Integration tests catch issues that unit tests might miss, particularly around state management and execution flow.

## Design Decisions Summary

### Key Architectural Decisions

1. **Pluggable Architecture**: Separating UI from core logic enables future interface implementations (JupyterLab, web) without code duplication.

1. **Immutable Operations**: Document operations return new instances rather than mutating in place, simplifying undo/redo and preventing state inconsistencies.

1. **Granular Edits**: Computing minimal edits preserves cursor position and undo/redo stack, worth the additional complexity.

1. **Centralized Node IDs**: Backend generates all node IDs, eliminating synchronization issues between frontend and backend.

1. **Performance Monitoring**: Built-in telemetry helps identify bottlenecks and ensures performance requirements are met.

### Trade-offs

1. **Full Document Replacement vs. Incremental Edits**

   - **Decision**: Compute minimal edits when possible
   - **Rationale**: Better cursor preservation and performance, worth the complexity

1. **Stateful REPL vs. Stateless Scripts**

   - **Decision**: REPL maintains state, scripts are stateless
   - **Rationale**: REPL supports exploration, scripts support automation

1. **Memory Management**

   - **Decision**: LRU cache with 500MB limit
   - **Rationale**: Prevents unbounded growth while supporting large documents

### Requirements Coverage

This design addresses the following requirements:

- **Requirements 12-14**: Script execution (REPL, files, code blocks)
- **Requirement 15**: Pluggable architecture
- **Requirement 17**: Performance for large documents
- **Requirement 20**: Integration with doctk core API
