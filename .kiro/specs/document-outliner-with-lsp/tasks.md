# Implementation Plan: Document Outliner with LSP

This implementation plan breaks down the feature into discrete, actionable coding tasks. Each task builds incrementally on previous tasks, with all code integrated at each step.

## Task List

- [x] 1. Set up project structure and core interfaces

  - Create directory structure for VS Code extension (`extensions/doctk-outliner/`)
  - Create directory structure for language server (`src/doctk/lsp/`)
  - Define TypeScript interfaces for tree nodes and operations
  - Define Python protocols for document operations
  - Set up build configuration (tsconfig.json, package.json for extension)
  - _Requirements: 15, 20_

- [x] 2. Implement core document manipulation API

  - [x] 2.1 Create StructureOperations class with promote/demote operations

    - Implement `promote()` method that decreases heading level
    - Implement `demote()` method that increases heading level
    - Add validation to ensure heading levels stay within 1-6 range
    - _Requirements: 3.2, 3.3, 20_

  - [x] 2.2 Add move operations (move_up, move_down)

    - Implement `move_up()` to reorder sections among siblings
    - Implement `move_down()` to reorder sections among siblings
    - Handle edge cases (first/last sibling)
    - _Requirements: 3.4, 3.5, 20_

  - [x] 2.3 Implement nest and unnest operations

    - Implement `nest()` to move section under a new parent
    - Implement `unnest()` to move section up one level
    - Validate parent-child relationships
    - _Requirements: 2.2, 2.3, 20_

  - [x] 2.4 Write unit tests for structure operations

    - Test promote/demote with various heading levels
    - Test move operations with different sibling positions
    - Test nest/unnest with complex hierarchies
    - _Requirements: 20_

- [x] 3. Create ExtensionBridge for TypeScript-Python communication

  - [x] 3.1 Implement JSON-RPC bridge in Python

    - Create `ExtensionBridge` class that accepts JSON-RPC requests
    - Implement stdin/stdout communication protocol
    - Add request/response handling with proper error serialization
    - _Requirements: 20_

  - [x] 3.2 Implement TypeScript PythonBridge client

    - Create `PythonBridge` class that spawns Python process
    - Implement JSON-RPC request/response handling
    - Add promise-based API for async operations
    - Handle process lifecycle (start, stop, restart)
    - _Requirements: 18, 20_

  - [x] 3.3 Write integration tests for bridge communication

    - Test request/response round-trip
    - Test error handling and serialization
    - Test process restart on failure
    - _Requirements: 18_

- [x] 4. Implement tree data provider for VS Code

  - [x] 4.1 Create DocumentOutlineProvider class

    - Implement `TreeDataProvider<OutlineNode>` interface
    - Implement `getTreeItem()` to create tree items from nodes
    - Implement `getChildren()` to build tree hierarchy
    - Implement `getParent()` for navigation
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 4.2 Add document parsing to build tree structure

    - Parse Markdown document to extract headings
    - Build OutlineNode tree from heading hierarchy
    - Assign unique IDs to each node
    - Track node ranges (line/column positions)
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 4.3 Implement tree refresh and update mechanisms

    - Add `refresh()` method to trigger tree re-render
    - Implement `updateFromDocument()` to sync with editor changes
    - Add debouncing to prevent excessive updates
    - _Requirements: 1.4, 16.1, 16.2, 16.3_

  - [x] 4.4 Write unit tests for tree provider

    - Test tree building from various Markdown structures
    - Test node ID generation and uniqueness
    - Test refresh and update logic
    - _Requirements: 1_

- [ ] 5. Implement context menu operations

  - [ ] 5.1 Create OperationHandler class

    - Implement `executeOperation()` method
    - Add operation-to-API mapping (promote, demote, move_up, move_down, delete)
    - Create workspace edits from operation results
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [ ] 5.2 Register context menu commands

    - Register commands in package.json (promote, demote, move_up, move_down, delete)
    - Implement command handlers that call OperationHandler
    - Add command enablement conditions (when tree view is focused)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [ ] 5.3 Integrate with undo/redo system

    - Use WorkspaceEdit for all document modifications
    - Ensure operations are added to VS Code undo stack
    - Test undo/redo functionality
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 3.7_

  - [ ] 5.4 Write integration tests for operations

    - Test each operation end-to-end
    - Test undo/redo for all operations
    - Test error handling for invalid operations
    - _Requirements: 3, 6_

