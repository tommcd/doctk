"""Backward compatibility wrapper for doctk.integration.bridge.

DEPRECATED: Import from doctk.integration.bridge instead.

This module exists solely for backward compatibility with code that imported
from doctk.lsp.bridge. All functionality has moved to doctk.integration.bridge.
"""

from doctk.integration.bridge import ExtensionBridge

__all__ = ["ExtensionBridge"]
