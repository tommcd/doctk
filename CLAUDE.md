# CLAUDE.md - AI Assistant Guide for doctk

**Last Updated**: 2025-11-18
**Project Version**: 0.1.0 (Alpha - POC Complete)
**Repository**: https://github.com/tommcd/doctk

## Quick Start for AI Assistants

**CRITICAL: This project uses spec-driven development with Kiro specs.**

All work on this project follows the spec-driven development methodology. You MUST understand how Kiro specs work before contributing.

**Required Reading (in order):**

1. **[AGENTS.md](AGENTS.md)** - How to work with Kiro specs (requirements → design → tasks)
1. **[.kiro/steering/workflow.md](.kiro/steering/workflow.md)** - Development workflow and quality standards
1. **[.kiro/steering/ai-agent-quick-reference.md](.kiro/steering/ai-agent-quick-reference.md)** - Quick reference and golden rules

**This document (CLAUDE.md)** provides comprehensive Claude-specific project context and reference information.

**Auto-included steering documents** (always in your context):

- **ai-agent-quick-reference.md** - Golden rules, checklist, commands
- **workflow.md** - Development workflow, branch strategy, quality gates
- **spec-maintenance.md** - Keeping specs synchronized with code
- **product.md** - Product overview and philosophy
- **tech.md** - Tech stack, build system, and common commands
- **structure.md** - Project organization and conventions

## Document Purpose

This document provides **comprehensive project context for Claude**.

**IMPORTANT:** This project was built using **spec-driven development with Kiro specs**. All AI agents working on this project must understand and follow the Kiro spec methodology.

**Essential guides for spec-driven development:**

