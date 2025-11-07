# Contributing to doctk

Thank you for your interest in contributing to doctk! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) package manager

### Getting Started

1. Fork and clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/doctk.git
cd doctk
```

2. Install dependencies:
```bash
uv sync --all-extras
```

3. Run tests:
```bash
uv run pytest -v
```

4. Try the demo:
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

# Run with coverage
uv run pytest --cov=doctk

# Run specific test
uv run pytest tests/test_basic.py::test_document_creation
```

### 4. Format Code

```bash
# Format with ruff
uv run ruff format .

# Lint
uv run ruff check .
```

### 5. Type Check (future)

```bash
# Type check with ty
uvx ty check
```

### 6. Commit Changes

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

### 7. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Coding Standards

### Style

- Follow PEP 8
- Use type annotations
- Maximum line length: 100 characters
- Use descriptive variable names

### Documentation

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

## Design Philosophy

When contributing, keep these principles in mind:

1. **Composability** - Build complex from simple
2. **Purity** - Immutable transformations
3. **Type Safety** - Use type annotations
4. **Readability** - Clear, self-documenting code
5. **Testing** - Comprehensive test coverage

See [docs/design/01-initial-design.md](docs/design/01-initial-design.md) for detailed design rationale.

## Getting Help

- **Questions**: Open a [Discussion](https://github.com/tommcd/doctk/discussions)
- **Bugs**: Open an [Issue](https://github.com/tommcd/doctk/issues)
- **Ideas**: Start a [Discussion](https://github.com/tommcd/doctk/discussions)

## Code of Conduct

Be respectful, inclusive, and constructive. We aim to maintain a welcoming community.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to doctk! 🚀
