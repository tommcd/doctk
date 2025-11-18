"""Document structure operations for the LSP integration layer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from doctk.core import Document, Heading, Node

if TYPE_CHECKING:
    from doctk.lsp.protocols import OperationResult, ValidationResult


class DocumentTreeBuilder:
    """Builds a tree representation of a document with node IDs."""

    def __init__(self, document: Document[Node]):
        """
        Initialize the tree builder.

        Args:
            document: The document to build a tree from
        """
        self.document = document
        self.node_map: dict[str, Node] = {}
        self.parent_map: dict[str, str] = {}
        self._build_node_map()

    def _build_node_map(self) -> None:
        """Build a map of node IDs to nodes."""
        heading_counter: dict[int, int] = {}

        for node in self.document.nodes:
            if isinstance(node, Heading):
                level = node.level
                heading_counter[level] = heading_counter.get(level, 0) + 1
                node_id = f"h{level}-{heading_counter[level] - 1}"
                self.node_map[node_id] = node

    def find_node(self, node_id: str) -> Node | None:
        """
        Find a node by its ID.

        Args:
            node_id: The ID of the node to find

        Returns:
            The node if found, None otherwise
        """
        return self.node_map.get(node_id)

    def get_node_index(self, node_id: str) -> int | None:
        """
        Get the index of a node in the document.

        Args:
            node_id: The ID of the node to find

        Returns:
            The index of the node, or None if not found
        """
        node = self.find_node(node_id)
        if node is None:
            return None

        try:
            return self.document.nodes.index(node)
        except ValueError:
            return None


class StructureOperations:
    """High-level operations for document structure manipulation."""

    @staticmethod
    def promote(document: Document[Node], node_id: str) -> tuple[Document[Node], OperationResult]:
        """
        Decrease heading level by one (e.g., h3 -> h2).

        Args:
            document: The document to operate on
            node_id: The ID of the node to promote

        Returns:
            Tuple of (modified document, operation result)
        """
        from doctk.lsp.protocols import OperationResult

        tree_builder = DocumentTreeBuilder(document)
        node = tree_builder.find_node(node_id)

        if node is None:
            return document, OperationResult(
                success=False, error=f"Node not found: {node_id}"
            )

        if not isinstance(node, Heading):
            return document, OperationResult(
                success=False, error=f"Node {node_id} is not a heading"
            )

        # Validate: already at minimum level?
        if node.level <= 1:
            return document, OperationResult(
                success=True,
                document=document.to_string(),
                error=None,
            )

        # Get the index of the node
        node_index = tree_builder.get_node_index(node_id)
        if node_index is None:
            return document, OperationResult(
                success=False, error=f"Could not find index for node: {node_id}"
            )

        # Create new promoted node
        promoted_node = node.promote()

        # Create new document with updated node
        new_nodes = list(document.nodes)
        new_nodes[node_index] = promoted_node
        new_document = Document(new_nodes)

        return new_document, OperationResult(
            success=True, document=new_document.to_string()
        )

    @staticmethod
    def demote(document: Document[Node], node_id: str) -> tuple[Document[Node], OperationResult]:
        """
        Increase heading level by one (e.g., h2 -> h3).

        Args:
            document: The document to operate on
            node_id: The ID of the node to demote

        Returns:
            Tuple of (modified document, operation result)
        """
        from doctk.lsp.protocols import OperationResult

        tree_builder = DocumentTreeBuilder(document)
        node = tree_builder.find_node(node_id)

        if node is None:
            return document, OperationResult(
                success=False, error=f"Node not found: {node_id}"
            )

        if not isinstance(node, Heading):
            return document, OperationResult(
                success=False, error=f"Node {node_id} is not a heading"
            )

        # Validate: already at maximum level?
        if node.level >= 6:
            return document, OperationResult(
                success=True,
                document=document.to_string(),
                error=None,
            )

        # Get the index of the node
        node_index = tree_builder.get_node_index(node_id)
        if node_index is None:
            return document, OperationResult(
                success=False, error=f"Could not find index for node: {node_id}"
            )

        # Create new demoted node
        demoted_node = node.demote()

        # Create new document with updated node
        new_nodes = list(document.nodes)
        new_nodes[node_index] = demoted_node
        new_document = Document(new_nodes)

        return new_document, OperationResult(
            success=True, document=new_document.to_string()
        )

    @staticmethod
    def validate_promote(document: Document[Node], node_id: str) -> ValidationResult:
        """
        Validate that a promote operation can be executed.

        Args:
            document: The document to validate against
            node_id: The ID of the node to promote

        Returns:
            ValidationResult indicating whether the operation is valid
        """
        from doctk.lsp.protocols import ValidationResult

        tree_builder = DocumentTreeBuilder(document)
        node = tree_builder.find_node(node_id)

        if node is None:
            return ValidationResult(valid=False, error=f"Node not found: {node_id}")

        if not isinstance(node, Heading):
            return ValidationResult(valid=False, error=f"Node {node_id} is not a heading")

        # Promote is always valid (at level 1 it's identity)
        return ValidationResult(valid=True)

    @staticmethod
    def validate_demote(document: Document[Node], node_id: str) -> ValidationResult:
        """
        Validate that a demote operation can be executed.

        Args:
            document: The document to validate against
            node_id: The ID of the node to demote

        Returns:
            ValidationResult indicating whether the operation is valid
        """
        from doctk.lsp.protocols import ValidationResult

        tree_builder = DocumentTreeBuilder(document)
        node = tree_builder.find_node(node_id)

        if node is None:
            return ValidationResult(valid=False, error=f"Node not found: {node_id}")

        if not isinstance(node, Heading):
            return ValidationResult(valid=False, error=f"Node {node_id} is not a heading")

        # Demote is always valid (at level 6 it's identity)
        return ValidationResult(valid=True)

    @staticmethod
    def move_up(document: Document[Node], node_id: str) -> tuple[Document[Node], OperationResult]:
        """
        Move a node up in the sibling order.

        Args:
            document: The document to operate on
            node_id: The ID of the node to move up

        Returns:
            Tuple of (modified document, operation result)
        """
        from doctk.lsp.protocols import OperationResult

        tree_builder = DocumentTreeBuilder(document)
        node = tree_builder.find_node(node_id)

        if node is None:
            return document, OperationResult(
                success=False, error=f"Node not found: {node_id}"
            )

        if not isinstance(node, Heading):
            return document, OperationResult(
                success=False, error=f"Node {node_id} is not a heading"
            )

        # Get the index of the node
        node_index = tree_builder.get_node_index(node_id)
        if node_index is None:
            return document, OperationResult(
                success=False, error=f"Could not find index for node: {node_id}"
            )

        # Check if already at the top (first sibling of its level)
        if node_index == 0:
            return document, OperationResult(
                success=True,
                document=document.to_string(),
                error=None,
            )

        # Find the previous sibling (same level or higher)
        prev_index = node_index - 1
        while prev_index >= 0:
            prev_node = document.nodes[prev_index]
            if isinstance(prev_node, Heading):
                # Found a heading - check if it's a valid swap target
                if prev_node.level <= node.level:
                    break
            prev_index -= 1

        # If we can't find a valid previous sibling, stay in place
        if prev_index < 0:
            return document, OperationResult(
                success=True,
                document=document.to_string(),
                error=None,
            )

        # Swap the nodes
        new_nodes = list(document.nodes)
        new_nodes[prev_index], new_nodes[node_index] = (
            new_nodes[node_index],
            new_nodes[prev_index],
        )
        new_document = Document(new_nodes)

        return new_document, OperationResult(
            success=True, document=new_document.to_string()
        )

    @staticmethod
    def move_down(
        document: Document[Node], node_id: str
    ) -> tuple[Document[Node], OperationResult]:
        """
        Move a node down in the sibling order.

        Args:
            document: The document to operate on
            node_id: The ID of the node to move down

        Returns:
            Tuple of (modified document, operation result)
        """
        from doctk.lsp.protocols import OperationResult

        tree_builder = DocumentTreeBuilder(document)
        node = tree_builder.find_node(node_id)

        if node is None:
            return document, OperationResult(
                success=False, error=f"Node not found: {node_id}"
            )

        if not isinstance(node, Heading):
            return document, OperationResult(
                success=False, error=f"Node {node_id} is not a heading"
            )

        # Get the index of the node
        node_index = tree_builder.get_node_index(node_id)
        if node_index is None:
            return document, OperationResult(
                success=False, error=f"Could not find index for node: {node_id}"
            )

        # Check if already at the bottom (last sibling of its level)
        if node_index >= len(document.nodes) - 1:
            return document, OperationResult(
                success=True,
                document=document.to_string(),
                error=None,
            )

        # Find the next sibling (same level or higher)
        next_index = node_index + 1
        while next_index < len(document.nodes):
            next_node = document.nodes[next_index]
            if isinstance(next_node, Heading):
                # Found a heading - check if it's a valid swap target
                if next_node.level <= node.level:
                    break
            next_index += 1

        # If we can't find a valid next sibling, stay in place
        if next_index >= len(document.nodes):
            return document, OperationResult(
                success=True,
                document=document.to_string(),
                error=None,
            )

        # Swap the nodes
        new_nodes = list(document.nodes)
        new_nodes[next_index], new_nodes[node_index] = (
            new_nodes[node_index],
            new_nodes[next_index],
        )
        new_document = Document(new_nodes)

        return new_document, OperationResult(
            success=True, document=new_document.to_string()
        )

    @staticmethod
    def validate_move_up(document: Document[Node], node_id: str) -> ValidationResult:
        """
        Validate that a move_up operation can be executed.

        Args:
            document: The document to validate against
            node_id: The ID of the node to move up

        Returns:
            ValidationResult indicating whether the operation is valid
        """
        from doctk.lsp.protocols import ValidationResult

        tree_builder = DocumentTreeBuilder(document)
        node = tree_builder.find_node(node_id)

        if node is None:
            return ValidationResult(valid=False, error=f"Node not found: {node_id}")

        if not isinstance(node, Heading):
            return ValidationResult(valid=False, error=f"Node {node_id} is not a heading")

        # Move up is always valid (stays in place if already at top)
        return ValidationResult(valid=True)

    @staticmethod
    def validate_move_down(document: Document[Node], node_id: str) -> ValidationResult:
        """
        Validate that a move_down operation can be executed.

        Args:
            document: The document to validate against
            node_id: The ID of the node to move down

        Returns:
            ValidationResult indicating whether the operation is valid
        """
        from doctk.lsp.protocols import ValidationResult

        tree_builder = DocumentTreeBuilder(document)
        node = tree_builder.find_node(node_id)

        if node is None:
            return ValidationResult(valid=False, error=f"Node not found: {node_id}")

        if not isinstance(node, Heading):
            return ValidationResult(valid=False, error=f"Node {node_id} is not a heading")

        # Move down is always valid (stays in place if already at bottom)
        return ValidationResult(valid=True)

    @staticmethod
    def nest(
        document: Document[Node], node_id: str, parent_id: str
    ) -> tuple[Document[Node], OperationResult]:
        """
        Nest a node under a new parent (make it a child of the parent).

        This operation moves the node to immediately after the parent and
        adjusts its level to be parent.level + 1.

        Args:
            document: The document to operate on
            node_id: The ID of the node to nest
            parent_id: The ID of the parent node

        Returns:
            Tuple of (modified document, operation result)
        """
        from doctk.lsp.protocols import OperationResult

        tree_builder = DocumentTreeBuilder(document)
        node = tree_builder.find_node(node_id)
        parent = tree_builder.find_node(parent_id)

        if node is None:
            return document, OperationResult(
                success=False, error=f"Node not found: {node_id}"
            )

        if parent is None:
            return document, OperationResult(
                success=False, error=f"Parent node not found: {parent_id}"
            )

        if not isinstance(node, Heading):
            return document, OperationResult(
                success=False, error=f"Node {node_id} is not a heading"
            )

        if not isinstance(parent, Heading):
            return document, OperationResult(
                success=False, error=f"Parent node {parent_id} is not a heading"
            )

        # Get indices
        node_index = tree_builder.get_node_index(node_id)
        parent_index = tree_builder.get_node_index(parent_id)

        if node_index is None or parent_index is None:
            return document, OperationResult(
                success=False, error="Could not find node indices"
            )

        # Calculate new level for the node
        new_level = min(6, parent.level + 1)

        # Create new node with adjusted level
        nested_node = Heading(
            level=new_level,
            text=node.text,
            children=node.children,
            metadata=node.metadata,
        )

        # Create new node list with the node moved after parent
        new_nodes = list(document.nodes)

        # Remove node from current position
        new_nodes.pop(node_index)

        # Adjust parent index if node was before parent
        if node_index < parent_index:
            parent_index -= 1

        # Insert node after parent
        new_nodes.insert(parent_index + 1, nested_node)

        new_document = Document(new_nodes)

        return new_document, OperationResult(
            success=True, document=new_document.to_string()
        )

    @staticmethod
    def unnest(document: Document[Node], node_id: str) -> tuple[Document[Node], OperationResult]:
        """
        Move a node up one level in the hierarchy (decrease level by 1).

        This is essentially a promote operation that represents "unnesting"
        from a parent section.

        Args:
            document: The document to operate on
            node_id: The ID of the node to unnest

        Returns:
            Tuple of (modified document, operation result)
        """
        from doctk.lsp.protocols import OperationResult

        tree_builder = DocumentTreeBuilder(document)
        node = tree_builder.find_node(node_id)

        if node is None:
            return document, OperationResult(
                success=False, error=f"Node not found: {node_id}"
            )

        if not isinstance(node, Heading):
            return document, OperationResult(
                success=False, error=f"Node {node_id} is not a heading"
            )

        # Validate: already at minimum level?
        if node.level <= 1:
            return document, OperationResult(
                success=True,
                document=document.to_string(),
                error=None,
            )

        # Get the index of the node
        node_index = tree_builder.get_node_index(node_id)
        if node_index is None:
            return document, OperationResult(
                success=False, error=f"Could not find index for node: {node_id}"
            )

        # Create new unnested node (promote by one level)
        unnested_node = node.promote()

        # Create new document with updated node
        new_nodes = list(document.nodes)
        new_nodes[node_index] = unnested_node
        new_document = Document(new_nodes)

        return new_document, OperationResult(
            success=True, document=new_document.to_string()
        )

    @staticmethod
    def validate_nest(
        document: Document[Node], node_id: str, parent_id: str
    ) -> ValidationResult:
        """
        Validate that a nest operation can be executed.

        Args:
            document: The document to validate against
            node_id: The ID of the node to nest
            parent_id: The ID of the parent node

        Returns:
            ValidationResult indicating whether the operation is valid
        """
        from doctk.lsp.protocols import ValidationResult

        tree_builder = DocumentTreeBuilder(document)
        node = tree_builder.find_node(node_id)
        parent = tree_builder.find_node(parent_id)

        if node is None:
            return ValidationResult(valid=False, error=f"Node not found: {node_id}")

        if parent is None:
            return ValidationResult(valid=False, error=f"Parent node not found: {parent_id}")

        if not isinstance(node, Heading):
            return ValidationResult(valid=False, error=f"Node {node_id} is not a heading")

        if not isinstance(parent, Heading):
            return ValidationResult(
                valid=False, error=f"Parent node {parent_id} is not a heading"
            )

        # Can't nest a node under itself
        if node_id == parent_id:
            return ValidationResult(valid=False, error="Cannot nest a node under itself")

        # Nest is valid as long as the result wouldn't exceed level 6
        new_level = parent.level + 1
        if new_level > 6:
            return ValidationResult(
                valid=False, error="Cannot nest: would exceed maximum heading level (6)"
            )

        return ValidationResult(valid=True)

    @staticmethod
    def validate_unnest(document: Document[Node], node_id: str) -> ValidationResult:
        """
        Validate that an unnest operation can be executed.

        Args:
            document: The document to validate against
            node_id: The ID of the node to unnest

        Returns:
            ValidationResult indicating whether the operation is valid
        """
        from doctk.lsp.protocols import ValidationResult

        tree_builder = DocumentTreeBuilder(document)
        node = tree_builder.find_node(node_id)

        if node is None:
            return ValidationResult(valid=False, error=f"Node not found: {node_id}")

        if not isinstance(node, Heading):
            return ValidationResult(valid=False, error=f"Node {node_id} is not a heading")

        # Unnest is always valid (at level 1 it's identity)
        return ValidationResult(valid=True)
