"""Tests for level operations (promote, demote) in the functional pipeline.

Structural moves (nest, unnest, move_up, move_down) relocate sections by
node id and live in doctk.integration.StructureOperations; they are tested
in test_lsp_operations.py and test_interface.py.
"""

from doctk import Document, Heading, Paragraph, demote, promote, where
from doctk.operations import heading


def test_promote_h3_to_h2():
    """Test that promote() lifts h3 to h2."""
    doc = Document(
        nodes=[
            Heading(level=3, text="Section 1.1.1"),
        ]
    )
    result = doc | heading | promote()
    assert len(result.nodes) == 1
    assert result.nodes[0].level == 2
    assert result.nodes[0].text == "Section 1.1.1"


def test_promote_h1_stays_h1():
    """Test that promote() keeps h1 at h1 (identity)."""
    doc = Document(
        nodes=[
            Heading(level=1, text="Chapter"),
        ]
    )
    result = doc | heading | promote()
    assert len(result.nodes) == 1
    assert result.nodes[0].level == 1
    assert result.nodes[0].text == "Chapter"


def test_promote_multiple_headings():
    """Test that promote() lifts multiple headings."""
    doc = Document(
        nodes=[
            Heading(level=3, text="Section 1"),
            Heading(level=3, text="Section 2"),
            Heading(level=4, text="Subsection"),
        ]
    )
    result = doc | heading | where(level=3) | promote()
    assert len(result.nodes) == 2
    assert result.nodes[0].level == 2
    assert result.nodes[0].text == "Section 1"
    assert result.nodes[1].level == 2
    assert result.nodes[1].text == "Section 2"


def test_demote_h2_to_h3():
    """Test that demote() lowers h2 to h3."""
    doc = Document(
        nodes=[
            Heading(level=2, text="Section 1"),
        ]
    )
    result = doc | heading | demote()
    assert len(result.nodes) == 1
    assert result.nodes[0].level == 3
    assert result.nodes[0].text == "Section 1"


def test_demote_h6_stays_h6():
    """Test that demote() keeps h6 at h6 (identity)."""
    doc = Document(
        nodes=[
            Heading(level=6, text="Deepest"),
        ]
    )
    result = doc | heading | demote()
    assert len(result.nodes) == 1
    assert result.nodes[0].level == 6
    assert result.nodes[0].text == "Deepest"


def test_demote_multiple_headings():
    """Test that demote() lowers multiple headings."""
    doc = Document(
        nodes=[
            Heading(level=2, text="Section 1"),
            Heading(level=2, text="Section 2"),
            Heading(level=3, text="Subsection"),
        ]
    )
    result = doc | heading | where(level=2) | demote()
    assert len(result.nodes) == 2
    assert result.nodes[0].level == 3
    assert result.nodes[0].text == "Section 1"
    assert result.nodes[1].level == 3
    assert result.nodes[1].text == "Section 2"


def test_functional_layer_has_no_structural_moves():
    """nest/unnest/lift/lower are not part of the functional vocabulary.

    Structural moves are id-addressed and live in StructureOperations;
    the old aliases (lift=promote, nest()=demote, ...) gave the same
    names conflicting meanings across layers.
    """
    import doctk
    import doctk.operations as ops

    for name in ("nest", "unnest", "lift", "lower"):
        assert not hasattr(ops, name), f"operations.{name} should not exist"
        assert name not in doctk.__all__


def test_promote_non_heading_unchanged():
    """Test that promote() doesn't affect non-heading nodes."""
    doc = Document(
        nodes=[
            Paragraph(content="Some text"),
        ]
    )
    result = doc | promote()
    assert len(result.nodes) == 1
    assert isinstance(result.nodes[0], Paragraph)
    assert result.nodes[0].content == "Some text"


def test_demote_non_heading_unchanged():
    """Test that demote() doesn't affect non-heading nodes."""
    doc = Document(
        nodes=[
            Paragraph(content="Some text"),
        ]
    )
    result = doc | demote()
    assert len(result.nodes) == 1
    assert isinstance(result.nodes[0], Paragraph)
    assert result.nodes[0].content == "Some text"


def test_structure_operations_compose():
    """Test that level operations compose correctly."""
    doc = Document(
        nodes=[
            Heading(level=3, text="Section"),
        ]
    )
    # Promote then demote should return to original level
    result = doc | heading | promote() | demote()
    assert len(result.nodes) == 1
    assert result.nodes[0].level == 3


def test_promote_demote_roundtrip():
    """Test that promote and demote are inverses (away from the boundaries)."""
    doc = Document(
        nodes=[
            Heading(level=3, text="Section"),
        ]
    )
    promoted = doc | heading | promote()
    roundtrip = promoted | heading | demote()

    assert len(roundtrip.nodes) == 1
    assert roundtrip.nodes[0].level == 3
    assert roundtrip.nodes[0].text == "Section"


def test_operations_immutability():
    """Test that level operations don't mutate the original document."""
    original_heading = Heading(level=3, text="Original")
    doc = Document(nodes=[original_heading])

    _result = doc | heading | promote()

    # Original should be unchanged
    assert original_heading.level == 3
    assert original_heading.text == "Original"

    # Original document should be unchanged
    assert doc.nodes[0].level == 3
