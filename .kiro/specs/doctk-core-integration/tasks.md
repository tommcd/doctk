# Implementation Plan: doctk Core Integration & Execution

This implementation plan breaks down the core integration layer and execution capabilities into discrete, actionable coding tasks. Each task builds incrementally on previous tasks, with all code integrated at each step.

## Task List

- [x] 1. Set up core integration project structure

  - Create directory structure for core integration (`src/doctk/integration/`)
  - Define Python protocols for document operations
  - Set up build configuration
  - _Requirements: 15, 20_

- [x] 2. Implement core document manipulation API

  - [x] 2.1 Create StructureOperations class with promote/demote operations

    - Implement `promote()` method that decreases heading level
    - Implement `demote()` method that increases heading level
    - Add validation to ensure heading levels stay within 1-6 range
    - _Requirements: 20_

  - [x] 2.2 Add move operations (move_up, move_down)

    - Implement `move_up()` to reorder sections among siblings
    - Implement `move_down()` to reorder sections among siblings
    - Handle edge cases (first/last sibling)
    - _Requirements: 20_

  - [x] 2.3 Implement nest and unnest operations

    - Implement `nest()` to move section under a new parent
    - Implement `unnest()` to move section up one level
    - Validate parent-child relationships
    - _Requirements: 20_

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

