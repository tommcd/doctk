"""Language Server Protocol support for doctk."""

from doctk.lsp.bridge import ExtensionBridge
from doctk.lsp.operations import DocumentTreeBuilder, StructureOperations
from doctk.lsp.protocols import (
    DocumentInterface,
    DocumentOperation,
    OperationResult,
    ValidationResult,
)

__all__ = [
    "DocumentInterface",
    "DocumentOperation",
    "DocumentTreeBuilder",
    "ExtensionBridge",
    "OperationResult",
    "StructureOperations",
    "ValidationResult",
]
