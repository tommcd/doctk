"""Hover Provider for doctk Language Server.

This module provides hover documentation for doctk DSL operations and parameters,
displaying operation descriptions, parameter information, usage examples, and type details.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass

from lsprotocol.types import (
    Hover,
    MarkupContent,
    MarkupKind,
    Position,
)

from doctk.lsp.registry import OperationMetadata, OperationRegistry, ParameterInfo

logger = logging.getLogger(__name__)


@dataclass
class HoverAnalysis:
    """Analysis of hover position."""

    line: int
    character: int
    word: str  # The word under cursor
    is_operation: bool
    is_parameter: bool
    operation_name: str | None = None  # If hovering over parameter, which operation
    parameter_name: str | None = None  # If hovering over parameter


@dataclass
class CachedHover:
    """Cached hover result with timestamp."""

    hover: Hover | None
    timestamp: float


class HoverProvider:
    """Provides hover documentation for doctk DSL operations and parameters."""

    def __init__(self, registry: OperationRegistry, cache_ttl: float = 5.0):
        """
        Initialize hover provider.

        Args:
            registry: Operation registry for available operations
            cache_ttl: Time-to-live for cached hover results in seconds (default: 5.0)
        """
        self.registry = registry
        self.cache: dict[str, CachedHover] = {}
        self.cache_ttl = cache_ttl
        self._cleanup_counter = 0
        self._cleanup_interval = 100  # Cleanup every 100 operations

    def provide_hover(self, document: str, position: Position) -> Hover | None:
        """
        Provide hover information at the given position.

        Args:
            document: Full document text
            position: Cursor position (line and character)

        Returns:
            Hover information or None if nothing to show
        """
        # Analyze position to identify what's under cursor
        analysis = self._analyze_position(document, position)

        # Check cache using a sentinel to distinguish cache hit from cached None
        cache_key = self._compute_cache_key(analysis)
        cache_miss = object()  # Unique sentinel value
        cached = self._get_cached_hover(cache_key, default=cache_miss)
        if cached is not cache_miss:
            logger.debug(f"Cache hit for hover at {position}")
            return cached

        # Return None if no identifiable word (but cache the result)
        if not analysis.word:
            self._cache_hover(cache_key, None)
            return None

        # Generate hover based on what's under cursor
        hover = None
        if analysis.is_operation and analysis.word:
            hover = self._create_operation_hover(analysis.word)
        elif analysis.is_parameter and analysis.parameter_name and analysis.operation_name:
            hover = self._create_parameter_hover(analysis.operation_name, analysis.parameter_name)

        # Cache the result (even if None)
        self._cache_hover(cache_key, hover)

        # Periodic automatic cache cleanup to prevent unbounded growth
        self._cleanup_counter += 1
        if self._cleanup_counter >= self._cleanup_interval:
            self.cleanup_expired_cache()
            self._cleanup_counter = 0

        return hover

    def _analyze_position(self, document: str, position: Position) -> HoverAnalysis:
        """
        Analyze cursor position to identify word and context.

        Args:
            document: Full document text
            position: Cursor position

        Returns:
            Hover analysis result
        """
        lines = document.split("\n")

        # Get current line
        if position.line >= len(lines):
            return HoverAnalysis(
                line=position.line,
                character=position.character,
                word="",
                is_operation=False,
                is_parameter=False,
            )

        line_text = lines[position.line]

        # Find the word under cursor
        # Word boundaries: whitespace, |, (, ), =
        word_pattern = r"[a-zA-Z_][a-zA-Z0-9_]*"

        # Find all words in the line
        matches = list(re.finditer(word_pattern, line_text))

        # Find which word the cursor is on
        current_word = ""
        current_word_match = None
        for match in matches:
            if match.start() <= position.character <= match.end():
                current_word = match.group()
                current_word_match = match
                break

        if not current_word:
            return HoverAnalysis(
                line=position.line,
                character=position.character,
                word="",
                is_operation=False,
                is_parameter=False,
            )

        # Determine if it's an operation or parameter
        # Get text before the word
        text_before = line_text[: position.character]

        # Check if word is an operation (appears after | or at start, not after =)
        is_operation = False
        is_parameter = False
        operation_name: str | None = None
        parameter_name: str | None = None

        # If preceded by = it's likely a parameter value, not parameter name
        if "=" in text_before and text_before.rstrip().endswith("="):
            # It's a value, not a parameter name or operation
            is_operation = False
            is_parameter = False
        else:
            # Check if current_word is followed by = (parameter name pattern)
            # Search only from the end of the current word to avoid matching duplicates
            word_followed_by_equals = False
            if current_word_match:
                text_after_word = line_text[current_word_match.end() :]
                word_followed_by_equals = bool(re.match(r"^\s*=", text_after_word))

            if word_followed_by_equals:
                # This is a parameter name
                is_parameter = True
                parameter_name = current_word

                # Find the operation this parameter belongs to
                # Look backwards for operation name, searching across lines if needed
                operation_name = self._find_operation_for_parameter(
                    lines, position.line, text_before
                )
            # Check if it's an operation
            elif self.registry.operation_exists(current_word):
                is_operation = True

        return HoverAnalysis(
            line=position.line,
            character=position.character,
            word=current_word,
            is_operation=is_operation,
            is_parameter=is_parameter,
            operation_name=operation_name,
            parameter_name=parameter_name,
        )

    def _find_operation_for_parameter(
        self, lines: list[str], current_line: int, text_before: str
    ) -> str | None:
        """
        Find the operation name that a parameter belongs to.

        Searches backward from the parameter position to find the last valid
        operation name. Handles multiline cases and junk text.

        Args:
            lines: All lines in the document
            current_line: Current line number (0-indexed)
            text_before: Text before cursor on current line

        Returns:
            Operation name or None if not found
        """
        # Get text to search: current line segment after last pipe
        text_to_search = text_before.split("|")[-1]

        # If no pipe in current text, search backward across previous lines
        if "|" not in text_before:
            # Build text from previous lines until we find a pipe
            for line_idx in range(current_line - 1, -1, -1):
                prev_line = lines[line_idx] if line_idx < len(lines) else ""
                if "|" in prev_line:
                    # Found pipe - take text after last pipe from this line
                    text_to_search = prev_line.split("|")[-1] + "\n" + text_to_search
                    break
                else:
                    # No pipe yet - prepend entire line
                    text_to_search = prev_line + "\n" + text_to_search

        # Find all identifiers in the text after pipe
        # Match all words (identifiers) in the text
        all_identifiers: list[str] = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", text_to_search)

        # Validate identifiers right-to-left to find the last valid operation
        # This handles cases like "junk where level=2" -> finds "where" not "junk"
        for identifier in reversed(all_identifiers):
            if self.registry.operation_exists(identifier):
                return identifier

        return None

    def _create_operation_hover(self, operation_name: str) -> Hover | None:
        """
        Create hover documentation for an operation.

        Args:
            operation_name: Name of the operation

        Returns:
            Hover with formatted documentation or None if operation not found
        """
        # Get operation metadata
        metadata = self.registry.get_operation(operation_name)
        if not metadata:
            return None

        # Format hover content
        content = self._format_operation_documentation(metadata)

        return Hover(contents=MarkupContent(kind=MarkupKind.Markdown, value=content))

    def _create_parameter_hover(self, operation_name: str, parameter_name: str) -> Hover | None:
        """
        Create hover documentation for a parameter.

        Args:
            operation_name: Name of the operation
            parameter_name: Name of the parameter

        Returns:
            Hover with formatted parameter documentation or None if not found
        """
        # Get operation metadata
        metadata = self.registry.get_operation(operation_name)
        if not metadata:
            return None

        # Find the parameter
        param_info: ParameterInfo | None = None
        for param in metadata.parameters:
            if param.name == parameter_name:
                param_info = param
                break

        if not param_info:
            return None

        # Format parameter documentation
        content = self._format_parameter_documentation(param_info, operation_name)

        return Hover(contents=MarkupContent(kind=MarkupKind.Markdown, value=content))

    def _format_operation_documentation(self, metadata: OperationMetadata) -> str:
        """
        Format operation metadata as markdown documentation.

        Args:
            metadata: Operation metadata

        Returns:
            Formatted markdown string
        """
        lines: list[str] = []

        # Operation name and signature
        if metadata.parameters:
            param_list = ", ".join(p.name for p in metadata.parameters)
            signature = f"**{metadata.name}**({param_list})"
        else:
            signature = f"**{metadata.name}**()"

        lines.append(signature)
        lines.append("")

        # Category badge
        lines.append(f"*{metadata.category}*")
        lines.append("")

        # Description
        lines.append(metadata.description)
        lines.append("")

        # Parameters section (if any)
        if metadata.parameters:
            lines.append("**Parameters:**")
            lines.append("")
            for param in metadata.parameters:
                required_marker = "" if param.required else " (optional)"
                default_marker = f" = {param.default}" if param.default is not None else ""
                lines.append(f"- `{param.name}`: `{param.type}`{required_marker}{default_marker}")
                if param.description:
                    lines.append(f"  - {param.description}")
            lines.append("")

        # Return type
        lines.append(f"**Returns:** `{metadata.return_type}`")
        lines.append("")

        # Examples section (if any)
        if metadata.examples:
            lines.append("**Examples:**")
            lines.append("")
            for example in metadata.examples[:3]:  # Show up to 3 examples
                lines.append("```doctk")
                lines.append(example)
                lines.append("```")
                lines.append("")

        return "\n".join(lines).rstrip()

    def _format_parameter_documentation(self, param: ParameterInfo, operation_name: str) -> str:
        """
        Format parameter information as markdown documentation.

        Args:
            param: Parameter information
            operation_name: Name of the operation this parameter belongs to

        Returns:
            Formatted markdown string
        """
        lines: list[str] = []

        # Parameter name and type
        required_str = "required" if param.required else "optional"
        lines.append(f"**{param.name}** (`{param.type}`, {required_str})")
        lines.append("")

        # Parameter description
        if param.description:
            lines.append(param.description)
            lines.append("")

        # Default value
        if param.default is not None:
            lines.append(f"**Default:** `{param.default}`")
            lines.append("")

        # Show which operation this belongs to
        lines.append(f"*Parameter of:* `{operation_name}`")

        return "\n".join(lines).rstrip()

    def _compute_cache_key(self, analysis: HoverAnalysis) -> str:
        """
        Compute cache key for hover analysis.

        Args:
            analysis: Hover analysis

        Returns:
            Cache key string
        """
        if analysis.is_parameter and analysis.parameter_name and analysis.operation_name:
            return f"param:{analysis.operation_name}:{analysis.parameter_name}"
        elif analysis.is_operation:
            return f"op:{analysis.word}"
        else:
            return f"unknown:{analysis.word}"

    def _get_cached_hover(self, cache_key: str, default: object = None) -> Hover | None | object:
        """
        Get cached hover if not expired.

        Args:
            cache_key: Cache key
            default: Value to return if not found or expired (default: None)

        Returns:
            Cached hover, default value if expired/not found
        """
        cached = self.cache.get(cache_key)
        if cached is None:
            return default

        age = time.time() - cached.timestamp

        # Check if expired
        if age > self.cache_ttl:
            del self.cache[cache_key]
            return default

        return cached.hover

    def _cache_hover(self, cache_key: str, hover: Hover | None) -> None:
        """
        Cache hover result.

        Args:
            cache_key: Cache key
            hover: Hover to cache (can be None)
        """
        self.cache[cache_key] = CachedHover(
            hover=hover,
            timestamp=time.time(),
        )

    def clear_cache(self) -> None:
        """Clear all cached hover results."""
        self.cache.clear()

    def cleanup_expired_cache(self) -> None:
        """
        Remove all expired entries from cache.

        This should be called periodically to prevent unbounded memory growth.
        Iterates over a copy of cache items in a single pass for efficiency.
        """
        current_time = time.time()
        # Iterate over copy to avoid modification during iteration
        for key, cached in list(self.cache.items()):
            if current_time - cached.timestamp > self.cache_ttl:
                del self.cache[key]
