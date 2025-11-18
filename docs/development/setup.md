# Development Setup

This guide will help you set up a development environment for contributing to doctk.

## Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- Git
- Bash shell (for scripts)

## Quick Setup

The fastest way to get started is using the automated setup script:

```bash
# Clone the repository
git clone https://github.com/tommcd/doctk.git
cd doctk

# Run the setup script
./scripts/setup-environment.sh
```

This script will:

1. Install uv if not present
1. Verify Python 3.10+ is available
1. Install external tools (shellcheck, shfmt, lychee, etc.)
1. Install Python dependencies
1. Install tox globally
1. Set up pre-commit hooks

## Manual Setup

If you prefer to set up manually:

### 1. Install uv

```bash
# On Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Install Dependencies

```bash
# Install all dependency groups
uv sync --all-groups
```

This installs:

- Core dependencies (markdown-it-py, rich, etc.)
- Development tools (pytest, ruff, pre-commit)
- Documentation tools (mkdocs, mkdocs-material)

### 3. Install External Tools

External tools (shellcheck, shfmt, etc.) are managed via plugin definitions:

```bash
python3 scripts/setup-external-tools.py
```

These tools are installed to `~/.local/bin` and tracked in a registry.

### 4. Install Pre-commit Hooks

```bash
uv run pre-commit install
```

This sets up Git hooks that run quality checks before each commit.

## Verify Your Setup

Check that everything is configured correctly:

```bash
./scripts/check-environment.sh
```

This verifies:

- Python version
- uv installation
- External tools
- Git configuration
- Pre-commit hooks
- Python dependencies

If all checks pass, you're ready to develop!

## Development Workflow

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test categories
uv run pytest tests/unit/
uv run pytest tests/e2e/
uv run pytest tests/quality/

# Run with coverage
uv run pytest --cov=doctk --cov-report=html
```

### Code Quality

```bash
# Run all quality checks with tox
tox

# Run specific checks
tox -e ruff          # Python linting
tox -e shellcheck    # Shell script linting
tox -e docs          # Documentation checks

# Auto-fix issues
tox -e ruff-fix      # Fix Python formatting
tox -e shfmt-fix     # Fix shell script formatting
tox -e docs-fix      # Fix documentation formatting
```

### Pre-commit Hooks

Pre-commit hooks run automatically on `git commit`. To run manually:

```bash
# Run on all files
uv run pre-commit run --all-files

# Run specific hook
uv run pre-commit run ruff --all-files
```

### Building Documentation

```bash
# Build documentation site
tox -e docs-build

# Serve documentation locally
tox -e docs-serve
# Visit http://127.0.0.1:8000
```

## Project Structure

```
doctk/
├── src/doctk/           # Source code
│   ├── core.py          # Core abstractions
│   ├── operations.py    # Document operations
│   ├── cli.py           # CLI interface
│   └── tools/           # Tool management framework
├── tests/               # Test suite
│   ├── unit/            # Unit tests
│   ├── e2e/             # End-to-end tests
│   ├── quality/         # Quality/meta tests
│   └── docs/            # Documentation tests
├── scripts/             # Development scripts
│   ├── setup-environment.sh
│   ├── check-environment.sh
│   └── tools/           # Tool plugin definitions
├── docs/                # Documentation source
└── pyproject.toml       # Project configuration
```

## Tool Management

doctk uses a plugin-based system for managing external tools.

### Check Tool Status

```bash
python3 scripts/check-tools.py
```

### Install Tools

```bash
# Install all tools
python3 scripts/setup-external-tools.py

# Install specific tool
python3 scripts/setup-external-tools.py --tool shellcheck
```

### Uninstall Tools

```bash
# Uninstall all plugin-managed tools
python3 scripts/clean-tools.py

# Preview what would be removed
python3 scripts/clean-tools.py --dry-run
```

## Cleaning Up

To reset your environment:

```bash
# Remove all generated files
./scripts/clean-environment.sh

# Preview what would be removed
./scripts/clean-environment.sh --dry-run
```

This removes:

- Virtual environments (.venv, .tox)
- Build artifacts (dist, build, \*.egg-info)
- Caches (.pytest_cache, .ruff_cache, \_\_pycache\_\_)
- Test reports (reports/, .coverage)
- Documentation build (site/)

## Troubleshooting

### PATH Issues

Ensure `~/.local/bin` is on your PATH:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Tool Version Mismatches

If tools show version mismatches:

```bash
# Reinstall tools
python3 scripts/clean-tools.py
python3 scripts/setup-external-tools.py
```

### Pre-commit Hook Failures

If pre-commit hooks fail:

```bash
# Update hooks
uv run pre-commit autoupdate

# Run manually to see errors
uv run pre-commit run --all-files
```

### Test Failures

If tests fail after pulling changes:

```bash
# Sync dependencies
uv sync --all-groups

# Clear caches
rm -rf .pytest_cache .ruff_cache

# Run tests
uv run pytest
```

## Next Steps

- Read the [Testing Guide](testing.md) to learn about the test structure
- Check the README for project overview
- Review CONTRIBUTING for contribution guidelines
