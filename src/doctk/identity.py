"""
Core identity system for stable node identification.

Provides stable, durable node identifiers that persist across edits and re-parsing.
"""

import hashlib
import os
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from doctk.core import Node


@dataclass(frozen=True)
class NodeId:
    """
    Stable, durable node identifier.

    Combines content-based stability with human-readable hints.
    Immutable to prevent accidental modification.

    Attributes:
        content_hash: Full SHA-256 hex digest (64 characters) of canonical node content.
                     Ensures content-addressable stability.
        hint: Human-readable hint (e.g., "introduction", "api-reference").
             Maximum 32 characters, slugified for readability.
        node_type: Node type identifier (e.g., "heading", "paragraph", "codeblock").
                  Lowercase string matching the node class name.

    Examples:
        >>> node_id = NodeId(
        ...     content_hash="a3f5b9c2d1e4f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1",
        ...     hint="introduction",
        ...     node_type="heading"
        ... )
        >>> node_id.content_hash
        'a3f5b9c2d1e4f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1'
        >>> node_id.hint
        'introduction'
        >>> node_id.node_type
        'heading'
        >>> str(node_id)
        'heading:introduction:a3f5b9c2d1e4f6a7'
    """

    content_hash: str  # Full SHA-256 hex (64 chars) stored internally
    hint: str  # Human-readable hint (e.g., "introduction", "api-reference")
    node_type: str  # "heading", "paragraph", etc.

    def __str__(self) -> str:
        """Canonical string representation: type:hint:hash16

        Uses 16-character hash prefix for balance between uniqueness
        and readability. Collision probability: ~1 in 2^64 for typical
        document sizes (<10K nodes).

        Returns:
            String in format "node_type:hint:hash16" where hash16 is the
            first 16 characters of the content_hash.

        Examples:
            >>> node_id = NodeId(
            ...     content_hash="a3f5b9c2d1e4f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1",
            ...     hint="intro",
            ...     node_type="heading"
            ... )
            >>> str(node_id)
            'heading:intro:a3f5b9c2d1e4f6a7'
        """
        return f"{self.node_type}:{self.hint}:{self.content_hash[:16]}"

    def to_short_string(self) -> str:
        """Short display format: type:hint:hash8

        For UI display only. NOT suitable for persistence or lookup.

        Returns:
            String in format "node_type:hint:hash8" where hash8 is the
            first 8 characters of the content_hash.

        Examples:
            >>> node_id = NodeId(
            ...     content_hash="a3f5b9c2d1e4f6a7b8c9d0e1f2a3b4c5",
            ...     hint="intro",
            ...     node_type="heading"
            ... )
            >>> node_id.to_short_string()
            'heading:intro:a3f5b9c2'
        """
        return f"{self.node_type}:{self.hint}:{self.content_hash[:8]}"

    @staticmethod
    def from_string(s: str) -> "NodeId":
        """Parse from canonical string representation.

        Accepts format: "type:hint:hash16" (16-character hash prefix)

        Args:
            s: String in format "node_type:hint:hash16"

        Returns:
            NodeId instance with hash prefix stored

        Raises:
            ValueError: If format is invalid or hash length wrong

        Examples:
            >>> node_id = NodeId.from_string("heading:intro:a3f5b9c2d1e4f6a7")
            >>> node_id.node_type
            'heading'
            >>> node_id.hint
            'intro'
            >>> len(node_id.content_hash)
            16
        """
        parts = s.split(":")
        if len(parts) != 3:
            raise ValueError(f"Invalid NodeId format: {s}. Expected 'type:hint:hash16'")

        node_type, hint, hash_prefix = parts

        # Validate hash length (must be 16 chars for canonical format)
        if len(hash_prefix) != 16:
            raise ValueError(
                f"Invalid hash length: {len(hash_prefix)}. "
                f"Expected 16 characters. Use NodeId.from_string() "
                f"only with canonical format from __str__()"
            )

        # Store hash prefix (we don't have full hash from string)
        return NodeId(node_type=node_type, hint=hint, content_hash=hash_prefix)

    @staticmethod
    def from_node(node: "Node") -> "NodeId":
        """Generate stable ID from node content with caching.

        Args:
            node: Node instance to generate ID for

        Returns:
            NodeId with full 64-character hash

        Examples:
            >>> from doctk.core import Heading
            >>> heading = Heading(level=2, text="Introduction")
            >>> node_id = NodeId.from_node(heading)
            >>> len(node_id.content_hash)
            64
        """
        cache_key = _get_node_cache_key(node)
        if cache_key in _node_id_cache:
            return _node_id_cache[cache_key]

        canonical = _canonicalize_node(node)
        # Generate FULL hash (64 chars)
        full_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        hint = _generate_hint(node)

        node_id = NodeId(
            content_hash=full_hash,  # Store full hash
            hint=hint,
            node_type=type(node).__name__.lower(),
        )

        _node_id_cache[cache_key] = node_id
        return node_id

    def __eq__(self, other: object) -> bool:
        """Equality based on first 16 characters of hash.

        This allows NodeIds created from strings (with 16-char hashes)
        to equal NodeIds created from nodes (with 64-char hashes).

        Args:
            other: Object to compare with

        Returns:
            True if node_type, hint, and first 16 chars of hash match
        """
        if not isinstance(other, NodeId):
            return False
        return (
            self.node_type == other.node_type
            and self.hint == other.hint
            and self.content_hash[:16] == other.content_hash[:16]
        )

    def __hash__(self) -> int:
        """Hash based on first 16 characters for consistency with __eq__."""
        return hash((self.node_type, self.hint, self.content_hash[:16]))


