"""
Core identity system for stable node identification.

Provides stable, durable node identifiers that persist across edits and re-parsing.
"""

from dataclasses import dataclass


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
