"""Backward compatibility wrapper for doctk.integration.memory.

DEPRECATED: Import from doctk.integration.memory instead.

This module exists solely for backward compatibility with code that imported
from doctk.lsp.memory. All functionality has moved to doctk.integration.memory.
"""

from doctk.integration.memory import DocumentStateManager, LRUCache

__all__ = ["DocumentStateManager", "LRUCache"]
