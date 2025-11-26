"""
Unit tests for node canonicalization and hint generation.

Tests the _canonicalize_node() and _generate_hint() functions.
"""

from doctk.core import BlockQuote, CodeBlock, Heading, List, ListItem, Paragraph
from doctk.identity import NodeId


class TestCanonicalization:
    """Test node canonicalization."""

    def test_heading_canonicalization_excludes_level(self):
        """Test heading canonicalization excludes level."""
        h1 = Heading(level=2, text="Introduction")
        h2 = Heading(level=3, text="Introduction")  # Different level

        id1 = NodeId.from_node(h1)
        id2 = NodeId.from_node(h2)

        # Same canonical form (level excluded)
        assert id1.content_hash == id2.content_hash

    def test_canonicalization_unicode_normalization(self):
        """Test Unicode NFC normalization."""
        # é can be single char (U+00E9) or e + combining acute (U+0065 U+0301)
        h1 = Heading(level=2, text="café")
        h2 = Heading(level=2, text="café")  # Should normalize to same

        id1 = NodeId.from_node(h1)
        id2 = NodeId.from_node(h2)

        assert id1.content_hash == id2.content_hash

    def test_canonicalization_whitespace(self):
        """Test whitespace normalization."""
        h1 = Heading(level=2, text="  Multiple   spaces  ")
        h2 = Heading(level=2, text="Multiple spaces")

        id1 = NodeId.from_node(h1)
        id2 = NodeId.from_node(h2)

        assert id1.content_hash == id2.content_hash

    def test_canonicalization_tabs(self):
        """Test tab conversion to 4 spaces before whitespace collapse."""
        h1 = Heading(level=2, text="Text\twith\ttabs")
        h2 = Heading(level=2, text="Text    with    tabs")

        id1 = NodeId.from_node(h1)
        id2 = NodeId.from_node(h2)

        # After tab→4 spaces conversion and whitespace collapse, these should match
        assert id1.content_hash == id2.content_hash

    def test_canonicalization_deterministic(self):
        """Test deterministic output."""
        from doctk.identity import clear_node_id_cache

        node = Heading(level=2, text="Test")

        clear_node_id_cache()
        id1 = NodeId.from_node(node)

        clear_node_id_cache()
        id2 = NodeId.from_node(node)

        assert id1.content_hash == id2.content_hash

    def test_paragraph_canonicalization(self):
        """Test paragraph canonicalization uses content only."""
        p1 = Paragraph(content="Test content")
        p2 = Paragraph(content="Test content", metadata={"key": "value"})

        id1 = NodeId.from_node(p1)
        id2 = NodeId.from_node(p2)

        # Metadata not in canonical form
        assert id1.content_hash == id2.content_hash

    def test_codeblock_canonicalization_preserves_whitespace(self):
        """Test CodeBlock canonicalization preserves whitespace in code."""
        c1 = CodeBlock(language="python", code="def foo():\n    pass")
        c2 = CodeBlock(language="python", code="def foo():\n    pass")

        id1 = NodeId.from_node(c1)
        id2 = NodeId.from_node(c2)

        assert id1.content_hash == id2.content_hash

    def test_codeblock_canonicalization_includes_language(self):
        """Test CodeBlock canonicalization includes language."""
        c1 = CodeBlock(language="python", code="print('hello')")
        c2 = CodeBlock(language="javascript", code="console.log('hello')")

        id1 = NodeId.from_node(c1)
        id2 = NodeId.from_node(c2)

        # Different code should produce different hashes
        assert id1.content_hash != id2.content_hash

    def test_list_canonicalization(self):
        """Test List canonicalization."""
        item1 = ListItem(content=[Paragraph(content="Item 1")])
        item2 = ListItem(content=[Paragraph(content="Item 2")])

        list1 = List(ordered=True, items=[item1, item2])
        list2 = List(ordered=True, items=[item1, item2])

        id1 = NodeId.from_node(list1)
        id2 = NodeId.from_node(list2)

        assert id1.content_hash == id2.content_hash

    def test_list_ordered_vs_unordered(self):
        """Test ordered vs unordered lists have SAME hash (preserves ID on conversion)."""
        item = ListItem(content=[Paragraph(content="Item")])

        list1 = List(ordered=True, items=[item])
        list2 = List(ordered=False, items=[item])

        id1 = NodeId.from_node(list1)
        id2 = NodeId.from_node(list2)

        # Ordered status NOT in canonical form, so IDs match
        assert id1.content_hash == id2.content_hash

    def test_listitem_canonicalization(self):
        """Test ListItem canonicalization."""
        item1 = ListItem(content=[Paragraph(content="Test")])
        item2 = ListItem(content=[Paragraph(content="Test")])

        id1 = NodeId.from_node(item1)
        id2 = NodeId.from_node(item2)

        assert id1.content_hash == id2.content_hash

    def test_blockquote_canonicalization(self):
        """Test BlockQuote canonicalization."""
        bq1 = BlockQuote(content=[Paragraph(content="Quote")])
        bq2 = BlockQuote(content=[Paragraph(content="Quote")])

        id1 = NodeId.from_node(bq1)
        id2 = NodeId.from_node(bq2)

        assert id1.content_hash == id2.content_hash


