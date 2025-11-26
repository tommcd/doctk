"""
Internal operations layer for document transformations.

This module provides the core operations layer that works with rich Document objects
instead of serialized strings. It serves as the foundation for all document transformations,
avoiding the overhead of JSON serialization/deserialization.

Key principles:
- Operations return OperationResult with Document objects (no serialization)
- Node IDs are preserved across operations where appropriate
- Metadata is deep-copied to ensure immutability
- Provenance is updated during transformations
- Source spans are preserved where appropriate
"""

from dataclasses import dataclass, field
from typing import Any

from doctk.core import Document, Heading, Node
from doctk.identity import NodeId


@dataclass
class OperationResult:
    """
    Result of an internal operation.

    Attributes:
        success: Whether the operation succeeded
        document: The transformed document (rich Document object, not serialized)
        modified_nodes: List of NodeIds that were modified
        error: Optional error message if operation failed
        metadata: Optional metadata about the operation
    """

    success: bool
    document: Document[Node]
    modified_nodes: list[NodeId] = field(default_factory=list)
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class InternalOperations:
    """
    Internal operations layer for document transformations.

    This class provides core document operations that work with rich Document objects
    instead of serialized strings. All operations:
    - Preserve NodeIds where appropriate (structural changes preserve IDs)
    - Deep-copy metadata to ensure immutability
    - Update provenance during transformations
    - Preserve source spans where appropriate
    - Return OperationResult with Document objects (no JSON serialization)

    Example:
        >>> doc = Document([Heading(level=2, text="Test")])
        >>> result = InternalOperations.promote(doc, doc.nodes[0].id)
        >>> assert result.success
        >>> assert result.document.nodes[0].level == 1
        >>> assert result.document.nodes[0].id == doc.nodes[0].id  # ID preserved
    """

    @staticmethod
    def promote(document: Document[Node], node_id: NodeId) -> OperationResult:
        """
        Promote a heading (decrease level: h3 -> h2).

        This is a structural operation that preserves NodeId because heading level
        is not part of the canonical form.

        Args:
            document: The document containing the node
            node_id: The ID of the node to promote

        Returns:
            OperationResult with the transformed document

        Raises:
            ValueError: If node not found or node is not a Heading
        """
        # Find the node
        node = document.find_node(node_id)
        if node is None:
            return OperationResult(
                success=False,
                document=document,
                error=f"Node with ID {node_id} not found",
            )

        if not isinstance(node, Heading):
            return OperationResult(
                success=False,
                document=document,
                error=f"Node {node_id} is not a Heading (type: {type(node).__name__})",
            )

        # Promote the heading (this preserves ID)
        promoted = node.promote()

        # Create new document with promoted node
        new_nodes = []
        for n in document.nodes:
            if n.id == node_id:
                new_nodes.append(promoted)
            else:
                new_nodes.append(n)

        new_document = Document(new_nodes)

        return OperationResult(
            success=True,
            document=new_document,
            modified_nodes=[node_id],
            metadata={"operation": "promote", "old_level": node.level, "new_level": promoted.level},
        )

    @staticmethod
    def demote(document: Document[Node], node_id: NodeId) -> OperationResult:
        """
        Demote a heading (increase level: h2 -> h3).

        This is a structural operation that preserves NodeId because heading level
        is not part of the canonical form.

        Args:
            document: The document containing the node
            node_id: The ID of the node to demote

        Returns:
            OperationResult with the transformed document

        Raises:
            ValueError: If node not found or node is not a Heading
        """
        # Find the node
        node = document.find_node(node_id)
        if node is None:
            return OperationResult(
                success=False,
                document=document,
                error=f"Node with ID {node_id} not found",
            )

        if not isinstance(node, Heading):
            return OperationResult(
                success=False,
                document=document,
                error=f"Node {node_id} is not a Heading (type: {type(node).__name__})",
            )

        # Demote the heading (this preserves ID)
        demoted = node.demote()

        # Create new document with demoted node
        new_nodes = []
        for n in document.nodes:
            if n.id == node_id:
                new_nodes.append(demoted)
            else:
                new_nodes.append(n)

        new_document = Document(new_nodes)

        return OperationResult(
            success=True,
            document=new_document,
            modified_nodes=[node_id],
            metadata={"operation": "demote", "old_level": node.level, "new_level": demoted.level},
        )
