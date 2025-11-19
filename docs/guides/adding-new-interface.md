# Guide: Adding a New Interface to doctk

**Audience**: Developers implementing new UIs for doctk
**Prerequisites**: Familiarity with doctk core concepts and the integration layer
**Estimated Time**: 2-4 hours for basic interface

---

## Overview

This guide walks you through adding a new interface (UI implementation) for doctk. The doctk architecture is designed to support multiple interfaces through the pluggable architecture pattern.

### What You'll Learn

- How to implement the `DocumentInterface` protocol
- How to use `StructureOperations` for document manipulation
- How to integrate with `ExtensionBridge` (for remote interfaces)
- Best practices and common patterns

### Example Interfaces

- **VS Code Extension**: TypeScript extension with JSON-RPC bridge ([source](../../extensions/doctk-outliner/))
- **CLI**: Command-line interface ([source](../../src/doctk/cli.py))
- **REPL**: Interactive terminal interface ([source](../../src/doctk/dsl/repl.py))

---

## Step 1: Understand the Architecture

### Component Layers

```
┌─────────────────────────────────────┐
│   Your New Interface (UI)           │  ← You implement this
│   - Display logic                   │
│   - User input handling              │
│   - State management                 │
└──────────────┬──────────────────────┘
               │ uses
┌──────────────▼──────────────────────┐
│   Core Integration Layer             │  ← Already implemented
│   - StructureOperations              │
│   - DocumentTreeBuilder              │
│   - ExtensionBridge (optional)       │
└──────────────┬──────────────────────┘
               │ uses
┌──────────────▼──────────────────────┐
│   doctk Core API                     │
│   - Document / Node                  │
│   - Parsers / Writers                │
└──────────────────────────────────────┘
```

### Key Principle

**Your interface handles UI; integration layer handles document operations.**

---

## Step 2: Choose Your Integration Approach

### Option A: Direct Integration (Python)

**Use when:** Building a Python-based interface (CLI, TUI, Jupyter, etc.)

**Pros:**
- Simple, direct access to integration layer
- No IPC overhead
- Type-safe

**Examples:** REPL, CLI

### Option B: Remote Integration (JSON-RPC)

**Use when:** Building an interface in another language (TypeScript, JavaScript, etc.)

**Pros:**
- Language-agnostic
- Runs in separate process
- Standard protocol

**Examples:** VS Code extension

---

## Step 3: Implement the DocumentInterface Protocol (Optional)

The `DocumentInterface` protocol defines the contract for UI implementations. Implementing it ensures consistency and type safety.

### Protocol Definition

```python
from abc import ABC, abstractmethod
from typing import Any
from doctk.integration.protocols import OperationResult

class DocumentInterface(ABC):
    """Abstract interface for document manipulation UIs."""

    @abstractmethod
    def display_tree(self, tree: Any) -> None:
        """
        Display document structure as a tree.

        Args:
            tree: The document tree to display (TreeNode)
        """
        pass

    @abstractmethod
    def get_user_selection(self) -> Any | None:
        """
        Get currently selected node(s).

        Returns:
            The selected node ID, or None if no selection
        """
        pass

    @abstractmethod
    def apply_operation(self, operation: Any) -> OperationResult:
        """
        Apply an operation and update the display.

        Args:
            operation: The operation to apply

        Returns:
            Result of the operation
        """
        pass

    @abstractmethod
    def show_error(self, message: str) -> None:
        """
        Display an error message to the user.

        Args:
            message: Error message to display
        """
        pass
```

### Implementation Example

```python
from doctk import Document
from doctk.integration.operations import StructureOperations, DocumentTreeBuilder
from doctk.integration.protocols import DocumentInterface, OperationResult

class MyInterface(DocumentInterface):
    def __init__(self, document: Document):
        self.document = document
        self.operations = StructureOperations()
        self.selected_node_id: str | None = None

    def display_tree(self, tree: Any) -> None:
        """Display tree (implement your UI logic)."""
        # Example: Print tree to console
        self._print_tree(tree, indent=0)

    def get_user_selection(self) -> str | None:
        """Get selected node."""
        return self.selected_node_id

    def apply_operation(self, operation: Any) -> OperationResult:
        """Apply operation dynamically."""
        # operation should be a callable that returns OperationResult
        # Example: lambda: self.operations.promote(self.document, node_id)
        result = operation() if callable(operation) else operation

        if result.success:
            # Update internal state
            self.document = Document.from_string(result.document)
            self.refresh_display()

        return result

    def show_error(self, message: str) -> None:
        """Show error."""
        print(f"ERROR: {message}")

    # Helper methods
    def _print_tree(self, node, indent):
        print("  " * indent + f"- {node.label}")
        for child in node.children:
            self._print_tree(child, indent + 1)

    def refresh_display(self):
        """Refresh the display after changes."""
        builder = DocumentTreeBuilder(self.document)
        tree = builder.build_tree_with_ids()
        self.display_tree(tree)
```

