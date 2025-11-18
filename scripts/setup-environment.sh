#!/bin/bash
# Comprehensive environment setup script
# Sets up everything needed for local development or devcontainer

set -euo pipefail

# Parse arguments
DEVCONTAINER_MODE=false
DRY_RUN=false

show_help() {
  cat <<EOF
Usage: $0 [OPTIONS]

Set up complete development environment for local development or devcontainer.

This script will:
  1. Install uv (Python package manager) if needed
  2. Install Python 3.12+ if needed (local dev only, via uv)
  3. Install external build tools (shellcheck, shfmt) from pyproject.toml
  4. Install Python dependencies (uv sync --all-groups)
  5. Install tox globally for test orchestration
  6. Install pre-commit hooks
  7. Verify installation

Options:
  --devcontainer    Run in devcontainer mode (uses vscode user paths)
  --dry-run         Show commands without executing them
  -h, --help        Show this help message and exit

Examples:
  $0                      # Local development setup
  $0 --devcontainer       # Devcontainer setup
  $0 --dry-run            # Preview what would be done

After setup, verify with:
  ./scripts/check-environment.sh
EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --devcontainer)
      DEVCONTAINER_MODE=true
      shift
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    -h | --help)
      show_help
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      show_help
      exit 1
      ;;
  esac
done

# Helper function to run commands
run_cmd() {
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "[DRY RUN] $*"
  else
    "$@"
  fi
}

echo "🚀 Setting up development environment..."
if [[ "$DEVCONTAINER_MODE" == "true" ]]; then
  echo "   Mode: Devcontainer"
else
  echo "   Mode: Local development"
fi
echo ""

# Step 1: Install uv if not present
echo "📦 Checking uv installation..."
if ! command -v uv &>/dev/null; then
  echo "   Installing uv..."
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "[DRY RUN] curl -LsSf https://astral.sh/uv/install.sh | sh"
  else
    curl -LsSf https://astral.sh/uv/install.sh | sh
  fi

  if [[ "$DEVCONTAINER_MODE" == "true" ]]; then
    export PATH="/home/vscode/.cargo/bin:/home/vscode/.local/bin:$PATH"
  else
    export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"
  fi
  echo "   ✓ uv installed"
else
  echo "   ✓ uv already installed ($(uv --version))"
fi
echo ""

# Step 1.5: Verify ~/.local/bin is on PATH
echo "🔍 Verifying ~/.local/bin is on PATH..."
LOCAL_BIN="$HOME/.local/bin"
if [[ ":$PATH:" != *":$LOCAL_BIN:"* ]]; then
  echo "   ⚠️  WARNING: $LOCAL_BIN is not on PATH"
  echo "   Tools installed to ~/.local/bin will not be found!"
  echo ""
  echo "   To fix, add this to your shell profile (~/.bashrc or ~/.zshrc):"
  echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
  echo ""
  echo "   Then run: source ~/.bashrc  (or source ~/.zshrc)"
  echo ""
  # Don't fail - just warn
else
  echo "   ✓ ~/.local/bin is on PATH"
fi
echo ""

# Step 2: Ensure correct Python version (local development only)
if [[ "$DEVCONTAINER_MODE" == "false" ]]; then
  echo "🐍 Checking Python installation..."
  REQUIRED_PYTHON="3.12"

  # Check if Python 3.12+ is available
  if command -v python3.12 &>/dev/null; then
    echo "   ✓ Python $REQUIRED_PYTHON already installed ($(python3.12 --version))"
  elif command -v python &>/dev/null && python --version 2>&1 | grep -qE "Python 3\.(1[2-9]|[2-9][0-9])"; then
    echo "   ✓ Python $REQUIRED_PYTHON+ already installed ($(python --version))"
  else
    echo "   Python $REQUIRED_PYTHON not found, installing via uv..."
    run_cmd uv python install $REQUIRED_PYTHON
    echo "   ✓ Python $REQUIRED_PYTHON installed"
  fi

  # Pin Python version for the project
  if [ ! -f .python-version ] || ! grep -qE "^3\.(1[2-9]|[2-9][0-9])" .python-version; then
    echo "   Setting project Python version to $REQUIRED_PYTHON..."
    run_cmd uv python pin $REQUIRED_PYTHON
    echo "   ✓ Python version pinned to $REQUIRED_PYTHON"
  else
    echo "   ✓ Python version already pinned to $(cat .python-version)"
  fi
  echo ""
