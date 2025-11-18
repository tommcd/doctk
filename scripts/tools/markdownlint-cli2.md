---
version: 0.18.1
install_method: npm
---

# markdownlint-cli2 - Markdown Linter

markdownlint-cli2 is a fast, flexible, and configuration-based Markdown linter built on markdownlint.

**Official Repository**: <https://github.com/DavidAnson/markdownlint-cli2>

## Prerequisites

**IMPORTANT**: markdownlint-cli2 requires Node.js and npm to be installed.

Check if npm is available:

```bash
npm --version
```

If npm is not installed, install Node.js first (which includes npm):

- **Ubuntu/Debian**: `sudo apt-get install nodejs npm`
- **Using nvm**: `curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash`
- **Official**: <https://nodejs.org/>

## Check Version

Check if markdownlint-cli2 is installed and get its version:

```bash check-version
markdownlint-cli2 --version 2>&1 | grep -oP 'markdownlint-cli2 v\K[\d.]+'
```

Exit code 0 means installed (prints version), non-zero means not installed.

## Install

Install markdownlint-cli2 v{VERSION} globally via npm:

```bash install
if ! command -v npm >/dev/null 2>&1; then
  echo "Error: npm not found - markdownlint-cli2 requires Node.js/npm" >&2
  echo "Install Node.js first, then re-run this command" >&2
  exit 1
fi
npm install -g "markdownlint-cli2@{VERSION}"
```

The `{VERSION}` placeholder is replaced with the version from `pyproject.toml`.

**Requirements**:

- `npm` (Node Package Manager)
- Node.js (usually installed with npm)
- Internet connection (to download from npm registry)

## Uninstall

Remove markdownlint-cli2 from the system:

```bash uninstall
npm uninstall -g markdownlint-cli2
```

## Verify

Verify that markdownlint-cli2 is working correctly (smoke test):

```bash verify
# Verify markdownlint-cli2 can process simple markdown
echo '# Title' | markdownlint-cli2 --stdin >/dev/null 2>&1
```

## Manual Testing

### Test Check Version

```bash
# Full version output
markdownlint-cli2 --version

# Extract just the version number (e.g., "0.18.1")
markdownlint-cli2 --version 2>&1 | grep -oP 'markdownlint-cli2 v\K[\d.]+'

# Exit code check
if command -v markdownlint-cli2 >/dev/null 2>&1; then
  echo "✓ markdownlint-cli2 is installed: $(markdownlint-cli2 --version)"
else
  echo "✗ markdownlint-cli2 is not installed"
fi
```

### Test npm Availability

```bash
# Check if npm is installed
if command -v npm >/dev/null 2>&1; then
  echo "✓ npm is available: $(npm --version)"
else
  echo "✗ npm is not installed"
  echo "  Install Node.js/npm first"
fi
```

### Test Installation

Replace `{VERSION}` with actual version (e.g., `0.18.1`):

```bash
# Check npm is available
if ! command -v npm >/dev/null 2>&1; then
  echo "Error: npm not found"
  exit 1
fi

# Install globally
npm install -g "markdownlint-cli2@0.18.1"

# Verify
markdownlint-cli2 --version

# Check where it's installed
which markdownlint-cli2
```

### Test markdownlint-cli2 Functionality

```bash
# Create a test Markdown file with issues
cat > /tmp/test.md <<'EOF'
#Bad heading (no space after #)

Line with trailing spaces

- List item 1
* List item 2 (inconsistent marker)

EOF

# Lint the file (will show violations)
markdownlint-cli2 /tmp/test.md

# Expected violations:
# - MD018: No space after hash on atx style heading
# - MD009: Trailing spaces
# - MD004: Inconsistent list style

# Fix violations automatically
markdownlint-cli2 --fix /tmp/test.md

# Show fixed result
cat /tmp/test.md

# Clean up
rm /tmp/test.md
```

### Test Uninstall

```bash
# Remove markdownlint-cli2
npm uninstall -g markdownlint-cli2

# Verify removed
if command -v markdownlint-cli2 >/dev/null 2>&1; then
  echo "✗ markdownlint-cli2 still installed"
else
  echo "✓ markdownlint-cli2 removed"
fi
```

## Usage in This Project

markdownlint-cli2 is used to lint Markdown documentation:

```bash
# Run via tox
uvx tox -e docs          # Full doc checks (includes markdownlint)

# Run directly
markdownlint-cli2 "**/*.md"
markdownlint-cli2 docs/

# Fix issues automatically
markdownlint-cli2 --fix "**/*.md"

# Use specific config
markdownlint-cli2 --config .markdownlint.yaml docs/
```

The tox environment is configured in [tox.ini](../../tox.ini), and markdownlint configuration is in [.markdownlint.yaml](../../.markdownlint.yaml).

## Version Management

The expected version is defined in `pyproject.toml`:

```toml
[tool.external-tools]
markdownlint-cli2 = "0.18.1"
```

To update the version:

1. Edit `pyproject.toml`
1. Run `python3 scripts/setup-external-tools.py`
1. Verify with `./scripts/check-environment.sh`

## markdownlint Configuration

This project configures markdownlint in [.markdownlint.yaml](../../.markdownlint.yaml):

- **MD013** (line length): Disabled (too restrictive for code blocks)
- **MD033** (inline HTML): Allowed (needed for some features)
- **MD041** (first line heading): Enforced
- **MD046** (code block style): Fenced (\`\`\`)

See [.markdownlint.yaml](../../.markdownlint.yaml) for complete configuration.

## Common markdownlint Rules

Some commonly enforced rules:

- **MD001**: Heading levels increment by one
- **MD009**: No trailing spaces
- **MD012**: No multiple consecutive blank lines
- **MD018**: Space after hash in atx heading
- **MD022**: Headings surrounded by blank lines
- **MD025**: Single top-level heading
- **MD031**: Fenced code blocks surrounded by blank lines

See <https://github.com/DavidAnson/markdownlint/blob/main/doc/Rules.md> for complete rule documentation.

## npm vs npm-Based Tool

**Important distinction**:

- **npm itself**: Installed system-wide (via apt, nvm, or Node.js installer)
- **markdownlint-cli2**: Installed via npm as a global package

This means:

1. npm must be installed first (prerequisite)
1. Then markdownlint-cli2 can be installed via npm
1. Uninstalling markdownlint-cli2 does NOT uninstall npm

## Troubleshooting

### npm Permission Issues

If you get permission errors installing globally:

```bash
# Option 1: Use sudo (simple but not ideal)
sudo npm install -g markdownlint-cli2@0.18.1

# Option 2: Configure npm to use user directory (recommended)
mkdir -p ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
npm install -g markdownlint-cli2@0.18.1
```

### npm Not Found

If npm is not installed:

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install nodejs npm

# Verify
npm --version
node --version
```
