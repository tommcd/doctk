"""Stable content-derived node addressing for structure operations.

The tree builder emits stable NodeId strings ("heading:hint:hash16");
operations resolve them alongside legacy positional ids ("h2-0"). The key
property: a stable id keeps addressing the same heading across
level-changing operations and re-parsing, which positional ids never did.
"""

from doctk import Document
from doctk.integration.operations import DocumentTreeBuilder, StructureOperations

SAMPLE = """# Guide

## Setup

Install the things.

## Usage

Run the things.

### Details

More.
"""


def _tree_ids(document: Document) -> dict[str, str]:
    """Map heading label -> emitted tree id."""
    root = DocumentTreeBuilder(document).build_tree_with_ids()
    result: dict[str, str] = {}

    def walk(node):
        for child in node.children:
            result[child.label] = child.id
            walk(child)

    walk(root)
    return result


class TestStableIdEmission:
    def test_tree_emits_stable_ids(self):
        ids = _tree_ids(Document.from_string(SAMPLE))
        assert ids["Setup"].startswith("heading:setup:")
        assert ids["Usage"].startswith("heading:usage:")
        # type:hint:hash16 - hash segment is 16 hex chars
        assert len(ids["Setup"].rsplit(":", 1)[1]) == 16

    def test_duplicate_headings_get_occurrence_suffix(self):
        doc = Document.from_string("## Overview\n\nA.\n\n## Overview\n\nB.\n")
        root = DocumentTreeBuilder(doc).build_tree_with_ids()
        first, second = (child.id for child in root.children)
        assert not first.endswith("#2")
        assert second == f"{first}#2"


class TestStableIdResolution:
    def test_operations_accept_stable_ids(self):
        doc = Document.from_string(SAMPLE)
        ids = _tree_ids(doc)
        result = StructureOperations.demote(doc, ids["Setup"])
        assert result.success
        assert "### Setup" in result.document

    def test_operations_still_accept_positional_ids(self):
        doc = Document.from_string(SAMPLE)
        result = StructureOperations.demote(doc, "h2-0")
        assert result.success
        assert "### Setup" in result.document

    def test_occurrence_suffix_addresses_the_right_duplicate(self):
        source = "## Overview\n\nA.\n\n## Overview\n\nB.\n"
        doc = Document.from_string(source)
        root = DocumentTreeBuilder(doc).build_tree_with_ids()
        second_id = root.children[1].id

        result = StructureOperations.demote(doc, second_id)
        assert result.success
        # Only the second Overview demoted
        assert result.document == "## Overview\n\nA.\n\n### Overview\n\nB.\n"

    def test_hash_one_suffix_is_alias_for_first_occurrence(self):
        source = "## Overview\n\nA.\n\n## Overview\n\nB.\n"
        doc = Document.from_string(source)
        root = DocumentTreeBuilder(doc).build_tree_with_ids()
        first_id = root.children[0].id

        result = StructureOperations.demote(doc, f"{first_id}#1")
        assert result.success
        assert result.document == "### Overview\n\nA.\n\n## Overview\n\nB.\n"


class TestStabilityAcrossEdits:
    """The property positional ids never had."""

    def test_id_survives_demote_and_reparse(self):
        doc = Document.from_string(SAMPLE)
        setup_id = _tree_ids(doc)["Setup"]

        demoted = StructureOperations.demote(doc, setup_id)
        assert demoted.success

        # Re-parse (as the DSL executor and bridge do) and address again:
        # level is excluded from canonical form, so the id is unchanged
        reparsed = Document.from_string(demoted.document)
        assert _tree_ids(reparsed)["Setup"] == setup_id

        # And the id still resolves for a follow-up operation
        promoted = StructureOperations.promote(reparsed, setup_id)
        assert promoted.success
        assert promoted.document == SAMPLE

    def test_id_survives_sibling_moves(self):
        doc = Document.from_string(SAMPLE)
        usage_id = _tree_ids(doc)["Usage"]

        moved = StructureOperations.move_up(doc, usage_id)
        assert moved.success

        reparsed = Document.from_string(moved.document)
        assert _tree_ids(reparsed)["Usage"] == usage_id

    def test_positional_id_would_have_drifted(self):
        # Documents the contrast: after moving Usage up, h2-0 now addresses
        # Usage (was Setup) - exactly the drift stable ids eliminate
        doc = Document.from_string(SAMPLE)
        moved = StructureOperations.move_up(doc, "h2-1")
        assert moved.success
        reparsed = Document.from_string(moved.document)
        builder = DocumentTreeBuilder(reparsed)
        assert builder.find_node("h2-0").text == "Usage"