---

## Step 4: Use StructureOperations

The `StructureOperations` class provides high-level document manipulation.

### Available Operations

```python
from doctk.integration.operations import StructureOperations

ops = StructureOperations()

# Promote heading (h3 → h2)
result = ops.promote(document, "h2-0")

# Demote heading (h2 → h3)
result = ops.demote(document, "h2-0")

# Move section up among siblings
result = ops.move_up(document, "h2-1")

# Move section down among siblings
result = ops.move_down(document, "h2-1")

# Nest section under another
result = ops.nest(document, "h2-2", "h1-0")

# Un-nest section
result = ops.unnest(document, "h3-0")

# Delete section
result = ops.delete(document, "h2-1")
```

### Handling Results

```python
result = ops.promote(document, node_id)

if result.success:
    # Operation succeeded
    new_document = Document.from_string(result.document)

    # Use granular edits if available (for editor integrations)
    if result.modified_ranges:
        for range in result.modified_ranges:
            apply_edit(range.start_line, range.start_column,
                       range.end_line, range.end_column,
                       range.new_text)
    else:
        # Fallback: Replace entire document
        replace_document(result.document)
else:
    # Operation failed
    show_error(result.error)
```

---

## Step 5: Build Document Trees

Use `DocumentTreeBuilder` to create hierarchical tree representations.

### Basic Usage

```python
from doctk import Document
from doctk.integration.operations import DocumentTreeBuilder

# Load document
doc = Document.from_file("example.md")

# Build tree
builder = DocumentTreeBuilder(doc)
tree = builder.build_tree_with_ids()

# Tree has stable node IDs
print(f"Root: {tree.label}")
for child in tree.children:
    print(f"  - {child.id}: {child.label} (level {child.level})")
```

### Node ID Format

Node IDs follow the format: `h{level}-{index}`

**Examples:**
- `h1-0`: First h1 heading
- `h2-1`: Second h2 heading
- `h3-0`: First h3 heading

### Tree Structure

```python
@dataclass
class TreeNode:
    id: str                    # "h2-0"
    label: str                 # "Introduction"
    level: int                 # 2
    line: int                  # 10
    column: int                # 0
    children: list[TreeNode]   # Child nodes
```

---

## Step 6: Handle User Input

### Pattern: Operation Execution

```python
def handle_user_action(self, action: str, node_id: str):
    """Handle user-initiated actions."""
    # Map user action to operation
    operation_map = {
        "promote": lambda: self.operations.promote(self.document, node_id),
        "demote": lambda: self.operations.demote(self.document, node_id),
        "move_up": lambda: self.operations.move_up(self.document, node_id),
        "move_down": lambda: self.operations.move_down(self.document, node_id),
        "delete": lambda: self.operations.delete(self.document, node_id),
    }

    # Execute operation
    operation = operation_map.get(action)
    if not operation:
        self.show_error(f"Unknown action: {action}")
        return

    result = operation()

    if result.success:
        # Update document
        self.document = Document.from_string(result.document)
        self.refresh_display()
    else:
        self.show_error(result.error)
```

---

## Step 7: Implement State Management

### Document State

```python
class MyInterface:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.document = Document.from_file(file_path)
        self.is_modified = False

    def handle_operation(self, operation_fn):
        """Wrapper for operations that tracks modifications."""
        result = operation_fn()

        if result.success:
            self.document = Document.from_string(result.document)
            self.is_modified = True
            self.refresh_display()
            return True
        else:
            self.show_error(result.error)
            return False

    def save(self):
        """Save document."""
        if self.is_modified:
            self.document.to_file(self.file_path)
            self.is_modified = False
```

### Undo/Redo (Optional)

```python
class MyInterface:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.document = Document.from_file(file_path)
        self.history: list[str] = [self.document.to_string()]
        self.history_index = 0

    def handle_operation(self, operation_fn):
        """Execute operation and add to history."""
        result = operation_fn()

        if result.success:
            self.document = Document.from_string(result.document)

            # Add to history (clear redo stack)
            self.history = self.history[:self.history_index + 1]
            self.history.append(result.document)
            self.history_index += 1

            self.refresh_display()
            return True
        return False

    def undo(self):
        """Undo last operation."""
        if self.history_index > 0:
            self.history_index -= 1
            self.document = Document.from_string(self.history[self.history_index])
            self.refresh_display()

    def redo(self):
        """Redo last undone operation."""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.document = Document.from_string(self.history[self.history_index])
            self.refresh_display()
```