fi

# Step 3: Fix .venv ownership in devcontainer if needed
if [[ "$DEVCONTAINER_MODE" == "true" ]] && [ -d .venv ]; then
  echo "🔧 Fixing .venv ownership..."
  run_cmd sudo chown -R vscode:vscode .venv
  echo ""
fi

# Step 4: Install Python dependencies
echo "📚 Installing Python dependencies..."
run_cmd uv sync --all-groups
echo "   ✓ Python dependencies installed"
echo ""

# Step 5: Install external build tools
echo "🐚 Installing external build tools..."
if [[ "$DRY_RUN" == "true" ]]; then
  run_cmd uv run python3 "$(dirname "$0")/setup-external-tools.py" --dry-run
else
  run_cmd uv run python3 "$(dirname "$0")/setup-external-tools.py"
fi
echo ""

# Step 6: Install tox globally
echo "🧪 Installing tox globally..."
if command -v tox &>/dev/null; then
  echo "   ✓ tox already installed ($(tox --version | head -1))"
else
  run_cmd uv tool install tox --with tox-uv
  echo "   ✓ tox installed"
fi
echo ""

# Step 7: Install pre-commit hooks
echo "🪝 Configuring pre-commit hooks..."

# Detect if we're in a monorepo (git root is not in current directory)
GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo "")
CURRENT_DIR=$(pwd)

if [[ -n "$GIT_ROOT" ]] && [[ "$GIT_ROOT" != "$CURRENT_DIR" ]]; then
  echo "   ⚠️  Monorepo detected - skipping automatic hook installation"
  echo "   The git root is at: $GIT_ROOT"
  echo "   This project is at: $CURRENT_DIR"
  echo ""
  echo "   To use pre-commit in this monorepo context:"
  echo "   1. Manually install: cd $GIT_ROOT && uv run --with pre-commit --directory $CURRENT_DIR pre-commit install"
  echo "   2. Or run manually: uv run pre-commit run --all-files"
  echo ""
else
  # Standalone repo - install hooks normally
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "[DRY RUN] uv run pre-commit install"
  else
    if run_cmd uv run pre-commit install; then
      echo "   ✓ pre-commit hooks installed"
    else
      echo "   ✗ Failed to install pre-commit hooks"
      echo "   This is usually because:"
      echo "     - Virtual environment not created (uv sync failed?)"
      echo "     - pre-commit not in dependencies"
      echo "   You can manually run: uv run pre-commit install"
      exit 1
    fi
  fi
fi
echo ""

# Step 8: Verify installation
echo "✅ Setup complete! Verification:"
if [[ "$DRY_RUN" == "false" ]]; then
  echo "   Python: $(python3 --version 2>&1 || echo 'not found')"
  echo "   uv: $(uv --version 2>&1 || echo 'not found')"
  echo "   tox: $(tox --version 2>&1 | head -1 || echo 'not found')"
  echo "   shellcheck: $(shellcheck --version 2>&1 | head -n 2 | tail -n 1 || echo 'not found')"
  echo "   shfmt: shfmt $(shfmt --version 2>&1 || echo 'not found')"

  # Verify pre-commit hooks (only check in standalone repo)
  GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo "")
  CURRENT_DIR=$(pwd)

  if [[ -n "$GIT_ROOT" ]] && [[ "$GIT_ROOT" != "$CURRENT_DIR" ]]; then
    echo "   pre-commit hooks: ⚠️  skipped (monorepo - manual setup required)"
  elif [ -f .git/hooks/pre-commit ]; then
    echo "   pre-commit hooks: ✓ installed"
  else
    echo "   pre-commit hooks: ✗ NOT installed (this is a problem!)"
  fi
fi
echo ""
echo "🎉 Environment is ready! You can now:"
echo "   - Run tests: tox"
echo "   - Check environment: ./scripts/check-environment.sh"
echo "   - Run pre-commit: uv run pre-commit run --all-files"
echo "   - Use doctk: uv run doctk --help"
