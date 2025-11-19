# Core Integration API Reference

**Module**: `doctk.integration`
**Version**: 0.2.0
**Status**: Stable

## Overview

The core integration layer provides the bridge between doctk's document manipulation capabilities and various user interfaces (VS Code, LSP, CLI, future JupyterLab). This layer is platform-agnostic and provides:

- **Document Structure Operations**: High-level operations for manipulating document structure
- **Extension Bridge**: JSON-RPC interface for TypeScript-Python communication
- **Tree Building**: Hierarchical tree representation with stable node IDs
- **Granular Edits**: Compute precise text ranges modified by operations
- **Memory Management**: LRU caching for large documents
- **Performance Monitoring**: Track operation performance
- **Backward Compatibility**: Version checking and feature detection

## Module Structure

```
src/doctk/integration/
├── __init__.py          # Public API exports
├── operations.py        # Document structure operations
├── bridge.py            # JSON-RPC bridge
├── protocols.py         # Type definitions and interfaces
├── compat.py            # Backward compatibility
├── memory.py            # Memory management
└── performance.py       # Performance monitoring
```

---

## Core Classes

### DocumentTreeBuilder

**Location**: `doctk.integration.operations.DocumentTreeBuilder`

Builds a tree representation of a document with stable node IDs.

#### Constructor

```python
DocumentTreeBuilder(document: Document[Node])
```

**Parameters:**
- `document`: The document to build a tree from

**Example:**
```python
from doctk import Document
from doctk.integration.operations import DocumentTreeBuilder

doc = Document.from_file("example.md")
builder = DocumentTreeBuilder(doc)
```

#### Methods

##### `find_node(node_id: str) -> Node | None`

Find a node by its ID.

**Parameters:**
- `node_id`: Node identifier (format: "h{level}-{index}", e.g., "h2-3")

**Returns:** The node if found, None otherwise

**Example:**
```python
node = builder.find_node("h2-0")  # First h2 heading
if node:
    print(f"Found: {node.text}")
```

##### `get_node_index(node_id: str) -> int | None`

Get the index of a node in the document.

**Parameters:**
- `node_id`: Node identifier

**Returns:** The index if found, None otherwise

##### `get_section_range(node_id: str) -> tuple[int, int] | None`

Get the range of indices for a complete section (heading + content until next heading).

**Parameters:**
- `node_id`: The ID of the heading node

**Returns:** Tuple of (start_index, end_index) inclusive, or None if not found

**Example:**
```python
section_range = builder.get_section_range("h2-0")
if section_range:
    start, end = section_range
    section_nodes = doc.nodes[start:end+1]
```

##### `build_tree_with_ids() -> TreeNode`

Build complete tree structure with IDs assigned.

**Returns:** TreeNode representing the document root with all children

**Example:**
```python
tree = builder.build_tree_with_ids()
print(f"Root has {len(tree.children)} top-level headings")
```

---

### DiffComputer

**Location**: `doctk.integration.operations.DiffComputer`

Computes granular text ranges modified by document operations.

#### Static Methods

##### `compute_ranges(original_doc, modified_doc, affected_node_ids) -> list[ModifiedRange]`

Compute the specific text ranges that changed between two documents.

**Parameters:**
- `original_doc`: The original document before the operation
- `modified_doc`: The modified document after the operation
- `affected_node_ids`: List of node IDs that were affected

**Returns:** List of ModifiedRange objects with precise line/column positions

**Example:**
```python
from doctk.integration.operations import DiffComputer

ranges = DiffComputer.compute_ranges(
    original_doc=old_doc,
    modified_doc=new_doc,
    affected_node_ids=["h2-0", "h3-1"]
)

for range in ranges:
    print(f"Modified: L{range.start_line}:{range.start_column} to L{range.end_line}:{range.end_column}")
```

---

### StructureOperations

**Location**: `doctk.integration.operations.StructureOperations`

High-level operations for document structure manipulation. All operations return an `OperationResult` with success status, modified document, and granular edit ranges.

#### Static Methods

##### `promote(document: Document[Node], node_id: str) -> OperationResult`

Decrease heading level by one (e.g., h3 → h2).

**Parameters:**
- `document`: The document to operate on
- `node_id`: The ID of the heading to promote

**Returns:** OperationResult with success status and modified document

**Example:**
```python
from doctk.integration.operations import StructureOperations

result = StructureOperations.promote(doc, "h3-2")
if result.success:
    print(f"Promoted! Modified ranges: {len(result.modified_ranges)}")
    updated_doc = Document.from_string(result.document)
else:
    print(f"Error: {result.error}")
```

##### `demote(document: Document[Node], node_id: str) -> OperationResult`

Increase heading level by one (e.g., h2 → h3).

##### `move_up(document: Document[Node], node_id: str) -> OperationResult`

Move section up among its siblings.

##### `move_down(document: Document[Node], node_id: str) -> OperationResult`

Move section down among its siblings.

##### `nest(document: Document[Node], node_id: str, under_id: str) -> OperationResult`

Nest a section under another section (move as last child).

