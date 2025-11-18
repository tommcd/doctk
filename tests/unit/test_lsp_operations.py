"""Tests for LSP structure operations."""


from doctk.core import Document, Heading, Paragraph
from doctk.lsp.operations import DocumentTreeBuilder, StructureOperations


class TestDocumentTreeBuilder:
    """Tests for DocumentTreeBuilder class."""

    def test_build_node_map_with_headings(self):
        """Test that DocumentTreeBuilder builds a correct node map."""
        doc = Document(
            nodes=[
                Heading(level=1, text="Title"),
                Heading(level=2, text="Section 1"),
                Heading(level=2, text="Section 2"),
                Heading(level=3, text="Subsection"),
            ]
        )
        builder = DocumentTreeBuilder(doc)

        assert len(builder.node_map) == 4
        assert "h1-0" in builder.node_map
        assert "h2-0" in builder.node_map
        assert "h2-1" in builder.node_map
        assert "h3-0" in builder.node_map

    def test_find_node_by_id(self):
        """Test finding a node by ID."""
        doc = Document(
            nodes=[
                Heading(level=1, text="Title"),
                Heading(level=2, text="Section"),
            ]
        )
        builder = DocumentTreeBuilder(doc)

        node = builder.find_node("h2-0")
        assert node is not None
        assert isinstance(node, Heading)
        assert node.text == "Section"

    def test_find_node_returns_none_for_invalid_id(self):
        """Test that find_node returns None for invalid ID."""
        doc = Document(nodes=[Heading(level=1, text="Title")])
        builder = DocumentTreeBuilder(doc)

        node = builder.find_node("h99-0")
        assert node is None

    def test_get_node_index(self):
        """Test getting node index in document."""
        doc = Document(
            nodes=[
                Heading(level=1, text="Title"),
                Heading(level=2, text="Section"),
                Paragraph(content="Text"),
            ]
        )
        builder = DocumentTreeBuilder(doc)

        index = builder.get_node_index("h2-0")
        assert index == 1


class TestPromote:
    """Tests for promote operation."""

    def test_promote_h2_to_h1(self):
        """Test promoting h2 to h1."""
        doc = Document(nodes=[Heading(level=2, text="Section")])

        new_doc, result = StructureOperations.promote(doc, "h2-0")

        assert result.success is True
        assert len(new_doc.nodes) == 1
        assert new_doc.nodes[0].level == 1
        assert new_doc.nodes[0].text == "Section"

    def test_promote_h1_stays_h1(self):
        """Test that promoting h1 stays at h1 (identity)."""
        doc = Document(nodes=[Heading(level=1, text="Title")])

        new_doc, result = StructureOperations.promote(doc, "h1-0")

        assert result.success is True
        assert len(new_doc.nodes) == 1
        assert new_doc.nodes[0].level == 1

    def test_promote_invalid_node_id(self):
        """Test promoting with invalid node ID."""
        doc = Document(nodes=[Heading(level=2, text="Section")])

        new_doc, result = StructureOperations.promote(doc, "h99-0")

        assert result.success is False
        assert "not found" in result.error.lower()

    def test_promote_non_heading_fails(self):
        """Test that promoting non-heading nodes fails gracefully."""
        doc = Document(
            nodes=[
                Heading(level=1, text="Title"),
                Paragraph(content="Text"),
            ]
        )

        # Attempting to promote a paragraph (which wouldn't have an ID)
        # would fail during node_map building, so this tests error handling
        new_doc, result = StructureOperations.promote(doc, "p-0")

        assert result.success is False

    def test_promote_immutability(self):
        """Test that promote doesn't mutate the original document."""
        original_heading = Heading(level=2, text="Section")
        doc = Document(nodes=[original_heading])

        new_doc, _result = StructureOperations.promote(doc, "h2-0")

        # Original should be unchanged
        assert original_heading.level == 2
        assert doc.nodes[0].level == 2

        # New document should have promoted heading
        assert new_doc.nodes[0].level == 1

    def test_validate_promote_success(self):
        """Test validating a valid promote operation."""
        doc = Document(nodes=[Heading(level=2, text="Section")])

        validation = StructureOperations.validate_promote(doc, "h2-0")

        assert validation.valid is True
        assert validation.error is None


