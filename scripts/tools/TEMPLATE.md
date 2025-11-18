# tool-name - Short Description

Brief description of what this tool does (1-2 sentences).

**Official Repository**: <https://github.com/org/tool-name>

## Prerequisites

*(Optional section - only if tool has special requirements)*

**IMPORTANT**: tool-name requires specific dependencies:

- Dependency 1 (how to check if installed)
- Dependency 2 (how to install)

Check if prerequisites are met:

```bash
command --version  # Check specific dependency
```

## Check Version

Check if tool-name is installed and get its version:

```bash check-version
tool-name --version 2>&1 | grep -oP 'tool-name \K[\d.]+'
```

Exit code 0 means installed (prints version), non-zero means not installed.

## Install

Download and install tool-name v{VERSION} from GitHub releases:

```bash install
mkdir -p ~/.local/bin
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"
wget -q "https://github.com/org/tool-name/releases/download/v{VERSION}/tool-name-linux-x86_64.tar.gz"
tar -xzf "tool-name-linux-x86_64.tar.gz"
mv tool-name ~/.local/bin/tool-name
chmod +x ~/.local/bin/tool-name
cd - >/dev/null
rm -rf "$TEMP_DIR"
```

The `{VERSION}` placeholder is replaced with the version from `pyproject.toml`.

**Requirements**:

- `~/.local/bin` on PATH
- `wget` for downloading
- `tar` for extraction (if needed)
- Linux x86_64 architecture

**Notes**:

- Adjust download URL format based on tool's release pattern
- Some tools use `v{VERSION}`, others just `{VERSION}`
- Extraction varies: `.tar.gz`, `.tar.xz`, `.gz`, or plain binary
- Some tools (like npm packages) use different install methods

## Uninstall

Remove tool-name from ~/.local/bin:

```bash uninstall
rm -f ~/.local/bin/tool-name
```

**Note**: Adjust path if tool installs to different location (e.g., npm global packages).

## Verify

Verify that tool-name is working correctly (smoke test):

```bash verify
# Simple smoke test - run tool with --help or process minimal input
tool-name --help >/dev/null 2>&1
```

**Note**: Verification is optional but recommended. The verify block should:

- Run a simple operation that confirms tool functionality
- Exit with code 0 on success, non-zero on failure
- Be fast (< 1 second ideally)
- Not require special setup or test files

**Good verification examples**:

- `tool-name --help` - Confirms tool can start and display help
- `echo "test" | tool-name` - Process minimal input
- `tool-name --version` - More thorough than check-version (may test dependencies)

**Bad verification examples**:

- Complex operations requiring test files
- Slow operations (> 5 seconds)
- Operations requiring network access
- Operations requiring special permissions

## Manual Testing

### Test Check Version

```bash
# Should print version if installed (e.g., "1.2.3")
tool-name --version

# Extract version number
tool-name --version 2>&1 | grep -oP 'tool-name \K[\d.]+'

# Exit code check
if command -v tool-name >/dev/null 2>&1; then
  echo "✓ tool-name is installed: $(tool-name --version)"
else
  echo "✗ tool-name is not installed"
fi
```

### Test Installation

Replace `{VERSION}` with actual version (e.g., `1.2.3`):

```bash
# Create temp directory for testing
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Download (adjust URL format as needed)
wget -q "https://github.com/org/tool-name/releases/download/v1.2.3/tool-name-linux-x86_64.tar.gz"

# Extract (if needed - skip for plain binaries)
tar -xzf "tool-name-linux-x86_64.tar.gz"

# Install
sudo mv tool-name /usr/local/bin/tool-name
sudo chmod +x /usr/local/bin/tool-name

# Verify
tool-name --version

# Cleanup
cd - >/dev/null
rm -rf "$TEMP_DIR"
```

### Test tool-name Functionality

```bash
# Create a test file
cat > /tmp/test-file <<'EOF'
# Sample content to test tool-name
line 1
line 2
EOF

# Run tool-name on test file
tool-name /tmp/test-file

# Expected output:
# (describe what should happen)

# Clean up
rm /tmp/test-file
```

### Test Uninstall

```bash
# Remove tool-name
sudo rm -f /usr/local/bin/tool-name

# Verify removed
if command -v tool-name >/dev/null 2>&1; then
  echo "✗ tool-name still installed"
else
  echo "✓ tool-name removed"
fi
```

## Usage in This Project

tool-name is used to \[describe purpose in this project\]:

```bash
# Run via tox
uvx tox -e tool-name

# Run directly
tool-name [files/options]

# Common options
tool-name --help
```

The tox environment is configured in [tox.ini](../../tox.ini).

## Version Management

The expected version is defined in `pyproject.toml`:

```toml
[tool.external-tools]
tool-name = "1.2.3"
```

To update the version:

1. Edit `pyproject.toml`
1. Run `python3 scripts/setup-external-tools.py`
1. Verify with `./scripts/check-environment.sh`

## Configuration

*(Optional section - only if tool has configuration files)*

tool-name is configured in [.tool-namerc](../../.tool-namerc):

```yaml
# Example configuration
option1: value1
option2: value2
```

Key configuration options:

- **option1**: Description
- **option2**: Description

See [.tool-namerc](../../.tool-namerc) for complete configuration.

## Common tool-name Options

*(Optional section - document useful command-line options)*

Useful command-line options:

- `--verbose`: Show detailed output
- `--fix`: Auto-fix issues
- `--config <file>`: Use specific config file
- `--format <format>`: Output format (json, plain, etc.)

## Troubleshooting

*(Optional section - only if tool has common issues)*

### Issue 1: Description

**Problem**: Describe the problem

**Cause**: Why it happens

**Solution**:

```bash
# Commands to fix
```

### Issue 2: Another Issue

**Problem**: Another problem description

**Solutions**:

1. Option 1
1. Option 2

## Additional Notes

*(Optional section - any other important information)*

- Special considerations for this tool
- Known limitations
- Performance characteristics
- Alternatives or related tools

## References

- Official documentation: <https://tool-name.example.com/docs>
- Release notes: <https://github.com/org/tool-name/releases>
- Configuration guide: <https://tool-name.example.com/config>
