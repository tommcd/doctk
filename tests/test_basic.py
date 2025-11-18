"""Basic tests for core functionality."""

from doctk import Document, Heading, Paragraph, compose, demote, heading, promote, select, where


def test_document_creation():
    """Test creating a document."""
    nodes = [
        Heading(level=1, text="Title"),
        Paragraph(content="Hello world"),
        Heading(level=2, text="Section"),
    ]
    doc = Document(nodes)

    assert len(doc) == 3
    assert isinstance(doc.nodes[0], Heading)
    assert isinstance(doc.nodes[1], Paragraph)


def test_document_from_string():
    """Test parsing markdown string."""
    md = """# Hello World

This is a paragraph.

## Section

Another paragraph.
"""
    doc = Document.from_string(md)

    assert len(doc) >= 3  # At least headings and paragraphs
    # Check first node is heading
    assert isinstance(doc.nodes[0], Heading)
    assert doc.nodes[0].level == 1
    assert doc.nodes[0].text == "Hello World"


def test_select_operation():
    """Test select operation."""
    nodes = [
        Heading(level=1, text="H1"),
        Paragraph(content="Para"),
        Heading(level=2, text="H2"),
    ]
    doc = Document(nodes)

    # Select headings
    headings = doc | select(lambda n: isinstance(n, Heading))

    assert len(headings) == 2
    assert all(isinstance(n, Heading) for n in headings)


def test_where_operation():
    """Test where operation."""
    nodes = [
        Heading(level=1, text="H1"),
        Heading(level=2, text="H2"),
        Heading(level=3, text="H3"),
    ]
    doc = Document(nodes)

    # Select level-2 headings
    h2_docs = doc | where(level=2)

    assert len(h2_docs) == 1
    assert h2_docs.nodes[0].level == 2


def test_promote_operation():
    """Test promote operation."""
    nodes = [Heading(level=3, text="H3"), Heading(level=2, text="H2")]
    doc = Document(nodes)

    # Promote all headings
    promoted = doc | select(lambda n: isinstance(n, Heading)) | promote()

    assert promoted.nodes[0].level == 2  # 3 -> 2
    assert promoted.nodes[1].level == 1  # 2 -> 1


def test_demote_operation():
    """Test demote operation."""
    nodes = [Heading(level=1, text="H1"), Heading(level=2, text="H2")]
    doc = Document(nodes)

    # Demote all headings
    demoted = doc | select(lambda n: isinstance(n, Heading)) | demote()

    assert demoted.nodes[0].level == 2  # 1 -> 2
    assert demoted.nodes[1].level == 3  # 2 -> 3


def test_compose_operations():
    """Test composition of operations."""
    nodes = [
        Heading(level=1, text="H1"),
        Heading(level=3, text="H3a"),
        Heading(level=3, text="H3b"),
        Paragraph(content="Para"),
    ]
    doc = Document(nodes)

    # Compose: select headings -> filter level 3 -> promote
    process = compose(promote(), where(level=3), heading)
    result = process(doc)

    assert len(result) == 2
    assert all(n.level == 2 for n in result)  # All promoted from 3 to 2


def test_map_operation():
    """Test map operation."""
    nodes = [Heading(level=2, text="H2"), Heading(level=3, text="H3")]
    doc = Document(nodes)

    # Map promote over all nodes
    result = doc.map(lambda n: n.promote() if isinstance(n, Heading) else n)

    assert result.nodes[0].level == 1
    assert result.nodes[1].level == 2


def test_filter_operation():
    """Test filter operation."""
    nodes = [
        Heading(level=1, text="H1"),
        Paragraph(content="Para"),
        Heading(level=2, text="H2"),
    ]
    doc = Document(nodes)

    # Filter to only headings
    headings = doc.filter(lambda n: isinstance(n, Heading))

    assert len(headings) == 2
    assert all(isinstance(n, Heading) for n in headings)


def test_union_operation():
    """Test union (set operation)."""
    doc1 = Document([Heading(level=1, text="H1")])
    doc2 = Document([Heading(level=2, text="H2")])

    result = doc1.union(doc2)

    assert len(result) == 2


def test_fluent_api():
    """Test fluent API (method chaining)."""
    nodes = [
        Heading(level=1, text="H1"),
        Heading(level=3, text="H3"),
        Paragraph(content="Para"),
    ]
    doc = Document(nodes)

    # Use fluent API
    result = doc.select(lambda n: isinstance(n, Heading)).select(lambda n: n.level == 3)

    assert len(result) == 1
    assert result.nodes[0].level == 3


def test_round_trip():
    """Test parsing and writing back to markdown."""
    original = """# Title

This is content.

## Section

More content.
"""
    doc = Document.from_string(original)
    output = doc.to_string()

    # Parse again to verify structure preserved
    doc2 = Document.from_string(output)

    assert len(doc) == len(doc2)
