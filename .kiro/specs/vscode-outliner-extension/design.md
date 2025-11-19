# Design Document: VS Code Outliner Extension

## Overview

This design document describes the architecture and implementation approach for a VS Code extension that provides a tree-based document outliner interface for the doctk project. The extension enables interactive document structure manipulation through drag-and-drop operations, context menus, and keyboard shortcuts.

The outliner provides a GUI interface to the underlying doctk API, allowing users to visualize and manipulate document structure through intuitive visual interactions. The design emphasizes separation of concerns, keeping UI logic decoupled from document manipulation logic to support the broader pluggable architecture.

### Design Principles

- **Separation of Concerns**: UI logic is decoupled from document manipulation logic
- **Reusability**: Core doctk API is the single source of truth for all operations
- **Performance**: Optimized for documents with up to 1000 headings
- **Responsiveness**: All UI operations complete within 500ms
- **Integration**: Seamless integration with VS Code's native features (undo/redo, commands, keybindings)

## Architecture

### Component Overview

**Updated 2025-11-19**: VS Code extension uses `src/doctk/integration/bridge.py` (ExtensionBridge)
for JSON-RPC communication with the platform-agnostic integration layer.

```
┌─────────────────────────────────────────────────────────────┐
│              VS Code Extension (TypeScript)                  │
│              extensions/doctk-outliner/                      │
│  ┌──────────────────┐         ┌─────────────────────────┐  │
│  │  Outliner View   │         │   Document Sync         │  │
│  │  (Tree Provider) │◄────────┤   Manager               │  │
│  └────────┬─────────┘         └──────────┬──────────────┘  │
│           │                               │                  │
│           │                               │                  │
│           ▼                               ▼                  │
│  ┌──────────────────┐         ┌─────────────────────────┐  │
│  │  Operation       │         │   Python Bridge         │  │
│  │  Handler         │────────►│   (JSON-RPC Client)     │  │
│  └──────────────────┘         └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                                          │
                                          │ JSON-RPC over stdio
                                          ▼
                              ┌─────────────────────┐
                              │  Extension Bridge   │
                              │  (Python Backend)   │
                              │  src/doctk/         │
                              │  integration/       │
                              │  bridge.py          │
                              └──────────┬──────────┘
                                         │
                                         ▼
                              ┌─────────────────────┐
                              │  Core Integration   │
                              │  src/doctk/         │
                              │  integration/       │
                              └──────────┬──────────┘
                                         │
                                         ▼
                              ┌─────────────────────┐
                              │  doctk Core API     │
                              │  src/doctk/core.py  │
                              └─────────────────────┘
```

**Key Point**: VS Code extension communicates with Python backend via `ExtensionBridge`,
which provides a JSON-RPC interface to the platform-agnostic integration layer.

### Component Responsibilities

#### Tree Data Provider (DocumentOutlineProvider)

- Renders tree view of document structure
- Handles user interactions (clicks, drag-drop)
- Manages tree state and updates
- Provides context menu integration

#### Document Synchronization Manager

- Manages bidirectional sync between tree view and editor
- Debounces rapid changes to prevent performance issues
- Handles external file modifications
- Coordinates updates across components

#### Operation Handler

- Translates user actions into doctk operations
- Manages operation execution via Python bridge
- Creates workspace edits for document updates
- Integrates with VS Code undo/redo system

#### Python Bridge

- Provides JSON-RPC communication with Python backend
- Manages Python process lifecycle
- Handles request/response serialization
- Implements error recovery and retry logic

## Components and Interfaces

### Tree Data Provider

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

#### Drag-and-Drop API Limitations

**Important Constraint**: VS Code's `TreeDragAndDropController` API has a fundamental limitation that impacts the reordering functionality described in Requirement 2.3.

**What the API Provides:**
- `handleDrop(target: OutlineNode | undefined, ...)`
  - When `target` is **defined**: User dropped onto a specific node
  - When `target` is **undefined**: User dropped at root level

**What the API Does NOT Provide:**
- Drop position information (before/after a node)
- Sibling ordering context
- Index within parent's children

