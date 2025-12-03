"""Document structure operations for the core integration layer."""

from __future__ import annotations

from doctk.core import Document, Heading, Node
from doctk.identity import NodeId
from doctk.integration.protocols import ModifiedRange, OperationResult, TreeNode, ValidationResult
from doctk.internal_ops import InternalOperations


class DocumentTreeBuilder:
    """Builds a tree representation of a document with node IDs."""

    def __init__(self, document: Document[Node], source_text: str | None = None):
        """
        Initialize the tree builder.

        Args:
            document: The document to build a tree from
            source_text: Optional original source text. If provided, this will be used
                        for line positioning instead of reconstructing from the document.
                        This is important because document reconstruction may add extra
                        blank lines that don't exist in the original source.
        """
        self.document = document
        self.source_text = source_text
        self.node_map: dict[str, Node] = {}
        self.parent_map: dict[str, str] = {}
        self._line_position_cache: dict[int, int] = {}  # Cache: node_index -> line_number
        self._line_count_cache: dict[int, int] = {}  # Cache: node_index -> line_count
        self._build_node_map()
        self._build_line_position_cache()

    def _build_node_map(self) -> None:
        """Build a map of node IDs to nodes."""
        heading_counter: dict[int, int] = {}

        for node in self.document.nodes:
            if isinstance(node, Heading):
                level = node.level
                heading_counter[level] = heading_counter.get(level, 0) + 1
                node_id = f"h{level}-{heading_counter[level] - 1}"
                self.node_map[node_id] = node

    def _build_line_position_cache(self) -> None:
        """
        Build a cache of line positions and line counts for all nodes (O(n) operation).

        This eliminates the O(n²) complexity from repeated line calculations.
        Includes fallback handling for nodes that cannot be matched.
        """
        # Get document text and split into lines
        # Use source_text if provided, otherwise reconstruct from document
        # Using source_text is critical for accurate line positioning because
        # document reconstruction may add extra blank lines
        doc_text = self.source_text if self.source_text is not None else self.document.to_string()
        lines = doc_text.split("\n")

        current_line = 0
        for node_index, node in enumerate(self.document.nodes):
            # Get the text for this node
            temp_doc = Document([node])
            search_text = temp_doc.to_string().strip()
            num_node_lines = search_text.count("\n") + 1

            # Cache line count to avoid repeated Document creation
            self._line_count_cache[node_index] = num_node_lines

            # Find this text in the remaining lines
            found = False
            for line_idx in range(current_line, len(lines)):
                line_content = lines[line_idx].rstrip("\n")
                # Check if this line starts the node
                # Improved matching: check for empty lines to avoid false positives
                if line_content and (
                    search_text.startswith(line_content)
                    or line_content.startswith(search_text.split("\n")[0])
                ):
                    # Found the start of this node
                    self._line_position_cache[node_index] = line_idx
                    found = True

                    # Skip past this node
                    current_line = line_idx + num_node_lines
                    # Skip any blank lines after this node
                    while current_line < len(lines) and lines[current_line].strip() == "":
                        current_line += 1
                    break

            # Fallback: if node not found, estimate position
            if not found:
                self._line_position_cache[node_index] = current_line
                current_line += num_node_lines

    def build_tree_with_ids(self) -> TreeNode:
        """
        Build complete tree structure with IDs assigned.

        This creates a hierarchical tree structure where each heading node
        has an ID assigned by the backend (single source of truth).

        Returns:
            TreeNode representing the document root with all children
        """
        # Create a virtual root node
        root = TreeNode(
            id="root",
            label="Document",
            level=0,
            line=0,
            column=0,
            children=[],
        )

        # Track the current path in the tree (stack of nodes by level)
        # level 0 is the root, level 1-6 are heading levels
        level_stack: list[TreeNode] = [root]

        # Counter for generating node IDs
        heading_counter: dict[int, int] = {}

        # Build the tree by iterating through all nodes
        for node_index, node in enumerate(self.document.nodes):
            if isinstance(node, Heading):
                level = node.level
                heading_counter[level] = heading_counter.get(level, 0) + 1
                node_id = f"h{level}-{heading_counter[level] - 1}"

                # Get line number from cache (O(1) lookup instead of O(n) calculation)
                node_line = self._line_position_cache.get(node_index, 0)

                # Create TreeNode for this heading
                tree_node = TreeNode(
                    id=node_id,
                    label=node.text,
                    level=level,
                    line=node_line,
                    column=0,
                    children=[],
                )

                # Find the appropriate parent
                # The parent is the last node in the stack with level < current level
                while len(level_stack) > 1 and level_stack[-1].level >= level:
                    level_stack.pop()

                # Add this node to the parent's children
                parent = level_stack[-1]
                parent.children.append(tree_node)

                # Push this node onto the stack
                level_stack.append(tree_node)

        return root

    def get_node_line_position(self, node_index: int) -> int | None:
        """
        Get the cached line position for a node (public accessor method).

        Args:
            node_index: Index of the node in the document

        Returns:
            Line number (0-indexed) or None if not found
        """
        return self._line_position_cache.get(node_index)

    def get_node_line_count(self, node_index: int) -> int | None:
        """
        Get the cached line count for a node (public accessor method).

        Args:
            node_index: Index of the node in the document

        Returns:
            Number of lines the node occupies, or None if not found
        """
        return self._line_count_cache.get(node_index)

    def find_node(self, node_id: str) -> Node | None:
        """
        Find a node by its ID.

        Args:
            node_id: The ID of the node to find

        Returns:
            The node if found, None otherwise
        """
        return self.node_map.get(node_id)

    def get_stable_node_id(self, temp_node_id: str) -> NodeId | None:
        """
        Get the stable NodeId for a temporary node ID.

        Args:
            temp_node_id: Temporary ID like "h2-0"

        Returns:
            The stable NodeId if found, None otherwise
        """
        node = self.find_node(temp_node_id)
        if node is None:
            return None

        # Ensure node has a stable ID
        if node.id is None:
            # Generate stable ID if not present
            node.id = NodeId.from_node(node)

        return node.id

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

    def get_section_range(self, node_id: str) -> tuple[int, int] | None:
        """
        Get the range of indices for a complete section.

        A section includes the heading and all nodes until the next heading
        of the same or lower level.

        Args:
            node_id: The ID of the heading node

        Returns:
            Tuple of (start_index, end_index) inclusive, or None if not found
        """
        node = self.find_node(node_id)
        if node is None or not isinstance(node, Heading):
            return None

        start_index = self.get_node_index(node_id)
        if start_index is None:
            return None

        # Find the end of this section (next heading of same or lower level)
        end_index = start_index
        for i in range(start_index + 1, len(self.document.nodes)):
            next_node = self.document.nodes[i]
            if isinstance(next_node, Heading) and next_node.level <= node.level:
                # Found the start of the next section at the same or higher level
                break
            end_index = i

        return (start_index, end_index)


