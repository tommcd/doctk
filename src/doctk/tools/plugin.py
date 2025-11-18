#!/usr/bin/env python3
"""
Tool plugin framework - Markdown-driven automation.

This module provides a framework for managing external tools through Markdown
plugins. Each tool has a Markdown file that contains:
- YAML frontmatter with tool metadata (version, install_method, etc.)
- Documentation for the tool
- Executable code blocks for checking, installing, and uninstalling
- Manual testing examples

The Markdown serves as both user documentation and automation source.
"""

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from .registry import ToolRegistry


# ANSI color codes for terminal output
class Colors:
    """Terminal color codes."""

    BLUE = "\033[34m"
    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    NC = "\033[0m"  # No Color


@dataclass
class CodeBlock:
    """
    Parsed code block from Markdown.

    Represents a labeled code block extracted from Markdown documentation.
    The label identifies the purpose (check-version, install, uninstall).
    """

    language: str  # e.g., "bash", "sh"
    label: str  # e.g., "check-version", "install", "uninstall"
    code: str  # The actual command(s) to execute


class ToolPlugin:
    """
    Represents a tool plugin from Markdown.

    Parses a Markdown file to extract frontmatter and labeled code blocks,
    provides methods to execute them (check version, install, uninstall).
    """

    def __init__(
        self,
        markdown_path: Path,
        version_override: str | None = None,
        registry: "ToolRegistry | None" = None,
    ):
        """
        Initialize plugin from Markdown file.

        Args:
            markdown_path: Path to the Markdown plugin file
            version_override: Version to use (overrides frontmatter default)
            registry: Optional ToolRegistry for tracking installations
        """
        self.path = markdown_path
        self.name = markdown_path.stem
        self.frontmatter, self.blocks = self._parse_markdown()
        self._version_override = version_override
        self.registry = registry

    def _parse_markdown(self) -> tuple[dict, dict[str, CodeBlock]]:
        """
        Parse Markdown file for frontmatter and labeled code blocks.

        Frontmatter format (YAML):
            ---
            version: "2.14.0"
            install_method: binary
            ---

        Code blocks format:
            ```bash check-version
            command here
            ```

        Returns:
            Tuple of (frontmatter_dict, blocks_dict)
        """
        content = self.path.read_text()
        frontmatter = {}
        blocks = {}

        # Extract YAML frontmatter
        frontmatter_pattern = r"^---\s*\n(.*?)\n---\s*\n"
        frontmatter_match = re.search(frontmatter_pattern, content, re.DOTALL | re.MULTILINE)
        if frontmatter_match:
            try:
                frontmatter = yaml.safe_load(frontmatter_match.group(1)) or {}
            except yaml.YAMLError:
                frontmatter = {}

        # Find code blocks like: ```bash check-version
        # Language: bash, sh, etc.
        # Label: check-version, install, uninstall, etc.
        pattern = r"```(\w+)\s+([a-z-]+)\n(.*?)```"
        for match in re.finditer(pattern, content, re.DOTALL):
            lang, label, code = match.groups()
            blocks[label] = CodeBlock(lang, label, code.strip())

        return frontmatter, blocks

    def get_version_spec(self) -> str:
        """
        Get the version specification for this tool.

        Uses hybrid resolution:
        1. version_override (from pyproject.toml) if provided
        2. frontmatter["version"] from Markdown if available
        3. Raises ValueError if neither exists

        Returns:
            Version string (e.g., "2.14.0")

        Raises:
            ValueError: If no version found
        """
        if self._version_override:
            return self._version_override

        if "version" in self.frontmatter:
            return self.frontmatter["version"]

        raise ValueError(
            f"No version found for {self.name}. "
            f"Add 'version' to frontmatter or provide override in pyproject.toml"
        )

    @property
    def install_method(self) -> str:
        """Get installation method from frontmatter (binary, npm, pip, cargo, etc.)."""
        return self.frontmatter.get("install_method", "unknown")

    def get_version(self) -> str | None:
        """
        Execute check-version block and return version string.

        Returns:
            Version string if installed and detected, None otherwise
        """
        if "check-version" not in self.blocks:
            return None

        block = self.blocks["check-version"]
        result = subprocess.run(  # noqa: S602
            block.code,
            shell=True,
            capture_output=True,
            text=True,
            check=False,
        )

        return result.stdout.strip() if result.returncode == 0 else None

    def get_install_location(self) -> str | None:
        """
        Find where the tool is actually installed.

        Returns:
            Full path to tool binary, or None if not found in PATH
        """
        result = subprocess.run(  # noqa: S602
            f"which {self.name}",
            shell=True,
            capture_output=True,
            text=True,
            check=False,
        )

        return result.stdout.strip() if result.returncode == 0 else None

    def is_plugin_managed(self) -> bool:
        """
        Check if tool is installed in the location managed by this plugin.

        First checks registry (if available), then falls back to path-based check.
        The plugin installs to ~/.local/bin/ (user-local, no sudo required).
        Tools installed in other locations (system package managers, snap,
        /usr/local/bin, npm, etc.) are treated as user-managed and skipped by
        the plugin system unless tracked in registry.

        Returns:
            True if tool is plugin-managed (in registry or in ~/.local/bin/), False otherwise
        """
        # Check registry first (authoritative)
        if self.registry and self.registry.is_registered(self.name):
            # Verify tool still exists at registered location
            location = self.get_install_location()
            if location:
                return True
            else:
                # Tool was registered but no longer exists - clean up registry
                self.registry.unregister_tool(self.name)
                return False

        # Fallback: Path-based check for backwards compatibility
        location = self.get_install_location()
        if not location:
            return False

        # Plugin-managed location (user-local installation)
        local_bin = os.path.expanduser("~/.local/bin/")
        return location.startswith(local_bin)

    def install(self, version: str | None = None, dry_run: bool = False) -> bool:
        """
        Execute install block with version substitution.

        Args:
            version: Version to install (defaults to get_version_spec())
            dry_run: If True, print commands without executing

        Returns:
            True if installation succeeded, False otherwise

        Raises:
            ValueError: If no install block exists in the Markdown
        """
        if "install" not in self.blocks:
            raise ValueError(f"No install block in {self.name}")

        # Use provided version or get from spec
        if version is None:
            version = self.get_version_spec()

        code = self.blocks["install"].code.replace("{VERSION}", version)

        if dry_run:
            print(f"{Colors.YELLOW}[DRY RUN]{Colors.NC} Would execute:")
            print(f"  {code}")
            return True

        result = subprocess.run(  # noqa: S602
            code,
            shell=True,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            print(f"{Colors.RED}Installation failed:{Colors.NC}", file=sys.stderr)
            print(f"  Command: {code}", file=sys.stderr)
            if result.stderr:
                print(f"  Error: {result.stderr}", file=sys.stderr)
            return False

        # Register successful installation
        if self.registry:
            location = self.get_install_location()
            if location:
                self.registry.register_tool(
                    self.name,
                    version,
                    location,
                    install_method=self.install_method,
                )

        return True

    def uninstall(self, dry_run: bool = False) -> bool:
        """
        Execute uninstall block.

        Args:
            dry_run: If True, print commands without executing

        Returns:
            True if uninstallation succeeded, False otherwise
        """
        if "uninstall" not in self.blocks:
            return True  # No uninstall means nothing to clean

        code = self.blocks["uninstall"].code

        if dry_run:
            print(f"{Colors.YELLOW}[DRY RUN]{Colors.NC} Would execute:")
            print(f"  {code}")
            return True

        result = subprocess.run(  # noqa: S602
            code,
            shell=True,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            print(f"{Colors.RED}Uninstallation failed:{Colors.NC}", file=sys.stderr)
            print(f"  Command: {code}", file=sys.stderr)
            if result.stderr:
                print(f"  Error: {result.stderr}", file=sys.stderr)
            return False

        # Unregister after successful uninstallation
        if self.registry:
            self.registry.unregister_tool(self.name)

        return True

    def get_repository_url(self) -> str | None:
        """
        Extract GitHub repository URL from plugin Markdown.

        Looks for line like:
            **Official Repository**: <https://github.com/org/tool>

        Returns:
            GitHub repository URL, or None if not found
        """
        content = self.path.read_text()

        # Pattern: **Official Repository**: <URL>
        # Matches: <https://github.com/owner/repo>
        pattern = r"\*\*Official Repository\*\*:\s*<(https://github\.com/[^>]+)>"
        match = re.search(pattern, content)

        return match.group(1) if match else None

    def verify(self) -> tuple[bool, str | None]:
        """
        Execute verify block to test tool functionality.

        The verify block should run a simple smoke test to confirm the tool
        works correctly after installation. This is more thorough than just
        checking the version.

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
            - (True, None) if verification passed
            - (False, error_msg) if verification failed
            - (True, None) if no verify block exists (verification is optional)

        Example verify blocks:
            - Run tool with --help flag
            - Process a small test file
            - Check tool can access required dependencies
        """
        if "verify" not in self.blocks:
            return (True, None)  # Verification is optional

        block = self.blocks["verify"]
        result = subprocess.run(  # noqa: S602
            block.code,
            shell=True,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            return (True, None)
        else:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            return (False, error_msg)


def format_status(tool: str, message: str, ok: bool = True) -> str:
    """
    Format a status message with color.

    Args:
        tool: Tool name
        message: Status message
        ok: True for success (green), False for failure (red)

    Returns:
        Formatted string with color codes

    Example:
        format_status("hadolint", "2.14.0 installed", ok=True)
        # Returns: "✓ hadolint: 2.14.0 installed" (in green)
    """
    symbol = "✓" if ok else "✗"
    color = Colors.GREEN if ok else Colors.RED
    return f"{color}{symbol}{Colors.NC} {tool}: {message}"


def validate_plugin(plugin: ToolPlugin) -> tuple[bool, list[str]]:
    """
    Validate plugin Markdown file for completeness and correctness.

    Checks:
    1. Required frontmatter fields (version, install_method)
    2. Required code blocks present (check-version, install, uninstall)
    3. Repository URL present and properly formatted
    4. No invalid code block labels (typos)
    5. Code blocks have content (not empty)

    Args:
        plugin: ToolPlugin instance to validate

    Returns:
        Tuple of (is_valid: bool, issues: List[str])
        - is_valid: True if all checks pass
        - issues: List of error/warning messages (empty if valid)

    Example:
        plugin = ToolPlugin(Path("scripts/tools/shellcheck.md"))
        valid, issues = validate_plugin(plugin)
        if not valid:
            for issue in issues:
                print(f"✗ {issue}")
    """
    issues = []

    # Check 1: Required frontmatter fields
    if "version" not in plugin.frontmatter:
        issues.append("Missing required frontmatter field: 'version'")
    if "install_method" not in plugin.frontmatter:
        issues.append("Missing required frontmatter field: 'install_method'")

    # Check 2: Required code blocks
    required_blocks = ["check-version", "install", "uninstall"]
    for block_label in required_blocks:
        if block_label not in plugin.blocks:
            issues.append(f"Missing required code block: '{block_label}'")
        elif not plugin.blocks[block_label].code.strip():
            issues.append(f"Empty code block: '{block_label}'")

    # Check 3: Recommended code blocks (warnings only)
    recommended_blocks = ["verify"]
    for block_label in recommended_blocks:
        if block_label not in plugin.blocks:
            issues.append(f"⚠ Missing recommended code block: '{block_label}' (warning only)")

    # Check 4: Repository URL
    raw_content = plugin.path.read_text()

    # Strip YAML frontmatter if present (delimited by ---)
    content = raw_content
    if raw_content.startswith("---"):
        parts = raw_content.split("---", 2)
        if len(parts) >= 3:
            content = parts[2].lstrip()  # Content after closing ---

    repo_pattern = r"\*\*Official Repository\*\*:\s*<(https://github\.com/[^>]+)>"
    repo_match = re.search(repo_pattern, content)

    if not repo_match:
        issues.append("Missing repository URL (should have '**Official Repository**: <URL>')")
    else:
        repo_url = repo_match.group(1)
        if not repo_url.startswith("https://github.com/"):
            issues.append(f"Invalid repository URL: {repo_url} (must be GitHub HTTPS URL)")

    # Check 5: Invalid/unknown code block labels (potential typos)
    known_labels = {
        "check-version",
        "install",
        "uninstall",
        "verify",
        "install-macos",
        "install-windows",  # Future multi-platform support
    }
    for label in plugin.blocks:
        if label not in known_labels:
            issues.append(f"Unknown code block label: '{label}' (possible typo?)")

    # Check 6: Tool name in title
    first_line = content.split("\n")[0]
    if not first_line.startswith(f"# {plugin.name}"):
        issues.append(f"Plugin file name '{plugin.name}' doesn't match title")

    # Separate errors from warnings
    errors = [issue for issue in issues if not issue.startswith("⚠")]

    # Valid if no errors (warnings are OK)
    is_valid = len(errors) == 0

    return is_valid, issues
