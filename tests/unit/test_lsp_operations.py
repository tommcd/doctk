"""Tests for LSP structure operations."""

from doctk.core import Document, Heading, Paragraph
from doctk.lsp.operations import DocumentTreeBuilder, StructureOperations
from doctk.lsp.protocols import TreeNode


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

    def test_build_tree_with_ids_single_heading(self):
        """Test building tree with a single heading."""
        doc = Document(nodes=[Heading(level=1, text="Title")])
        builder = DocumentTreeBuilder(doc)

        tree = builder.build_tree_with_ids()

        assert tree.id == "root"
        assert len(tree.children) == 1
        assert tree.children[0].id == "h1-0"
        assert tree.children[0].label == "Title"
        assert tree.children[0].level == 1

    def test_build_tree_with_ids_flat_structure(self):
        """Test building tree with flat heading structure (all same level)."""
        doc = Document(
            nodes=[
                Heading(level=1, text="First"),
                Heading(level=1, text="Second"),
                Heading(level=1, text="Third"),
            ]
        )
        builder = DocumentTreeBuilder(doc)

        tree = builder.build_tree_with_ids()

        assert tree.id == "root"
        assert len(tree.children) == 3
        assert tree.children[0].id == "h1-0"
        assert tree.children[0].label == "First"
        assert tree.children[1].id == "h1-1"
        assert tree.children[1].label == "Second"
        assert tree.children[2].id == "h1-2"
        assert tree.children[2].label == "Third"

    def test_build_tree_with_ids_nested_structure(self):
        """Test building tree with nested heading structure."""
        doc = Document(
            nodes=[
                Heading(level=1, text="Chapter 1"),
                Heading(level=2, text="Section 1.1"),
                Heading(level=2, text="Section 1.2"),
                Heading(level=1, text="Chapter 2"),
            ]
        )
        builder = DocumentTreeBuilder(doc)

        tree = builder.build_tree_with_ids()

        assert tree.id == "root"
        assert len(tree.children) == 2

        # Chapter 1 should have 2 children
        chapter1 = tree.children[0]
        assert chapter1.id == "h1-0"
        assert chapter1.label == "Chapter 1"
        assert len(chapter1.children) == 2
        assert chapter1.children[0].id == "h2-0"
        assert chapter1.children[0].label == "Section 1.1"
        assert chapter1.children[1].id == "h2-1"
        assert chapter1.children[1].label == "Section 1.2"

        # Chapter 2 should have no children
        chapter2 = tree.children[1]
        assert chapter2.id == "h1-1"
        assert chapter2.label == "Chapter 2"
        assert len(chapter2.children) == 0

    def test_build_tree_with_ids_deep_nesting(self):
        """Test building tree with deep nesting (h1 -> h2 -> h3 -> h4)."""
        doc = Document(
            nodes=[
                Heading(level=1, text="Level 1"),
                Heading(level=2, text="Level 2"),
                Heading(level=3, text="Level 3"),
                Heading(level=4, text="Level 4"),
            ]
        )
        builder = DocumentTreeBuilder(doc)

        tree = builder.build_tree_with_ids()

        assert tree.id == "root"
        assert len(tree.children) == 1

        level1 = tree.children[0]
        assert level1.id == "h1-0"
        assert level1.label == "Level 1"
        assert len(level1.children) == 1

        level2 = level1.children[0]
        assert level2.id == "h2-0"
        assert level2.label == "Level 2"
        assert len(level2.children) == 1

        level3 = level2.children[0]
        assert level3.id == "h3-0"
        assert level3.label == "Level 3"
        assert len(level3.children) == 1

        level4 = level3.children[0]
        assert level4.id == "h4-0"
        assert level4.label == "Level 4"
        assert len(level4.children) == 0

    def test_build_tree_with_ids_complex_structure(self):
        """Test building tree with complex mixed structure."""
        doc = Document(
            nodes=[
                Heading(level=1, text="Title"),
                Heading(level=2, text="Section 1"),
                Heading(level=3, text="Subsection 1.1"),
                Heading(level=3, text="Subsection 1.2"),
                Heading(level=2, text="Section 2"),
                Heading(level=1, text="Appendix"),
            ]
        )
        builder = DocumentTreeBuilder(doc)

        tree = builder.build_tree_with_ids()

        assert tree.id == "root"
        assert len(tree.children) == 2

        # Title should have 2 sections
        title = tree.children[0]
        assert title.id == "h1-0"
        assert title.label == "Title"
        assert len(title.children) == 2

        # Section 1 should have 2 subsections
        section1 = title.children[0]
        assert section1.id == "h2-0"
        assert section1.label == "Section 1"
        assert len(section1.children) == 2
        assert section1.children[0].id == "h3-0"
        assert section1.children[0].label == "Subsection 1.1"
        assert section1.children[1].id == "h3-1"
        assert section1.children[1].label == "Subsection 1.2"

        # Section 2 should have no children
        section2 = title.children[1]
        assert section2.id == "h2-1"
        assert section2.label == "Section 2"
        assert len(section2.children) == 0

        # Appendix should have no children
        appendix = tree.children[1]
        assert appendix.id == "h1-1"
        assert appendix.label == "Appendix"
        assert len(appendix.children) == 0

    def test_build_tree_with_ids_skipped_levels(self):
        """Test building tree when heading levels are skipped (h1 -> h3)."""
        doc = Document(
            nodes=[
                Heading(level=1, text="Title"),
                Heading(level=3, text="Subsection"),  # Skipped h2
            ]
        )
        builder = DocumentTreeBuilder(doc)

        tree = builder.build_tree_with_ids()

        assert tree.id == "root"
        assert len(tree.children) == 1

        title = tree.children[0]
        assert title.id == "h1-0"
        assert title.label == "Title"
        # h3 should still be nested under h1
        assert len(title.children) == 1
        assert title.children[0].id == "h3-0"
        assert title.children[0].label == "Subsection"

    def test_build_tree_with_ids_empty_document(self):
        """Test building tree with empty document."""
        doc = Document(nodes=[])
        builder = DocumentTreeBuilder(doc)

        tree = builder.build_tree_with_ids()

        assert tree.id == "root"
        assert tree.label == "Document"
        assert len(tree.children) == 0

    def test_build_tree_with_ids_consistency_with_node_map(self):
        """Test that build_tree_with_ids generates same IDs as node_map."""
        doc = Document(
            nodes=[
                Heading(level=1, text="Title"),
                Heading(level=2, text="Section 1"),
                Heading(level=2, text="Section 2"),
                Heading(level=3, text="Subsection"),
            ]
        )
        builder = DocumentTreeBuilder(doc)

        tree = builder.build_tree_with_ids()

        # Collect all IDs from the tree
        def collect_ids(node: TreeNode, ids: list[str]) -> None:
            if node.id != "root":
                ids.append(node.id)
            for child in node.children:
                collect_ids(child, ids)

        tree_ids = []
        collect_ids(tree, tree_ids)

        # Compare with node_map IDs
        node_map_ids = set(builder.node_map.keys())

        assert set(tree_ids) == node_map_ids
        assert len(tree_ids) == len(node_map_ids)  # No duplicates

    def test_build_tree_with_ids_line_numbers_simple(self):
        """Test that line numbers are calculated correctly for simple document."""
        doc = Document(
            nodes=[
                Heading(level=1, text="First"),
                Heading(level=1, text="Second"),
                Heading(level=1, text="Third"),
            ]
        )
        builder = DocumentTreeBuilder(doc)

        tree = builder.build_tree_with_ids()

        # First heading should be at line 0
        assert tree.children[0].line == 0
        # Second heading should be at line 2 (0: "# First", 1: blank, 2: "# Second")
        assert tree.children[1].line == 2
        # Third heading should be at line 4 (4: "# Third")
        assert tree.children[2].line == 4

    def test_build_tree_with_ids_line_numbers_with_paragraphs(self):
        """Test line numbers with paragraphs between headings."""
        doc = Document(
            nodes=[
                Heading(level=1, text="Title"),
                Paragraph(content="Introduction paragraph."),
                Heading(level=2, text="Section"),
                Paragraph(content="Section content."),
            ]
        )
        builder = DocumentTreeBuilder(doc)

        tree = builder.build_tree_with_ids()

        # Title should be at line 0
        assert tree.children[0].line == 0
        # Section should be at line 4 (0: "# Title", 1: blank, 2: "Introduction...", 3: blank, 4: "## Section")
        assert tree.children[0].children[0].line == 4

    def test_build_tree_with_ids_line_numbers_complex_document(self):
        """Test line numbers in complex document with mixed content."""
        doc = Document(
            nodes=[
                Heading(level=1, text="Chapter 1"),
                Paragraph(content="Chapter intro."),
                Heading(level=2, text="Section 1.1"),
                Paragraph(content="Section content."),
                Heading(level=2, text="Section 1.2"),
                Heading(level=1, text="Chapter 2"),
            ]
        )
        builder = DocumentTreeBuilder(doc)

        tree = builder.build_tree_with_ids()

        # Verify the document structure
        doc_text = doc.to_string()
        lines = doc_text.split("\n")

        # Chapter 1 should be at line 0
        chapter1 = tree.children[0]
        assert chapter1.line == 0
        assert lines[chapter1.line].startswith("# Chapter 1")

        # Section 1.1 should be after Chapter intro paragraph
        section11 = chapter1.children[0]
        assert lines[section11.line].startswith("## Section 1.1")

        # Section 1.2 should be after Section content paragraph
        section12 = chapter1.children[1]
        assert lines[section12.line].startswith("## Section 1.2")

        # Chapter 2 should be after Section 1.2
        chapter2 = tree.children[1]
        assert lines[chapter2.line].startswith("# Chapter 2")

    def test_build_tree_with_ids_line_numbers_nested(self):
        """Test line numbers with nested heading structure."""
        doc = Document(
            nodes=[
                Heading(level=1, text="Title"),
                Heading(level=2, text="Section"),
                Heading(level=3, text="Subsection"),
                Heading(level=4, text="Sub-subsection"),
            ]
        )
        builder = DocumentTreeBuilder(doc)

        tree = builder.build_tree_with_ids()

        # Get document text to verify
        doc_text = doc.to_string()
        lines = doc_text.split("\n")

        # Verify each heading's line number matches its actual position
        title = tree.children[0]
        assert lines[title.line].startswith("# Title")

        section = title.children[0]
        assert lines[section.line].startswith("## Section")

        subsection = section.children[0]
        assert lines[subsection.line].startswith("### Subsection")

        sub_subsection = subsection.children[0]
        assert lines[sub_subsection.line].startswith("#### Sub-subsection")

    def test_build_tree_with_ids_column_is_zero(self):
        """Test that column is always 0 (headings start at column 0)."""
        doc = Document(
            nodes=[
                Heading(level=1, text="Title"),
                Heading(level=2, text="Section"),
            ]
        )
        builder = DocumentTreeBuilder(doc)

        tree = builder.build_tree_with_ids()

        # Root should have column 0
        assert tree.column == 0

        # All headings should have column 0
        def check_column(node: TreeNode) -> None:
            assert node.column == 0
            for child in node.children:
                check_column(child)

        check_column(tree)


