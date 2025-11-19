# Tech Stack

## Language & Runtime

- **Python 3.12+** (required minimum version)
- Type annotations throughout codebase

## Package Management

- **uv** - Primary package manager (fast, modern Python tooling)
- **tox** - Test orchestration and environment management
- **tox-uv** - Integration between tox and uv

## Core Dependencies

- **markdown-it-py** - Markdown parsing
- **mdit-py-plugins** - Markdown parser extensions
- **rich** - Terminal formatting and visualization
- **pyyaml** - YAML configuration
- **pygls** - Language Server Protocol implementation

## Development Tools

### Python Quality

- **ruff** - Linting and formatting (replaces black, isort, flake8)
- **pytest** - Testing framework
- **pytest-cov** - Coverage reporting
- **mypy** - Type checking (gradual adoption)
- **vulture** - Dead code detection
- **pre-commit** - Git hooks for quality checks

### External Tools

Managed via `[tool.external-tools]` in pyproject.toml:

- **shellcheck** (0.11.0) - Shell script linting
- **shfmt** (3.10.0) - Shell script formatting (Google style)
- **lychee** (0.20.1) - Link checking
- **markdownlint-cli2** (0.18.1) - Markdown linting
- **taplo** (0.9.3) - TOML formatting
- **hadolint** (2.14.0) - Dockerfile linting

### Documentation

- **mkdocs** - Documentation site generator
- **mkdocs-material** - Material theme
- **mkdocstrings** - API documentation from docstrings
- **mdformat** - Markdown formatting

## Build System

- **hatchling** - PEP 517 build backend
- Uses PEP 735 `[dependency-groups]` for dev dependencies (not published to PyPI)

## Common Commands

### Setup

```bash
# Full environment setup (recommended)
./scripts/setup-environment.sh

# Verify environment
./scripts/check-environment.sh

# Install dependencies only
uv sync --all-groups
```

### Testing

```bash
# Run all tests (excludes slow tests by default)
uv run pytest

# Run specific test categories
uv run pytest tests/unit/      # Unit tests
uv run pytest tests/e2e/       # End-to-end tests
uv run pytest tests/quality/   # Quality/meta tests
uv run pytest tests/docs/      # Documentation tests

# Run with coverage
uv run pytest --cov=doctk --cov-report=html

# Run specific test
uv run pytest tests/unit/test_nested_lists.py -v
```

### Quality Checks

```bash
# Run all quality checks
tox

# Run specific checks
tox -e ruff          # Python linting
tox -e shellcheck    # Shell script linting
tox -e taplo         # TOML formatting
tox -e docs          # Documentation checks

# Auto-fix issues
tox -e ruff-fix      # Fix Python formatting
tox -e shfmt-fix     # Fix shell script formatting
tox -e taplo-fix     # Fix TOML formatting
tox -e docs-fix      # Fix markdown formatting
```

### Documentation

```bash
# Build documentation site
tox -e docs-build

# Serve locally at http://127.0.0.1:8000
tox -e docs-serve

# Deploy to GitHub Pages
tox -e docs-deploy
```

### CLI Usage

```bash
# View document outline
doctk outline README.md --headings-only

# Run interactive demo
doctk demo

# Show help
doctk help
```

## Code Style

- **Line length**: 100 characters
- **Quote style**: Double quotes
- **Indentation**: 4 spaces (Python), 2 spaces (shell scripts)
- **Shell style**: Google Shell Style Guide
- **Import sorting**: Automatic via ruff
- **Type hints**: Required for all public functions

## Testing Strategy

- **Unit tests**: Fast, isolated tests in `tests/unit/`
- **E2E tests**: CLI integration tests in `tests/e2e/`
- **Quality tests**: Meta tests for config consistency in `tests/quality/`
- **Docs tests**: Spec validation, link checking in `tests/docs/`
- **Markers**: `@pytest.mark.slow`, `@pytest.mark.e2e`, `@pytest.mark.unit`, `@pytest.mark.quality`, `@pytest.mark.docs`
- **Coverage**: Configured in pyproject.toml, reports to `reports/coverage/`