class DiffComputer:
    """Computes granular text ranges modified by document operations."""

    @staticmethod
    def compute_ranges(
        original_doc: Document[Node],
        modified_doc: Document[Node],
        affected_node_ids: list[str],
    ) -> list[ModifiedRange]:
        """
        Compute the specific text ranges that changed.

        Args:
            original_doc: The original document before the operation
            modified_doc: The modified document after the operation
            affected_node_ids: List of node IDs that were affected by the operation

        Returns:
            List of ModifiedRange objects representing the changes
        """
        # Convert documents to text and split into lines
        original_text = original_doc.to_string()
        modified_text = modified_doc.to_string()
        original_lines = original_text.splitlines(keepends=True)
        modified_lines = modified_text.splitlines(keepends=True)

        # Build node maps for both documents (created once for performance)
        original_builder = DocumentTreeBuilder(original_doc)
        modified_builder = DocumentTreeBuilder(modified_doc)

        ranges: list[ModifiedRange] = []

        # For each affected node, compute the text range that changed
        for node_id in affected_node_ids:
            # Find the node in the original document
            original_node = original_builder.find_node(node_id)
            if original_node is None:
                continue  # Node doesn't exist in original document

            # Find the corresponding node in the modified document
            # Use content-based matching instead of index because operations
            # like move_up, move_down, and nest change node positions
            modified_node = DiffComputer._find_matching_node(original_node, modified_doc.nodes)

            if modified_node is None:
                # Node was deleted or cannot be matched
                original_range = DiffComputer._get_node_line_range(
                    original_doc, original_node, original_builder
                )
                if original_range is not None:
                    start_line, end_line = original_range
                    ranges.append(
                        ModifiedRange(
                            start_line=start_line,
                            start_column=0,
                            end_line=end_line,
                            end_column=len(original_lines[end_line])
                            if end_line < len(original_lines)
                            else 0,
                            new_text="",
                        )
                    )
                continue

            # Get line ranges for the node in both documents
            original_range = DiffComputer._get_node_line_range(
                original_doc, original_node, original_builder
            )
            modified_range = DiffComputer._get_node_line_range(
                modified_doc, modified_node, modified_builder
            )

            # Compute the modified range
            if original_range is not None and modified_range is not None:
                # Node was modified
                start_line, end_line = original_range
                mod_start_line, mod_end_line = modified_range

                # Extract the new text from modified document
                new_text = "".join(modified_lines[mod_start_line : mod_end_line + 1])

                ranges.append(
                    ModifiedRange(
                        start_line=start_line,
                        start_column=0,
                        end_line=end_line,
                        end_column=len(original_lines[end_line])
                        if end_line < len(original_lines)
                        else 0,
                        new_text=new_text,
                    )
                )

        return ranges

    @staticmethod
    def _find_matching_node(original_node: Node, modified_nodes: list[Node]) -> Node | None:
        """
        Find a node in the modified document that matches the original node by content.

        This is necessary because operations like move_up, move_down, and nest
        change node positions, making index-based matching unreliable.

        Args:
            original_node: The node to find a match for
            modified_nodes: List of nodes in the modified document

        Returns:
            The matching node, or None if no match found
        """
        # Match headings by text (level may change in promote/demote)
        if isinstance(original_node, Heading):
            for node in modified_nodes:
                if isinstance(node, Heading) and node.text == original_node.text:
                    return node

        # Match paragraphs by content
        from doctk.core import Paragraph

        if isinstance(original_node, Paragraph):
            for node in modified_nodes:
                if isinstance(node, Paragraph) and node.content == original_node.content:
                    return node

        # Match other node types by their content
        # For now, just check if it's the same type and content
        for node in modified_nodes:
            if type(node) == type(original_node):  # noqa: E721
                # Use string representation as a fallback
                orig_str = str(original_node)
                node_str = str(node)
                if orig_str == node_str:
                    return node

        return None

    @staticmethod
    def _get_node_line_range(
        doc: Document[Node], node: Node | None, builder: DocumentTreeBuilder
    ) -> tuple[int, int] | None:
        """
        Get the line range for a node in the document (uses cached positions).

        Args:
            doc: The document containing the node
            node: The node to find the range for
            builder: The DocumentTreeBuilder for this document (contains line position cache)

        Returns:
            Tuple of (start_line, end_line) or None if not found
        """
        if node is None:
            return None

        # Find the node index
        try:
            node_index = doc.nodes.index(node)
        except ValueError:
            return None

        # Use cached line position from builder via public accessor (O(1) lookup)
        start_line = builder.get_node_line_position(node_index)
        if start_line is None:
            return None

        # Use cached line count to avoid repeated Document creation
        num_node_lines = builder.get_node_line_count(node_index)
        if num_node_lines is None:
            # Fallback: calculate line count if not cached
            temp_doc = Document([node])
            search_text = temp_doc.to_string().strip()
            num_node_lines = search_text.count("\n") + 1

        end_line = start_line + num_node_lines - 1

        return (start_line, end_line)


