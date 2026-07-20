"""
Round-trip fidelity tests: parse -> write must be source-faithful.

This is the permanent quality gate defined in docs/design/07-revival-plan.md:
- Parsing a document and writing it back unchanged is byte-identical.
- Constructs the parser does not model (HTML blocks, thematic breaks,
  reference definitions, tables) are preserved verbatim via RawBlock.
- An edit to one node changes only that node's lines in the output.
"""

import difflib
from pathlib import Path

import pytest

from doctk import Document
from doctk.core import Heading, Paragraph, RawBlock

REPO_ROOT = Path(__file__).parents[2]

CORPUS_FILES = [
    "README.md",
    "CLAUDE.md",
    "AGENTS.md",
    "docs/development/testing.md",
    "docs/development/quality.md",
]


def _diff_lines(original: str, result: str) -> list[str]:
    """Return changed lines (additions/deletions only) between two texts."""
    return [
        line
        for line in difflib.unified_diff(original.splitlines(), result.splitlines(), lineterm="")
        if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
    ]


class TestByteIdenticalRoundTrip:
    """write(parse(x)) == x for unmodified documents."""

    @pytest.mark.parametrize("relative_path", CORPUS_FILES)
    def test_corpus_file_roundtrips_byte_identical(self, relative_path: str) -> None:
        source = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        result = Document.from_string(source).to_string()
        assert result == source, (
            f"{relative_path} did not round-trip byte-identical:\n"
            + "\n".join(_diff_lines(source, result)[:20])
        )

    def test_no_trailing_newline_preserved(self) -> None:
        source = "# Title\n\nBody text without trailing newline"
        assert Document.from_string(source).to_string() == source

    def test_multiple_blank_lines_preserved(self) -> None:
        source = "# Title\n\n\n\nParagraph after extra blank lines.\n"
        assert Document.from_string(source).to_string() == source

    def test_setext_heading_preserved(self) -> None:
        source = "Title\n=====\n\nSubtitle\n--------\n\nBody.\n"
        assert Document.from_string(source).to_string() == source

    def test_list_numbering_style_preserved(self) -> None:
        source = "1. first\n1. second\n1. third\n"
        assert Document.from_string(source).to_string() == source

    def test_bullet_char_and_hard_break_preserved(self) -> None:
        source = "* star bullet\n* another\n\nline one  \nline two\n"
        assert Document.from_string(source).to_string() == source


class TestNoContentLoss:
    """Constructs the parser does not model must survive round-trip."""

    def test_thematic_break_preserved(self) -> None:
        source = "before\n\n---\n\nafter\n"
        doc = Document.from_string(source)
        assert doc.to_string() == source
        assert any(isinstance(node, RawBlock) for node in doc.nodes)

    def test_html_block_preserved(self) -> None:
        source = '# Title\n\n<div class="note">\n  <p>html content</p>\n</div>\n\nAfter.\n'
        doc = Document.from_string(source)
        assert doc.to_string() == source
        raw_blocks = [node for node in doc.nodes if isinstance(node, RawBlock)]
        assert raw_blocks and "html content" in raw_blocks[0].content

    def test_reference_definition_preserved(self) -> None:
        # Link reference definitions produce no tokens in markdown-it;
        # they must be captured as untokenized gap content.
        source = "See [the docs][ref].\n\n[ref]: https://example.com\n\nMore text.\n"
        doc = Document.from_string(source)
        assert doc.to_string() == source
        assert any(
            isinstance(node, RawBlock) and "example.com" in node.content for node in doc.nodes
        )

    def test_trailing_reference_definition_preserved(self) -> None:
        source = "See [the docs][ref].\n\n[ref]: https://example.com\n"
        assert Document.from_string(source).to_string() == source

    def test_leading_comment_preserved(self) -> None:
        source = "<!-- editor: do not reformat -->\n\n# Title\n\nBody.\n"
        assert Document.from_string(source).to_string() == source

    def test_table_preserved(self) -> None:
        source = "| Col A | Col B |\n|-------|-------|\n| 1     | 2     |\n"
        assert Document.from_string(source).to_string() == source

    def test_front_matter_preserved(self) -> None:
        source = "---\ntitle: My Doc\ntags: [a, b]\n---\n\n# Title\n\nBody.\n"
        assert Document.from_string(source).to_string() == source

    def test_raw_block_survives_re_render(self) -> None:
        # Even when verbatim source text is unavailable (programmatic nodes),
        # RawBlock content must still be written out.
        raw = RawBlock(content="<div>kept</div>", token_type="html_block")
        doc = Document([Heading(level=1, text="T"), raw])
        assert "<div>kept</div>" in doc.to_string()


