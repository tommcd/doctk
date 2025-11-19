# Project Structure

## Root Layout

```
doctk/
├── src/doctk/              # Main source code
├── tests/                  # Test suite
├── docs/                   # Documentation
├── scripts/                # Development scripts
├── examples/               # Example documents
├── extensions/             # Editor extensions
├── .kiro/                  # Kiro configuration
├── pyproject.toml          # Project metadata and dependencies
├── tox.ini                 # Test orchestration
└── mkdocs.yml              # Documentation site config
```

## Source Code (`src/doctk/`)

### Core Modules

- **core.py** - Document and Node abstractions (foundation)
- **operations.py** - Composable operations (select, filter, promote, demote)
- **outliner.py** - Document structure visualization
- **cli.py** - Command-line interface

### Parsers (`src/doctk/parsers/`)

Format readers that convert external formats to doctk AST:

- **markdown.py** - Markdown parser (markdown-it-py based)

### Writers (`src/doctk/writers/`)

Format writers that convert doctk AST to external formats:

- **markdown.py** - Markdown writer

### Integration Layer (`src/doctk/integration/`)

Platform-agnostic bridge between core API and UIs:

- **operations.py** - Document structure operations (promote, demote, nest, unnest)
- **bridge.py** - JSON-RPC bridge for TypeScript-Python communication
- **protocols.py** - Type definitions and interfaces
- **memory.py** - LRU cache for document states
- **performance.py** - Performance monitoring
- **compat.py** - Compatibility utilities

### DSL Layer (`src/doctk/dsl/`)

Domain-Specific Language for document manipulation:

- **lexer.py** - Tokenization of DSL syntax
- **parser.py** - AST generation
- **executor.py** - DSL execution engine
- **repl.py** - Interactive REPL
- **codeblock.py** - Markdown code block execution

### LSP Layer (`src/doctk/lsp/`)

Language Server Protocol implementation for editor support:

- **server.py** - LSP server
- **completion.py** - Code completion provider
- **hover.py** - Hover documentation provider
- **registry.py** - Operation registry
- **config.py** - LSP configuration
- **ai_support.py** - AI-assisted features

### Tools (`src/doctk/tools/`)

External tool management system:

- **plugin.py** - Plugin system for external tools
- **manager.py** - Tool installation and version management
- **registry.py** - Tool registry

## Tests (`tests/`)

### Test Categories

- **unit/** - Fast, isolated unit tests
- **e2e/** - End-to-end CLI integration tests
- **quality/** - Meta tests for config consistency
- **docs/** - Documentation tests (spec validation, link checking)

### Test Markers

Use pytest markers to categorize tests:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.quality` - Quality/meta tests
- `@pytest.mark.docs` - Documentation tests
- `@pytest.mark.slow` - Slow tests (excluded by default)

## Documentation (`docs/`)

- **api/** - API reference documentation
- **design/** - Design documents and ADRs
- **development/** - Development guides
- **getting-started/** - User guides
- **guides/** - How-to guides
- **SPECIFICATION.md** - Complete specification and roadmap
- **POC-SUMMARY.md** - Proof-of-concept validation
- **SESSION-SUMMARY.md** - Development session notes
- **REPRODUCTION-GUIDE.md** - Issue reproduction guide

## Scripts (`scripts/`)

Development automation scripts:

- **setup-environment.sh** - Full environment setup
- **check-environment.sh** - Verify environment
- **setup-external-tools.py** - Install external tools
- **check-tools.py** - Verify tool versions
- **clean-tools.py** - Uninstall tools
- **clean-environment.sh** - Reset to fresh state
- **show-tox-commands.py** - Display tox environments
- **sync-precommit-versions.py** - Sync tool versions
- **validate-plugins.py** - Validate tool plugins
- **tool_manager.py** - Tool management utilities
- **tools/** - Tool plugin definitions (Markdown files)

## Extensions (`extensions/`)

Editor integrations:

- **doctk-outliner/** - VS Code extension (TypeScript)

## Configuration Files

- **pyproject.toml** - Project metadata, dependencies, tool configs
- **tox.ini** - Test orchestration and quality checks
- **mkdocs.yml** - Documentation site configuration
- **.pre-commit-config.yaml** - Pre-commit hooks
- **.gitignore** - Git ignore patterns
- **.python-version** - Python version for uv
- **.markdownlint.yaml** - Markdown linting rules
- **.lychee.toml** - Link checking configuration

## Naming Conventions

### Python Files

- **Modules**: lowercase with underscores (e.g., `operations.py`)
- **Classes**: PascalCase (e.g., `Document`, `OperationRegistry`)
- **Functions**: lowercase with underscores (e.g., `select_nodes`)
- **Constants**: UPPERCASE with underscores (e.g., `MAX_DEPTH`)

### Test Files

- **Pattern**: `test_*.py` (e.g., `test_operations.py`)
- **Test functions**: `test_<feature>_<scenario>` (e.g., `test_promote_heading_at_minimum_level`)

### Documentation

- **Guides**: lowercase with hyphens (e.g., `getting-started.md`)
- **Design docs**: numbered with descriptive names (e.g., `01-initial-design.md`)
- **API docs**: match module names (e.g., `core.md` for `core.py`)

## Import Conventions

### Absolute Imports

Always use absolute imports from the `doctk` package:

```python
from doctk.core import Document, Node
from doctk.operations import select, where
from doctk.integration.operations import promote_heading
```

### Module Organization

- Keep modules focused and single-purpose
- Avoid circular dependencies
- Use `__init__.py` to expose public APIs
- Keep internal utilities private (prefix with `_`)

## Architecture Layers

1. **Core Layer** (`core.py`, `operations.py`) - Pure, immutable document abstractions
1. **Parser/Writer Layer** (`parsers/`, `writers/`) - Format conversion
1. **Integration Layer** (`integration/`) - Platform-agnostic operations and bridges
1. **DSL Layer** (`dsl/`) - Domain-specific language
1. **LSP Layer** (`lsp/`) - Editor integration
1. **CLI Layer** (`cli.py`) - Command-line interface

Each layer depends only on layers below it, maintaining clean separation of concerns.
