# doctk - Document Toolkit

**A composable, functional toolkit for structured document manipulation with interactive REPL, VS Code extension, and Language Server support.**

[![Tests](https://github.com/tommcd/doctk/workflows/Tests/badge.svg)](https://github.com/tommcd/doctk/actions)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

**Version**: 0.1.0 (MVP Complete - Ready for Release)

## Philosophy

Inspired by category theory, set theory, and the Zen of Python, `doctk` provides elegant primitives for document transformation:

- **Composable**: Complex operations built from simple primitives
- **Pure**: Operations transform rather than mutate
- **Format-agnostic**: Operates on universal document AST
- **Type-safe**: Well-typed transformations
- **Pipeable**: Unix-philosophy pipelines for documents

## Features

### Core Engine
- 📚 **Core abstractions** - Document, Node hierarchy, operations
- 🔧 **Markdown support** - Full parser and writer with markdown-it-py
- 🌲 **Document outliner** - Tree visualization with rich console output
- ✅ **749 tests passing** - Comprehensive test coverage (68.78%)
- 🔒 **Type-safe** - Full type annotations throughout

### Operations
- 🔍 **Selection & filtering** - select, where predicates
- ↕️ **Level operations** - promote, demote, lift, lower
- 🔄 **Structure operations** - nest, unnest, move_up, move_down
- ⚡ **Pipe syntax** - `doc | select(heading) | promote()`
- 🧩 **Composable** - Chain operations functionally

### DSL and Execution
- 💬 **Domain-Specific Language** - Intuitive document manipulation DSL
- 🖥️ **Interactive REPL** - Live document editing with state management
- 📄 **Script execution** - Run `.tk` files with doctk commands
- 📝 **Code blocks** - Execute DSL from Markdown documents
- ⚠️ **Error recovery** - Line/column position tracking

### VS Code Extension
- 🌲 **Tree view** - Hierarchical document outline sidebar
- 🖱️ **Drag-and-drop** - Visual section reorganization
- ⌨️ **Keyboard shortcuts** - Fast operations (promote, demote, move, delete, rename)
- 🎨 **Context menus** - Right-click operations
- 🔄 **Real-time sync** - Bidirectional editor synchronization
- ⚡ **Performance** - Optimized for 1000+ heading documents
- 📦 **Ready to install** - Packaged as `.vsix`

### Language Server (LSP)
- ✨ **Auto-completion** - Operation suggestions as you type
- 📖 **Hover docs** - Rich documentation with examples
- 🔍 **Syntax validation** - Real-time diagnostics
- 💡 **Signature help** - Parameter hints and types
- 🗺️ **Document symbols** - Navigate operations easily
- 🤖 **AI support** - Structured operation catalog for AI agents
- ⚡ **Fast** - < 200ms response times

### Integration & Architecture
- 🔌 **JSON-RPC bridge** - TypeScript ↔ Python communication
- 🏗️ **Pluggable** - Extensible architecture for new interfaces
- ✏️ **Granular edits** - Cursor position preservation
- 🆔 **Centralized IDs** - Consistent node identification
- 💾 **Memory management** - LRU cache for large documents
- 🛡️ **Error resilience** - Automatic recovery and retry
- 🧪 **E2E tested** - Comprehensive integration tests

---

## Quick Examples

### Python API

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

# Structure operations (static methods)
result = StructureOperations.move_up(doc, node_id="h2-intro")
result = StructureOperations.nest(doc, node_id="h3-details", under_id="h2-intro")
```

### Interactive REPL

```bash
# Start REPL
$ doctk repl guide.md

# Execute operations
doctk> promote(1)        # Promote first heading
doctk> move_up(2)        # Move second section up
doctk> nest(3, under=1)  # Nest section 3 under section 1
doctk> save output.md    # Save changes
```

### Script Execution

```
# script.tk - Reorganize document structure
promote(1)
move_up(2)
nest(3, under=1)
```

Execute with: `doctk execute script.tk guide.md`

**Note**: The script modifies the input file in place.

---

## Getting Started

Ready to dive in? Check out these resources:

- **[Installation Guide](getting-started/installation/)** - Get doctk installed
- **[Quick Start](getting-started/quick-start/)** - Hands-on tutorial
- **[API Reference](api/core-integration/)** - Complete API documentation
- **[Integration Guides](guides/adding-new-interface/)** - Extend doctk to new platforms

---

## Roadmap

🚀 **Planned for v0.2.0**:

- Enhanced node types (Section, Table, Inline)
- Path/CSS/XPath selection system
- Additional format support (reStructuredText, HTML, Confluence)
- Advanced tools (differ, validator, stats)
- Interactive TUI

---

## License

MIT - see [LICENSE](https://github.com/tommcd/doctk/blob/main/LICENSE) for details.
