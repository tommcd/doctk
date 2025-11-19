# Pluggable Architecture for Document Interfaces

**Status**: Implemented (v0.2.0)
**Last Updated**: 2025-11-19
**Related Spec**: `.kiro/specs/doctk-core-integration`

## Overview

The doctk pluggable architecture provides a clean separation between document manipulation logic and user interface implementations. This design enables multiple interface implementations (VS Code, JupyterLab, web, CLI) to share the same core document manipulation capabilities without code duplication.

## Design Principles

1. **Separation of Concerns**: UI logic is completely decoupled from document manipulation logic
1. **Reusability**: Core doctk API is the single source of truth for all operations
1. **Extensibility**: New interfaces can be added without modifying core functionality
1. **Consistency**: All interfaces use identical operation semantics
1. **Type Safety**: Abstract protocols ensure interface implementations are complete

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Interface Layer (Pluggable)              │
│  ┌──────────────────┐         ┌──────────────────────┐     │
│  │  VS Code         │         │  JupyterLab          │     │
│  │  Interface       │         │  Interface (Future)  │     │
│  └────────┬─────────┘         └──────────┬───────────┘     │
└───────────┼────────────────────────────────┼────────────────┘
            │                                │
            └────────────┬───────────────────┘
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
              │  - Parser/Writer    │
              └─────────────────────┘
```

## DocumentInterface Protocol

The `DocumentInterface` abstract base class defines the contract that all UI implementations must satisfy.

### Location

```python
from doctk.lsp.protocols import DocumentInterface
```

### Required Methods

```python
class DocumentInterface(ABC):
    """Abstract interface for document manipulation UIs."""

    @abstractmethod
    def display_tree(self, tree: Any) -> None:
        """
        Display document structure as a tree.

        Args:
            tree: The document tree to display (typically a TreeNode)
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
            Result of the operation (success, document, modified_ranges, error)
        """
        pass

    @abstractmethod
    def show_error(self, message: str) -> None:
        """
        Display error message to user.

        Args:
            message: The error message to display
        """
        pass
```

## Shared Core Components

All interfaces share these core components without modification:

### 1. StructureOperations

High-level document manipulation operations:

- `promote(document, node_id)` - Decrease heading level
- `demote(document, node_id)` - Increase heading level
- `move_up(document, node_id)` - Move section up among siblings
- `move_down(document, node_id)` - Move section down among siblings
- `nest(document, node_id, parent_id)` - Nest section under parent
- `unnest(document, node_id)` - Un-nest section (promote level)
- `delete(document, node_id)` - Delete section and subsections

### 2. ExtensionBridge

JSON-RPC bridge for TypeScript-Python communication (primarily for VS Code, but reusable):

- Handles request/response serialization
- Provides granular edit computation
- Manages error propagation
- Supports stdin/stdout communication

### 3. Script Executor

DSL execution engine for running doctk scripts:

- Supports REPL (interactive)
- Supports file execution (`.tk` files)
- Supports code block execution (Markdown `doctk` blocks)

### 4. DocumentTreeBuilder

Builds hierarchical tree structures with backend-assigned node IDs:

- Single source of truth for node IDs
- Provides tree structure for display
- Computes line/column positions

## Implementation Guide

### Creating a New Interface

Follow these steps to create a new interface implementation (e.g., for JupyterLab):

#### Step 1: Implement DocumentInterface

```python
from doctk.lsp.protocols import DocumentInterface, OperationResult, TreeNode
from doctk.lsp.operations import StructureOperations, DocumentTreeBuilder
from doctk.core import Document

