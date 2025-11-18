#!/bin/bash
# Clean setup script - simulates a fresh clone environment

set -e

show_help() {
  cat <<EOF
Usage: $0 [OPTIONS]

Remove all generated files and caches to simulate a fresh clone environment.

Removes:
  - Virtual environment (.venv)
  - Tox environments (.tox)
  - Python caches (__pycache__, .pytest_cache)
  - Build artifacts (dist/, build/, *.egg-info)
  - Pre-commit git hooks
  - Coverage files
  - Ruff cache
  - Test output directories

Options:
  --deep        Also remove global pre-commit cache (~/.cache/pre-commit/)
                Warning: This affects all projects using pre-commit
  --tools       Also uninstall external tools (shellcheck, shfmt, etc.)
                Warning: Requires sudo and affects system-wide tools
  -h, --help    Show this help message and exit

Examples:
  $0             # Clean project only (safe)
  $0 --deep      # Also clear global pre-commit cache
  $0 --tools     # Also uninstall external tools
  $0 --deep --tools # Full cleanup (project + cache + tools)

After cleaning, set up the project with:
  ./scripts/setup-environment.sh  # Install build tools (shellcheck, shfmt)
  uv sync --all-groups            # Install Python dependencies
  uv run pre-commit install       # Install git hooks
  tox                             # Run tests
EOF
}

# Parse arguments
DEEP_CLEAN=false
CLEAN_TOOLS=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h | --help)
      show_help
      exit 0
      ;;
    --deep)
      DEEP_CLEAN=true
      shift
      ;;
    --tools)
      CLEAN_TOOLS=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      show_help
      exit 1
      ;;
  esac
done

if [[ "$DEEP_CLEAN" == "true" ]] && [[ "$CLEAN_TOOLS" == "true" ]]; then
  echo "🧹 Full clean (project + global cache + external tools)..."
elif [[ "$DEEP_CLEAN" == "true" ]]; then
  echo "🧹 Deep cleaning project (including global pre-commit cache)..."
elif [[ "$CLEAN_TOOLS" == "true" ]]; then
  echo "🧹 Cleaning project and uninstalling external tools..."
else
  echo "🧹 Cleaning up project to simulate fresh clone..."
fi

# Remove virtual environments
echo "  Removing .venv/ .uv-cache/"
rm -rf .venv .uv-cache

# Remove tox environments
echo "  Removing .tox/"
rm -rf .tox

# Remove pytest cache
echo "  Removing .pytest_cache/"
rm -rf .pytest_cache
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

# Remove Python cache
echo "  Removing __pycache__/"
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Remove Python build artifacts
echo "  Removing build artifacts"
rm -rf build/ dist/ ./*.egg-info .eggs/
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

# Remove pre-commit git hooks (repository-specific)
echo "  Removing pre-commit git hooks"
rm -f .git/hooks/pre-commit .git/hooks/commit-msg .git/hooks/pre-push 2>/dev/null || true

# Optionally remove global pre-commit cache (only with --deep flag)
if [[ "$DEEP_CLEAN" == "true" ]]; then
  echo "  Removing global pre-commit cache (~/.cache/pre-commit/)"
  rm -rf ~/.cache/pre-commit/ 2>/dev/null || true
fi

# Remove coverage files if present
echo "  Removing coverage files"
rm -f .coverage
rm -rf htmlcov/
rm -rf reports/

# Remove ruff cache
echo "  Removing ruff cache"
rm -rf .ruff_cache/

# Remove test outputs
echo "  Removing test output files"
rm -rf tests/e2e/output/
rm -rf tests/e2e/output_subprocess/
rm -rf tests/e2e/output_bash/

# Generated site files
echo "  Removing generated site files"
rm -rf site/

# Optionally uninstall external tools (only with --tools flag)
if [[ "$CLEAN_TOOLS" == "true" ]]; then
  echo ""
  echo "🗑️  Uninstalling external tools..."
  # Use the Python clean-tools.py script with --force to skip confirmation
  if python3 "$(dirname "$0")/clean-tools.py" --force; then
    echo "  ✓ External tools uninstalled"
  else
    echo "  ⚠️  Some tools may have failed to uninstall (sudo required)"
  fi
fi

echo ""
if [[ "$DEEP_CLEAN" == "true" ]] && [[ "$CLEAN_TOOLS" == "true" ]]; then
  echo "✅ Full clean complete! Project, global caches, and external tools cleared."
elif [[ "$DEEP_CLEAN" == "true" ]]; then
  echo "✅ Deep clean complete! Project and global caches cleared."
elif [[ "$CLEAN_TOOLS" == "true" ]]; then
  echo "✅ Clean complete! Project and external tools cleared."
else
  echo "✅ Clean complete! Project is now in a fresh-clone state."
fi
echo ""
echo "💡 Tip: Run './scripts/setup-environment.sh' to set up the project"