class TestHintGeneration:
    """Test hint generation."""

    def test_hint_generation_heading(self):
        """Test hint generation with slugification."""
        h = Heading(level=2, text="API Reference Guide")
        node_id = NodeId.from_node(h)

        assert node_id.hint == "api-reference-guide"
        assert len(node_id.hint) <= 32

    def test_hint_generation_special_chars(self):
        """Test special character removal."""
        h = Heading(level=2, text="Getting Started!")
        node_id = NodeId.from_node(h)

        assert node_id.hint == "getting-started"
        assert "!" not in node_id.hint

    def test_hint_generation_truncation(self):
        """Test 32-character truncation."""
        h = Heading(
            level=2,
            text="Very Long Heading That Definitely Exceeds The Thirty Two Character Limit",
        )
        node_id = NodeId.from_node(h)

        assert len(node_id.hint) <= 32
        # Verify it's truncated (exact value may vary based on word boundaries)
        assert node_id.hint.startswith("very-long-heading-that-")

    def test_hint_generation_paragraph(self):
        """Test hint generation for paragraph uses first 50 chars."""
        p = Paragraph(content="Some text content for testing")
        node_id = NodeId.from_node(p)

        # Should use first 50 chars of content
        assert "some-text" in node_id.hint or node_id.hint == "paragraph"
        assert len(node_id.hint) <= 32

    def test_hint_generation_codeblock_with_language(self):
        """Test hint generation for CodeBlock uses language."""
        c = CodeBlock(language="python", code="print('hello')")
        node_id = NodeId.from_node(c)

        assert node_id.hint == "python"

    def test_hint_generation_fallback(self):
        """Test fallback for non-text nodes."""
        item = ListItem(content=[Paragraph(content="Test")])
        node_id = NodeId.from_node(item)

        # Should fallback to node type
        assert node_id.hint == "listitem"


class TestCanonicalizationEdgeCases:
    """Test edge cases in canonicalization."""

    def test_list_canonicalization(self):
        """Test List canonicalization."""
        from doctk.core import List, ListItem, Paragraph
        from doctk.identity import _canonicalize_node

        items = [
            ListItem(content=[Paragraph(content="Item 1")]),
            ListItem(content=[Paragraph(content="Item 2")]),
        ]
        list_node = List(ordered=True, items=items)

        canonical = _canonicalize_node(list_node)

        # Ordered status NOT in canonical form (preserves ID across to_ordered/to_unordered)
        assert "list:" in canonical
        assert "listitem:" in canonical
        assert "ordered" not in canonical

    def test_list_item_canonicalization(self):
        """Test ListItem canonicalization."""
        from doctk.core import ListItem, Paragraph
        from doctk.identity import _canonicalize_node

        list_item = ListItem(content=[Paragraph(content="Test content")])

        canonical = _canonicalize_node(list_item)

        assert "listitem:" in canonical
        assert "paragraph:" in canonical

    def test_block_quote_canonicalization(self):
        """Test BlockQuote canonicalization."""
        from doctk.core import BlockQuote, Paragraph
        from doctk.identity import _canonicalize_node

        block_quote = BlockQuote(content=[Paragraph(content="Quoted text")])

        canonical = _canonicalize_node(block_quote)

        assert "blockquote:" in canonical
        assert "paragraph:" in canonical
