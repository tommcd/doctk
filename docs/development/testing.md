# Testing Guide

This guide explains the testing infrastructure and how to write tests for doctk.

## Test Structure

doctk uses a multi-tier test structure to organize different types of tests:

```
tests/
├── unit/              # Fast, isolated unit tests
├── e2e/               # End-to-end CLI integration tests
├── quality/           # Meta tests (config consistency, code quality)
│   ├── meta/          # Configuration consistency tests
│   └── shell/         # Shell script quality tests
├── docs/              # Documentation quality tests
└── test_basic.py      # Legacy tests (to be migrated)
```

## Test Categories

### Unit Tests

**Location**: `tests/unit/`

**Purpose**: Test individual functions and classes in isolation

**Characteristics**:

- Fast execution (< 1 second per test)
- No external dependencies
- Mock file system and network calls
- Focus on single units of functionality

**Example**:

```python
# tests/unit/test_document.py
from doctk import Document

def test_document_from_markdown():
    """Test creating a document from markdown string."""
    markdown = "# Hello\n\nWorld"
    doc = Document.from_markdown(markdown)
    assert len(doc.nodes) == 2
    assert doc.nodes[0].type == "heading"
```

### End-to-End Tests

**Location**: `tests/e2e/`

**Purpose**: Test complete workflows through the CLI

**Characteristics**:

- Test real CLI commands
- Use temporary files
- Verify output and exit codes
- May be slower than unit tests

**Example**:

```python
# tests/e2e/test_cli.py
import subprocess
import tempfile
from pathlib import Path

def test_outline_command():
    """Test the outline CLI command."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("# Title\n\n## Section\n")
        f.flush()

        result = subprocess.run(
            ["doctk", "outline", f.name],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "Title" in result.stdout
        assert "Section" in result.stdout
```

### Quality Tests

**Location**: `tests/quality/`

**Purpose**: Verify project configuration and code quality

**Characteristics**:

- Meta tests (tests about the project itself)
- Configuration consistency checks
- Code quality verification
- Shell script linting

**Example**:

```python
# tests/quality/meta/test_config_consistency.py
import tomli
from pathlib import Path

def test_tool_versions_match():
    """Verify tool versions match between pyproject.toml and pre-commit."""
    with open("pyproject.toml", "rb") as f:
        pyproject = tomli.load(f)

    external_tools = pyproject["tool"]["external-tools"]

    # Verify versions are consistent
    assert "shellcheck" in external_tools
    assert external_tools["shellcheck"] == "0.11.0"
```

### Documentation Tests

**Location**: `tests/docs/`

**Purpose**: Verify documentation quality and completeness

**Characteristics**:

- Check for required sections
- Verify links are valid
- Ensure markdown is well-formatted
- Test code examples

**Example**:

```python
# tests/docs/test_documentation_quality.py
from pathlib import Path

def test_readme_has_required_sections():
    """Verify README has all required sections."""
    readme = Path("README.md").read_text()

    required_sections = [
        "# doctk",
        "## Installation",
        "## Usage",
        "## Contributing",
    ]

    for section in required_sections:
        assert section in readme, f"Missing section: {section}"
```

## Running Tests

### Run All Tests

```bash
# Using pytest directly
uv run pytest

# Using tox (recommended)
tox -e pytest
```

### Run Specific Categories

```bash
# Unit tests only
uv run pytest tests/unit/

# E2E tests only
uv run pytest tests/e2e/

# Quality tests only
uv run pytest tests/quality/

# Documentation tests only
uv run pytest tests/docs/
```

### Run with Markers

```bash
# Run only unit tests (using marker)
uv run pytest -m unit

# Run only e2e tests
uv run pytest -m e2e

# Run all except slow tests
uv run pytest -m "not slow"
```

### Run Specific Test File

```bash
uv run pytest tests/unit/test_document.py -v
```

### Run Specific Test Function

```bash
uv run pytest tests/unit/test_document.py::test_document_from_markdown -v
```

## Coverage

### Generate Coverage Report

```bash
# Run tests with coverage
uv run pytest --cov=doctk --cov-report=html

# View HTML report
open reports/coverage/html/index.html
```

### Coverage Configuration

Coverage is configured in `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["doctk"]
branch = true
omit = ["*/tests/*"]

[tool.coverage.report]
show_missing = true
precision = 2
fail_under = 0  # Set to desired minimum coverage
```

## Writing Tests

### Test Naming

- Test files: `test_*.py`
- Test functions: `test_*`
- Test classes: `Test*`

### Test Structure

Follow the Arrange-Act-Assert pattern:

```python
def test_example():
    # Arrange: Set up test data
    doc = Document.from_markdown("# Hello")

    # Act: Perform the operation
    result = doc | select(heading)

    # Assert: Verify the result
    assert len(result.nodes) == 1
    assert result.nodes[0].content == "Hello"
```

### Using Fixtures

```python
import pytest
from doctk import Document

@pytest.fixture
def sample_doc():
    """Fixture providing a sample document."""
    return Document.from_markdown("""
# Title

## Section 1

Content here.

## Section 2

More content.
""")

def test_with_fixture(sample_doc):
    """Test using the fixture."""
    headings = sample_doc | select(heading)
    assert len(headings.nodes) == 3
```

### Parametrized Tests

```python
import pytest

@pytest.mark.parametrize("level,expected", [
    (1, "Title"),
    (2, "Section 1"),
    (2, "Section 2"),
])
def test_heading_levels(sample_doc, level, expected):
    """Test heading selection by level."""
    headings = sample_doc | select(heading) | where(level=level)
    assert any(h.content == expected for h in headings.nodes)
```

### Mocking

```python
from unittest.mock import patch, mock_open

def test_file_reading():
    """Test reading from file with mock."""
    mock_content = "# Test\n\nContent"

    with patch("builtins.open", mock_open(read_data=mock_content)):
        doc = Document.from_file("fake.md")
        assert len(doc.nodes) == 2
```

## Test Markers

Tests can be marked for selective execution:

```python
import pytest

@pytest.mark.unit
def test_fast_unit():
    """Fast unit test."""
    pass

@pytest.mark.e2e
def test_cli_integration():
    """End-to-end CLI test."""
    pass

@pytest.mark.slow
def test_expensive_operation():
    """Slow test that's skipped by default."""
    pass
```

## Continuous Integration

Tests run automatically on:

- Every push to main
- Every pull request
- Scheduled nightly builds

CI configuration is in `.github/workflows/tests.yml`.

## Best Practices

### Do

- Write tests for new features
- Keep tests fast and focused
- Use descriptive test names
- Test edge cases and error conditions
- Mock external dependencies
- Use fixtures for common setup

### Don't

- Test implementation details
- Write tests that depend on each other
- Use real files or network calls in unit tests
- Ignore failing tests
- Write tests without assertions

## Debugging Tests

### Run with Verbose Output

```bash
uv run pytest -v
```

### Show Print Statements

```bash
uv run pytest -s
```

### Drop into Debugger on Failure

```bash
uv run pytest --pdb
```

### Run Last Failed Tests

```bash
uv run pytest --lf
```

## Next Steps

- Read the [Development Setup](setup.md) guide
- Check the README for project overview
- Review CONTRIBUTING for contribution guidelines
