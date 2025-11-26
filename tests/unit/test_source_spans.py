"""
Unit tests for source span tracking.

Tests the SourceSpan class for tracking source positions.
"""

import pytest

from doctk.identity import SourceSpan


class TestSourceSpan:
    """Test SourceSpan class."""

    def test_source_span_is_frozen(self):
        """Test SourceSpan is immutable (frozen dataclass)."""
        span = SourceSpan(start_line=0, start_column=0, end_line=5, end_column=10)

        # Attempting to modify should raise an error
        with pytest.raises(AttributeError):
            span.start_line = 1

    def test_source_span_contains_position_inside(self):
        """Test contains() returns True for position inside span."""
        span = SourceSpan(start_line=5, start_column=10, end_line=10, end_column=20)

        # Position in middle of span
        assert span.contains(7, 15) is True

        # Position at start
        assert span.contains(5, 10) is True

        # Position at end
        assert span.contains(10, 20) is True

    def test_source_span_contains_position_outside(self):
        """Test contains() returns False for position outside span."""
        span = SourceSpan(start_line=5, start_column=10, end_line=10, end_column=20)

        # Before span
        assert span.contains(4, 15) is False
        assert span.contains(5, 9) is False

        # After span
        assert span.contains(11, 15) is False
        assert span.contains(10, 21) is False

    def test_source_span_contains_single_line(self):
        """Test contains() for single-line span."""
        span = SourceSpan(start_line=5, start_column=10, end_line=5, end_column=20)

        # Inside span
        assert span.contains(5, 15) is True

        # At boundaries
        assert span.contains(5, 10) is True
        assert span.contains(5, 20) is True

        # Outside span
        assert span.contains(5, 9) is False
        assert span.contains(5, 21) is False
        assert span.contains(4, 15) is False
        assert span.contains(6, 15) is False

    def test_source_span_overlaps_with_overlap(self):
        """Test overlaps() returns True for overlapping spans."""
        span1 = SourceSpan(start_line=5, start_column=0, end_line=10, end_column=0)
        span2 = SourceSpan(start_line=8, start_column=0, end_line=12, end_column=0)

        assert span1.overlaps(span2) is True
        assert span2.overlaps(span1) is True

    def test_source_span_overlaps_no_overlap(self):
        """Test overlaps() returns False for non-overlapping spans."""
        span1 = SourceSpan(start_line=5, start_column=0, end_line=10, end_column=0)
        span2 = SourceSpan(start_line=11, start_column=0, end_line=15, end_column=0)

        assert span1.overlaps(span2) is False
        assert span2.overlaps(span1) is False

    def test_source_span_overlaps_adjacent(self):
        """Test overlaps() for adjacent spans (touching but not overlapping)."""
        span1 = SourceSpan(start_line=5, start_column=0, end_line=10, end_column=0)
        span2 = SourceSpan(start_line=10, start_column=0, end_line=15, end_column=0)

        # Adjacent spans should overlap (end_line == start_line)
        assert span1.overlaps(span2) is True
        assert span2.overlaps(span1) is True

    def test_source_span_overlaps_contained(self):
        """Test overlaps() when one span is contained in another."""
        span1 = SourceSpan(start_line=5, start_column=0, end_line=15, end_column=0)
        span2 = SourceSpan(start_line=8, start_column=0, end_line=12, end_column=0)

        assert span1.overlaps(span2) is True
        assert span2.overlaps(span1) is True

    def test_source_span_overlaps_identical(self):
        """Test overlaps() for identical spans."""
        span1 = SourceSpan(start_line=5, start_column=10, end_line=10, end_column=20)
        span2 = SourceSpan(start_line=5, start_column=10, end_line=10, end_column=20)

        assert span1.overlaps(span2) is True
        assert span2.overlaps(span1) is True
