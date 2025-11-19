"""Backward compatibility handling for doctk core API.

This module provides version checking and migration paths for changes
in the doctk core API, ensuring the LSP integration layer can work with
different versions of doctk.
"""

from __future__ import annotations

import importlib.metadata
import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class VersionInfo:
    """Version information for doctk."""

    major: int
    minor: int
    patch: int
    raw: str

    @classmethod
    def from_string(cls, version_str: str) -> VersionInfo:
        """
        Parse version string into VersionInfo.

        Args:
            version_str: Version string (e.g., "0.1.0")

        Returns:
            VersionInfo object

        Raises:
            ValueError: If version string is invalid
        """
        # Handle versions with additional suffixes (e.g., "0.1.0-alpha", "0.1.0.dev1")
        clean_version = version_str.split("-")[0].split("+")[0]
        parts = clean_version.split(".")

        if len(parts) < 2:
            raise ValueError(f"Invalid version string: {version_str}")

        major = int(parts[0])
        minor = int(parts[1])
        patch = int(parts[2]) if len(parts) > 2 else 0

        return cls(major=major, minor=minor, patch=patch, raw=version_str)

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.major}.{self.minor}.{self.patch}"

    def __lt__(self, other: VersionInfo) -> bool:
        """Compare versions for ordering."""
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

    def __le__(self, other: VersionInfo) -> bool:
        """Compare versions for ordering."""
        return (self.major, self.minor, self.patch) <= (other.major, other.minor, other.patch)

    def __gt__(self, other: VersionInfo) -> bool:
        """Compare versions for ordering."""
        return (self.major, self.minor, self.patch) > (other.major, other.minor, other.patch)

    def __ge__(self, other: VersionInfo) -> bool:
        """Compare versions for ordering."""
        return (self.major, self.minor, self.patch) >= (other.major, other.minor, other.patch)

    def __eq__(self, other: object) -> bool:
        """Compare versions for equality."""
        if not isinstance(other, VersionInfo):
            return NotImplemented
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)


class CompatibilityChecker:
    """Checks compatibility between LSP and doctk core versions."""

    # Minimum supported doctk version
    MIN_VERSION = VersionInfo(0, 1, 0, "0.1.0")

    # Known breaking changes and migration paths
    BREAKING_CHANGES: dict[str, dict[str, Any]] = {
        # Example: "0.2.0": {
        #     "changes": ["Node IDs now use UUIDs instead of counters"],
        #     "migration": "Use get_node_by_id() instead of direct ID construction"
        # }
    }

    def __init__(self) -> None:
        """Initialize compatibility checker."""
        self.doctk_version = self._get_doctk_version()
        self._check_compatibility()

    def _get_doctk_version(self) -> VersionInfo:
        """
        Get the installed doctk version.

        Returns:
            VersionInfo for the installed doctk package

        Raises:
            ImportError: If doctk is not installed
        """
        try:
            version_str = importlib.metadata.version("doctk")
            return VersionInfo.from_string(version_str)
        except importlib.metadata.PackageNotFoundError as e:
            raise ImportError("doctk package not found. Please install doctk.") from e

    def _check_compatibility(self) -> None:
        """
        Check if doctk version is compatible with this LSP version.

        Logs warnings for version compatibility issues.
        """
        if self.doctk_version < self.MIN_VERSION:
            logger.warning(
                f"doctk version {self.doctk_version} is below minimum supported "
                f"version {self.MIN_VERSION}. Some features may not work correctly."
            )

        # Check for breaking changes
        for breaking_version, info in self.BREAKING_CHANGES.items():
            breaking_ver = VersionInfo.from_string(breaking_version)
            if self.doctk_version >= breaking_ver:
                logger.info(
                    f"doctk {breaking_version} includes breaking changes: "
                    f"{', '.join(info['changes'])}. "
                    f"Migration: {info['migration']}"
                )

    def is_compatible(self) -> bool:
        """
        Check if current doctk version is compatible.

        Returns:
            True if compatible, False otherwise
        """
        return self.doctk_version >= self.MIN_VERSION

    def get_version(self) -> VersionInfo:
        """
        Get the current doctk version.

        Returns:
            VersionInfo object for the installed doctk
        """
        return self.doctk_version

    def check_feature(self, feature: str, min_version: str) -> bool:
        """
        Check if a specific feature is available.

        Args:
            feature: Feature name
            min_version: Minimum version required for the feature

        Returns:
            True if feature is available, False otherwise
        """
        required_version = VersionInfo.from_string(min_version)
        available = self.doctk_version >= required_version

        if not available:
            logger.debug(
                f"Feature '{feature}' requires doctk {min_version} "
                f"but {self.doctk_version} is installed"
            )

        return available


# Global compatibility checker instance
_compat_checker: CompatibilityChecker | None = None


def get_compatibility_checker() -> CompatibilityChecker:
    """
    Get the global compatibility checker instance.

    Returns:
        CompatibilityChecker singleton instance
    """
    global _compat_checker
    if _compat_checker is None:
        _compat_checker = CompatibilityChecker()
    return _compat_checker


def check_compatibility() -> bool:
    """
    Check if current doctk version is compatible with this LSP.

    Returns:
        True if compatible, False otherwise
    """
    return get_compatibility_checker().is_compatible()


def get_doctk_version() -> VersionInfo:
    """
    Get the installed doctk version.

    Returns:
        VersionInfo object
    """
    return get_compatibility_checker().get_version()


def check_feature(feature: str, min_version: str) -> bool:
    """
    Check if a specific feature is available in the current doctk version.

    Args:
        feature: Feature name
        min_version: Minimum version required

    Returns:
        True if available, False otherwise
    """
    return get_compatibility_checker().check_feature(feature, min_version)
