# doctk - Document Toolkit

A composable, functional toolkit for structured document manipulation.

## Philosophy

Inspired by category theory, set theory, and the Zen of Python, `doctk` provides elegant primitives for document transformation:

- **Composable**: Complex operations built from simple primitives
- **Pure**: Operations transform rather than mutate
- **Format-agnostic**: Operates on universal document AST
- **Type-safe**: Well-typed transformations
- **Pipeable**: Unix-philosophy pipelines for documents

## Features

### Core Capabilities

- **Document Parsing**: Parse Markdown documents into a universal AST
- **Functional Operations**: Transform documents using composable operations
- **Selection System**: Query and filter document nodes with predicates
- **Pipe Syntax**: Chain operations using Python's pipe operator
- **CLI Tools**: Command-line interface for common document tasks

### Current Status

**Version**: 0.1.0 (Alpha - POC Complete)

✅ **Implemented**:

- Core abstractions (Document, Node, operations)
- Markdown parser and writer
- Document outliner with tree visualization
- Basic operations (select, where, promote, demote)
- Pipe operator syntax
- CLI with demo and outline commands
- Comprehensive test suite

🚧 **In Progress** (v0.2):

- Enhanced node types (Section, Table, Inline)
- Structure operations (lift, lower, nest, unnest)
- Location tracking for error reporting

📋 **Planned**:

- Path/CSS/XPath selection system
- reStructuredText, HTML, Confluence support
- Advanced tools (differ, validator, stats)
- Interactive TUI
- LSP server and VSCode extension

## Quick Example

```python
from doctk import Document
from doctk.operations import select, where, promote

# Load document
doc = Document.from_file("guide.md")

# Pipe-style transformations
result = doc | select(heading) | where(level=3) | promote()

# Save
result.to_file("guide_updated.md")
```

## Getting Started

Ready to dive in? Check out the [Installation Guide](getting-started/installation.md) to get started, or jump straight to the [Quick Start](getting-started/quick-start.md) for a hands-on introduction.

## Documentation

- **[Getting Started](getting-started/installation.md)**: Installation and quick start
- **[Development](development/setup.md)**: Contributing and development setup

## License

MIT - see [LICENSE](https://github.com/tommcd/doctk/blob/main/LICENSE) for details.