class StructureOperations:
    """High-level operations for document structure manipulation."""

    @staticmethod
    def _ensure_document_has_ids(document: Document[Node]) -> Document[Node]:
        """
        Ensure all nodes in the document have stable IDs.

        This is needed because InternalOperations requires nodes to have IDs
        for the document.find_node() method to work.

        Args:
            document: The document to process

        Returns:
            A new document with all nodes having stable IDs
        """
        nodes_with_ids = []
        for node in document.nodes:
            if node.id is None:
                node.id = NodeId.from_node(node)
            nodes_with_ids.append(node)
        return Document(nodes_with_ids)

    @staticmethod
    def promote(document: Document[Node], node_id: str) -> OperationResult:
        """
        Decrease heading level by one (e.g., h3 -> h2).

        Args:
            document: The document to operate on
            node_id: The ID of the node to promote (temporary ID like "h2-0")

        Returns:
            Operation result with serialized document
        """
        # Ensure all nodes have IDs
        doc_with_ids = StructureOperations._ensure_document_has_ids(document)

        # Map temporary ID to stable NodeId
        tree_builder = DocumentTreeBuilder(doc_with_ids)
        stable_id = tree_builder.get_stable_node_id(node_id)

        if stable_id is None:
            return OperationResult(success=False, error=f"Node not found: {node_id}")

        # Delegate to internal operations
        internal_result = InternalOperations.promote(doc_with_ids, stable_id)

        if not internal_result.success:
            return OperationResult(
                success=False,
                error=internal_result.error,
            )

        # Serialize document at boundary
        serialized_doc = internal_result.document.to_string()

        # Compute modified ranges for JSON-RPC response
        modified_ranges = DiffComputer.compute_ranges(
            original_doc=document,
            modified_doc=internal_result.document,
            affected_node_ids=[node_id],
        )

        return OperationResult(
            success=True,
            document=serialized_doc,
            modified_ranges=modified_ranges,
        )

    @staticmethod
    def demote(document: Document[Node], node_id: str) -> OperationResult:
        """
        Increase heading level by one (e.g., h2 -> h3).

        Args:
            document: The document to operate on
            node_id: The ID of the node to demote (temporary ID like "h2-0")

        Returns:
            Operation result with serialized document
        """
        # Ensure all nodes have IDs
        doc_with_ids = StructureOperations._ensure_document_has_ids(document)

        # Map temporary ID to stable NodeId
        tree_builder = DocumentTreeBuilder(doc_with_ids)
        stable_id = tree_builder.get_stable_node_id(node_id)

        if stable_id is None:
            return OperationResult(success=False, error=f"Node not found: {node_id}")

        # Delegate to internal operations
        internal_result = InternalOperations.demote(doc_with_ids, stable_id)

        if not internal_result.success:
            return OperationResult(
                success=False,
                error=internal_result.error,
            )

        # Serialize document at boundary
        serialized_doc = internal_result.document.to_string()

        # Compute modified ranges for JSON-RPC response
        modified_ranges = DiffComputer.compute_ranges(
            original_doc=document,
            modified_doc=internal_result.document,
            affected_node_ids=[node_id],
        )

        return OperationResult(
            success=True,
            document=serialized_doc,
            modified_ranges=modified_ranges,
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
        tree_builder = DocumentTreeBuilder(document)
        node = tree_builder.find_node(node_id)

        if node is None:
            return ValidationResult(valid=False, error=f"Node not found: {node_id}")

        if not isinstance(node, Heading):
            return ValidationResult(valid=False, error=f"Node {node_id} is not a heading")

        # Demote is always valid (at level 6 it's identity)
        return ValidationResult(valid=True)

    @staticmethod
    def move_up(document: Document[Node], node_id: str) -> OperationResult:
        """
        Move a node up in the sibling order.

        Args:
            document: The document to operate on
            node_id: The ID of the node to move up (temporary ID like "h2-0")

        Returns:
            Operation result with serialized document
        """
        # Ensure all nodes have IDs
        doc_with_ids = StructureOperations._ensure_document_has_ids(document)

        # Map temporary ID to stable NodeId
        tree_builder = DocumentTreeBuilder(doc_with_ids)
        stable_id = tree_builder.get_stable_node_id(node_id)

        if stable_id is None:
            return OperationResult(success=False, error=f"Node not found: {node_id}")

        # Delegate to internal operations
        internal_result = InternalOperations.move_up(doc_with_ids, stable_id)

        if not internal_result.success:
            return OperationResult(
                success=False,
                error=internal_result.error,
            )

        # Serialize document at boundary
        serialized_doc = internal_result.document.to_string()

        # Compute modified ranges for JSON-RPC response
        modified_ranges = DiffComputer.compute_ranges(
            original_doc=document,
            modified_doc=internal_result.document,
            affected_node_ids=[node_id],
        )

        return OperationResult(
            success=True,
            document=serialized_doc,
            modified_ranges=modified_ranges,
        )

    @staticmethod
    def move_down(document: Document[Node], node_id: str) -> OperationResult:
        """
        Move a node down in the sibling order.

        Args:
            document: The document to operate on
            node_id: The ID of the node to move down (temporary ID like "h2-0")

        Returns:
            Operation result with serialized document
        """
        # Ensure all nodes have IDs
        doc_with_ids = StructureOperations._ensure_document_has_ids(document)

        # Map temporary ID to stable NodeId
        tree_builder = DocumentTreeBuilder(doc_with_ids)
        stable_id = tree_builder.get_stable_node_id(node_id)

        if stable_id is None:
            return OperationResult(success=False, error=f"Node not found: {node_id}")

        # Delegate to internal operations
        internal_result = InternalOperations.move_down(doc_with_ids, stable_id)

        if not internal_result.success:
            return OperationResult(
                success=False,
                error=internal_result.error,
            )

        # Serialize document at boundary
        serialized_doc = internal_result.document.to_string()

        # Compute modified ranges for JSON-RPC response
        modified_ranges = DiffComputer.compute_ranges(
            original_doc=document,
            modified_doc=internal_result.document,
            affected_node_ids=[node_id],
        )

        return OperationResult(
            success=True,
            document=serialized_doc,
            modified_ranges=modified_ranges,
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
        tree_builder = DocumentTreeBuilder(document)
        node = tree_builder.find_node(node_id)

        if node is None:
            return ValidationResult(valid=False, error=f"Node not found: {node_id}")

        if not isinstance(node, Heading):
            return ValidationResult(valid=False, error=f"Node {node_id} is not a heading")

        # Move down is always valid (stays in place if already at bottom)
        return ValidationResult(valid=True)

    @staticmethod
    def nest(document: Document[Node], node_id: str, parent_id: str) -> OperationResult:
        """
        Nest a node under a new parent (make it a child of the parent).

        This operation moves the node to immediately after the parent and
        adjusts its level to be parent.level + 1.

        Args:
            document: The document to operate on
            node_id: The ID of the node to nest (temporary ID like "h2-0")
            parent_id: The ID of the parent node (temporary ID like "h1-0")

        Returns:
            Operation result with serialized document
        """
        # Ensure all nodes have IDs
        doc_with_ids = StructureOperations._ensure_document_has_ids(document)

        # Map temporary IDs to stable NodeIds
        tree_builder = DocumentTreeBuilder(doc_with_ids)
        stable_node_id = tree_builder.get_stable_node_id(node_id)
        stable_parent_id = tree_builder.get_stable_node_id(parent_id)

        if stable_node_id is None:
            return OperationResult(success=False, error=f"Node not found: {node_id}")

        if stable_parent_id is None:
            return OperationResult(success=False, error=f"Parent node not found: {parent_id}")

        # Delegate to internal operations
        internal_result = InternalOperations.nest(doc_with_ids, stable_node_id, stable_parent_id)

        if not internal_result.success:
            return OperationResult(
                success=False,
                error=internal_result.error,
            )

        # Serialize document at boundary
        serialized_doc = internal_result.document.to_string()

        # Compute modified ranges for JSON-RPC response
        modified_ranges = DiffComputer.compute_ranges(
            original_doc=document,
            modified_doc=internal_result.document,
            affected_node_ids=[node_id],
        )

        return OperationResult(
            success=True,
            document=serialized_doc,
            modified_ranges=modified_ranges,
        )

    @staticmethod
    def unnest(document: Document[Node], node_id: str) -> OperationResult:
        """
        Move a node up one level in the hierarchy (decrease level by 1).

        This is essentially a promote operation that represents "unnesting"
        from a parent section.

        Args:
            document: The document to operate on
            node_id: The ID of the node to unnest (temporary ID like "h2-0")

        Returns:
            Operation result with serialized document
        """
        # Ensure all nodes have IDs
        doc_with_ids = StructureOperations._ensure_document_has_ids(document)

        # Map temporary ID to stable NodeId
        tree_builder = DocumentTreeBuilder(doc_with_ids)
        stable_id = tree_builder.get_stable_node_id(node_id)

        if stable_id is None:
            return OperationResult(success=False, error=f"Node not found: {node_id}")

        # Delegate to internal operations
        internal_result = InternalOperations.unnest(doc_with_ids, stable_id)

        if not internal_result.success:
            return OperationResult(
                success=False,
                error=internal_result.error,
            )

        # Serialize document at boundary
        serialized_doc = internal_result.document.to_string()

        # Compute modified ranges for JSON-RPC response
        modified_ranges = DiffComputer.compute_ranges(
            original_doc=document,
            modified_doc=internal_result.document,
            affected_node_ids=[node_id],
        )

        return OperationResult(
            success=True,
            document=serialized_doc,
            modified_ranges=modified_ranges,
        )

    @staticmethod
    def validate_nest(document: Document[Node], node_id: str, parent_id: str) -> ValidationResult:
        """
        Validate that a nest operation can be executed.

        Args:
            document: The document to validate against
            node_id: The ID of the node to nest
            parent_id: The ID of the parent node

        Returns:
            ValidationResult indicating whether the operation is valid
        """
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
            return ValidationResult(valid=False, error=f"Parent node {parent_id} is not a heading")

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
        tree_builder = DocumentTreeBuilder(document)
        node = tree_builder.find_node(node_id)

        if node is None:
            return ValidationResult(valid=False, error=f"Node not found: {node_id}")

        if not isinstance(node, Heading):
            return ValidationResult(valid=False, error=f"Node {node_id} is not a heading")

        # Unnest is always valid (at level 1 it's identity)
        return ValidationResult(valid=True)

    @staticmethod
    def delete(document: Document[Node], node_id: str) -> OperationResult:
        """
        Delete a section (heading and all its content/subsections).

        Args:
            document: The document to operate on
            node_id: The ID of the node to delete

        Returns:
            Operation result
        """
        tree_builder = DocumentTreeBuilder(document)
        node = tree_builder.find_node(node_id)

        if node is None:
            return OperationResult(success=False, error=f"Node not found: {node_id}")

        if not isinstance(node, Heading):
            return OperationResult(success=False, error=f"Node {node_id} is not a heading")

        # Get the section range (start and end indices in document.nodes)
        section_range = tree_builder.get_section_range(node_id)
        if section_range is None:
            return OperationResult(
                success=False, error=f"Could not determine section range for {node_id}"
            )

        start_idx, end_idx = section_range

        # Create new document with the section removed
        # Note: end_idx is inclusive, so we use end_idx + 1 for the slice
        new_nodes = document.nodes[:start_idx] + document.nodes[end_idx + 1 :]
        modified_doc = Document(nodes=new_nodes)

        # Compute modified ranges for granular edits
        # For delete operations, we need to manually compute the range because
        # DiffComputer only processes individual nodes, not entire sections
        modified_ranges: list[ModifiedRange] = []

        # Get the line range for the entire section being deleted
        first_node = document.nodes[start_idx]
        last_node = document.nodes[end_idx]

        first_node_range = DiffComputer._get_node_line_range(document, first_node, tree_builder)
        last_node_range = DiffComputer._get_node_line_range(document, last_node, tree_builder)

        if first_node_range is not None and last_node_range is not None:
            # Get the full document text for column calculation
            original_text = document.to_string()
            original_lines = original_text.splitlines(keepends=True)

            start_line = first_node_range[0]
            end_line = last_node_range[1]

            # Extend to include trailing blank line that markdown writer adds
            # The markdown writer appends a blank line after each node (markdown.py:41-50)
            # We need to delete this separator to avoid doubled blank lines
            if end_line + 1 < len(original_lines):
                end_line = end_line + 1
                end_column = 0  # Start of next line
            else:
                end_column = len(original_lines[end_line]) if end_line < len(original_lines) else 0

            # Create a deletion range (empty new_text)
            modified_ranges.append(
                ModifiedRange(
                    start_line=start_line,
                    start_column=0,
                    end_line=end_line,
                    end_column=end_column,
                    new_text="",
                )
            )

        return OperationResult(
            success=True, document=modified_doc.to_string(), modified_ranges=modified_ranges
        )

    @staticmethod
    def validate_delete(document: Document[Node], node_id: str) -> ValidationResult:
        """
        Validate that a delete operation can be executed.

        Args:
            document: The document to validate against
            node_id: The ID of the node to delete

        Returns:
            ValidationResult indicating whether the operation is valid
        """
        tree_builder = DocumentTreeBuilder(document)
        node = tree_builder.find_node(node_id)

        if node is None:
            return ValidationResult(valid=False, error=f"Node not found: {node_id}")

        if not isinstance(node, Heading):
            return ValidationResult(valid=False, error=f"Node {node_id} is not a heading")

        # Delete is always valid for any heading
        return ValidationResult(valid=True)
