#!/usr/bin/env python3
"""
Validate tool plugin Markdown files.

Checks that plugin files have:
- Required code blocks (check-version, install, uninstall)
- Valid repository URLs
- Proper structure and sections
- No typos in code block labels

Exit codes:
    0 - All plugins valid
    1 - One or more plugins invalid
    2 - No plugins found or script error
"""

import argparse
import sys
from pathlib import Path

# Import from doctk.tools package
try:
    from doctk.tools import Colors, ToolPlugin, validate_plugin
except ImportError:
    print(
        "Error: doctk.tools package not found.\nInstall dependencies with: uv sync --all-groups",
        file=sys.stderr,
    )
    sys.exit(2)

SCRIPT_DIR = Path(__file__).parent


def main():
    parser = argparse.ArgumentParser(
        description="Validate tool plugin Markdown files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--tool",
        help="Validate specific tool only (default: all tools)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors (fail on warnings)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only show summary, not individual issues",
    )

    args = parser.parse_args()

    # Find all plugin files
    tools_dir = SCRIPT_DIR / "tools"
    tool_files = [f for f in tools_dir.glob("*.md") if f.name != "TEMPLATE.md"]

    if not tool_files:
        print(f"{Colors.RED}✗{Colors.NC} No plugin files found in {tools_dir}")
        return 2

    # Filter by specific tool if requested
    if args.tool:
        tool_files = [f for f in tool_files if f.stem == args.tool]
        if not tool_files:
            print(f"{Colors.RED}✗{Colors.NC} Tool '{args.tool}' not found")
            return 2

    print(f"Validating {len(tool_files)} plugin(s)...\n")

    # Validate each plugin
    valid_count = 0
    invalid_plugins = []

    for tool_file in sorted(tool_files):
        plugin = ToolPlugin(tool_file)
        is_valid, issues = validate_plugin(plugin)

        # In strict mode, treat warnings as errors
        if args.strict:
            errors = issues
            is_valid = len(errors) == 0
        else:
            errors = [issue for issue in issues if not issue.startswith("⚠")]
            is_valid = len(errors) == 0

        if is_valid:
            if not args.quiet:
                print(f"{Colors.GREEN}✓{Colors.NC} {tool_file.name} - All checks passed")
            valid_count += 1
        else:
            if not args.quiet:
                issue_word = "issue" if len(issues) == 1 else "issues"
                print(
                    f"{Colors.RED}✗{Colors.NC} {tool_file.name} - {len(issues)} {issue_word} found:"
                )

                for issue in issues:
                    if issue.startswith("⚠"):
                        print(f"  {Colors.YELLOW}{issue}{Colors.NC}")
                    else:
                        print(f"  {Colors.RED}✗{Colors.NC} {issue}")

            invalid_plugins.append(tool_file.name)

        if not args.quiet and not is_valid:
            print()  # Blank line between plugins

    # Summary
    print(f"\nValidation: {valid_count}/{len(tool_files)} plugins passed")

    if invalid_plugins:
        print(f"\n{Colors.RED}Invalid plugins:{Colors.NC}")
        for name in invalid_plugins:
            print(f"  - {name}")
        return 1

    print(f"\n{Colors.GREEN}✓ All plugins valid{Colors.NC}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
