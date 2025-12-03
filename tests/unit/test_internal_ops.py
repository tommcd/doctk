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


class TestInternalOperationsMoveUp:
    """Test move_up operation."""

    def test_move_up_swaps_with_previous(self):
        """Test moving a node up swaps it with the previous node."""
        h1 = Heading(level=2, text="First")
        h1.id = NodeId.from_node(h1)
        h2 = Heading(level=2, text="Second")
        h2.id = NodeId.from_node(h2)

        doc = Document([h1, h2])

        result = InternalOperations.move_up(doc, h2.id)

        assert result.success is True
        assert len(result.document.nodes) == 2
        assert result.document.nodes[0].text == "Second"
        assert result.document.nodes[1].text == "First"

    def test_move_up_at_top_stays_in_place(self):
        """Test moving up the first node keeps it in place."""
        h1 = Heading(level=2, text="First")
        h1.id = NodeId.from_node(h1)
        h2 = Heading(level=2, text="Second")
        h2.id = NodeId.from_node(h2)

        doc = Document([h1, h2])

        result = InternalOperations.move_up(doc, h1.id)

        assert result.success is True
        assert result.document.nodes[0].text == "First"
        assert result.document.nodes[1].text == "Second"
        assert len(result.modified_nodes) == 0

    def test_move_up_node_not_found(self):
        """Test move_up with non-existent node ID."""
        h1 = Heading(level=2, text="Test")
        h1.id = NodeId.from_node(h1)
        doc = Document([h1])

        other_heading = Heading(level=3, text="Other")
        other_id = NodeId.from_node(other_heading)

        result = InternalOperations.move_up(doc, other_id)

        assert result.success is False
        assert "not found" in result.error.lower()

    def test_move_up_non_heading_node(self):
        """Test move_up on non-heading node."""
        paragraph = Paragraph(content="Test")
        paragraph.id = NodeId.from_node(paragraph)
        doc = Document([paragraph])

        result = InternalOperations.move_up(doc, paragraph.id)

        assert result.success is False
        assert "not a Heading" in result.error


class TestInternalOperationsMoveDown:
    """Test move_down operation."""

    def test_move_down_swaps_with_next(self):
        """Test moving a node down swaps it with the next node."""
        h1 = Heading(level=2, text="First")
        h1.id = NodeId.from_node(h1)
        h2 = Heading(level=2, text="Second")
        h2.id = NodeId.from_node(h2)

        doc = Document([h1, h2])

        result = InternalOperations.move_down(doc, h1.id)

        assert result.success is True
        assert len(result.document.nodes) == 2
        assert result.document.nodes[0].text == "Second"
        assert result.document.nodes[1].text == "First"

    def test_move_down_at_bottom_stays_in_place(self):
        """Test moving down the last node keeps it in place."""
        h1 = Heading(level=2, text="First")
        h1.id = NodeId.from_node(h1)
        h2 = Heading(level=2, text="Second")
        h2.id = NodeId.from_node(h2)

        doc = Document([h1, h2])

        result = InternalOperations.move_down(doc, h2.id)

        assert result.success is True
        assert result.document.nodes[0].text == "First"
        assert result.document.nodes[1].text == "Second"
        assert len(result.modified_nodes) == 0

    def test_move_down_node_not_found(self):
        """Test move_down with non-existent node ID."""
        h1 = Heading(level=2, text="Test")
        h1.id = NodeId.from_node(h1)
        doc = Document([h1])

        other_heading = Heading(level=3, text="Other")
        other_id = NodeId.from_node(other_heading)

        result = InternalOperations.move_down(doc, other_id)

        assert result.success is False
        assert "not found" in result.error.lower()

    def test_move_down_non_heading_node(self):
        """Test move_down on non-heading node."""
        paragraph = Paragraph(content="Test")
        paragraph.id = NodeId.from_node(paragraph)
        doc = Document([paragraph])

        result = InternalOperations.move_down(doc, paragraph.id)

        assert result.success is False
        assert "not a Heading" in result.error


