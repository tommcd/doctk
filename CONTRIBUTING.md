# Contributing to doctk

Thank you for your interest in contributing to doctk! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites

- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- Git
- Bash shell (for setup scripts)

### Automated Setup (Recommended)

The fastest way to get started is using the automated setup script:

```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/doctk.git
cd doctk

# Run the automated setup
./scripts/setup-environment.sh
```

This script will:

1. Install uv if not present
1. Verify Python 3.12+ is available
1. Install external tools (shellcheck, shfmt, lychee, markdownlint, taplo, hadolint)
1. Install Python dependencies with `uv sync --all-groups`
1. Install tox globally
1. Set up pre-commit hooks

After setup completes, verify everything is working:

```bash
./scripts/check-environment.sh
```

### Manual Setup

If you prefer manual setup or need to troubleshoot:

1. Fork and clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/doctk.git
cd doctk
```

2. Install uv:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. Install dependencies:

```bash
uv sync --all-groups
```

4. Install external tools:

```bash
python3 scripts/setup-external-tools.py
```

5. Install pre-commit hooks:

```bash
uv run pre-commit install
```

6. Try the demo:

```bash
uv run doctk demo
```

## Project Structure

```
doctk/
├── src/doctk/         # Main source code
│   ├── core.py        # Document/Node abstractions
│   ├── operations.py  # Composable operations
│   ├── outliner.py    # Structure visualization
│   ├── cli.py         # Command-line interface
│   ├── parsers/       # Format readers
│   └── writers/       # Format writers
├── tests/             # Test suite
├── docs/              # Documentation
└── examples/          # Example documents
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Write code following the existing style
- Add tests for new functionality
- Update documentation as needed

### 3. Run Tests

```bash
# Run all tests
uv run pytest -v

# Run specific test categories
uv run pytest tests/unit/      # Unit tests
uv run pytest tests/e2e/       # End-to-end tests
uv run pytest tests/quality/   # Quality checks
uv run pytest tests/docs/      # Documentation tests

# Run with coverage
uv run pytest --cov=doctk --cov-report=html

# Run specific test
uv run pytest tests/test_basic.py::test_document_creation
```

### 4. Run Quality Checks

doctk uses tox to orchestrate quality checks:

```bash
# Run all quality checks
tox

# Run specific environments
tox -e ruff          # Python linting
tox -e shellcheck    # Shell script linting
tox -e shfmt         # Shell script formatting
tox -e taplo         # TOML formatting
tox -e docs          # Documentation checks (markdownlint, lychee)
tox -e pytest        # All tests

# Auto-fix issues
tox -e ruff-fix      # Fix Python formatting
tox -e shfmt-fix     # Fix shell script formatting
tox -e taplo-fix     # Fix TOML formatting
tox -e docs-fix      # Fix documentation formatting
```

### 5. Pre-commit Hooks

Pre-commit hooks run automatically on `git commit` to catch issues early:

```bash
# Hooks run automatically on commit
git commit -m "feat: add new feature"

# Run manually on all files
uv run pre-commit run --all-files

# Run specific hook
uv run pre-commit run ruff --all-files

# Update hook versions
uv run pre-commit autoupdate
```

The hooks check:

- Trailing whitespace and end-of-file newlines
- YAML syntax
- Shell scripts (shellcheck, shfmt)
- Python code (ruff)
- Markdown formatting (mdformat)
- TOML formatting (taplo)
- Tool plugin definitions

### 6. Type Check (future)

```bash
# Type check with ty
uvx ty check
```

### 7. Commit Changes

Follow conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

Types:

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Build/tooling changes

Example:

```bash
git commit -m "feat(operations): add lift/lower sibling operations"
```

### 8. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Code Quality Standards

doctk maintains high code quality through automated tooling and manual review.

### Style Guidelines

- Follow PEP 8 (enforced by ruff)
- Use type annotations for all functions
- Maximum line length: 100 characters
- Use descriptive variable names
- Write docstrings for all public APIs

### Automated Quality Checks

All code must pass these checks before merging:

1. **Python Linting** (ruff): No linting errors
1. **Python Formatting** (ruff): Consistent code style
1. **Shell Scripts** (shellcheck, shfmt): Google Shell Style Guide compliance
1. **TOML Files** (taplo): Consistent formatting
1. **Markdown** (markdownlint, mdformat): Consistent documentation style
1. **Links** (lychee): No broken links in documentation
1. **Tests**: All tests passing with adequate coverage
1. **Type Checking** (future): No type errors

Run all checks locally before pushing:

```bash
tox
```

### Documentation Standards

- Docstrings for all public functions/classes
- Include type hints
- Add usage examples for complex functions

Example:

```python
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
    ...
```

### Testing

- Write tests for new features
- Aim for >80% code coverage
- Use descriptive test names
- Test edge cases

Example:

```python
def test_promote_heading_at_minimum_level():
    """Test that promoting h1 stays at h1 (identity)."""
    node = Heading(level=1, text="Title")
    result = node.promote()
    assert result.level == 1
```

## Areas for Contribution

### High Priority

- [ ] Enhanced node types (Section, Table, Inline)
- [ ] Structure operations (lift, lower, nest, unnest)
- [ ] Path-based selection
- [ ] Additional format support (RST, HTML)

### Medium Priority

- [ ] Documentation improvements
- [ ] Example gallery
- [ ] Performance optimizations
- [ ] Error messages

### Good First Issues

Look for issues labeled `good-first-issue` on GitHub.

## Tox Environments

doctk uses tox to manage test and quality check environments. Here are the available environments:

### Quality Checks

- `tox -e check-environment` - Verify development environment setup
- `tox -e ruff` - Run Python linting
- `tox -e ruff-fix` - Auto-fix Python formatting issues
- `tox -e shellcheck` - Lint shell scripts
- `tox -e shfmt` - Check shell script formatting
- `tox -e shfmt-fix` - Auto-fix shell script formatting
- `tox -e taplo` - Check TOML formatting
- `tox -e taplo-fix` - Auto-fix TOML formatting
- `tox -e docs` - Run documentation checks (markdownlint, lychee)
- `tox -e docs-fix` - Auto-fix documentation formatting

### Testing

- `tox -e unit` - Run unit tests
- `tox -e e2e` - Run end-to-end tests
- `tox -e quality` - Run quality/meta tests
- `tox -e pytest` - Run all tests
- `tox -e pytest-all` - Run all tests with coverage

### Documentation

- `tox -e docs-build` - Build MkDocs documentation site
- `tox -e docs-serve` - Serve documentation locally at http://127.0.0.1:8000

### Combined

- `tox` - Run all environments (full quality check)

View all available environments:

```bash
python3 scripts/show-tox-commands.py
```

## Design Philosophy

When contributing, keep these principles in mind:

1. **Composability** - Build complex from simple
1. **Purity** - Immutable transformations
1. **Type Safety** - Use type annotations
1. **Readability** - Clear, self-documenting code
1. **Testing** - Comprehensive test coverage

See [docs/design/01-initial-design.md](docs/design/01-initial-design.md) for detailed design rationale.

## Getting Help

- **Questions**: Open a [Discussion](https://github.com/tommcd/doctk/discussions)
- **Bugs**: Open an [Issue](https://github.com/tommcd/doctk/issues)
- **Ideas**: Start a [Discussion](https://github.com/tommcd/doctk/discussions)

## Code of Conduct

Be respectful, inclusive, and constructive. We aim to maintain a welcoming community.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

______________________________________________________________________

Thank you for contributing to doctk! 🚀
