"""AI Agent Support for doctk Language Server.

This module provides structured information endpoints specifically designed for AI
agent consumption, including operation catalogs, context-aware suggestions, and
machine-readable documentation.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any

from doctk.lsp.registry import OperationMetadata, OperationRegistry

logger = logging.getLogger(__name__)


@dataclass
class OperationSuggestion:
    """Suggestion for an operation based on context."""

    operation: str
    confidence: float  # 0.0 to 1.0
    reason: str
    example: str


@dataclass
class StructuredDocumentation:
    """Machine-readable documentation format for an operation."""

    operation: str
    summary: str
    description: str
    parameters: list[dict[str, Any]]
    returns: dict[str, Any]
    examples: list[dict[str, Any]]
    related_operations: list[str]
    category: str


class AIAgentSupport:
    """Provides structured information for AI agents."""

    def __init__(self, registry: OperationRegistry):
        """
        Initialize AI agent support.

        Args:
            registry: Operation registry to query for operation metadata
        """
        self.registry = registry

    def get_operation_catalog(self) -> dict[str, dict[str, Any]]:
        """
        Return complete catalog of available operations in JSON-serializable format.

        This method provides a comprehensive catalog of all available doctk operations,
        including their parameters, types, descriptions, and examples. The format is
        optimized for AI agent consumption.

        Returns:
            Dictionary mapping operation names to their metadata including:
            - description: Human-readable description
            - parameters: List of parameter information (name, type, required, description, default)
            - return_type: Return type of the operation
            - examples: List of usage examples
            - category: Operation category (selection, structure, etc.)

        Example:
            >>> support = AIAgentSupport(registry)
            >>> catalog = support.get_operation_catalog()
            >>> print(catalog['promote']['description'])
            'Promote heading levels (h3 -> h2)'
        """
        catalog: dict[str, dict[str, Any]] = {}

        for op_name, op_metadata in self.registry.operations.items():
            catalog[op_name] = {
                "description": op_metadata.description,
                "parameters": [
                    {
                        "name": p.name,
                        "type": p.type,
                        "required": p.required,
                        "description": p.description,
                        "default": p.default,
                    }
                    for p in op_metadata.parameters
                ],
                "return_type": op_metadata.return_type,
                "examples": op_metadata.examples,
                "category": op_metadata.category,
            }

        return catalog

    def get_structured_docs(self, operation: str) -> StructuredDocumentation | None:
        """
        Return documentation in machine-readable format for a specific operation.

        Args:
            operation: Name of the operation to get documentation for

        Returns:
            Structured documentation object or None if operation not found

        Example:
            >>> support = AIAgentSupport(registry)
            >>> docs = support.get_structured_docs('promote')
            >>> print(docs.summary)
            'Promote heading levels (h3 -> h2)'
        """
        metadata = self.registry.get_operation(operation)

        if not metadata:
            return None

        # Convert examples from strings to structured format
        examples = [
            {"code": ex, "description": f"Example usage of {operation}"}
            for ex in metadata.examples
        ]

        # Find related operations (same category)
        related_operations = [
            op.name
            for op in self.registry.get_operations_by_category(metadata.category)
            if op.name != operation
        ]

        return StructuredDocumentation(
            operation=operation,
            summary=metadata.description,
            description=self._get_detailed_description(metadata),
            parameters=[asdict(p) for p in metadata.parameters],
            returns={"type": metadata.return_type, "description": "Modified document"},
            examples=examples,
            related_operations=related_operations[:5],  # Limit to 5
            category=metadata.category,
        )

    def get_context_aware_suggestions(
        self, intent: str, max_suggestions: int = 5
    ) -> list[OperationSuggestion]:
        """
        Suggest operations based on user intent (natural language).

        This method analyzes user intent and suggests relevant operations that might
        help achieve the desired goal.

        Args:
            intent: Natural language description of what the user wants to do
            max_suggestions: Maximum number of suggestions to return

        Returns:
            List of operation suggestions with confidence scores

        Example:
            >>> support = AIAgentSupport(registry)
            >>> suggestions = support.get_context_aware_suggestions('increase heading level')
            >>> print(suggestions[0].operation)
            'demote'
        """
        suggestions: list[OperationSuggestion] = []

        # Simple keyword-based matching (can be enhanced with ML in the future)
        intent_lower = intent.lower()

        # Structure operation keywords
        if any(
            kw in intent_lower
            for kw in ["promote", "increase level", "move up", "lift", "raise"]
        ):
            if self.registry.operation_exists("promote"):
                op = self.registry.get_operation("promote")
                if op:
                    suggestions.append(
                        OperationSuggestion(
                            operation="promote",
                            confidence=0.9,
                            reason="Promotes heading levels (e.g., h3 -> h2)",
                            example=op.examples[0] if op.examples else "doc | promote()",
                        )
                    )

        if any(
            kw in intent_lower
            for kw in ["demote", "decrease", "decrease level", "move down", "lower"]
        ):
            if self.registry.operation_exists("demote"):
                op = self.registry.get_operation("demote")
                if op:
                    suggestions.append(
                        OperationSuggestion(
                            operation="demote",
                            confidence=0.9,
                            reason="Demotes heading levels (e.g., h2 -> h3)",
                            example=op.examples[0] if op.examples else "doc | demote()",
                        )
                    )

        # Selection operation keywords
        if any(kw in intent_lower for kw in ["select", "find", "filter", "get"]):
            if "heading" in intent_lower and self.registry.operation_exists("heading"):
                op = self.registry.get_operation("heading")
                if op:
                    suggestions.append(
                        OperationSuggestion(
                            operation="heading",
                            confidence=0.85,
                            reason="Selects all heading nodes",
                            example=op.examples[0] if op.examples else "doc | heading",
                        )
                    )

            if "paragraph" in intent_lower and self.registry.operation_exists("paragraph"):
                op = self.registry.get_operation("paragraph")
                if op:
                    suggestions.append(
                        OperationSuggestion(
                            operation="paragraph",
                            confidence=0.85,
                            reason="Selects all paragraph nodes",
                            example=op.examples[0] if op.examples else "doc | paragraph",
                        )
                    )

        # Nesting keywords
        if any(kw in intent_lower for kw in ["nest", "indent", "move under"]):
            if self.registry.operation_exists("nest"):
                op = self.registry.get_operation("nest")
                if op:
                    suggestions.append(
                        OperationSuggestion(
                            operation="nest",
                            confidence=0.85,
                            reason="Nests sections under a target section",
                            example=op.examples[0] if op.examples else "doc | nest()",
                        )
                    )

        if any(kw in intent_lower for kw in ["unnest", "outdent", "move out"]):
            if self.registry.operation_exists("unnest"):
                op = self.registry.get_operation("unnest")
                if op:
                    suggestions.append(
                        OperationSuggestion(
                            operation="unnest",
                            confidence=0.85,
                            reason="Removes nesting from sections",
                            example=op.examples[0] if op.examples else "doc | unnest()",
                        )
                    )

        # Limit to max_suggestions
        return suggestions[:max_suggestions]

    def _get_detailed_description(self, metadata: OperationMetadata) -> str:
        """
        Get detailed description for an operation.

        Args:
            metadata: Operation metadata

        Returns:
            Detailed description string
        """
        desc = metadata.description

        # Add parameter information if available
        if metadata.parameters:
            desc += "\n\nParameters:\n"
            for param in metadata.parameters:
                required = "required" if param.required else "optional"
                desc += f"  - {param.name} ({param.type}, {required}): {param.description}"
                if param.default is not None:
                    desc += f" [default: {param.default}]"
                desc += "\n"

        return desc
