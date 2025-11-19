"""Tests for DocumentInterface protocol and pluggable architecture."""

from typing import Any

import pytest

from doctk.core import Document, Heading, Paragraph
from doctk.lsp.operations import DocumentTreeBuilder, StructureOperations
from doctk.lsp.protocols import DocumentInterface, OperationResult, TreeNode


class MockInterface(DocumentInterface):
    """Mock implementation of DocumentInterface for testing."""

    def __init__(self):
        """Initialize mock interface."""
        self.operations = StructureOperations()
        self.document: Document | None = None
        self.tree: TreeNode | None = None
        self.selected_node_id: str | None = None
        self.displayed_tree: TreeNode | None = None
        self.error_message: str | None = None

    def display_tree(self, tree: TreeNode | Any) -> None:
        """Record displayed tree."""
        self.displayed_tree = tree

    def get_user_selection(self) -> Any | None:
        """Return pre-configured selection."""
        return self.selected_node_id

    def apply_operation(self, operation: Any) -> OperationResult:
        """Apply operation using shared StructureOperations."""
        if not self.document or not self.selected_node_id:
            return OperationResult(success=False, error="No document loaded or no node selected")

        # Map operation names to methods
        op_map = {
            "promote": self.operations.promote,
            "demote": self.operations.demote,
            "move_up": self.operations.move_up,
            "move_down": self.operations.move_down,
            "unnest": self.operations.unnest,
        }

        op_fn = op_map.get(operation)
        if not op_fn:
            return OperationResult(success=False, error=f"Unknown operation: {operation}")

        # Store the original node to track it through the operation
        original_node = None
        if self.document:
            builder = DocumentTreeBuilder(self.document)
            original_node = builder.find_node(self.selected_node_id)

        result = op_fn(self.document, self.selected_node_id)

        if result.success:
            # Handle optional document field (may be None if only granular edits provided)
            if result.document is not None:
                # Update document
                self.document = Document.from_string(result.document)
                # Rebuild tree
                builder = DocumentTreeBuilder(self.document)
                self.tree = builder.build_tree_with_ids()

                # Remap selected_node_id to the new tree structure
                # After promote/demote/move operations, the node ID may have changed
                if original_node is not None:
                    self.selected_node_id = self._find_node_in_tree(original_node, builder)

        return result

    def _find_node_in_tree(self, original_node: Any, builder: DocumentTreeBuilder) -> str | None:
        """
        Find the ID of a node in the rebuilt tree that matches the original node.

        After operations like promote/demote, node IDs change because they encode
        the heading level (e.g., h2-0 becomes h1-0 after promote). This method
        finds the corresponding node in the new tree by matching content.

        Args:
            original_node: The original node to find
            builder: DocumentTreeBuilder for the new tree

        Returns:
            The new node ID, or None if not found
        """
        from doctk.core import Heading

        # Match headings by text content (level may have changed)
        if isinstance(original_node, Heading):
            for node_id, node in builder.node_map.items():
                if isinstance(node, Heading) and node.text == original_node.text:
                    return node_id

        return None

    def show_error(self, message: str) -> None:
        """Record error message."""
        self.error_message = message

    def load_document(self, doc: Document) -> None:
        """Helper to load a document."""
        self.document = doc
        builder = DocumentTreeBuilder(doc)
        self.tree = builder.build_tree_with_ids()


class TestDocumentInterfaceContract:
    """Test that DocumentInterface contract is well-defined."""

    def test_interface_is_abstract(self):
        """Test that DocumentInterface cannot be instantiated directly."""
        with pytest.raises(TypeError):
            DocumentInterface()  # type: ignore

    def test_interface_requires_all_methods(self):
        """Test that incomplete implementations fail."""

        class IncompleteInterface(DocumentInterface):
            def display_tree(self, tree: Any) -> None:
                pass

        with pytest.raises(TypeError):
            IncompleteInterface()

    def test_mock_interface_implements_all_methods(self):
        """Test that MockInterface implements all required methods."""
        interface = MockInterface()

        # Verify all abstract methods are implemented
        assert hasattr(interface, "display_tree")
        assert hasattr(interface, "get_user_selection")
        assert hasattr(interface, "apply_operation")
        assert hasattr(interface, "show_error")

    def test_interface_methods_are_callable(self):
        """Test that all interface methods are callable."""
        interface = MockInterface()

        # Create a simple document
        doc = Document(nodes=[Heading(level=1, text="Title")])
        interface.load_document(doc)

        # Test all methods are callable
        interface.display_tree(interface.tree)
        selection = interface.get_user_selection()
        interface.show_error("Test error")

        assert selection is None  # No selection set yet