1. **[AGENTS.md](AGENTS.md)** - Understanding Kiro specs (requirements, design, tasks)
1. **[.kiro/steering/workflow.md](.kiro/steering/workflow.md)** - Development workflow
1. **[.kiro/steering/ai-agent-quick-reference.md](.kiro/steering/ai-agent-quick-reference.md)** - Quick reference
1. **CLAUDE.md** (this document) - Comprehensive project reference

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
1. [Understanding the .kiro Directory](#understanding-the-kiro-directory)
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

**For complete project structure**, see [Project Structure](.kiro/steering/structure.md).

**Key directories:**

- `src/doctk/` - Main source code (core, operations, parsers, writers, integration, DSL, LSP)
- `tests/` - Test suite (unit, e2e, quality, docs)
- `docs/` - Documentation (getting-started, development, api, design, archive)
- `scripts/` - Automation scripts and tool plugins
- `.kiro/specs/` - Feature specifications (requirements, design, tasks)
- `.kiro/steering/` - AI assistant guidance (auto-included context)

### Key Source Files by Purpose

| Module | Purpose |
|--------|---------|
| `core.py` | Document/Node abstractions (foundation) |
| `operations.py` | Composable transformations |
| `integration/` | Platform-agnostic bridge layer |
| `dsl/` | Domain-Specific Language |
| `lsp/` | Language Server Protocol |
| `tools/` | External tool management |
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

### Quick Start

```bash
# Setup
./scripts/setup-environment.sh
./scripts/check-environment.sh

# Development
uv run pytest                    # Run tests
tox                              # Run quality checks
git commit -m "feat: description"  # Commit with conventional format
```

**For detailed guides**, see:

- **[Development Setup](docs/development/setup.md)** - Complete setup instructions
- **[Testing Guide](docs/development/testing.md)** - Running and writing tests
- **[Quality Standards](docs/development/quality.md)** - Code quality checks
- **[Tooling Guide](docs/development/tooling.md)** - External tools management

### CI/CD

GitHub Actions runs tests on:

- **Ubuntu only**: Python 3.12, 3.13, 3.14 (actively maintained versions)
- **Coverage**: Reported to codecov (Ubuntu 3.13)

**Total**: 3 jobs (optimized for speed - Windows dropped due to slow builds)

______________________________________________________________________

## Code Conventions

**For complete quality standards**, see [Quality Guide](docs/development/quality.md).

**Quick reference:**

- **Python**: PEP 8, 100 char lines, type annotations required, ruff for linting/formatting
- **Shell**: Google Shell Style Guide, 2-space indent, shellcheck + shfmt
- **Markdown**: markdownlint + mdformat
- **TOML**: taplo formatting

**Run quality checks:**

```bash
tox                    # All checks
tox -e ruff-fix        # Auto-fix Python
tox -e docs-build      # Build docs (strict mode)
```

______________________________________________________________________

## Testing Strategy

**For comprehensive testing guide**, see [Testing Guide](docs/development/testing.md).

**Quick reference:**

```bash
uv run pytest                    # Run all tests (skip slow)
uv run pytest -m "slow or not slow"  # Include slow tests
uv run pytest --cov=doctk        # With coverage
```

**Test categories:** unit, e2e, quality, docs (see testing guide for details)

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

## Understanding the .kiro Directory

The `.kiro/` directory contains two important subdirectories for AI assistants:

### .kiro/steering/

**Purpose**: Provides always-available context and guidance for AI assistants.

Steering documents are automatically included in your context and contain:

- **product.md** - Product overview, philosophy, and current status
- **tech.md** - Tech stack, build system, common commands, testing strategy
- **structure.md** - Project organization, folder structure, naming conventions
- **python-wsl-uv.md** - Python environment and WSL-specific command rules
- **validate-spec-accuracy.md** - Spec validation testing guidelines

**When to reference**: Anytime you need to understand project conventions, tech stack, or structure without asking basic questions.

### .kiro/specs/

**Purpose**: Contains structured feature specifications for incremental development.

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
| Project conventions | `.kiro/steering/` (auto-included) |
| Product overview | `.kiro/steering/product.md` |
| Tech stack & commands | `.kiro/steering/tech.md` |
| Project structure | `.kiro/steering/structure.md` |
| Find specs | `.kiro/specs/<spec-name>/` |
| Read requirements | `.kiro/specs/<spec-name>/requirements.md` |
| Read design | `.kiro/specs/<spec-name>/design.md` |
| Track progress | `.kiro/specs/<spec-name>/tasks.md` |
| Spec implementation guide | `AGENTS.md` |

### Spec-Driven Development Workflow

**This project uses Kiro specs for ALL development work.** Understanding the spec-driven methodology is mandatory.

**Essential guides:**

1. **[AGENTS.md](AGENTS.md)** - Understanding Kiro specs (requirements → design → tasks)

   - How to read requirements.md (acceptance criteria)
   - How to read design.md (technical approach)
   - How to execute tasks.md (implementation steps)
   - How to update task progress

1. **[workflow.md](.kiro/steering/workflow.md)** - Development workflow

   - Spec-driven development cycle
   - Quality standards (80% coverage, all tests pass)
   - Branch strategy and PR process
   - AI-assisted development protocols

1. **[ai-agent-quick-reference.md](.kiro/steering/ai-agent-quick-reference.md)** - Quick reference

   - Golden rules (ONE TASK AT A TIME, NEVER PUSH TO MASTER)
   - Task implementation checklist
   - Essential commands
   - When to stop and ask for help

1. **[spec-maintenance.md](.kiro/steering/spec-maintenance.md)** - Keeping specs synchronized

   - Spec lifecycle and quality standards
   - When and how to update specs
   - Spec validation procedures

**All work follows: Read spec → Implement task → Test → Update tasks.md → Stop for review**

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
| Project conventions | `.kiro/steering/*.md` |
| Feature specs | `.kiro/specs/<spec-name>/` |
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
| Complete specification | `docs/archive/SPECIFICATION.md` (Historical) |
| POC summary | `docs/archive/POC-SUMMARY.md` (Historical) |
| Design rationale | `docs/design/01-initial-design.md` |
| Development setup | `docs/development/setup.md` |
| Testing guide | `docs/development/testing.md` |
| Tool management | `docs/development/tooling.md` |
| Quality standards | `docs/development/quality.md` |
| Reproduction guide | `docs/guides/reproduction-guide.md` |

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
1. ✅ Read `.kiro/specs/` for current feature specifications
1. ✅ Review [Development Setup](docs/development/setup.md) if needed

### While Working

1. ✅ Follow the immutability pattern (no mutations)
1. ✅ Add type annotations to all functions
1. ✅ Write docstrings with examples
1. ✅ Write tests as you develop (TDD preferred)
1. ✅ Run `uv run pytest` frequently

### Before Committing

1. ✅ Run `tox` to verify all checks pass
1. ✅ If you modified `docs/`: Run `tox -e docs-build`
1. ✅ Ensure tests cover new code
1. ✅ Use conventional commit messages
1. ✅ Let pre-commit hooks run (don't skip)

**For detailed workflow**, see [Quality Guide](docs/development/quality.md).

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

**Note to AI Assistants**: This project values code quality, testing, and documentation. Always run quality checks before suggesting changes are complete. When implementing new features, prioritize composability and immutability. Consult `.kiro/specs/` for current specifications before proposing major changes.