**Parameters:**
- `document`: The document to operate on
- `node_id`: The ID of the section to nest
- `under_id`: The ID of the target parent section

**Example:**
```python
result = StructureOperations.nest(doc, "h2-3", "h2-1")
# Moves h2-3 to become a child of h2-1 (level adjusted to h3)
```

##### `unnest(document: Document[Node], node_id: str) -> OperationResult`

Un-nest a section (promote it to the level of its parent).

##### `delete(document: Document[Node], node_id: str) -> OperationResult`

Delete a heading and optionally all its content.

**Parameters:**
- `document`: The document to operate on
- `node_id`: The ID of the heading to delete

**Behavior:** Deletes the heading and all nodes until the next heading of same or lower level.

---

### ExtensionBridge

**Location**: `doctk.integration.bridge.ExtensionBridge`

JSON-RPC bridge between TypeScript extension and Python backend.

#### Constructor

```python
ExtensionBridge()
```

#### Methods

##### `handle_request(request: dict[str, Any]) -> dict[str, Any]`

Handle a JSON-RPC request.

**Parameters:**
- `request`: JSON-RPC request dictionary with:
  - `jsonrpc`: "2.0"
  - `id`: Request ID
  - `method`: Method name (e.g., "promote", "demote", "get_document_tree")
  - `params`: Method parameters

**Returns:** JSON-RPC response dictionary

**Example:**
```python
bridge = ExtensionBridge()

request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "promote",
    "params": {
        "document": "# Title\n\n## Section\n",
        "node_id": "h2-0"
    }
}

response = bridge.handle_request(request)
if "result" in response:
    print(f"Success: {response['result']['success']}")
```

##### `run() -> None`

Start the bridge's main loop (reads from stdin, writes to stdout).

**Usage:** This method is called by the extension to start the JSON-RPC server process.

```python
if __name__ == "__main__":
    bridge = ExtensionBridge()
    bridge.run()  # Blocks, processing JSON-RPC requests
```

---

### CompatibilityChecker

**Location**: `doctk.integration.compat.CompatibilityChecker`

Ensures backward compatibility with older doctk core API versions.

#### Constructor

```python
CompatibilityChecker(current_version: str, minimum_version: str = "0.1.0")
```

#### Methods

##### `check_compatibility() -> bool`

Check if current version meets minimum requirements.

**Returns:** True if compatible, False otherwise

##### `check_feature(feature_name: str) -> bool`

Check if a specific feature is available.

**Parameters:**
- `feature_name`: Name of the feature to check

**Example:**
```python
from doctk.integration.compat import CompatibilityChecker

checker = CompatibilityChecker("0.2.0", "0.1.0")
if checker.check_compatibility():
    print("Compatible!")

if checker.check_feature("granular_edits"):
    # Use granular edits
    pass
else:
    # Fall back to full document replacement
    pass
```

---

### DocumentStateManager

**Location**: `doctk.integration.memory.DocumentStateManager`

LRU cache for document states with memory management.

#### Constructor

```python
DocumentStateManager(
    max_cache_size: int = 100,
    max_memory_mb: int = 500
)
```

**Parameters:**
- `max_cache_size`: Maximum number of documents to cache
- `max_memory_mb`: Maximum memory usage in MB

#### Methods

##### `get_document(doc_uri: str) -> Document[Node] | None`

Get a cached document.

##### `put_document(doc_uri: str, document: Document[Node]) -> None`

Cache a document.

##### `get_stats() -> dict[str, Any]`

Get cache statistics.

**Example:**
```python
from doctk.integration.memory import DocumentStateManager

manager = DocumentStateManager(max_cache_size=50, max_memory_mb=250)

# Cache a document
manager.put_document("file:///path/to/doc.md", doc)

# Retrieve it later
cached = manager.get_document("file:///path/to/doc.md")

# Check stats
stats = manager.get_stats()
print(f"Cache hits: {stats['hits']}, misses: {stats['misses']}")
```

---

### PerformanceMonitor

**Location**: `doctk.integration.performance.PerformanceMonitor`

Monitor and report operation performance.

#### Constructor

```python
PerformanceMonitor(slow_threshold_ms: float = 500.0)
```

#### Methods

##### `record_operation(operation_name: str, duration_ms: float) -> None`

Record an operation's duration.

##### `get_slow_operations() -> list[dict[str, Any]]`

Get operations that exceeded the slow threshold.

##### `track(operation_name: str) -> ContextManager`

Context manager for automatic timing.

**Example:**
```python
from doctk.integration.performance import PerformanceMonitor

monitor = PerformanceMonitor(slow_threshold_ms=200.0)

# Manual recording
monitor.record_operation("promote", 150.5)

# Automatic timing with context manager
with monitor.track("complex_operation"):
    # Do work
    result = StructureOperations.nest(doc, "h2-0", "h1-0")

# Get slow operations
slow_ops = monitor.get_slow_operations()
for op in slow_ops:
    print(f"{op['operation']}: {op['duration_ms']:.1f}ms")
```

---

## Data Types

### OperationResult

**Location**: `doctk.integration.protocols.OperationResult`

