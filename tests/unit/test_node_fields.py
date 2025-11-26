"""
Unit tests for Node base class fields.

Tests that all node types have id, provenance, and source_span fields.
"""

from doctk.core import BlockQuote, CodeBlock, Heading, List, ListItem, Paragraph
from doctk.identity import NodeId, Provenance, SourceSpan


class TestNodeFields:
    """Test that all node types have the required identity fields."""

    def test_heading_has_identity_fields(self):
        """Test Heading has id, provenance, source_span fields."""
        heading = Heading(level=2, text="Test")

        assert hasattr(heading, "id")
        assert hasattr(heading, "provenance")
        assert hasattr(heading, "source_span")
        assert heading.id is None
        assert heading.provenance is None
        assert heading.source_span is None

    def test_paragraph_has_identity_fields(self):
        """Test Paragraph has id, provenance, source_span fields."""
        paragraph = Paragraph(content="Test content")

        assert hasattr(paragraph, "id")
        assert hasattr(paragraph, "provenance")
        assert hasattr(paragraph, "source_span")
        assert paragraph.id is None
        assert paragraph.provenance is None
        assert paragraph.source_span is None

    def test_codeblock_has_identity_fields(self):
        """Test CodeBlock has id, provenance, source_span fields."""
        code_block = CodeBlock(code="print('hello')", language="python")

        assert hasattr(code_block, "id")
        assert hasattr(code_block, "provenance")
        assert hasattr(code_block, "source_span")
        assert code_block.id is None
        assert code_block.provenance is None
        assert code_block.source_span is None

    def test_list_has_identity_fields(self):
        """Test List has id, provenance, source_span fields."""
        list_node = List(ordered=True, items=[])

        assert hasattr(list_node, "id")
        assert hasattr(list_node, "provenance")
        assert hasattr(list_node, "source_span")
        assert list_node.id is None
        assert list_node.provenance is None
        assert list_node.source_span is None

    def test_listitem_has_identity_fields(self):
        """Test ListItem has id, provenance, source_span fields."""
        list_item = ListItem(content=[])

        assert hasattr(list_item, "id")
        assert hasattr(list_item, "provenance")
        assert hasattr(list_item, "source_span")
        assert list_item.id is None
        assert list_item.provenance is None
        assert list_item.source_span is None

    def test_blockquote_has_identity_fields(self):
        """Test BlockQuote has id, provenance, source_span fields."""
        block_quote = BlockQuote(content=[])

        assert hasattr(block_quote, "id")
        assert hasattr(block_quote, "provenance")
        assert hasattr(block_quote, "source_span")
        assert block_quote.id is None
        assert block_quote.provenance is None
        assert block_quote.source_span is None

    def test_node_with_id(self):
        """Test creating node with NodeId."""
        node_id = NodeId(content_hash="a" * 64, hint="test", node_type="heading")
        heading = Heading(level=2, text="Test", id=node_id)

        assert heading.id == node_id

    def test_node_with_provenance(self):
        """Test creating node with Provenance."""
        from datetime import datetime

        provenance = Provenance(
            origin_file="test.md",
            version="v1.0",
            author="Test User",
            created_at=datetime.now(),
            modified_at=None,
            parent_id=None,
        )
        heading = Heading(level=2, text="Test", provenance=provenance)

        assert heading.provenance == provenance

    def test_node_with_source_span(self):
        """Test creating node with SourceSpan."""
        source_span = SourceSpan(start_line=0, start_column=0, end_line=5, end_column=10)
        heading = Heading(level=2, text="Test", source_span=source_span)

        assert heading.source_span == source_span

    def test_existing_constructors_remain_compatible(self):
        """Test that existing code without new fields still works."""
        # These should all work without specifying id, provenance, source_span
        heading = Heading(level=2, text="Test")
        paragraph = Paragraph(content="Test")
        code_block = CodeBlock(code="test")
        list_node = List(ordered=True, items=[])
        list_item = ListItem(content=[])
        block_quote = BlockQuote(content=[])

        # All should have None for new fields
        assert heading.id is None
        assert paragraph.id is None
        assert code_block.id is None
        assert list_node.id is None
        assert list_item.id is None
        assert block_quote.id is None