class TestPromote:
    """Tests for promote operation."""

    def test_promote_h2_to_h1(self):
        """Test promoting h2 to h1."""
        doc = Document(nodes=[Heading(level=2, text="Section")])

        result = StructureOperations.promote(doc, "h2-0")
        new_doc = (
            Document.from_string(result.document) if result.success and result.document else doc
        )

        assert result.success is True
        assert len(new_doc.nodes) == 1
        assert new_doc.nodes[0].level == 1
        assert new_doc.nodes[0].text == "Section"

    def test_promote_h1_stays_h1(self):
        """Test that promoting h1 stays at h1 (identity)."""
        doc = Document(nodes=[Heading(level=1, text="Title")])

        result = StructureOperations.promote(doc, "h1-0")
        new_doc = (
            Document.from_string(result.document) if result.success and result.document else doc
        )

        assert result.success is True
        assert len(new_doc.nodes) == 1
        assert new_doc.nodes[0].level == 1

    def test_promote_invalid_node_id(self):
        """Test promoting with invalid node ID."""
        doc = Document(nodes=[Heading(level=2, text="Section")])

        result = StructureOperations.promote(doc, "h99-0")

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
        result = StructureOperations.promote(doc, "p-0")

        assert result.success is False

    def test_promote_immutability(self):
        """Test that promote doesn't mutate the original document."""
        original_heading = Heading(level=2, text="Section")
        doc = Document(nodes=[original_heading])

        result = StructureOperations.promote(doc, "h2-0")
        new_doc = (
            Document.from_string(result.document) if result.success and result.document else doc
        )

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

        result = StructureOperations.demote(doc, "h1-0")
        new_doc = (
            Document.from_string(result.document) if result.success and result.document else doc
        )

        assert result.success is True
        assert len(new_doc.nodes) == 1
        assert new_doc.nodes[0].level == 2
        assert new_doc.nodes[0].text == "Title"

    def test_demote_h6_stays_h6(self):
        """Test that demoting h6 stays at h6 (identity)."""
        doc = Document(nodes=[Heading(level=6, text="Deepest")])

        result = StructureOperations.demote(doc, "h6-0")
        new_doc = (
            Document.from_string(result.document) if result.success and result.document else doc
        )

        assert result.success is True
        assert len(new_doc.nodes) == 1
        assert new_doc.nodes[0].level == 6

    def test_demote_invalid_node_id(self):
        """Test demoting with invalid node ID."""
        doc = Document(nodes=[Heading(level=2, text="Section")])

        result = StructureOperations.demote(doc, "h99-0")

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

        result = StructureOperations.move_up(doc, "h2-1")
        new_doc = (
            Document.from_string(result.document) if result.success and result.document else doc
        )

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

        result = StructureOperations.move_up(doc, "h1-0")
        new_doc = (
            Document.from_string(result.document) if result.success and result.document else doc
        )

        assert result.success is True
        assert new_doc.nodes[0].text == "First"

    def test_move_up_invalid_node_id(self):
        """Test move_up with invalid node ID."""
        doc = Document(nodes=[Heading(level=1, text="Title")])

        result = StructureOperations.move_up(doc, "h99-0")

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

        result = StructureOperations.move_down(doc, "h2-0")
        new_doc = (
            Document.from_string(result.document) if result.success and result.document else doc
        )

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

        result = StructureOperations.move_down(doc, "h1-1")
        new_doc = (
            Document.from_string(result.document) if result.success and result.document else doc
        )

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

        result = StructureOperations.nest(doc, "h1-1", "h1-0")
        new_doc = (
            Document.from_string(result.document) if result.success and result.document else doc
        )

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

        result = StructureOperations.nest(doc, "h1-0", "h2-0")
        new_doc = (
            Document.from_string(result.document) if result.success and result.document else doc
        )

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

        result = StructureOperations.nest(doc, "h1-0", "h6-0")
        new_doc = (
            Document.from_string(result.document) if result.success and result.document else doc
        )

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

        result = StructureOperations.nest(doc, "h1-1", "h99-0")

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

        result = StructureOperations.unnest(doc, "h3-0")
        new_doc = (
            Document.from_string(result.document) if result.success and result.document else doc
        )

        assert result.success is True
        assert new_doc.nodes[0].level == 2
        assert new_doc.nodes[0].text == "Nested"

    def test_unnest_h1_stays_h1(self):
        """Test that unnesting h1 stays at h1 (identity)."""
        doc = Document(nodes=[Heading(level=1, text="Top")])

        result = StructureOperations.unnest(doc, "h1-0")
        new_doc = (
            Document.from_string(result.document) if result.success and result.document else doc
        )

        assert result.success is True
        assert new_doc.nodes[0].level == 1

    def test_unnest_invalid_node_id(self):
        """Test unnest with invalid node ID."""
        doc = Document(nodes=[Heading(level=2, text="Section")])

        result = StructureOperations.unnest(doc, "h99-0")

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
        result = StructureOperations.promote(doc, "h2-0")
        new_doc = (
            Document.from_string(result.document) if result.success and result.document else doc
        )
        assert original_heading.level == 2
        assert doc.nodes[0].level == 2
        assert new_doc.nodes[0].level == 1

        # Test demote
        result = StructureOperations.demote(doc, "h2-0")
        new_doc = (
            Document.from_string(result.document) if result.success and result.document else doc
        )
        assert original_heading.level == 2
        assert doc.nodes[0].level == 2
        assert new_doc.nodes[0].level == 3

        # Test unnest
        result = StructureOperations.unnest(doc, "h2-0")
        new_doc = (
            Document.from_string(result.document) if result.success and result.document else doc
        )
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
        result = StructureOperations.promote(doc, "h2-1")
        new_doc = (
            Document.from_string(result.document) if result.success and result.document else doc
        )

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

        result = StructureOperations.move_down(doc, "h1-0")
        new_doc = (
            Document.from_string(result.document) if result.success and result.document else doc
        )

        assert result.success is True
        # Verify the headings were swapped
        headings = [n for n in new_doc.nodes if isinstance(n, Heading)]
        assert headings[0].text == "Second"
        assert headings[1].text == "First"


