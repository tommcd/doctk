# Implementation Plan: Document Outliner with LSP - Phase 1

This implementation plan breaks down Phase 1 (Core DSL and Execution Engine) into discrete, manageable tasks. Phase 1 focuses on the Python foundation: DSL parser, structure operations, executor, REPL, and script execution.

## Status Summary

**Phase**: Phase 1 - Core DSL and Execution Engine
**Status**: In Progress - Foundation Complete
**Target**: Implement foundational DSL capabilities in Python

**Completed**:
- ✅ Structure operations (lift, lower, nest, unnest) fully implemented
- ✅ Comprehensive tests for structure operations (15 tests, all passing)
- ✅ DSL package structure created
- ✅ DSL lexer fully implemented with 90.81% code coverage
- ✅ DSL lexer comprehensive tests (13 tests, all passing)
- ✅ Stub files for parser, executor, REPL (ready for future implementation)

**Test Results**:
- 53 tests passing (2 skipped - external tools not installed)
- Code coverage: 32.97% (increased from 20.43%)
- All quality checks passing

The outliner and LSP server (VS Code extension) are deferred to future phases.

## Phase 1 Tasks

### Task 1: Add Structure Operations to Core

- [x] 1. Add structure operations (lift, lower, nest, unnest) to operations.py
  - [x] Implement `lift()` operation - move section up in hierarchy
  - [x] Implement `lower()` operation - move section down in hierarchy
  - [x] Implement `nest()` operation - nest section under target
  - [x] Implement `unnest()` operation - remove one level of nesting
  - [x] Add type hints and docstrings for all operations
  - [x] Export new operations from `__init__.py`
  - [x] _Requirements: 3 (Context Menu Operations), 20 (Integration with doctk Core API)_

### Task 2: Write Tests for Structure Operations

- [x] 2. Write comprehensive tests for structure operations
  - [x] Create `tests/unit/test_structure_operations.py`
  - [x] Test `lift()` with various heading levels
  - [x] Test `lower()` with various heading levels
  - [x] Test `nest()` with different targets
  - [x] Test `unnest()` with nested structures
  - [x] Test edge cases (lift h1, lower h6, etc.)
  - [x] Verify immutability (operations return new documents)
  - [x] _Requirements: 3, 20_

### Task 3: Create DSL Package Structure

- [x] 3. Create src/doctk/dsl/ package for DSL components
  - [x] Create `src/doctk/dsl/` directory
  - [x] Create `src/doctk/dsl/__init__.py`
  - [x] Create `src/doctk/dsl/lexer.py` (fully implemented)
  - [x] Create `src/doctk/dsl/parser.py` (stub with data structures)
  - [x] Create `src/doctk/dsl/executor.py` (stub)
  - [x] Create `src/doctk/dsl/repl.py` (stub)
  - [x] _Requirements: 7 (Language Server for DSL)_

### Task 4: Implement DSL Lexer

- [x] 4. Implement lexer to tokenize DSL syntax
  - [x] Define `TokenType` enum with all token types
  - [x] Define `Token` dataclass
  - [x] Implement `Lexer` class with `next_token()` method
  - [x] Implement `tokenize()` method to tokenize entire source
  - [x] Handle identifiers, strings, numbers, operators
  - [x] Handle keywords (let, doc, where, select)
  - [x] Track line and column positions for error reporting
  - [x] Skip whitespace and comments
  - [x] _Requirements: 7, 8 (Real-Time Syntax Validation)_

### Task 5: Write Tests for DSL Lexer

- [x] 5. Write comprehensive tests for lexer
  - [x] Create `tests/unit/dsl/` directory
  - [x] Create `tests/unit/dsl/__init__.py`
  - [x] Create `tests/unit/dsl/test_lexer.py`
  - [x] Test tokenizing identifiers
  - [x] Test tokenizing strings (single and double quoted)
  - [x] Test tokenizing numbers (int and float)
  - [x] Test tokenizing operators (|, =, ~)
  - [x] Test tokenizing keywords
  - [x] Test line and column tracking
  - [x] Test error handling for invalid characters
  - [x] _Requirements: 7, 8_