# Module-level cache for NodeId generation
# NOTE: This is an IN-PROCESS, NON-PERSISTENT cache only.
# Cache keys use Python's hash() which is randomized per process.
# DO NOT persist or share this cache across processes.
_node_id_cache: dict[str, NodeId] = {}


def _get_node_cache_key(node: "Node") -> str:
    """
    Generate cache key for node (lightweight hash).

    Uses Python's built-in hash() which is process-specific and randomized.
    This is acceptable because the cache is strictly in-memory and per-process.
    Cache keys are NOT stable across runs and must never be persisted.

    Args:
        node: Node to generate cache key for

    Returns:
        Cache key string
    """
    # Import here to avoid circular dependency
    from doctk.core import BlockQuote, CodeBlock, Heading, List, ListItem, Paragraph

    if isinstance(node, Heading):
        return f"h:{node.level}:{hash(node.text)}"
    elif isinstance(node, Paragraph):
        return f"p:{hash(node.content[:100])}"
    elif isinstance(node, CodeBlock):
        return f"c:{hash(node.code[:100])}"
    elif isinstance(node, List):
        return f"l:{node.ordered}:{hash(str(node.items)[:100])}"
    elif isinstance(node, ListItem):
        return f"li:{hash(str(node.content)[:100])}"
    elif isinstance(node, BlockQuote):
        return f"bq:{hash(str(node.content)[:100])}"
    else:
        return f"{type(node).__name__.lower()}:{hash(str(node)[:100])}"


def clear_node_id_cache() -> None:
    """Clear NodeId cache (for testing or memory management)."""
    global _node_id_cache
    _node_id_cache.clear()


