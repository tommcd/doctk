"""Core integration layer for doctk.

This module provides the core integration capabilities that bridge UI components
with the doctk core API. It is independent of any specific interface (LSP, VS Code, CLI)
and can be used by all consumers.
"""

from doctk.integration.bridge import ExtensionBridge
from doctk.integration.operations import DocumentTreeBuilder, StructureOperations
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
    "DocumentTreeBuilder",
    "ExtensionBridge",
    "ModifiedRange",
    "OperationResult",
    "StructureOperations",
    "TreeNode",
    "ValidationResult",
]
