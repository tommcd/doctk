"""
Tests for text edit ID semantics.

Verifies that:
- Text edits generate new NodeIds (canonical content changes)
- Structural changes preserve NodeIds (non-canonical changes)
- Metadata changes preserve NodeIds
"""

from doctk.core import CodeBlock, Heading, ListItem, Paragraph
from doctk.identity import NodeId


class TestHeadingTextEditSemantics:
    """Test Heading text edit ID semantics."""

    def test_text_edit_changes_id(self):
        """Verify text edits generate new IDs."""
        heading = Heading(level=2, text="Original")
        heading.id = NodeId.from_node(heading)
        original_id = heading.id

        edited = heading.with_text("Modified")

        assert edited.id != original_id
        assert edited.text == "Modified"
        assert edited.level == heading.level

    def test_structural_change_preserves_id(self):
        """Verify structural changes preserve IDs."""
        heading = Heading(level=2, text="Test")
        heading.id = NodeId.from_node(heading)
        original_id = heading.id

        promoted = heading.promote()

        assert promoted.id == original_id
        assert promoted.level == 1
        assert promoted.text == heading.text

    def test_demote_preserves_id(self):
        """Verify demote preserves IDs."""
        heading = Heading(level=2, text="Test")
        heading.id = NodeId.from_node(heading)
        original_id = heading.id

        demoted = heading.demote()

        assert demoted.id == original_id
        assert demoted.level == 3
        assert demoted.text == heading.text

    def test_metadata_change_preserves_id(self):
        """Verify metadata changes preserve IDs."""
        heading = Heading(level=2, text="Test")
        heading.id = NodeId.from_node(heading)
        original_id = heading.id

        tagged = heading.with_metadata({"tags": ["important"]})

        assert tagged.id == original_id
        assert tagged.metadata["tags"] == ["important"]

    def test_metadata_deep_copied(self):
        """Verify metadata is deep copied."""
        heading = Heading(level=2, text="Test", metadata={"tags": ["original"]})
        heading.id = NodeId.from_node(heading)

        tagged = heading.with_metadata({"tags": ["modified"]})

        # Original should be unchanged
        assert heading.metadata["tags"] == ["original"]
        assert tagged.metadata["tags"] == ["modified"]


class TestParagraphTextEditSemantics:
    """Test Paragraph text edit ID semantics."""

    def test_content_edit_changes_id(self):
        """Verify content edits generate new IDs."""
        paragraph = Paragraph(content="Original content")
        paragraph.id = NodeId.from_node(paragraph)
        original_id = paragraph.id

        edited = paragraph.with_content("Modified content")

        assert edited.id != original_id
        assert edited.content == "Modified content"

    def test_metadata_change_preserves_id(self):
        """Verify metadata changes preserve IDs."""
        paragraph = Paragraph(content="Test")
        paragraph.id = NodeId.from_node(paragraph)
        original_id = paragraph.id

        tagged = paragraph.with_metadata({"tags": ["important"]})

        assert tagged.id == original_id
        assert tagged.metadata["tags"] == ["important"]


class TestCodeBlockTextEditSemantics:
    """Test CodeBlock text edit ID semantics."""

    def test_code_edit_changes_id(self):
        """Verify code edits generate new IDs."""
        code_block = CodeBlock(language="python", code="print('hello')")
        code_block.id = NodeId.from_node(code_block)
        original_id = code_block.id

        edited = code_block.with_code("print('world')")

        assert edited.id != original_id
        assert edited.code == "print('world')"
        assert edited.language == code_block.language

    def test_language_edit_changes_id(self):
        """Verify language edits generate new IDs."""
        from doctk.identity import clear_node_id_cache

        # Clear cache to ensure fresh IDs
        clear_node_id_cache()

        code_block = CodeBlock(language="python", code="print('hello')")
        code_block.id = NodeId.from_node(code_block)
        original_id = code_block.id

        edited = code_block.with_language("javascript")

        assert edited.id != original_id, (
            f"Expected different IDs but got: original={original_id}, edited={edited.id}"
        )
        assert edited.language == "javascript"
        assert edited.code == code_block.code

    def test_metadata_change_preserves_id(self):
        """Verify metadata changes preserve IDs."""
        code_block = CodeBlock(language="python", code="print('hello')")
        code_block.id = NodeId.from_node(code_block)
        original_id = code_block.id

        tagged = code_block.with_metadata({"tags": ["example"]})

        assert tagged.id == original_id
        assert tagged.metadata["tags"] == ["example"]


class TestListItemTextEditSemantics:
    """Test ListItem text edit ID semantics."""

    def test_content_edit_changes_id(self):
        """Verify content edits generate new IDs."""
        from doctk.core import Paragraph

        original_content = [Paragraph(content="Original")]
        list_item = ListItem(content=original_content)
        list_item.id = NodeId.from_node(list_item)
        original_id = list_item.id

        new_content = [Paragraph(content="Modified")]
        edited = list_item.with_content(new_content)

        assert edited.id != original_id
        assert len(edited.content) == 1
        assert edited.content[0].content == "Modified"

    def test_metadata_change_preserves_id(self):
        """Verify metadata changes preserve IDs."""
        from doctk.core import Paragraph

        list_item = ListItem(content=[Paragraph(content="Test")])
        list_item.id = NodeId.from_node(list_item)
        original_id = list_item.id

        tagged = list_item.with_metadata({"tags": ["item"]})

        assert tagged.id == original_id
        assert tagged.metadata["tags"] == ["item"]


class TestProvenanceUpdates:
    """Test that provenance is updated appropriately."""

    def test_text_edit_updates_provenance(self):
        """Verify text edits update provenance."""
        from doctk.identity import Provenance, ProvenanceContext

        context = ProvenanceContext.from_repl()
        heading = Heading(level=2, text="Original")
        heading.provenance = Provenance.from_context(context)

        edited = heading.with_text("Modified")

        # Provenance should be updated (with_modification)
        assert edited.provenance is not None
        assert edited.provenance != heading.provenance

    def test_structural_change_updates_provenance(self):
        """Verify structural changes update provenance."""
        from doctk.identity import Provenance, ProvenanceContext

        context = ProvenanceContext.from_repl()
        heading = Heading(level=2, text="Test")
        heading.provenance = Provenance.from_context(context)

        promoted = heading.promote()

        # Provenance should be updated
        assert promoted.provenance is not None
        assert promoted.provenance != heading.provenance


class TestSourceSpanPreservation:
    """Test that source spans are preserved across transformations."""

    def test_text_edit_preserves_source_span(self):
        """Verify text edits preserve source spans."""
        from doctk.identity import SourceSpan

        heading = Heading(level=2, text="Original")
        heading.source_span = SourceSpan(start_line=0, start_column=0, end_line=0, end_column=10)

        edited = heading.with_text("Modified")

        assert edited.source_span == heading.source_span

    def test_structural_change_preserves_source_span(self):
        """Verify structural changes preserve source spans."""
        from doctk.identity import SourceSpan

        heading = Heading(level=2, text="Test")
        heading.source_span = SourceSpan(start_line=0, start_column=0, end_line=0, end_column=10)

        promoted = heading.promote()

        assert promoted.source_span == heading.source_span