**Implementation Implications:**

| User Action | API Detection | Implementation |
|-------------|---------------|----------------|
| Drop node onto another node | `target` defined | Execute `nest()` operation |
| Drop node at root level | `target` undefined | Execute `unnest()` operation |
| Drop node between siblings | ❌ **Not detectable** | Cannot implement via drag-and-drop |

**Workaround for Requirement 2.3 (Reordering):**

Since precise sibling reordering cannot be achieved through drag-and-drop alone, the implementation provides:

1. **Drag-and-Drop**: Changes hierarchy level (nest/unnest)
2. **Context Menu Operations**: Provides `move_up()` and `move_down()` for precise sibling positioning

This two-step approach fulfills the functional requirements while working within VS Code API constraints:
- User drags to change hierarchy level
- User uses context menu to adjust position within sibling list

**Alternative Considered and Rejected:**

Implementing a custom tree view with full position detection would require:
- Building entire tree UI from scratch (no native VS Code components)
- Reimplementing all VS Code tree view features (accessibility, keyboard nav, etc.)
- Significantly increased complexity with marginal UX improvement

The context menu approach provides equivalent functionality with better reliability.

### Document Synchronization Manager

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

### Operation Handler

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

### Python Bridge

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

## Data Models

### Document Tree Representation

The outliner uses a tree structure that mirrors the document's heading hierarchy.

```typescript
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

### Configuration Schema

```typescript
interface OutlinerConfiguration {
  autoRefresh: boolean;
  refreshDelay: number;        // milliseconds
  showContentPreview: boolean;
  maxPreviewLength: number;

  keybindings: {
    promote: string;
    demote: string;
    moveUp: string;
    moveDown: string;
    delete: string;
  };

  performance: {
    largeDocumentThreshold: number;  // Number of headings
    enableVirtualization: boolean;
  };
}
```

**Design Rationale**: Comprehensive configuration allows users to tune performance and behavior. The `largeDocumentThreshold` enables automatic optimization strategies for large documents.

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

## Document Synchronization

### Bidirectional Sync Strategy

```typescript
class DocumentSyncManager {
  private debounceTimer: NodeJS.Timeout | null = null;
  private readonly DEBOUNCE_DELAY = 300;
  private isUpdating = false;

  onDocumentChange(document: TextDocument): void {
    if (this.isUpdating) return; // Prevent circular updates

    this.debounceUpdate(() => {
      this.treeProvider.updateFromDocument(document);
    });
  }

  async onTreeViewChange(operation: TreeOperation): Promise<void> {
    this.isUpdating = true;
    try {
      await this.operationHandler.executeOperation(operation);
    } finally {
      this.isUpdating = false;
    }
  }

  private debounceUpdate(callback: () => void): void {
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
    }
    this.debounceTimer = setTimeout(callback, this.DEBOUNCE_DELAY);
  }
}
```

**Design Rationale**: The `isUpdating` flag prevents circular updates when tree operations modify the document. Debouncing batches rapid changes while maintaining responsiveness.

**Implementation Status**: ✅ **Completed in Task 7** (PR #19, updated PR #20)
- Created `DocumentSyncManager` class in `extensions/doctk-outliner/src/documentSyncManager.ts`
- Integrated into `extension.ts` with all document change listeners
- Includes comprehensive error handling with recovery mechanisms
- Tracks synchronization version and maintains error history
- **Code Review Improvements (PR #20)**:
  - Removed double debouncing (sync manager delegates to outline provider's debouncing)
  - Added user error notifications for all tree operation failures
  - Removed false external change detection (relied on normal document change events)
  - Fixed race condition in recovery (checks isUpdating flag before recovery)
  - Improved error type handling with formatError() method
  - Extracted magic numbers to named constants for maintainability
  - Updated comments for accuracy and clarity
  - Made all commands consistent by using sync manager

## Error Handling

### Error Recovery Strategy

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

## VS Code Extension Packaging

### Package Configuration

```json
{
  "name": "doctk-outliner",
  "displayName": "doctk Document Outliner",
  "description": "Tree-based document outliner with drag-and-drop support",
  "version": "0.1.0",
  "engines": {
    "vscode": "^1.80.0"
  },
  "activationEvents": [
    "onLanguage:markdown"
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
      },
      {
        "command": "doctk.moveUp",
        "title": "Move Section Up"
      },
      {
        "command": "doctk.moveDown",
        "title": "Move Section Down"
      },
      {
        "command": "doctk.delete",
        "title": "Delete Section"
      }
    ],
    "keybindings": [
      {
        "command": "doctk.promote",
        "key": "ctrl+shift+up",
        "when": "doctkOutlineView.focused"
      },
      {
        "command": "doctk.demote",
        "key": "ctrl+shift+down",
        "when": "doctkOutlineView.focused"
      }
    ]
  }
}
```

**Design Rationale**: Standard VS Code extension packaging ensures easy installation via the marketplace. Command and keybinding contributions integrate seamlessly with VS Code's command palette and keyboard shortcut system.

## Testing Strategy

### Unit Testing

```typescript
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

