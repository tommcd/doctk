"""Core integration layer for doctk.

This module provides the core integration capabilities that bridge UI components
with the doctk core API. It is independent of any specific interface (LSP, VS Code, CLI)
and can be used by all consumers.
"""

from doctk.integration.bridge import ExtensionBridge
from doctk.integration.compat import (
    CompatibilityChecker,
    VersionInfo,
    check_compatibility,
    check_feature,
    get_compatibility_checker,
    get_doctk_version,
)
from doctk.integration.memory import DocumentStateManager, LRUCache
from doctk.integration.operations import DocumentTreeBuilder, StructureOperations
from doctk.integration.performance import PerformanceMonitor
from doctk.integration.protocols import (
    DocumentInterface,
    DocumentOperation,
    ModifiedRange,
    OperationResult,
    TreeNode,
    ValidationResult,
)

__all__ = [
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
