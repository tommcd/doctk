---
version: 0.11.0
install_method: binary
---

# shellcheck - Shell Script Static Analysis

shellcheck is a static analysis tool for shell scripts that finds bugs and suggests improvements.

**Official Repository**: <https://github.com/koalaman/shellcheck>
**Official Wiki**: <https://www.shellcheck.net/>

## Check Version

Check if shellcheck is installed and get its version:

```bash check-version
shellcheck --version 2>&1 | grep -oP 'version: \K[\d.]+' | head -n 1
```

Exit code 0 means installed (prints version), non-zero means not installed.

## Install

Download and install shellcheck v{VERSION} from GitHub releases:

```bash install
mkdir -p ~/.local/bin
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"
wget -q "https://github.com/koalaman/shellcheck/releases/download/v{VERSION}/shellcheck-v{VERSION}.linux.x86_64.tar.xz"
tar -xf "shellcheck-v{VERSION}.linux.x86_64.tar.xz"
mv "shellcheck-v{VERSION}/shellcheck" ~/.local/bin/shellcheck
chmod +x ~/.local/bin/shellcheck
cd - >/dev/null
rm -rf "$TEMP_DIR"
```

The `{VERSION}` placeholder is replaced with the version from `pyproject.toml`.

**Requirements**:

- `~/.local/bin` on PATH
- `wget` for downloading
- `tar` with xz support (tar.xz extraction)
- Linux x86_64 architecture

## Uninstall

Remove shellcheck from ~/.local/bin:

```bash uninstall
rm -f ~/.local/bin/shellcheck
```

## Verify

Verify that shellcheck is working correctly (smoke test):

```bash verify
# Verify shellcheck can analyze a simple script
echo '#!/bin/bash' | shellcheck - >/dev/null 2>&1
```

## Manual Testing

### Test Check Version

```bash
# Full version output
shellcheck --version

# Extract just the version number (e.g., "0.11.0")
shellcheck --version 2>&1 | grep -oP 'version: \K[\d.]+' | head -n 1

# Exit code check
if command -v shellcheck >/dev/null 2>&1; then
  echo "✓ shellcheck is installed: $(shellcheck --version | grep version | head -n 1)"
else
  echo "✗ shellcheck is not installed"
fi
```

### Test Installation

Replace `{VERSION}` with actual version (e.g., `0.11.0`):

```bash
# Create temp directory for testing
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Download (note: v-prefixed in URL and filename)
wget -q "https://github.com/koalaman/shellcheck/releases/download/v0.11.0/shellcheck-v0.11.0.linux.x86_64.tar.xz"

# Extract tar.xz archive
tar -xf "shellcheck-v0.11.0.linux.x86_64.tar.xz"

# List extracted files
ls -la

# Install (binary is in subdirectory)
sudo mv "shellcheck-v0.11.0/shellcheck" /usr/local/bin/shellcheck
sudo chmod +x /usr/local/bin/shellcheck

# Verify
shellcheck --version

# Cleanup
cd - >/dev/null
rm -rf "$TEMP_DIR"
```

### Test shellcheck Functionality

```bash
# Create a test shell script with issues
cat > /tmp/test.sh <<'EOF'
#!/bin/bash
echo $PATH
name="hello world"
echo $name
if [ $name = "hello world" ]
then
  echo "match"
fi
EOF

# Run shellcheck (should show warnings)
shellcheck /tmp/test.sh

# Expected warnings:
# SC2086: Double quote to prevent globbing and word splitting
# SC2181: Check exit code directly with e.g. 'if mycmd;', not indirectly with $?

# Run with specific severity
shellcheck --severity=error /tmp/test.sh

# Run with JSON output
shellcheck --format=json /tmp/test.sh

# Clean up
rm /tmp/test.sh
```

### Test Uninstall

```bash
# Remove shellcheck
sudo rm -f /usr/local/bin/shellcheck

# Verify removed
if command -v shellcheck >/dev/null 2>&1; then
  echo "✗ shellcheck still installed"
else
  echo "✓ shellcheck removed"
fi
```

## Usage in This Project

shellcheck is used to lint bash scripts for potential issues:

```bash
# Run via tox
uvx tox -e shellcheck

# Run directly
shellcheck scripts/*.sh

# Check specific severity level
shellcheck --severity=error scripts/*.sh

# Exclude specific checks
shellcheck --exclude=SC2086 scripts/*.sh
```

The tox environment is configured in [tox.ini](../../tox.ini).

## Version Management

The expected version is defined in `pyproject.toml`:

```toml
[tool.external-tools]
shellcheck = "0.11.0"
```

To update the version:

1. Edit `pyproject.toml`
1. Run `python3 scripts/setup-external-tools.py`
1. Verify with `./scripts/check-environment.sh`

## shellcheck Configuration

This project uses shellcheck with:

- **Severity**: `--severity=error` (only fail on errors, not warnings)
- **Format**: Default text output (also supports json, gcc, tty)
- **Shell**: Auto-detected from shebang (bash in this project)

Configuration is in [tox.ini](../../tox.ini) under `[testenv:shellcheck]`.

## Common shellcheck Codes

Some common issues shellcheck detects:

- **SC2086**: Double quote to prevent globbing/word splitting
- **SC2181**: Check exit code directly, not with `$?`
- **SC2046**: Quote to prevent word splitting
- **SC2006**: Use `$(...)` instead of backticks
- **SC1091**: Not following sourced files (can be ignored with `--exclude`)

See <https://www.shellcheck.net/wiki/> for complete documentation.
