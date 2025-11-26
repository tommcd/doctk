"""
Tests for ViewSourceMapping.

Verifies view-to-source position mapping for LSP features.
"""

import pytest

from doctk.identity import NodeId, SourceSpan, ViewSourceMapping


class TestViewSourceMapping:
    """Test ViewSourceMapping functionality."""

    def test_view_source_mapping_is_frozen(self):
        """Verify ViewSourceMapping is immutable."""
        view_span = SourceSpan(start_line=0, start_column=0, end_line=0, end_column=10)
        source_span = SourceSpan(start_line=5, start_column=0, end_line=5, end_column=10)
        node_id = NodeId(
            content_hash="a" * 64,
            hint="test",
            node_type="heading",
        )

        mapping = ViewSourceMapping(
            view_span=view_span,
            source_span=source_span,
            node_id=node_id,
            transform="identity",
        )

        # Should not be able to modify
        with pytest.raises(AttributeError):
            mapping.transform = "modified"  # type: ignore

    def test_project_to_source_single_line(self):
        """Test projecting position from view to source (single line)."""
        view_span = SourceSpan(
            start_line=0, start_column=0, end_line=0, end_column=20, source_file="view.md"
        )
        source_span = SourceSpan(
            start_line=10,
            start_column=5,
            end_line=10,
            end_column=25,
            source_file="source.md",
        )
        node_id = NodeId(
            content_hash="a" * 64,
            hint="test",
            node_type="heading",
        )

        mapping = ViewSourceMapping(
            view_span=view_span,
            source_span=source_span,
            node_id=node_id,
            transform="identity",
        )

        # Project position at column 10 in view
        source_file, source_line, source_column = mapping.project_to_source(0, 10)

        assert source_file == "source.md"
        assert source_line == 10
        assert source_column == 15  # 5 (start) + 10 (offset)

    def test_project_to_source_multiline(self):
        """Test projecting position from view to source (multi-line)."""
        view_span = SourceSpan(
            start_line=0, start_column=0, end_line=2, end_column=10, source_file="view.md"
        )
        source_span = SourceSpan(
            start_line=10,
            start_column=0,
            end_line=12,
            end_column=10,
            source_file="source.md",
        )
        node_id = NodeId(
            content_hash="a" * 64,
            hint="test",
            node_type="heading",
        )

        mapping = ViewSourceMapping(
            view_span=view_span,
            source_span=source_span,
            node_id=node_id,
            transform="identity",
        )

        # Project position on line 1 (not start line)
        source_file, source_line, source_column = mapping.project_to_source(1, 5)

        assert source_file == "source.md"
        assert source_line == 10
        assert source_column == 5  # Approximate offset for multi-line

    def test_project_to_source_position_not_in_span(self):
        """Test error when position is outside view span."""
        view_span = SourceSpan(
            start_line=0, start_column=0, end_line=0, end_column=10, source_file="view.md"
        )
        source_span = SourceSpan(
            start_line=10,
            start_column=0,
            end_line=10,
            end_column=10,
            source_file="source.md",
        )
        node_id = NodeId(
            content_hash="a" * 64,
            hint="test",
            node_type="heading",
        )

        mapping = ViewSourceMapping(
            view_span=view_span,
            source_span=source_span,
            node_id=node_id,
            transform="identity",
        )

        # Try to project position outside view span
        with pytest.raises(ValueError, match="not in view span"):
            mapping.project_to_source(5, 0)

    def test_identity_mapping(self):
        """Test identity mapping (view = source)."""
        span = SourceSpan(
            start_line=0, start_column=0, end_line=0, end_column=10, source_file="doc.md"
        )
        node_id = NodeId(
            content_hash="a" * 64,
            hint="test",
            node_type="heading",
        )

        mapping = ViewSourceMapping(
            view_span=span,
            source_span=span,  # Same span for identity
            node_id=node_id,
            transform="identity",
        )

        # Project position should map to same position
        source_file, source_line, source_column = mapping.project_to_source(0, 5)

        assert source_file == "doc.md"
        assert source_line == 0
        assert source_column == 5

    def test_promoted_heading_mapping(self):
        """Test mapping for promoted heading (structural change)."""
        # View: heading at line 0
        view_span = SourceSpan(
            start_line=0, start_column=0, end_line=0, end_column=15, source_file="view.md"
        )
        # Source: heading was at line 5
        source_span = SourceSpan(
            start_line=5,
            start_column=0,
            end_line=5,
            end_column=15,
            source_file="source.md",
        )
        node_id = NodeId(
            content_hash="a" * 64,
            hint="introduction",
            node_type="heading",
        )

        mapping = ViewSourceMapping(
            view_span=view_span,
            source_span=source_span,
            node_id=node_id,
            transform="promoted",
        )

        # Position in view maps back to original source
        source_file, source_line, source_column = mapping.project_to_source(0, 10)

        assert source_file == "source.md"
        assert source_line == 5
        assert source_column == 10

    def test_no_source_file(self):
        """Test mapping when source_file is None."""
        view_span = SourceSpan(start_line=0, start_column=0, end_line=0, end_column=10)
        source_span = SourceSpan(start_line=5, start_column=0, end_line=5, end_column=10)
        node_id = NodeId(
            content_hash="a" * 64,
            hint="test",
            node_type="heading",
        )

        mapping = ViewSourceMapping(
            view_span=view_span,
            source_span=source_span,
            node_id=node_id,
            transform="identity",
        )

        # Should return empty string for source_file
        source_file, source_line, source_column = mapping.project_to_source(0, 5)

        assert source_file == ""
        assert source_line == 5
        assert source_column == 5


