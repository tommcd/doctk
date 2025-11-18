---
version: 3.10.0
install_method: binary
---

# shfmt - Shell Script Formatter

shfmt is a shell parser, formatter, and interpreter with support for POSIX Shell, Bash, and mksh.

**Official Repository**: <https://github.com/mvdan/sh>

## Check Version

Check if shfmt is installed and get its version:

```bash check-version
shfmt -version 2>&1 | grep -oP 'v?\K[\d.]+'
```

Exit code 0 means installed (prints version), non-zero means not installed.

## Install

Download and install shfmt v{VERSION} from GitHub releases:

```bash install
mkdir -p ~/.local/bin
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"
wget -q "https://github.com/mvdan/sh/releases/download/v{VERSION}/shfmt_v{VERSION}_linux_amd64"
mv "shfmt_v{VERSION}_linux_amd64" ~/.local/bin/shfmt
chmod +x ~/.local/bin/shfmt
cd - >/dev/null
rm -rf "$TEMP_DIR"
```

The `{VERSION}` placeholder is replaced with the version from `pyproject.toml`.

**Requirements**:

- `~/.local/bin` on PATH
- `wget` for downloading
- Linux x86_64 (amd64) architecture

## Uninstall

Remove shfmt from ~/.local/bin:

```bash uninstall
rm -f ~/.local/bin/shfmt
```

## Verify

Verify that shfmt is working correctly (smoke test):

```bash verify
# Verify shfmt can format a simple script
echo 'echo "test"' | shfmt >/dev/null 2>&1
```

## Manual Testing

### Test Check Version

```bash
# Should print version if installed (e.g., "3.10.0")
shfmt -version

# Parse version number
shfmt -version 2>&1 | grep -oP 'v?\K[\d.]+'

# Exit code check
if command -v shfmt >/dev/null 2>&1; then
  echo "✓ shfmt is installed: $(shfmt -version)"
else
  echo "✗ shfmt is not installed"
fi
```

### Test Installation

Replace `{VERSION}` with actual version (e.g., `3.10.0`):

```bash
# Create temp directory for testing
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Download (note: v-prefixed in URL)
wget -q "https://github.com/mvdan/sh/releases/download/v3.10.0/shfmt_v3.10.0_linux_amd64"

# Install
sudo mv "shfmt_v3.10.0_linux_amd64" /usr/local/bin/shfmt
sudo chmod +x /usr/local/bin/shfmt

# Verify
shfmt -version

# Cleanup
cd - >/dev/null
rm -rf "$TEMP_DIR"
```

### Test shfmt Functionality

```bash
# Create a test shell script with formatting issues
cat > /tmp/test.sh <<'EOF'
#!/bin/bash
function hello( ) {
echo "hello"
  echo "world"
}
EOF

# Format the file (default: 2-space indentation)
shfmt /tmp/test.sh

# Format with specific options (Google Shell Style)
shfmt -i 2 -ci -bn /tmp/test.sh

# Format in-place
shfmt -w /tmp/test.sh

# Show formatted result
cat /tmp/test.sh

# Clean up
rm /tmp/test.sh
```

### Test Uninstall

```bash
# Remove shfmt
sudo rm -f /usr/local/bin/shfmt

# Verify removed
if command -v shfmt >/dev/null 2>&1; then
  echo "✗ shfmt still installed"
else
  echo "✓ shfmt removed"
fi
```

## Usage in This Project

shfmt is used to format bash scripts following Google Shell Style Guide:

```bash
# Run via tox
uvx tox -e shfmt           # Check formatting only
uvx tox -e shfmt-fix       # Format scripts in-place

# Run directly
shfmt -d scripts/*.sh      # Check formatting (diff)
shfmt -w scripts/*.sh      # Format in-place

# Google Shell Style options
shfmt -i 2 -ci -bn -d scripts/*.sh
#     │   │   └── Binary ops at line start
#     │   └────── Case indentation
#     └────────── 2-space indentation
```

The tox environments are configured in [tox.ini](../../tox.ini).

## Version Management

The expected version is defined in `pyproject.toml`:

```toml
[tool.external-tools]
shfmt = "3.10.0"
```

To update the version:

1. Edit `pyproject.toml`
1. Run `python3 scripts/setup-external-tools.py`
1. Verify with `./scripts/check-environment.sh`

## Formatting Options Used

This project uses Google Shell Style Guide formatting options:

- `-i 2`: 2-space indentation
- `-ci`: Case indentation (indent patterns in switch cases)
- `-bn`: Binary ops at line start (e.g., `&&` and `||` at beginning of line)

These options are configured in the tox `shfmt` and `shfmt-fix` environments.
