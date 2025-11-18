# VS Code Outliner Extension Spec

This spec covers the VS Code extension that provides a tree-based document outliner interface for the doctk project.

## Scope

This spec focuses on the **user interface layer** for document structure manipulation:

- Tree-based document visualization
- Drag-and-drop structure manipulation
- Context menu operations
- Inline editing
- Keyboard shortcuts
- Undo/redo integration
- Document synchronization
- Configuration and customization

## Requirements Coverage

- Requirements 1-6: Core outliner UI features
- Requirement 16: Document synchronization
- Requirement 19: Configuration (UI-specific settings)

## Dependencies

This spec depends on:

- **doctk-core-integration**: Provides the document manipulation API and Python bridge
- **doctk-language-server**: Optional integration for DSL editing in code blocks

## Related Specs

- [doctk-core-integration](../doctk-core-integration/): Core API and execution layer
- [doctk-language-server](../doctk-language-server/): LSP for doctk DSL

## Files

- `requirements.md`: Detailed requirements for the outliner extension
- `design.md`: Architecture and implementation design
- `tasks.md`: Implementation task breakdown
