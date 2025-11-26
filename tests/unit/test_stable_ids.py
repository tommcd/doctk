"""
Unit tests for stable node identity system.

Tests the NodeId class and related identity infrastructure.
"""

import pytest

from doctk.core import ListItem
from doctk.identity import NodeId


class TestNodeIdBasicStructure:
    """Test basic NodeId structure and fields."""

    def test_node_id_has_required_fields(self) -> None:
        """Test NodeId class has content_hash, hint, and node_type fields."""
        node_id = NodeId(
            content_hash="a3f5b9c2d1e4f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1",
            hint="intro",
            node_type="heading",
        )

        assert (
            node_id.content_hash
            == "a3f5b9c2d1e4f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1"
        )
        assert node_id.hint == "intro"
        assert node_id.node_type == "heading"

    def test_node_id_is_frozen(self) -> None:
        """Test NodeId is immutable (frozen dataclass)."""
        node_id = NodeId(
            content_hash="a3f5b9c2d1e4f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1",
            hint="intro",
            node_type="heading",
        )

        # Attempting to modify should raise an error
        with pytest.raises(AttributeError):
            node_id.content_hash = "different_hash"

    def test_node_id_stores_full_64_char_hash(self) -> None:
        """Test NodeId stores the full 64-character SHA-256 hash."""
        full_hash = "a3f5b9c2d1e4f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1"
        node_id = NodeId(
            content_hash=full_hash,
            hint="test",
            node_type="paragraph",
        )

        assert len(node_id.content_hash) == 64
        assert node_id.content_hash == full_hash


class TestNodeIdStringRepresentation:
    """Test NodeId string representation methods."""

    def test_node_id_canonical_format(self) -> None:
        """Test 16-character canonical format."""
        node_id = NodeId(
            content_hash="a3f5b9c2d1e4f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1",
            hint="intro",
            node_type="heading",
        )
        assert str(node_id) == "heading:intro:a3f5b9c2d1e4f6a7"  # 16 chars

    def test_node_id_str_uses_16_char_hash_prefix(self) -> None:
        """Test __str__() uses exactly 16 characters from hash."""
        node_id = NodeId(
            content_hash="abcdef0123456789" + "x" * 48,  # 64 chars total
            hint="test",
            node_type="paragraph",
        )
        result = str(node_id)

        # Extract hash portion
        parts: list[str] = result.split(":")
        assert len(parts) == 3
        hash_part: str = parts[2]

        # Verify it's exactly 16 characters
        assert len(hash_part) == 16
        assert hash_part == "abcdef0123456789"

    def test_node_id_str_format_structure(self) -> None:
        """Test __str__() returns type:hint:hash16 format."""
        node_id = NodeId(
            content_hash="1234567890abcdef" + "0" * 48,
            hint="my-hint",
            node_type="codeblock",
        )
        result = str(node_id)

        assert result == "codeblock:my-hint:1234567890abcdef"
        assert result.count(":") == 2  # Two colons separating three parts

    def test_node_id_short_format(self) -> None:
        """Test 8-character display format."""
        node_id = NodeId(
            content_hash="a3f5b9c2d1e4f6a7b8c9d0e1f2a3b4c5",
            hint="intro",
            node_type="heading",
        )
        assert node_id.to_short_string() == "heading:intro:a3f5b9c2"  # 8 chars

    def test_node_id_short_format_uses_8_chars(self) -> None:
        """Test to_short_string() uses exactly 8 characters from hash."""
        node_id = NodeId(
            content_hash="abcdef01" + "x" * 56,  # 64 chars total
            hint="test",
            node_type="paragraph",
        )
        result: str = node_id.to_short_string()

        # Extract hash portion
        parts: list[str] = result.split(":")
        assert len(parts) == 3
        hash_part: str = parts[2]

        # Verify it's exactly 8 characters
        assert len(hash_part) == 8
        assert hash_part == "abcdef01"


class TestNodeIdParsing:
    """Test NodeId.from_string() parsing."""

    def test_from_string_valid_format(self) -> None:
        """Test parsing valid 16-char format."""
        node_id: NodeId = NodeId.from_string("heading:intro:a3f5b9c2d1e4f6a7")

        assert node_id.node_type == "heading"
        assert node_id.hint == "intro"
        assert node_id.content_hash == "a3f5b9c2d1e4f6a7"
        assert len(node_id.content_hash) == 16

    def test_from_string_invalid_format_no_colons(self) -> None:
        """Test validation rejects format without colons."""
        with pytest.raises(ValueError, match="Invalid NodeId format"):
            NodeId.from_string("invalid")

    def test_from_string_invalid_format_too_few_parts(self) -> None:
        """Test validation rejects format with too few parts."""
        with pytest.raises(ValueError, match="Invalid NodeId format"):
            NodeId.from_string("heading:intro")

    def test_from_string_invalid_hash_length_too_short(self) -> None:
        """Test validation rejects hash shorter than 16 chars."""
        with pytest.raises(ValueError, match="Invalid hash length"):
            NodeId.from_string("heading:intro:a3f5")  # Too short

    def test_from_string_invalid_hash_length_too_long(self) -> None:
        """Test validation rejects hash longer than 16 chars."""
        with pytest.raises(ValueError, match="Invalid hash length"):
            NodeId.from_string("heading:intro:a3f5b9c2d1e4f6a7extra")  # Too long


