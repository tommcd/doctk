"""
Unit tests for stable node identity system.

Tests the NodeId class and related identity infrastructure.
"""

import pytest

from doctk.identity import NodeId


class TestNodeIdBasicStructure:
    """Test basic NodeId structure and fields."""

    def test_node_id_has_required_fields(self):
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

    def test_node_id_is_frozen(self):
        """Test NodeId is immutable (frozen dataclass)."""
        node_id = NodeId(
            content_hash="a3f5b9c2d1e4f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1",
            hint="intro",
            node_type="heading",
        )

        # Attempting to modify should raise an error
        with pytest.raises(AttributeError):
            node_id.content_hash = "different_hash"

    def test_node_id_stores_full_64_char_hash(self):
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

    def test_node_id_canonical_format(self):
        """Test 16-character canonical format."""
        node_id = NodeId(
            content_hash="a3f5b9c2d1e4f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1",
            hint="intro",
            node_type="heading",
        )
        assert str(node_id) == "heading:intro:a3f5b9c2d1e4f6a7"  # 16 chars

    def test_node_id_str_uses_16_char_hash_prefix(self):
        """Test __str__() uses exactly 16 characters from hash."""
        node_id = NodeId(
            content_hash="abcdef0123456789" + "x" * 48,  # 64 chars total
            hint="test",
            node_type="paragraph",
        )
        result = str(node_id)

        # Extract hash portion
        parts = result.split(":")
        assert len(parts) == 3
        hash_part = parts[2]

        # Verify it's exactly 16 characters
        assert len(hash_part) == 16
        assert hash_part == "abcdef0123456789"

    def test_node_id_str_format_structure(self):
        """Test __str__() returns type:hint:hash16 format."""
        node_id = NodeId(
            content_hash="1234567890abcdef" + "0" * 48,
            hint="my-hint",
            node_type="codeblock",
        )
        result = str(node_id)

        assert result == "codeblock:my-hint:1234567890abcdef"
        assert result.count(":") == 2  # Two colons separating three parts
