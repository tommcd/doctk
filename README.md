# doctk - Document Toolkit

[![Tests](https://github.com/tommcd/doctk/workflows/Tests/badge.svg)](https://github.com/tommcd/doctk/actions)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

A composable, functional toolkit for structured document manipulation with interactive REPL, VS Code extension, and Language Server support.

## Philosophy

Inspired by category theory, set theory, and the Zen of Python, `doctk` provides elegant primitives for document transformation:

- **Composable**: Complex operations built from simple primitives
- **Pure**: Operations transform rather than mutate
- **Format-agnostic**: Operates on universal document AST
- **Type-safe**: Well-typed transformations
- **Pipeable**: Unix-philosophy pipelines for documents

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/tommcd/doctk.git
cd doctk

# Install with uv (recommended)
uv sync
uv pip install -e .

# Or with pip
pip install -e .
```

### Usage

```bash
# Interactive REPL for document manipulation
doctk repl guide.md

# Execute script files
doctk execute script.tk guide.md -o guide_updated.md

# View document outline
doctk outline README.md --headings-only

# Run interactive demo
doctk demo
```

Current CLI commands (v0.1):

```bash
doctk repl <file>              # Interactive REPL with DSL
doctk execute <script> <file>  # Execute .tk script files
doctk outline <file>           # View document structure
doctk demo                     # Interactive demonstration
```

## Python API

```python
from doctk import Document
from doctk.operations import select, where, promote, demote
from doctk.integration import StructureOperations

# Load document
doc = Document.from_file("guide.md")

# Pipe-style transformations
result = doc | select(heading) | where(level=3) | promote()

# Save
result.to_file("guide_updated.md")

# Structure operations (move, nest, unnest)
ops = StructureOperations(doc)
result = ops.move_up(node_id="h2-intro")
result = ops.nest(node_id="h3-details", under_id="h2-intro")
```

## DSL and Interactive REPL

doctk includes a Domain-Specific Language (DSL) for document manipulation:

```bash
# Start REPL
$ doctk repl guide.md

# Execute operations
doctk> promote(1)        # Promote first heading
doctk> move_up(2)        # Move second section up
doctk> nest(3, under=1)  # Nest section 3 under section 1
doctk> save output.md    # Save changes
```

Script files (`.tk` extension):

```
# script.tk - Reorganize document structure
promote(1)
move_up(2)
nest(3, under=1)
```

Execute with: `doctk execute script.tk guide.md -o output.md`

## VS Code Extension

doctk includes a VS Code extension with visual document outlining and manipulation:

**Features:**
- 📋 **Tree view** of document structure
- 🖱️ **Drag-and-drop** to reorganize sections
- ⌨️ **Keyboard shortcuts** (promote, demote, move, delete, rename)
- 🎨 **Context menu** operations
- 🔄 **Real-time synchronization** with editor
- ⚡ **Performance optimized** for large documents (1000+ headings)

**Installation:**

```bash
# Install the extension
code --install-extension extensions/doctk-outliner/doctk-outliner-0.1.0.vsix
```

**Usage:**
1. Open any Markdown file in VS Code
2. Open the "Document Outline" view in the sidebar
3. Use drag-and-drop, context menu, or keyboard shortcuts to manipulate document structure

## Language Server

doctk includes a Language Server Protocol (LSP) implementation with:

- ✅ **Syntax highlighting** for `.tk` DSL files
- ✅ **Auto-completion** for operations
- ✅ **Hover documentation** with examples
- ✅ **Diagnostics** and error checking
- ✅ **Signature help** for operation parameters
- ✅ **AI agent support** with structured operation catalog

The language server is automatically activated when you open `.tk` files in VS Code.

## Core Concepts

### Documents as Functors

Documents are containers that can be mapped over:

```python
doc.map(transform_fn)  # Apply to each node
doc.filter(predicate)  # Subset selection
doc.reduce(fold_fn, init)  # Fold operation
```

### Operations as Morphisms

Operations are composable transformations:

```python
from doctk.operations import compose

process = compose(
    select(heading),
    where(level=3),
    promote()
)

result = process(doc)
```

### Set Operations

Documents support set algebra:

```python
doc1.union(doc2)      # Combine
doc1.intersect(doc2)  # Common elements
doc1.diff(doc2)       # Unique to doc1
```

## Project Status

**Version**: 0.1.0 (MVP Complete - Ready for Release)

✅ **Implemented**:

**Core Engine:**
- Core abstractions (Document, Node hierarchy, operations)
- Markdown parser and writer with markdown-it-py
- Document outliner with tree visualization
- Comprehensive test suite (**749 tests passing**, 68.78% coverage)
- Type-safe operations with full type annotations

**Operations:**
- Selection and filtering (select, where)
- Level operations (promote, demote, lift, lower)
- Structure operations (nest, unnest, move_up, move_down)
- Pipe operator syntax (`doc | select(heading) | promote()`)
- Composable transformations

**DSL and Execution:**
- Domain-Specific Language (DSL) for document manipulation
- Interactive REPL with state management
- Script file execution (`.tk` files)
- Code block execution in Markdown documents
- Error recovery and reporting with line/column positions

**VS Code Extension:**
- Tree view with hierarchical document outline
- Drag-and-drop section reorganization
- Context menu operations
- Keyboard shortcuts (promote, demote, move, delete, rename)
- Real-time document synchronization
- Performance optimizations for large documents (1000+ headings)
- Packaged as `.vsix` (ready for installation)

**Language Server (LSP):**
- Auto-completion for operations
- Hover documentation with examples
- Syntax validation with diagnostics
- Signature help for parameters
- Document symbols and navigation
- AI agent support with structured operation catalog
- Performance optimized (< 200ms response times)

**Integration & Architecture:**
- JSON-RPC bridge for TypeScript ↔ Python communication
- Pluggable architecture for multiple interfaces
- Granular document edits (preserves cursor position)
- Centralized node ID generation
- Memory management with LRU cache
- Error recovery and resilience
- Comprehensive E2E testing

📋 **Remaining for v0.1.0 Release**:

- GitHub release and changelog
- Publish VS Code extension to marketplace (optional)

🚀 **Planned for v0.2.0**:

- Enhanced node types (Section, Table, Inline)
- Path/CSS/XPath selection system
- Additional format support (reStructuredText, HTML, Confluence)
- Advanced tools (differ, validator, stats)
- Interactive TUI

See [Documentation](https://tommcd.github.io/doctk/) for complete guides and API reference.

## Development

### Quick Setup

Get started with development in one command:

```bash
./scripts/setup-environment.sh
```

This installs all dependencies, external tools, and sets up pre-commit hooks.

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test categories
uv run pytest tests/unit/      # Unit tests
uv run pytest tests/e2e/       # End-to-end tests
uv run pytest tests/quality/   # Quality checks

# Run with coverage
uv run pytest --cov=doctk --cov-report=html
```

### Code Quality Tools

doctk uses comprehensive quality tooling:

```bash
# Run all quality checks
tox

# Run specific checks
tox -e ruff          # Python linting
tox -e shellcheck    # Shell script linting
tox -e docs          # Documentation checks

# Auto-fix issues
tox -e ruff-fix      # Fix Python formatting
tox -e docs-fix      # Fix documentation formatting
```

Pre-commit hooks run automatically on commit to catch issues early.

### Documentation

Full documentation is available at [https://tommcd.github.io/doctk/](https://tommcd.github.io/doctk/):

**Getting Started:**
- [Installation](https://tommcd.github.io/doctk/getting-started/installation/)
- [Quick Start Guide](https://tommcd.github.io/doctk/getting-started/quick-start/)

**API Reference:**
- [Core Integration API](https://tommcd.github.io/doctk/api/core-integration/) - StructureOperations, ExtensionBridge
- [DSL API](https://tommcd.github.io/doctk/api/dsl/) - Parser, Lexer, Executor, REPL
- [Language Server API](https://tommcd.github.io/doctk/api/lsp/) - LSP features and AI support

**Development Guides:**
- [Development Setup](https://tommcd.github.io/doctk/development/setup/)
- [Testing Guide](https://tommcd.github.io/doctk/development/testing/)
- [Tool Management](https://tommcd.github.io/doctk/development/tooling/)
- [Code Quality Standards](https://tommcd.github.io/doctk/development/quality/)

**Integration Guides:**
- [Adding New Interfaces](https://tommcd.github.io/doctk/guides/adding-new-interface/) - Extend doctk to new platforms
- [Extending the DSL](https://tommcd.github.io/doctk/guides/extending-dsl/) - Add custom operations

**Additional Resources:**
- [POC Summary](docs/POC-SUMMARY.md) - Proof-of-concept validation
- [Complete Specification](docs/SPECIFICATION.md) - Full technical specification

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Quick start for contributors:

1. Run `./scripts/setup-environment.sh` to set up your environment
1. Make your changes and add tests
1. Run `tox` to verify all checks pass
1. Submit a pull request

## License

MIT - see [LICENSE](LICENSE) for details

<!-- GPG signing test from Windows -->