- [ ] 6. Implement drag-and-drop support

  - [ ] 6.1 Add TreeDragAndDropController to tree provider

    - Implement `handleDrag()` to capture dragged nodes
    - Implement `handleDrop()` to process drop operations
    - Determine drop type (nest vs. reorder) based on target
    - _Requirements: 2.1, 2.2, 2.3_

  - [ ] 6.2 Add visual feedback for drag operations

    - Implement drop target validation
    - Show visual indicators for valid/invalid drops
    - Highlight drop zones during drag
    - _Requirements: 2.1, 2.5_

  - [ ] 6.3 Execute operations on drop

    - Call appropriate operation (nest or move) based on drop type
    - Update document and tree view
    - Handle drop errors gracefully
    - _Requirements: 2.4, 2.5_

  - [ ] 6.4 Write tests for drag-and-drop

    - Test nest operation via drag-drop
    - Test reorder operation via drag-drop
    - Test invalid drop prevention
    - _Requirements: 2_

- [ ] 7. Implement inline editing in tree view

  - [ ] 7.1 Add inline editing support to tree items

    - Enable inline editing on double-click
    - Show text input field with current heading text
    - _Requirements: 4.1, 4.2_

  - [ ] 7.2 Handle edit completion and cancellation

    - Save changes on Enter or focus loss
    - Cancel editing on Escape
    - Update document with new heading text
    - _Requirements: 4.3, 4.4, 4.5_

  - [ ] 7.3 Write tests for inline editing

    - Test edit activation on double-click
    - Test save and cancel operations
    - Test document synchronization after edit
    - _Requirements: 4_

- [ ] 8. Add keyboard shortcuts

  - [ ] 8.1 Register keybindings in package.json

    - Define keybindings for promote, demote, move_up, move_down, delete
    - Set appropriate "when" clauses (tree view focused)
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [ ] 8.2 Make keybindings configurable

    - Add configuration schema for custom keybindings
    - Load user-defined keybindings from settings
    - _Requirements: 19.1_

  - [ ] 8.3 Write tests for keyboard shortcuts

    - Test each shortcut triggers correct operation
    - Test shortcuts only work when tree view is focused
    - _Requirements: 5_

- [ ] 9. Implement document synchronization

  - [ ] 9.1 Create DocumentSyncManager class

    - Implement `onDocumentChange()` to handle editor changes
    - Implement `onTreeViewChange()` to handle tree operations
    - Add debouncing for rapid changes
    - _Requirements: 16.1, 16.2, 16.3_

  - [ ] 9.2 Add bidirectional sync between editor and tree

    - Listen to document change events
    - Update tree view when document changes
    - Update document when tree view changes
    - Detect and handle external file modifications
    - _Requirements: 16.1, 16.2, 16.5_

  - [ ] 9.3 Handle synchronization errors

    - Detect sync failures
    - Display error messages
    - Attempt recovery
    - _Requirements: 16.4, 18.3_

  - [ ] 9.4 Write tests for synchronization

    - Test editor-to-tree sync
    - Test tree-to-editor sync
    - Test debouncing behavior
    - Test error recovery
    - _Requirements: 16_

- [ ] 10. Set up language server foundation

  - [ ] 10.1 Create DoctkLanguageServer class using pygls

    - Set up basic language server with pygls
    - Implement server initialization
    - Add document lifecycle handlers (didOpen, didChange, didClose)
    - _Requirements: 7.1, 7.3, 7.5_

  - [ ] 10.2 Implement DSL parser

    - Create `DSLParser` class to parse doctk DSL syntax
    - Build AST from DSL text
    - Handle parse errors gracefully
    - _Requirements: 8.1, 8.2_

  - [ ] 10.3 Add syntax validation

    - Implement `validate_syntax()` method
    - Check for unknown operations
    - Validate operation arguments
    - Generate diagnostic messages with line/column positions
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [ ] 10.4 Write tests for parser and validator

    - Test parsing valid DSL syntax
    - Test error handling for invalid syntax
    - Test diagnostic generation
    - _Requirements: 8_

- [ ] 11. Create operation registry for LSP

  - [ ] 11.1 Implement OperationRegistry class

    - Create data structures for operation metadata
    - Implement dynamic operation loading from doctk core
    - Store operation signatures, parameters, and documentation
    - _Requirements: 9.1, 10.1, 20.4_

  - [ ] 11.2 Add operation introspection

    - Introspect doctk module to discover operations
    - Extract parameter information and types
    - Load documentation strings
    - _Requirements: 20.4_

  - [ ] 11.3 Write tests for operation registry

    - Test operation discovery
    - Test metadata extraction
    - Test registry queries
    - _Requirements: 20_