class TestDemote:
    """Tests for demote operation."""

    def test_demote_h1_to_h2(self):
        """Test demoting h1 to h2."""
        doc = Document(nodes=[Heading(level=1, text="Title")])

        new_doc, result = StructureOperations.demote(doc, "h1-0")

        assert result.success is True
        assert len(new_doc.nodes) == 1
        assert new_doc.nodes[0].level == 2
        assert new_doc.nodes[0].text == "Title"

    def test_demote_h6_stays_h6(self):
        """Test that demoting h6 stays at h6 (identity)."""
        doc = Document(nodes=[Heading(level=6, text="Deepest")])

        new_doc, result = StructureOperations.demote(doc, "h6-0")

        assert result.success is True
        assert len(new_doc.nodes) == 1
        assert new_doc.nodes[0].level == 6

    def test_demote_invalid_node_id(self):
        """Test demoting with invalid node ID."""
        doc = Document(nodes=[Heading(level=2, text="Section")])

        new_doc, result = StructureOperations.demote(doc, "h99-0")

        assert result.success is False
        assert "not found" in result.error.lower()

    def test_validate_demote_success(self):
        """Test validating a valid demote operation."""
        doc = Document(nodes=[Heading(level=2, text="Section")])

        validation = StructureOperations.validate_demote(doc, "h2-0")

        assert validation.valid is True
        assert validation.error is None


class TestMoveUp:
    """Tests for move_up operation."""

    def test_move_up_swaps_with_previous(self):
        """Test moving a heading up swaps it with previous sibling."""
        doc = Document(
            nodes=[
                Heading(level=2, text="Section 1"),
                Heading(level=2, text="Section 2"),
            ]
        )

        new_doc, result = StructureOperations.move_up(doc, "h2-1")

        assert result.success is True
        assert new_doc.nodes[0].text == "Section 2"
        assert new_doc.nodes[1].text == "Section 1"

    def test_move_up_at_top_stays_in_place(self):
        """Test moving up the first element stays in place."""
        doc = Document(
            nodes=[
                Heading(level=1, text="First"),
                Heading(level=1, text="Second"),
            ]
        )

        new_doc, result = StructureOperations.move_up(doc, "h1-0")

        assert result.success is True
        assert new_doc.nodes[0].text == "First"

    def test_move_up_invalid_node_id(self):
        """Test move_up with invalid node ID."""
        doc = Document(nodes=[Heading(level=1, text="Title")])

        new_doc, result = StructureOperations.move_up(doc, "h99-0")

        assert result.success is False

    def test_validate_move_up_success(self):
        """Test validating move_up operation."""
        doc = Document(
            nodes=[
                Heading(level=1, text="First"),
                Heading(level=1, text="Second"),
            ]
        )

        validation = StructureOperations.validate_move_up(doc, "h1-1")

        assert validation.valid is True


class TestMoveDown:
    """Tests for move_down operation."""

    def test_move_down_swaps_with_next(self):
        """Test moving a heading down swaps it with next sibling."""
        doc = Document(
            nodes=[
                Heading(level=2, text="Section 1"),
                Heading(level=2, text="Section 2"),
            ]
        )

        new_doc, result = StructureOperations.move_down(doc, "h2-0")

        assert result.success is True
        assert new_doc.nodes[0].text == "Section 2"
        assert new_doc.nodes[1].text == "Section 1"

    def test_move_down_at_bottom_stays_in_place(self):
        """Test moving down the last element stays in place."""
        doc = Document(
            nodes=[
                Heading(level=1, text="First"),
                Heading(level=1, text="Last"),
            ]
        )

        new_doc, result = StructureOperations.move_down(doc, "h1-1")

        assert result.success is True
        assert new_doc.nodes[1].text == "Last"

    def test_validate_move_down_success(self):
        """Test validating move_down operation."""
        doc = Document(
            nodes=[
                Heading(level=1, text="First"),
                Heading(level=1, text="Second"),
            ]
        )

        validation = StructureOperations.validate_move_down(doc, "h1-0")

        assert validation.valid is True


class TestNest:
    """Tests for nest operation."""

    def test_nest_under_parent(self):
        """Test nesting a heading under a parent."""
        doc = Document(
            nodes=[
                Heading(level=1, text="Parent"),
                Heading(level=1, text="Child"),
            ]
        )

        new_doc, result = StructureOperations.nest(doc, "h1-1", "h1-0")

        assert result.success is True
        # Child should now be h2 (parent.level + 1)
        assert new_doc.nodes[1].level == 2
        assert new_doc.nodes[1].text == "Child"
        # Child should be moved after parent
        assert new_doc.nodes[0].text == "Parent"

    def test_nest_adjusts_level(self):
        """Test that nest adjusts the level correctly."""
        doc = Document(
            nodes=[
                Heading(level=2, text="Parent"),
                Heading(level=1, text="Child"),
            ]
        )

        new_doc, result = StructureOperations.nest(doc, "h1-0", "h2-0")

        assert result.success is True
        # Child should become h3 (parent.level + 1)
        assert new_doc.nodes[1].level == 3

    def test_nest_respects_max_level(self):
        """Test that nest respects maximum heading level of 6."""
        doc = Document(
            nodes=[
                Heading(level=6, text="Parent"),
                Heading(level=1, text="Child"),
            ]
        )

        new_doc, result = StructureOperations.nest(doc, "h1-0", "h6-0")

        assert result.success is True
        # Child should be capped at level 6
        assert new_doc.nodes[1].level == 6

    def test_nest_invalid_parent_id(self):
        """Test nest with invalid parent ID."""
        doc = Document(
            nodes=[
                Heading(level=1, text="Parent"),
                Heading(level=1, text="Child"),
            ]
        )

        new_doc, result = StructureOperations.nest(doc, "h1-1", "h99-0")

        assert result.success is False
        assert "not found" in result.error.lower()

    def test_validate_nest_under_self_fails(self):
        """Test that nesting a node under itself fails validation."""
        doc = Document(nodes=[Heading(level=1, text="Parent")])

        validation = StructureOperations.validate_nest(doc, "h1-0", "h1-0")

        assert validation.valid is False
        assert "under itself" in validation.error.lower()

    def test_validate_nest_exceeding_max_level_fails(self):
        """Test validation fails when nest would exceed level 6."""
        doc = Document(
            nodes=[
                Heading(level=6, text="Parent"),
                Heading(level=1, text="Child"),
            ]
        )

        # Note: This actually doesn't fail in validate because we cap at level 6
        # Let's test the validation logic
        validation = StructureOperations.validate_nest(doc, "h1-0", "h6-0")

        # Actually should fail because parent.level + 1 would be 7
        assert validation.valid is False
        assert "exceed" in validation.error.lower()