class TestInternalOperationsNest:
    """Test nest operation."""

    def test_nest_under_parent(self):
        """Test nesting a node under a parent."""
        parent = Heading(level=2, text="Parent")
        parent.id = NodeId.from_node(parent)
        child = Heading(level=2, text="Child")
        child.id = NodeId.from_node(child)

        doc = Document([parent, child])

        result = InternalOperations.nest(doc, child.id, parent.id)

        assert result.success is True
        assert result.document.nodes[1].level == 3  # parent.level + 1
        assert result.document.nodes[1].text == "Child"
        assert result.document.nodes[1].id == child.id  # ID preserved

    def test_nest_adjusts_level(self):
        """Test that nest adjusts level to parent.level + 1."""
        parent = Heading(level=1, text="Parent")
        parent.id = NodeId.from_node(parent)
        child = Heading(level=4, text="Child")
        child.id = NodeId.from_node(child)

        doc = Document([parent, child])

        result = InternalOperations.nest(doc, child.id, parent.id)

        assert result.success is True
        assert result.document.nodes[1].level == 2  # parent.level + 1

    def test_nest_respects_max_level(self):
        """Test that nest caps level at 6."""
        parent = Heading(level=5, text="Parent")
        parent.id = NodeId.from_node(parent)
        child = Heading(level=2, text="Child")
        child.id = NodeId.from_node(child)

        doc = Document([parent, child])

        result = InternalOperations.nest(doc, child.id, parent.id)

        assert result.success is True
        assert result.document.nodes[1].level == 6  # Capped at 6

    def test_nest_node_not_found(self):
        """Test nest with non-existent node ID."""
        parent = Heading(level=2, text="Parent")
        parent.id = NodeId.from_node(parent)
        doc = Document([parent])

        other_heading = Heading(level=3, text="Other")
        other_id = NodeId.from_node(other_heading)

        result = InternalOperations.nest(doc, other_id, parent.id)

        assert result.success is False
        assert "not found" in result.error.lower()

    def test_nest_parent_not_found(self):
        """Test nest with non-existent parent ID."""
        child = Heading(level=2, text="Child")
        child.id = NodeId.from_node(child)
        doc = Document([child])

        other_heading = Heading(level=3, text="Other")
        other_id = NodeId.from_node(other_heading)

        result = InternalOperations.nest(doc, child.id, other_id)

        assert result.success is False
        assert "Parent node" in result.error
        assert "not found" in result.error.lower()

    def test_nest_preserves_node_id(self):
        """Test that nest preserves NodeId (level not in canonical form)."""
        parent = Heading(level=2, text="Parent")
        parent.id = NodeId.from_node(parent)
        child = Heading(level=2, text="Child")
        child.id = NodeId.from_node(child)
        original_child_id = child.id

        doc = Document([parent, child])

        result = InternalOperations.nest(doc, child.id, parent.id)

        assert result.success is True
        assert result.document.nodes[1].id == original_child_id


class TestInternalOperationsUnnest:
    """Test unnest operation."""

    def test_unnest_decreases_level(self):
        """Test unnesting decreases level by 1."""
        heading = Heading(level=3, text="Test")
        heading.id = NodeId.from_node(heading)
        doc = Document([heading])

        result = InternalOperations.unnest(doc, heading.id)

        assert result.success is True
        assert result.document.nodes[0].level == 2

    def test_unnest_at_minimum_level(self):
        """Test unnesting h1 keeps it at h1."""
        heading = Heading(level=1, text="Test")
        heading.id = NodeId.from_node(heading)
        doc = Document([heading])

        result = InternalOperations.unnest(doc, heading.id)

        assert result.success is True
        assert result.document.nodes[0].level == 1

    def test_unnest_preserves_node_id(self):
        """Test that unnest preserves NodeId."""
        heading = Heading(level=3, text="Test")
        heading.id = NodeId.from_node(heading)
        original_id = heading.id
        doc = Document([heading])

        result = InternalOperations.unnest(doc, heading.id)

        assert result.success is True
        assert result.document.nodes[0].id == original_id

    def test_unnest_metadata_indicates_operation(self):
        """Test that unnest result metadata indicates unnest operation."""
        heading = Heading(level=3, text="Test")
        heading.id = NodeId.from_node(heading)
        doc = Document([heading])

        result = InternalOperations.unnest(doc, heading.id)

        assert result.metadata["operation"] == "unnest"


class TestInternalOperationsMetadataImmutability:
    """Test that all operations maintain metadata immutability."""

    def test_nest_deep_copies_metadata(self):
        """Test that nest deep-copies metadata."""
        parent = Heading(level=2, text="Parent", metadata={"parent_tag": "value"})
        parent.id = NodeId.from_node(parent)
        child = Heading(level=2, text="Child", metadata={"child_tag": "value"})
        child.id = NodeId.from_node(child)

        doc = Document([parent, child])

        result = InternalOperations.nest(doc, child.id, parent.id)

        # Modify result metadata
        result.document.nodes[1].metadata["new_key"] = "new_value"

        # Original should be unchanged
        assert "new_key" not in child.metadata

    def test_move_operations_preserve_metadata(self):
        """Test that move operations preserve metadata without mutation."""
        h1 = Heading(level=2, text="First", metadata={"tag": "original"})
        h1.id = NodeId.from_node(h1)
        h2 = Heading(level=2, text="Second")
        h2.id = NodeId.from_node(h2)

        doc = Document([h1, h2])

        result = InternalOperations.move_down(doc, h1.id)

        # Original metadata unchanged
        assert h1.metadata["tag"] == "original"
        # Moved node has same metadata
        assert result.document.nodes[1].metadata["tag"] == "original"


class TestInternalOperationsProvenanceUpdates:
    """Test that operations update provenance appropriately."""

    def test_nest_updates_provenance(self):
        """Test that nest updates provenance with modification time."""
        from doctk.identity import Provenance, ProvenanceContext

        context = ProvenanceContext.from_repl()
        parent = Heading(level=2, text="Parent")
        parent.id = NodeId.from_node(parent)
        parent.provenance = Provenance.from_context(context)

        child = Heading(level=2, text="Child")
        child.id = NodeId.from_node(child)
        child.provenance = Provenance.from_context(context)

        doc = Document([parent, child])

        result = InternalOperations.nest(doc, child.id, parent.id)

        assert result.success is True
        assert result.document.nodes[1].provenance is not None
        assert result.document.nodes[1].provenance.modified_at is not None
