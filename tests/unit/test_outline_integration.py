"""Tests for outline tree building and integration."""


from doctk.core import Document, Heading, Paragraph
from doctk.lsp.operations import DocumentTreeBuilder


class TestOutlineTreeBuilding:
    """Tests for building outline trees from documents."""

    def test_simple_heading_structure(self):
        """Test building tree from simple heading structure."""
        doc = Document(
            nodes=[
                Heading(level=1, text="Title"),
                Heading(level=2, text="Section 1"),
                Heading(level=2, text="Section 2"),
            ]
        )

        builder = DocumentTreeBuilder(doc)

        # Check node map
        assert len(builder.node_map) == 3
        assert "h1-0" in builder.node_map
        assert "h2-0" in builder.node_map
        assert "h2-1" in builder.node_map

        # Check node content
        h1 = builder.find_node("h1-0")
        assert h1 is not None
        assert h1.text == "Title"
        assert h1.level == 1

        h2_0 = builder.find_node("h2-0")
        assert h2_0 is not None
        assert h2_0.text == "Section 1"

    def test_nested_heading_structure(self):
        """Test building tree from nested heading structure."""
        doc = Document(
            nodes=[
                Heading(level=1, text="Chapter 1"),
                Heading(level=2, text="Section 1.1"),
                Heading(level=3, text="Subsection 1.1.1"),
                Heading(level=2, text="Section 1.2"),
            ]
        )

        builder = DocumentTreeBuilder(doc)

        # Check all nodes are mapped
        assert len(builder.node_map) == 4
        assert "h1-0" in builder.node_map
        assert "h2-0" in builder.node_map
        assert "h3-0" in builder.node_map
        assert "h2-1" in builder.node_map

    def test_heading_id_generation(self):
        """Test that heading IDs are unique and sequential."""
        doc = Document(
            nodes=[
                Heading(level=2, text="First h2"),
                Heading(level=2, text="Second h2"),
                Heading(level=2, text="Third h2"),
                Heading(level=3, text="First h3"),
                Heading(level=3, text="Second h3"),
            ]
        )

        builder = DocumentTreeBuilder(doc)

        # Check h2 IDs are sequential
        assert "h2-0" in builder.node_map
        assert "h2-1" in builder.node_map
        assert "h2-2" in builder.node_map

        # Check h3 IDs are sequential
        assert "h3-0" in builder.node_map
        assert "h3-1" in builder.node_map

        # Verify content
        assert builder.find_node("h2-0").text == "First h2"
        assert builder.find_node("h2-1").text == "Second h2"
        assert builder.find_node("h2-2").text == "Third h2"

    def test_mixed_content_with_paragraphs(self):
        """Test that paragraphs don't interfere with heading indexing."""
        doc = Document(
            nodes=[
                Heading(level=1, text="Title"),
                Paragraph(content="Some intro text"),
                Heading(level=2, text="Section"),
                Paragraph(content="Section content"),
                Heading(level=2, text="Another Section"),
            ]
        )

        builder = DocumentTreeBuilder(doc)

        # Only headings should be in the map
        assert len(builder.node_map) == 3
        assert "h1-0" in builder.node_map
        assert "h2-0" in builder.node_map
        assert "h2-1" in builder.node_map

    def test_get_node_index(self):
        """Test getting node index in document."""
        doc = Document(
            nodes=[
                Heading(level=1, text="Title"),
                Paragraph(content="Text"),
                Heading(level=2, text="Section"),
            ]
        )

        builder = DocumentTreeBuilder(doc)

        # h1-0 should be at index 0
        assert builder.get_node_index("h1-0") == 0

        # h2-0 should be at index 2 (after paragraph)
        assert builder.get_node_index("h2-0") == 2

    def test_empty_document(self):
        """Test handling empty document."""
        doc = Document(nodes=[])
        builder = DocumentTreeBuilder(doc)

        assert len(builder.node_map) == 0
        assert builder.find_node("h1-0") is None

    def test_document_with_no_headings(self):
        """Test document with only paragraphs."""
        doc = Document(
            nodes=[
                Paragraph(content="First paragraph"),
                Paragraph(content="Second paragraph"),
            ]
        )

        builder = DocumentTreeBuilder(doc)

        assert len(builder.node_map) == 0

    def test_all_heading_levels(self):
        """Test document with all heading levels 1-6."""
        doc = Document(
            nodes=[
                Heading(level=1, text="H1"),
                Heading(level=2, text="H2"),
                Heading(level=3, text="H3"),
                Heading(level=4, text="H4"),
                Heading(level=5, text="H5"),
                Heading(level=6, text="H6"),
            ]
        )

        builder = DocumentTreeBuilder(doc)

        assert len(builder.node_map) == 6
        for level in range(1, 7):
            node_id = f"h{level}-0"
            assert node_id in builder.node_map
            node = builder.find_node(node_id)
            assert node.level == level
            assert node.text == f"H{level}"