class TestUnnest:
    """Tests for unnest operation."""

    def test_unnest_decreases_level(self):
        """Test that unnest decreases heading level by 1."""
        doc = Document(nodes=[Heading(level=3, text="Nested")])

        new_doc, result = StructureOperations.unnest(doc, "h3-0")

        assert result.success is True
        assert new_doc.nodes[0].level == 2
        assert new_doc.nodes[0].text == "Nested"

    def test_unnest_h1_stays_h1(self):
        """Test that unnesting h1 stays at h1 (identity)."""
        doc = Document(nodes=[Heading(level=1, text="Top")])

        new_doc, result = StructureOperations.unnest(doc, "h1-0")

        assert result.success is True
        assert new_doc.nodes[0].level == 1

    def test_unnest_invalid_node_id(self):
        """Test unnest with invalid node ID."""
        doc = Document(nodes=[Heading(level=2, text="Section")])

        new_doc, result = StructureOperations.unnest(doc, "h99-0")

        assert result.success is False

    def test_validate_unnest_success(self):
        """Test validating unnest operation."""
        doc = Document(nodes=[Heading(level=3, text="Section")])

        validation = StructureOperations.validate_unnest(doc, "h3-0")

        assert validation.valid is True


class TestOperationImmutability:
    """Tests to ensure all operations maintain immutability."""

    def test_all_operations_dont_mutate_original(self):
        """Test that all operations don't mutate the original document."""
        original_heading = Heading(level=2, text="Original")
        doc = Document(nodes=[original_heading])

        # Test promote
        new_doc, _ = StructureOperations.promote(doc, "h2-0")
        assert original_heading.level == 2
        assert doc.nodes[0].level == 2
        assert new_doc.nodes[0].level == 1

        # Test demote
        new_doc, _ = StructureOperations.demote(doc, "h2-0")
        assert original_heading.level == 2
        assert doc.nodes[0].level == 2
        assert new_doc.nodes[0].level == 3

        # Test unnest
        new_doc, _ = StructureOperations.unnest(doc, "h2-0")
        assert original_heading.level == 2
        assert doc.nodes[0].level == 2
        assert new_doc.nodes[0].level == 1


class TestComplexScenarios:
    """Tests for complex document structures."""

    def test_operations_on_mixed_document(self):
        """Test operations on a document with mixed node types."""
        doc = Document(
            nodes=[
                Heading(level=1, text="Title"),
                Paragraph(content="Introduction"),
                Heading(level=2, text="Section 1"),
                Paragraph(content="Content"),
                Heading(level=2, text="Section 2"),
            ]
        )

        # Promote second h2
        new_doc, result = StructureOperations.promote(doc, "h2-1")

        assert result.success is True
        # Find the promoted heading (should be at index 4, level 1)
        heading_count = sum(1 for n in new_doc.nodes if isinstance(n, Heading))
        assert heading_count == 3

    def test_move_with_intervening_paragraphs(self):
        """Test move operations with non-heading nodes between headings."""
        doc = Document(
            nodes=[
                Heading(level=1, text="First"),
                Paragraph(content="Text 1"),
                Heading(level=1, text="Second"),
                Paragraph(content="Text 2"),
            ]
        )

        new_doc, result = StructureOperations.move_down(doc, "h1-0")

        assert result.success is True
        # Verify the headings were swapped
        headings = [n for n in new_doc.nodes if isinstance(n, Heading)]
        assert headings[0].text == "Second"
        assert headings[1].text == "First"
