"""
Unit tests for Document ID indexing.

Tests the Document._id_index, find_node(), and find_nodes() functionality.
"""

from doctk.core import Document, Heading, Paragraph
from doctk.identity import NodeId


class TestDocumentIndexing:
    """Test Document ID indexing functionality."""

    def test_document_builds_id_index_on_init(self):
        """Test that Document builds ID index on initialization."""
        node_id1 = NodeId(content_hash="a" * 64, hint="test1", node_type="heading")
        node_id2 = NodeId(content_hash="b" * 64, hint="test2", node_type="paragraph")

        heading = Heading(level=2, text="Test", id=node_id1)
        paragraph = Paragraph(content="Content", id=node_id2)

        doc = Document([heading, paragraph])

        # Index should be built
        assert len(doc._id_index) == 2
        assert node_id1 in doc._id_index
        assert node_id2 in doc._id_index

    def test_find_node_returns_node_with_matching_id(self):
        """Test find_node() returns node with matching ID."""
        node_id = NodeId(content_hash="a" * 64, hint="test", node_type="heading")
        heading = Heading(level=2, text="Test", id=node_id)
        paragraph = Paragraph(content="Content")

        doc = Document([heading, paragraph])

        found = doc.find_node(node_id)
        assert found == heading

    def test_find_node_returns_none_for_missing_id(self):
        """Test find_node() returns None when ID not found."""
        node_id = NodeId(content_hash="a" * 64, hint="test", node_type="heading")
        missing_id = NodeId(content_hash="b" * 64, hint="missing", node_type="heading")

        heading = Heading(level=2, text="Test", id=node_id)
        doc = Document([heading])

        found = doc.find_node(missing_id)
        assert found is None

    def test_find_node_o1_lookup(self):
        """Test find_node() provides O(1) lookup performance."""
        # Create many nodes
        nodes = []
        target_id = None
        for i in range(1000):
            node_id = NodeId(content_hash=f"{i:064d}", hint=f"node{i}", node_type="heading")
            if i == 500:
                target_id = node_id
            nodes.append(Heading(level=2, text=f"Heading {i}", id=node_id))

        doc = Document(nodes)

        # Should find quickly (O(1) via dict lookup)
        found = doc.find_node(target_id)
        assert found is not None
        assert found.text == "Heading 500"

    def test_find_nodes_returns_matching_nodes(self):
        """Test find_nodes() returns all nodes matching predicate."""
        heading1 = Heading(level=2, text="Heading 1")
        paragraph1 = Paragraph(content="Content 1")
        heading2 = Heading(level=3, text="Heading 2")
        paragraph2 = Paragraph(content="Content 2")

        doc = Document([heading1, paragraph1, heading2, paragraph2])

        # Find all headings
        headings = doc.find_nodes(lambda n: isinstance(n, Heading))
        assert len(headings.nodes) == 2
        assert heading1 in headings.nodes
        assert heading2 in headings.nodes

    def test_find_nodes_returns_empty_document_when_no_matches(self):
        """Test find_nodes() returns empty Document when no matches."""
        paragraph = Paragraph(content="Content")
        doc = Document([paragraph])

        # Find headings (none exist)
        headings = doc.find_nodes(lambda n: isinstance(n, Heading))
        assert len(headings.nodes) == 0

    def test_find_nodes_on_performance(self):
        """Test find_nodes() has O(n) performance."""
        # Create many nodes
        nodes = []
        for i in range(1000):
            if i % 2 == 0:
                nodes.append(Heading(level=2, text=f"Heading {i}"))
            else:
                nodes.append(Paragraph(content=f"Content {i}"))

        doc = Document(nodes)

        # Find all headings
        headings = doc.find_nodes(lambda n: isinstance(n, Heading))
        assert len(headings.nodes) == 500

    def test_index_updated_after_filter(self):
        """Test that ID index is updated after filter operation."""
        node_id1 = NodeId(content_hash="a" * 64, hint="test1", node_type="heading")
        node_id2 = NodeId(content_hash="b" * 64, hint="test2", node_type="paragraph")

        heading = Heading(level=2, text="Test", id=node_id1)
        paragraph = Paragraph(content="Content", id=node_id2)

        doc = Document([heading, paragraph])

        # Filter to only headings
        filtered = doc.filter(lambda n: isinstance(n, Heading))

        # Index should only contain heading
        assert len(filtered._id_index) == 1
        assert node_id1 in filtered._id_index
        assert node_id2 not in filtered._id_index

    def test_index_handles_nodes_without_ids(self):
        """Test that index handles nodes without IDs gracefully."""
        node_id = NodeId(content_hash="a" * 64, hint="test", node_type="heading")
        heading_with_id = Heading(level=2, text="With ID", id=node_id)
        heading_without_id = Heading(level=2, text="Without ID")

        doc = Document([heading_with_id, heading_without_id])

        # Index should only contain node with ID
        assert len(doc._id_index) == 1
        assert node_id in doc._id_index

    def test_existing_document_api_remains_stable(self):
        """Test that existing Document API still works."""
        heading = Heading(level=2, text="Test")
        paragraph = Paragraph(content="Content")

        doc = Document([heading, paragraph])

        # Existing operations should still work
        assert len(doc.nodes) == 2
        filtered = doc.filter(lambda n: isinstance(n, Heading))
        assert len(filtered.nodes) == 1
        mapped = doc.map(lambda n: n)
        assert len(mapped.nodes) == 2
