# doctk - Document Toolkit

[![Tests](https://github.com/tommcd/doctk/workflows/Tests/badge.svg)](https://github.com/tommcd/doctk/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

A composable, functional toolkit for structured document manipulation.

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
# View document outline
doctk outline README.md --headings-only

# Run interactive demo
doctk demo

# See all commands
doctk help
```

Current CLI commands (v0.1):
- `doctk outline <file>` - View document structure
- `doctk demo` - Interactive demonstration
- `doctk help` - Show help

## Python API

```python
from doctk import Document
from doctk.operations import select, where, promote

# Load document
doc = Document.from_file("guide.md")

# Pipe-style transformations
result = doc | select(heading) | where(level=3) | promote()

# Or fluent API
result = doc.select(heading).where(level=3).promote()

# Save
result.to_file("guide_updated.md")
```

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

**Version**: 0.1.0 (Alpha - POC Complete)

✅ **Implemented**:
- Core abstractions (Document, Node, operations)
- Markdown parser and writer
- Document outliner with tree visualization
- Basic operations (select, where, promote, demote)
- Pipe operator syntax
- CLI with demo and outline commands
- Comprehensive test suite (12 tests passing)

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

See [docs/SPECIFICATION.md](docs/SPECIFICATION.md) for the complete roadmap.

## Documentation

- **[Design](docs/design/01-initial-design.md)**: Design rationale and principles
- **[POC Summary](docs/POC-SUMMARY.md)**: Proof-of-concept validation
- **[Specification](docs/SPECIFICATION.md)**: Complete specification and roadmap
- **[Contributing](CONTRIBUTING.md)**: Development guidelines

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT - see [LICENSE](LICENSE) for details
