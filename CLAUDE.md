# CLAUDE.md - AI Assistant Guide for doctk

**Last Updated**: 2025-11-18
**Project Version**: 0.1.0 (Alpha - POC Complete)
**Repository**: https://github.com/tommcd/doctk

## Table of Contents

1. [Project Overview](#project-overview)
1. [Repository Structure](#repository-structure)
1. [Development Workflow](#development-workflow)
1. [Code Conventions](#code-conventions)
1. [Testing Strategy](#testing-strategy)
1. [Key Technologies](#key-technologies)
1. [Common Tasks](#common-tasks)
1. [Important Patterns](#important-patterns)
1. [External Tools System](#external-tools-system)
1. [Working with Kiro Specs](#working-with-kiro-specs)
1. [Quick Reference](#quick-reference)

______________________________________________________________________

## Project Overview

### What is doctk?

**doctk** (Document Toolkit) is a composable, functional toolkit for structured document manipulation written in Python. It provides elegant primitives for document transformation inspired by **category theory**, **set theory**, and the **Zen of Python**.

**Core Philosophy**:

- Documents as functors (mappable containers)
- Operations as morphisms (composable transformations)
- Immutability (pure transformations, no mutations)
- Type safety (well-typed operations)
- Format agnostic (universal AST with adapters)

### Current Status (v0.1.0)

**Implemented**:

- ✅ Core abstractions (Document, Node hierarchy)
- ✅ Markdown parser/writer
- ✅ Document outliner with tree visualization
- ✅ Functional operations (select, where, promote, demote)
- ✅ Pipe operator syntax
- ✅ CLI with demo and outline commands
- ✅ Comprehensive test suite
- ✅ Tool plugin system (Markdown-driven automation)

**In Progress (v0.2)**:

- 🚧 Enhanced node types (Section, Table, Inline)
- 🚧 Structure operations (lift, lower, nest, unnest)
- 🚧 Location tracking for error reporting

**Planned**:

- 📋 Path/CSS/XPath selection system
- 📋 Additional formats (reStructuredText, HTML, Confluence)
- 📋 Advanced tools (differ, validator, stats)
- 📋 Interactive TUI
- 📋 LSP server and VSCode extension

______________________________________________________________________

## Repository Structure

```
doctk/
├── src/doctk/                 # Main source code
│   ├── __init__.py            # Package exports
│   ├── core.py                # Core abstractions (Document, Node classes)
│   ├── operations.py          # Composable transformations
│   ├── outliner.py            # Document structure visualization
│   ├── cli.py                 # Command-line interface
│   ├── parsers/               # Format parsers
│   │   └── markdown.py        # Markdown parser (markdown-it-py)
│   ├── writers/               # Format writers
│   │   └── markdown.py        # Markdown writer
│   └── tools/                 # Tool management system
│       ├── plugin.py          # Markdown-driven plugin framework
│       ├── registry.py        # Tool registry
│       └── manager.py         # Tool lifecycle management
│
├── tests/                     # Test suite (814 lines)
│   ├── unit/                  # Unit tests (fast, isolated)
│   ├── e2e/                   # End-to-end CLI integration tests
│   ├── quality/               # Quality/meta tests
│   │   ├── shell/             # Shell script quality checks
│   │   └── meta/              # Configuration consistency tests
│   ├── docs/                  # Documentation quality tests
│   └── test_basic.py          # Core functionality tests
│
├── docs/                      # Documentation source
│   ├── index.md               # Documentation homepage
│   ├── getting-started/       # Installation & quick start
│   ├── development/           # Dev setup, testing, tooling, quality
│   ├── design/                # Design rationale & principles
│   ├── SPECIFICATION.md       # Complete specification & roadmap
│   ├── POC-SUMMARY.md         # Proof-of-concept validation
│   └── REPRODUCTION-GUIDE.md  # Complex reproduction procedures
│
├── scripts/                   # Automation & setup scripts
│   ├── setup-environment.sh   # Complete dev environment setup
│   ├── check-environment.sh   # Verify environment readiness
│   ├── clean-environment.sh   # Clean generated files/caches
│   ├── setup-external-tools.py
│   ├── check-tools.py
│   ├── validate-plugins.py
│   └── tools/                 # Tool plugin definitions (Markdown)
│       ├── shellcheck.md, shfmt.md, lychee.md, etc.
│
├── examples/                  # Sample documents
│   └── sample.md
│
├── .github/
│   └── workflows/tests.yml    # GitHub Actions CI/CD
│
├── .kiro/                     # Project specifications & steering
│   ├── specs/
│   └── steering/
│
├── .pre-commit-config.yaml    # Pre-commit hooks
├── .markdownlint.yaml         # Markdown linting rules
├── .lychee.toml               # Link checking config
├── pyproject.toml             # Python project config
├── tox.ini                    # Test orchestration (20+ environments)
├── mkdocs.yml                 # Documentation site config
├── README.md
├── CONTRIBUTING.md
└── LICENSE (MIT)
```

### Key Source Files by Size

| File | Lines | Purpose |
|------|-------|---------|
| `tools/plugin.py` | 492 | Markdown-driven plugin framework |
| `core.py` | 347 | Node types & Document class |
| `tools/manager.py` | 294 | Tool lifecycle management |
| `operations.py` | 243 | Composable transformations |
| `cli.py` | 242 | Command-line interface |
| `outliner.py` | 191 | Document structure visualization |
| `tools/registry.py` | 188 | Tool registry system |
| `parsers/markdown.py` | 148 | Markdown parsing |
| `writers/markdown.py` | 104 | Markdown generation |

______________________________________________________________________

## Development Workflow

### Initial Setup

**Automated (Recommended)**:

```bash
./scripts/setup-environment.sh
```

This script:

1. Installs `uv` (fast Python package manager)
1. Verifies Python 3.12+
1. Installs external tools (shellcheck, shfmt, lychee, markdownlint, taplo, hadolint)
1. Installs Python dependencies with `uv sync --all-groups` (dev and docs)
1. Installs tox globally
1. Sets up pre-commit hooks

**Manual**:

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies (includes dev and docs groups)
uv sync --all-groups

# Install external tools
python3 scripts/setup-external-tools.py

# Install pre-commit hooks
uv run pre-commit install
```

### Verification

```bash
./scripts/check-environment.sh  # Verify environment readiness
uv run doctk demo               # Run interactive demo
```

### Making Changes

1. **Create a branch**:

   ```bash
   git checkout -b feature/your-feature-name
   ```

1. **Make changes** following code conventions (see below)

1. **Add tests** for new functionality

1. **Run tests locally**:

   ```bash
   uv run pytest                      # Unit + e2e tests (skip slow)
   uv run pytest -m slow              # Run only slow tests
   uv run pytest -m "slow or not slow"  # Include all tests
   uv run pytest tests/quality/       # Quality/meta tests
   ```

1. **Run quality checks**:

   ```bash
   tox                    # All checks
   tox -e ruff            # Python linting
   tox -e ruff-fix        # Auto-fix formatting
   tox -e docs            # Documentation checks
   tox -e shellcheck      # Shell script linting
   ```

1. **Commit changes** using conventional commit format:

   ```
   type(scope): description

   [optional body]
   ```

   Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

   Example: `feat(operations): add lift/lower sibling operations`

1. **Pre-commit hooks** run automatically on commit

### CI/CD

GitHub Actions runs tests on:

- **Ubuntu only**: Python 3.12, 3.13, 3.14 (actively maintained versions)
- **Coverage**: Reported to codecov (Ubuntu 3.13)

**Total**: 3 jobs (optimized for speed - Windows dropped due to slow builds)

______________________________________________________________________

## Code Conventions

### Python Style

**Linter/Formatter**: Ruff (v0.14.0+)

**Key Rules** (enforced):

- **PEP 8** compliance
- **Line length**: 100 characters max
- **Quote style**: Double quotes
- **Indent style**: Spaces (4 spaces)
- **Type annotations**: Required for all public functions
- **Docstrings**: Required for all public APIs

**Ruff Configuration** (`pyproject.toml`):

```toml
[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "C4", "S"]
ignore = [
  "B008",  # Function calls in defaults (for typer)
  "B007",  # Unused loop variables
  "S101",  # Assert statements (in tests)
  "S603",  # Subprocess calls (test suite)
  "S607",  # Partial executable paths
  "E501",  # Line too long (handled by formatter)
]
```

### Code Style Examples

**Dataclass with Type Hints**:

```python
from dataclasses import dataclass, field
from typing import Any

@dataclass
class Heading(Node):
    """Heading node (h1-h6)."""

    level: int  # 1-6
    text: str
    children: list[Node] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def promote(self) -> "Heading":
        """Decrease heading level (h3 -> h2). Identity if already h1."""
        return Heading(
            level=max(1, self.level - 1),
            text=self.text,
            children=self.children,
            metadata=self.metadata,
        )
```

**Function with Docstring**:

```python
from collections.abc import Callable
from doctk.core import Document, Node

# Type alias for operations
Operation = Callable[[Document], Document]

def select(predicate: Callable[[Node], bool]) -> Operation:
    """
    Select nodes matching predicate.

    Args:
        predicate: Function that returns True for nodes to select

    Returns:
        Operation that filters document to matching nodes

    Example:
        >>> doc | select(is_heading)
        Document(3 nodes)
    """
    def transform(doc: Document) -> Document:
        return Document(nodes=[n for n in doc.nodes if predicate(n)])
    return transform
```

### Shell Script Style

**Formatter**: shfmt (Google Shell Style Guide)

**Key Rules**:

- **Indentation**: 2 spaces
- **Case indent**: Yes (`-ci`)
- **Binary ops on next line**: Yes (`-bn`)
- **Executable**: All `.sh` files must be executable

**Example**:

```bash
#!/usr/bin/env bash
set -euo pipefail

function install_tool() {
  local tool="$1"
  local version="$2"

  if command -v "$tool" &>/dev/null; then
    echo "✓ $tool already installed"
    return 0
  fi

  echo "Installing $tool v$version..."
  # Installation logic
}
```

### Markdown Style

**Linter**: markdownlint-cli2 (v0.18.1+)
**Formatter**: mdformat (v0.7.22+) with frontmatter plugin

**Key Rules** (`.markdownlint.yaml`):

- Consistent heading style
- No trailing spaces
- Proper list formatting
- Fenced code blocks with language specifiers

### TOML Style

**Formatter**: taplo (v0.9.3+)

- Alphabetically sorted keys
- Consistent spacing

______________________________________________________________________

## Testing Strategy

### Test Categories

doctk uses a multi-layered testing approach:

| Category | Location | Purpose | Speed | Markers |
|----------|----------|---------|-------|---------|
| **Unit** | `tests/unit/` | Fast, isolated tests | Fast | `@pytest.mark.unit` |
| **E2E** | `tests/e2e/` | CLI integration tests | Medium | `@pytest.mark.e2e` |
| **Quality** | `tests/quality/` | Config consistency, shell style | Slow | `@pytest.mark.quality` |
| **Docs** | `tests/docs/` | Markdown linting, link validation | Slow | `@pytest.mark.docs` |

### Running Tests

```bash
# Default: unit + e2e (skip slow)
uv run pytest

# Include slow tests
uv run pytest -m slow              # Run only slow tests
uv run pytest -m "slow or not slow"  # Run all tests (including slow)

# Specific categories
uv run pytest tests/unit/
uv run pytest tests/e2e/
uv run pytest tests/quality/
uv run pytest tests/docs/

# Specific test
uv run pytest tests/test_basic.py::test_document_creation

# With coverage
uv run pytest --cov=doctk --cov-report=html
```

### Coverage Configuration

**Target**: >80% (currently no hard requirement)

**Reports**: Generated in `reports/coverage/`

- `coverage.xml` - For codecov
- `html/` - HTML report
- `coverage.json` - JSON report

**Exclusions**:

- Test code (`*/tests/*`)
- Abstract methods (`@abstractmethod`)
- Debug code (`if __name__ == "__main__"`)
- Type checking blocks (`if TYPE_CHECKING:`)

### Test Naming Convention

```python
def test_<functionality>_<condition>():
    """Test that <expected behavior>."""
    # Arrange
    ...
    # Act
    ...
    # Assert
    ...
```

Example:

```python
def test_promote_heading_at_minimum_level():
    """Test that promoting h1 stays at h1 (identity)."""
    node = Heading(level=1, text="Title")
    result = node.promote()
    assert result.level == 1
```

______________________________________________________________________

## Key Technologies

### Core Dependencies (Production)

| Package | Version | Purpose |
|---------|---------|---------|
| `markdown-it-py` | >=3.0.0 | Markdown parsing |
| `mdit-py-plugins` | >=0.4.0 | Markdown parser extensions |
| `rich` | >=13.0.0 | Terminal formatting & rich output |
| `pyyaml` | >=6.0 | YAML parsing (tool metadata) |
| `tomli` | >=2.0.0 | TOML parsing (Python \<3.11) |

### Development Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | >=8.4.2 | Testing framework |
| `pytest-cov` | >=7.0.0 | Code coverage |
| `ruff` | >=0.14.0 | Linting & formatting |
| `pre-commit` | >=4.3.0 | Git hook framework |
| `tox` | >=4.31.0 | Test orchestration |
| `mkdocs` | >=1.6.1 | Documentation site generation |
| `mkdocs-material` | >=9.6.21 | Material theme |

### External Tools (Managed via Plugin System)

| Tool | Version | Purpose |
|------|---------|---------|
| `shellcheck` | 0.11.0 | Shell script linting |
| `shfmt` | 3.10.0 | Shell script formatting |
| `lychee` | 0.20.1 | Link validation |
| `markdownlint-cli2` | 0.18.1 | Markdown linting |
| `taplo` | 0.9.3 | TOML formatting |
| `hadolint` | 2.14.0 | Dockerfile linting |

**Note**: External tool versions are specified in `pyproject.toml` under `[tool.external-tools]`.

### Build System

- **Build backend**: hatchling
- **Package manager**: uv (recommended) or pip
- **Python versions**: 3.12, 3.13, 3.14 (actively maintained only)

______________________________________________________________________

## Common Tasks

### Add a New Node Type

1. **Define the node class** in `src/doctk/core.py`:

   ```python
   @dataclass
   class Table(Node):
       """Table node."""

       headers: list[str]
       rows: list[list[str]]
       metadata: dict[str, Any] = field(default_factory=dict)

       def accept(self, visitor: "NodeVisitor") -> Any:
           return visitor.visit_table(self)

       def to_dict(self) -> dict[str, Any]:
           return {
               "type": "table",
               "headers": self.headers,
               "rows": self.rows,
               "metadata": self.metadata,
           }
   ```

1. **Update the visitor** in `src/doctk/core.py`:

   ```python
   class NodeVisitor(ABC):
       @abstractmethod
       def visit_table(self, node: Table) -> Any:
           pass
   ```

1. **Add parser support** in `src/doctk/parsers/markdown.py`

1. **Add writer support** in `src/doctk/writers/markdown.py`

1. **Write tests** in `tests/unit/test_nodes.py`

### Add a New Operation

1. **Define the operation** in `src/doctk/operations.py`:

   ```python
   def wrap(tag: str) -> Operation:
       """
       Wrap nodes in a container.

       Args:
           tag: Container tag name

       Returns:
           Operation that wraps nodes

       Example:
           >>> doc | select(heading) | wrap("section")
       """
       def transform(doc: Document) -> Document:
           # Implementation
           ...
       return transform
   ```

1. **Export from `__init__.py`**:

   ```python
   from doctk.operations import wrap
   ```

1. **Write tests** in `tests/unit/test_operations.py`

1. **Update documentation** in `docs/` if needed

### Add an External Tool

1. **Create tool plugin** in `scripts/tools/toolname.md`:

   ````markdown
   # Tool Name

   Description of the tool.

   ## Metadata

   ```yaml
   name: toolname
   version: "1.0.0"
   install_method: npm
   package_name: toolname
   ```

   ## Installation

   ```bash install
   npm install -g toolname@1.0.0
   ```

   ## Version Check

   ```bash check-version
   toolname --version
   ```

   ## Uninstall

   ```bash uninstall
   npm uninstall -g toolname
   ```
   ````

1. **Add version to `pyproject.toml`**:

   ```toml
   [tool.external-tools]
   toolname = "1.0.0"
   ```

1. **Add tox environment** in `tox.ini`:

   ```ini
   [testenv:toolname]
   description = Run toolname checks
   commands = toolname check .
   ```

1. **Run setup**:

   ```bash
   python3 scripts/setup-external-tools.py
   ```

### Add a CLI Command

1. **Add command function** in `src/doctk/cli.py`:

   ```python
   @app.command()
   def validate(
       file_path: str = typer.Argument(..., help="Document to validate")
   ) -> None:
       """Validate document structure."""
       try:
           doc = Document.from_file(file_path)
           # Validation logic
           console.print("[green]✓[/green] Document is valid")
       except Exception as e:
           console.print(f"[red]✗[/red] Validation failed: {e}")
           raise typer.Exit(1)
   ```

1. **Write E2E tests** in `tests/e2e/test_cli.py`

1. **Update documentation** in `README.md` and `docs/`

### Run Documentation Site Locally

```bash
# Build and serve
tox -e docs-serve

# Open browser to http://127.0.0.1:8000

# Build only
tox -e docs-build
```

______________________________________________________________________

## Important Patterns

### Documents as Functors

Documents support functor operations (map, filter, reduce):

```python
# Map: Apply function to each node
doc.map(transform_fn)

# Filter: Select subset of nodes
doc.filter(predicate)

# Reduce: Fold operation
doc.reduce(fold_fn, initial_value)
```

### Operations as Morphisms

Operations are composable transformations:

```python
from doctk.operations import compose, select, where, promote

# Right-to-left composition (category theory)
process = compose(
    select(heading),
    where(level=3),
    promote()
)

result = process(doc)
```

### Pipe Operator Pattern

Unix-style pipelining for document operations:

```python
result = (
    doc
    | select(heading)
    | where(level=3)
    | promote()
)
```

### Immutability Pattern

**DO**: Return new objects, never mutate

```python
# Good
def promote(self) -> "Heading":
    return Heading(
        level=max(1, self.level - 1),
        text=self.text,
        children=self.children,
        metadata=self.metadata,
    )

# Bad
def promote(self) -> "Heading":
    self.level = max(1, self.level - 1)  # Mutation!
    return self
```

### Visitor Pattern

All nodes implement the visitor pattern for traversal:

```python
class NodeVisitor(ABC):
    @abstractmethod
    def visit_heading(self, node: Heading) -> Any:
        pass

    @abstractmethod
    def visit_paragraph(self, node: Paragraph) -> Any:
        pass

# Usage
node.accept(visitor)
```

### Anti-Patterns to Avoid

**DON'T**:

- ❌ Mutate nodes or documents in place
- ❌ Use bare `except:` clauses
- ❌ Skip type annotations on public APIs
- ❌ Write functions without docstrings
- ❌ Create files without adding tests
- ❌ Commit without running pre-commit hooks
- ❌ Use magic numbers (define constants instead)
- ❌ Write deeply nested code (extract functions)

**DO**:

- ✅ Return new instances from transformations
- ✅ Use specific exception types
- ✅ Add comprehensive type hints
- ✅ Write clear docstrings with examples
- ✅ Write tests before/during implementation
- ✅ Run `tox` before pushing
- ✅ Use named constants
- ✅ Keep functions small and focused

______________________________________________________________________

## External Tools System

### Novel Markdown-Driven Plugin Framework

doctk uses a **unique Markdown-driven tool management system** where tool definitions serve as both documentation and automation.

### How It Works

1. **Tool definition**: Each tool has a `.md` file in `scripts/tools/`
1. **YAML frontmatter**: Contains metadata (version, install method)
1. **Labeled code blocks**: Contain executable commands
1. **Single source of truth**: Markdown is both docs and automation

### Example Tool Plugin (`scripts/tools/shellcheck.md`)

````markdown
# shellcheck

Shell script static analysis tool.

## Metadata

```yaml
name: shellcheck
version: "0.11.0"
install_method: binary
download_url_template: "https://github.com/koalaman/shellcheck/releases/download/v{version}/shellcheck-v{version}.{os}.{arch}.tar.xz"
binary_path_in_archive: "shellcheck-v{version}/shellcheck"
os_map:
  linux: linux
  darwin: darwin
  windows: windows
arch_map:
  x86_64: x86_64
  arm64: aarch64
```

## Installation

```bash install
# Handled by Python script using download_url_template
```

## Version Check

```bash check-version
shellcheck --version
```

## Uninstall

```bash uninstall
rm -f ~/.local/bin/shellcheck
```
````

### Tool Management Commands

```bash
# Setup all external tools
python3 scripts/setup-external-tools.py

# Check tool installation
python3 scripts/check-tools.py

# Validate plugin definitions
python3 scripts/validate-plugins.py

# Verify environment (includes tool checks)
./scripts/check-environment.sh
```

### Adding New Tools

See "Add an External Tool" in [Common Tasks](#common-tasks).

______________________________________________________________________

## Working with Kiro Specs

### Overview

doctk uses **Kiro specs** for structured feature development. A Kiro spec formalizes the design and implementation process through a three-document structure that defines WHAT needs to be built, HOW it will be built, and the step-by-step implementation plan.

This approach ensures:

- Clear requirements and acceptance criteria
- Well-documented technical design
- Incremental, trackable progress
- Alignment between vision and implementation

### Spec Structure

Each spec lives in `.kiro/specs/<spec-name>/` and consists of three documents:

1. **requirements.md** - Defines WHAT needs to be built

   - Introduction and goals
   - Glossary of domain terms
   - Formal requirements (WHEN/SHALL format)
   - Acceptance criteria

1. **design.md** - Defines HOW it will be built

   - Architecture and technical approach
   - Code structure and organization
   - Key components and modules
   - Design patterns and principles
   - Integration points

1. **tasks.md** - Defines the implementation plan

   - Discrete, ordered tasks with checkboxes
   - Sub-tasks for complex work
   - Links to requirements
   - Progress tracking

### Basic Workflow

When implementing a Kiro spec:

```bash
# 1. Read the spec documents in order
cat .kiro/specs/<spec-name>/requirements.md
cat .kiro/specs/<spec-name>/design.md
cat .kiro/specs/<spec-name>/tasks.md

# 2. Implement the first uncompleted task
# 3. Verify against requirements
# 4. Update tasks.md - mark task as complete [x]
# 5. Test your work
# 6. Move to next task
```

**Task marking format**:

```markdown
- [ ] 1. Not started task
  - [x] Completed sub-task
  - [ ] Pending sub-task
- [x] 2. Completed task
- [ ]* 3. Optional task
```

### Quick Reference

| Need | Location |
|------|----------|
| Find specs | `.kiro/specs/<spec-name>/` |
| Read requirements | `.kiro/specs/<spec-name>/requirements.md` |
| Read design | `.kiro/specs/<spec-name>/design.md` |
| Track progress | `.kiro/specs/<spec-name>/tasks.md` |
| Implementation guide | `claude-code-kiro-spec-prompt.md` |

### Detailed Guide

For comprehensive instructions on working with Kiro specs, including:

- How to read and interpret requirements
- Understanding design documents
- Task execution best practices
- Progress tracking conventions
- Tips for successful spec implementation

**See**: `claude-code-kiro-spec-prompt.md` in the repository root.

______________________________________________________________________

## Quick Reference

### Essential Commands

```bash
# Setup
./scripts/setup-environment.sh      # Initial setup
./scripts/check-environment.sh      # Verify setup

# Development
uv run doctk demo                   # Run demo
uv run doctk outline <file>         # View structure
uv run pytest                       # Run tests
tox                                 # All quality checks

# Quality
tox -e ruff                         # Lint Python
tox -e ruff-fix                     # Fix Python formatting
tox -e shellcheck                   # Lint shell scripts
tox -e docs                         # Check documentation

# Documentation
tox -e docs-serve                   # Serve docs locally
```

### Tox Environments

Run `python3 scripts/show-tox-commands.py` for full list.

**Key environments**:

- `tox -e check-environment` - Verify dev environment
- `tox -e ruff` / `tox -e ruff-fix` - Python linting/formatting
- `tox -e shellcheck` - Shell script linting
- `tox -e shfmt` / `tox -e shfmt-fix` - Shell formatting
- `tox -e taplo` / `tox -e taplo-fix` - TOML formatting
- `tox -e docs` / `tox -e docs-fix` - Documentation checks
- `tox -e pytest` - All tests
- `tox -e docs-serve` - Serve documentation
- `tox` - Run all checks

### File Locations

| Need | Location |
|------|----------|
| Add node type | `src/doctk/core.py` |
| Add operation | `src/doctk/operations.py` |
| Add CLI command | `src/doctk/cli.py` |
| Add parser | `src/doctk/parsers/` |
| Add writer | `src/doctk/writers/` |
| Add unit test | `tests/unit/` |
| Add E2E test | `tests/e2e/` |
| Add external tool | `scripts/tools/toolname.md` |
| Update dependencies | `pyproject.toml` (dependency-groups) |
| Add tox environment | `tox.ini` |
| Update pre-commit hooks | `.pre-commit-config.yaml` |

### Key Documentation

| Topic | Location |
|-------|----------|
| Complete specification | `docs/SPECIFICATION.md` |
| POC summary | `docs/POC-SUMMARY.md` |
| Design rationale | `docs/design/01-initial-design.md` |
| Development setup | `docs/development/setup.md` |
| Testing guide | `docs/development/testing.md` |
| Tool management | `docs/development/tooling.md` |
| Quality standards | `docs/development/quality.md` |
| Reproduction guide | `docs/REPRODUCTION-GUIDE.md` |

### Core Abstractions Reference

```python
# Document (functor)
from doctk import Document

doc = Document.from_file("file.md")
doc.map(fn)
doc.filter(predicate)
doc.reduce(fold_fn, init)
doc.to_file("output.md")

# Nodes
from doctk.core import Heading, Paragraph, List, ListItem, CodeBlock

# Operations
from doctk.operations import select, where, heading, promote, demote, compose

# Pipe style
result = doc | select(heading) | where(level=3) | promote()

# Composition
process = compose(select(heading), where(level=3), promote())
result = process(doc)
```

______________________________________________________________________

## When Working on This Project

### Before Starting Work

1. ✅ Run `./scripts/check-environment.sh` to verify setup
1. ✅ Read `docs/SPECIFICATION.md` for context on planned features
1. ✅ Check `docs/POC-SUMMARY.md` for lessons learned
1. ✅ Review existing tests to understand patterns

### While Working

1. ✅ Follow the immutability pattern (no mutations)
1. ✅ Add type annotations to all functions
1. ✅ Write docstrings with examples
1. ✅ Write tests as you develop (TDD preferred)
1. ✅ Run `uv run pytest` frequently
1. ✅ Keep functions small and focused

### Before Committing

1. ✅ Run `tox` to verify all checks pass
1. ✅ Ensure tests cover new code
1. ✅ Update documentation if needed
1. ✅ Use conventional commit messages
1. ✅ Let pre-commit hooks run (don't skip)

### Design Principles to Remember

1. **Composability**: Build complex from simple primitives
1. **Purity**: Transformations, not mutations
1. **Type Safety**: Well-typed operations
1. **Readability**: Self-documenting code
1. **Testing**: Comprehensive coverage

______________________________________________________________________

## Additional Resources

- **GitHub Repository**: https://github.com/tommcd/doctk
- **Documentation Site**: https://tommcd.github.io/doctk/
- **Issue Tracker**: https://github.com/tommcd/doctk/issues
- **Discussions**: https://github.com/tommcd/doctk/discussions
- **License**: MIT

______________________________________________________________________

**Note to AI Assistants**: This project values code quality, testing, and documentation. Always run quality checks before suggesting changes are complete. When implementing new features, prioritize composability and immutability. Consult `docs/SPECIFICATION.md` for planned architecture before proposing major changes.