### Integration Testing

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

**Design Rationale**: Comprehensive testing at all levels ensures reliability. Integration tests catch issues that unit tests might miss, particularly around synchronization and state management.

## Design Decisions Summary

### Key Architectural Decisions

1. **Native VS Code APIs**: Using VS Code's `TreeDataProvider` and `WorkspaceEdit` ensures consistency with the editor and provides built-in features like undo/redo.

1. **JSON-RPC Bridge**: Using JSON-RPC for extension-to-Python communication provides a simple, reliable protocol that's easy to debug.

1. **Debounced Synchronization**: Batching rapid changes prevents excessive updates while maintaining the appearance of real-time synchronization.

1. **Virtual Scrolling**: For large documents, only rendering visible nodes maintains constant memory usage and ensures responsiveness.

1. **Granular Edits**: Computing minimal edits preserves cursor position and undo/redo stack, worth the additional complexity.

### Trade-offs

1. **Full Document Replacement vs. Incremental Edits**

   - **Decision**: Compute minimal edits when possible
   - **Rationale**: Better cursor preservation and performance, worth the complexity

1. **Synchronous vs. Asynchronous Operations**

   - **Decision**: All operations are asynchronous
   - **Rationale**: Prevents UI blocking, essential for large documents

### Requirements Coverage

This design addresses the following requirements:

- **Requirement 1**: Tree-based document outliner - ✅ Fully implemented via TreeDataProvider
- **Requirement 2**: Drag-and-drop structure manipulation - ⚠️ **Partially implemented with API constraint**
  - **2.1** (Visual feedback): ✅ VS Code native drag UI + validation errors
  - **2.2** (Nest on drop onto node): ✅ Fully implemented via `nest()` operation
  - **2.3** (Reorder on drop between nodes): ⚠️ **Not possible via VS Code drag-and-drop API**
    - API limitation: Cannot detect drop position (before/after)
    - **Workaround**: Hierarchy changes via drag-and-drop (nest/unnest), precise positioning via context menu operations (move_up/move_down)
    - Functionality is equivalent, requires two-step interaction
  - **2.4** (Update document): ✅ Fully implemented with granular edits
  - **2.5** (Prevent invalid drops): ✅ Fully implemented with descendant validation
- **Requirement 3**: Context menu operations - ✅ Fully implemented (also compensates for 2.3 limitation)
- **Requirement 4**: Inline editing - 🔜 Planned for Task 5
- **Requirement 5**: Keyboard shortcuts - 🔜 Planned for Task 6
- **Requirement 6**: Undo/redo support - ✅ Fully implemented via WorkspaceEdit integration
- **Requirement 16**: Document synchronization - ✅ Fully implemented with debouncing
- **Requirement 19**: Configuration and customization - 🔜 Planned for Task 10

**Key Design Decision**: The VS Code API limitation for Requirement 2.3 (reordering via drop between siblings) led to a hybrid approach where drag-and-drop handles hierarchy changes and context menu handles precise positioning. This provides equivalent functionality while working within platform constraints.
