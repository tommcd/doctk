"""
Unit tests for internal operations layer.

Tests the core internal operations that work with rich Document objects
without JSON serialization.
"""

from doctk.core import Document, Heading, Paragraph
from doctk.identity import NodeId
from doctk.internal_ops import InternalOperations, OperationResult


class TestOperationResult:
    """Test OperationResult dataclass."""

    def test_operation_result_success(self):
        """Test successful operation result."""
        doc = Document([Heading(level=2, text="Test")])
        result = OperationResult(success=True, document=doc)

        assert result.success is True
        assert result.document == doc
        assert result.modified_nodes == []
        assert result.error is None
        assert result.metadata == {}

    def test_operation_result_failure(self):
        """Test failed operation result."""
        doc = Document([Heading(level=2, text="Test")])
        result = OperationResult(
            success=False,
            document=doc,
            error="Node not found",
        )

        assert result.success is False
        assert result.document == doc
        assert result.error == "Node not found"

    def test_operation_result_with_modified_nodes(self):
        """Test operation result with modified nodes."""
        doc = Document([Heading(level=2, text="Test")])
        node_id = NodeId.from_node(doc.nodes[0])
        result = OperationResult(
            success=True,
            document=doc,
            modified_nodes=[node_id],
        )

        assert len(result.modified_nodes) == 1
        assert result.modified_nodes[0] == node_id

    def test_operation_result_with_metadata(self):
        """Test operation result with metadata."""
        doc = Document([Heading(level=2, text="Test")])
        result = OperationResult(
            success=True,
            document=doc,
            metadata={"operation": "promote", "old_level": 2, "new_level": 1},
        )

        assert result.metadata["operation"] == "promote"
        assert result.metadata["old_level"] == 2
        assert result.metadata["new_level"] == 1


class TestInternalOperationsPromote:
    """Test promote operation."""

    def test_promote_heading_success(self):
        """Test promoting a heading."""
        heading = Heading(level=2, text="Test")
        heading.id = NodeId.from_node(heading)
        doc = Document([heading])

        result = InternalOperations.promote(doc, heading.id)

        assert result.success is True
        assert len(result.document.nodes) == 1
        assert result.document.nodes[0].level == 1
        assert result.document.nodes[0].text == "Test"
        assert len(result.modified_nodes) == 1
        assert result.modified_nodes[0] == heading.id

    def test_promote_preserves_node_id(self):
        """Test that promote preserves NodeId."""
        heading = Heading(level=2, text="Test")
        heading.id = NodeId.from_node(heading)
        original_id = heading.id
        doc = Document([heading])

        result = InternalOperations.promote(doc, heading.id)

        assert result.success is True
        assert result.document.nodes[0].id == original_id

    def test_promote_heading_at_minimum_level(self):
        """Test promoting h1 (should remain h1)."""
        heading = Heading(level=1, text="Test")
        heading.id = NodeId.from_node(heading)
        doc = Document([heading])

        result = InternalOperations.promote(doc, heading.id)

        assert result.success is True
        assert result.document.nodes[0].level == 1  # Still h1

    def test_promote_node_not_found(self):
        """Test promote with non-existent node ID."""
        heading = Heading(level=2, text="Test")
        heading.id = NodeId.from_node(heading)
        doc = Document([heading])

        # Create a different node ID
        other_heading = Heading(level=3, text="Other")
        other_id = NodeId.from_node(other_heading)

        result = InternalOperations.promote(doc, other_id)

        assert result.success is False
        assert "not found" in result.error.lower()
        assert result.document == doc  # Original document unchanged

    def test_promote_non_heading_node(self):
        """Test promote on non-heading node."""
        paragraph = Paragraph(content="Test")
        paragraph.id = NodeId.from_node(paragraph)
        doc = Document([paragraph])

        result = InternalOperations.promote(doc, paragraph.id)

        assert result.success is False
        assert "not a Heading" in result.error
        assert result.document == doc  # Original document unchanged

    def test_promote_multiple_nodes_in_document(self):
        """Test promoting one node in a document with multiple nodes."""
        h1 = Heading(level=1, text="First")
        h1.id = NodeId.from_node(h1)
        h2 = Heading(level=2, text="Second")
        h2.id = NodeId.from_node(h2)
        h3 = Heading(level=3, text="Third")
        h3.id = NodeId.from_node(h3)

        doc = Document([h1, h2, h3])

        result = InternalOperations.promote(doc, h2.id)

        assert result.success is True
        assert len(result.document.nodes) == 3
        assert result.document.nodes[0].level == 1  # h1 unchanged
        assert result.document.nodes[1].level == 1  # h2 promoted
        assert result.document.nodes[2].level == 3  # h3 unchanged

    def test_promote_includes_metadata(self):
        """Test that promote result includes operation metadata."""
        heading = Heading(level=2, text="Test")
        heading.id = NodeId.from_node(heading)
        doc = Document([heading])

        result = InternalOperations.promote(doc, heading.id)

        assert result.metadata["operation"] == "promote"
        assert result.metadata["old_level"] == 2
        assert result.metadata["new_level"] == 1


