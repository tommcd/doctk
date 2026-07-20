"""Language Server Protocol support for doctk.

This module provides LSP-specific functionality for the doctk DSL.
For core integration functionality (operations, bridge, etc.),
use doctk.integration instead.
"""

from doctk.lsp.registry import OperationMetadata, OperationRegistry, ParameterInfo
from doctk.lsp.server import DoctkLanguageServer, DocumentState

__all__ = [
    "DoctkLanguageServer",
    "DocumentState",
    "OperationMetadata",
    "OperationRegistry",
    "ParameterInfo",
]
