# doctk Language Server Spec

This spec covers the Language Server Protocol (LSP) implementation for the doctk DSL.

## Scope

This spec focuses on **language intelligence features** for doctk DSL:

- Real-time syntax validation
- Auto-completion for operations and arguments
- Hover documentation
- AI-friendly structured information
- Error recovery and resilience
- Performance optimization

## Requirements Coverage

- Requirements 7-11: Language server features
- Requirement 18: Error recovery and resilience
- Requirement 19: Configuration (LSP-specific settings)

## Dependencies

This spec depends on:

- **doctk-core-integration**: Provides operation registry and core API integration

## Related Specs

- [doctk-core-integration](../doctk-core-integration/): Core API and execution layer
- [vscode-outliner-extension](../vscode-outliner-extension/): VS Code UI that hosts the language client

## Files

- `requirements.md`: Detailed requirements for the language server
- `design.md`: Architecture and implementation design
- `tasks.md`: Implementation task breakdown
