# Requirements Document: VS Code Outliner Extension

## Introduction

This document specifies the requirements for a VS Code extension that provides a tree-based document outliner interface for the doctk project. The outliner enables interactive document structure manipulation through drag-and-drop operations, context menus, and keyboard shortcuts, providing a GUI interface to the underlying doctk API.

## Glossary

- **doctk**: Document toolkit - a composable, functional toolkit for structured document manipulation
- **Outliner**: A tree-based view of document structure similar to MS Word's outline view
- **Tree View**: A hierarchical visual representation of document structure in the VS Code sidebar
- **Operation**: A transformation function in doctk (e.g., promote, demote, nest, unnest)
- **Extension Host**: The VS Code process that runs extensions

## Requirements

### Requirement 1: Tree-Based Document Outliner

**User Story:** As a technical writer, I want to view my document structure as a hierarchical tree, so that I can understand the organization at a glance.

#### Acceptance Criteria

1. WHEN a Markdown document is opened in VS Code, THE Outliner SHALL display the document structure as a tree view in the sidebar
1. WHEN the document contains headings, THE Outliner SHALL represent each heading as a tree node with its level indicated
1. WHEN a heading has child content or subheadings, THE Outliner SHALL display these as nested child nodes
1. WHEN the document structure changes, THE Outliner SHALL update the tree view within 500 milliseconds
1. WHEN a user clicks on a tree node, THE Outliner SHALL navigate the editor to the corresponding location in the document

### Requirement 2: Drag-and-Drop Structure Manipulation

**User Story:** As a content editor, I want to reorganize document sections by dragging and dropping them in the outliner, so that I can quickly restructure my document without manual cut-and-paste.

#### Acceptance Criteria

1. WHEN a user drags a tree node, THE Outliner SHALL provide visual feedback indicating valid drop targets
1. WHEN a user drops a node onto another node, THE Outliner SHALL nest the dragged section under the target section
1. WHEN a user drops a node between two nodes, THE Outliner SHALL reorder the section to the new position
1. WHEN a drag-and-drop operation completes, THE Outliner SHALL update the underlying Markdown document to reflect the structural change
1. WHEN a drag-and-drop operation is invalid, THE Outliner SHALL prevent the drop and display a visual indicator

### Requirement 3: Context Menu Operations

**User Story:** As a document author, I want to right-click on sections in the outliner and apply precise structural operations, so that I can make exact transformations without relying solely on drag-and-drop positioning.

#### Acceptance Criteria

1. WHEN a user right-clicks on a tree node, THE Outliner SHALL display a context menu with available operations
1. WHEN the context menu includes "Promote", THE Outliner SHALL decrease the heading level by one when selected
1. WHEN the context menu includes "Demote", THE Outliner SHALL increase the heading level by one when selected
1. WHEN the context menu includes "Move Up", THE Outliner SHALL move the section up in sibling order when selected
1. WHEN the context menu includes "Move Down", THE Outliner SHALL move the section down in sibling order when selected
1. WHEN the context menu includes "Delete", THE Outliner SHALL remove the section from the document when selected
1. WHEN an operation is applied, THE Outliner SHALL update both the tree view and the document within 500 milliseconds

### Requirement 4: Inline Editing in Tree View

**User Story:** As a writer, I want to edit heading text directly in the outliner tree view, so that I can make quick changes without switching to the main editor.

#### Acceptance Criteria

1. WHEN a user double-clicks on a tree node label, THE Outliner SHALL enable inline editing mode for that node
1. WHEN inline editing mode is active, THE Outliner SHALL display a text input field with the current heading text
1. WHEN a user presses Enter or clicks outside the input field, THE Outliner SHALL save the changes to the document
1. WHEN a user presses Escape, THE Outliner SHALL cancel editing and restore the original text
1. WHEN the heading text is updated, THE Outliner SHALL update the corresponding heading in the Markdown document

### Requirement 5: Keyboard Shortcuts for Structure Operations

**User Story:** As a power user, I want to use keyboard shortcuts to manipulate document structure, so that I can work efficiently without using the mouse.

#### Acceptance Criteria

1. WHEN a tree node is selected and the user presses a promote shortcut, THE Outliner SHALL promote the selected section
1. WHEN a tree node is selected and the user presses a demote shortcut, THE Outliner SHALL demote the selected section
1. WHEN a tree node is selected and the user presses a move-up shortcut, THE Outliner SHALL move the section up
1. WHEN a tree node is selected and the user presses a move-down shortcut, THE Outliner SHALL move the section down
1. WHEN a tree node is selected and the user presses a delete shortcut, THE Outliner SHALL delete the section

### Requirement 6: Undo/Redo Support

**User Story:** As a document editor, I want to undo and redo structural changes made through the outliner, so that I can experiment with different organizations without fear of losing work.

#### Acceptance Criteria

1. WHEN a structural operation is performed through the Outliner, THE Extension SHALL add the operation to VS Code's undo stack
1. WHEN a user triggers undo, THE Extension SHALL revert the last structural change in both the document and tree view
1. WHEN a user triggers redo, THE Extension SHALL reapply the last undone structural change
1. WHEN multiple operations are performed, THE Extension SHALL maintain a complete undo history
1. WHEN the document is saved, THE Extension SHALL preserve the undo history

### Requirement 16: Document Synchronization

**User Story:** As a user working with the outliner, I want changes made in the tree view to immediately reflect in the editor and vice versa, so that I have a consistent view of my document.

#### Acceptance Criteria

1. WHEN a change is made in the outliner, THE Extension SHALL update the editor content within 500 milliseconds
1. WHEN a change is made in the editor, THE Extension SHALL update the outliner tree view within 500 milliseconds
1. WHEN multiple changes occur rapidly, THE Extension SHALL batch updates to prevent performance degradation
1. WHEN synchronization fails, THE Extension SHALL display an error message and attempt recovery
1. WHEN the document is modified externally, THE Extension SHALL detect changes and update both views

### Requirement 19: Configuration and Customization

**User Story:** As a user, I want to configure the outliner appearance and behavior, so that I can adapt it to my workflow preferences.

#### Acceptance Criteria

1. WHEN configuration options are available, THE Extension SHALL provide settings for keyboard shortcuts
1. WHEN configuration options are available, THE Extension SHALL provide settings for tree view appearance
1. WHEN configuration options are available, THE Extension SHALL provide settings for auto-save behavior
1. WHEN settings are changed, THE Extension SHALL apply changes without requiring a restart
1. WHEN invalid settings are provided, THE Extension SHALL use default values and display a warning
