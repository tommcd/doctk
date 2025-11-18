# Development Scripts

This directory contains scripts for setting up and managing the development environment.

## Quick Start

```bash
# Full environment setup (recommended for first-time setup)
./scripts/setup-environment.sh

# Check if environment is ready
./scripts/check-environment.sh
```

## Scripts

### Environment Management

- **`setup-environment.sh`** - Complete development environment setup

  - Installs uv, Python, external tools, dependencies, tox, and pre-commit hooks
  - Run this first when setting up a new development environment
  - Usage: `./scripts/setup-environment.sh [--devcontainer] [--dry-run]`

- **`check-environment.sh`** - Verify environment is ready

  - Checks Python, uv, external tools, git, and dependencies
  - Run before starting development or running tests
  - Usage: `./scripts/check-environment.sh`

- **`clean-environment.sh`** - Clean all generated files

  - Removes .venv, .tox, build artifacts, caches
  - Useful for troubleshooting or starting fresh
  - Usage: `./scripts/clean-environment.sh`

### Tool Management

- **`setup-external-tools.py`** - Install external tools from plugins

  - Reads tool definitions from `scripts/tools/*.md`
  - Gets versions from `pyproject.toml [tool.external-tools]`
  - Installs to `~/.local/bin` (user-local, no sudo required)
  - Usage: `python3 scripts/setup-external-tools.py [--dry-run] [--tool NAME]`

- **`check-tools.py`** - Check external tool versions

  - Verifies installed tools match expected versions
  - Usage: `python3 scripts/check-tools.py`

- **`clean-tools.py`** - Uninstall plugin-managed tools

  - Only removes tools installed by the plugin system
  - Usage: `python3 scripts/clean-tools.py [--dry-run]`

### Utilities

- **`show-tox-commands.py`** - Display all tox environments

  - Shows available tox commands with descriptions
  - Usage: `python3 scripts/show-tox-commands.py`

- **`sync-precommit-versions.py`** - Sync tool versions to pre-commit config

  - Updates `.pre-commit-config.yaml` with versions from `pyproject.toml`
  - Usage: `python3 scripts/sync-precommit-versions.py`

- **`validate-plugins.py`** - Validate tool plugin Markdown files

  - Checks that tool definitions have required sections
  - Usage: `python3 scripts/validate-plugins.py`

## Tool Plugin System

The tool plugin system manages external development tools through Markdown-based definitions. This provides:

- **Single source of truth**: Tool versions in `pyproject.toml`
- **Declarative definitions**: Installation logic in readable Markdown
- **Registry tracking**: Knows which tools were installed by the system
- **Safe uninstallation**: Only removes plugin-managed tools

### Plugin File Format

Tool definitions live in `scripts/tools/*.md` as Markdown files with:

1. **Frontmatter (YAML)**: Metadata about the tool

   ```yaml
   ---
   name: shellcheck
   description: Shell script linting
   default_version: "0.11.0"
   ---
   ```

1. **Installation section**: Bash code block with installation commands

   ````markdown
   ## Installation
   ```bash
   VERSION="${VERSION:-0.11.0}"
   # Installation commands here
   ````

   ```

   ```

1. **Version Check section**: Bash code block to get installed version

   ````markdown
   ## Version Check
   ```bash
   shellcheck --version | grep "^version:" | awk '{print $2}'
   ````

   ```

   ```

1. **Uninstall section**: Bash code block to remove the tool

   ````markdown
   ## Uninstall
   ```bash
   rm -f ~/.local/bin/shellcheck
   ````

   ```

   ```

See `scripts/tools/TEMPLATE.md` for the complete plugin format.

### How It Works

1. **Installation**: `setup-external-tools.py` reads plugin files, extracts bash commands, and executes them
1. **Version Override**: Versions from `pyproject.toml [tool.external-tools]` override plugin defaults
1. **Registry**: Installed tools are tracked in `~/.local/share/doctk/tool-registry.json`
1. **Verification**: `check-tools.py` runs version check commands and compares with expected versions
1. **Cleanup**: `clean-tools.py` only removes tools listed in the registry

## Workflow

### First-Time Setup

```bash
# 1. Clone repository
git clone <repo-url>
cd <repo>

