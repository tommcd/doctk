# Tool Management System

doctk uses a plugin-based system for managing external development tools. This system ensures consistent tool versions across all development environments and simplifies setup for new contributors.

## Overview

The tool management system consists of three main components:

1. **Tool Plugins**: Markdown files defining how to install, check, and uninstall tools
1. **Tool Manager**: Python framework that reads plugins and executes operations
1. **Tool Registry**: JSON file tracking which tools are managed by the system

## Architecture

```
scripts/tools/          # Tool plugin definitions
├── TEMPLATE.md         # Template for creating new plugins
├── shellcheck.md       # Shell script linter
├── shfmt.md            # Shell script formatter
├── lychee.md           # Link checker
├── markdownlint-cli2.md # Markdown linter
├── taplo.md            # TOML formatter
└── hadolint.md         # Dockerfile linter

src/doctk/tools/        # Tool management framework
├── __init__.py
├── manager.py          # ToolManager class
├── plugin.py           # ToolPlugin class
└── registry.py         # ToolRegistry class

~/.local/bin/           # Tool installation directory
~/.local/share/doctk/   # Tool registry location
└── tool-registry.json  # Tracks managed tools
```

## Tool Plugins

### Plugin Format

Tool plugins are Markdown files with YAML frontmatter and bash code blocks:

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

### Required Sections

Each plugin must have:

1. **Frontmatter**: YAML metadata with `name`, `description`, and `default_version`
2. **Installation**: Bash script to install the tool
3. **Version Check**: Bash script to get the installed version
4. **Uninstall**: Bash script to remove the tool

### Version Management

Tool versions can be specified in two places:

1. **Plugin default**: `default_version` in frontmatter
2. **Project override**: `[tool.external-tools]` in `pyproject.toml`

Project overrides take precedence:

```toml
[tool.external-tools]
shellcheck = "0.11.0"
shfmt = "3.10.0"
lychee = "0.18.0"
markdownlint-cli2 = "0.16.0"
taplo = "0.9.3"
hadolint = "2.12.0"
````

## Tool Management Scripts

### setup-external-tools.py

Install tools from plugin definitions:

```bash
# Install all tools
python3 scripts/setup-external-tools.py

# Install specific tool
python3 scripts/setup-external-tools.py --tool shellcheck

# Preview without installing
python3 scripts/setup-external-tools.py --dry-run
```

### check-tools.py

Verify tool versions match expectations:

```bash
python3 scripts/check-tools.py
```

Output shows:

- Tool name
- Expected version (from pyproject.toml or plugin)
- Installed version
- Status (✓ match, ✗ mismatch, ⚠ not installed)
- Whether tool is plugin-managed

### clean-tools.py

Uninstall plugin-managed tools:

```bash
# Uninstall all plugin-managed tools
python3 scripts/clean-tools.py

# Preview what would be removed
python3 scripts/clean-tools.py --dry-run
```

**Important**: Only removes tools tracked in the registry. System-installed tools are not affected.

## Tool Registry

### Purpose

The registry tracks which tools are managed by the plugin system. This prevents accidentally removing system-installed tools.

### Location

`~/.local/share/doctk/tool-registry.json`

### Format

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
```

### Operations

- **Add**: Record tool installation
- **Remove**: Remove tool from registry
- **Check**: Verify if tool is managed
- **Get Info**: Retrieve tool metadata

## Python API

### ToolManager

Main interface for tool operations:

```python
from doctk.tools import ToolManager

# Initialize manager
manager = ToolManager(
    plugins_dir="scripts/tools",
    version_overrides={"shellcheck": "0.11.0"}
)

# Install all tools
manager.install_all(dry_run=False)

# Check all tools
status = manager.check_all()

# Uninstall all tools
manager.uninstall_all(dry_run=False)

# Get specific tool
tool = manager.get_tool("shellcheck")
```

### ToolPlugin

Represents a single tool:

```python
from doctk.tools import ToolPlugin

# Load plugin from file
plugin = ToolPlugin.from_file("scripts/tools/shellcheck.md")

# Get version info
expected = plugin.get_version_spec()
installed = plugin.get_version()

# Install tool
plugin.install(version="0.11.0", dry_run=False)

# Check if managed
is_managed = plugin.is_plugin_managed()

# Uninstall tool
plugin.uninstall(dry_run=False)
```