class TestMockInterfaceOperations:
    """Test operations through the MockInterface."""

    def test_load_and_display_document(self):
        """Test loading a document and displaying its tree."""
        interface = MockInterface()

        doc = Document(
            nodes=[
                Heading(level=1, text="Title"),
                Heading(level=2, text="Section"),
            ]
        )
        interface.load_document(doc)

        # Display tree
        interface.display_tree(interface.tree)

        # Verify tree was displayed
        assert interface.displayed_tree is not None
        assert interface.displayed_tree.id == "root"
        assert len(interface.displayed_tree.children) == 1
        assert interface.displayed_tree.children[0].label == "Title"

    def test_promote_operation_through_interface(self):
        """Test promote operation via interface."""
        interface = MockInterface()

        doc = Document(
            nodes=[
                Heading(level=2, text="Section"),
            ]
        )
        interface.load_document(doc)
        interface.selected_node_id = "h2-0"

        # Apply promote operation
        result = interface.apply_operation("promote")

        assert result.success
        assert result.document is not None
        assert "# Section" in result.document

    def test_demote_operation_through_interface(self):
        """Test demote operation via interface."""
        interface = MockInterface()

        doc = Document(
            nodes=[
                Heading(level=1, text="Title"),
            ]
        )
        interface.load_document(doc)
        interface.selected_node_id = "h1-0"

        # Apply demote operation
        result = interface.apply_operation("demote")

        assert result.success
        assert result.document is not None
        assert "## Title" in result.document

    def test_move_up_operation_through_interface(self):
        """Test move_up operation via interface."""
        interface = MockInterface()

        doc = Document(
            nodes=[
                Heading(level=1, text="First"),
                Heading(level=1, text="Second"),
            ]
        )
        interface.load_document(doc)
        interface.selected_node_id = "h1-1"  # Second heading

        # Apply move_up operation
        result = interface.apply_operation("move_up")

        assert result.success
        # Verify order changed (Second should be first now)
        lines = result.document.split("\n")
        assert "# Second" in lines[0]

    def test_move_down_operation_through_interface(self):
        """Test move_down operation via interface."""
        interface = MockInterface()

        doc = Document(
            nodes=[
                Heading(level=1, text="First"),
                Heading(level=1, text="Second"),
            ]
        )
        interface.load_document(doc)
        interface.selected_node_id = "h1-0"  # First heading

        # Apply move_down operation
        result = interface.apply_operation("move_down")

        assert result.success
        # Verify order changed (First should be second now)
        lines = result.document.split("\n")
        assert "# Second" in lines[0]

    def test_unnest_operation_through_interface(self):
        """Test unnest operation via interface."""
        interface = MockInterface()

        doc = Document(
            nodes=[
                Heading(level=2, text="Section"),
            ]
        )
        interface.load_document(doc)
        interface.selected_node_id = "h2-0"

        # Apply unnest operation (should promote)
        result = interface.apply_operation("unnest")

        assert result.success
        assert "# Section" in result.document


class TestInterfaceErrorHandling:
    """Test error handling through the interface."""

    def test_operation_without_document(self):
        """Test operation fails when no document is loaded."""
        interface = MockInterface()

        result = interface.apply_operation("promote")

        assert not result.success
        assert "No document loaded" in result.error

    def test_operation_without_selection(self):
        """Test operation fails when no node is selected."""
        interface = MockInterface()

        doc = Document(nodes=[Heading(level=1, text="Title")])
        interface.load_document(doc)
        # Don't set selected_node_id

        result = interface.apply_operation("promote")

        assert not result.success
        assert "no node selected" in result.error.lower()

    def test_unknown_operation(self):
        """Test unknown operation returns error."""
        interface = MockInterface()

        doc = Document(nodes=[Heading(level=1, text="Title")])
        interface.load_document(doc)
        interface.selected_node_id = "h1-0"

        result = interface.apply_operation("invalid_operation")

        assert not result.success
        assert "Unknown operation" in result.error

    def test_show_error_records_message(self):
        """Test that show_error properly records error messages."""
        interface = MockInterface()

        interface.show_error("Test error message")

        assert interface.error_message == "Test error message"


