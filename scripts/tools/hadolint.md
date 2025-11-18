---
version: 2.14.0
install_method: binary
---

# hadolint - Dockerfile Linter

hadolint is a Haskell-based Dockerfile linter that checks for best practices and common mistakes in Dockerfiles.

**Official Repository**: <https://github.com/hadolint/hadolint>

## Check Version

Check if hadolint is installed and get its version:

```bash check-version
hadolint --version 2>&1 | grep -oP 'Haskell Dockerfile Linter \K[\d.]+'
```

Exit code 0 means installed (prints version), non-zero means not installed.

## Install

Download and install hadolint v{VERSION} from GitHub releases:

```bash install
mkdir -p ~/.local/bin
wget -q "https://github.com/hadolint/hadolint/releases/download/v{VERSION}/hadolint-Linux-x86_64"
mv "hadolint-Linux-x86_64" ~/.local/bin/hadolint
chmod +x ~/.local/bin/hadolint
```

The `{VERSION}` placeholder is replaced with the version from `pyproject.toml`.

**Requirements**:

- `~/.local/bin` on PATH
- `wget` for downloading
- Linux x86_64 architecture

## Uninstall

Remove hadolint from ~/.local/bin:

```bash uninstall
rm -f ~/.local/bin/hadolint
```

## Verify

Verify that hadolint is working correctly (smoke test):

```bash verify
# Verify hadolint can analyze a simple Dockerfile
echo 'FROM alpine:3.18' | hadolint - >/dev/null 2>&1
```

## Manual Testing

### Test Check Version

```bash
# Should print version if installed (e.g., "2.14.0")
hadolint --version 2>&1 | grep -oP 'Haskell Dockerfile Linter \K[\d.]+'

# Exit code check
if hadolint --version 2>&1 | grep -qP 'Haskell Dockerfile Linter [\d.]+'; then
  echo "✓ hadolint is installed"
else
  echo "✗ hadolint is not installed"
fi
```

### Test Installation

Replace `{VERSION}` with actual version (e.g., `2.14.0`):

```bash
# Create temp directory for testing
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Download
wget -q "https://github.com/hadolint/hadolint/releases/download/v2.14.0/hadolint-Linux-x86_64"

# Install
sudo mv "hadolint-Linux-x86_64" /usr/local/bin/hadolint
sudo chmod +x /usr/local/bin/hadolint

# Verify
hadolint --version

# Cleanup
cd - >/dev/null
rm -rf "$TEMP_DIR"
```

### Test hadolint Functionality

```bash
# Create a test Dockerfile with issues
cat > /tmp/test.Dockerfile <<'EOF'
FROM ubuntu
RUN apt-get update && apt-get install curl
CMD curl example.com
EOF

# Run hadolint (should show warnings)
hadolint /tmp/test.Dockerfile

# Expected output shows violations:
# - DL3008: Pin versions in apt-get install
# - DL3009: Delete apt-get lists after installing
# - DL4006: Set the SHELL option -o pipefail

# Clean up
rm /tmp/test.Dockerfile
```

### Test Uninstall

```bash
# Remove hadolint
sudo rm -f /usr/local/bin/hadolint

# Verify removed
if command -v hadolint >/dev/null 2>&1; then
  echo "✗ hadolint still installed"
else
  echo "✓ hadolint removed"
fi
```

## Usage in This Project

hadolint is used to lint the Dockerfile:

```bash
# Run via tox
uvx tox -e hadolint

# Run directly
hadolint Dockerfile
```

The tox environment is configured in [tox.ini](../../tox.ini).

## Version Management

The expected version is defined in `pyproject.toml`:

```toml
[tool.external-tools]
hadolint = "2.14.0"
```

To update the version:

1. Edit `pyproject.toml`
1. Run `python3 scripts/setup-external-tools.py`
1. Verify with `./scripts/check-environment.sh`