def _canonicalize_node(node: "Node") -> str:
    """Generate canonical string representation for hashing.

    Applies normalization rules:
    - Unicode NFC normalization
    - Whitespace: strip leading/trailing, collapse internal to single space
    - Tabs converted to 4 spaces
    - Line endings converted to LF

    Args:
        node: Node to canonicalize

    Returns:
        Canonical string representation
    """
    # Import here to avoid circular dependency
    from doctk.core import BlockQuote, CodeBlock, Heading, List, ListItem, Paragraph

    def normalize_text(text: str) -> str:
        """Apply normalization rules."""
        # NFC normalization
        text = unicodedata.normalize("NFC", text)
        # Strip and collapse whitespace
        text = " ".join(text.split())
        # Convert tabs to spaces
        text = text.replace("\t", "    ")
        return text

    if isinstance(node, Heading):
        # IMPORTANT: Exclude level so promote/demote preserve ID
        return f"heading:{normalize_text(node.text)}"

    elif isinstance(node, Paragraph):
        return f"paragraph:{normalize_text(node.content)}"

    elif isinstance(node, CodeBlock):
        # Preserve whitespace in code
        return f"codeblock:{node.language or 'none'}:{node.code}"

    elif isinstance(node, ListItem):
        # ListItem.content is list[Node], need to serialize it
        content_str = "|".join(_canonicalize_node(n) for n in node.content)
        return f"listitem:{content_str}"

    elif isinstance(node, List):
        items_canonical = "|".join(_canonicalize_node(item) for item in node.items)
        list_type = "ordered" if node.ordered else "unordered"
        return f"list:{list_type}:{items_canonical}"

    elif isinstance(node, BlockQuote):
        # BlockQuote.content is list[Node], need to serialize it
        content_str = "|".join(_canonicalize_node(n) for n in node.content)
        return f"blockquote:{content_str}"

    else:
        # Fallback for unknown types
        return f"{type(node).__name__.lower()}:{str(node)}"


def _generate_hint(node: "Node") -> str:
    """
    Generate human-readable hint for NodeId.

    Rules:
    - Deterministic: Same node content → same hint
    - Lowercase: All hints are lowercase for consistency
    - Slugified: Spaces → hyphens, special chars removed
    - Truncated: Maximum 32 characters
    - Fallback: Node type for non-text nodes

    Args:
        node: Node to generate hint for

    Returns:
        Human-readable hint string (max 32 chars)

    Examples:
        Heading("Introduction") → "introduction"
        Heading("API Reference Guide") → "api-reference-guide"
        Heading("Getting Started!") → "getting-started"
        Heading("Very Long Heading That Exceeds Limit") → "very-long-heading-that-exceeds"
        Paragraph("Some text") → "some-text"
        CodeBlock(...) → "codeblock"

    Collision Handling:
        Hints are for human readability only. The content_hash ensures
        uniqueness. Two headings with identical text will have the same
        hint but different hashes (if any other content differs).
    """
    # Import here to avoid circular dependency
    from doctk.core import CodeBlock, Heading, Paragraph

    # Get text content based on node type
    if isinstance(node, Heading):
        text = node.text
    elif isinstance(node, Paragraph):
        # Use first 50 chars of paragraph for hint
        text = node.content[:50]
    elif isinstance(node, CodeBlock):
        # Use language as hint if available
        return node.language.lower() if node.language else "codeblock"
    else:
        # Fallback to node type
        return type(node).__name__.lower()

    # Normalize Unicode
    text = unicodedata.normalize("NFC", text)

    # Convert to lowercase
    text = text.lower()

    # Remove non-alphanumeric except spaces and hyphens
    text = re.sub(r"[^a-z0-9\s-]", "", text)

    # Collapse whitespace and convert to hyphens
    text = re.sub(r"\s+", "-", text.strip())

    # Remove consecutive hyphens
    text = re.sub(r"-+", "-", text)

    # Truncate to 32 characters
    text = text[:32].rstrip("-")

    # Ensure non-empty
    if not text:
        return type(node).__name__.lower()

    return text


