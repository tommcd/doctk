#!/usr/bin/env python3
"""Display all tox environment commands in a clean, readable format.

Usage:
    python scripts/show-tox-commands.py
    uv run scripts/show-tox-commands.py
"""

import re
import sys
from pathlib import Path


def parse_tox_ini(tox_path: Path) -> dict[str, dict]:
    """Parse tox.ini and extract environment information."""
    if not tox_path.exists():
        print(f"Error: {tox_path} not found", file=sys.stderr)
        sys.exit(1)

    content = tox_path.read_text()
    environments = {}
    current_env = None
    current_section = None

    for line in content.splitlines():
        # Match [testenv:name] sections
        env_match = re.match(r"^\[testenv:([^\]]+)\]", line)
        if env_match:
            current_env = env_match.group(1)
            current_section = None
            environments[current_env] = {
                "description": "",
                "commands": [],
            }
            continue

        # Skip non-testenv sections
        if re.match(r"^\[(?!testenv)", line):
            current_env = None
            continue

        if current_env is None:
            continue

        # Parse description
        if line.startswith("description = "):
            environments[current_env]["description"] = line.split("=", 1)[1].strip()
            continue

        # Parse commands section
        if line.startswith("commands"):
            current_section = "commands"
            # Check if command is on same line
            if "=" in line:
                cmd = line.split("=", 1)[1].strip()
                if cmd:
                    environments[current_env]["commands"].append(cmd)
            continue

        # Continue parsing commands (indented lines)
        if current_section == "commands" and line.startswith("    "):
            cmd = line.strip()
            if cmd and not cmd.startswith("#"):
                environments[current_env]["commands"].append(cmd)
        elif line and not line.startswith(" "):
            # New section started
            current_section = None

    return environments


def clean_command(cmd: str) -> str:
    """Remove bash -c wrapper and quotes from command."""
    # Remove bash -c 'command'
    if cmd.startswith("bash -c "):
        cmd = cmd[8:].strip()
        # Remove surrounding quotes
        if (cmd.startswith("'") and cmd.endswith("'")) or (
            cmd.startswith('"') and cmd.endswith('"')
        ):
            cmd = cmd[1:-1]
    return cmd


def display_environments(environments: dict[str, dict], clean: bool = True) -> None:
    """Display environment information in a readable format."""
    if not environments:
        print("No testenv environments found in tox.ini")
        return

    print("=" * 80)
    print("TOX ENVIRONMENTS AND COMMANDS")
    print("=" * 80)
    print()

    for env_name, info in environments.items():
        # Header
        print(f"[{env_name}]")
        if info["description"]:
            print(f"  Description: {info['description']}")

        # Commands
        if info["commands"]:
            print("  Commands:")
            for cmd in info["commands"]:
                display_cmd = clean_command(cmd) if clean else cmd
                print(f"    • {display_cmd}")
        else:
            print("  Commands: (none)")

        print()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Display tox environment commands in a clean format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show all commands (cleaned)
  python scripts/show-tox-commands.py

  # Show raw commands as they appear in tox.ini
  python scripts/show-tox-commands.py --raw

  # Show only specific environment
  python scripts/show-tox-commands.py --env docs
        """,
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Show raw commands without cleaning bash -c wrappers",
    )
    parser.add_argument(
        "--env",
        metavar="NAME",
        help="Show only specific environment",
    )
    parser.add_argument(
        "--tox-ini",
        type=Path,
        default=Path("tox.ini"),
        help="Path to tox.ini file (default: tox.ini)",
    )

    args = parser.parse_args()

    # Parse tox.ini
    environments = parse_tox_ini(args.tox_ini)

    # Filter to specific environment if requested
    if args.env:
        if args.env in environments:
            environments = {args.env: environments[args.env]}
        else:
            print(f"Error: Environment '{args.env}' not found", file=sys.stderr)
            print(f"Available: {', '.join(sorted(environments.keys()))}")
            sys.exit(1)

    # Display
    display_environments(environments, clean=not args.raw)


if __name__ == "__main__":
    main()