# 2. Run full setup
./scripts/setup-environment.sh

# 3. Verify
./scripts/check-environment.sh

# 4. Run tests
tox
```

### Daily Development

```bash
# Check environment before starting work
./scripts/check-environment.sh

# Run tests
tox

# Run specific test environment
tox -e unit          # Unit tests only
tox -e ruff          # Python linting
tox -e shellcheck    # Bash linting
tox -e docs          # Documentation checks

# Auto-fix formatting issues
tox -e ruff-fix      # Fix Python formatting
tox -e shfmt-fix     # Fix bash formatting
tox -e docs-fix      # Fix markdown formatting
```

#### Pre-commit Workflow

Pre-commit hooks run automatically on `git commit`:

```bash
# Make changes
git add .

# Commit (hooks run automatically)
git commit -m "Your message"

# If hooks fail, fix issues and try again
# Some hooks auto-fix (ruff, shfmt, mdformat)
git add .
git commit -m "Your message"
```

Run hooks manually:

```bash
# Run all hooks on all files
uv run pre-commit run --all-files

# Run specific hook
uv run pre-commit run ruff --all-files
uv run pre-commit run shellcheck --all-files
```

### Troubleshooting

#### Environment Issues

```bash
# Clean and start fresh
./scripts/clean-environment.sh
./scripts/setup-environment.sh

# Check what's wrong
./scripts/check-environment.sh

# Reinstall specific tool
python3 scripts/setup-external-tools.py --tool shellcheck
```

#### Common Issues

**Problem**: `~/.local/bin` not on PATH

```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="$HOME/.local/bin:$PATH"

# Reload shell
source ~/.bashrc  # or source ~/.zshrc
```

**Problem**: Tool version mismatch

```bash
# Check current versions
python3 scripts/check-tools.py --verbose

# Reinstall all tools
python3 scripts/clean-tools.py
python3 scripts/setup-external-tools.py
```

**Problem**: Pre-commit hooks not running

```bash
# Reinstall hooks
uv run pre-commit install

# Test manually
uv run pre-commit run --all-files
```

**Problem**: Python version too old

```bash
# Install Python 3.10+ via uv
uv python install 3.10

# Pin project to use it
uv python pin 3.10
```

**Problem**: Tox environment fails

```bash
# Clean tox cache
rm -rf .tox

# Reinstall dependencies
uv sync --all-groups

# Run specific environment
tox -e unit
```

## Design Philosophy

- **User-local installation**: Tools install to `~/.local/bin` (no sudo)
- **Version pinning**: Exact versions in `pyproject.toml` for reproducibility
- **Plugin-based**: Easy to add new tools by creating Markdown files
- **Idempotent**: Scripts can be run multiple times safely
- **Dry-run support**: Preview changes before applying

## External Tools

External tools are managed via the plugin system:

| Tool | Purpose | Config File |
|------|---------|-------------|
| shellcheck | Bash linting | `scripts/tools/shellcheck.md` |
| shfmt | Bash formatting | `scripts/tools/shfmt.md` |
| lychee | Link checking | `scripts/tools/lychee.md` |
| markdownlint-cli2 | Markdown linting | `scripts/tools/markdownlint-cli2.md` |
| taplo | TOML formatting | `scripts/tools/taplo.md` |
| hadolint | Dockerfile linting | `scripts/tools/hadolint.md` |

Versions are defined in `pyproject.toml`:

```toml
[tool.external-tools]
shellcheck = "0.11.0"
shfmt = "3.10.0"
lychee = "0.20.1"
markdownlint-cli2 = "0.18.1"
taplo = "0.9.3"
hadolint = "2.14.0"
```

## Adding a New Tool

1. Create `scripts/tools/newtool.md` using `TEMPLATE.md` as a guide
1. Add version to `pyproject.toml [tool.external-tools]`
1. Run `python3 scripts/validate-plugins.py` to check format
1. Run `python3 scripts/setup-external-tools.py --tool newtool` to test
1. Add to tox.ini if needed

## CI/CD Integration

```yaml
# .github/workflows/ci.yml
- name: Setup environment
  run: ./scripts/setup-environment.sh

- name: Check environment
  run: ./scripts/check-environment.sh

- name: Run tests
  run: tox
```
