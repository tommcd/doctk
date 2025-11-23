# Code Quality Checks

doctk maintains high code quality through comprehensive automated checks. This guide explains the quality tools, how to run them, and how to fix issues.

## Overview

Quality checks are organized into several categories:

1. **Python Code Quality**: Linting and formatting with ruff
1. **Shell Script Quality**: Linting with shellcheck, formatting with shfmt
1. **TOML Quality**: Formatting with taplo
1. **Documentation Quality**: Linting with markdownlint, link checking with lychee
1. **Configuration Consistency**: Meta tests for config drift
1. **Test Quality**: Comprehensive test coverage

## Running Quality Checks

### All Checks

Run all quality checks with tox:

```bash
tox
```

This runs all environments in sequence and reports pass/fail for each.

### Specific Checks

Run individual quality checks:

```bash
# Python
tox -e ruff

# Shell scripts
tox -e shellcheck
tox -e shfmt

# TOML
tox -e taplo

# Documentation
tox -e docs

# Tests
tox -e pytest
```

### Auto-fix

Many issues can be automatically fixed:

```bash
# Fix Python formatting
tox -e ruff-fix

# Fix shell script formatting
tox -e shfmt-fix

# Fix TOML formatting
tox -e taplo-fix

# Fix documentation formatting
tox -e docs-fix
```

## Python Code Quality

### Ruff

Ruff is an extremely fast Python linter and formatter that replaces multiple tools (flake8, isort, black, etc.).

#### Configuration

Configured in `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "UP",  # pyupgrade
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "SIM", # flake8-simplify
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

#### Running

```bash
# Check for issues
tox -e ruff

# Auto-fix issues
tox -e ruff-fix

# Or use ruff directly
uv run ruff check .
uv run ruff format .
```

#### Common Issues

- **E501**: Line too long (> 100 characters)
  - Fix: Break line into multiple lines
- **F401**: Unused import
  - Fix: Remove the import
- **I001**: Import block is un-sorted
  - Fix: Run `tox -e ruff-fix`
- **N802**: Function name should be lowercase
  - Fix: Rename function

## Shell Script Quality

### Shellcheck

Shellcheck is a static analysis tool for shell scripts that catches common errors.

#### Running

```bash
# Check all shell scripts
tox -e shellcheck

# Or use shellcheck directly
shellcheck scripts/*.sh
```

#### Common Issues

- **SC2086**: Double quote to prevent globbing
  - Fix: `"$variable"` instead of `$variable`
- **SC2155**: Declare and assign separately
  - Fix: Split into two lines
- **SC2164**: Use `cd ... || exit` in case cd fails
  - Fix: Add error handling

### Shfmt

Shfmt formats shell scripts according to Google Shell Style Guide.

#### Configuration

- Indent: 2 spaces
- Binary operators at start of line
- Redirect operators followed by space
- Keep column alignment

#### Running

```bash
# Check formatting
tox -e shfmt

# Auto-fix formatting
tox -e shfmt-fix

# Or use shfmt directly
shfmt -d scripts/*.sh
shfmt -w scripts/*.sh
```

## TOML Quality

### Taplo

Taplo formats TOML files consistently.

#### Running

```bash
# Check formatting
tox -e taplo

# Auto-fix formatting
tox -e taplo-fix

# Or use taplo directly
taplo format --check pyproject.toml
taplo format pyproject.toml
```

## Documentation Quality

### Markdownlint

Markdownlint enforces consistent Markdown style.

#### Configuration

Configured in `.markdownlint.yaml`:

```yaml
# Heading style
MD003:
  style: atx

# Unordered list style
MD004:
  style: dash

# Line length (disabled for flexibility)
MD013: false

# Code block style
MD046:
  style: fenced
```

#### Running

```bash
# Check all markdown files
tox -e docs

# Auto-fix issues
tox -e docs-fix

# Or use markdownlint directly
markdownlint-cli2 "**/*.md"
```

#### Common Issues

- **MD001**: Heading levels should increment by one
  - Fix: Don't skip heading levels (h1 → h3)
- **MD022**: Headings should be surrounded by blank lines
  - Fix: Add blank lines before/after headings
- **MD032**: Lists should be surrounded by blank lines
  - Fix: Add blank lines before/after lists

### MkDocs Site Build

**CRITICAL**: Always build the documentation site in strict mode before committing changes to `docs/`.

MkDocs strict mode catches broken links, missing files, and other documentation issues that would cause the GitHub Pages deployment to fail.

#### Running

```bash
# Build docs in strict mode (catches all issues)
tox -e docs-build