- [x] 4. Implement granular document edits (CRITICAL from PR #6 review)

  - [x] 4.1 Add ModifiedRange dataclass to protocols.py

    - Define ModifiedRange with start_line, start_column, end_line, end_column, new_text
    - Update OperationResult to include optional List[ModifiedRange]
    - Maintain backward compatibility with full document field
    - _PR #6 Issue #1 (Critical)_

  - [x] 4.2 Implement DiffComputer in operations.py

    - Create DiffComputer class to compute modified ranges
    - Implement `compute_ranges(original_doc, modified_doc, affected_node_ids)` method
    - Calculate line/column positions for changed nodes
    - Handle multi-node operations (move, nest)
    - Fixed bug where node IDs change after level modifications
    - _PR #6 Issue #1 (Critical)_

  - [x] 4.3 Update all operation methods to return modified ranges

    - Update promote() to compute and return modified ranges
    - Update demote() to compute and return modified ranges
    - Update move_up(), move_down() to return ranges for moved sections
    - Update nest(), unnest() to return ranges for level-adjusted nodes
    - _PR #6 Issue #1 (Critical)_

  - [x] 4.4 Write tests for granular edits

    - Test ModifiedRange computation for each operation type
    - Test multi-node operations
    - Verify line/column accuracy
    - Added 16 comprehensive tests for granular edit functionality
    - _PR #6 Issue #1 (Critical)_

- [x] 5. Centralize node ID generation in backend (MEDIUM from PR #6 review)

  - [x] 5.1 Add TreeNode dataclass and tree building method

    - Define TreeNode dataclass with id, label, level, line, column, children
    - Add `build_tree_with_ids()` method to DocumentTreeBuilder
    - Return hierarchical tree structure with all IDs assigned
    - _PR #6 Issue #5 (Medium)_

  - [x] 5.2 Add get_document_tree RPC method to bridge

    - Implement `get_document_tree()` in ExtensionBridge
    - Add tree serialization helper method
    - Return JSON-serializable tree structure
    - _PR #6 Issue #5 (Medium)_

  - [x] 5.3 Write tests for centralized ID generation

    - Test backend tree building with various document structures
    - Test IDs are consistent between operations
    - Test tree serialization
    - _PR #6 Issue #5 (Medium)_

- [x] 6. Implement REPL for interactive DSL execution

  - [x] 6.1 Create DoctkREPL class

    - Implement main REPL loop with prompt
    - Handle user input and command parsing
    - Maintain document state across commands
    - _Requirements: 12.1, 12.4_

  - [x] 6.2 Add REPL commands

    - Implement `load <file>` command to load documents
    - Implement `help` command to show available operations
    - Implement `exit` command to quit REPL
    - Execute operation commands (promote, demote, move_up, move_down, nest, unnest)
    - Added additional commands: `save`, `tree`, `list`
    - _Requirements: 12.2, 12.5_

  - [x] 6.3 Add error handling for REPL

    - Display syntax errors with helpful messages
    - Handle execution errors gracefully
    - Maintain REPL state after errors
    - _Requirements: 12.3_

  - [x] 6.4 Write tests for REPL

    - Test command execution (25 comprehensive tests)
    - Test state management
    - Test error handling
    - Test all operations (promote, demote, move_up, move_down, nest, unnest)
    - Achieved 83.26% code coverage
    - _Requirements: 12_

- [ ] 7. Implement script file execution

  - [ ] 7.1 Create ScriptExecutor class

    - Implement `execute_file()` method
    - Parse script file content
    - Execute operations on target document
    - _Requirements: 13.1_

  - [ ] 7.2 Add progress reporting

    - Report script execution progress
    - Display completion status
    - _Requirements: 13.2_

  - [ ] 7.3 Add error reporting for scripts

    - Report errors with file location and line number
    - Handle execution failures gracefully
    - _Requirements: 13.3_

  - [ ] 7.4 Add VS Code integration for script execution

    - Register command to execute .tk files
    - Display output in integrated terminal
    - _Requirements: 13.5_

  - [ ] 7.5 Write tests for script execution

    - Test successful script execution
    - Test error handling
    - Test progress reporting
    - _Requirements: 13_

- [ ] 8. Implement code block execution in Markdown

  - [ ] 8.1 Create CodeBlockExecutor class

    - Implement code block detection (\`\`\`doctk blocks)
    - Extract DSL code from code blocks
    - _Requirements: 14.1_

  - [ ] 8.2 Add execution command for code blocks

    - Register command to execute selected code block
    - Execute DSL code and apply to document
    - _Requirements: 14.2, 14.3_

  - [ ] 8.3 Add error handling for code block execution

    - Display errors in output panel
    - Handle execution failures gracefully
    - _Requirements: 14.4_

  - [ ] 8.4 Support multiple code blocks

    - Execute only the selected code block
    - Handle documents with multiple doctk blocks
    - _Requirements: 14.5_

  - [ ] 8.5 Write tests for code block execution

    - Test code block detection
    - Test execution and document update
    - Test error handling
    - _Requirements: 14_

- [ ] 9. Implement pluggable architecture interfaces

  - [ ] 9.1 Define DocumentInterface abstract class

    - Create abstract interface for document manipulation UIs
    - Define required methods (display_tree, get_user_selection, apply_operation, show_error)
    - _Requirements: 15.1, 15.5_

  - [ ] 9.2 Implement VSCodeInterface

    - Create VS Code-specific implementation of DocumentInterface
    - Integrate with existing VS Code extension code
    - _Requirements: 15.1, 15.3_

  - [ ] 9.3 Document pluggable architecture

    - Create architecture documentation
    - Provide examples for future interface implementations
    - _Requirements: 15.5_

  - [ ] 9.4 Write tests for interface abstraction

    - Test interface contract compliance
    - Test VS Code interface implementation
    - _Requirements: 15_

- [ ] 10. Implement performance optimizations for large documents

  - [ ] 10.1 Add incremental parsing

    - Parse only changed document sections
    - Reuse unchanged AST nodes
    - _Requirements: 17.3_

  - [ ] 10.2 Implement memory management

    - Add LRU cache for document states
    - Implement memory usage monitoring
    - Evict least recently used documents when memory limit reached
    - _Requirements: 17.5_

  - [ ] 10.3 Add performance monitoring

    - Implement PerformanceMonitor class
    - Record operation durations
    - Report slow operations
    - _Requirements: 17.4_

  - [ ] 10.4 Write performance tests

    - Test with documents containing 1000+ headings
    - Verify response times meet requirements
    - Test memory usage stays under 500MB
    - Verify operations complete within 2 seconds
    - _Requirements: 17_

- [ ] 11. Implement error recovery and resilience

  - [ ] 11.1 Create ErrorHandler class

    - Implement error classification (network, validation, system)
    - Add retry logic with exponential backoff
    - _Requirements: 18.4_

  - [ ] 11.2 Add comprehensive error logging

    - Log detailed diagnostic information
    - Include stack traces for debugging
    - _Requirements: 18.5_

  - [ ] 11.3 Write tests for error recovery

    - Test retry logic
    - Test error classification
    - _Requirements: 18_

- [ ] 12. Implement security features

  - [ ] 12.1 Add input validation

    - Implement InputValidator class
    - Validate operation parameters against schema
    - Use JSON Schema for validation
    - _Requirements: 20_

  - [ ] 12.2 Implement sandboxed execution

    - Create SandboxedExecutor class
    - Limit execution time
    - Validate operations before execution
    - _Requirements: 12, 13, 14_

  - [ ] 12.3 Write security tests

    - Test input validation
    - Test execution timeouts
    - Test operation whitelisting
    - _Requirements: 12, 13, 14_

- [ ] 13. Integration with doctk core API

  - [ ] 13.1 Ensure all operations use doctk core API

    - Verify all operations call doctk Document and Node abstractions
    - Ensure no direct document manipulation outside doctk API
    - _Requirements: 20.1, 20.3_

  - [ ] 13.2 Implement dynamic operation discovery

    - Add mechanism to discover new operations from doctk core
    - Ensure automatic support for new operations
    - _Requirements: 20.4_

  - [ ] 13.3 Add backward compatibility handling

    - Implement version checking
    - Provide migration paths for API changes
    - _Requirements: 20.5_

  - [ ] 13.4 Write integration tests

    - Test all operations with doctk core API
    - Test dynamic operation discovery
    - Test backward compatibility
    - _Requirements: 20_

- [ ] 14. End-to-end integration and testing

  - [ ] 14.1 Write end-to-end tests for script execution

    - Test REPL workflow
    - Test script file execution
    - Test code block execution in Markdown
    - _Requirements: 12, 13, 14_

  - [ ] 14.2 Write end-to-end tests for pluggable architecture

    - Test interface abstraction
    - Test VS Code interface implementation
    - _Requirements: 15_

  - [ ] 14.3 Perform performance benchmarking

    - Benchmark with large documents (1000+ headings)
    - Verify all response time requirements are met
    - Verify memory usage stays under limits
    - _Requirements: 17_

- [ ] 15. Final polish and documentation

  - [ ] 15.1 Code review and refactoring

    - Review all code for quality and consistency
    - Refactor complex sections
    - Add code comments where needed

  - [ ] 15.2 Complete developer documentation

    - Document architecture and design decisions
    - Add API documentation
    - Create contribution guidelines

  - [ ] 15.3 Create integration guides

    - Document how to add new interfaces
    - Provide examples for JupyterLab integration
    - Document extension points

## Notes

- Each task should be completed and verified before moving to the next
- All code should be integrated and functional at each step
- Performance requirements should be validated throughout development
- Tasks marked with [x] are already completed
- Integration with doctk core API should be verified at each step
