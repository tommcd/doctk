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

    def _validate_trace(self, trace_value: Any, use_default: bool = True) -> None:
        """
        Validate and update trace level.

        Args:
            trace_value: Trace level value to validate
            use_default: If True, use default on invalid value; if False, keep current
        """
        try:
            self.trace = TraceLevel(trace_value)
        except ValueError:
            default_or_current = (
                f"'{TraceLevel.OFF.value}'" if use_default else f"'{self.trace.value}'"
            )
            action = "Using default" if use_default else "Keeping current"
            self._warnings.append(
                f"Invalid trace level '{trace_value}'. "
                f"Valid values are: {[t.value for t in TraceLevel]}. "
                f"{action}: {default_or_current}"
            )
            logger.warning(self._warnings[-1])

    def _validate_max_completion_items(self, max_items: Any, use_default: bool = True) -> None:
        """
        Validate and update max completion items.

        Args:
            max_items: Max items value to validate
            use_default: If True, use default on invalid value; if False, keep current
        """
        if isinstance(max_items, int) and max_items > 0:
            self.max_completion_items = max_items
        else:
            default_or_current = 50 if use_default else self.max_completion_items
            action = "Using default" if use_default else "Keeping current"
            self._warnings.append(
                f"Invalid maxCompletionItems '{max_items}'. "
                "Must be a positive integer. "
                f"{action}: {default_or_current}"
            )
            logger.warning(self._warnings[-1])

    def _validate_enabled(self, enabled: Any, use_default: bool = True) -> None:
        """
        Validate and update enabled flag.

        Args:
            enabled: Enabled value to validate
            use_default: If True, use default on invalid value; if False, keep current
        """
        if isinstance(enabled, bool):
            self.enabled = enabled
        else:
            default_or_current = True if use_default else self.enabled
            action = "Using default" if use_default else "Keeping current"
            self._warnings.append(
                f"Invalid enabled value '{enabled}'. "
                "Must be a boolean. "
                f"{action}: {default_or_current}"
            )
            logger.warning(self._warnings[-1])

    def _validate_python_command(self, python_cmd: Any) -> None:
        """
        Validate and update Python command.

        Args:
            python_cmd: Python command value to validate
        """
        if isinstance(python_cmd, str):
            self.python_command = python_cmd

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

        # Validate and set each field using helper methods
        if "trace" in config_dict:
            instance._validate_trace(config_dict["trace"], use_default=True)

        if "maxCompletionItems" in config_dict:
            instance._validate_max_completion_items(config_dict["maxCompletionItems"], use_default=True)

        if "enabled" in config_dict:
            instance._validate_enabled(config_dict["enabled"], use_default=True)

        if "pythonCommand" in config_dict:
            instance._validate_python_command(config_dict["pythonCommand"])

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

        # Validate and update each field using helper methods
        if "trace" in config_dict:
            self._validate_trace(config_dict["trace"], use_default=False)

        if "maxCompletionItems" in config_dict:
            self._validate_max_completion_items(config_dict["maxCompletionItems"], use_default=False)

        if "enabled" in config_dict:
            self._validate_enabled(config_dict["enabled"], use_default=False)

        if "pythonCommand" in config_dict:
            self._validate_python_command(config_dict["pythonCommand"])

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