class TestNodeIdRoundTrip:
    """Test NodeId round-trip guarantee."""

    def test_round_trip_from_string_to_str(self) -> None:
        """Test round-trip from_string/str."""
        original = NodeId(
            content_hash="a3f5b9c2d1e4f6a7b8c9d0e1f2a3b4c5",
            hint="intro",
            node_type="heading",
        )
        string_repr = str(original)
        parsed: NodeId = NodeId.from_string(string_repr)

        assert parsed == original  # Round-trip works

    def test_round_trip_preserves_all_fields(self) -> None:
        """Test round-trip preserves node_type, hint, and hash prefix."""
        original = NodeId(
            content_hash="1234567890abcdef" + "x" * 48,
            hint="test-hint",
            node_type="paragraph",
        )

        # Round-trip
        string_repr = str(original)
        parsed: NodeId = NodeId.from_string(string_repr)

        assert parsed.node_type == original.node_type
        assert parsed.hint == original.hint
        assert parsed.content_hash[:16] == original.content_hash[:16]


class TestNodeIdEquality:
    """Test NodeId equality and hashing."""

    def test_equality_uses_first_16_characters(self) -> None:
        """Test equality uses first 16 characters."""
        id1 = NodeId(
            content_hash="a3f5b9c2d1e4f6a7" + "0" * 48,
            hint="test",
            node_type="heading",
        )
        id2 = NodeId(
            content_hash="a3f5b9c2d1e4f6a7" + "1" * 48,
            hint="test",
            node_type="heading",
        )

        assert id1 == id2  # Same first 16 chars

    def test_equality_requires_matching_type(self) -> None:
        """Test equality requires matching node_type."""
        id1 = NodeId(
            content_hash="a3f5b9c2d1e4f6a7" + "0" * 48,
            hint="test",
            node_type="heading",
        )
        id2 = NodeId(
            content_hash="a3f5b9c2d1e4f6a7" + "0" * 48,
            hint="test",
            node_type="paragraph",
        )

        assert id1 != id2  # Different types

    def test_equality_requires_matching_hint(self) -> None:
        """Test equality requires matching hint."""
        id1 = NodeId(
            content_hash="a3f5b9c2d1e4f6a7" + "0" * 48,
            hint="test1",
            node_type="heading",
        )
        id2 = NodeId(
            content_hash="a3f5b9c2d1e4f6a7" + "0" * 48,
            hint="test2",
            node_type="heading",
        )

        assert id1 != id2  # Different hints

    def test_hash_consistency_with_equality(self) -> None:
        """Test hash() is consistent with __eq__()."""
        id1 = NodeId(
            content_hash="a3f5b9c2d1e4f6a7" + "0" * 48,
            hint="test",
            node_type="heading",
        )
        id2 = NodeId(
            content_hash="a3f5b9c2d1e4f6a7" + "1" * 48,
            hint="test",
            node_type="heading",
        )

        # If equal, hashes must be equal
        assert id1 == id2
        assert hash(id1) == hash(id2)

    def test_hash_uses_first_16_characters(self) -> None:
        """Test hash() uses first 16 characters."""
        id1 = NodeId(
            content_hash="a3f5b9c2d1e4f6a7" + "0" * 48,
            hint="test",
            node_type="heading",
        )
        id2 = NodeId(
            content_hash="a3f5b9c2d1e4f6a7" + "1" * 48,
            hint="test",
            node_type="heading",
        )

        # Same hash because first 16 chars match
        assert hash(id1) == hash(id2)


