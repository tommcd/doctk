"""Language Server Protocol support for doctk.

This module provides LSP-specific functionality for the doctk DSL.
For core integration functionality (operations, bridge, memory, etc.),
use doctk.integration instead.
"""

# Re-export core integration items for backward compatibility
# DEPRECATED: Import from doctk.integration instead
from doctk.integration import (
    CompatibilityChecker,
    DocumentInterface,
    DocumentOperation,
    DocumentStateManager,
    DocumentTreeBuilder,
    ExtensionBridge,
    LRUCache,
    ModifiedRange,
    OperationResult,
    PerformanceMonitor,
    StructureOperations,
    TreeNode,
    ValidationResult,
    VersionInfo,
    check_compatibility,
    check_feature,
    get_compatibility_checker,
    get_doctk_version,
)

# LSP-specific exports
from doctk.lsp.registry import OperationMetadata, OperationRegistry, ParameterInfo
from doctk.lsp.server import DoctkLanguageServer, DocumentState

__all__ = [
    # LSP-specific items (primary exports)
    "DoctkLanguageServer",
    "DocumentState",
    "OperationMetadata",
    "OperationRegistry",
    "ParameterInfo",
    # Core integration items (re-exported for backward compatibility)
    # Use doctk.integration instead
    "CompatibilityChecker",
    "DocumentInterface",
    "DocumentOperation",
    "DocumentStateManager",
    "DocumentTreeBuilder",
    "ExtensionBridge",
    "LRUCache",
    "ModifiedRange",
    "OperationResult",
    "PerformanceMonitor",
    "StructureOperations",
    "TreeNode",
    "ValidationResult",
    "VersionInfo",
    "check_compatibility",
    "check_feature",
    "get_compatibility_checker",
    "get_doctk_version",
]