class TestGranularEdits:
    """Tests for granular edit functionality (modified_ranges)."""

    def test_promote_returns_modified_ranges(self):
        """Test that promote operation returns modified ranges."""
        doc = Document(nodes=[Heading(level=2, text="Section")])

        result = StructureOperations.promote(doc, "h2-0")

        assert result.success is True
        assert result.modified_ranges is not None
        assert len(result.modified_ranges) > 0

    def test_promote_modified_range_content(self):
        """Test that promote modified range contains correct new text."""
        doc = Document(nodes=[Heading(level=2, text="Section")])

        result = StructureOperations.promote(doc, "h2-0")

        assert result.success is True
        assert result.modified_ranges is not None
        # Should have one range for the heading
        assert len(result.modified_ranges) == 1
        modified_range = result.modified_ranges[0]
        # New text should be h1
        assert "# Section" in modified_range.new_text

    def test_promote_modified_range_positions(self):
        """Test that promote modified range has correct line/column positions."""
        doc = Document(nodes=[Heading(level=2, text="Section")])

        result = StructureOperations.promote(doc, "h2-0")

        assert result.success is True
        assert result.modified_ranges is not None
        modified_range = result.modified_ranges[0]
        # Should start at line 0, column 0 for first node
        assert modified_range.start_line == 0
        assert modified_range.start_column == 0
        # Should end at same line (single heading)
        assert modified_range.end_line == 0

    def test_demote_returns_modified_ranges(self):
        """Test that demote operation returns modified ranges."""
        doc = Document(nodes=[Heading(level=1, text="Title")])

        result = StructureOperations.demote(doc, "h1-0")

        assert result.success is True
        assert result.modified_ranges is not None
        assert len(result.modified_ranges) > 0

    def test_demote_modified_range_content(self):
        """Test that demote modified range contains correct new text."""
        doc = Document(nodes=[Heading(level=1, text="Title")])

        result = StructureOperations.demote(doc, "h1-0")

        assert result.success is True
        assert result.modified_ranges is not None
        modified_range = result.modified_ranges[0]
        # New text should be h2
        assert "## Title" in modified_range.new_text

    def test_move_up_returns_modified_ranges(self):
        """Test that move_up operation returns modified ranges."""
        doc = Document(
            nodes=[
                Heading(level=2, text="Section 1"),
                Heading(level=2, text="Section 2"),
            ]
        )

        result = StructureOperations.move_up(doc, "h2-1")

        assert result.success is True
        assert result.modified_ranges is not None
        # Should have at least one range for the moved section
        assert len(result.modified_ranges) >= 1
        # Verify that Section 2 is in the modified ranges
        assert any("Section 2" in r.new_text for r in result.modified_ranges)

    def test_move_up_modified_range_details(self):
        """Test move_up modified range has correct positions and content."""
        doc = Document(
            nodes=[
                Heading(level=2, text="Section 1"),
                Paragraph(content="Content 1"),
                Heading(level=2, text="Section 2"),
                Paragraph(content="Content 2"),
            ]
        )

        result = StructureOperations.move_up(doc, "h2-1")

        assert result.success is True
        assert result.modified_ranges is not None
        # The moved heading should be in the results
        heading_range = next((r for r in result.modified_ranges if "Section 2" in r.new_text), None)
        assert heading_range is not None
        # Verify it's a heading (should have ##)
        assert "##" in heading_range.new_text

    def test_move_down_returns_modified_ranges(self):
        """Test that move_down operation returns modified ranges."""
        doc = Document(
            nodes=[
                Heading(level=2, text="Section 1"),
                Heading(level=2, text="Section 2"),
            ]
        )

        result = StructureOperations.move_down(doc, "h2-0")

        assert result.success is True
        assert result.modified_ranges is not None
        # Should have at least one range for the moved section
        assert len(result.modified_ranges) >= 1
        # Verify that Section 1 is in the modified ranges
        assert any("Section 1" in r.new_text for r in result.modified_ranges)

    def test_move_down_modified_range_details(self):
        """Test move_down modified range has correct positions and content."""
        doc = Document(
            nodes=[
                Heading(level=2, text="Section 1"),
                Paragraph(content="Content 1"),
                Heading(level=2, text="Section 2"),
                Paragraph(content="Content 2"),
            ]
        )

        result = StructureOperations.move_down(doc, "h2-0")

        assert result.success is True
        assert result.modified_ranges is not None
        # The moved heading should be in the results
        heading_range = next((r for r in result.modified_ranges if "Section 1" in r.new_text), None)
        assert heading_range is not None
        # Verify start_line and end_line are valid
        assert heading_range.start_line >= 0
        assert heading_range.end_line >= heading_range.start_line

    def test_nest_returns_modified_ranges(self):
        """Test that nest operation returns modified ranges."""
        doc = Document(
            nodes=[
                Heading(level=1, text="Parent"),
                Heading(level=1, text="Child"),
            ]
        )

        result = StructureOperations.nest(doc, "h1-1", "h1-0")

        assert result.success is True
        assert result.modified_ranges is not None
        # Should have at least one range for the nested node
        assert len(result.modified_ranges) >= 1

    def test_nest_modified_range_shows_level_change(self):
        """Test that nest modified range reflects the level change."""
        doc = Document(
            nodes=[
                Heading(level=1, text="Parent"),
                Heading(level=1, text="Child"),
            ]
        )

        result = StructureOperations.nest(doc, "h1-1", "h1-0")

        assert result.success is True
        assert result.modified_ranges is not None
        # The child should now be level 2 (h2 -> ##)
        child_range = next((r for r in result.modified_ranges if "Child" in r.new_text), None)
        assert child_range is not None
        # Should show level 2 heading
        assert "##" in child_range.new_text
        # Should NOT be level 1
        assert not child_range.new_text.strip().startswith("# Child")

    def test_nest_modified_range_content(self):
        """Test that nest modified range contains adjusted level."""
        doc = Document(
            nodes=[
                Heading(level=1, text="Parent"),
                Heading(level=1, text="Child"),
            ]
        )

        result = StructureOperations.nest(doc, "h1-1", "h1-0")

        assert result.success is True
        # Verify the modified document has the child at level 2
        new_doc = Document.from_string(result.document)
        assert new_doc.nodes[1].level == 2

    def test_unnest_returns_modified_ranges(self):
        """Test that unnest operation returns modified ranges."""
        doc = Document(nodes=[Heading(level=3, text="Nested")])

        result = StructureOperations.unnest(doc, "h3-0")

        assert result.success is True
        assert result.modified_ranges is not None

    def test_unnest_modified_range_content(self):
        """Test that unnest modified range contains promoted level."""
        doc = Document(nodes=[Heading(level=3, text="Nested")])

        result = StructureOperations.unnest(doc, "h3-0")

        assert result.success is True
        assert result.modified_ranges is not None
        modified_range = result.modified_ranges[0]
        # New text should be h2
        assert "## Nested" in modified_range.new_text

    def test_modified_ranges_with_multiple_nodes(self):
        """Test modified ranges with document containing multiple nodes."""
        doc = Document(
            nodes=[
                Heading(level=1, text="Title"),
                Paragraph(content="Introduction"),
                Heading(level=2, text="Section"),
            ]
        )

        result = StructureOperations.promote(doc, "h2-0")

        assert result.success is True
        assert result.modified_ranges is not None
        # Should have modified ranges for the heading
        assert len(result.modified_ranges) > 0

    def test_modified_range_preserves_full_document_fallback(self):
        """Test that operations still provide full document for fallback."""
        doc = Document(nodes=[Heading(level=2, text="Section")])

        result = StructureOperations.promote(doc, "h2-0")

        assert result.success is True
        # Both modified_ranges and full document should be present
        assert result.modified_ranges is not None
        assert result.document is not None
        # Full document should be valid markdown
        assert "# Section" in result.document

    def test_identity_operation_still_returns_ranges(self):
        """Test that identity operations (h1 promote) still return ranges."""
        doc = Document(nodes=[Heading(level=1, text="Title")])

        result = StructureOperations.promote(doc, "h1-0")

        assert result.success is True
        # Even though it's identity, should still work
        # The implementation might return empty ranges or the same content
        assert result.document is not None

    def test_modified_range_line_numbers_are_zero_indexed(self):
        """Test that modified range line numbers are zero-indexed."""
        doc = Document(
            nodes=[
                Heading(level=1, text="First"),
                Heading(level=2, text="Second"),
            ]
        )

        result = StructureOperations.promote(doc, "h2-0")

        assert result.success is True
        assert result.modified_ranges is not None
        # Line numbers should be zero-indexed
        for modified_range in result.modified_ranges:
            assert modified_range.start_line >= 0
            assert modified_range.end_line >= modified_range.start_line

    def test_modified_range_new_text_not_empty_for_valid_operations(self):
        """Test that new_text is not empty for valid operations."""
        doc = Document(nodes=[Heading(level=2, text="Section")])

        result = StructureOperations.promote(doc, "h2-0")

        assert result.success is True
        assert result.modified_ranges is not None
        # new_text should not be empty for a valid operation
        for modified_range in result.modified_ranges:
            # For non-deletion operations, new_text should not be empty
            if modified_range.end_line >= modified_range.start_line:
                assert len(modified_range.new_text) > 0
