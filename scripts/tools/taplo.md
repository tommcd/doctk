---
version: 0.9.3
install_method: binary
---

# taplo - TOML Formatter and Linter

taplo is a TOML toolkit written in Rust that provides formatting, linting, and LSP support for TOML files.

**Official Repository**: <https://github.com/tamasfe/taplo>

## Check Version

Check if taplo is installed and get its version:

```bash check-version
taplo --version 2>&1 | grep -oP 'taplo \K[\d.]+'
```

Exit code 0 means installed (prints version), non-zero means not installed.

## Install

Download and install taplo v{VERSION} from GitHub releases:

```bash install
mkdir -p ~/.local/bin
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"
wget -q "https://github.com/tamasfe/taplo/releases/download/{VERSION}/taplo-linux-x86_64.gz"
gunzip "taplo-linux-x86_64.gz"
mv "taplo-linux-x86_64" ~/.local/bin/taplo
chmod +x ~/.local/bin/taplo
cd - >/dev/null
rm -rf "$TEMP_DIR"
```

The `{VERSION}` placeholder is replaced with the version from `pyproject.toml`.

**Requirements**:

- `~/.local/bin` on PATH
- `wget` for downloading
- `gunzip` for decompression
- Linux x86_64 architecture

## Uninstall

Remove taplo from ~/.local/bin:

```bash uninstall
rm -f ~/.local/bin/taplo
```

## Verify

Verify that taplo is working correctly (smoke test):

```bash verify
# Verify taplo can format simple TOML
echo '[section]' | taplo fmt - >/dev/null 2>&1
```

## Manual Testing

### Test Check Version

```bash
# Should print version if installed (e.g., "0.9.3")
taplo --version 2>&1 | grep -oP 'taplo \K[\d.]+'

# Exit code check
if taplo --version 2>&1 | grep -qP 'taplo [\d.]+'; then
  echo "✓ taplo is installed"
else
  echo "✗ taplo is not installed"
fi
```

### Test Installation

Replace `{VERSION}` with actual version (e.g., `0.9.3`):

```bash
# Create temp directory for testing
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Download (note: direct version, not v-prefixed)
wget -q "https://github.com/tamasfe/taplo/releases/download/0.9.3/taplo-linux-x86_64.gz"

# Extract
gunzip "taplo-linux-x86_64.gz"

# Install
sudo mv "taplo-linux-x86_64" /usr/local/bin/taplo
sudo chmod +x /usr/local/bin/taplo

# Verify
taplo --version

# Cleanup
cd - >/dev/null
rm -rf "$TEMP_DIR"
```

### Test taplo Functionality

```bash
# Create a test TOML file with formatting issues
cat > /tmp/test.toml <<'EOF'
[package]
name="test"
version = "0.1.0"

  [dependencies]
  some_dep = "1.0"
EOF

# Format the file
taplo format /tmp/test.toml

# Show formatted result
cat /tmp/test.toml

# Lint the file
taplo lint /tmp/test.toml

# Clean up
rm /tmp/test.toml
```

### Test Uninstall

```bash
# Remove taplo
sudo rm -f /usr/local/bin/taplo

# Verify removed
if command -v taplo >/dev/null 2>&1; then
  echo "✗ taplo still installed"
else
  echo "✓ taplo removed"
fi
```

## Usage in This Project

taplo is used to format and lint TOML files (pyproject.toml):

```bash
# Run via tox
uvx tox -e taplo-format    # Format TOML files
uvx tox -e taplo-check     # Check formatting only

# Run directly
taplo format pyproject.toml
taplo lint pyproject.toml
```

The tox environments are configured in [tox.ini](../../tox.ini).

## Version Management

The expected version is defined in `pyproject.toml`:

```toml
[tool.external-tools]
taplo = "0.9.3"
```

To update the version:

1. Edit `pyproject.toml`
1. Run `python3 scripts/setup-external-tools.py`
1. Verify with `./scripts/check-environment.sh`

## Notes

- taplo releases use direct version numbers (e.g., `0.9.3`), not `v0.9.3`
- The downloaded file is gzipped and must be extracted with `gunzip`
- After extraction, the file is named `taplo-linux-x86_64` (no `.gz` extension)
