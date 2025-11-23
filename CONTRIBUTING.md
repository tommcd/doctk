# Contributing to doctk

Thank you for your interest in contributing to doctk! This guide will help you get started quickly.

## Quick Start

### Prerequisites

- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- Git

### Setup in 3 Steps

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/doctk.git
cd doctk

# 2. Run automated setup
./scripts/setup-environment.sh

# 3. Verify everything works
./scripts/check-environment.sh
```

**For detailed setup instructions**, see [Development Setup Guide](docs/development/setup.md).

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Write code following project conventions (see [Project Structure](.kiro/steering/structure.md))
- Add tests for new functionality
- Update documentation as needed

### 3. Test Your Changes

```bash
# Run tests
uv run pytest

# Run quality checks
tox
```

**For comprehensive testing guide**, see [Testing Guide](docs/development/testing.md).

### 4. Commit and Push

Follow conventional commit format:

```bash
git commit -m "feat(scope): description"
git push origin feature/your-feature-name
```

**Commit types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### 5. Create Pull Request

Open a PR on GitHub. All CI checks must pass before merging.

## Key Resources

### Development Guides

- **[Development Setup](docs/development/setup.md)** - Complete setup instructions
- **[Testing Guide](docs/development/testing.md)** - Running and writing tests
- **[Quality Standards](docs/development/quality.md)** - Code quality and checks
- **[Tooling Guide](docs/development/tooling.md)** - External tools management

### Project Structure

- **[Project Structure](.kiro/steering/structure.md)** - Codebase organization
- **[Tech Stack](.kiro/steering/tech.md)** - Technologies and commands
- **[Product Overview](.kiro/steering/product.md)** - Philosophy and vision

### API Documentation

- **[Core Integration API](docs/api/core-integration.md)** - Document operations
- **[DSL API](docs/api/dsl.md)** - Domain-Specific Language
- **[LSP API](docs/api/lsp.md)** - Language Server Protocol

## Quick Reference

### Common Commands

```bash
# Testing
uv run pytest                    # Run all tests
uv run pytest tests/unit/        # Unit tests only
uv run pytest --cov=doctk        # With coverage

# Quality Checks
tox                              # Run all checks
tox -e ruff                      # Python linting
tox -e ruff-fix                  # Auto-fix formatting
tox -e docs-build                # Build documentation

# Documentation
tox -e docs-serve                # Serve docs locally
```

**For complete command reference**, see [Tech Stack](.kiro/steering/tech.md).

### Pre-commit Hooks

Hooks run automatically on commit to catch issues early:

```bash
git commit -m "feat: add feature"  # Hooks run automatically
uv run pre-commit run --all-files  # Run manually
```

## Code Quality Standards

All code must pass:

- ✅ Python linting (ruff)
- ✅ Shell script linting (shellcheck)
- ✅ Documentation checks (markdownlint, lychee)
- ✅ All tests passing
- ✅ Type annotations on public APIs

**For detailed quality standards**, see [Quality Guide](docs/development/quality.md).

## Design Philosophy

When contributing, keep these principles in mind:

- **Composable** - Build complex from simple primitives
- **Pure** - Immutable transformations, no mutations
- **Type-safe** - Well-typed operations
- **Readable** - Self-documenting code
- **Tested** - Comprehensive test coverage

**For design rationale**, see [Initial Design](docs/design/01-initial-design.md).

## Areas for Contribution

### High Priority

- Enhanced node types (Section, Table, Inline)
- Structure operations (lift, lower, nest, unnest)
- Path-based selection
- Additional format support (RST, HTML)

### Good First Issues

Look for issues labeled `good-first-issue` on GitHub.

## Getting Help

- **Questions**: Open a [Discussion](https://github.com/tommcd/doctk/discussions)
- **Bugs**: Open an [Issue](https://github.com/tommcd/doctk/issues)
- **Ideas**: Start a [Discussion](https://github.com/tommcd/doctk/discussions)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

______________________________________________________________________

**Thank you for contributing to doctk!** 🚀

For detailed guides, see the [docs/development/](docs/development/) directory.
