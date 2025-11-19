"""Configuration management for doctk Language Server.

This module handles configuration loading, validation, and application for the LSP server.
It supports dynamic configuration updates without requiring a server restart.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class TraceLevel(Enum):
    """LSP trace level for debugging."""

    OFF = "off"
    MESSAGES = "messages"
    VERBOSE = "verbose"


@dataclass
class LSPConfiguration:
    """Configuration settings for the doctk language server.

    This class holds all configurable settings for the LSP server, with
    validation and default values. Settings can be updated dynamically
    without requiring a server restart.
    """

    # LSP trace level for debugging
    trace: TraceLevel = TraceLevel.OFF

    # Maximum number of completion items to return
    max_completion_items: int = 50

    # Whether the language server is enabled
    enabled: bool = True

    # Python command or path (used by client, not server)
    python_command: str = "python3"

    # Internal tracking
    _warnings: list[str] = field(default_factory=list, init=False, repr=False)

    @classmethod
    def from_dict(cls, config_dict: dict[str, Any]) -> LSPConfiguration:
        """
        Create configuration from a dictionary.

        Validates all settings and uses defaults for invalid values.
        Warnings are collected for invalid settings.

        Args:
            config_dict: Configuration dictionary from LSP client

        Returns:
            LSPConfiguration instance with validated settings

        Example:
            >>> config = LSPConfiguration.from_dict({
            ...     "trace": "verbose",
            ...     "maxCompletionItems": 100
            ... })
            >>> config.trace
            <TraceLevel.VERBOSE: 'verbose'>
            >>> config.max_completion_items
            100
        """
        instance = cls()

        # Validate and set trace level
        if "trace" in config_dict:
            trace_value = config_dict["trace"]
            try:
                instance.trace = TraceLevel(trace_value)
            except ValueError:
                instance._warnings.append(
                    f"Invalid trace level '{trace_value}'. "
                    f"Valid values are: {[t.value for t in TraceLevel]}. "
                    f"Using default: '{TraceLevel.OFF.value}'"
                )
                logger.warning(instance._warnings[-1])

        # Validate and set max completion items
        if "maxCompletionItems" in config_dict:
            max_items = config_dict["maxCompletionItems"]
            if isinstance(max_items, int) and max_items > 0:
                instance.max_completion_items = max_items
            else:
                instance._warnings.append(
                    f"Invalid maxCompletionItems '{max_items}'. "
                    "Must be a positive integer. "
                    "Using default: 50"
                )
                logger.warning(instance._warnings[-1])

        # Validate and set enabled
        if "enabled" in config_dict:
            enabled = config_dict["enabled"]
            if isinstance(enabled, bool):
                instance.enabled = enabled
            else:
                instance._warnings.append(
                    f"Invalid enabled value '{enabled}'. "
                    "Must be a boolean. "
                    "Using default: True"
                )
                logger.warning(instance._warnings[-1])

        # Python command (informational only, not validated by server)
        if "pythonCommand" in config_dict:
            python_cmd = config_dict["pythonCommand"]
            if isinstance(python_cmd, str):
                instance.python_command = python_cmd

        return instance

    def get_warnings(self) -> list[str]:
        """
        Get list of validation warnings.

        Returns:
            List of warning messages for invalid settings
        """
        return self._warnings.copy()

    def has_warnings(self) -> bool:
        """
        Check if there are any validation warnings.

        Returns:
            True if warnings exist, False otherwise
        """
        return len(self._warnings) > 0

    def update_from_dict(self, config_dict: dict[str, Any]) -> list[str]:
        """
        Update configuration from dictionary.

        Validates all settings and collects warnings for invalid values.
        This method is used for dynamic configuration updates.
        Only updates fields that are present in the config_dict.

        Args:
            config_dict: Configuration dictionary with new settings

        Returns:
            List of validation warnings
        """
        # Clear previous warnings
        self._warnings = []

        # Validate and update trace level
        if "trace" in config_dict:
            trace_value = config_dict["trace"]
            try:
                self.trace = TraceLevel(trace_value)
            except ValueError:
                self._warnings.append(
                    f"Invalid trace level '{trace_value}'. "
                    f"Valid values are: {[t.value for t in TraceLevel]}. "
                    f"Keeping current: '{self.trace.value}'"
                )
                logger.warning(self._warnings[-1])

        # Validate and update max completion items
        if "maxCompletionItems" in config_dict:
            max_items = config_dict["maxCompletionItems"]
            if isinstance(max_items, int) and max_items > 0:
                self.max_completion_items = max_items
            else:
                self._warnings.append(
                    f"Invalid maxCompletionItems '{max_items}'. "
                    "Must be a positive integer. "
                    f"Keeping current: {self.max_completion_items}"
                )
                logger.warning(self._warnings[-1])

        # Validate and update enabled
        if "enabled" in config_dict:
            enabled = config_dict["enabled"]
            if isinstance(enabled, bool):
                self.enabled = enabled
            else:
                self._warnings.append(
                    f"Invalid enabled value '{enabled}'. "
                    "Must be a boolean. "
                    f"Keeping current: {self.enabled}"
                )
                logger.warning(self._warnings[-1])

        # Update python command
        if "pythonCommand" in config_dict:
            python_cmd = config_dict["pythonCommand"]
            if isinstance(python_cmd, str):
                self.python_command = python_cmd

        return self._warnings

    def to_dict(self) -> dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns:
            Dictionary representation of configuration
        """
        return {
            "trace": self.trace.value,
            "maxCompletionItems": self.max_completion_items,
            "enabled": self.enabled,
            "pythonCommand": self.python_command,
        }


# Global configuration instance
# This is initialized with defaults and updated via LSP configuration messages
_global_config = LSPConfiguration()


def get_config() -> LSPConfiguration:
    """
    Get the global LSP configuration instance.

    Returns:
        Global LSPConfiguration instance
    """
    return _global_config


def update_config(config_dict: dict[str, Any]) -> list[str]:
    """
    Update the global configuration from a dictionary.

    Args:
        config_dict: Configuration dictionary from LSP client

    Returns:
        List of validation warnings
    """
    return _global_config.update_from_dict(config_dict)
