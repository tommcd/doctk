# Requirements Document: Document Outliner with LSP

## Introduction

This document specifies the requirements for a Document Outliner with Language Server Protocol (LSP) support for the doctk project. The system enables interactive document structure manipulation through a VS Code extension with a tree-based outliner interface, backed by a language server that provides intelligent code completion, validation, and documentation for the doctk DSL (Domain-Specific Language).

The outliner provides a GUI interface to the underlying doctk API, allowing users to visualize and manipulate document structure through drag-and-drop operations, context menus, and keyboard shortcuts. The LSP server ensures that both human users and AI agents can effectively work with the doctk DSL through real-time validation, auto-completion, and inline documentation.

## Glossary

- **doctk**: Document toolkit - a composable, functional toolkit for structured document manipulation
- **DSL**: Domain-Specific Language - the doctk operation syntax (e.g., `select heading | where level=2 | promote`)
- **LSP**: Language Server Protocol - a protocol for providing language intelligence features
- **Outliner**: A tree-based view of document structure similar to MS Word's outline view
- **UDAST**: Universal Document AST - the internal representation of documents in doctk
- **Tree View**: A hierarchical visual representation of document structure in the VS Code sidebar
- **Operation**: A transformation function in doctk (e.g., promote, demote, nest, unnest)
- **Extension Host**: The VS Code process that runs extensions
- **Language Client**: The VS Code extension component that communicates with the language server
- **Language Server**: The backend process that provides language intelligence features
- **REPL**: Read-Eval-Print Loop - an interactive command-line interface

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

### Requirement 7: Language Server for DSL

**User Story:** As a developer, I want a language server that understands the doctk DSL, so that I can write transformation scripts with intelligent code completion and validation.

#### Acceptance Criteria

1. WHEN a `.tk` file is opened in VS Code, THE Language Server SHALL activate and provide language features
1. WHEN doctk DSL code is present in a Markdown code block with language identifier `doctk`, THE Language Server SHALL provide language features
1. WHEN the Language Server starts, THE Language Server SHALL initialize within 2 seconds
1. WHEN the Language Server encounters an error, THE Language Server SHALL log diagnostic information
1. WHEN a document is closed, THE Language Server SHALL release associated resources

### Requirement 8: Real-Time Syntax Validation

**User Story:** As a script author, I want real-time feedback on syntax errors in my doctk scripts, so that I can fix issues immediately while writing.

#### Acceptance Criteria

1. WHEN invalid DSL syntax is typed, THE Language Server SHALL display error diagnostics within 500 milliseconds
1. WHEN an unknown operation is used, THE Language Server SHALL report an error with the operation name
1. WHEN operation arguments are invalid, THE Language Server SHALL report an error with expected argument types
1. WHEN syntax errors are fixed, THE Language Server SHALL clear the error diagnostics within 500 milliseconds
1. WHEN multiple errors exist, THE Language Server SHALL report all errors with accurate line and column positions

### Requirement 9: Auto-Completion for DSL Operations

**User Story:** As a user writing doctk scripts, I want auto-completion suggestions for operations and arguments, so that I can discover available functionality and write code faster.

#### Acceptance Criteria

1. WHEN a user types in a `.tk` file, THE Language Server SHALL provide completion suggestions for available operations
1. WHEN a user types after a pipe operator, THE Language Server SHALL suggest operations valid for the current document state
1. WHEN a user types within an operation, THE Language Server SHALL suggest valid arguments and parameters
1. WHEN a completion item is selected, THE Language Server SHALL insert the operation with placeholder arguments
1. WHEN completion is triggered, THE Language Server SHALL display suggestions within 200 milliseconds

### Requirement 10: Hover Documentation

**User Story:** As a developer learning the doctk DSL, I want to see documentation when I hover over operations, so that I can understand what each operation does without leaving the editor.

#### Acceptance Criteria

1. WHEN a user hovers over an operation name, THE Language Server SHALL display documentation describing the operation
1. WHEN a user hovers over an operation parameter, THE Language Server SHALL display documentation for that parameter
1. WHEN documentation is available, THE Language Server SHALL include usage examples
1. WHEN documentation is available, THE Language Server SHALL include parameter types and return types
1. WHEN hover is triggered, THE Language Server SHALL display documentation within 200 milliseconds

### Requirement 11: AI-Friendly Language Server

**User Story:** As an AI agent, I want to query the language server for available operations and their signatures, so that I can generate valid doctk code programmatically.

#### Acceptance Criteria

1. WHEN an AI agent requests completion at a position, THE Language Server SHALL return all valid operations with full signatures
1. WHEN an AI agent requests hover information, THE Language Server SHALL return structured documentation in a machine-readable format
1. WHEN an AI agent requests signature help, THE Language Server SHALL return parameter information with types and descriptions
1. WHEN an AI agent requests document symbols, THE Language Server SHALL return all operations and their locations
1. WHEN an AI agent requests diagnostics, THE Language Server SHALL return all validation errors with actionable messages

### Requirement 12: DSL Execution in Terminal REPL

**User Story:** As a user experimenting with document transformations, I want to run doctk commands interactively in a terminal, so that I can test operations quickly without writing script files.

#### Acceptance Criteria

1. WHEN a user starts the doctk REPL, THE System SHALL display a prompt accepting DSL commands
1. WHEN a user enters a valid DSL command, THE REPL SHALL execute the command and display the result
1. WHEN a user enters an invalid command, THE REPL SHALL display an error message with details
1. WHEN a document is loaded in the REPL, THE REPL SHALL maintain the document state across multiple commands
1. WHEN a user exits the REPL, THE System SHALL optionally save changes to the document

