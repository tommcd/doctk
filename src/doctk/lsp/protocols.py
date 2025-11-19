"""Backward compatibility wrapper for doctk.integration.protocols.

DEPRECATED: Import from doctk.integration.protocols instead.

This module exists solely for backward compatibility with code that imported
from doctk.lsp.protocols. All functionality has moved to doctk.integration.protocols.
"""

from doctk.integration.protocols import (
    DocumentInterface,
    DocumentOperation,
    ModifiedRange,
    OperationResult,
    TreeNode,
    ValidationResult,
)

__all__ = [
    "DocumentInterface",
    "DocumentOperation",
    "ModifiedRange",
    "OperationResult",
    "TreeNode",
    "ValidationResult",
]