# Serve docs locally for preview
tox -e docs-serve
# Then open http://127.0.0.1:8000 in your browser
```

#### Why This Matters

- **Broken links fail the build**: Any reference to a non-existent file will cause a build failure
- **Excluded files**: Files in `exclude_docs` (like `archive/`, `design/`) cannot be linked from published docs
- **Missing nav entries**: Files not in the nav configuration won't be published
- **GitHub Pages deployment**: The CI/CD pipeline runs `mkdocs build --strict` and will fail if there are issues

#### Common Issues

- **Link to excluded file**: `Doc file 'index.md' contains a link to 'design/file.md' which is excluded`
  - Fix: Either remove the link or change it to reference the repository path
- **Broken relative link**: `contains a link '../file.md', but the target 'file.md' is not found`
  - Fix: Correct the relative path or move the file into the docs structure
- **Unrecognized link**: `contains an unrecognized relative link 'folder/'`
  - Fix: Link to a specific file like `folder/README.md` instead of the directory

#### Workflow

**Before committing any changes to `docs/`:**

```bash
# 1. Make your documentation changes
vim docs/index.md

# 2. Build in strict mode to check for issues
tox -e docs-build

# 3. If build succeeds, commit
git add docs/
git commit -m "docs: update documentation"

# 4. If build fails, fix the issues and repeat
```

### Mdformat

Mdformat auto-formats Markdown files.

#### Running

```bash
# Format all markdown files
tox -e docs-fix

# Or use mdformat directly
uv run mdformat docs/ README.md CONTRIBUTING.md
```

### Lychee

Lychee checks for broken links in documentation.

#### Configuration

Configured in `.lychee.toml`:

```toml
# Exclude patterns
exclude = [
    "localhost",
    "127.0.0.1",
    "mailto:",
]

# Retry failed requests
max_retries = 2
retry_wait_time = 2

# Timeout
timeout = 20
```

#### Running

```bash
# Check all links
tox -e docs

# Or use lychee directly
lychee docs/ README.md CONTRIBUTING.md
```

#### Common Issues

- **404 Not Found**: Link is broken
  - Fix: Update or remove the link
- **Timeout**: Server didn't respond
  - Fix: Check if URL is correct, may need to exclude
- **SSL Error**: Certificate issue
  - Fix: May need to exclude or update URL

## Configuration Consistency

### Meta Tests

Meta tests verify project configuration is consistent.

#### Location

`tests/quality/meta/test_config_consistency.py`

#### Tests

1. **Tool versions match**: Versions in `pyproject.toml` match `.pre-commit-config.yaml`
1. **Tox environments documented**: All tox environments have descriptions
1. **Dependency groups complete**: All required dependencies are listed
1. **External tools have plugins**: All tools in `pyproject.toml` have plugin files

#### Running

```bash
# Run meta tests
uv run pytest tests/quality/meta/ -v

# Or via tox
tox -e quality
```

#### Fixing Issues

If meta tests fail:

1. Check the error message for specific mismatch
1. Update the relevant configuration file
1. Run `python3 scripts/sync-precommit-versions.py` to sync versions
1. Re-run tests to verify

## Pre-commit Hooks

Pre-commit hooks run automatically on `git commit` to catch issues early.

### Installed Hooks

1. **File quality**: trailing whitespace, end-of-file, YAML syntax
1. **Shell scripts**: shellcheck, shfmt
1. **Python**: ruff
1. **Markdown**: mdformat
1. **TOML**: taplo
1. **Tool plugins**: validate plugin format

### Running Manually

```bash
# Run all hooks on all files
uv run pre-commit run --all-files

