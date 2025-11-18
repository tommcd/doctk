"""Tests for structure operations (lift, lower, nest, unnest)."""

import pytest

from doctk import Document, Heading, Paragraph, lift, lower, nest, unnest, where
from doctk.operations import heading


def test_lift_h3_to_h2():
    """Test that lift() promotes h3 to h2."""
    doc = Document(
        nodes=[
            Heading(level=3, text="Section 1.1.1"),
        ]
    )
    result = doc | heading | lift()
    assert len(result.nodes) == 1
    assert result.nodes[0].level == 2
    assert result.nodes[0].text == "Section 1.1.1"


def test_lift_h1_stays_h1():
    """Test that lift() keeps h1 at h1 (identity)."""
    doc = Document(
        nodes=[
            Heading(level=1, text="Chapter"),
        ]
    )
    result = doc | heading | lift()
    assert len(result.nodes) == 1
    assert result.nodes[0].level == 1
    assert result.nodes[0].text == "Chapter"


def test_lift_multiple_headings():
    """Test that lift() promotes multiple headings."""
    doc = Document(
        nodes=[
            Heading(level=3, text="Section 1"),
            Heading(level=3, text="Section 2"),
            Heading(level=4, text="Subsection"),
        ]
    )
    result = doc | heading | where(level=3) | lift()
    assert len(result.nodes) == 2
    assert result.nodes[0].level == 2
    assert result.nodes[0].text == "Section 1"
    assert result.nodes[1].level == 2
    assert result.nodes[1].text == "Section 2"


def test_lower_h2_to_h3():
    """Test that lower() demotes h2 to h3."""
    doc = Document(
        nodes=[
            Heading(level=2, text="Section 1"),
        ]
    )
    result = doc | heading | lower()
    assert len(result.nodes) == 1
    assert result.nodes[0].level == 3
    assert result.nodes[0].text == "Section 1"


def test_lower_h6_stays_h6():
    """Test that lower() keeps h6 at h6 (identity)."""
    doc = Document(
        nodes=[
            Heading(level=6, text="Deepest"),
        ]
    )
    result = doc | heading | lower()
    assert len(result.nodes) == 1
    assert result.nodes[0].level == 6
    assert result.nodes[0].text == "Deepest"


def test_lower_multiple_headings():
    """Test that lower() demotes multiple headings."""
    doc = Document(
        nodes=[
            Heading(level=2, text="Section 1"),
            Heading(level=2, text="Section 2"),
            Heading(level=3, text="Subsection"),
        ]
    )
    result = doc | heading | where(level=2) | lower()
    assert len(result.nodes) == 2
    assert result.nodes[0].level == 3
    assert result.nodes[0].text == "Section 1"
    assert result.nodes[1].level == 3
    assert result.nodes[1].text == "Section 2"


def test_nest_demotes_heading():
    """Test that nest() demotes headings (basic implementation)."""
    doc = Document(
        nodes=[
            Heading(level=2, text="Section"),
        ]
    )
    result = doc | heading | nest()
    assert len(result.nodes) == 1
    assert result.nodes[0].level == 3
    assert result.nodes[0].text == "Section"


def test_nest_with_under_parameter():
    """Test that nest() raises NotImplementedError when under parameter is provided."""
    doc = Document(
        nodes=[
            Heading(level=2, text="Parent"),
            Heading(level=2, text="Child"),
        ]
    )
    # Hierarchical nesting is not yet implemented
    with pytest.raises(NotImplementedError) as exc_info:
        doc | heading | where(text="Child") | nest(under="previous")

    assert "under" in str(exc_info.value).lower()
    assert "not yet implemented" in str(exc_info.value).lower()


def test_unnest_promotes_heading():
    """Test that unnest() promotes headings."""
    doc = Document(
        nodes=[
            Heading(level=4, text="Deeply Nested"),
        ]
    )
    result = doc | heading | unnest()
    assert len(result.nodes) == 1
    assert result.nodes[0].level == 3
    assert result.nodes[0].text == "Deeply Nested"


def test_unnest_h1_stays_h1():
    """Test that unnest() keeps h1 at h1."""
    doc = Document(
        nodes=[
            Heading(level=1, text="Top Level"),
        ]
    )
    result = doc | heading | unnest()
    assert len(result.nodes) == 1
    assert result.nodes[0].level == 1


def test_lift_non_heading_unchanged():
    """Test that lift() doesn't affect non-heading nodes."""
    doc = Document(
        nodes=[
            Paragraph(content="Some text"),
        ]
    )
    # Apply lift to all (paragraph should be unchanged)
    result = doc | lift()
    assert len(result.nodes) == 1
    assert isinstance(result.nodes[0], Paragraph)
    assert result.nodes[0].content == "Some text"


def test_lower_non_heading_unchanged():
    """Test that lower() doesn't affect non-heading nodes."""
    doc = Document(
        nodes=[
            Paragraph(content="Some text"),
        ]
    )
    result = doc | lower()
    assert len(result.nodes) == 1
    assert isinstance(result.nodes[0], Paragraph)
    assert result.nodes[0].content == "Some text"


def test_structure_operations_compose():
    """Test that structure operations compose correctly."""
    doc = Document(
        nodes=[
            Heading(level=3, text="Section"),
        ]
    )
    # Lift then lower should return to original level
    result = doc | heading | lift() | lower()
    assert len(result.nodes) == 1
    assert result.nodes[0].level == 3


def test_lift_lower_roundtrip():
    """Test that lift and lower are inverses (for most levels)."""
    doc = Document(
        nodes=[
            Heading(level=3, text="Section"),
        ]
    )
    # Apply lift then lower
    lifted = doc | heading | lift()
    roundtrip = lifted | heading | lower()

    assert len(roundtrip.nodes) == 1
    assert roundtrip.nodes[0].level == 3
    assert roundtrip.nodes[0].text == "Section"


def test_operations_immutability():
    """Test that structure operations don't mutate original document."""
    original_heading = Heading(level=3, text="Original")
    doc = Document(nodes=[original_heading])

    # Apply lift
    _result = doc | heading | lift()

    # Original should be unchanged
    assert original_heading.level == 3
    assert original_heading.text == "Original"

    # Original document should be unchanged
    assert doc.nodes[0].level == 3