class TestInterfaceStateManagement:
    """Test state management through the interface."""

    def test_document_updates_after_operation(self):
        """Test that document is updated after successful operation."""
        interface = MockInterface()

        doc = Document(nodes=[Heading(level=2, text="Section")])
        interface.load_document(doc)
        interface.selected_node_id = "h2-0"

        # Verify initial state
        assert interface.document.nodes[0].level == 2

        # Apply promote
        result = interface.apply_operation("promote")

        assert result.success
        # Verify document was updated
        assert interface.document.nodes[0].level == 1

    def test_tree_rebuilds_after_operation(self):
        """Test that tree is rebuilt after successful operation."""
        interface = MockInterface()

        doc = Document(
            nodes=[
                Heading(level=1, text="Title"),
                Heading(level=2, text="Section"),
            ]
        )
        interface.load_document(doc)

        # Verify initial tree exists
        assert interface.tree is not None
        assert len(interface.tree.children) > 0

        # Select and demote the h1 (should change tree structure)
        interface.selected_node_id = "h1-0"
        result = interface.apply_operation("demote")

        assert result.success
        # Tree should be rebuilt with new structure
        assert interface.tree is not None

    def test_user_selection_persists(self):
        """Test that user selection is maintained."""
        interface = MockInterface()

        # Set selection
        interface.selected_node_id = "h1-0"

        # Verify selection persists
        assert interface.get_user_selection() == "h1-0"


class TestInterfaceIntegration:
    """Integration tests for interface with core components."""

    def test_interface_uses_shared_operations(self):
        """Test that interface uses shared StructureOperations."""
        interface = MockInterface()

        # Verify operations instance exists
        assert isinstance(interface.operations, StructureOperations)

    def test_interface_with_complex_document(self):
        """Test interface with complex document structure."""
        interface = MockInterface()

        doc = Document(
            nodes=[
                Heading(level=1, text="Title"),
                Paragraph(content="Intro text"),
                Heading(level=2, text="Section 1"),
                Paragraph(content="Section 1 content"),
                Heading(level=2, text="Section 2"),
                Paragraph(content="Section 2 content"),
                Heading(level=3, text="Subsection"),
                Paragraph(content="Subsection content"),
            ]
        )
        interface.load_document(doc)

        # Test promoting h3
        interface.selected_node_id = "h3-0"
        result = interface.apply_operation("promote")

        assert result.success
        # Verify level changed
        assert interface.document.nodes[6].level == 2

    def test_interface_with_multiple_operations(self):
        """Test applying multiple operations in sequence."""
        interface = MockInterface()

        doc = Document(
            nodes=[
                Heading(level=3, text="Section"),
            ]
        )
        interface.load_document(doc)
        interface.selected_node_id = "h3-0"

        # Promote twice
        result1 = interface.apply_operation("promote")
        assert result1.success

        # After first promote, it's h2-0
        interface.selected_node_id = "h2-0"
        result2 = interface.apply_operation("promote")
        assert result2.success

        # Should now be h1
        assert interface.document.nodes[0].level == 1


class TestInterfaceImmutability:
    """Test that interface operations don't mutate original documents."""

    def test_operations_dont_mutate_original(self):
        """Test that operations create new document instances."""
        interface = MockInterface()

        original_doc = Document(nodes=[Heading(level=2, text="Section")])
        interface.load_document(original_doc)
        interface.selected_node_id = "h2-0"

        # Store reference to original
        original_level = original_doc.nodes[0].level

        # Apply operation
        result = interface.apply_operation("promote")

        assert result.success
        # Original document should be unchanged
        assert original_doc.nodes[0].level == original_level
        # New document should be different
        assert interface.document.nodes[0].level == 1


class TestInterfaceGranularEdits:
    """Test that interface operations return granular edits."""

    def test_operation_returns_modified_ranges(self):
        """Test that operations return granular edit information."""
        interface = MockInterface()

        doc = Document(nodes=[Heading(level=2, text="Section")])
        interface.load_document(doc)
        interface.selected_node_id = "h2-0"

        result = interface.apply_operation("promote")

        assert result.success
        assert result.modified_ranges is not None
        assert len(result.modified_ranges) > 0

    def test_modified_ranges_contain_correct_data(self):
        """Test that modified ranges have correct structure."""
        interface = MockInterface()

        doc = Document(nodes=[Heading(level=2, text="Section")])
        interface.load_document(doc)
        interface.selected_node_id = "h2-0"

        result = interface.apply_operation("promote")

        assert result.success
        range_data = result.modified_ranges[0]

        # Verify range has required fields
        assert hasattr(range_data, "start_line")
        assert hasattr(range_data, "start_column")
        assert hasattr(range_data, "end_line")
        assert hasattr(range_data, "end_column")
        assert hasattr(range_data, "new_text")

        # Verify new_text contains promoted heading
        assert "# Section" in range_data.new_text