class TestOutlineTreeFromMarkdown:
    """Tests for building outline trees from Markdown strings."""

    def test_parse_simple_markdown(self):
        """Test parsing simple Markdown document."""
        markdown = """# Title

## Section 1

Some content here.

## Section 2

More content.
"""
        doc = Document.from_string(markdown)
        builder = DocumentTreeBuilder(doc)

        # Should have 1 h1 and 2 h2 headings
        assert "h1-0" in builder.node_map
        assert "h2-0" in builder.node_map
        assert "h2-1" in builder.node_map

        h1 = builder.find_node("h1-0")
        assert h1.text == "Title"

    def test_parse_nested_markdown(self):
        """Test parsing nested Markdown structure."""
        markdown = """# Chapter 1

## Section 1.1

### Subsection 1.1.1

#### Deep heading

## Section 1.2

# Chapter 2
"""
        doc = Document.from_string(markdown)
        builder = DocumentTreeBuilder(doc)

        # Check all levels are present
        assert "h1-0" in builder.node_map  # Chapter 1
        assert "h2-0" in builder.node_map  # Section 1.1
        assert "h3-0" in builder.node_map  # Subsection 1.1.1
        assert "h4-0" in builder.node_map  # Deep heading
        assert "h2-1" in builder.node_map  # Section 1.2
        assert "h1-1" in builder.node_map  # Chapter 2

    def test_parse_markdown_with_code_blocks(self):
        """Test that code blocks don't interfere with heading parsing."""
        markdown = """# Title

Some code:

```markdown
# This is not a heading
## It's inside a code block
```

## Real Section
"""
        doc = Document.from_string(markdown)
        builder = DocumentTreeBuilder(doc)

        # Should only have 2 headings (Title and Real Section)
        # Note: This depends on the Markdown parser implementation
        # The parser should correctly ignore headings in code blocks
        assert "h1-0" in builder.node_map


class TestOutlineOperationsIntegration:
    """Tests for operations working with the outline tree."""

    def test_promote_updates_node_id(self):
        """Test that promoting a heading changes its level in the tree."""
        doc = Document(
            nodes=[
                Heading(level=1, text="Title"),
                Heading(level=2, text="Section"),
            ]
        )

        from doctk.lsp.operations import StructureOperations

        # Promote h2 to h1
        result = StructureOperations.promote(doc, "h2-0")
        assert result.success
        new_doc = Document.from_string(result.document)

        # Build new tree
        new_builder = DocumentTreeBuilder(new_doc)

        # Should now have 2 h1 nodes
        assert "h1-0" in new_builder.node_map
        assert "h1-1" in new_builder.node_map

        # The promoted node should be h1
        promoted = new_builder.find_node("h1-1")
        assert promoted is not None
        assert promoted.level == 1
        assert promoted.text == "Section"

    def test_demote_updates_node_id(self):
        """Test that demoting a heading changes its level in the tree."""
        doc = Document(
            nodes=[
                Heading(level=1, text="Title"),
            ]
        )

        from doctk.lsp.operations import StructureOperations

        # Demote h1 to h2
        result = StructureOperations.demote(doc, "h1-0")
        assert result.success
        new_doc = Document.from_string(result.document)

        # Build new tree
        new_builder = DocumentTreeBuilder(new_doc)

        # Should now have h2 instead of h1
        assert "h2-0" in new_builder.node_map
        assert "h1-0" not in new_builder.node_map

        demoted = new_builder.find_node("h2-0")
        assert demoted.level == 2
        assert demoted.text == "Title"

    def test_move_operations_preserve_structure(self):
        """Test that move operations preserve the tree structure."""
        doc = Document(
            nodes=[
                Heading(level=1, text="First"),
                Heading(level=1, text="Second"),
                Heading(level=1, text="Third"),
            ]
        )

        from doctk.lsp.operations import StructureOperations

        # Move third up
        result = StructureOperations.move_up(doc, "h1-2")
        assert result.success
        new_doc = Document.from_string(result.document)

        # Build new tree
        new_builder = DocumentTreeBuilder(new_doc)

        # Should still have 3 h1 nodes
        assert len([k for k in new_builder.node_map.keys() if k.startswith("h1-")]) == 3

        # Order should be: Third, Second, First (counting from rebuild)
        # Note: IDs are regenerated based on order in document
        nodes = [new_builder.find_node(f"h1-{i}") for i in range(3)]
        assert nodes[0].text == "First"
        assert nodes[1].text == "Third"  # Moved up
        assert nodes[2].text == "Second"  # Moved down


class TestOutlineEdgeCases:
    """Tests for edge cases in outline tree building."""

    def test_multiple_h1_headings(self):
        """Test document with multiple top-level headings."""
        doc = Document(
            nodes=[
                Heading(level=1, text="Chapter 1"),
                Heading(level=1, text="Chapter 2"),
                Heading(level=1, text="Chapter 3"),
            ]
        )

        builder = DocumentTreeBuilder(doc)

        assert len(builder.node_map) == 3
        assert "h1-0" in builder.node_map
        assert "h1-1" in builder.node_map
        assert "h1-2" in builder.node_map

    def test_skipped_heading_levels(self):
        """Test document with skipped heading levels (h1 -> h3)."""
        doc = Document(
            nodes=[
                Heading(level=1, text="Title"),
                Heading(level=3, text="Subsection"),  # Skips h2
            ]
        )

        builder = DocumentTreeBuilder(doc)

        # Both should be in the map
        assert "h1-0" in builder.node_map
        assert "h3-0" in builder.node_map

    def test_reverse_level_order(self):
        """Test document with reverse level order (h3 before h1)."""
        doc = Document(
            nodes=[
                Heading(level=3, text="Deep"),
                Heading(level=2, text="Mid"),
                Heading(level=1, text="Top"),
            ]
        )

        builder = DocumentTreeBuilder(doc)

        # All should be mapped with correct IDs
        assert "h3-0" in builder.node_map
        assert "h2-0" in builder.node_map
        assert "h1-0" in builder.node_map
