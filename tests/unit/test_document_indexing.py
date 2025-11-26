"""
Tests for Document ID indexing with nested nodes.

Validates that find_node() works correctly for all nodes in the tree,
including nested ListItems, BlockQuotes, and Heading children.
"""

from doctk.core import BlockQuote, Document, Heading, List, ListItem, Paragraph
from doctk.identity import NodeId


class TestDocumentIndexing:
    """Test Document._build_id_index() and find_node() with nested structures."""

    def test_find_top_level_node(self):
        """Test finding a top-level node."""
        heading = Heading(level=1, text="Title")
        heading.id = NodeId.from_node(heading)

        doc = Document([heading])

        found = doc.find_node(heading.id)
        assert found == heading

    def test_find_nested_list_item(self):
        """Test finding a ListItem nested within a List."""
        item1 = ListItem(content=[Paragraph(content="Item 1")])
        item1.id = NodeId.from_node(item1)

        item2 = ListItem(content=[Paragraph(content="Item 2")])
        item2.id = NodeId.from_node(item2)

        list_node = List(ordered=False, items=[item1, item2])
        list_node.id = NodeId.from_node(list_node)

        doc = Document([list_node])

        # Should find the list itself
        found_list = doc.find_node(list_node.id)
        assert found_list == list_node

        # Should find nested list items
        found_item1 = doc.find_node(item1.id)
        assert found_item1 == item1

        found_item2 = doc.find_node(item2.id)
        assert found_item2 == item2

    def test_find_paragraph_in_list_item(self):
        """Test finding a Paragraph nested within a ListItem."""
        para = Paragraph(content="Nested paragraph")
        para.id = NodeId.from_node(para)

        item = ListItem(content=[para])
        item.id = NodeId.from_node(item)

        list_node = List(ordered=True, items=[item])
        list_node.id = NodeId.from_node(list_node)

        doc = Document([list_node])

        # Should find the deeply nested paragraph
        found_para = doc.find_node(para.id)
        assert found_para == para

    def test_find_nested_blockquote_content(self):
        """Test finding nodes nested within a BlockQuote."""
        para1 = Paragraph(content="Quote line 1")
        para1.id = NodeId.from_node(para1)

        para2 = Paragraph(content="Quote line 2")
        para2.id = NodeId.from_node(para2)

        blockquote = BlockQuote(content=[para1, para2])
        blockquote.id = NodeId.from_node(blockquote)

        doc = Document([blockquote])

        # Should find the blockquote itself
        found_bq = doc.find_node(blockquote.id)
        assert found_bq == blockquote

        # Should find nested paragraphs
        found_para1 = doc.find_node(para1.id)
        assert found_para1 == para1

        found_para2 = doc.find_node(para2.id)
        assert found_para2 == para2

    def test_find_heading_children(self):
        """Test finding nodes nested as Heading children."""
        child_para = Paragraph(content="Under heading")
        child_para.id = NodeId.from_node(child_para)

        heading = Heading(level=2, text="Section", children=[child_para])
        heading.id = NodeId.from_node(heading)

        doc = Document([heading])

        # Should find the heading
        found_heading = doc.find_node(heading.id)
        assert found_heading == heading

        # Should find the child paragraph
        found_child = doc.find_node(child_para.id)
        assert found_child == child_para

    def test_find_deeply_nested_structure(self):
        """Test finding nodes in a deeply nested structure."""
        # Create: Heading > List > ListItem > BlockQuote > Paragraph
        deep_para = Paragraph(content="Deeply nested")
        deep_para.id = NodeId.from_node(deep_para)

        blockquote = BlockQuote(content=[deep_para])
        blockquote.id = NodeId.from_node(blockquote)

        list_item = ListItem(content=[blockquote])
        list_item.id = NodeId.from_node(list_item)

        list_node = List(ordered=False, items=[list_item])
        list_node.id = NodeId.from_node(list_node)

        heading = Heading(level=1, text="Top", children=[list_node])
        heading.id = NodeId.from_node(heading)

        doc = Document([heading])

        # Should find all nodes at all levels
        assert doc.find_node(heading.id) == heading
        assert doc.find_node(list_node.id) == list_node
        assert doc.find_node(list_item.id) == list_item
        assert doc.find_node(blockquote.id) == blockquote
        assert doc.find_node(deep_para.id) == deep_para

    def test_find_node_not_in_tree(self):
        """Test that find_node returns None for nodes not in the tree."""
        heading = Heading(level=1, text="In tree")
        heading.id = NodeId.from_node(heading)

        other_heading = Heading(level=1, text="Not in tree")
        other_heading.id = NodeId.from_node(other_heading)

        doc = Document([heading])

        # Should find the node in the tree
        assert doc.find_node(heading.id) == heading

        # Should not find the node not in the tree
        assert doc.find_node(other_heading.id) is None

    def test_find_node_without_id(self):
        """Test that nodes without IDs are not indexed."""
        # Create nodes without setting IDs
        para = Paragraph(content="No ID")
        heading = Heading(level=1, text="Also no ID", children=[para])

        doc = Document([heading])

        # Index should be empty since no nodes have IDs
        assert len(doc._id_index) == 0

    def test_index_rebuilds_on_document_creation(self):
        """Test that index is built when Document is created."""
        para1 = Paragraph(content="First")
        para1.id = NodeId.from_node(para1)

        para2 = Paragraph(content="Second")
        para2.id = NodeId.from_node(para2)

        doc = Document([para1, para2])

        # Index should contain both nodes
        assert len(doc._id_index) == 2
        assert doc.find_node(para1.id) == para1
        assert doc.find_node(para2.id) == para2

    def test_multiple_lists_with_items(self):
        """Test indexing multiple lists each with multiple items."""
        # First list with 2 items
        item1a = ListItem(content=[Paragraph(content="1a")])
        item1a.id = NodeId.from_node(item1a)

        item1b = ListItem(content=[Paragraph(content="1b")])
        item1b.id = NodeId.from_node(item1b)

        list1 = List(ordered=True, items=[item1a, item1b])
        list1.id = NodeId.from_node(list1)

        # Second list with 2 items
        item2a = ListItem(content=[Paragraph(content="2a")])
        item2a.id = NodeId.from_node(item2a)

        item2b = ListItem(content=[Paragraph(content="2b")])
        item2b.id = NodeId.from_node(item2b)

        list2 = List(ordered=False, items=[item2a, item2b])
        list2.id = NodeId.from_node(list2)

        doc = Document([list1, list2])

        # Should find all lists and all items
        assert doc.find_node(list1.id) == list1
        assert doc.find_node(list2.id) == list2
        assert doc.find_node(item1a.id) == item1a
        assert doc.find_node(item1b.id) == item1b
        assert doc.find_node(item2a.id) == item2a
        assert doc.find_node(item2b.id) == item2b
