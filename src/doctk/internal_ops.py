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

import copy
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

    @staticmethod
    def move_up(document: Document[Node], node_id: NodeId) -> OperationResult:
        """
        Move a node up in the sibling order (swap with previous sibling).

        Args:
            document: The document containing the node
            node_id: The ID of the node to move up

        Returns:
            OperationResult with the transformed document
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

        # Find the node's index
        try:
            node_index = document.nodes.index(node)
        except ValueError:
            return OperationResult(
                success=False,
                document=document,
                error=f"Node {node_id} not found in document nodes",
            )

        # Check if already at the top
        if node_index == 0:
            return OperationResult(
                success=True,
                document=document,
                modified_nodes=[],
                metadata={"operation": "move_up", "position": "already_at_top"},
            )

        # Swap with previous node
        new_nodes = list(document.nodes)
        new_nodes[node_index - 1], new_nodes[node_index] = (
            new_nodes[node_index],
            new_nodes[node_index - 1],
        )

        new_document = Document(new_nodes)

        return OperationResult(
            success=True,
            document=new_document,
            modified_nodes=[node_id],
            metadata={
                "operation": "move_up",
                "old_index": node_index,
                "new_index": node_index - 1,
            },
        )

    @staticmethod
    def move_down(document: Document[Node], node_id: NodeId) -> OperationResult:
        """
        Move a node down in the sibling order (swap with next sibling).

        Args:
            document: The document containing the node
            node_id: The ID of the node to move down

        Returns:
            OperationResult with the transformed document
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

        # Find the node's index
        try:
            node_index = document.nodes.index(node)
        except ValueError:
            return OperationResult(
                success=False,
                document=document,
                error=f"Node {node_id} not found in document nodes",
            )

        # Check if already at the bottom
        if node_index >= len(document.nodes) - 1:
            return OperationResult(
                success=True,
                document=document,
                modified_nodes=[],
                metadata={"operation": "move_down", "position": "already_at_bottom"},
            )

        # Swap with next node
        new_nodes = list(document.nodes)
        new_nodes[node_index], new_nodes[node_index + 1] = (
            new_nodes[node_index + 1],
            new_nodes[node_index],
        )

        new_document = Document(new_nodes)

        return OperationResult(
            success=True,
            document=new_document,
            modified_nodes=[node_id],
            metadata={
                "operation": "move_down",
                "old_index": node_index,
                "new_index": node_index + 1,
            },
        )

    @staticmethod
    def nest(document: Document[Node], node_id: NodeId, parent_id: NodeId) -> OperationResult:
        """
        Nest a node under a parent (increase level to parent.level + 1 and move after parent).

        Args:
            document: The document containing the nodes
            node_id: The ID of the node to nest
            parent_id: The ID of the parent node

        Returns:
            OperationResult with the transformed document
        """
        # Find both nodes
        node = document.find_node(node_id)
        parent = document.find_node(parent_id)

        if node is None:
            return OperationResult(
                success=False,
                document=document,
                error=f"Node with ID {node_id} not found",
            )

        if parent is None:
            return OperationResult(
                success=False,
                document=document,
                error=f"Parent node with ID {parent_id} not found",
            )

        if not isinstance(node, Heading):
            return OperationResult(
                success=False,
                document=document,
                error=f"Node {node_id} is not a Heading (type: {type(node).__name__})",
            )

        if not isinstance(parent, Heading):
            return OperationResult(
                success=False,
                document=document,
                error=f"Parent node {parent_id} is not a Heading (type: {type(parent).__name__})",
            )

        # Calculate new level (parent level + 1, capped at 6)
        new_level = min(6, parent.level + 1)

        # Create nested node with new level
        nested_node = Heading(
            level=new_level,
            text=node.text,
            children=node.children,
            metadata=copy.deepcopy(node.metadata),
            id=node.id,  # Preserve ID (level not in canonical form)
            provenance=node.provenance.with_modification() if node.provenance else None,
            source_span=node.source_span,
        )

        # Find indices
        try:
            node_index = document.nodes.index(node)
            parent_index = document.nodes.index(parent)
        except ValueError:
            return OperationResult(
                success=False,
                document=document,
                error="Could not find node or parent in document",
            )

        # Create new node list
        new_nodes = list(document.nodes)

        # Remove node from current position
        new_nodes.pop(node_index)

        # Adjust parent index if node was before parent
        if node_index < parent_index:
            parent_index -= 1

        # Insert nested node after parent
        new_nodes.insert(parent_index + 1, nested_node)

        new_document = Document(new_nodes)

        return OperationResult(
            success=True,
            document=new_document,
            modified_nodes=[node_id],
            metadata={
                "operation": "nest",
                "old_level": node.level,
                "new_level": new_level,
                "parent_id": str(parent_id),
            },
        )

    @staticmethod
    def unnest(document: Document[Node], node_id: NodeId) -> OperationResult:
        """
        Unnest a node (decrease level by 1, moving it up in the hierarchy).

        This is equivalent to promoting the node.

        Args:
            document: The document containing the node
            node_id: The ID of the node to unnest

        Returns:
            OperationResult with the transformed document
        """
        # Unnest is just promote with different semantics
        result = InternalOperations.promote(document, node_id)

        # Update metadata to reflect unnest operation
        if result.success and result.metadata:
            result.metadata["operation"] = "unnest"

        return result
