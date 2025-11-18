#!/usr/bin/env python3
"""
Tool Installation Registry.

Tracks tools installed by the plugin system to solve detection issues for
tools installed to dynamic paths (npm, pip, cargo, etc.).

Registry location: ~/.local/share/doctk/tool-registry.json
"""

import json
from datetime import datetime
from pathlib import Path
from typing import TypedDict


class ToolInfo(TypedDict):
    """Tool metadata stored in registry."""

    version: str
    installed_by: str
    installed_at: str
    install_location: str
    install_method: str


class ToolRegistry:
    """
    Persistent registry tracking plugin-installed tools.

    Location: ~/.local/share/doctk/tool-registry.json
    Scope: User-global registry (not per-project).

    Design: Tools installed to ~/.local/bin/ are user-global and shared
    across all projects. Goal is alignment on latest tool versions.
    For project isolation, use DevContainers.
    """

    def __init__(self):
        """Initialize registry with default location."""
        self.registry_path = Path.home() / ".local" / "share" / "doctk" / "tool-registry.json"

    def load(self) -> dict:
        """
        Load registry from disk.

        Returns:
            Registry data dictionary, or empty structure if file doesn't exist

        Example:
            {
                "schema_version": "1.0",
                "tools": {
                    "hadolint": {
                        "version": "2.14.0",
                        "installed_by": "plugin",
                        "installed_at": "2025-10-17T10:30:00",
                        "install_location": "/home/user/.local/bin/hadolint",
                        "install_method": "binary"
                    }
                }
            }
        """
        if not self.registry_path.exists():
            return {"schema_version": "1.0", "tools": {}}

        try:
            with open(self.registry_path) as f:
                data = json.load(f)
                # Ensure schema_version exists
                if "schema_version" not in data:
                    data["schema_version"] = "1.0"
                # Ensure tools dict exists
                if "tools" not in data:
                    data["tools"] = {}
                return data
        except (OSError, json.JSONDecodeError):
            # Corrupted registry - return empty
            return {"schema_version": "1.0", "tools": {}}

    def save(self, data: dict) -> None:
        """
        Save registry to disk.

        Args:
            data: Registry data dictionary

        Creates parent directory if it doesn't exist.
        """
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, "w") as f:
            json.dump(data, f, indent=2)

    def register_tool(
        self, name: str, version: str, location: str, install_method: str = "unknown"
    ) -> None:
        """
        Record that plugin installed a tool.

        Args:
            name: Tool name (e.g., "hadolint")
            version: Installed version (e.g., "2.14.0")
            location: Full path where tool is installed
            install_method: Installation method (binary, npm, pip, cargo, etc.)

        Example:
            registry.register_tool("hadolint", "2.14.0", "/home/user/.local/bin/hadolint", "binary")
        """
        data = self.load()

        data["tools"][name] = {
            "version": version,
            "installed_by": "plugin",
            "installed_at": datetime.now().isoformat(),
            "install_location": location,
            "install_method": install_method,
        }

        self.save(data)

    def unregister_tool(self, name: str) -> None:
        """
        Remove tool from registry (after uninstall).

        Args:
            name: Tool name to unregister

        Does nothing if tool not in registry.
        """
        data = self.load()

        if name in data["tools"]:
            del data["tools"][name]
            self.save(data)

    def is_registered(self, name: str) -> bool:
        """
        Check if tool is in registry.

        Args:
            name: Tool name

        Returns:
            True if tool is registered, False otherwise
        """
        data = self.load()
        return name in data["tools"]

    def get_tool_info(self, name: str) -> ToolInfo | None:
        """
        Get metadata for registered tool.

        Args:
            name: Tool name

        Returns:
            ToolInfo dictionary or None if not registered

        Example:
            info = registry.get_tool_info("hadolint")
            print(f"Version: {info['version']}")
            print(f"Location: {info['install_location']}")
        """
        data = self.load()
        return data["tools"].get(name)

    def list_tools(self) -> list[str]:
        """
        List all registered tools.

        Returns:
            List of tool names

        Example:
            tools = registry.list_tools()
            # ['hadolint', 'shellcheck', 'shfmt', ...]
        """
        data = self.load()
        return list(data["tools"].keys())

    def clear(self) -> None:
        """
        Clear all registered tools.

        Useful for testing or cleanup after moving to different tool management system.
        """
        data = {"schema_version": "1.0", "tools": {}}
        self.save(data)