Result of a document operation.

**Fields:**
- `success: bool` - Whether the operation succeeded
- `document: str` - The modified document as a string
- `error: str | None` - Error message if operation failed
- `modified_ranges: list[ModifiedRange] | None` - Granular edit ranges

### ModifiedRange

**Location**: `doctk.integration.protocols.ModifiedRange`

A text range that was modified by an operation.

**Fields:**
- `start_line: int` - Starting line number (0-indexed)
- `start_column: int` - Starting column number (0-indexed)
- `end_line: int` - Ending line number (0-indexed)
- `end_column: int` - Ending column number (0-indexed)
- `new_text: str` - The new text for this range

### TreeNode

**Location**: `doctk.integration.protocols.TreeNode`

A node in the document tree.

**Fields:**
- `id: str` - Stable node identifier
- `label: str` - Display label (heading text)
- `level: int` - Heading level (1-6, or 0 for root)
- `line: int` - Line number in document
- `column: int` - Column number in document
- `children: list[TreeNode]` - Child nodes

---

## Usage Examples

### Basic Operation Flow

```python
from doctk import Document
from doctk.integration.operations import StructureOperations, DocumentTreeBuilder

# Load document
doc = Document.from_file("example.md")

# Build tree to understand structure
builder = DocumentTreeBuilder(doc)
tree = builder.build_tree_with_ids()

# Find a node
node = builder.find_node("h2-1")
if node:
    # Perform operation
    result = StructureOperations.promote(doc, "h2-1")

    if result.success:
        # Save modified document
        new_doc = Document.from_string(result.document)
        new_doc.to_file("example.md")

        # Use granular edits for editor updates
        if result.modified_ranges:
            for r in result.modified_ranges:
                print(f"Edit at L{r.start_line}:{r.start_column}")
```

### JSON-RPC Server

```python
from doctk.integration.bridge import ExtensionBridge

# Start bridge (blocks, processing stdin/stdout)
bridge = ExtensionBridge()
bridge.run()
```

### Performance Monitoring

```python
from doctk.integration.performance import PerformanceMonitor

monitor = PerformanceMonitor(slow_threshold_ms=200.0)

with monitor.track("batch_operations"):
    for node_id in node_ids:
        with monitor.track(f"promote_{node_id}"):
            result = StructureOperations.promote(doc, node_id)

# Report slow operations
for op in monitor.get_slow_operations():
    print(f"SLOW: {op['operation']} took {op['duration_ms']:.1f}ms")
```

---

## Performance Characteristics

### Time Complexity

| Operation | Complexity | Notes |
|-----------|------------|-------|
| Tree Building | O(n) | With line position caching |
| Node Lookup | O(1) | Via node_map dictionary |
| promote/demote | O(n) | Document serialization |
| move_up/move_down | O(n) | Node reordering + serialization |
| nest/unnest | O(n) | Level adjustment + serialization |
| Diff Computation | O(n×m) | n=affected nodes, m=avg node lines |

### Space Complexity

- **DocumentTreeBuilder**: O(n) for node maps and line caches
- **MemoryManager**: O(k) where k = max_cache_size
- **DiffComputer**: O(m) where m = number of modified ranges

### Performance Requirements

From spec requirements:

- **Tree View Rendering**: ≤ 1 second for 1000 headings ✓
- **User Interactions**: ≤ 200ms for large documents ✓
- **Structural Operations**: ≤ 2 seconds for large documents ✓
- **Memory Usage**: ≤ 500MB per document ✓

---

## Error Handling

All operations follow consistent error handling patterns:

### OperationResult Pattern

```python
result = StructureOperations.promote(doc, "h2-0")

if result.success:
    # Operation succeeded
    updated_doc = Document.from_string(result.document)
else:
    # Operation failed
    print(f"Error: {result.error}")
```

### Common Error Conditions

- **Node Not Found**: `"Node not found: {node_id}"`
- **Invalid Node Type**: `"Node {node_id} is not a heading"`
- **Invalid Operation**: `"Cannot move {node_id} up, already at top"`
- **Validation Error**: `"Cannot nest a section under itself"`

---

## Thread Safety

The core integration layer is **not thread-safe**. Each document operation creates new document instances (immutability pattern), but shared state (caches, monitors) should be protected if used across threads:

```python
import threading

# Thread-safe usage with locks
lock = threading.Lock()
manager = DocumentStateManager()

with lock:
    doc = manager.get_document(uri)
```

---

## Testing

See `tests/unit/test_*.py` for comprehensive test examples covering:

- Unit tests for all operations
- Integration tests for bridge communication
- Performance benchmarks for large documents
- Memory management tests
- Backward compatibility tests

Run tests:

```bash
uv run pytest tests/unit/  # Unit tests
uv run pytest tests/e2e/   # End-to-end tests
uv run pytest -m slow      # Performance tests
```

---

## See Also

- [Pluggable Architecture Design](../design/02-pluggable-architecture.md)
- [DSL API Reference](./dsl.md)
- [LSP API Reference](./lsp.md)
- [Core API Reference](./core.md)
