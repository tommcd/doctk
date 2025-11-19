# Implementation Plan: doctk Language Server

This implementation plan breaks down the language server into discrete, actionable coding tasks. Each task builds incrementally on previous tasks, with all code integrated at each step.

## Task List

- [x] 1. Set up language server foundation

  - [x] 1.1 Create DoctkLanguageServer class using pygls

    - Set up basic language server with pygls
    - Implement server initialization
    - Add document lifecycle handlers (didOpen, didChange, didClose)
    - _Requirements: 7.1, 7.3, 7.5_
    - _Implemented in: src/doctk/lsp/server.py_

  - [x] 1.2 Implement DSL parser

    - Create `DSLParser` class to parse doctk DSL syntax
    - Build AST from DSL text
    - Handle parse errors gracefully
    - _Requirements: 8.1, 8.2_
    - _Implemented in: src/doctk/dsl/parser.py_

  - [x] 1.3 Add syntax validation

    - Implement `validate_syntax()` method
    - Check for unknown operations (stub for future work)
    - Validate operation arguments
    - Generate diagnostic messages with line/column positions
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_
    - _Implemented in: src/doctk/lsp/server.py:validate_syntax()_

  - [x] 1.4 Write tests for parser and validator

    - Test parsing valid DSL syntax
    - Test error handling for invalid syntax
    - Test diagnostic generation
    - _Requirements: 8_
    - _Tests in: tests/unit/test_dsl_parser.py, tests/unit/test_language_server.py_

- [x] 2. Create operation registry for LSP

  - [x] 2.1 Implement OperationRegistry class

    - Create data structures for operation metadata
    - Implement dynamic operation loading from doctk core
    - Store operation signatures, parameters, and documentation
    - _Requirements: 9.1, 10.1, 20.4_
    - _Implemented in: src/doctk/lsp/registry.py_

  - [x] 2.2 Add operation introspection

    - Introspect doctk module to discover operations
    - Extract parameter information and types
    - Load documentation strings
    - _Requirements: 20.4_
    - _Implemented in: src/doctk/lsp/registry.py:_load_operations_from_doctk()_

  - [x] 2.3 Write tests for operation registry

    - Test operation discovery
    - Test metadata extraction
    - Test registry queries
    - _Requirements: 20_
    - _Tests in: tests/unit/test_operation_registry.py (22 tests, all passing)_

- [x] 3. Implement LSP completion provider

  - [x] 3.1 Create CompletionProvider class

    - Implement context analysis to determine cursor position
    - Identify completion context (after pipe, in operation, etc.)
    - _Requirements: 9.2, 9.3_
    - _Implemented in: src/doctk/lsp/completion.py_

  - [x] 3.2 Add operation completions

    - Generate completion items for available operations
    - Include operation descriptions
    - Add snippet support for operation parameters
    - _Requirements: 9.1, 9.4_
    - _Implemented in: src/doctk/lsp/completion.py:_operation_completions()_

  - [x] 3.3 Add parameter completions

    - Provide completions for operation parameters
    - Include parameter types and descriptions
    - _Requirements: 9.3_
    - _Implemented in: src/doctk/lsp/completion.py:_parameter_completions()_

  - [x] 3.4 Optimize completion performance

    - Add caching for completion results
    - Implement TTL-based cache invalidation
    - Ensure 200ms response time
    - _Requirements: 9.5_
    - _Implemented in: src/doctk/lsp/completion.py (CachedCompletion dataclass and caching methods)_

  - [x] 3.5 Write tests for completion provider

    - Test completions after pipe operator
    - Test parameter completions
    - Test completion performance
    - _Requirements: 9_
    - _Tests in: tests/unit/test_completion_provider.py (28 tests, all passing)_

- [x] 4. Implement hover documentation provider

  - [x] 4.1 Create HoverProvider class

    - Implement hover position analysis
    - Identify operation or parameter under cursor
    - _Requirements: 10.1, 10.2_
    - _Implemented in: src/doctk/lsp/hover.py (HoverProvider class, 437 lines)_

  - [x] 4.2 Generate hover documentation

    - Format operation documentation with descriptions
    - Include parameter information
    - Add usage examples
    - Include type information
    - _Requirements: 10.1, 10.2, 10.3, 10.4_
    - _Implemented in: src/doctk/lsp/hover.py (_format_operation_documentation, _format_parameter_documentation)_

  - [x] 4.3 Optimize hover performance

    - Ensure 200ms response time
    - Cache documentation where appropriate
    - _Requirements: 10.5_
    - _Implemented in: src/doctk/lsp/hover.py (LRU cache with 5s TTL)_

  - [x] 4.4 Write tests for hover provider

    - Test hover on operations
    - Test hover on parameters
    - Test documentation formatting
    - _Requirements: 10_
    - _Tests in: tests/unit/test_hover_provider.py (29 tests, all passing, 92.48% coverage)_

