# Design Document: Integrate Python Project Template Tooling

## Overview

This design document outlines the technical approach for integrating comprehensive development tooling from the python-project-template into doctk. The integration brings a plugin-based tool management system, comprehensive test infrastructure, documentation tooling, and development automation scripts.

The core design principle is **self-contained reproducibility**: all tooling should be version-pinned, automatically installable, and work consistently across development environments without requiring manual configuration.

## Architecture

### High-Level Structure

```
doctk/
├── src/doctk/
│   ├── tools/              # NEW: Inlined tool management framework
│   │   ├── __init__.py
│   │   ├── manager.py      # ToolManager class
│   │   ├── plugin.py       # ToolPlugin class
│   │   └── registry.py     # ToolRegistry class
│   ├── core.py
│   ├── operations.py
│   └── ...
├── scripts/                # NEW: Development automation scripts
│   ├── README.md
│   ├── setup-environment.sh
│   ├── check-environment.sh
│   ├── clean-environment.sh
│   ├── setup-external-tools.py
│   ├── check-tools.py
│   ├── clean-tools.py
│   ├── show-tox-commands.py
│   ├── sync-precommit-versions.py
│   ├── validate-plugins.py
│   └── tools/              # Tool plugin definitions
│       ├── TEMPLATE.md
│       ├── shellcheck.md
│       ├── shfmt.md
│       ├── lychee.md
│       ├── markdownlint-cli2.md
│       ├── taplo.md
│       └── hadolint.md
├── tests/
│   ├── test_basic.py       # EXISTING: Keep for now
│   ├── unit/               # NEW: Unit tests
│   │   └── __init__.py
│   ├── e2e/                # NEW: End-to-end tests
│   │   └── __init__.py
│   ├── quality/            # NEW: Quality/meta tests
│   │   ├── __init__.py
│   │   ├── meta/
│   │   │   ├── __init__.py
│   │   │   └── test_config_consistency.py
│   │   └── shell/
│   │       ├── __init__.py
│   │       └── test_shell_quality.py
│   └── docs/               # NEW: Documentation tests
│       ├── __init__.py
│       └── test_documentation_quality.py
├── docs/                   # EXISTING: Enhanced with MkDocs
│   ├── index.md            # NEW: MkDocs homepage
│   ├── getting-started.md  # NEW
│   ├── user-guide/         # NEW
│   ├── development/        # NEW
│   └── api/                # NEW
├── mkdocs.yml              # NEW: MkDocs configuration
├── pyproject.toml          # UPDATED: Already enhanced
├── tox.ini                 # NEW: Already created
├── .pre-commit-config.yaml # NEW: Already created
├── .lychee.toml            # NEW: Already created
├── .markdownlint.yaml      # NEW: Already created
└── .gitignore              # UPDATED: Already enhanced
```

## Components

### 1. Tool Management Framework (Inlined from sstdf-python-standards)

#### 1.1 ToolPlugin Class

**Purpose**: Represents a single external tool with installation/verification logic

**Location**: `src/doctk/tools/plugin.py`

**Key Methods**:

- `get_version_spec()` - Get expected version from pyproject.toml or Markdown frontmatter
- `get_version()` - Get currently installed version
- `install(version, dry_run)` - Install tool to ~/.local/bin
- `uninstall(dry_run)` - Remove tool if plugin-managed
- `is_plugin_managed()` - Check if tool is tracked in registry

**Data Flow**:

```
Markdown Plugin File (.md)
    ↓
Parse frontmatter (YAML) → Extract metadata (name, default_version)
    ↓
Parse code blocks → Extract bash commands (install, check, uninstall)
    ↓
Check pyproject.toml [tool.external-tools] → Override version if present
    ↓
Execute bash commands → Install/check/uninstall tool
    ↓
Update registry → Track installation in ~/.local/share/doctk/tool-registry.json
```

**Markdown Plugin Format**:

````markdown
---
name: shellcheck
description: Shell script linting
default_version: "0.11.0"
---

# shellcheck

Shell script static analysis tool.

## Installation