class JupyterLabInterface(DocumentInterface):
    """JupyterLab implementation of document interface."""

    def __init__(self):
        self.operations = StructureOperations()
        self.current_document: Document | None = None
        self.current_tree: TreeNode | None = None
        self.selected_node_id: str | None = None

    def display_tree(self, tree: TreeNode) -> None:
        """Render tree in JupyterLab widget."""
        self.current_tree = tree
        # JupyterLab-specific tree rendering
        # Example: Use ipywidgets Tree widget
        from ipywidgets import Tree
        tree_widget = self._build_tree_widget(tree)
        display(tree_widget)

    def get_user_selection(self) -> str | None:
        """Get selected node from JupyterLab widget."""
        return self.selected_node_id

    def apply_operation(self, operation: str) -> OperationResult:
        """Execute operation and update display."""
        if not self.current_document or not self.selected_node_id:
            return OperationResult(
                success=False,
                error="No document loaded or no node selected"
            )

        # Delegate to shared operations
        operation_map = {
            'promote': self.operations.promote,
            'demote': self.operations.demote,
            'move_up': self.operations.move_up,
            'move_down': self.operations.move_down,
            'nest': self.operations.nest,
            'unnest': self.operations.unnest,
        }

        op_fn = operation_map.get(operation)
        if not op_fn:
            return OperationResult(success=False, error=f"Unknown operation: {operation}")

        # Store original node for ID remapping
        original_node = None
        if self.current_document:
            builder_pre = DocumentTreeBuilder(self.current_document)
            original_node = builder_pre.find_node(self.selected_node_id)

        result = op_fn(self.current_document, self.selected_node_id)

        if result.success and result.document is not None:
            # Update current document (check for None - operations may return only granular edits)
            self.current_document = Document.from_string(result.document)
            # Rebuild and refresh tree display
            builder = DocumentTreeBuilder(self.current_document)
            self.current_tree = builder.build_tree_with_ids()
            self.display_tree(self.current_tree)

            # Remap selected node ID (node IDs change after promote/demote/move)
            if original_node is not None:
                self.selected_node_id = self._remap_node_id(original_node, builder)

        return result

    def show_error(self, message: str) -> None:
        """Display error in JupyterLab."""
        # JupyterLab-specific error display
        from IPython.display import display, HTML
        display(HTML(f'<div style="color: red;">Error: {message}</div>'))

    def load_document(self, file_path: str) -> None:
        """Load a document and display its tree."""
        self.current_document = Document.from_file(file_path)
        builder = DocumentTreeBuilder(self.current_document)
        self.current_tree = builder.build_tree_with_ids()
        self.display_tree(self.current_tree)

    def on_node_selected(self, node_id: str) -> None:
        """Callback when user selects a node in the tree."""
        self.selected_node_id = node_id

    def on_promote_clicked(self) -> None:
        """Callback when user clicks promote button."""
        result = self.apply_operation('promote')
        if not result.success:
            self.show_error(result.error)

    def _build_tree_widget(self, node: TreeNode):
        """Build ipywidgets Tree widget from TreeNode (helper method)."""
        from ipywidgets import Tree
        # Recursive tree building logic
        # This is a placeholder - actual implementation depends on ipywidgets API
        return Tree()

    def _remap_node_id(self, original_node, builder: DocumentTreeBuilder) -> str | None:
        """
        Find the new ID for a node after the tree has been rebuilt.

        After operations like promote/demote, node IDs change because they
        encode structural information (e.g., h2-0 becomes h1-0 after promote).
        This finds the same node in the new tree by matching content.
        """
        from doctk.core import Heading
        if isinstance(original_node, Heading):
            for node_id, node in builder.node_map.items():
                if isinstance(node, Heading) and node.text == original_node.text:
                    return node_id
        return None
```

**Note**: The complete class above includes all methods. Steps 2 and 3 have been consolidated into the main class definition.

### VS Code Implementation

For VS Code, the interface implementation is split between:

1. **TypeScript Extension** (UI layer)

   - Implements tree view using `vscode.TreeDataProvider`
   - Handles user interactions (clicks, drag-and-drop, context menus)
   - Communicates with Python via ExtensionBridge (JSON-RPC)

1. **PythonBridge Client** (TypeScript)

   - Spawns Python process running ExtensionBridge
   - Sends JSON-RPC requests for operations
   - Receives operation results with granular edits
   - Applies edits to document using `vscode.WorkspaceEdit`

See `.kiro/specs/vscode-outliner-extension` for detailed VS Code implementation.

## Key Design Decisions

### 1. Abstract Interface vs. Concrete Base Class

**Decision**: Use abstract base class (ABC) rather than Protocol

**Rationale**:

- Enforces implementation of all required methods at instantiation time
- Provides better error messages when methods are missing
- Allows shared helper methods in the base class (future extension)

### 2. Tree Structure Ownership

**Decision**: Backend owns tree structure and node IDs

**Rationale**:

- Eliminates synchronization issues between frontend and backend
- Single source of truth for document structure
- Simplifies frontend implementation (no ID generation logic needed)

### 3. Operation Results with Granular Edits

**Decision**: Operations return both full document and modified ranges

**Rationale**:

- Full document provides fallback for simple implementations
- Granular edits enable sophisticated UIs to preserve cursor position and undo/redo
- Minimal performance overhead (computed once per operation)

### 4. Immutable Operations

**Decision**: All operations return new Document instances rather than mutating

**Rationale**:

- Simplifies undo/redo implementation
- Prevents state inconsistencies
- Aligns with functional programming principles of doctk core
- Thread-safe by design

## Example: Minimal CLI Interface

Here's a minimal command-line interface implementation:

```python
from doctk.lsp.protocols import DocumentInterface, OperationResult, TreeNode
from doctk.lsp.operations import StructureOperations, DocumentTreeBuilder
from doctk.core import Document