# Run specific hook
uv run pre-commit run ruff --all-files

# Run on staged files only
uv run pre-commit run
```

### Skipping Hooks

In rare cases, you may need to skip hooks:

```bash
# Skip all hooks
git commit --no-verify

# Skip specific hook (not recommended)
SKIP=ruff git commit
```

**Note**: Only skip hooks if absolutely necessary. CI will still run all checks.

### Updating Hooks

Update hook versions:

```bash
# Update to latest versions
uv run pre-commit autoupdate

# Sync versions from pyproject.toml
python3 scripts/sync-precommit-versions.py
```

## Test Quality

### Coverage

Aim for high test coverage:

```bash
# Run tests with coverage
uv run pytest --cov=doctk --cov-report=html

# View HTML report
open reports/coverage/html/index.html
```

### Test Categories

- **Unit tests**: Fast, isolated tests
- **E2E tests**: End-to-end CLI tests
- **Quality tests**: Meta tests for config
- **Docs tests**: Documentation quality tests

See [Testing Guide](testing.md) for details.

## CI/CD Integration

### GitHub Actions

All quality checks run in CI on every push and pull request.

#### Workflow

```yaml
name: Quality Checks

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install tools
        run: python3 scripts/setup-external-tools.py
      - name: Run quality checks
        run: tox
```

### Required Checks

Pull requests must pass:

1. All tox environments
1. All tests
1. All pre-commit hooks
1. Coverage threshold (if configured)

## Troubleshooting

### Ruff Errors

If ruff reports errors:

1. Try auto-fix: `tox -e ruff-fix`
1. If still failing, read error message carefully
1. Fix manually if auto-fix doesn't work
1. Check ruff documentation: https://docs.astral.sh/ruff/

### Shellcheck Errors

If shellcheck reports errors:

1. Read the error code (e.g., SC2086)
1. Check shellcheck wiki: https://www.shellcheck.net/wiki/SC2086
1. Fix the issue manually
1. Re-run: `tox -e shellcheck`

### Pre-commit Hook Failures

If pre-commit hooks fail:

1. Read the error message
1. Run the specific hook manually: `uv run pre-commit run <hook-name> --all-files`
1. Fix the issues
1. Try committing again

### Version Mismatches

If tool versions don't match:

1. Run: `python3 scripts/sync-precommit-versions.py`
1. Verify: `python3 scripts/check-tools.py`
1. Reinstall if needed: `python3 scripts/setup-external-tools.py`

## Best Practices

### Before Committing

1. Run tests: `uv run pytest`
1. Run quality checks: `tox`
1. **If you modified `docs/`**: Build docs in strict mode: `tox -e docs-build`
1. Fix any issues
1. Commit changes

### During Development

1. Run relevant checks frequently
1. Use auto-fix tools when available
1. Don't accumulate quality debt
1. Fix issues as they arise

### Code Review

1. Verify all CI checks pass
1. Review code quality manually
1. Check test coverage
1. Ensure documentation is updated

## Quality Metrics

### Current Status

- **Python**: 100% ruff compliant
- **Shell**: 100% shellcheck compliant
- **TOML**: 100% taplo compliant
- **Markdown**: 100% markdownlint compliant
- **Links**: 0 broken links
- **Tests**: All passing
- **Coverage**: >80% (target)

### Goals

- Maintain 100% compliance with all linters
- Increase test coverage to >90%
- Zero broken links in documentation
- All tox environments passing

## References

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Shellcheck Wiki](https://www.shellcheck.net/wiki/)
- [Markdownlint Rules](https://github.com/DavidAnson/markdownlint/blob/main/doc/Rules.md)
- [Google Shell Style Guide](https://google.github.io/styleguide/shellguide.html)
- [Development Setup](setup.md)
- [Testing Guide](testing.md)
- [Contributing Guide](https://github.com/tommcd/doctk/blob/main/CONTRIBUTING.md)