```bash
# Install shellcheck
VERSION="${VERSION:-0.11.0}"
wget -qO- "https://github.com/koalaman/shellcheck/releases/download/v${VERSION}/shellcheck-v${VERSION}.linux.x86_64.tar.xz" \
  | tar -xJv --strip-components=1 -C ~/.local/bin shellcheck-v${VERSION}/shellcheck
chmod +x ~/.local/bin/shellcheck
````

## Version Check

```bash
shellcheck --version | grep "^version:" | awk '{print $2}'
```

## Uninstall

```bash
rm -f ~/.local/bin/shellcheck
```

````

#### 1.2 ToolManager Class

**Purpose**: Orchestrates operations across all tool plugins

**Location**: `src/doctk/tools/manager.py`

**Key Methods**:
- `install_all(dry_run)` - Install all tools from plugins
- `check_all()` - Check status of all tools
- `uninstall_all(dry_run)` - Uninstall all plugin-managed tools
- `get_tool(name)` - Get specific tool plugin

**Responsibilities**:
1. Load version overrides from pyproject.toml
2. Discover all .md files in scripts/tools/
3. Create ToolPlugin instances
4. Coordinate installation/checking/uninstallation
5. Report progress and errors

#### 1.3 ToolRegistry Class

**Purpose**: Track which tools are managed by the plugin system

**Location**: `src/doctk/tools/registry.py`

**Registry File**: `~/.local/share/doctk/tool-registry.json`

**Format**:
```json
{
  "shellcheck": {
    "version": "0.11.0",
    "installed_at": "2024-11-17T12:34:56Z",
    "location": "/home/user/.local/bin/shellcheck"
  },
  "shfmt": {
    "version": "3.10.0",
    "installed_at": "2024-11-17T12:35:10Z",
    "location": "/home/user/.local/bin/shfmt"
  }
}
````

**Operations**:

- `add(tool_name, version, location)` - Record tool installation
- `remove(tool_name)` - Remove tool from registry
- `is_managed(tool_name)` - Check if tool is tracked
- `get_info(tool_name)` - Get tool metadata

### 2. Development Scripts

#### 2.1 setup-environment.sh

**Purpose**: One-command setup for complete development environment

**Steps**:

1. Check if uv is installed, install if missing
1. Verify ~/.local/bin is on PATH
1. Install Python 3.10+ via uv (if not present)
1. Pin Python version with `uv python pin`
1. Install external tools via `python3 scripts/setup-external-tools.py`
1. Run `uv sync --all-groups` to install Python dependencies
1. Install tox globally via `uv tool install tox --with tox-uv`
1. Install pre-commit hooks via `uv run pre-commit install`
1. Verify installation with summary

**Modes**:

- `--devcontainer`: Adjust paths for devcontainer environment
- `--dry-run`: Show commands without executing

**Error Handling**:

- Continue on non-critical failures
- Display warnings for PATH issues
- Exit with code 1 on critical failures

#### 2.2 check-environment.sh

**Purpose**: Verify environment is ready for development

**Checks**:

1. Python 3.10+ installed
1. uv installed
1. External tools installed with correct versions (delegates to check-tools.py)
1. git installed
1. pre-commit hooks installed
1. Python dependencies installed (pre-commit, tox, mdformat available)

**Output**:

- Green ✓ for passing checks
- Red ✗ for failing checks
- Yellow ⚠ for warnings
- Exit code 0 if ready, 1 if not ready

#### 2.3 clean-environment.sh

**Purpose**: Remove all generated files and caches

**Removes**:

- `.venv/` - Virtual environment
- `.tox/` - Tox environments
- `dist/`, `build/`, `*.egg-info/` - Build artifacts
- `.pytest_cache/`, `.ruff_cache/`, `__pycache__/` - Caches
- `reports/`, `.coverage`, `htmlcov/` - Test reports
- `site/` - MkDocs output

**Safety**:

- Only removes known generated directories
- Does not remove source code or configuration
- Displays what was removed

#### 2.4 setup-external-tools.py

**Purpose**: Install external tools from plugin definitions

**Usage**:

```bash
python3 scripts/setup-external-tools.py              # Install all
python3 scripts/setup-external-tools.py --dry-run    # Preview
python3 scripts/setup-external-tools.py --tool shellcheck  # Install one
```

**Logic**:

1. Import ToolManager from doctk.tools
1. Initialize manager with scripts/tools/ directory
1. Load version overrides from pyproject.toml
1. Install requested tools
1. Report success/failure

#### 2.5 check-tools.py

**Purpose**: Verify external tool versions match expectations

**Logic**:

1. Import ToolManager from doctk.tools
1. Check all tools
1. Report installed vs expected versions
1. Distinguish between plugin-managed and system-installed tools
1. Exit with code 0 if all match, 1 if any mismatch

#### 2.6 clean-tools.py

**Purpose**: Uninstall plugin-managed tools

**Logic**:

1. Import ToolManager from doctk.tools
1. Check which tools are plugin-managed
1. Uninstall only plugin-managed tools
1. Skip system-installed tools
1. Report what was removed

### 3. Test Infrastructure

#### 3.1 Test Directory Structure

**Rationale**: Separate test types for targeted execution and clarity

**Categories**:

- `tests/unit/` - Fast, isolated unit tests
- `tests/e2e/` - End-to-end CLI integration tests
- `tests/quality/` - Meta tests (config consistency, shell quality)
- `tests/docs/` - Documentation quality tests
- `tests/` - Legacy tests (keep test_basic.py for now)

**Pytest Configuration**:

```toml
[tool.pytest.ini_options]
testpaths = ["tests/unit", "tests/e2e", "tests/quality", "tests/docs", "tests"]
markers = [
  "unit: fast, isolated unit tests",
  "e2e: end-to-end integration tests",
  "quality: meta tests for config consistency",
  "docs: documentation quality tests",
  "slow: slow tests (deselected by default)",
]
```

#### 3.2 Quality Meta Tests

**File**: `tests/quality/meta/test_config_consistency.py`

**Tests**:

1. `test_tool_versions_match_precommit()` - Verify versions in pyproject.toml match .pre-commit-config.yaml
1. `test_tox_environments_documented()` - Verify all tox environments have descriptions
1. `test_dependency_groups_complete()` - Verify all required dependencies are in groups
1. `test_external_tools_have_plugins()` - Verify all tools in pyproject.toml have plugin files

**Purpose**: Catch configuration drift early

#### 3.3 Shell Quality Tests

**File**: `tests/quality/shell/test_shell_quality.py`

**Tests**:

1. `test_shell_scripts_pass_shellcheck()` - Run shellcheck on all .sh files
1. `test_shell_scripts_formatted()` - Verify shfmt formatting
1. `test_shell_scripts_have_shebangs()` - Verify #!/bin/bash present
1. `test_shell_scripts_executable()` - Verify chmod +x

**Purpose**: Enforce Google Shell Style Guide

#### 3.4 Documentation Quality Tests

**File**: `tests/docs/test_documentation_quality.py`

**Tests**:

1. `test_readme_has_required_sections()` - Verify README has Features, Installation, Usage, Development
1. `test_important_files_are_linked()` - Verify important files are markdown links (not just text)
1. `test_markdown_passes_linter()` - Run markdownlint on all .md files
1. `test_links_are_valid()` - Run lychee link checker

**Purpose**: Maintain documentation quality

### 4. MkDocs Documentation Site

#### 4.1 Configuration

**File**: `mkdocs.yml`

```yaml
site_name: doctk
site_description: A composable toolkit for structured document manipulation
site_url: https://tommcd.github.io/doctk/
repo_url: https://github.com/tommcd/doctk
repo_name: tommcd/doctk

theme:
  name: material
  palette:
    - scheme: default
      primary: indigo
      accent: indigo
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.expand
    - search.suggest
    - search.highlight
    - content.code.copy

nav:
  - Home: index.md
  - Getting Started:
      - Installation: getting-started/installation.md
      - Quick Start: getting-started/quick-start.md
  - User Guide:
      - Core Concepts: user-guide/concepts.md
      - Operations: user-guide/operations.md
      - Selection: user-guide/selection.md
      - Examples: user-guide/examples.md
  - Development:
      - Setup: development/setup.md
      - Testing: development/testing.md
      - Contributing: development/contributing.md
      - Architecture: development/architecture.md
  - API Reference:
      - Document: api/document.md
      - Operations: api/operations.md
      - Nodes: api/nodes.md

plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          paths: [src]

markdown_extensions:
  - pymdownx.highlight
  - pymdownx.superfences
  - pymdownx.inlinehilite
  - pymdownx.snippets
  - admonition
  - pymdownx.details
  - pymdownx.tabbed:
      alternate_style: true
```

