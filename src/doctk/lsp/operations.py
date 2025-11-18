"""Document structure operations for the LSP integration layer."""

from __future__ import annotations

from doctk.core import Document, Heading, Node
from doctk.lsp.protocols import ModifiedRange, OperationResult, TreeNode, ValidationResult


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

                # Create TreeNode for this heading
                tree_node = TreeNode(
                    id=node_id,
                    label=node.text,
                    level=level,
                    line=node_index,  # Use node index as line for now
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
        Get the line range for a node in the document.

        Args:
            doc: The document containing the node
            node: The node to find the range for
            builder: The DocumentTreeBuilder for this document

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

        # Get the full document text and split into lines
        full_text = doc.to_string()
        lines = full_text.splitlines(keepends=True)

        # Find where this node's text appears in the document
        current_line = 0
        for i in range(node_index + 1):
            # Get the text for node i
            temp_doc_i = Document([doc.nodes[i]])
            search_text = temp_doc_i.to_string().strip()

            # Find this text in the remaining lines
            found = False
            for line_idx in range(current_line, len(lines)):
                line_content = lines[line_idx].rstrip("\n")
                if search_text.startswith(line_content) or line_content.startswith(
                    search_text.split("\n")[0]
                ):
                    # Found the start of this node
                    if i == node_index:
                        # This is the node we're looking for
                        start_line = line_idx
                        # Count how many lines this node occupies
                        num_node_lines = search_text.count("\n") + 1
                        end_line = start_line + num_node_lines - 1
                        return (start_line, end_line)
                    else:
                        # Skip past this node
                        num_node_lines = search_text.count("\n") + 1
                        current_line = line_idx + num_node_lines
                        # Skip any blank lines after this node
                        while current_line < len(lines) and lines[current_line].strip() == "":
                            current_line += 1
                        found = True
                        break
            if not found:
                return None

        return None


class StructureOperations:
    """High-level operations for document structure manipulation."""

    @staticmethod
    def promote(document: Document[Node], node_id: str) -> OperationResult:
        """
        Decrease heading level by one (e.g., h3 -> h2).

        Args:
            document: The document to operate on
            node_id: The ID of the node to promote

        Returns:
            Operation result
        """
        tree_builder = DocumentTreeBuilder(document)
        node = tree_builder.find_node(node_id)

        if node is None:
            return OperationResult(success=False, error=f"Node not found: {node_id}")

        if not isinstance(node, Heading):
            return OperationResult(success=False, error=f"Node {node_id} is not a heading")

        # Validate: already at minimum level?
        if node.level <= 1:
            return OperationResult(
                success=True,
                document=document.to_string(),
                error=None,
            )

        # Get the index of the node
        node_index = tree_builder.get_node_index(node_id)
        if node_index is None:
            return OperationResult(success=False, error=f"Could not find index for node: {node_id}")

        # Create new promoted node
        promoted_node = node.promote()

        # Create new document with updated node
        new_nodes = list(document.nodes)
        new_nodes[node_index] = promoted_node
        new_document = Document(new_nodes)

        # Compute modified ranges
        modified_ranges = DiffComputer.compute_ranges(
            original_doc=document,
            modified_doc=new_document,
            affected_node_ids=[node_id],
        )

        return OperationResult(
            success=True,
            document=new_document.to_string(),
            modified_ranges=modified_ranges,
        )

    @staticmethod
    def demote(document: Document[Node], node_id: str) -> OperationResult:
        """
        Increase heading level by one (e.g., h2 -> h3).

        Args:
            document: The document to operate on
            node_id: The ID of the node to demote

        Returns:
            Operation result
        """
        tree_builder = DocumentTreeBuilder(document)
        node = tree_builder.find_node(node_id)

        if node is None:
            return OperationResult(success=False, error=f"Node not found: {node_id}")

        if not isinstance(node, Heading):
            return OperationResult(success=False, error=f"Node {node_id} is not a heading")

        # Validate: already at maximum level?
        if node.level >= 6:
            return OperationResult(
                success=True,
                document=document.to_string(),
                error=None,
            )

        # Get the index of the node
        node_index = tree_builder.get_node_index(node_id)
        if node_index is None:
            return OperationResult(success=False, error=f"Could not find index for node: {node_id}")

        # Create new demoted node
        demoted_node = node.demote()

        # Create new document with updated node
        new_nodes = list(document.nodes)
        new_nodes[node_index] = demoted_node
        new_document = Document(new_nodes)

        # Compute modified ranges
        modified_ranges = DiffComputer.compute_ranges(
            original_doc=document,
            modified_doc=new_document,
            affected_node_ids=[node_id],
        )

        return OperationResult(
            success=True,
            document=new_document.to_string(),
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
            node_id: The ID of the node to move up

        Returns:
            Operation result
        """
        tree_builder = DocumentTreeBuilder(document)
        node = tree_builder.find_node(node_id)

        if node is None:
            return OperationResult(success=False, error=f"Node not found: {node_id}")

        if not isinstance(node, Heading):
            return OperationResult(success=False, error=f"Node {node_id} is not a heading")

        # Get the section range for the current node
        section_range = tree_builder.get_section_range(node_id)
        if section_range is None:
            return OperationResult(
                success=False, error=f"Could not find section for node: {node_id}"
            )

        section_start, section_end = section_range

        # Check if already at the top
        if section_start == 0:
            return OperationResult(
                success=True,
                document=document.to_string(),
                error=None,
            )

        # Find the previous sibling heading (same level or higher)
        prev_heading_index = section_start - 1
        while prev_heading_index >= 0:
            prev_node = document.nodes[prev_heading_index]
            if isinstance(prev_node, Heading) and prev_node.level <= node.level:
                break
            prev_heading_index -= 1

        # If we can't find a valid previous sibling, stay in place
        if prev_heading_index < 0:
            return OperationResult(
                success=True,
                document=document.to_string(),
                error=None,
            )

        # Get the section range for the previous sibling
        prev_node_id = None
        for nid, n in tree_builder.node_map.items():
            if n is document.nodes[prev_heading_index]:
                prev_node_id = nid
                break

        if prev_node_id is None:
            return OperationResult(success=False, error="Could not find previous section ID")

        prev_section_range = tree_builder.get_section_range(prev_node_id)
        if prev_section_range is None:
            return OperationResult(success=False, error="Could not find previous section range")

        prev_section_start, prev_section_end = prev_section_range

        # Move the entire current section to before the previous section
        new_nodes = list(document.nodes)
        current_section = new_nodes[section_start : section_end + 1]
        # Remove current section
        del new_nodes[section_start : section_end + 1]
        # Insert current section before previous section
        new_nodes[prev_section_start:prev_section_start] = current_section
        new_document = Document(new_nodes)

        # Collect all affected node IDs from the moved section
        affected_node_ids = [node_id]  # At minimum, the heading itself

        # Compute modified ranges
        modified_ranges = DiffComputer.compute_ranges(
            original_doc=document,
            modified_doc=new_document,
            affected_node_ids=affected_node_ids,
        )

        return OperationResult(
            success=True,
            document=new_document.to_string(),
            modified_ranges=modified_ranges,
        )

    @staticmethod
    def move_down(document: Document[Node], node_id: str) -> OperationResult:
        """
        Move a node down in the sibling order.

        Args:
            document: The document to operate on
            node_id: The ID of the node to move down

        Returns:
            Operation result
        """
        tree_builder = DocumentTreeBuilder(document)
        node = tree_builder.find_node(node_id)

        if node is None:
            return OperationResult(success=False, error=f"Node not found: {node_id}")

        if not isinstance(node, Heading):
            return OperationResult(success=False, error=f"Node {node_id} is not a heading")

        # Get the section range for the current node
        section_range = tree_builder.get_section_range(node_id)
        if section_range is None:
            return OperationResult(
                success=False, error=f"Could not find section for node: {node_id}"
            )

        section_start, section_end = section_range

        # Check if already at the bottom
        if section_end >= len(document.nodes) - 1:
            return OperationResult(
                success=True,
                document=document.to_string(),
                error=None,
            )

        # Find the next sibling heading (same level or higher)
        next_heading_index = section_end + 1
        while next_heading_index < len(document.nodes):
            next_node = document.nodes[next_heading_index]
            if isinstance(next_node, Heading) and next_node.level <= node.level:
                break
            next_heading_index += 1

        # If we can't find a valid next sibling, stay in place
        if next_heading_index >= len(document.nodes):
            return OperationResult(
                success=True,
                document=document.to_string(),
                error=None,
            )

        # Get the section range for the next sibling
        next_node_id = None
        for nid, n in tree_builder.node_map.items():
            if n is document.nodes[next_heading_index]:
                next_node_id = nid
                break

        if next_node_id is None:
            return OperationResult(success=False, error="Could not find next section ID")

        next_section_range = tree_builder.get_section_range(next_node_id)
        if next_section_range is None:
            return OperationResult(success=False, error="Could not find next section range")

        next_section_start, next_section_end = next_section_range

        # Move the entire current section to after the next section
        new_nodes = list(document.nodes)
        current_section = new_nodes[section_start : section_end + 1]
        # Remove current section
        del new_nodes[section_start : section_end + 1]
        # Calculate new insertion position (after removing current section)
        insert_pos = next_section_end - (section_end - section_start)
        # Insert current section after next section
        new_nodes[insert_pos:insert_pos] = current_section
        new_document = Document(new_nodes)

        # Collect all affected node IDs from the moved section
        affected_node_ids = [node_id]  # At minimum, the heading itself

        # Compute modified ranges
        modified_ranges = DiffComputer.compute_ranges(
            original_doc=document,
            modified_doc=new_document,
            affected_node_ids=affected_node_ids,
        )

        return OperationResult(
            success=True,
            document=new_document.to_string(),
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
            node_id: The ID of the node to nest
            parent_id: The ID of the parent node

        Returns:
            Operation result
        """
        tree_builder = DocumentTreeBuilder(document)
        node = tree_builder.find_node(node_id)
        parent = tree_builder.find_node(parent_id)

        if node is None:
            return OperationResult(success=False, error=f"Node not found: {node_id}")

        if parent is None:
            return OperationResult(success=False, error=f"Parent node not found: {parent_id}")

        if not isinstance(node, Heading):
            return OperationResult(success=False, error=f"Node {node_id} is not a heading")

        if not isinstance(parent, Heading):
            return OperationResult(success=False, error=f"Parent node {parent_id} is not a heading")

        # Get section ranges
        section_range = tree_builder.get_section_range(node_id)
        parent_section_range = tree_builder.get_section_range(parent_id)

        if section_range is None:
            return OperationResult(
                success=False, error=f"Could not find section for node: {node_id}"
            )

        if parent_section_range is None:
            return OperationResult(
                success=False, error=f"Could not find section for parent: {parent_id}"
            )

        section_start, section_end = section_range
        parent_section_start, parent_section_end = parent_section_range

        # Calculate level adjustment (difference between parent+1 and current level)
        level_adjustment = (parent.level + 1) - node.level

        # Extract the section and adjust all heading levels
        new_nodes = list(document.nodes)
        section_nodes = new_nodes[section_start : section_end + 1]
        adjusted_section = []

        for section_node in section_nodes:
            if isinstance(section_node, Heading):
                # Adjust level, capping at 6
                adjusted_level = min(6, section_node.level + level_adjustment)
                adjusted_node = Heading(
                    level=adjusted_level,
                    text=section_node.text,
                    children=section_node.children,
                    metadata=section_node.metadata,
                )
                adjusted_section.append(adjusted_node)
            else:
                # Non-heading nodes are kept as-is
                adjusted_section.append(section_node)

        # Remove section from current position
        del new_nodes[section_start : section_end + 1]

        # Adjust parent section end if section was before parent
        if section_start < parent_section_start:
            parent_section_end -= section_end - section_start + 1

        # Insert adjusted section after parent section
        new_nodes[parent_section_end + 1 : parent_section_end + 1] = adjusted_section

        new_document = Document(new_nodes)

        # Collect all affected node IDs from the nested section
        affected_node_ids = [node_id]  # At minimum, the heading itself

        # Compute modified ranges
        modified_ranges = DiffComputer.compute_ranges(
            original_doc=document,
            modified_doc=new_document,
            affected_node_ids=affected_node_ids,
        )

        return OperationResult(
            success=True,
            document=new_document.to_string(),
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
            node_id: The ID of the node to unnest

        Returns:
            Operation result
        """
        tree_builder = DocumentTreeBuilder(document)
        node = tree_builder.find_node(node_id)

        if node is None:
            return OperationResult(success=False, error=f"Node not found: {node_id}")

        if not isinstance(node, Heading):
            return OperationResult(success=False, error=f"Node {node_id} is not a heading")

        # Validate: already at minimum level?
        if node.level <= 1:
            return OperationResult(
                success=True,
                document=document.to_string(),
                error=None,
            )

        # Get the index of the node
        node_index = tree_builder.get_node_index(node_id)
        if node_index is None:
            return OperationResult(success=False, error=f"Could not find index for node: {node_id}")

        # Create new unnested node (promote by one level)
        unnested_node = node.promote()

        # Create new document with updated node
        new_nodes = list(document.nodes)
        new_nodes[node_index] = unnested_node
        new_document = Document(new_nodes)

        # Compute modified ranges
        modified_ranges = DiffComputer.compute_ranges(
            original_doc=document,
            modified_doc=new_document,
            affected_node_ids=[node_id],
        )

        return OperationResult(
            success=True,
            document=new_document.to_string(),
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