### Task 6: Implement DSL Parser

- [ ] 6. Implement parser to build AST from tokens
  - [ ] Define AST node base class `ASTNode`
  - [ ] Define `Pipeline`, `Source`, `FunctionCall`, `Assignment` node types
  - [ ] Implement `Parser` class with recursive descent parsing
  - [ ] Implement `parse()` method to parse token stream
  - [ ] Implement `parse_statement()` for top-level statements
  - [ ] Implement `parse_pipeline()` for pipeline expressions
  - [ ] Implement `parse_operation()` for operations
  - [ ] Implement `parse_arguments()` for operation arguments
  - [ ] Handle syntax errors with helpful messages
  - [ ] _Requirements: 7, 8_

### Task 7: Write Tests for DSL Parser

- [ ] 7. Write comprehensive tests for parser
  - [ ] Create `tests/unit/dsl/test_parser.py`
  - [ ] Test parsing simple pipelines (doc | select heading)
  - [ ] Test parsing pipelines with arguments (where level=3)
  - [ ] Test parsing variable assignments (let x = ...)
  - [ ] Test parsing complex expressions
  - [ ] Test error handling for syntax errors
  - [ ] Test error messages include line/column information
  - [ ] Verify AST structure is correct
  - [ ] _Requirements: 7, 8_

### Task 8: Implement DSL Executor

- [ ] 8. Implement executor to run DSL commands on documents
  - [ ] Define `Executor` class with document and variables
  - [ ] Implement `execute()` method to execute AST
  - [ ] Implement `execute_pipeline()` to execute pipelines
  - [ ] Implement `execute_assignment()` to handle variable assignments
  - [ ] Implement `get_operation()` to map operation names to functions
  - [ ] Support all core operations (select, where, promote, demote)
  - [ ] Support new structure operations (lift, lower, nest, unnest)
  - [ ] Handle runtime errors gracefully
  - [ ] _Requirements: 7, 12 (DSL Execution in Terminal REPL), 13 (Script File Execution)_

### Task 9: Write Tests for DSL Executor

- [ ] 9. Write comprehensive tests for executor
  - [ ] Create `tests/unit/dsl/test_executor.py`
  - [ ] Test executing simple operations
  - [ ] Test executing pipelines with multiple operations
  - [ ] Test variable assignments
  - [ ] Test operation composition
  - [ ] Test error handling for unknown operations
  - [ ] Test error handling for invalid arguments
  - [ ] Verify document transformations are correct
  - [ ] _Requirements: 7, 12, 13_

### Task 10: Implement REPL

- [ ] 10. Implement interactive REPL for DSL
  - [ ] Implement `REPL` class with start() method
  - [ ] Implement command loop with prompt
  - [ ] Handle special commands (load, save, help, exit)
  - [ ] Integrate lexer, parser, executor
  - [ ] Display results after each command
  - [ ] Handle errors gracefully with helpful messages
  - [ ] Support command history
  - [ ] Use rich console for formatted output
  - [ ] _Requirements: 12 (DSL Execution in Terminal REPL)_

### Task 11: Write Tests for REPL

- [ ] 11. Write E2E tests for REPL functionality
  - [ ] Create `tests/e2e/test_repl.py`
  - [ ] Test REPL initialization
  - [ ] Test load command
  - [ ] Test save command
  - [ ] Test executing DSL commands
  - [ ] Test error handling
  - [ ] Test help command
  - [ ] Mock user input for testing
  - [ ] _Requirements: 12_

### Task 12: Add CLI Commands

- [ ] 12. Add repl and run commands to CLI
  - [ ] Add `repl` command to cli.py
  - [ ] Add `run` command to cli.py to execute .tk files
  - [ ] Add `--output` option to run command
  - [ ] Add help text and examples
  - [ ] Handle file not found errors
  - [ ] Handle parsing errors
  - [ ] Handle execution errors
  - [ ] Display success/error messages with rich console
  - [ ] _Requirements: 12, 13 (Script File Execution)_

