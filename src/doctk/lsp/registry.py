"""Operation Registry for Language Server.

This module provides the OperationRegistry which maintains metadata about all
available doctk operations and provides this information for LSP features like
completion and hover documentation.
"""

from __future__ import annotations

import inspect
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


# Metadata enrichment for known operations
# This supplements dynamically discovered operations with examples and categories
_OPERATION_METADATA: dict[str, dict[str, Any]] = {
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
        "examples": ["doc | select heading | promote()"],
    },
    "demote": {
        "description": "Demote heading levels (h2 -> h3)",
        "category": "structure",
        "parameters": [],
        "examples": ["doc | select heading | demote()"],
    },
    "lift": {
        "description": "Lift sections up (alias for promote)",
        "category": "structure",
        "parameters": [],
        "examples": ["doc | select heading | lift()"],
    },
    "lower": {
        "description": "Lower sections down (alias for demote)",
        "category": "structure",
        "parameters": [],
        "examples": ["doc | select heading | lower()"],
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
        "examples": ["doc | select heading | unnest()"],
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
    "first": {
        "description": "Take first element",
        "category": "selection",
        "parameters": [],
        "examples": ["doc | select heading | first()"],
    },
    "last": {
        "description": "Take last element",
        "category": "selection",
        "parameters": [],
        "examples": ["doc | select heading | last()"],
    },
    "nth": {
        "description": "Take nth element (0-indexed)",
        "category": "selection",
        "parameters": [
            ParameterInfo(
                name="n",
                type="int",
                required=True,
                description="Index of element to take",
            )
        ],
        "examples": ["doc | select heading | nth(2)"],
    },
    "slice_nodes": {
        "description": "Take slice of nodes",
        "category": "selection",
        "parameters": [
            ParameterInfo(
                name="start",
                type="int",
                required=True,
                description="Start index",
            ),
            ParameterInfo(
                name="end",
                type="int | None",
                required=False,
                description="End index (optional)",
                default=None,
            ),
        ],
        "examples": ["doc | select heading | slice_nodes(0, 5)"],
    },
    "is_heading": {
        "description": "Check if node is a heading",
        "category": "predicates",
        "parameters": [],
        "examples": ["doc | select(is_heading)"],
    },
    "is_paragraph": {
        "description": "Check if node is a paragraph",
        "category": "predicates",
        "parameters": [],
        "examples": ["doc | select(is_paragraph)"],
    },
    "is_list": {
        "description": "Check if node is a list",
        "category": "predicates",
        "parameters": [],
        "examples": ["doc | select(is_list)"],
    },
    "is_code_block": {
        "description": "Check if node is a code block",
        "category": "predicates",
        "parameters": [],
        "examples": ["doc | select(is_code_block)"],
    },
    "matches": {
        "description": "Create predicate that matches text content against pattern",
        "category": "predicates",
        "parameters": [
            ParameterInfo(
                name="pattern",
                type="str",
                required=True,
                description="Pattern to match",
            )
        ],
        "examples": ["doc | select(matches('TODO'))"],
    },
    "contains": {
        "description": "Alias for matches (more readable)",
        "category": "predicates",
        "parameters": [
            ParameterInfo(
                name="substring",
                type="str",
                required=True,
                description="Substring to search for",
            )
        ],
        "examples": ["doc | select(contains('important'))"],
    },
    "to_ordered": {
        "description": "Convert lists to ordered",
        "category": "structure",
        "parameters": [],
        "examples": ["doc | select(is_list) | to_ordered()"],
    },
    "to_unordered": {
        "description": "Convert lists to unordered",
        "category": "structure",
        "parameters": [],
        "examples": ["doc | select(is_list) | to_unordered()"],
    },
    "count": {
        "description": "Count nodes in document",
        "category": "utility",
        "parameters": [],
        "examples": ["doc | select heading | count()"],
        "return_type": "int",
    },
    "extract": {
        "description": "Extract nodes as list",
        "category": "utility",
        "parameters": [],
        "examples": ["doc | select heading | extract()"],
        "return_type": "list",
    },
    "code_block": {
        "description": "Select all code block nodes",
        "category": "selection",
        "parameters": [],
        "examples": ["doc | code_block"],
    },
    "list_node": {
        "description": "Select all list nodes",
        "category": "selection",
        "parameters": [],
        "examples": ["doc | list_node"],
    },
}


class OperationRegistry:
    """Registry of available doctk operations."""

    def __init__(self) -> None:
        """Initialize the operation registry."""
        self.operations: dict[str, OperationMetadata] = {}
        self._load_operations_from_doctk()

    def _load_operations_from_doctk(self) -> None:
        """Dynamically load operations from doctk module using introspection."""
        try:
            import doctk.operations as ops_module

            # Dynamically discover all callable operations in the module
            for name, obj in inspect.getmembers(ops_module, callable):
                # Skip private members and imports
                if name.startswith("_"):
                    continue

                # Skip type objects and classes (they're not operations)
                if inspect.isclass(obj):
                    continue

                # Skip imports from other modules (check if defined in this module)
                if hasattr(obj, "__module__") and obj.__module__ != "doctk.operations":
                    continue

                # Get basic metadata from the function
                description = self._extract_description(obj)
                category = "general"
                parameters: list[ParameterInfo] = []
                examples: list[str] = []
                return_type = "Document"

                # Enrich with static metadata if available
                if name in _OPERATION_METADATA:
                    metadata = _OPERATION_METADATA[name]
                    description = metadata.get("description", description)
                    category = metadata.get("category", category)
                    parameters = metadata.get("parameters", parameters)
                    examples = metadata.get("examples", examples)
                    return_type = metadata.get("return_type", return_type)

                # Register the operation
                self.operations[name] = OperationMetadata(
                    name=name,
                    description=description,
                    parameters=parameters,
                    return_type=return_type,
                    examples=examples,
                    category=category,
                )

        except ImportError:
            # doctk.operations not available - registry will be empty
            logger.warning("Could not import 'doctk.operations'. Operation registry will be empty.")

    def _extract_description(self, obj: Any) -> str:
        """
        Extract description from a function's docstring.

        Args:
            obj: Function or callable to extract description from

        Returns:
            First line of docstring or a default description
        """
        if not obj.__doc__:
            return "No description available"

        # Get first line of docstring
        lines = obj.__doc__.strip().split("\n")
        return lines[0].strip() if lines else "No description available"

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

    def search_operations(self, query: str) -> list[OperationMetadata]:
        """
        Search operations by name or description.

        Args:
            query: Search query string

        Returns:
            List of operations matching the query (case-insensitive)

        Example:
            >>> registry = OperationRegistry()
            >>> results = registry.search_operations("head")
            >>> # Returns operations with "head" in name or description
        """
        query_lower = query.lower()
        results = []
        for op in self.operations.values():
            if query_lower in op.name.lower() or query_lower in op.description.lower():
                results.append(op)
        return results

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
