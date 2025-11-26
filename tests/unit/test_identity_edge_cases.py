"""
Tests for edge cases in identity module.
"""

from doctk.core import BlockQuote, CodeBlock, List, ListItem, Paragraph
from doctk.identity import ProvenanceContext, _canonicalize_node, _generate_hint


class TestCanonicalizationEdgeCases:
    """Test edge cases in canonicalization."""

    def test_list_canonicalization(self):
        """Test List canonicalization."""
        items = [
            ListItem(content=[Paragraph(content="Item 1")]),
            ListItem(content=[Paragraph(content="Item 2")]),
        ]
        list_node = List(ordered=True, items=items)

        canonical = _canonicalize_node(list_node)

        assert "list:ordered:" in canonical
        assert "listitem:" in canonical

    def test_list_item_canonicalization(self):
        """Test ListItem canonicalization."""
        list_item = ListItem(content=[Paragraph(content="Test content")])

        canonical = _canonicalize_node(list_item)

        assert "listitem:" in canonical
        assert "paragraph:" in canonical

    def test_block_quote_canonicalization(self):
        """Test BlockQuote canonicalization."""
        block_quote = BlockQuote(content=[Paragraph(content="Quoted text")])

        canonical = _canonicalize_node(block_quote)

        assert "blockquote:" in canonical
        assert "paragraph:" in canonical


class TestHintGenerationEdgeCases:
    """Test edge cases in hint generation."""

    def test_hint_for_code_block_without_language(self):
        """Test hint generation for CodeBlock without language."""
        code_block = CodeBlock(code="print('hello')", language=None)

        hint = _generate_hint(code_block)

        assert hint == "codeblock"

    def test_hint_for_paragraph_long_content(self):
        """Test hint generation for Paragraph with long content."""
        # Content longer than 50 chars
        long_content = "This is a very long paragraph that exceeds fifty characters"
        paragraph = Paragraph(content=long_content)

        hint = _generate_hint(paragraph)

        # Should use first 50 chars
        assert len(hint) <= 32
        assert "this-is-a-very-long-paragraph" in hint

    def test_hint_for_unknown_node_type(self):
        """Test hint generation fallback for unknown node types."""
        # List doesn't have special hint handling
        list_node = List(ordered=True, items=[])

        hint = _generate_hint(list_node)

        assert hint == "list"


class TestUnknownNodeTypeFallback:
    """Test fallback for unknown node types."""

    def test_canonicalization_unknown_type(self):
        """Test canonicalization fallback for unknown node types."""

        # Create a mock node type that's not in the standard set
        class CustomNode:
            def __str__(self):
                return "custom_content"

        custom = CustomNode()
        canonical = _canonicalize_node(custom)

        # Should use fallback: typename:str(node)
        assert canonical == "customnode:custom_content"


class TestHintEmptyFallback:
    """Test hint generation when text becomes empty after processing."""

    def test_hint_empty_after_special_char_removal(self):
        """Test hint fallback when only special chars present."""
        from doctk.core import Heading

        # Heading with only special characters
        heading = Heading(level=2, text="!@#$%^&*()")

        hint = _generate_hint(heading)

        # Should fallback to node type
        assert hint == "heading"

    def test_hint_empty_after_truncation_strip(self):
        """Test hint when truncation leaves only hyphens."""
        from doctk.core import Heading

        # Create text that becomes all hyphens after processing
        heading = Heading(level=2, text="- " * 20)  # Will become "--------..."

        hint = _generate_hint(heading)

        # After truncation and rstrip("-"), might be empty
        # Should fallback to node type if empty
        assert len(hint) > 0
        assert hint in ["heading", ""] or "-" in hint


class TestProvenanceGitFallback:
    """Test provenance git command fallbacks."""

    def test_provenance_context_without_git(self, monkeypatch):
        """Test ProvenanceContext when git commands fail."""
        import subprocess

        def mock_run(*args, **kwargs):
            raise FileNotFoundError("git not found")

        monkeypatch.setattr(subprocess, "run", mock_run)

        # Should not raise, should use fallbacks
        context = ProvenanceContext.from_file("/tmp/test.md")  # noqa: S108

        assert context.file_path == "/tmp/test.md"  # noqa: S108
        # version and author should be None
        assert context.version is None
        assert context.author is None

    def test_provenance_context_git_timeout(self, monkeypatch):
        """Test ProvenanceContext when git commands timeout."""
        import subprocess

        def mock_run(*args, **kwargs):
            raise subprocess.TimeoutExpired("git", 1)

        monkeypatch.setattr(subprocess, "run", mock_run)

        context = ProvenanceContext.from_file("/tmp/test.md")  # noqa: S108

        # Should handle timeout gracefully
        assert context.version is None
        assert context.author is None

    def test_provenance_context_git_error(self, monkeypatch):
        """Test ProvenanceContext when git commands return error."""
        import subprocess

        def mock_run(*args, **kwargs):
            raise subprocess.CalledProcessError(1, "git")

        monkeypatch.setattr(subprocess, "run", mock_run)

        context = ProvenanceContext.from_file("/tmp/test.md")  # noqa: S108

        # Should handle error gracefully
        assert context.version is None
        assert context.author is None


class TestNodeIdHashCollision:
    """Test NodeId behavior with hash collisions."""

    def test_node_id_equality_different_full_hash(self):
        """Test that NodeIds with same 16-char prefix are equal."""
        from doctk.identity import NodeId

        # Same first 16 chars, different after
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

        # Should be equal (first 16 chars match)
        assert id1 == id2
        assert hash(id1) == hash(id2)

    def test_node_id_inequality_different_prefix(self):
        """Test that NodeIds with different 16-char prefix are not equal."""
        from doctk.identity import NodeId

        id1 = NodeId(
            content_hash="a3f5b9c2d1e4f6a7" + "0" * 48,
            hint="test",
            node_type="heading",
        )
        id2 = NodeId(
            content_hash="b3f5b9c2d1e4f6a7" + "0" * 48,
            hint="test",
            node_type="heading",
        )

        # Should not be equal (first 16 chars differ)
        assert id1 != id2
        assert hash(id1) != hash(id2)