### Task 13: Write Tests for CLI Commands

- [ ] 13. Write E2E tests for CLI commands
  - [ ] Create `tests/e2e/test_cli_dsl.py`
  - [ ] Test `doctk repl` command (if testable non-interactively)
  - [ ] Test `doctk run script.tk input.md` command
  - [ ] Test `doctk run` with --output option
  - [ ] Test error handling for missing files
  - [ ] Test error handling for syntax errors in scripts
  - [ ] Verify output documents are correct
  - [ ] _Requirements: 12, 13_

### Task 14: Create Example Scripts

- [ ] 14. Create example .tk scripts demonstrating DSL
  - [ ] Create `examples/transformations/` directory
  - [ ] Create `examples/transformations/promote-h3.tk` - promote all h3 headings
  - [ ] Create `examples/transformations/nest-sections.tk` - nest sections
  - [ ] Create `examples/transformations/reorder-toc.tk` - reorder table of contents
  - [ ] Create `examples/transformations/README.md` with usage instructions
  - [ ] Test all example scripts on sample.md
  - [ ] _Requirements: 13_

### Task 15: Write DSL Documentation

- [ ] 15. Create comprehensive DSL documentation
  - [ ] Create `docs/user-guide/dsl-reference.md`
  - [ ] Document DSL grammar and syntax
  - [ ] Document all operations with examples
  - [ ] Document REPL commands
  - [ ] Document script file format
  - [ ] Add examples and use cases
  - [ ] Add troubleshooting section
  - [ ] Update mkdocs.yml navigation
  - [ ] _Requirements: 10 (Hover Documentation), 13_

### Task 16: Update README and CLAUDE.md

- [ ] 16. Update project documentation
  - [ ] Update README.md with DSL capabilities
  - [ ] Add REPL usage example to README
  - [ ] Add script execution example to README
  - [ ] Update CLAUDE.md with DSL architecture
  - [ ] Update CLAUDE.md common tasks
  - [ ] Document new directory structure (src/doctk/dsl/)
  - [ ] _Requirements: 7, 12, 13_

### Task 17: Run Quality Checks

- [ ] 17. Ensure all quality checks pass
  - [ ] Run `uv run pytest -m "slow or not slow"` - all tests pass
  - [ ] Run `tox -e ruff` - Python linting passes
  - [ ] Run `tox -e mypy` - Type checking passes (if mypy configured)
  - [ ] Run `tox -e docs-build` - Documentation builds successfully
  - [ ] Verify code coverage is >40% (increased from 20%)
  - [ ] Fix any warnings or errors
  - [ ] _Requirements: All_

## Success Criteria

Phase 1 is complete when:

1. ✅ All structure operations (lift, lower, nest, unnest) are implemented and tested
1. ✅ DSL lexer can tokenize all supported syntax
1. ✅ DSL parser can parse pipelines, assignments, and operations
1. ✅ DSL executor can execute operations on documents
1. ✅ REPL provides interactive command-line interface
1. ✅ CLI `repl` and `run` commands work correctly
1. ✅ Example .tk scripts demonstrate DSL capabilities
1. ✅ DSL documentation is comprehensive and accurate
1. ✅ All tests pass (unit, e2e, quality, docs)
1. ✅ All quality checks pass (ruff, mypy, docs)
1. ✅ Code coverage is >40%

## Future Phases

### Phase 2: LSP Server (Future)

- Implement Language Server Protocol server in TypeScript
- Real-time syntax validation
- Auto-completion for operations
- Hover documentation
- Signature help

### Phase 3: VS Code Extension (Future)

- Tree view outliner
- Drag-and-drop restructuring
- Context menu operations
- Inline editing
- Keyboard shortcuts
- Document synchronization

## Notes

- Phase 1 focuses on Python implementation only (no VS Code extension or LSP server)
- The DSL provides a solid foundation for future LSP and outliner features
- All operations follow immutability pattern (return new documents)
- Error messages should be helpful and include line/column information
- REPL should be user-friendly with good help messages
- Example scripts should demonstrate real-world use cases
