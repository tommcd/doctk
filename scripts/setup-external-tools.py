#!/usr/bin/env python3
"""
Setup external tools from Markdown plugins.

Tool definitions are read from scripts/tools/*.md with versions from pyproject.toml.

Usage:
    ./scripts/setup-external-tools.py           # Install all tools
    ./scripts/setup-external-tools.py --dry-run # Preview commands
    ./scripts/setup-external-tools.py --tool hadolint  # Install specific tool
    ./scripts/setup-external-tools.py --help    # Show help
"""

import sys
from pathlib import Path

# Import from doctk.tools package
try:
    from doctk.tools import ToolManager
except ImportError:
    print(
        "Error: doctk.tools package not found.\nInstall dependencies with: uv sync --all-groups",
        file=sys.stderr,
    )
    sys.exit(1)

import argparse

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
TOOLS_DIR = SCRIPT_DIR / "tools"


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Install external tools from Markdown plugins",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s              # Install all tools
  %(prog)s --dry-run    # Preview what would be installed
  %(prog)s --tool hadolint  # Install only hadolint

Tool versions are defined in:
1. Markdown frontmatter (default)
2. pyproject.toml [tool.external-tools] (override)

After installation, verify with:
  ./scripts/check-environment.sh

For more information:
  See scripts/tools/TEMPLATE.md for example plugin
        """,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show commands without executing them",
    )
    parser.add_argument(
        "--tool",
        metavar="NAME",
        help="Install only the specified tool (e.g., hadolint)",
    )

    args = parser.parse_args()

    # Initialize manager
    manager = ToolManager(tools_dir=TOOLS_DIR, project_root=PROJECT_ROOT)

    # Install specific tool or all tools
    if args.tool:
        plugin = manager.get_tool(args.tool)
        if not plugin:
            print(f"✗ Tool '{args.tool}' not found in {TOOLS_DIR}", file=sys.stderr)
            return 1

        try:
            version = plugin.get_version_spec()
            print(f"Installing {plugin.name} {version}...")
            if plugin.install(version=version, dry_run=args.dry_run):
                print(f"  ✓ {plugin.name} installed")
                return 0
            else:
                print(f"  ✗ {plugin.name} installation failed", file=sys.stderr)
                return 1
        except Exception as e:
            print(f"✗ {plugin.name}: {e}", file=sys.stderr)
            return 1
    else:
        # Install all tools
        installed = manager.install_all(dry_run=args.dry_run)
        return 0 if installed > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