class CLIInterface(DocumentInterface):
    """Simple command-line interface for doctk."""

    def __init__(self):
        self.operations = StructureOperations()
        self.document: Document | None = None
        self.tree: TreeNode | None = None

    def display_tree(self, tree: TreeNode) -> None:
        """Print tree to console."""
        def print_node(node, indent=0):
            prefix = "  " * indent
            print(f"{prefix}- {node.label} [{node.id}] (line {node.line})")
            for child in node.children:
                print_node(child, indent + 1)

        print("\nDocument Structure:")
        print_node(tree)

    def get_user_selection(self) -> str | None:
        """Prompt user for node ID."""
        return input("Enter node ID (e.g., h1-0): ").strip()

    def apply_operation(self, operation: str) -> OperationResult:
        """Execute operation on selected node."""
        node_id = self.get_user_selection()
        if not node_id or not self.document:
            return OperationResult(success=False, error="Invalid selection")

        # Map operations to methods
        op_map = {
            'promote': self.operations.promote,
            'demote': self.operations.demote,
            'move_up': self.operations.move_up,
            'move_down': self.operations.move_down,
        }

        op_fn = op_map.get(operation)
        if not op_fn:
            return OperationResult(success=False, error=f"Unknown operation: {operation}")

        result = op_fn(self.document, node_id)

        if result.success:
            self.document = Document.from_string(result.document)
            builder = DocumentTreeBuilder(self.document)
            self.tree = builder.build_tree_with_ids()

        return result

    def show_error(self, message: str) -> None:
        """Print error to console."""
        print(f"\n❌ Error: {message}\n")

    def run(self, file_path: str) -> None:
        """Main loop."""
        # Load document
        self.document = Document.from_file(file_path)
        builder = DocumentTreeBuilder(self.document)
        self.tree = builder.build_tree_with_ids()

        # Display initial tree
        self.display_tree(self.tree)

        # Main loop
        while True:
            print("\nOperations: promote, demote, move_up, move_down, tree, save, quit")
            command = input("Command: ").strip().lower()

            if command == 'quit':
                break
            elif command == 'tree':
                self.display_tree(self.tree)
            elif command == 'save':
                output_path = input("Save to: ").strip()
                self.document.to_file(output_path)
                print(f"✅ Saved to {output_path}")
            elif command in ['promote', 'demote', 'move_up', 'move_down']:
                result = self.apply_operation(command)
                if result.success:
                    print("✅ Operation successful")
                    self.display_tree(self.tree)
                else:
                    self.show_error(result.error)
            else:
                print("Unknown command")

# Usage
if __name__ == "__main__":
    interface = CLIInterface()
    interface.run("document.md")
```

## Benefits of This Architecture

1. **No Code Duplication**: Document manipulation logic is written once and shared
1. **Consistent Behavior**: All interfaces behave identically for the same operations
1. **Easy Testing**: Core logic can be tested independently of UI frameworks
1. **Future-Proof**: New interfaces can be added without modifying existing code
1. **Flexible Deployment**: Same core can run in VS Code, JupyterLab, web, or CLI
1. **Clear Contracts**: Abstract interface makes requirements explicit

## Future Interfaces

Potential future interface implementations:

- **Web Interface**: Browser-based editor using React/Vue with WebAssembly backend
- **Emacs Interface**: Emacs Lisp frontend calling Python backend via JSON-RPC
- **Vim Interface**: Vim plugin with Python integration
- **API Server**: REST/GraphQL API for document manipulation
- **GitHub Action**: Automated document transformation in CI/CD

## Testing the Interface

See `tests/unit/test_interface.py` for examples of testing `DocumentInterface` implementations.

Key testing strategies:

1. **Contract Testing**: Verify that implementations satisfy the interface contract
1. **Behavior Testing**: Ensure operations produce expected results
1. **Error Handling**: Test error conditions and edge cases
1. **Integration Testing**: Test interaction between interface and core components

## References

- **Implementation**: `src/doctk/lsp/protocols.py` (DocumentInterface definition)
- **Spec**: `.kiro/specs/doctk-core-integration/design.md` (Pluggable Architecture section)
- **VS Code Example**: `.kiro/specs/vscode-outliner-extension/design.md`
- **Related Design**: `docs/design/01-initial-design.md` (Core abstractions)
