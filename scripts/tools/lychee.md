---
version: 0.20.1
install_method: binary
---

# lychee - Fast Link Checker

lychee is a fast, asynchronous link checker written in Rust that finds broken links in Markdown, HTML, and other text files.

**Official Repository**: <https://github.com/lycheeverse/lychee>

## Check Version

Check if lychee is installed and get its version:

```bash check-version
lychee --version 2>&1 | grep -oP 'lychee \K[\d.]+'
```

Exit code 0 means installed (prints version), non-zero means not installed.

## Install

Download and install lychee v{VERSION} from GitHub releases:

```bash install
mkdir -p ~/.local/bin
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"
wget -q "https://github.com/lycheeverse/lychee/releases/download/lychee-v{VERSION}/lychee-x86_64-unknown-linux-gnu.tar.gz"
tar -xzf "lychee-x86_64-unknown-linux-gnu.tar.gz"
mv lychee ~/.local/bin/lychee
chmod +x ~/.local/bin/lychee
cd - >/dev/null
rm -rf "$TEMP_DIR"
```

The `{VERSION}` placeholder is replaced with the version from `pyproject.toml`.

**Requirements**:

- `~/.local/bin` on PATH
- `wget` for downloading
- `tar` with gzip support (tar.gz extraction)
- Linux x86_64 architecture

## Uninstall

Remove lychee from ~/.local/bin:

```bash uninstall
rm -f ~/.local/bin/lychee
```

## Verify

Verify that lychee is working correctly (smoke test):

```bash verify
# Verify lychee can check a simple URL
echo 'https://example.com' | lychee - >/dev/null 2>&1
```

## Manual Testing

### Test Check Version

```bash
# Full version output
lychee --version

# Extract just the version number (e.g., "0.20.1")
lychee --version 2>&1 | grep -oP 'lychee \K[\d.]+'

# Exit code check
if command -v lychee >/dev/null 2>&1; then
  echo "✓ lychee is installed: $(lychee --version)"
else
  echo "✗ lychee is not installed"
fi
```

### Test Installation

Replace `{VERSION}` with actual version (e.g., `0.20.1`):

```bash
# Create temp directory for testing
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Download (note: lychee-v prefix in URL)
wget -q "https://github.com/lycheeverse/lychee/releases/download/lychee-v0.20.1/lychee-x86_64-unknown-linux-gnu.tar.gz"

# Extract tar.gz archive
tar -xzf "lychee-x86_64-unknown-linux-gnu.tar.gz"

# List extracted files
ls -la

# Install
sudo mv lychee /usr/local/bin/lychee
sudo chmod +x /usr/local/bin/lychee

# Verify
lychee --version

# Cleanup
cd - >/dev/null
rm -rf "$TEMP_DIR"
```

### Test lychee Functionality

```bash
# Create a test Markdown file with links
cat > /tmp/test.md <<'EOF'
# Test Links

- [Valid Link](https://github.com)
- [Broken Link](https://this-domain-does-not-exist-12345.com)
- [Local File](README.md)
EOF

# Check links (will show broken ones)
lychee /tmp/test.md

# Check with verbose output
lychee --verbose /tmp/test.md

# Check with specific excludes
lychee --exclude "broken" /tmp/test.md

# Clean up
rm /tmp/test.md
```

### Test Uninstall

```bash
# Remove lychee
sudo rm -f /usr/local/bin/lychee

# Verify removed
if command -v lychee >/dev/null 2>&1; then
  echo "✗ lychee still installed"
else
  echo "✓ lychee removed"
fi
```

## Usage in This Project

lychee is used to check for broken links in Markdown documentation:

```bash
# Run via tox
uvx tox -e docs          # Full doc checks (includes lychee)

# Run directly
lychee docs/**/*.md
lychee README.md

# Check with specific config
lychee --config .lychee.toml docs/
```

The tox environment is configured in [tox.ini](../../tox.ini), and lychee configuration is in [.lychee.toml](../../.lychee.toml).

## Version Management

The expected version is defined in `pyproject.toml`:

```toml
[tool.external-tools]
lychee = "0.20.1"
```

To update the version:

1. Edit `pyproject.toml`
1. Run `python3 scripts/setup-external-tools.py`
1. Verify with `./scripts/check-environment.sh`

## lychee Configuration

This project configures lychee in [.lychee.toml](../../.lychee.toml):

- **Excluded paths**: `.venv/`, `.tox/`, `tests/data/`, `site/`
- **Excluded URLs**: Local paths, build artifacts
- **Max retries**: 3
- **Timeout**: 30 seconds
- **User agent**: Custom (to avoid rate limiting)

See [.lychee.toml](../../.lychee.toml) for complete configuration.

## Common lychee Options

Useful command-line options:

- `--verbose`: Show detailed output
- `--no-progress`: Disable progress bar (useful for CI)
- `--exclude <pattern>`: Exclude URLs matching pattern
- `--config <file>`: Use specific config file
- `--format <format>`: Output format (plain, json, markdown)
- `--offline`: Only check local file links (skip HTTP)

## Performance

lychee is written in Rust and uses async I/O, making it significantly faster than traditional link checkers:

- **Parallel checking**: Checks multiple links concurrently
- **Caching**: Remembers checked URLs within session
- **Smart retry**: Exponential backoff for failed requests