@dataclass(frozen=True)
class SourceSpan:
    """
    Precise source location for AST nodes.
    Enables accurate error reporting and round-trip mapping.

    Attributes:
        start_line: 0-indexed line number where node starts
        start_column: 0-indexed column number where node starts
        end_line: 0-indexed line number where node ends
        end_column: 0-indexed column number where node ends
    """

    start_line: int  # 0-indexed line number
    start_column: int  # 0-indexed column number
    end_line: int  # 0-indexed line number
    end_column: int  # 0-indexed column number

    def contains(self, line: int, column: int) -> bool:
        """Check if position is within this span.

        Args:
            line: 0-indexed line number
            column: 0-indexed column number

        Returns:
            True if position is within span
        """
        if line < self.start_line or line > self.end_line:
            return False
        if line == self.start_line and column < self.start_column:
            return False
        if line == self.end_line and column > self.end_column:
            return False
        return True

    def overlaps(self, other: "SourceSpan") -> bool:
        """Check if this span overlaps with another.

        Args:
            other: Another SourceSpan to check overlap with

        Returns:
            True if spans overlap
        """
        return not (self.end_line < other.start_line or other.end_line < self.start_line)


@dataclass(frozen=True)
class Provenance:
    """
    Tracks origin and history of a node.
    Immutable to ensure audit trail integrity.

    Attributes:
        origin_file: Source file path (None for REPL/stdin)
        version: Git commit hash, version tag, or timestamp
        author: Creator/last modifier
        created_at: Creation timestamp
        modified_at: Last modification timestamp (None if never modified)
        parent_id: Parent node ID for fragments (None for root nodes)
    """

    origin_file: str | None  # Source file path
    version: str | None  # Git commit hash, version tag, or timestamp
    author: str | None  # Creator/last modifier
    created_at: datetime  # Creation timestamp
    modified_at: datetime | None  # Last modification timestamp
    parent_id: NodeId | None  # Parent node ID (for fragments)

    def with_modification(self, author: str | None = None) -> "Provenance":
        """Create new provenance with updated modification time.

        Args:
            author: New author (defaults to current author)

        Returns:
            New Provenance instance with updated modified_at
        """
        return Provenance(
            origin_file=self.origin_file,
            version=self.version,
            author=author or self.author,
            created_at=self.created_at,
            modified_at=datetime.now(),
            parent_id=self.parent_id,
        )

    @staticmethod
    def from_context(context: "ProvenanceContext") -> "Provenance":
        """Create provenance from execution context.

        Args:
            context: ProvenanceContext with file/version/author info

        Returns:
            New Provenance instance
        """
        return Provenance(
            origin_file=context.file_path,
            version=context.version,
            author=context.author,
            created_at=datetime.now(),
            modified_at=None,
            parent_id=None,
        )


@dataclass
class ProvenanceContext:
    """
    Context for provenance generation.
    Populated by parser/REPL/CLI based on source.

    Attributes:
        file_path: File being parsed (None for REPL/stdin)
        version: Git commit or version tag
        author: From git config or environment
    """

    file_path: str | None = None  # File being parsed (None for REPL/stdin)
    version: str | None = None  # Git commit or version tag
    author: str | None = None  # From git config or environment

    @staticmethod
    def from_file(path: str) -> "ProvenanceContext":
        """Create context for file parsing.

        Args:
            path: Path to file being parsed

        Returns:
            ProvenanceContext with file path and git info
        """
        return ProvenanceContext(
            file_path=path,
            version=_get_git_commit(),  # Try to get git commit
            author=_get_git_author(),  # Try to get git user
        )

    @staticmethod
    def from_repl() -> "ProvenanceContext":
        """Create context for REPL input.

        Returns:
            ProvenanceContext with user from environment
        """
        return ProvenanceContext(
            file_path=None,
            version=None,
            author=os.environ.get("USER") or os.environ.get("USERNAME"),
        )


def _get_git_commit() -> str | None:
    """Try to get current git commit hash.

    Returns:
        Git commit hash or None if not in git repo
    """
    try:
        import subprocess

        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=1,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return None


def _get_git_author() -> str | None:
    """Try to get git user name.

    Returns:
        Git user name or None if not configured
    """
    try:
        import subprocess

        result = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True,
            text=True,
            check=True,
            timeout=1,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return None