class TestEditLocality:
    """Editing one node must not disturb the rest of the document."""

    def test_single_demote_changes_single_line(self) -> None:
        source = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        doc = Document.from_string(source)
        edited = doc.map(
            lambda node: (
                node.demote() if isinstance(node, Heading) and node.text == "Philosophy" else node
            )
        )
        changed = _diff_lines(source, edited.to_string())
        assert changed == ["-## Philosophy", "+### Philosophy"]

    def test_promote_at_level_one_is_identity(self) -> None:
        source = "# Top\n\nBody.\n"
        doc = Document.from_string(source)
        edited = doc.map(lambda node: node.promote() if isinstance(node, Heading) else node)
        assert edited.to_string() == source

    def test_edited_paragraph_rerendered_others_verbatim(self) -> None:
        source = "# Title\n\nfirst  paragraph\n\n1. a\n1. b\n"
        doc = Document.from_string(source)
        edited = doc.map(
            lambda node: node.with_content("replaced") if isinstance(node, Paragraph) else node
        )
        result = edited.to_string()
        assert "replaced" in result
        # Untouched list keeps its original (non-renumbered) form
        assert "1. a\n1. b" in result

    def test_metadata_change_keeps_verbatim_output(self) -> None:
        source = "Text with  odd   spacing preserved.\n"
        doc = Document.from_string(source)
        edited = doc.map(lambda node: node.with_metadata({"reviewed": True}))
        assert edited.to_string() == source


class TestIdempotence:
    """Writing is stable: parse(write(parse(x))) writes identically."""

    @pytest.mark.parametrize("relative_path", CORPUS_FILES)
    def test_write_is_idempotent(self, relative_path: str) -> None:
        source = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        once = Document.from_string(source).to_string()
        twice = Document.from_string(once).to_string()
        assert once == twice

    def test_rendered_output_is_stable(self) -> None:
        # Programmatic document: rendered once, re-parsed, rendered again
        doc = Document(
            [
                Heading(level=2, text="Section"),
                Paragraph(content="Some text."),
            ]
        )
        once = doc.to_string()
        twice = Document.from_string(once).to_string()
        assert once == twice


class TestRawBlockNode:
    """RawBlock behaves like every other node."""

    def test_to_dict(self) -> None:
        raw = RawBlock(content="---", token_type="hr")
        assert raw.to_dict() == {
            "type": "raw_block",
            "content": "---",
            "token_type": "hr",
            "metadata": {},
        }

    def test_node_id_generation_is_stable(self) -> None:
        from doctk.identity import NodeId

        first = NodeId.from_node(RawBlock(content="<hr>", token_type="html_block"))
        second = NodeId.from_node(RawBlock(content="<hr>", token_type="html_block"))
        assert first == second

    def test_with_content_regenerates_id(self) -> None:
        from doctk.identity import NodeId

        raw = RawBlock(content="---", token_type="hr")
        raw.id = NodeId.from_node(raw)
        updated = raw.with_content("***")
        assert updated.content == "***"
        assert updated.id != raw.id

    def test_with_metadata_preserves_id_and_source_text(self) -> None:
        from doctk.identity import NodeId

        raw = RawBlock(content="---", token_type="hr", source_text="---")
        raw.id = NodeId.from_node(raw)
        updated = raw.with_metadata({"note": "keep"})
        assert updated.id == raw.id
        assert updated.source_text == "---"

    def test_outliner_handles_raw_block(self) -> None:
        from io import StringIO

        from rich.console import Console

        from doctk.outliner import outline

        doc = Document.from_string("before\n\n---\n\nafter\n")
        buffer = StringIO()
        outline(doc, show_content=True, console=Console(file=buffer))
        assert "Raw block" in buffer.getvalue()


class TestSourceTextInvalidation:
    """source_text must be dropped exactly when content changes."""

    def test_demote_drops_source_text(self) -> None:
        doc = Document.from_string("## Heading\n")
        heading = doc.nodes[0]
        assert heading.source_text is not None
        assert heading.demote().source_text is None

    def test_noop_update_keeps_source_text(self) -> None:
        doc = Document.from_string("# Heading\n")
        heading = doc.nodes[0]
        assert heading.promote().source_text == heading.source_text

    def test_with_content_drops_source_text(self) -> None:
        doc = Document.from_string("some paragraph\n")
        paragraph = doc.nodes[0]
        assert paragraph.source_text is not None
        assert paragraph.with_content("new").source_text is None