---

## Step 8: Remote Integration (JSON-RPC)

For interfaces in other languages (TypeScript, JavaScript, etc.), use the `ExtensionBridge`.

### Start the Bridge (Python)

```python
from doctk.integration.bridge import ExtensionBridge

# Start JSON-RPC server (reads from stdin, writes to stdout)
bridge = ExtensionBridge()
bridge.run()  # Blocks, processing requests
```

### Client Implementation (TypeScript Example)

```typescript
import { spawn, ChildProcess } from 'child_process';

class DoctkClient {
    private process: ChildProcess;
    private requestId = 0;

    constructor() {
        this.process = spawn('python', ['-m', 'doctk.integration.bridge']);
    }

    async request(method: string, params: any): Promise<any> {
        const id = ++this.requestId;

        const request = {
            jsonrpc: '2.0',
            id,
            method,
            params
        };

        this.process.stdin!.write(JSON.stringify(request) + '\n');

        return new Promise((resolve, reject) => {
            this.process.stdout!.once('data', (data) => {
                const response = JSON.parse(data.toString());

                if (response.error) {
                    reject(new Error(response.error.message));
                } else {
                    resolve(response.result);
                }
            });
        });
    }

    async promote(document: string, nodeId: string) {
        return this.request('promote', { document, node_id: nodeId });
    }

    async demote(document: string, nodeId: string) {
        return this.request('demote', { document, node_id: nodeId });
    }

    // ... other operations
}

// Usage
const client = new DoctkClient();
const result = await client.promote(documentText, 'h2-0');
if (result.success) {
    updateEditor(result.document);
}
```

---

## Complete Example: Jupyter Lab Widget

Here's a complete example of a JupyterLab widget interface.

**Prerequisites:**
```bash
pip install ipywidgets  # Required for this example
```

```python
# jupyterlab_doctk_widget.py
from ipywidgets import VBox, HBox, Button, Output, HTML
from IPython.display import display
from doctk import Document
from doctk.integration.operations import StructureOperations, DocumentTreeBuilder
from doctk.integration.protocols import DocumentInterface

class DoctkWidget(DocumentInterface):
    """JupyterLab widget for doctk."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.document = Document.from_file(file_path)
        self.operations = StructureOperations()
        self.selected_node_id: str | None = None

        # Create widgets
        self.tree_output = Output()
        self.error_output = Output()

        # Create buttons
        self.promote_btn = Button(description="Promote")
        self.demote_btn = Button(description="Demote")
        self.save_btn = Button(description="Save")

        # Wire up handlers
        self.promote_btn.on_click(lambda b: self._handle_promote())
        self.demote_btn.on_click(lambda b: self._handle_demote())
        self.save_btn.on_click(lambda b: self._handle_save())

        # Layout
        button_box = HBox([self.promote_btn, self.demote_btn, self.save_btn])
        self.widget = VBox([button_box, self.tree_output, self.error_output])

        # Initial display
        self.refresh_display()

    def display(self):
        """Display the widget."""
        display(self.widget)

    def display_tree(self, tree):
        """Display tree as HTML."""
        html = self._tree_to_html(tree)
        with self.tree_output:
            self.tree_output.clear_output()
            display(HTML(html))

    def get_user_selection(self):
        """Get selected node."""
        return self.selected_node_id

    def apply_operation(self, operation):
        """Apply operation."""
        result = operation()

        if result.success:
            self.document = Document.from_string(result.document)
            self.refresh_display()

        return result

    def show_error(self, message):
        """Show error."""
        with self.error_output:
            self.error_output.clear_output()
            print(f"❌ {message}")

    # Event handlers
    def _handle_promote(self):
        if not self.selected_node_id:
            self.show_error("No node selected")
            return

        result = self.operations.promote(self.document, self.selected_node_id)
        if result.success:
            # Update document state
            self.document = Document.from_string(result.document)
            self.refresh_display()
        else:
            self.show_error(result.error)

    def _handle_demote(self):
        if not self.selected_node_id:
            self.show_error("No node selected")
            return

        result = self.operations.demote(self.document, self.selected_node_id)
        if result.success:
            # Update document state
            self.document = Document.from_string(result.document)
            self.refresh_display()
        else:
            self.show_error(result.error)

    def _handle_save(self):
        self.document.to_file(self.file_path)
        print(f"✅ Saved to {self.file_path}")

    # Helper methods
    def refresh_display(self):
        """Refresh display after changes."""
        builder = DocumentTreeBuilder(self.document)
        tree = builder.build_tree_with_ids()
        self.display_tree(tree)

    def _tree_to_html(self, node, level=0):
        """Convert tree to HTML."""
        import html

        indent = "  " * level
        # Escape HTML to prevent injection
        safe_id = html.escape(node.id, quote=True)
        safe_label = html.escape(node.label)

        html_str = f"{indent}<div style='margin-left: {level*20}px;'>"
        html_str += f"<a href='#' onclick='selectNode(\"{safe_id}\")'>{safe_label}</a>"
        html_str += "</div>"

        for child in node.children:
            html_str += self._tree_to_html(child, level + 1)

        return html_str

# Usage in Jupyter notebook:
# widget = DoctkWidget("document.md")
# widget.display()
```

