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
            {"code": ex, "description": f"Example usage of {operation}"} for ex in metadata.examples
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
            >>> suggestions = support.get_context_aware_suggestions('decrease heading level')
            >>> print(suggestions[0].operation)
            'demote'
        """
        suggestions: list[OperationSuggestion] = []

        # Simple keyword-based matching (can be enhanced with ML in the future)
        intent_lower = intent.lower()

        # Operation suggestion rules: (keywords, operation, reason, confidence)
        suggestion_rules = [
            (
                ["promote", "increase level", "move up", "lift", "raise"],
                "promote",
                "Promotes heading levels (e.g., h3 -> h2)",
                0.9,
            ),
            (
                ["demote", "decrease", "decrease level", "move down", "lower"],
                "demote",
                "Demotes heading levels (e.g., h2 -> h3)",
                0.9,
            ),
            (
                ["nest", "indent", "move under"],
                "nest",
                "Nests sections under a target section",
                0.85,
            ),
            (
                ["unnest", "outdent", "move out"],
                "unnest",
                "Removes nesting from sections",
                0.85,
            ),
        ]

        # Apply simple rules
        for keywords, operation, reason, confidence in suggestion_rules:
            if any(kw in intent_lower for kw in keywords):
                if self.registry.operation_exists(operation):
                    op = self.registry.get_operation(operation)
                    if op:
                        suggestions.append(
                            OperationSuggestion(
                                operation=operation,
                                confidence=confidence,
                                reason=reason,
                                example=op.examples[0] if op.examples else f"doc | {operation}()",
                            )
                        )

        # Selection operations (require additional context)
        if any(kw in intent_lower for kw in ["select", "find", "filter", "get"]):
            selection_ops = [
                ("heading", "Selects all heading nodes"),
                ("paragraph", "Selects all paragraph nodes"),
            ]

            for op_name, reason in selection_ops:
                if op_name in intent_lower and self.registry.operation_exists(op_name):
                    op = self.registry.get_operation(op_name)
                    if op:
                        suggestions.append(
                            OperationSuggestion(
                                operation=op_name,
                                confidence=0.85,
                                reason=reason,
                                example=op.examples[0] if op.examples else f"doc | {op_name}",
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