### ToolRegistry

Tracks managed tools:

```python
from doctk.tools import ToolRegistry

# Initialize registry
registry = ToolRegistry()

# Add tool
registry.add("shellcheck", "0.11.0", "/home/user/.local/bin/shellcheck")

# Check if managed
is_managed = registry.is_managed("shellcheck")

# Get tool info
info = registry.get_info("shellcheck")

# Remove tool
registry.remove("shellcheck")
```

## Creating New Tool Plugins

### 1. Copy Template

```bash
cp scripts/tools/TEMPLATE.md scripts/tools/mytool.md
```

### 2. Update Frontmatter

```yaml
---
name: mytool
description: Description of the tool
default_version: "1.0.0"
---
```

### 3. Write Installation Script

```bash
VERSION="${VERSION:-1.0.0}"
# Download and install to ~/.local/bin
# Make executable with chmod +x
```

### 4. Write Version Check Script

```bash
# Output just the version number
mytool --version | awk '{print $2}'
```

### 5. Write Uninstall Script

```bash
rm -f ~/.local/bin/mytool
```

### 6. Add to pyproject.toml

```toml
[tool.external-tools]
mytool = "1.0.0"
```

### 7. Validate Plugin

```bash
python3 scripts/validate-plugins.py
```

### 8. Test Installation

```bash
python3 scripts/setup-external-tools.py --tool mytool
python3 scripts/check-tools.py
```

## Best Practices

### Plugin Development

- Use `${VERSION:-default}` pattern for version variables
- Install to `~/.local/bin` (user directory, not system)
- Make binaries executable with `chmod +x`
- Download from official sources (GitHub releases)
- Use `wget -qO-` or `curl -fsSL` for downloads
- Extract directly to destination when possible
- Clean up temporary files

### Version Management

- Pin exact versions in `pyproject.toml`
- Update all versions together
- Test after version updates
- Document breaking changes

### Registry Management

- Never manually edit the registry
- Use `clean-tools.py` to reset if corrupted
- Registry is per-project (different projects can have different versions)

## Troubleshooting

### Tool Not Found After Installation

Ensure `~/.local/bin` is on your PATH:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Version Mismatch

Reinstall the tool:

```bash
python3 scripts/clean-tools.py
python3 scripts/setup-external-tools.py
```

### Registry Corruption

If the registry is corrupted:

```bash
# Remove registry
rm ~/.local/share/doctk/tool-registry.json

# Reinstall tools
python3 scripts/setup-external-tools.py
```

### Plugin Validation Errors

Run validation to see specific errors:

```bash
python3 scripts/validate-plugins.py
```

Common issues:

- Missing required sections
- Invalid YAML frontmatter
- Missing code blocks
- Incorrect code block labels

## Integration with Other Tools

### Pre-commit Hooks

Tool plugins are validated in pre-commit:

```yaml
- repo: local
  hooks:
    - id: validate-tool-plugins
      name: Validate tool plugins
      entry: python3 scripts/validate-plugins.py
      language: system
      pass_filenames: false
```

### Tox Environments

Tools are checked in the `check-environment` tox environment:

```ini
[testenv:check-environment]
description = Verify development environment is ready
commands =
    bash scripts/check-environment.sh
```

### CI/CD

Tools are installed in CI workflows:

```yaml
- name: Install external tools
  run: python3 scripts/setup-external-tools.py
```

## Future Enhancements

### Planned Features

- **Checksum verification**: Verify downloaded binaries
- **Parallel installation**: Install multiple tools concurrently
- **Platform detection**: Support macOS and Windows
- **Auto-update**: Check for newer versions
- **Caching**: Cache downloaded binaries

### Contributing

To add support for a new tool:

1. Create a plugin file in `scripts/tools/`
1. Add version to `pyproject.toml`
1. Test installation and version checking
1. Submit a pull request

See the [Contributing Guide](https://github.com/tommcd/doctk/blob/main/CONTRIBUTING.md) for details.

## References

- [Tool Plugin Template](https://github.com/tommcd/doctk/blob/main/scripts/tools/TEMPLATE.md)
- [Development Setup](setup.md)
- [Contributing Guide](https://github.com/tommcd/doctk/blob/main/CONTRIBUTING.md)
