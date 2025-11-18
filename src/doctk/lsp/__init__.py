"""Language Server Protocol support for doctk."""

from doctk.lsp.bridge import ExtensionBridge
from doctk.lsp.operations import DocumentTreeBuilder, StructureOperations
from doctk.lsp.protocols import (
    DocumentInterface,
    DocumentOperation,
    OperationResult,
    ValidationResult,
)
from doctk.lsp.registry import OperationMetadata, OperationRegistry, ParameterInfo
from doctk.lsp.server import DoctkLanguageServer, DocumentState

__all__ = [
    "DoctkLanguageServer",
    "DocumentInterface",
    "DocumentOperation",
    "DocumentState",
    "DocumentTreeBuilder",
    "ExtensionBridge",
    "OperationMetadata",
    "OperationRegistry",
    "OperationResult",
    "ParameterInfo",
    "StructureOperations",
    "ValidationResult",
]