#### 4.2 Documentation Structure

**docs/index.md** - Homepage with project overview
**docs/getting-started/** - Installation and quick start guides
**docs/user-guide/** - Comprehensive user documentation
**docs/development/** - Developer documentation
**docs/api/** - API reference (auto-generated from docstrings)

### 5. Configuration Files

#### 5.1 pyproject.toml (Already Updated)

**Key Sections**:

- `[tool.external-tools]` - Version pins for external tools
- `[dependency-groups]` - Dev and docs dependencies
- `[tool.pytest.ini_options]` - Pytest configuration
- `[tool.coverage.*]` - Coverage configuration
- `[tool.ruff.*]` - Ruff linting/formatting rules

#### 5.2 tox.ini (Already Created)

**Key Environments**:

- `check-environment` - Verify setup
- `ruff` / `ruff-fix` - Python linting/formatting
- `shellcheck` / `shfmt` - Bash quality
- `taplo` / `taplo-fix` - TOML formatting
- `docs` / `docs-fix` - Documentation quality
- `unit` / `e2e` / `quality` - Test suites
- `pytest` / `pytest-all` - Combined test runs
- `docs-build` / `docs-serve` - MkDocs operations

#### 5.3 .pre-commit-config.yaml (Already Created)

**Hooks**:

- File quality (trailing whitespace, end-of-file, YAML syntax)
- Bash quality (shellcheck, shfmt)
- Python quality (ruff)
- Markdown formatting (mdformat)
- TOML formatting (taplo)
- Tool plugin validation

#### 5.4 .lychee.toml (Already Created)

**Configuration**:

- Exclude localhost and mailto links
- Exclude test data and build output
- Retry failed requests 2 times
- 20 second timeout

#### 5.5 .markdownlint.yaml (Already Created)

**Rules**:

- Enforce fenced code blocks
- Allow flexible line length (disabled MD013)
- Allow duplicate headings in different sections
- Require asterisk style for emphasis/strong

## Data Models

### Tool Plugin Metadata

```python
@dataclass
class ToolMetadata:
    name: str
    description: str
    default_version: str
    homepage: str | None = None
    docs_url: str | None = None
```

### Tool Registry Entry

```python
@dataclass
class RegistryEntry:
    version: str
    installed_at: datetime
    location: Path
    checksum: str | None = None  # Future: verify integrity
```

### Plugin Code Blocks

```python
@dataclass
class PluginCodeBlocks:
    install: str  # Bash script to install
    check: str    # Bash script to get version
    uninstall: str  # Bash script to uninstall
```

## Error Handling

### Tool Installation Failures

**Strategy**: Continue with other tools, report failures at end

**Handling**:

1. Catch exceptions during installation
1. Log error with tool name and exception message
1. Continue to next tool
1. Report summary: "Installed 5/6 tools (shellcheck failed)"

### Missing Dependencies

**Strategy**: Fail fast with helpful error message

**Handling**:

1. Check for uv before running any Python commands
1. Check for Python 3.10+ before installing dependencies
1. Display installation instructions if missing
1. Exit with code 1

### Registry Corruption

**Strategy**: Graceful degradation

**Handling**:

1. If registry file is corrupted, treat all tools as unmanaged
1. Log warning about corruption
1. Allow manual cleanup
1. Provide command to rebuild registry

### Version Mismatches

**Strategy**: Warn but don't fail

**Handling**:

1. Display warning if installed version != expected version
1. Show both versions
1. Suggest reinstallation command
1. Continue with other checks

## Testing Strategy

### Unit Tests

**Scope**: Test individual functions and classes in isolation

**Examples**:

- Test ToolPlugin.parse_frontmatter()
- Test ToolRegistry.add() / remove()
- Test version comparison logic

**Mocking**: Mock file system, subprocess calls, network requests

### Integration Tests

**Scope**: Test tool management end-to-end

**Examples**:

- Install tool via plugin → verify in registry → uninstall → verify removed
- Check tool version → compare with expected
- Load version overrides from pyproject.toml

**Environment**: Use temporary directories and test fixtures

### Quality Tests

**Scope**: Verify project configuration and code quality

**Examples**:

- Config consistency tests
- Shell script quality tests
- Documentation quality tests

**Execution**: Run via tox quality environment

### Documentation Tests

**Scope**: Verify documentation is complete and accurate

**Examples**:

- README has required sections
- Links are valid
- Markdown is well-formatted

**Execution**: Run via tox docs environment

## Performance Considerations

### Tool Installation

**Optimization**: Parallel installation (future enhancement)

**Current**: Sequential installation
**Future**: Use asyncio or multiprocessing to install tools in parallel

### Version Checking

**Optimization**: Cache version checks

**Current**: Run version check command each time
**Future**: Cache results for 5 minutes to speed up repeated checks

### Registry Operations

**Optimization**: Lazy loading

**Current**: Load registry on every operation
**Future**: Load once and keep in memory

## Security Considerations

### Tool Installation

**Risk**: Downloading and executing binaries from internet

**Mitigation**:

1. Pin exact versions in pyproject.toml
1. Download from official GitHub releases
1. Verify checksums (future enhancement)
1. Install to user directory (~/.local/bin), not system-wide

### Script Execution

**Risk**: Executing bash scripts from Markdown files

**Mitigation**:

1. Scripts are part of the repository (reviewed in PRs)
1. Dry-run mode to preview commands
1. No automatic execution without user consent

### Registry File

**Risk**: Registry file could be tampered with

**Mitigation**:

1. Store in user directory (~/.local/share/doctk/)
1. Validate JSON structure before parsing
1. Graceful degradation if corrupted

## Migration Path

### Phase 1: Inline Tool Framework (Current Spec)

1. Copy sstdf-python-standards code to src/doctk/tools/
1. Update imports in scripts
1. Remove external dependency

### Phase 2: Copy Scripts and Plugins

1. Copy all scripts from template
1. Copy all tool plugin definitions
1. Make scripts executable

### Phase 3: Test Infrastructure

1. Create test subdirectories
1. Copy quality and docs tests
1. Update pytest configuration

### Phase 4: Documentation

1. Create MkDocs configuration
1. Create initial documentation pages
1. Set up GitHub Pages deployment

### Phase 5: Verification

1. Run setup-environment.sh
1. Run check-environment.sh
1. Run tox to verify all environments
1. Run pre-commit to verify hooks

## Future Enhancements

### Tool Management

- **Checksum verification**: Verify downloaded binaries match expected checksums
- **Parallel installation**: Install multiple tools concurrently
- **Auto-update**: Check for newer versions and prompt to update
- **Platform detection**: Support macOS and Windows in addition to Linux

### Testing

- **Coverage enforcement**: Fail if coverage drops below threshold
- **Mutation testing**: Use mutmut to verify test quality
- **Performance benchmarks**: Track performance over time

### Documentation

- **API docs auto-generation**: Use mkdocstrings to generate API docs from docstrings
- **Changelog automation**: Auto-generate changelog from git commits
- **Version documentation**: Keep docs for multiple versions

### CI/CD

- **GitHub Actions**: Run tox on every PR
- **Automated releases**: Publish to PyPI on tag
- **Documentation deployment**: Auto-deploy docs to GitHub Pages

## Open Questions

1. **Should we support multiple Python versions?** Currently targeting 3.10+, but should we test on 3.11, 3.12?
1. **Should tool plugins support platform-specific installation?** Currently Linux-only, but could add macOS/Windows support
1. **Should we cache downloaded tool binaries?** Could speed up reinstallation but adds complexity
1. **Should we integrate with system package managers?** Could use apt/brew as fallback if available

## References

- **python-project-template**: Source of tooling patterns
- **sstdf-python-standards**: Tool management framework
- **uv documentation**: https://docs.astral.sh/uv/
- **tox documentation**: https://tox.wiki/
- **pre-commit documentation**: https://pre-commit.com/
- **MkDocs documentation**: https://www.mkdocs.org/
- **MkDocs Material**: https://squidfunk.github.io/mkdocs-material/