- [ ] 12. Implement LSP completion provider

  - [ ] 12.1 Create CompletionProvider class

    - Implement context analysis to determine cursor position
    - Identify completion context (after pipe, in operation, etc.)
    - _Requirements: 9.2, 9.3_

  - [ ] 12.2 Add operation completions

    - Generate completion items for available operations
    - Include operation descriptions
    - Add snippet support for operation parameters
    - _Requirements: 9.1, 9.4_

  - [ ] 12.3 Add parameter completions

    - Provide completions for operation parameters
    - Include parameter types and descriptions
    - _Requirements: 9.3_

  - [ ] 12.4 Optimize completion performance

    - Add caching for completion results
    - Implement TTL-based cache invalidation
    - Ensure 200ms response time
    - _Requirements: 9.5_

  - [ ] 12.5 Write tests for completion provider

    - Test completions after pipe operator
    - Test parameter completions
    - Test completion performance
    - _Requirements: 9_

- [ ] 13. Implement hover documentation provider

  - [ ] 13.1 Create HoverProvider class

    - Implement hover position analysis
    - Identify operation or parameter under cursor
    - _Requirements: 10.1, 10.2_

  - [ ] 13.2 Generate hover documentation

    - Format operation documentation with descriptions
    - Include parameter information
    - Add usage examples
    - Include type information
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

  - [ ] 13.3 Optimize hover performance

    - Ensure 200ms response time
    - Cache documentation where appropriate
    - _Requirements: 10.5_

  - [ ] 13.4 Write tests for hover provider

    - Test hover on operations
    - Test hover on parameters
    - Test documentation formatting
    - _Requirements: 10_

- [ ] 14. Add AI agent support to language server

  - [ ] 14.1 Implement structured information endpoints

    - Create `get_operation_catalog()` method
    - Return complete operation metadata in JSON format
    - Include all parameters, types, and examples
    - _Requirements: 11.1, 11.2_

  - [ ] 14.2 Add signature help support

    - Implement LSP signature help feature
    - Provide parameter information during typing
    - _Requirements: 11.3_

  - [ ] 14.3 Add document symbols support

    - Implement LSP document symbols feature
    - Return all operations and their locations
    - _Requirements: 11.4_

  - [ ] 14.4 Enhance diagnostics for AI consumption

    - Ensure diagnostic messages are actionable
    - Include fix suggestions where possible
    - _Requirements: 11.5_

  - [ ] 14.5 Write tests for AI agent features

    - Test operation catalog generation
    - Test signature help
    - Test document symbols
    - _Requirements: 11_

- [ ] 15. Connect language server to VS Code extension

  - [ ] 15.1 Create DoctkLanguageClient class

    - Set up LanguageClient with server options
    - Configure document selectors for .tk files and doctk language
    - Set up file watchers
    - _Requirements: 7.1, 7.2_

  - [ ] 15.2 Implement server lifecycle management

    - Start language server on extension activation
    - Stop server on deactivation
    - Handle server crashes with automatic restart
    - _Requirements: 7.3, 18.1_

  - [ ] 15.3 Configure server command to use uv

    - Set server command to `uv run python`
    - Pass correct working directory
    - Set up environment variables if needed
    - _Requirements: 7.1_

  - [ ] 15.4 Write integration tests for LSP connection

    - Test server startup and connection
    - Test server restart on crash
    - Test LSP feature activation
    - _Requirements: 7, 18_

- [ ] 16. Implement REPL for interactive DSL execution

  - [ ] 16.1 Create DoctkREPL class

    - Implement main REPL loop with prompt
    - Handle user input and command parsing
    - Maintain document state across commands
    - _Requirements: 12.1, 12.4_

  - [ ] 16.2 Add REPL commands

    - Implement `load <file>` command to load documents
    - Implement `help` command to show available operations
    - Implement `exit` command to quit REPL
    - Execute DSL commands and display results
    - _Requirements: 12.2, 12.5_

  - [ ] 16.3 Add error handling for REPL

    - Display syntax errors with helpful messages
    - Handle execution errors gracefully
    - Maintain REPL state after errors
    - _Requirements: 12.3_

  - [ ] 16.4 Write tests for REPL

    - Test command execution
    - Test state management
    - Test error handling
    - _Requirements: 12_

- [ ] 17. Implement script file execution

  - [ ] 17.1 Create ScriptExecutor class

    - Implement `execute_file()` method
    - Parse script file content
    - Execute operations on target document
    - _Requirements: 13.1_

  - [ ] 17.2 Add progress reporting

    - Report script execution progress
    - Display completion status
    - _Requirements: 13.2_

  - [ ] 17.3 Add error reporting for scripts

    - Report errors with file location and line number
    - Handle execution failures gracefully
    - _Requirements: 13.3_

  - [ ] 17.4 Add VS Code integration for script execution

    - Register command to execute .tk files
    - Display output in integrated terminal
    - _Requirements: 13.5_

  - [ ] 17.5 Write tests for script execution

    - Test successful script execution
    - Test error handling
    - Test progress reporting
    - _Requirements: 13_

