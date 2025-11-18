#!/bin/bash
# Check if development environment is ready to build/test/run the project

set -e

show_help() {
  cat <<EOF
Usage: $0 [OPTIONS]

Check if development environment is ready to build/test/run the project.

Verifies:
  - Python 3.10+
  - uv package manager
  - External tools (shellcheck, shfmt, taplo, lychee, markdownlint-cli2, hadolint) match pyproject.toml versions
  - git version control
  - Python dependencies installed (pre-commit, tox, mdformat available)

Options:
  -h, --help    Show this help message and exit

Exit codes:
  0 - Environment is ready (can run 'tox' successfully)
  1 - One or more requirements missing or wrong version

Examples:
  $0           # Check environment
  $0 --help    # Show this help
EOF
}

# Parse arguments
if [[ "${1:-}" =~ ^(-h|--help)$ ]]; then
  show_help
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Track failures
FAILED=0

echo -e "${BLUE}Checking development environment...${NC}"
echo ""

# ============================================================================
# Python 3.10+
# ============================================================================
echo -e "${BLUE}Python:${NC}"

# Check for .python-version file (created by uv python pin)
if [ -f .python-version ]; then
  PINNED_VERSION=$(cat .python-version)
  echo -e "${GREEN}✓${NC} Project pinned to Python $PINNED_VERSION (.python-version)"
fi

if command -v python3 >/dev/null 2>&1; then
  PYTHON_VERSION=$(python3 --version 2>&1)
  echo -e "${GREEN}✓${NC} $PYTHON_VERSION"

  # Check version >= 3.10
  PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
  PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
  if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]; then
    echo -e "${RED}  ✗ Python 3.10+ required (found 3.$PYTHON_MINOR)${NC}"
    FAILED=1
  fi
else
  echo -e "${RED}✗ python3: not installed${NC}"
  echo -e "  ${YELLOW}Note: setup-environment.sh can install Python via uv${NC}"
  FAILED=1
fi
echo ""

# ============================================================================
# uv package manager
# ============================================================================
echo -e "${BLUE}Package Manager:${NC}"
if command -v uv >/dev/null 2>&1; then
  UV_VERSION=$(uv --version 2>&1)
  echo -e "${GREEN}✓${NC} $UV_VERSION"
else
  echo -e "${RED}✗ uv: not installed${NC}"
  echo -e "  Install: ${YELLOW}curl -LsSf https://astral.sh/uv/install.sh | sh${NC}"
  FAILED=1
fi
echo ""

# ============================================================================
# External tools - delegated to check-tools.py (plugin framework)
# ============================================================================
echo -e "${BLUE}External Tools:${NC}"

# Use the plugin framework to check all external tools
# This ensures single source of truth for version checking
if uv run python "${SCRIPT_DIR}/check-tools.py" >/dev/null 2>&1; then
  # Tools are installed and correct versions - show output
  uv run python "${SCRIPT_DIR}/check-tools.py"
else
  # Tools are missing or wrong versions - show output and fail
  uv run python "${SCRIPT_DIR}/check-tools.py"
  FAILED=1
fi

echo ""

# ============================================================================
# Git version control and pre-commit hooks
# ============================================================================
echo -e "${BLUE}Version Control:${NC}"
if command -v git >/dev/null 2>&1; then
  GIT_VERSION=$(git --version 2>&1)
  echo -e "${GREEN}✓${NC} $GIT_VERSION"
else
  echo -e "${RED}✗ git: not installed${NC}"
  FAILED=1
fi

# Check if pre-commit hooks are installed (skip check in monorepo)
GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo "")
CURRENT_DIR=$(pwd)

if [[ -n "$GIT_ROOT" ]] && [[ "$GIT_ROOT" != "$CURRENT_DIR" ]]; then
  echo -e "${YELLOW}⚠${NC} pre-commit hooks: skipped (monorepo - manual setup required)"
  echo -e "   ${YELLOW}To use pre-commit, run manually: uv run pre-commit run --all-files${NC}"
elif [ -f .git/hooks/pre-commit ]; then
  echo -e "${GREEN}✓${NC} pre-commit hooks: installed"
else
  echo -e "${RED}✗${NC} pre-commit hooks: NOT installed"
  echo -e "   ${YELLOW}This means commits won't be validated automatically!${NC}"
  echo -e "   ${YELLOW}Run: uv run pre-commit install${NC}"
  FAILED=1
fi
echo ""

# ============================================================================
# Python dependencies (pre-commit, tox)
# ============================================================================
echo -e "${BLUE}Python Dependencies:${NC}"

# Check if Python dependencies are installed
if [ -d "$PROJECT_ROOT/.venv" ] || [ -n "$VIRTUAL_ENV" ]; then
  # Check pre-commit
  if command -v uv >/dev/null 2>&1 && uv run pre-commit --version >/dev/null 2>&1; then
    PRECOMMIT_VERSION=$(uv run pre-commit --version 2>&1)
    echo -e "${GREEN}✓${NC} pre-commit: $PRECOMMIT_VERSION"
  else
    echo -e "${YELLOW}⚠${NC} pre-commit: not available (run 'uv sync --all-groups')"
    FAILED=1
  fi

  # Check tox (can be via uv run or uv tool)
  if command -v tox >/dev/null 2>&1; then
    TOX_VERSION=$(tox --version 2>&1 | head -n 1)
    echo -e "${GREEN}✓${NC} tox: $TOX_VERSION"
  elif command -v uv >/dev/null 2>&1 && uv run tox --version >/dev/null 2>&1; then
    TOX_VERSION=$(uv run tox --version 2>&1 | head -n 1)
    echo -e "${GREEN}✓${NC} tox: $TOX_VERSION (via uv)"
  else
    echo -e "${YELLOW}⚠${NC} tox: not available (install with 'uv tool install tox --with tox-uv')"
    FAILED=1
  fi

  # Check mdformat (needed for docs tox environment)
  if command -v uv >/dev/null 2>&1 && uv run mdformat --version >/dev/null 2>&1; then
    MDFORMAT_VERSION=$(uv run mdformat --version 2>&1)
    echo -e "${GREEN}✓${NC} mdformat: $MDFORMAT_VERSION"
  else
    echo -e "${YELLOW}⚠${NC} mdformat: not available (run 'uv sync --all-groups')"
    FAILED=1
  fi
else
  echo -e "${YELLOW}⚠${NC} Python dependencies not installed"
  echo -e "  Run: ${YELLOW}uv sync --all-groups${NC}"
  FAILED=1
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ $FAILED -eq 0 ]; then
  echo -e "${GREEN}✓ Environment ready!${NC}"
  echo ""
  echo -e "You can now run: ${YELLOW}tox${NC}"
  exit 0
else
  echo -e "${RED}✗ Environment not ready${NC}"
  echo ""
  echo -e "${BLUE}To fix:${NC}"
  echo -e "  Run: ${YELLOW}./scripts/setup-environment.sh${NC}"
  echo ""
  echo -e "  This will install everything: uv, external tools, Python deps, tox, and pre-commit hooks"
  exit 1
fi