class TestViewSourceMappingIntegration:
    """Test ViewSourceMapping with Document."""

    def test_document_stores_view_mappings(self):
        """Test that Document can store view mappings."""
        from doctk.core import Document, Heading

        heading = Heading(level=2, text="Test")
        doc = Document([heading])

        # Create a mapping
        view_span = SourceSpan(start_line=0, start_column=0, end_line=0, end_column=10)
        source_span = SourceSpan(start_line=5, start_column=0, end_line=5, end_column=10)
        node_id = NodeId(
            content_hash="a" * 64,
            hint="test",
            node_type="heading",
        )

        mapping = ViewSourceMapping(
            view_span=view_span,
            source_span=source_span,
            node_id=node_id,
            transform="identity",
        )

        # Add mapping to document
        doc.add_view_mapping(mapping)

        # Verify it's stored
        assert len(doc._view_mappings) == 1
        assert doc._view_mappings[0] == mapping

    def test_document_find_source_position(self):
        """Test Document.find_source_position() method."""
        from doctk.core import Document, Heading

        heading = Heading(level=2, text="Test")
        doc = Document([heading])

        # Create a mapping
        view_span = SourceSpan(
            start_line=0, start_column=0, end_line=0, end_column=10, source_file="view.md"
        )
        source_span = SourceSpan(
            start_line=5,
            start_column=0,
            end_line=5,
            end_column=10,
            source_file="source.md",
        )
        node_id = NodeId(
            content_hash="a" * 64,
            hint="test",
            node_type="heading",
        )

        mapping = ViewSourceMapping(
            view_span=view_span,
            source_span=source_span,
            node_id=node_id,
            transform="identity",
        )

        doc.add_view_mapping(mapping)

        # Find source position for view position
        result = doc.find_source_position(0, 5)

        assert result is not None
        source_file, source_line, source_column = result
        assert source_file == "source.md"
        assert source_line == 5
        assert source_column == 5

    def test_document_find_source_position_not_found(self):
        """Test Document.find_source_position() when position not mapped."""
        from doctk.core import Document, Heading

        heading = Heading(level=2, text="Test")
        doc = Document([heading])

        # No mappings added

        # Try to find source position
        result = doc.find_source_position(0, 5)

        assert result is None
