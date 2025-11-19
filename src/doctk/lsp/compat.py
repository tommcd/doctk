"""Backward compatibility wrapper for doctk.integration.compat.

DEPRECATED: Import from doctk.integration.compat instead.

This module exists solely for backward compatibility with code that imported
from doctk.lsp.compat. All functionality has moved to doctk.integration.compat.
"""

from doctk.integration.compat import (
    CompatibilityChecker,
    VersionInfo,
    check_compatibility,
    check_feature,
    get_compatibility_checker,
    get_doctk_version,
)

__all__ = [
    "CompatibilityChecker",
    "VersionInfo",
    "check_compatibility",
    "check_feature",
    "get_compatibility_checker",
    "get_doctk_version",
]
