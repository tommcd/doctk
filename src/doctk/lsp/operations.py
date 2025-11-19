"""Backward compatibility wrapper for doctk.integration.operations.

DEPRECATED: Import from doctk.integration.operations instead.

This module exists solely for backward compatibility with code that imported
from doctk.lsp.operations. All functionality has moved to doctk.integration.operations.
"""

from doctk.integration.operations import DocumentTreeBuilder, StructureOperations

__all__ = ["DocumentTreeBuilder", "StructureOperations"]