class TestInternalOperationsDemote:
    """Test demote operation."""

    def test_demote_heading_success(self):
        """Test demoting a heading."""
        heading = Heading(level=2, text="Test")
        heading.id = NodeId.from_node(heading)
        doc = Document([heading])

        result = InternalOperations.demote(doc, heading.id)

        assert result.success is True
        assert len(result.document.nodes) == 1
        assert result.document.nodes[0].level == 3
        assert result.document.nodes[0].text == "Test"
        assert len(result.modified_nodes) == 1
        assert result.modified_nodes[0] == heading.id

    def test_demote_preserves_node_id(self):
        """Test that demote preserves NodeId."""
        heading = Heading(level=2, text="Test")
        heading.id = NodeId.from_node(heading)
        original_id = heading.id
        doc = Document([heading])

        result = InternalOperations.demote(doc, heading.id)

        assert result.success is True
        assert result.document.nodes[0].id == original_id

    def test_demote_heading_at_maximum_level(self):
        """Test demoting h6 (should remain h6)."""
        heading = Heading(level=6, text="Test")
        heading.id = NodeId.from_node(heading)
        doc = Document([heading])

        result = InternalOperations.demote(doc, heading.id)

        assert result.success is True
        assert result.document.nodes[0].level == 6  # Still h6

    def test_demote_node_not_found(self):
        """Test demote with non-existent node ID."""
        heading = Heading(level=2, text="Test")
        heading.id = NodeId.from_node(heading)
        doc = Document([heading])

        # Create a different node ID
        other_heading = Heading(level=3, text="Other")
        other_id = NodeId.from_node(other_heading)

        result = InternalOperations.demote(doc, other_id)

        assert result.success is False
        assert "not found" in result.error.lower()
        assert result.document == doc  # Original document unchanged

    def test_demote_non_heading_node(self):
        """Test demote on non-heading node."""
        paragraph = Paragraph(content="Test")
        paragraph.id = NodeId.from_node(paragraph)
        doc = Document([paragraph])

        result = InternalOperations.demote(doc, paragraph.id)

        assert result.success is False
        assert "not a Heading" in result.error
        assert result.document == doc  # Original document unchanged

    def test_demote_multiple_nodes_in_document(self):
        """Test demoting one node in a document with multiple nodes."""
        h1 = Heading(level=1, text="First")
        h1.id = NodeId.from_node(h1)
        h2 = Heading(level=2, text="Second")
        h2.id = NodeId.from_node(h2)
        h3 = Heading(level=3, text="Third")
        h3.id = NodeId.from_node(h3)

        doc = Document([h1, h2, h3])

        result = InternalOperations.demote(doc, h2.id)

        assert result.success is True
        assert len(result.document.nodes) == 3
        assert result.document.nodes[0].level == 1  # h1 unchanged
        assert result.document.nodes[1].level == 3  # h2 demoted
        assert result.document.nodes[2].level == 3  # h3 unchanged

    def test_demote_includes_metadata(self):
        """Test that demote result includes operation metadata."""
        heading = Heading(level=2, text="Test")
        heading.id = NodeId.from_node(heading)
        doc = Document([heading])

        result = InternalOperations.demote(doc, heading.id)

        assert result.metadata["operation"] == "demote"
        assert result.metadata["old_level"] == 2
        assert result.metadata["new_level"] == 3


class TestInternalOperationsImmutability:
    """Test that operations maintain immutability."""

    def test_promote_does_not_mutate_original_document(self):
        """Test that promote doesn't mutate the original document."""
        heading = Heading(level=2, text="Test")
        heading.id = NodeId.from_node(heading)
        doc = Document([heading])
        original_level = doc.nodes[0].level

        result = InternalOperations.promote(doc, heading.id)

        # Original document unchanged
        assert doc.nodes[0].level == original_level
        # New document has changes
        assert result.document.nodes[0].level == 1

    def test_demote_does_not_mutate_original_document(self):
        """Test that demote doesn't mutate the original document."""
        heading = Heading(level=2, text="Test")
        heading.id = NodeId.from_node(heading)
        doc = Document([heading])
        original_level = doc.nodes[0].level

        result = InternalOperations.demote(doc, heading.id)

        # Original document unchanged
        assert doc.nodes[0].level == original_level
        # New document has changes
        assert result.document.nodes[0].level == 3
