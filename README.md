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
doctk execute script.tk guide.md

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
from doctk import Document, heading, promote, where
from doctk.integration import DocumentTreeBuilder, StructureOperations

# Load document
doc = Document.from_file("guide.md")

# Query: selectors filter to a subset (the rest of the document is not included)
level3 = doc | heading | where(level=3)

# Transform the whole document: promote every level-3 heading in place
promoted = doc.map(lambda n: n.promote() if heading(n) and n.level == 3 else n)
promoted.to_file("guide_updated.md")  # untouched nodes are written byte-identically

# Structure operations move whole sections, addressed by stable node ids
tree = DocumentTreeBuilder(doc).build_tree_with_ids()
intro_id = tree.children[0].id  # e.g. "heading:introduction:a3f5b9c2d1e4f6a7"
result = StructureOperations.move_up(doc, intro_id)
result = StructureOperations.nest(doc, node_id=tree.children[1].id, parent_id=intro_id)
```

## DSL and Interactive REPL

doctk includes a Domain-Specific Language (DSL) for document manipulation:

```bash
# Start REPL
$ doctk repl

# Execute operations (nodes are addressed by stable ids shown in `tree`)
doctk> load guide.md
doctk> tree                                          # List sections with their ids
doctk> promote heading:setup:1a2b3c4d5e6f7a8b        # Promote that section
doctk> nest heading:details:9f8e7d6c5b4a3f2e heading:setup:1a2b3c4d5e6f7a8b
doctk> save                                          # Write changes back
```

Script files (`.tk` extension):

```
# script.tk - Reorganize document structure
doc | promote heading:setup:1a2b3c4d5e6f7a8b
```

Execute with: `doctk execute script.tk guide.md`

**Note**: The script modifies the input file in place. To preserve the original, make a copy first.

## VS Code Extension

doctk includes a VS Code extension with visual document outlining and manipulation:

**Features:**

- 📋 **Tree view** of document structure
- 🖱️ **Drag-and-drop** to reorganize sections
- ⌨️ **Keyboard shortcuts** (promote, demote, move, delete, rename)
- 🎨 **Context menu** operations
- 🔄 **Real-time synchronization** with editor
- ⚡ **Performance optimized** for large documents (1000+ headings)

### Installing the Extension

**Prerequisites:**

- Python 3.12+ installed
- doctk package installed (see [Installation](#installation) above)
- VS Code 1.80.0 or higher

The extension resolves a Python interpreter automatically (ms-python's
active interpreter, then a workspace `.venv`, then `python3` on PATH) and
health-checks that doctk is importable before starting. If resolution
picks the wrong Python, set `doctk.pythonPath` in your settings.

**Option 1: Build from source** (recommended)

```bash
cd extensions/doctk-outliner
npm install
npm run compile
npx @vscode/vsce package
code --install-extension doctk-outliner-0.1.0.vsix
```

**Note:** The `.vsix` file is not included in the repository (it's gitignored). You must either build it yourself (Option 1) or download a pre-built version from [GitHub Releases](https://github.com/tommcd/doctk/releases) when available.

**Option 2: Install from command line** (after building or downloading)

```bash
code --install-extension path/to/doctk-outliner-0.1.0.vsix
```

**Option 3: Install via VS Code UI** (after building or downloading)

1. Open VS Code
1. Open Extensions view (`Ctrl+Shift+X` / `Cmd+Shift+X`)
1. Click "..." menu → "Install from VSIX..."
1. Navigate to and select the `.vsix` file

### Using the Extension

1. Open any Markdown (`.md`) file in VS Code
1. The "Document Outline" view appears automatically in the Explorer sidebar
1. If not visible: **View → Open View → Document Outline**
1. Use drag-and-drop, context menu, or keyboard shortcuts to manipulate sections

For detailed usage instructions, see the [extension README](extensions/doctk-outliner/README.md).

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

**Version**: 0.1.0-dev (MVP Complete - Pre-Release)

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

📋 **Before Public v0.1.0 Release**:

See the release preparation checklist (`.kiro/specs/release-preparation/tasks.md`) for detailed tasks:

- Logo design and branding
- Distribution strategy (PyPI vs local-only)
- VS Code marketplace preparation (if publishing)
- Documentation for end users
- GitHub release and changelog

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

- [Design Rationale](docs/design/01-initial-design.md) - Design principles and decisions
- [POC Summary](docs/archive/POC-SUMMARY.md) - Historical: Proof-of-concept validation
- [Complete Specification](docs/archive/SPECIFICATION.md) - Historical: Original specification (see `.kiro/specs/` for current)

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
