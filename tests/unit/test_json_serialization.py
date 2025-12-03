"""Tests for Document JSON serialization."""

import json

import pytest

from doctk.core import BlockQuote, CodeBlock, Document, Heading, List, ListItem, Paragraph


class TestDocumentJsonSerialization:
    """Test Document.to_json() and Document.from_json() methods."""

    def test_empty_document_round_trip(self):
        """Empty document should serialize and deserialize correctly."""
        doc = Document([])
        json_str = doc.to_json()
        restored = Document.from_json(json_str)

        assert len(restored.nodes) == 0

    def test_simple_heading_round_trip(self):
        """Simple heading should serialize and deserialize correctly."""
        doc = Document([Heading(level=1, text="Hello World")])
        json_str = doc.to_json()
        restored = Document.from_json(json_str)

        assert len(restored.nodes) == 1
        assert isinstance(restored.nodes[0], Heading)
        assert restored.nodes[0].level == 1
        assert restored.nodes[0].text == "Hello World"

    def test_paragraph_round_trip(self):
        """Paragraph should serialize and deserialize correctly."""
        doc = Document([Paragraph(content="This is a paragraph.")])
        json_str = doc.to_json()
        restored = Document.from_json(json_str)

        assert len(restored.nodes) == 1
        assert isinstance(restored.nodes[0], Paragraph)
        assert restored.nodes[0].content == "This is a paragraph."

    def test_code_block_round_trip(self):
        """Code block should serialize and deserialize correctly."""
        doc = Document([CodeBlock(code="print('hello')", language="python")])
        json_str = doc.to_json()
        restored = Document.from_json(json_str)

        assert len(restored.nodes) == 1
        assert isinstance(restored.nodes[0], CodeBlock)
        assert restored.nodes[0].code == "print('hello')"
        assert restored.nodes[0].language == "python"

    def test_list_round_trip(self):
        """List with items should serialize and deserialize correctly."""
        doc = Document(
            [
                List(
                    ordered=False,
                    items=[
                        ListItem(content=[Paragraph(content="Item 1")]),
                        ListItem(content=[Paragraph(content="Item 2")]),
                    ],
                )
            ]
        )
        json_str = doc.to_json()
        restored = Document.from_json(json_str)

        assert len(restored.nodes) == 1
        assert isinstance(restored.nodes[0], List)
        assert restored.nodes[0].ordered is False
        assert len(restored.nodes[0].items) == 2
        assert isinstance(restored.nodes[0].items[0], ListItem)

    def test_block_quote_round_trip(self):
        """Block quote should serialize and deserialize correctly."""
        doc = Document([BlockQuote(content=[Paragraph(content="Quoted text")])])
        json_str = doc.to_json()
        restored = Document.from_json(json_str)

        assert len(restored.nodes) == 1
        assert isinstance(restored.nodes[0], BlockQuote)
        assert len(restored.nodes[0].content) == 1
        assert isinstance(restored.nodes[0].content[0], Paragraph)

    def test_nested_heading_round_trip(self):
        """Heading with children should serialize and deserialize correctly."""
        doc = Document(
            [
                Heading(
                    level=1,
                    text="Parent",
                    children=[
                        Paragraph(content="Child paragraph"),
                        Heading(level=2, text="Child heading"),
                    ],
                )
            ]
        )
        json_str = doc.to_json()
        restored = Document.from_json(json_str)

        assert len(restored.nodes) == 1
        heading = restored.nodes[0]
        assert isinstance(heading, Heading)
        assert heading.text == "Parent"
        assert len(heading.children) == 2
        assert isinstance(heading.children[0], Paragraph)
        assert isinstance(heading.children[1], Heading)

    def test_metadata_preserved(self):
        """Node metadata should be preserved in round trip."""
        doc = Document([Heading(level=1, text="Test", metadata={"custom": "value"})])
        json_str = doc.to_json()
        restored = Document.from_json(json_str)

        assert restored.nodes[0].metadata == {"custom": "value"}

    def test_complex_document_round_trip(self):
        """Complex document with multiple node types should round trip correctly."""
        doc = Document(
            [
                Heading(level=1, text="Title"),
                Paragraph(content="Introduction paragraph."),
                List(
                    ordered=True,
                    items=[
                        ListItem(content=[Paragraph(content="First item")]),
                        ListItem(content=[Paragraph(content="Second item")]),
                    ],
                ),
                CodeBlock(code="def hello():\n    pass", language="python"),
                BlockQuote(content=[Paragraph(content="A quote")]),
            ]
        )
        json_str = doc.to_json()
        restored = Document.from_json(json_str)

        assert len(restored.nodes) == 5
        assert isinstance(restored.nodes[0], Heading)
        assert isinstance(restored.nodes[1], Paragraph)
        assert isinstance(restored.nodes[2], List)
        assert isinstance(restored.nodes[3], CodeBlock)
        assert isinstance(restored.nodes[4], BlockQuote)

    def test_json_structure(self):
        """JSON output should have expected structure."""
        doc = Document([Heading(level=1, text="Test")])
        json_str = doc.to_json()
        data = json.loads(json_str)

        assert "version" in data
        assert data["version"] == "1.0"
        assert "nodes" in data
        assert isinstance(data["nodes"], list)
        assert len(data["nodes"]) == 1
        assert data["nodes"][0]["type"] == "heading"

    def test_from_json_invalid_json(self):
        """from_json should raise ValueError for invalid JSON."""
        with pytest.raises(ValueError, match="Invalid JSON"):
            Document.from_json("{invalid json")

    def test_from_json_not_object(self):
        """from_json should raise ValueError if JSON is not an object."""
        with pytest.raises(ValueError, match="JSON must be an object"):
            Document.from_json("[]")

    def test_from_json_missing_nodes(self):
        """from_json should raise ValueError if 'nodes' field is missing."""
        with pytest.raises(ValueError, match="must contain 'nodes' field"):
            Document.from_json('{"version": "1.0"}')

    def test_from_json_nodes_not_array(self):
        """from_json should raise ValueError if 'nodes' is not an array."""
        with pytest.raises(ValueError, match="'nodes' field must be an array"):
            Document.from_json('{"version": "1.0", "nodes": "not an array"}')

    def test_from_json_unknown_node_type(self):
        """from_json should raise ValueError for unknown node types."""
        json_str = '{"version": "1.0", "nodes": [{"type": "unknown"}]}'
        with pytest.raises(ValueError, match="Unknown node type"):
            Document.from_json(json_str)

    def test_from_json_node_missing_type(self):
        """from_json should raise ValueError if node is missing 'type' field."""
        json_str = '{"version": "1.0", "nodes": [{"text": "no type"}]}'
        with pytest.raises(ValueError, match="must have 'type' field"):
            Document.from_json(json_str)

    def test_markdown_to_json_round_trip(self):
        """Document parsed from markdown should round trip through JSON."""
        markdown = """# Title

This is a paragraph.

- Item 1
- Item 2

```python
print("hello")
```
"""
        doc = Document.from_string(markdown)
        json_str = doc.to_json()
        restored = Document.from_json(json_str)

        # Should have same number of nodes
        assert len(restored.nodes) == len(doc.nodes)

        # Should have same node types
        for original, restored_node in zip(doc.nodes, restored.nodes, strict=True):
            assert isinstance(restored_node, type(original))
