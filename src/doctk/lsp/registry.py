"""Operation Registry for Language Server.

This module provides the OperationRegistry which maintains metadata about all
available doctk operations and provides this information for LSP features like
completion and hover documentation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ParameterInfo:
    """Information about an operation parameter."""

    name: str
    type: str
    required: bool
    description: str
    default: Any = None


@dataclass
class OperationMetadata:
    """Metadata for a doctk operation."""

    name: str
    description: str
    parameters: list[ParameterInfo] = field(default_factory=list)
    return_type: str = "Document"
    examples: list[str] = field(default_factory=list)
    category: str = "general"


# Known operations with their metadata
# This could be made more dynamic with introspection in the future
_KNOWN_OPERATIONS: dict[str, dict[str, Any]] = {
    "select": {
        "description": "Select nodes matching a predicate",
        "category": "selection",
        "parameters": [
            ParameterInfo(
                name="predicate",
                type="Callable[[Node], bool]",
                required=True,
                description="Function that returns True for nodes to select",
            )
        ],
        "examples": [
            "doc | select heading",
            "doc | select paragraph",
        ],
    },
    "where": {
        "description": "Filter nodes by attribute conditions",
        "category": "selection",
        "parameters": [
            ParameterInfo(
                name="conditions",
                type="dict",
                required=False,
                description="Key-value pairs to match (e.g., level=2, text='foo')",
            )
        ],
        "examples": [
            "doc | where level=2",
            "doc | where text='Introduction'",
        ],
    },
    "promote": {
        "description": "Promote heading levels (h3 -> h2)",
        "category": "structure",
        "parameters": [],
        "examples": ["doc | select heading | promote"],
    },
    "demote": {
        "description": "Demote heading levels (h2 -> h3)",
        "category": "structure",
        "parameters": [],
        "examples": ["doc | select heading | demote"],
    },
    "lift": {
        "description": "Lift sections up (alias for promote)",
        "category": "structure",
        "parameters": [],
        "examples": ["doc | select heading | lift"],
    },
    "lower": {
        "description": "Lower sections down (alias for demote)",
        "category": "structure",
        "parameters": [],
        "examples": ["doc | select heading | lower"],
    },
    "nest": {
        "description": "Nest sections under a target section",
        "category": "structure",
        "parameters": [
            ParameterInfo(
                name="under",
                type="str | None",
                required=False,
                description="Target section identifier (default: previous section)",
                default=None,
            )
        ],
        "examples": ["doc | select heading | nest()"],
    },
    "unnest": {
        "description": "Remove nesting (alias for promote)",
        "category": "structure",
        "parameters": [],
        "examples": ["doc | select heading | unnest"],
    },
    "heading": {
        "description": "Select all heading nodes",
        "category": "selection",
        "parameters": [],
        "examples": ["doc | heading"],
    },
    "paragraph": {
        "description": "Select all paragraph nodes",
        "category": "selection",
        "parameters": [],
        "examples": ["doc | paragraph"],
    },
    "compose": {
        "description": "Compose operations right-to-left",
        "category": "composition",
        "parameters": [
            ParameterInfo(
                name="operations",
                type="*Callable",
                required=True,
                description="Operations to compose",
            )
        ],
        "examples": ["compose(promote, select(heading))"],
    },
}


class OperationRegistry:
    """Registry of available doctk operations."""

    def __init__(self):
        """Initialize the operation registry."""
        self.operations: dict[str, OperationMetadata] = {}
        self._load_operations_from_doctk()

    def _load_operations_from_doctk(self) -> None:
        """Dynamically load operations from doctk module."""
        try:
            import doctk.operations as ops_module

            # Load each operation from the known operations dictionary
            for op_name, metadata in _KNOWN_OPERATIONS.items():
                # Check if operation exists in module
                if hasattr(ops_module, op_name):
                    self.operations[op_name] = OperationMetadata(
                        name=op_name,
                        description=metadata["description"],
                        parameters=metadata.get("parameters", []),
                        return_type=metadata.get("return_type", "Document"),
                        examples=metadata.get("examples", []),
                        category=metadata.get("category", "general"),
                    )

        except ImportError:
            # doctk.operations not available - registry will be empty
            logger.warning(
                "Could not import 'doctk.operations'. Operation registry will be empty."
            )

    def get_operation(self, name: str) -> OperationMetadata | None:
        """
        Get operation metadata by name.

        Args:
            name: Operation name

        Returns:
            Operation metadata or None if not found
        """
        return self.operations.get(name)

    def get_all_operations(self) -> list[OperationMetadata]:
        """
        Get all registered operations.

        Returns:
            List of all operation metadata
        """
        return list(self.operations.values())

    def get_operations_by_category(self, category: str) -> list[OperationMetadata]:
        """
        Get operations in a specific category.

        Args:
            category: Operation category (e.g., "selection", "structure")

        Returns:
            List of operations in the category
        """
        return [op for op in self.operations.values() if op.category == category]

    def get_operation_names(self) -> list[str]:
        """
        Get names of all registered operations.

        Returns:
            List of operation names
        """
        return list(self.operations.keys())

    def operation_exists(self, name: str) -> bool:
        """
        Check if an operation is registered.

        Args:
            name: Operation name

        Returns:
            True if operation exists, False otherwise
        """
        return name in self.operations