- [ ] 5. Add AI agent support to language server

  - [ ] 5.1 Implement structured information endpoints

    - Create `get_operation_catalog()` method
    - Return complete operation metadata in JSON format
    - Include all parameters, types, and examples
    - _Requirements: 11.1, 11.2_

  - [ ] 5.2 Add signature help support

    - Implement LSP signature help feature
    - Provide parameter information during typing
    - _Requirements: 11.3_

  - [ ] 5.3 Add document symbols support

    - Implement LSP document symbols feature
    - Return all operations and their locations
    - _Requirements: 11.4_

  - [ ] 5.4 Enhance diagnostics for AI consumption

    - Ensure diagnostic messages are actionable
    - Include fix suggestions where possible
    - _Requirements: 11.5_

  - [ ] 5.5 Write tests for AI agent features

    - Test operation catalog generation
    - Test signature help
    - Test document symbols
    - _Requirements: 11_

- [ ] 6. Connect language server to VS Code extension

  - [ ] 6.1 Create DoctkLanguageClient class

    - Set up LanguageClient with server options
    - Configure document selectors for .tk files and doctk language
    - Set up file watchers
    - _Requirements: 7.1, 7.2_

  - [ ] 6.2 Implement server lifecycle management

    - Start language server on extension activation
    - Stop server on deactivation
    - Handle server crashes with automatic restart
    - _Requirements: 7.3, 18.1_

  - [ ] 6.3 Configure server command to use uv

    - Set server command to `uv run python`
    - Pass correct working directory
    - Set up environment variables if needed
    - _Requirements: 7.1_

  - [ ] 6.4 Write integration tests for LSP connection

    - Test server startup and connection
    - Test server restart on crash
    - Test LSP feature activation
    - _Requirements: 7, 18_

- [ ] 7. Implement error recovery and resilience

  - [ ] 7.1 Add graceful degradation for parsing errors

    - Display partial diagnostics when parsing fails
    - Show available information even with errors
    - _Requirements: 18.2_

  - [ ] 7.2 Implement automatic server restart

    - Detect language server crashes
    - Restart server within 5 seconds
    - Restore server state after restart
    - _Requirements: 18.1_

  - [ ] 7.3 Add comprehensive error logging

    - Log detailed diagnostic information
    - Include stack traces for debugging
    - _Requirements: 18.5_

  - [ ] 7.4 Write tests for error recovery

    - Test graceful degradation
    - Test server restart
    - _Requirements: 18_

- [ ] 8. Implement memory management

  - [ ] 8.1 Add LRU cache for document states

    - Implement DocumentStateManager with LRU cache
    - Add memory usage monitoring
    - Evict least recently used documents when memory limit reached
    - _Requirements: 17.5_

  - [ ] 8.2 Write performance tests

    - Test memory usage stays under 500MB
    - Test with large documents
    - _Requirements: 17_

- [ ] 9. Add configuration and customization

  - [ ] 9.1 Define configuration schema

    - Add settings for LSP trace level
    - Add settings for maximum completion items
    - Add settings to enable/disable the language server
    - _Requirements: 19.1, 19.2, 19.3_

  - [ ] 9.2 Implement configuration loading

    - Load settings from VS Code configuration
    - Apply settings without restart
    - _Requirements: 19.4_

  - [ ] 9.3 Add configuration validation

    - Validate settings on change
    - Use defaults for invalid settings
    - Display warnings for invalid values
    - _Requirements: 19.5_

  - [ ] 9.4 Write tests for configuration

    - Test settings loading
    - Test settings validation
    - Test dynamic settings updates
    - _Requirements: 19_

- [ ] 10. Python dependencies and packaging

  - [ ] 10.1 Set up uv dependency management

    - Create pyproject.toml with dependencies
    - Configure pygls and doctk dependencies
    - Add dev dependencies for testing
    - _Requirements: 7.1_

  - [ ] 10.2 Create language server entry point

    - Create main script for language server
    - Handle command-line arguments
    - Set up logging
    - _Requirements: 7.1_

- [ ] 11. End-to-end integration and testing

  - [ ] 11.1 Write end-to-end tests for LSP workflows

    - Test complete workflow: open .tk file → type code → get completions → execute
    - Test hover documentation
    - Test syntax validation
    - _Requirements: 7, 8, 9, 10_

  - [ ] 11.2 Perform performance benchmarking

    - Verify completion response times < 200ms
    - Verify hover response times < 200ms
    - Test with large documents
    - _Requirements: 9.5, 10.5, 17_

- [ ] 12. Final polish and documentation

  - [ ] 12.1 Code review and refactoring

    - Review all code for quality and consistency
    - Refactor complex sections
    - Add code comments where needed

  - [ ] 12.2 Complete developer documentation

    - Document LSP architecture
    - Add API documentation
    - Create contribution guidelines

## Notes

- Each task should be completed and verified before moving to the next
- All code should be integrated and functional at each step
- Performance requirements should be validated throughout development
- LSP standard compliance should be verified at each step
