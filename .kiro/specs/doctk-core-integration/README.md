# doctk Core Integration & Execution Spec

This spec covers the core integration layer and execution capabilities that bridge UI components with the doctk core API.

## Scope

This spec focuses on the **backend and execution layer**:

- Document manipulation API (promote, demote, nest, unnest, move operations)
- Extension bridge (JSON-RPC communication)
- Pluggable architecture interfaces
- REPL for interactive execution
- Script file execution
- Code block execution in Markdown
- Performance optimization for large documents
- Integration with doctk core API

## Requirements Coverage

- Requirements 12-14: Script execution (REPL, files, code blocks)
- Requirement 15: Pluggable architecture
- Requirement 17: Performance for large documents
- Requirement 20: Integration with doctk core API

## Dependencies

This spec depends on:

- **doctk core**: The underlying document manipulation library

## Related Specs

- [vscode-outliner-extension](../vscode-outliner-extension/): VS Code UI that uses this integration layer
- [doctk-language-server](../doctk-language-server/): LSP that uses the operation registry

## Files

- `requirements.md`: Detailed requirements for core integration and execution
- `design.md`: Architecture and implementation design
- `tasks.md`: Implementation task breakdown

## Key Design Decisions

### Granular Edits (PR #6 Critical Issue)

The backend computes specific modified ranges for each operation, allowing the frontend to apply minimal edits. This preserves cursor position and undo/redo stack.

### Centralized Node ID Generation (PR #6 Medium Priority)

The backend is the single source of truth for node IDs, eliminating synchronization issues between frontend and backend.

### Pluggable Architecture

The abstract `DocumentInterface` allows multiple UI implementations (VS Code, JupyterLab, etc.) to share the same core logic.