class TestNodeIdFromNode:
    """Test NodeId.from_node() generation."""

    def test_from_node_generates_full_64_char_hash(self) -> None:
        """Test from_node() generates full 64-character hash."""
        from doctk.core import Heading

        heading = Heading(level=2, text="Introduction")
        node_id: NodeId = NodeId.from_node(heading)

        assert len(node_id.content_hash) == 64

    def test_from_node_generates_hint(self) -> None:
        """Test from_node() generates human-readable hint."""
        from doctk.core import Heading

        heading = Heading(level=2, text="API Reference")
        node_id: NodeId = NodeId.from_node(heading)

        assert node_id.hint == "api-reference"

    def test_from_node_sets_node_type(self) -> None:
        """Test from_node() sets correct node_type."""
        from doctk.core import Heading, Paragraph

        heading = Heading(level=2, text="Test")
        heading_id: NodeId = NodeId.from_node(heading)
        assert heading_id.node_type == "heading"

        paragraph = Paragraph(content="Test content")
        paragraph_id: NodeId = NodeId.from_node(paragraph)
        assert paragraph_id.node_type == "paragraph"

    def test_from_node_caching(self) -> None:
        """Test cache improves performance."""
        from doctk.core import Heading
        from doctk.identity import clear_node_id_cache

        # Clear cache first
        clear_node_id_cache()

        node = Heading(level=2, text="Test")

        # First call generates and caches
        id1: NodeId = NodeId.from_node(node)

        # Second call uses cache
        id2: NodeId = NodeId.from_node(node)

        assert id1 == id2
        assert id1 is id2  # Same object (cached)

    def test_from_node_deterministic(self) -> None:
        """Test from_node() is deterministic."""
        from doctk.core import Heading
        from doctk.identity import clear_node_id_cache

        # Clear cache to ensure fresh generation
        clear_node_id_cache()

        node1 = Heading(level=2, text="Test")
        node2 = Heading(level=2, text="Test")

        id1: NodeId = NodeId.from_node(node1)

        clear_node_id_cache()

        id2: NodeId = NodeId.from_node(node2)

        # Same content should produce same ID
        assert id1 == id2
        assert id1.content_hash == id2.content_hash


class TestHintGenerationEdgeCases:
    """Test edge cases in hint generation."""

    def test_hint_for_code_block_without_language(self) -> None:
        """Test hint generation for CodeBlock without language."""
        from doctk.core import CodeBlock
        from doctk.identity import _generate_hint

        code_block = CodeBlock(code="print('hello')", language=None)

        hint: str = _generate_hint(code_block)

        assert hint == "codeblock"

    def test_hint_for_paragraph_long_content(self) -> None:
        """Test hint generation for Paragraph with long content."""
        from doctk.core import Paragraph
        from doctk.identity import _generate_hint

        # Content longer than 50 chars
        long_content = "This is a very long paragraph that exceeds fifty characters"
        paragraph = Paragraph(content=long_content)

        hint: str = _generate_hint(paragraph)

        # Should use first 50 chars
        assert len(hint) <= 32
        assert "this-is-a-very-long-paragraph" in hint

    def test_hint_for_unknown_node_type(self) -> None:
        """Test hint generation fallback for unknown node types."""
        from doctk.core import List
        from doctk.identity import _generate_hint

        # List doesn't have special hint handling
        list_node = List(ordered=True, items=[])

        hint: str = _generate_hint(list_node)

        assert hint == "list"


class TestHintEdgeCases:
    """Test edge cases in hint generation."""

    def test_hint_for_code_block_without_language(self) -> None:
        """Test hint generation for CodeBlock without language."""
        from doctk.core import CodeBlock
        from doctk.identity import _generate_hint

        code_block = CodeBlock(code="print('hello')", language=None)
        hint: str = _generate_hint(code_block)
        assert hint == "codeblock"

    def test_hint_for_paragraph_long_content(self) -> None:
        """Test hint generation for Paragraph with long content."""
        from doctk.core import Paragraph
        from doctk.identity import _generate_hint

        long_content = "This is a very long paragraph that exceeds fifty characters"
        paragraph = Paragraph(content=long_content)
        hint: str = _generate_hint(paragraph)
        assert len(hint) <= 32

    def test_hint_for_list_node(self) -> None:
        """Test hint generation for List node."""
        from doctk.core import List
        from doctk.identity import _generate_hint

        list_node = List(ordered=True, items=[])
        hint: str = _generate_hint(list_node)
        assert hint == "list"


class TestCanonicalizationEdgeCases:
    """Test canonicalization edge cases."""

    def test_list_canonicalization(self) -> None:
        """Test List canonicalization."""
        from doctk.core import List, Paragraph
        from doctk.identity import _canonicalize_node

        items: list[ListItem] = [
            ListItem(content=[Paragraph(content="Item 1")]),
            ListItem(content=[Paragraph(content="Item 2")]),
        ]
        list_node = List(ordered=True, items=items)
        canonical: str = _canonicalize_node(list_node)
        # Ordered status NOT in canonical form (preserves ID across to_ordered/to_unordered)
        assert "list:" in canonical
        assert "listitem:" in canonical
        assert "ordered" not in canonical

    def test_list_item_canonicalization(self) -> None:
        """Test ListItem canonicalization."""
        from doctk.core import Paragraph
        from doctk.identity import _canonicalize_node

        list_item = ListItem(content=[Paragraph(content="Test content")])
        canonical: str = _canonicalize_node(list_item)
        assert "listitem:" in canonical
        assert "paragraph:" in canonical

    def test_block_quote_canonicalization(self) -> None:
        """Test BlockQuote canonicalization."""
        from doctk.core import BlockQuote, Paragraph
        from doctk.identity import _canonicalize_node

        block_quote = BlockQuote(content=[Paragraph(content="Quoted text")])
        canonical: str = _canonicalize_node(block_quote)
        assert "blockquote:" in canonical
        assert "paragraph:" in canonical
