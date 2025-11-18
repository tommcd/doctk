#!/usr/bin/env python3
"""
Sync pre-commit hook versions with pyproject.toml build tools.

This script updates .pre-commit-config.yaml to use the same tool versions
defined in pyproject.toml [tool.external-tools].
"""

import re
import sys
from pathlib import Path

import tomllib

PROJECT_ROOT = Path(__file__).parent.parent
PYPROJECT_TOML = PROJECT_ROOT / "pyproject.toml"
PRECOMMIT_CONFIG = PROJECT_ROOT / ".pre-commit-config.yaml"


def load_tool_versions():
    """Load tool versions from pyproject.toml."""
    with open(PYPROJECT_TOML, "rb") as f:
        config = tomllib.load(f)

    tools = config.get("tool", {}).get("external-tools", {})

    if not tools:
        print("Error: No external-tools found in pyproject.toml")
        sys.exit(1)

    return tools


def update_precommit_config(tools):
    """Update .pre-commit-config.yaml with versions from pyproject.toml."""
    with open(PRECOMMIT_CONFIG) as f:
        content = f.read()

    original_content = content

    # Update shellcheck-py version
    if "shellcheck" in tools:
        shellcheck_ver = tools["shellcheck"]
        # Match the repo and update the rev line
        pattern = (
            r"(- repo: https://github\.com/shellcheck-py/shellcheck-py"
            r"\s+rev: )v[\d\.]+"
        )
        replacement = rf"\1v{shellcheck_ver}.1"  # shellcheck-py adds .1 suffix
        content = re.sub(pattern, replacement, content)

    # Update shfmt version
    if "shfmt" in tools:
        shfmt_ver = tools["shfmt"]
        # Match the repo and update the rev line
        pattern = (
            r"(- repo: https://github\.com/scop/pre-commit-shfmt"
            r"\s+rev: )v[\d\.]+-\d+"
        )
        replacement = rf"\1v{shfmt_ver}-1"  # pre-commit-shfmt adds -1 suffix
        content = re.sub(pattern, replacement, content)

    if content != original_content:
        with open(PRECOMMIT_CONFIG, "w") as f:
            f.write(content)
        print("✓ Updated .pre-commit-config.yaml with versions from pyproject.toml")
        return True
    else:
        print("✓ .pre-commit-config.yaml already up to date")
        return False


def main():
    """Main entry point."""
    print("🔄 Syncing pre-commit versions from pyproject.toml...")
    tools = load_tool_versions()

    print(f"  shellcheck: {tools.get('shellcheck')}")
    print(f"  shfmt: {tools.get('shfmt')}")

    updated = update_precommit_config(tools)

    if updated:
        print("\nRun 'pre-commit autoupdate' if you want to update other hooks.")
    else:
        print("\nNo changes needed.")


if __name__ == "__main__":
    main()