---

## Best Practices

### 1. Always Handle Errors

```python
result = self.operations.promote(document, node_id)

if not result.success:
    # ALWAYS check success before using result
    self.show_error(result.error)
    return
```

### 2. Use Granular Edits for Editors

```python
if result.modified_ranges:
    # Apply precise edits (better UX)
    for range in result.modified_ranges:
        apply_edit(range)
else:
    # Fallback to full document replacement
    replace_document(result.document)
```

### 3. Keep UI Logic Separate

```python
# ✅ Good: Separation of concerns
class MyInterface:
    def __init__(self):
        self.operations = StructureOperations()  # Business logic

    def on_button_click(self):
        # UI event handler calls business logic
        result = self.operations.promote(...)

# ❌ Bad: Mixed concerns
class MyInterface:
    def on_button_click(self):
        # Don't manipulate document AST directly in UI code
        doc.nodes[0].level -= 1  # NO!
```

### 4. Cache DocumentTreeBuilder

```python
# ✅ Good: Cache builder if document unchanged
class MyInterface:
    def __init__(self, document):
        self.document = document
        self._builder = DocumentTreeBuilder(document)

    def on_document_change(self, new_document):
        self.document = new_document
        self._builder = DocumentTreeBuilder(new_document)  # Rebuild
```

### 5. Use Type Annotations

```python
from doctk import Document
from doctk.integration.protocols import OperationResult

def handle_operation(
    self,
    document: Document,
    node_id: str
) -> OperationResult:
    """Type annotations improve IDE support and catch bugs."""
    pass
```

---

## Testing Your Interface

### Unit Tests

```python
import pytest
from doctk import Document
from your_interface import MyInterface

def test_interface_promotes_heading():
    """Test that interface correctly promotes headings."""
    doc_text = "# Title\n\n## Section\n"
    doc = Document.from_string(doc_text)

    interface = MyInterface(doc)
    interface.selected_node_id = "h2-0"

    result = interface.apply_operation(
        lambda: interface.operations.promote(doc, "h2-0")
    )

    assert result.success
    assert "# Section" in result.document
```

### Integration Tests

```python
def test_full_workflow():
    """Test complete user workflow."""
    interface = MyInterface("test.md")

    # Select node
    interface.selected_node_id = "h2-1"

    # Execute operation
    interface._handle_promote()

    # Verify state
    assert interface.is_modified
    assert interface.document != interface.original_document
```

---

## Troubleshooting

### Issue: "Node not found"

**Cause:** Node ID is invalid or document has changed.

**Solution:**
```python
# Always rebuild tree after operations
builder = DocumentTreeBuilder(self.document)
tree = builder.build_tree_with_ids()

# Use fresh node IDs
node = builder.find_node(old_node_id)
if node:
    # Found
    pass
else:
    # Node no longer exists
    self.show_error("Node not found")
```

### Issue: Granular edits don't preserve cursor

**Cause:** Incorrect line/column calculation.

**Solution:** Always use backend-computed `modified_ranges`:

```python
# ✅ Good: Use backend ranges
for range in result.modified_ranges:
    editor.apply_edit(range)

# ❌ Bad: Compute ranges in frontend
# Don't do this!
```

---

## Additional Resources

- [Core Integration API Reference](../api/core-integration.md)
- [Pluggable Architecture Design](../design/02-pluggable-architecture.md)
- [VS Code Extension Source](../../extensions/doctk-outliner/)
- [REPL Source](../../src/doctk/dsl/repl.py)
- [Architecture Decisions](../design/03-core-integration-decisions.md)

---

## Getting Help

- **Issues**: https://github.com/tommcd/doctk/issues
- **Discussions**: https://github.com/tommcd/doctk/discussions
- **Examples**: See `examples/` directory

---

**Next Steps:**

1. Study existing interfaces (REPL, VS Code extension)
2. Choose your integration approach (direct vs. remote)
3. Implement `DocumentInterface` protocol
4. Test thoroughly
5. Share your interface with the community!
