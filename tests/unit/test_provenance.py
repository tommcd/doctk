"""
Unit tests for provenance tracking system.

Tests the Provenance and ProvenanceContext classes.
"""

from datetime import datetime

import pytest

from doctk.identity import NodeId, Provenance, ProvenanceContext


class TestProvenance:
    """Test Provenance class."""

    def test_provenance_is_frozen(self):
        """Test Provenance is immutable (frozen dataclass)."""
        prov = Provenance(
            origin_file="test.md",
            version="abc123",
            author="Test User",
            created_at=datetime.now(),
            modified_at=None,
            parent_id=None,
        )

        # Attempting to modify should raise an error
        with pytest.raises(AttributeError):
            prov.origin_file = "other.md"

    def test_provenance_with_modification(self):
        """Test with_modification() creates new instance with updated time."""
        original = Provenance(
            origin_file="test.md",
            version="abc123",
            author="Test User",
            created_at=datetime.now(),
            modified_at=None,
            parent_id=None,
        )

        modified = original.with_modification(author="New Author")

        # Original unchanged
        assert original.modified_at is None
        assert original.author == "Test User"

        # Modified has new values
        assert modified.modified_at is not None
        assert modified.author == "New Author"
        assert modified.origin_file == original.origin_file
        assert modified.created_at == original.created_at

    def test_provenance_with_modification_preserves_author(self):
        """Test with_modification() preserves author if not specified."""
        original = Provenance(
            origin_file="test.md",
            version="abc123",
            author="Test User",
            created_at=datetime.now(),
            modified_at=None,
            parent_id=None,
        )

        modified = original.with_modification()

        assert modified.author == "Test User"
        assert modified.modified_at is not None

    def test_provenance_from_context(self):
        """Test creating Provenance from ProvenanceContext."""
        context = ProvenanceContext(file_path="test.md", version="abc123", author="Test User")

        prov = Provenance.from_context(context)

        assert prov.origin_file == "test.md"
        assert prov.version == "abc123"
        assert prov.author == "Test User"
        assert prov.created_at is not None
        assert prov.modified_at is None
        assert prov.parent_id is None

    def test_provenance_with_parent_id(self):
        """Test Provenance can track parent node ID."""
        parent_id = NodeId(content_hash="a" * 64, hint="parent", node_type="heading")

        prov = Provenance(
            origin_file="test.md",
            version="abc123",
            author="Test User",
            created_at=datetime.now(),
            modified_at=None,
            parent_id=parent_id,
        )

        assert prov.parent_id == parent_id


class TestProvenanceContext:
    """Test ProvenanceContext class."""

    def test_provenance_context_from_file(self):
        """Test creating context for file parsing."""
        context = ProvenanceContext.from_file("test.md")

        assert context.file_path == "test.md"
        # version and author may be None if not in git repo
        assert context.version is None or isinstance(context.version, str)
        assert context.author is None or isinstance(context.author, str)

    def test_provenance_context_from_repl(self):
        """Test creating context for REPL input."""
        context = ProvenanceContext.from_repl()

        assert context.file_path is None
        assert context.version is None
        # author should be from environment
        assert context.author is None or isinstance(context.author, str)

    def test_provenance_context_manual_creation(self):
        """Test manually creating ProvenanceContext."""
        context = ProvenanceContext(file_path="manual.md", version="v1.0.0", author="Manual User")

        assert context.file_path == "manual.md"
        assert context.version == "v1.0.0"
        assert context.author == "Manual User"
