#!/usr/bin/env python3
"""
Tool management system for external tools.

Reads tool definitions from scripts/tools/*.md and manages installation.
This is a simplified inline version of the sstdf-python-standards tool management.
"""

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import tomllib


@dataclass
class ToolPlugin:
    """Represents a tool plugin from a Markdown file."""

    name: str
    path: Path
    default_version: str
    install_method: str
    install_command: str
    check_command: str

    def get_version_spec(self, pyproject_path: Path | None = None) -> str:
        """Get version from pyproject.toml or use default."""
        if pyproject_path and pyproject_path.exists():
            try:
                with open(pyproject_path, "rb") as f:
                    data = tomllib.load(f)
                    external_tools = data.get("tool", {}).get("external-tools", {})
                    if self.name in external_tools:
                        return external_tools[self.name]
            except Exception:  # noqa: S110
                pass
        return self.default_version

    def is_installed(self, version: str | None = None) -> bool:
        """Check if tool is installed."""
        try:
            result = subprocess.run(
                self.check_command.split(),
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                return False

            if version:
                # Check if version matches
                return version in result.stdout or version in result.stderr
            return True
        except FileNotFoundError:
            return False

    def install(self, version: str | None = None, dry_run: bool = False) -> bool:
        """Install the tool."""
        version = version or self.default_version

        # Replace {version} placeholder in install command
        cmd = self.install_command.replace("{version}", version)

        if dry_run:
            print(f"[DRY RUN] {cmd}")
            return True

        try:
            result = subprocess.run(  # noqa: S602
                cmd,
                shell=True,
                check=True,
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            print(f"Error installing {self.name}: {e}", file=sys.stderr)
            if e.stdout:
                print(e.stdout, file=sys.stderr)
            if e.stderr:
                print(e.stderr, file=sys.stderr)
            return False


class ToolManager:
    """Manages external tools from Markdown plugins."""

    def __init__(self, tools_dir: Path, project_root: Path):
        self.tools_dir = tools_dir
        self.project_root = project_root
        self.pyproject_path = project_root / "pyproject.toml"
        self._plugins: dict[str, ToolPlugin] | None = None

    def _parse_plugin(self, md_file: Path) -> ToolPlugin | None:
        """Parse a tool plugin Markdown file."""
        content = md_file.read_text()

        # Extract frontmatter
        frontmatter_match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
        if not frontmatter_match:
            return None

        frontmatter = frontmatter_match.group(1)

        # Parse frontmatter fields
        name_match = re.search(r"^name:\s*(.+)$", frontmatter, re.MULTILINE)
        version_match = re.search(r"^version:\s*(.+)$", frontmatter, re.MULTILINE)
        method_match = re.search(r"^install_method:\s*(.+)$", frontmatter, re.MULTILINE)

        if not (name_match and version_match and method_match):
            return None

        name = name_match.group(1).strip()
        version = version_match.group(1).strip()
        method = method_match.group(1).strip()

        # Extract install command from code block
        install_match = re.search(r"```(?:bash|sh)\n# Install\n(.*?)\n```", content, re.DOTALL)
        if not install_match:
            return None

        install_cmd = install_match.group(1).strip()

        # Extract check command from code block
        check_match = re.search(r"```(?:bash|sh)\n# Check\n(.*?)\n```", content, re.DOTALL)
        if not check_match:
            return None

        check_cmd = check_match.group(1).strip()

        return ToolPlugin(
            name=name,
            path=md_file,
            default_version=version,
            install_method=method,
            install_command=install_cmd,
            check_command=check_cmd,
        )

    def _load_plugins(self) -> dict[str, ToolPlugin]:
        """Load all tool plugins from Markdown files."""
        if self._plugins is not None:
            return self._plugins

        self._plugins = {}
        if not self.tools_dir.exists():
            return self._plugins

        for md_file in self.tools_dir.glob("*.md"):
            if md_file.name == "TEMPLATE.md":
                continue

            plugin = self._parse_plugin(md_file)
            if plugin:
                self._plugins[plugin.name] = plugin

        return self._plugins

    def get_tool(self, name: str) -> ToolPlugin | None:
        """Get a specific tool plugin."""
        plugins = self._load_plugins()
        return plugins.get(name)

    def list_tools(self) -> list[ToolPlugin]:
        """List all available tool plugins."""
        plugins = self._load_plugins()
        return list(plugins.values())

    def install_all(self, dry_run: bool = False) -> int:
        """Install all tools. Returns number of tools installed."""
        plugins = self._load_plugins()
        if not plugins:
            print("No tool plugins found", file=sys.stderr)
            return 0

        installed = 0
        for plugin in plugins.values():
            version = plugin.get_version_spec(self.pyproject_path)
            print(f"Installing {plugin.name} {version}...")

            if plugin.install(version=version, dry_run=dry_run):
                print(f"  ✓ {plugin.name} installed")
                installed += 1
            else:
                print(f"  ✗ {plugin.name} installation failed", file=sys.stderr)

        return installed

    def check_all(self) -> dict[str, tuple[bool, str]]:
        """Check all tools. Returns dict of {tool_name: (is_installed, version)}."""
        plugins = self._load_plugins()
        results = {}

        for plugin in plugins.values():
            expected_version = plugin.get_version_spec(self.pyproject_path)
            is_installed = plugin.is_installed(expected_version)
            results[plugin.name] = (is_installed, expected_version)

        return results