### Requirement 13: Script File Execution

**User Story:** As a documentation engineer, I want to write doctk transformation scripts in `.tk` files and execute them, so that I can automate repetitive document processing tasks.

#### Acceptance Criteria

1. WHEN a `.tk` file contains valid DSL code, THE System SHALL execute the script and apply transformations to the target document
1. WHEN a script file is executed, THE System SHALL report progress and completion status
1. WHEN a script encounters an error, THE System SHALL report the error with file location and line number
1. WHEN a script completes successfully, THE System SHALL save the transformed document
1. WHEN a script is executed from VS Code, THE Extension SHALL display output in the integrated terminal

### Requirement 14: Code Block Execution in Markdown

**User Story:** As a technical writer, I want to embed doctk scripts in Markdown code blocks and execute them, so that I can document transformations alongside their implementation.

#### Acceptance Criteria

1. WHEN a Markdown document contains a code block with language identifier `doctk`, THE Extension SHALL recognize it as executable
1. WHEN a user triggers execution on a doctk code block, THE Extension SHALL execute the DSL commands
1. WHEN execution completes, THE Extension SHALL update the document with the transformation results
1. WHEN execution fails, THE Extension SHALL display error messages in the output panel
1. WHEN multiple code blocks exist, THE Extension SHALL execute only the selected code block

### Requirement 15: Pluggable Interface Architecture

**User Story:** As a platform developer, I want the outliner and LSP to use a pluggable architecture, so that I can add support for JupyterLab and other interfaces in the future without rewriting core logic.

#### Acceptance Criteria

1. WHEN the outliner is implemented, THE System SHALL separate UI logic from document manipulation logic
1. WHEN the LSP server is implemented, THE System SHALL use a platform-agnostic communication protocol
1. WHEN a new interface is added, THE System SHALL reuse the core document manipulation API
1. WHEN a new interface is added, THE System SHALL reuse the LSP server without modification
1. WHEN the architecture is reviewed, THE System SHALL demonstrate clear separation between interface and core layers

### Requirement 16: Document Synchronization

**User Story:** As a user working with the outliner, I want changes made in the tree view to immediately reflect in the editor and vice versa, so that I have a consistent view of my document.

#### Acceptance Criteria

1. WHEN a change is made in the outliner, THE Extension SHALL update the editor content within 500 milliseconds
1. WHEN a change is made in the editor, THE Extension SHALL update the outliner tree view within 500 milliseconds
1. WHEN multiple changes occur rapidly, THE Extension SHALL batch updates to prevent performance degradation
1. WHEN synchronization fails, THE Extension SHALL display an error message and attempt recovery
1. WHEN the document is modified externally, THE Extension SHALL detect changes and update both views

### Requirement 17: Performance for Large Documents

**User Story:** As a user working with large technical documents, I want the outliner and LSP to remain responsive, so that I can work efficiently regardless of document size.

#### Acceptance Criteria

1. WHEN a document contains up to 1000 headings, THE Outliner SHALL render the tree view within 1 second
1. WHEN a document contains up to 1000 headings, THE Outliner SHALL respond to user interactions within 200 milliseconds
1. WHEN the Language Server processes a large document, THE Language Server SHALL provide completions within 500 milliseconds
1. WHEN structural operations are performed on large documents, THE System SHALL complete operations within 2 seconds
1. WHEN memory usage exceeds 500MB, THE System SHALL implement optimization strategies to reduce memory consumption

### Requirement 18: Error Recovery and Resilience

**User Story:** As a user, I want the outliner and LSP to handle errors gracefully, so that temporary issues don't disrupt my workflow.

#### Acceptance Criteria

1. WHEN the Language Server crashes, THE Extension SHALL automatically restart the server within 5 seconds
1. WHEN a document parsing error occurs, THE Outliner SHALL display a partial tree view with available structure
1. WHEN an operation fails, THE System SHALL display an error message and maintain document integrity
1. WHEN network or file system errors occur, THE System SHALL retry operations up to 3 times
1. WHEN unrecoverable errors occur, THE System SHALL log detailed diagnostic information for troubleshooting

### Requirement 19: Configuration and Customization

**User Story:** As a user, I want to configure the outliner appearance and behavior, so that I can adapt it to my workflow preferences.

#### Acceptance Criteria

1. WHEN configuration options are available, THE Extension SHALL provide settings for keyboard shortcuts
1. WHEN configuration options are available, THE Extension SHALL provide settings for tree view appearance
1. WHEN configuration options are available, THE Extension SHALL provide settings for auto-save behavior
1. WHEN settings are changed, THE Extension SHALL apply changes without requiring a restart
1. WHEN invalid settings are provided, THE Extension SHALL use default values and display a warning

### Requirement 20: Integration with doctk Core API

**User Story:** As a system architect, I want the outliner and LSP to use the existing doctk core API, so that all document operations are consistent and maintainable.

#### Acceptance Criteria

1. WHEN the Outliner performs a structural operation, THE Extension SHALL invoke the corresponding doctk API operation
1. WHEN the Language Server validates syntax, THE Language Server SHALL use doctk operation definitions
1. WHEN document transformations are applied, THE System SHALL use the doctk Document and Node abstractions
1. WHEN new operations are added to doctk core, THE System SHALL automatically support them in the LSP and outliner
1. WHEN the doctk API changes, THE System SHALL maintain backward compatibility or provide migration paths
