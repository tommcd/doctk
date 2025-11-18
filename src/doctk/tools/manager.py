#!/usr/bin/env python3
"""
Tool Manager - Orchestrates tool plugin operations.

Provides high-level API for managing external development tools:
- Install all tools from definitions
- Check status of all tools
- Uninstall all tools
- Load version overrides from pyproject.toml
"""

import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore

from .plugin import Colors, ToolPlugin
from .registry import ToolRegistry


class ToolManager:
    """
    Manages external development tools via plugin system.

    Coordinates tool plugins, version resolution, and registry tracking.
    """

    def __init__(
        self,
        tools_dir: Path | str | None = None,
        project_root: Path | None = None,
        registry: ToolRegistry | None = None,
    ):
        """
        Initialize tool manager.

        Args:
            tools_dir: Directory containing tool Markdown files
                      (default: {project_root}/scripts/tools)
            project_root: Project root directory
                         (default: current working directory)
            registry: ToolRegistry instance (default: creates new one)

        Example:
            manager = ToolManager(tools_dir="scripts/tools")
            manager.install_all()
        """
        project_root = Path.cwd() if project_root is None else Path(project_root)
        tools_dir = project_root / "scripts" / "tools" if tools_dir is None else Path(tools_dir)

        self.project_root = project_root
        self.tools_dir = tools_dir
        self.registry = registry or ToolRegistry()

        # Load version overrides from pyproject.toml
        self.version_overrides = self._load_version_overrides()

    def _load_version_overrides(self) -> dict[str, str]:
        """
        Load tool version overrides from pyproject.toml.

        Looks for [tool.external-tools] section:
            [tool.external-tools]
            hadolint = "2.15.0"  # Override default from Markdown

        Returns:
            Dictionary mapping tool name to version override

        Returns empty dict if:
        - pyproject.toml doesn't exist
        - File can't be parsed
        - [tool.external-tools] section doesn't exist
        """
        pyproject_path = self.project_root / "pyproject.toml"

        if not pyproject_path.exists():
            return {}

        try:
            with open(pyproject_path, "rb") as f:
                config = tomllib.load(f)
                return config.get("tool", {}).get("external-tools", {})
        except (OSError, tomllib.TOMLDecodeError):
            return {}

    def _get_tool_plugins(self) -> list[ToolPlugin]:
        """
        Get all tool plugins from tools directory.

        Returns:
            List of ToolPlugin instances (one per .md file)

        Filters out TEMPLATE.md which is documentation only.
        """
        if not self.tools_dir.exists():
            return []

        plugins = []
        for md_file in sorted(self.tools_dir.glob("*.md")):
            # Skip template file
            if md_file.stem == "TEMPLATE":
                continue

            # Get version override if exists
            version_override = self.version_overrides.get(md_file.stem)

            plugin = ToolPlugin(
                md_file,
                version_override=version_override,
                registry=self.registry,
            )
            plugins.append(plugin)

        return plugins

    def install_all(self, dry_run: bool = False) -> int:
        """
        Install all tools from plugins.

        Args:
            dry_run: If True, show what would be done without executing

        Returns:
            Number of tools successfully installed

        Example:
            manager = ToolManager()
            installed = manager.install_all()
            print(f"Installed {installed} tools")
        """
        plugins = self._get_tool_plugins()
        if not plugins:
            print(f"{Colors.YELLOW}No tool plugins found in {self.tools_dir}{Colors.NC}")
            return 0

        installed_count = 0
        for plugin in plugins:
            try:
                version = plugin.get_version_spec()
                print(f"Installing {plugin.name} {version}...")

                if plugin.install(version=version, dry_run=dry_run):
                    installed_count += 1
                    print(f"  {Colors.GREEN}✓{Colors.NC} {plugin.name} installed")
                else:
                    print(
                        f"  {Colors.RED}✗{Colors.NC} {plugin.name} installation failed",
                        file=sys.stderr,
                    )
            except Exception as e:
                print(
                    f"  {Colors.RED}✗{Colors.NC} {plugin.name}: {e}",
                    file=sys.stderr,
                )

        print(f"\nInstalled {installed_count}/{len(plugins)} tools")
        return installed_count

    def check_all(self) -> tuple[int, int]:
        """
        Check status of all tools.

        Returns:
            Tuple of (installed_count, expected_count)

        Example:
            manager = ToolManager()
            installed, total = manager.check_all()
            print(f"{installed}/{total} tools installed")
        """
        plugins = self._get_tool_plugins()
        if not plugins:
            print(f"{Colors.YELLOW}No tool plugins found in {self.tools_dir}{Colors.NC}")
            return (0, 0)

        installed_count = 0
        for plugin in plugins:
            try:
                expected_version = plugin.get_version_spec()
                current_version = plugin.get_version()

                if current_version:
                    is_managed = plugin.is_plugin_managed()
                    location = plugin.get_install_location()

                    if is_managed:
                        if current_version == expected_version:
                            print(f"{Colors.GREEN}✓{Colors.NC} {plugin.name}: {current_version}")
                        else:
                            print(
                                f"{Colors.YELLOW}⚠{Colors.NC} {plugin.name}: {current_version} "
                                f"(expected {expected_version})"
                            )
                        installed_count += 1
                    else:
                        print(f"{Colors.GREEN}✓{Colors.NC} {plugin.name}: {current_version}")
                        print(f"  {Colors.YELLOW}⚠{Colors.NC}  Installed at: {location}")
                        print("     This tool is NOT managed by the plugin system")
                        installed_count += 1
                else:
                    print(
                        f"{Colors.RED}✗{Colors.NC} {plugin.name}: not installed "
                        f"(expected {expected_version})"
                    )
            except Exception as e:
                print(
                    f"{Colors.RED}✗{Colors.NC} {plugin.name}: {e}",
                    file=sys.stderr,
                )

        print(f"\n{installed_count}/{len(plugins)} tools installed")
        return (installed_count, len(plugins))

    def uninstall_all(self, dry_run: bool = False) -> int:
        """
        Uninstall all plugin-managed tools.

        Only uninstalls tools tracked in the registry or in ~/.local/bin/.
        Skips tools installed by other means.

        Args:
            dry_run: If True, show what would be done without executing

        Returns:
            Number of tools successfully uninstalled

        Example:
            manager = ToolManager()
            removed = manager.uninstall_all()
            print(f"Removed {removed} tools")
        """
        plugins = self._get_tool_plugins()
        if not plugins:
            print(f"{Colors.YELLOW}No tool plugins found in {self.tools_dir}{Colors.NC}")
            return 0

        uninstalled_count = 0
        for plugin in plugins:
            if not plugin.is_plugin_managed():
                print(
                    f"{Colors.YELLOW}⊘{Colors.NC} {plugin.name}: "
                    f"not managed by plugin system, skipping"
                )
                continue

            try:
                print(f"Uninstalling {plugin.name}...")
                if plugin.uninstall(dry_run=dry_run):
                    uninstalled_count += 1
                    print(f"  {Colors.GREEN}✓{Colors.NC} {plugin.name} uninstalled")
                else:
                    print(
                        f"  {Colors.RED}✗{Colors.NC} {plugin.name} uninstallation failed",
                        file=sys.stderr,
                    )
            except Exception as e:
                print(
                    f"  {Colors.RED}✗{Colors.NC} {plugin.name}: {e}",
                    file=sys.stderr,
                )

        managed_count = sum(1 for p in plugins if p.is_plugin_managed())
        print(f"\nUninstalled {uninstalled_count}/{managed_count} managed tools")
        return uninstalled_count

    def get_tool(self, name: str) -> ToolPlugin | None:
        """
        Get a specific tool plugin by name.

        Args:
            name: Tool name (e.g., "hadolint")

        Returns:
            ToolPlugin instance or None if not found

        Example:
            manager = ToolManager()
            hadolint = manager.get_tool("hadolint")
            if hadolint:
                print(f"Version: {hadolint.get_version_spec()}")
        """
        tool_path = self.tools_dir / f"{name}.md"
        if not tool_path.exists():
            return None

        version_override = self.version_overrides.get(name)
        return ToolPlugin(
            tool_path,
            version_override=version_override,
            registry=self.registry,
        )
