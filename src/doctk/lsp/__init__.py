"""Language Server Protocol support for doctk."""

from doctk.lsp.bridge import ExtensionBridge
from doctk.lsp.memory import DocumentStateManager, LRUCache
from doctk.lsp.operations import DocumentTreeBuilder, StructureOperations
from doctk.lsp.performance import PerformanceMonitor
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
    "DocumentStateManager",
    "DocumentTreeBuilder",
    "ExtensionBridge",
    "LRUCache",
    "OperationMetadata",
    "OperationRegistry",
    "OperationResult",
    "ParameterInfo",
    "PerformanceMonitor",
    "StructureOperations",
    "ValidationResult",
]