- [ ] 18. Implement code block execution in Markdown

  - [ ] 18.1 Create CodeBlockExecutor class

    - Implement code block detection (\`\`\`doctk blocks)
    - Extract DSL code from code blocks
    - _Requirements: 14.1_

  - [ ] 18.2 Add execution command for code blocks

    - Register command to execute selected code block
    - Execute DSL code and apply to document
    - _Requirements: 14.2, 14.3_

  - [ ] 18.3 Add error handling for code block execution

    - Display errors in output panel
    - Handle execution failures gracefully
    - _Requirements: 14.4_

  - [ ] 18.4 Support multiple code blocks

    - Execute only the selected code block
    - Handle documents with multiple doctk blocks
    - _Requirements: 14.5_

  - [ ] 18.5 Write tests for code block execution

    - Test code block detection
    - Test execution and document update
    - Test error handling
    - _Requirements: 14_

- [ ] 19. Implement performance optimizations for large documents

  - [ ] 19.1 Add virtual scrolling to tree view

    - Implement VirtualTreeRenderer class
    - Render only visible nodes
    - Update visible range on scroll
    - _Requirements: 17.1, 17.2_

  - [ ] 19.2 Implement lazy loading for tree nodes

    - Load child nodes only on expansion
    - Cache loaded nodes
    - _Requirements: 17.1, 17.2_

  - [ ] 19.3 Add incremental parsing

    - Parse only changed document sections
    - Reuse unchanged AST nodes
    - _Requirements: 17.3_

  - [ ] 19.4 Implement memory management

    - Add LRU cache for document states
    - Implement memory usage monitoring
    - Evict least recently used documents when memory limit reached
    - _Requirements: 17.5_

  - [ ] 19.5 Write performance tests

    - Test with documents containing 1000+ headings
    - Verify response times meet requirements
    - Test memory usage stays under 500MB
    - _Requirements: 17_

- [ ] 20. Implement error recovery and resilience

  - [ ] 20.1 Create ErrorHandler class

    - Implement error classification (network, validation, system)
    - Add retry logic with exponential backoff
    - _Requirements: 18.4_

  - [ ] 20.2 Add graceful degradation for parsing errors

    - Display partial tree view when parsing fails
    - Show available structure even with errors
    - _Requirements: 18.2_

  - [ ] 20.3 Implement automatic server restart

    - Detect language server crashes
    - Restart server within 5 seconds
    - Restore server state after restart
    - _Requirements: 18.1_

  - [ ] 20.4 Add comprehensive error logging

    - Log detailed diagnostic information
    - Include stack traces for debugging
    - _Requirements: 18.5_

  - [ ] 20.5 Write tests for error recovery

    - Test retry logic
    - Test graceful degradation
    - Test server restart
    - _Requirements: 18_

- [ ] 21. Add configuration and customization

  - [ ] 21.1 Define configuration schema

    - Add settings for keyboard shortcuts
    - Add settings for tree view appearance
    - Add settings for auto-save behavior
    - Add settings for performance thresholds
    - _Requirements: 19.1, 19.2, 19.3_

  - [ ] 21.2 Implement configuration loading

    - Load settings from VS Code configuration
    - Apply settings without restart
    - _Requirements: 19.4_

  - [ ] 21.3 Add configuration validation

    - Validate settings on change
    - Use defaults for invalid settings
    - Display warnings for invalid values
    - _Requirements: 19.5_

  - [ ] 21.4 Write tests for configuration

    - Test settings loading
    - Test settings validation
    - Test dynamic settings updates
    - _Requirements: 19_

- [ ] 22. Create extension packaging and distribution

  - [ ] 22.1 Configure package.json for VS Code extension

    - Set extension metadata (name, version, description)
    - Define activation events
    - Configure views, commands, and keybindings
    - Add language definition for doctk
    - _Requirements: 7.1, 7.2_

  - [ ] 22.2 Set up build process

    - Configure TypeScript compilation
    - Bundle extension with webpack or esbuild
    - Include Python language server in package
    - _Requirements: 7.1_

  - [ ] 22.3 Create extension documentation

    - Write README with feature overview
    - Add usage examples
    - Document configuration options
    - _Requirements: 19_

  - [ ] 22.4 Package extension as .vsix

    - Use vsce to package extension
    - Test installation from .vsix file
    - _Requirements: 7.1_

- [ ] 22.5. Implement granular document edits (CRITICAL from PR #6 review)

  - [ ] 22.5.1 Add ModifiedRange dataclass to protocols.py

    - Define ModifiedRange with start_line, start_column, end_line, end_column, new_text
    - Update OperationResult to include optional List[ModifiedRange]
    - Maintain backward compatibility with full document field
    - _PR #6 Issue #1 (Critical)_

  - [ ] 22.5.2 Implement DiffComputer in operations.py

    - Create DiffComputer class to compute modified ranges
    - Implement `compute_ranges(original_doc, modified_doc, affected_node_ids)` method
    - Calculate line/column positions for changed nodes
    - Handle multi-node operations (move, nest)
    - _PR #6 Issue #1 (Critical)_

  - [ ] 22.5.3 Update all operation methods to return modified ranges

    - Update promote() to compute and return modified ranges
    - Update demote() to compute and return modified ranges
    - Update move_up(), move_down() to return ranges for moved sections
    - Update nest(), unnest() to return ranges for level-adjusted nodes
    - _PR #6 Issue #1 (Critical)_

  - [ ] 22.5.4 Update TypeScript extension to use granular edits

    - Modify executeOperation() in extension.ts to check for modifiedRanges
    - Create WorkspaceEdit with granular ranges when available
    - Keep fallback to full document replacement
    - Test cursor position preservation
    - Test undo/redo stack preservation
    - _PR #6 Issue #1 (Critical)_

  - [ ] 22.5.5 Write tests for granular edits

    - Test ModifiedRange computation for each operation type
    - Test frontend applies granular edits correctly
    - Test cursor position is preserved after operations
    - Test undo/redo works with granular edits
    - _PR #6 Issue #1 (Critical)_

- [ ] 22.6. Centralize node ID generation in backend (MEDIUM from PR #6 review)

  - [ ] 22.6.1 Add TreeNode dataclass and tree building method

    - Define TreeNode dataclass with id, label, level, line, column, children
    - Add `build_tree_with_ids()` method to DocumentTreeBuilder
    - Return hierarchical tree structure with all IDs assigned
    - _PR #6 Issue #5 (Medium)_

  - [ ] 22.6.2 Add get_document_tree RPC method to bridge

    - Implement `get_document_tree()` in ExtensionBridge
    - Add tree serialization helper method
    - Return JSON-serializable tree structure
    - _PR #6 Issue #5 (Medium)_

  - [ ] 22.6.3 Update frontend to request tree from backend

    - Add `getDocumentTree()` method to PythonBridge TypeScript class
    - Update `updateFromDocument()` in DocumentOutlineProvider to use backend tree
    - Remove local ID generation logic from outlineProvider.ts
    - Add tree deserialization method
    - _PR #6 Issue #5 (Medium)_

  - [ ] 22.6.4 Write tests for centralized ID generation

    - Test backend tree building with various document structures
    - Test frontend correctly deserializes backend tree
    - Test IDs are consistent between operations
    - Verify no duplicate ID generation logic remains
    - _PR #6 Issue #5 (Medium)_

- [ ] 23. End-to-end integration and testing

  - [ ] 23.1 Write end-to-end tests for outliner workflows

    - Test complete workflow: open document → view outliner → drag-drop → verify changes
    - Test operation execution from context menu
    - Test keyboard shortcuts
    - Test undo/redo
    - _Requirements: 1, 2, 3, 5, 6_

  - [ ] 23.2 Write end-to-end tests for LSP workflows

    - Test complete workflow: open .tk file → type code → get completions → execute
    - Test hover documentation
    - Test syntax validation
    - _Requirements: 7, 8, 9, 10_

  - [ ] 23.3 Write end-to-end tests for script execution

    - Test REPL workflow
    - Test script file execution
    - Test code block execution in Markdown
    - _Requirements: 12, 13, 14_

  - [ ] 23.4 Perform performance benchmarking

    - Benchmark with large documents (1000+ headings)
    - Verify all response time requirements are met
    - Verify memory usage stays under limits
    - _Requirements: 17_

- [ ] 24. Final polish and documentation

  - [ ] 24.1 Code review and refactoring

    - Review all code for quality and consistency
    - Refactor complex sections
    - Add code comments where needed

  - [ ] 24.2 Complete user documentation

    - Write comprehensive user guide
    - Add troubleshooting section
    - Create video tutorials or GIFs

  - [ ] 24.3 Complete developer documentation

    - Document architecture and design decisions
    - Add API documentation
    - Create contribution guidelines

## Notes

- Each task should be completed and verified before moving to the next
- All code should be integrated and functional at each step
- Performance requirements should be validated throughout development
