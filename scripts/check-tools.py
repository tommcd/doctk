#!/usr/bin/env python3
"""
Check external tool versions.

Usage:
    ./scripts/check-tools.py         # Check all tools
    ./scripts/check-tools.py --verbose  # Show registry details

Exit Codes:
    0 - All tools installed
    1 - One or more tools missing
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
        description="Check status of external development tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s              # Check all tools
  %(prog)s --verbose    # Show registry details

Symbols:
  ✓ = Tool installed
  ⚠ = Tool installed but not plugin-managed, or version mismatch
  ✗ = Tool not installed
        """,
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show additional details (registry info, etc.)",
    )

    args = parser.parse_args()

    # Initialize manager
    manager = ToolManager(tools_dir=TOOLS_DIR, project_root=PROJECT_ROOT)

    installed, total = manager.check_all()

    if args.verbose:
        print()
        print("Registry details:")
        registry_tools = manager.registry.list_tools()
        if registry_tools:
            for tool_name in sorted(registry_tools):
                info = manager.registry.get_tool_info(tool_name)
                if info:
                    print(f"  {tool_name}:")
                    print(f"    Version: {info['version']}")
                    print(f"    Location: {info['install_location']}")
                    print(f"    Method: {info['install_method']}")
                    print(f"    Installed: {info['installed_at']}")
        else:
            print("  (empty)")
        print(f"  Registry: {manager.registry.registry_path}")

    # Return exit code: 0 if all installed, 1 if any missing
    return 0 if installed == total else 1


if __name__ == "__main__":
    sys.exit(main())
