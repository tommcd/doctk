"""Completion Provider for doctk Language Server.

This module provides intelligent code completion for doctk DSL operations,
including context-aware operation suggestions and parameter completions.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum

from lsprotocol.types import (
    CompletionItem,
    CompletionItemKind,
    CompletionList,
    InsertTextFormat,
    Position,
)

from doctk.lsp.registry import OperationRegistry

logger = logging.getLogger(__name__)


class CompletionContext(Enum):
    """Type of completion context."""

    START_OF_LINE = "start_of_line"  # doc or identifier
    AFTER_PIPE = "after_pipe"  # After | operator
    IN_OPERATION = "in_operation"  # Inside operation parameters
    UNKNOWN = "unknown"


@dataclass
class CompletionAnalysis:
    """Analysis of cursor position for completion."""

    context: CompletionContext
    line: int
    character: int
    current_word: str
    line_text: str
    operation_name: str | None = None  # Operation name when context is IN_OPERATION


@dataclass
class CachedCompletion:
    """Cached completion result with timestamp."""

    completions: CompletionList
    timestamp: float


class CompletionProvider:
    """Provides intelligent code completion for doctk DSL."""

    def __init__(self, registry: OperationRegistry, cache_ttl: float = 5.0):
        """
        Initialize completion provider.

        Args:
            registry: Operation registry for available operations
            cache_ttl: Time-to-live for cached completions in seconds (default: 5.0)
        """
        self.registry = registry
        self.cache: dict[str, CachedCompletion] = {}
        self.cache_ttl = cache_ttl

    def provide_completions(
        self, document: str, position: Position
    ) -> CompletionList:
        """
        Provide completion suggestions at the given position.

        Args:
            document: Full document text
            position: Cursor position (line and character)

        Returns:
            List of completion items
        """
        # Analyze context
        analysis = self._analyze_context(document, position)

        # Check cache
        cache_key = self._compute_cache_key(analysis)
        cached = self._get_cached_completion(cache_key)
        if cached:
            logger.debug(f"Cache hit for completion at {position}")
            return cached

        # Generate completions based on context
        if analysis.context == CompletionContext.START_OF_LINE:
            completions = self._start_of_line_completions()
        elif analysis.context == CompletionContext.AFTER_PIPE:
            completions = self._operation_completions(analysis)
        elif analysis.context == CompletionContext.IN_OPERATION:
            completions = self._parameter_completions(analysis)
        else:
            completions = CompletionList(is_incomplete=False, items=[])

        # Cache the result
        self._cache_completion(cache_key, completions)

        return completions

    def _analyze_context(
        self, document: str, position: Position
    ) -> CompletionAnalysis:
        """
        Analyze cursor position to determine completion context.

        Args:
            document: Full document text
            position: Cursor position

        Returns:
            Completion analysis result
        """
        lines = document.split("\n")

        # Get current line
        if position.line >= len(lines):
            line_text = ""
        else:
            line_text = lines[position.line]

        # Get text before cursor
        text_before = line_text[: position.character]

        # Get text after last pipe (if any)
        if "|" in text_before:
            text_after_pipe = text_before.split("|")[-1]
        else:
            text_after_pipe = text_before

        # Get current word (text after last whitespace, excluding special chars)
        # Split by whitespace and get last part, then remove special characters
        parts = text_after_pipe.strip().split()
        if parts:
            current_word = parts[-1].strip("|").strip()
        else:
            current_word = ""

        # Determine context
        context = CompletionContext.UNKNOWN
        operation_name: str | None = None

        # Check if we're at start of line (doc or identifier)
        if not text_before.strip():
            context = CompletionContext.START_OF_LINE
        # Check if after pipe operator (with or without space)
        elif "|" in text_before:
            text_after_pipe_stripped = text_after_pipe.strip()
            parts = text_after_pipe_stripped.split()

            # Check if there's text after the pipe that looks like an operation with params
            # Pattern: "operation_name param1" or "operation_name "
            if parts:
                # Check if the first word is a valid operation
                first_word = parts[0]
                if self.registry.operation_exists(first_word):
                    # Check if there's a space after the operation name
                    # This indicates we're inside the operation's parameters
                    if text_after_pipe.strip() != first_word or text_after_pipe.endswith(" "):
                        context = CompletionContext.IN_OPERATION
                        operation_name = first_word  # Store for parameter completions
                    else:
                        context = CompletionContext.AFTER_PIPE
                else:
                    context = CompletionContext.AFTER_PIPE
            else:
                context = CompletionContext.AFTER_PIPE
        # Default to after pipe for partial matches
        elif text_before.strip() and not text_before.strip().startswith("doc"):
            context = CompletionContext.AFTER_PIPE

        return CompletionAnalysis(
            context=context,
            line=position.line,
            character=position.character,
            current_word=current_word,
            line_text=line_text,
            operation_name=operation_name,
        )

    def _start_of_line_completions(self) -> CompletionList:
        """
        Provide completions for start of line (doc keyword).

        Returns:
            Completion list with doc keyword
        """
        items = [
            CompletionItem(
                label="doc",
                kind=CompletionItemKind.Keyword,
                detail="Document source",
                documentation="The source document to operate on",
                insert_text="doc",
            )
        ]

        return CompletionList(is_incomplete=False, items=items)

    def _operation_completions(
        self, analysis: CompletionAnalysis
    ) -> CompletionList:
        """
        Provide completions for operations after pipe operator.

        Args:
            analysis: Context analysis result

        Returns:
            Completion list with available operations
        """
        items: list[CompletionItem] = []

        # Get all operations from registry
        operations = self.registry.get_all_operations()

        # Filter by current word (prefix match)
        prefix = analysis.current_word.lower()

        for op in operations:
            # Skip if doesn't match prefix
            if prefix and not op.name.lower().startswith(prefix):
                continue

            # Create completion item
            detail = f"{op.category} operation"
            documentation = op.description

            # Add examples to documentation if available
            if op.examples:
                examples_str = "\n".join(f"  {ex}" for ex in op.examples[:2])  # Show up to 2 examples
                documentation += f"\n\nExample:\n{examples_str}"

            # Create snippet for operations with parameters
            if op.parameters:
                # Create snippet with placeholders
                param_placeholders = ", ".join(
                    f"${{{i+1}:{param.name}}}"
                    for i, param in enumerate(op.parameters)
                )
                insert_text = f"{op.name}({param_placeholders})"
                insert_text_format = InsertTextFormat.Snippet
            else:
                # No parameters - simple completion
                insert_text = op.name
                insert_text_format = InsertTextFormat.PlainText

            item = CompletionItem(
                label=op.name,
                kind=CompletionItemKind.Function,
                detail=detail,
                documentation=documentation,
                insert_text=insert_text,
                insert_text_format=insert_text_format,
                sort_text=f"{op.category}_{op.name}",  # Sort by category then name
            )

            items.append(item)

        # Sort items by label
        items.sort(key=lambda x: x.sort_text or x.label)

        return CompletionList(is_incomplete=False, items=items)

    def _parameter_completions(
        self, analysis: CompletionAnalysis
    ) -> CompletionList:
        """
        Provide completions for operation parameters.

        Args:
            analysis: Context analysis result

        Returns:
            Completion list with parameter suggestions
        """
        # Use operation name from analysis (already extracted in _analyze_context)
        if not analysis.operation_name:
            return CompletionList(is_incomplete=False, items=[])

        # Get operation metadata
        op_metadata = self.registry.get_operation(analysis.operation_name)
        if not op_metadata or not op_metadata.parameters:
            return CompletionList(is_incomplete=False, items=[])

        # Create completion items for parameters
        items: list[CompletionItem] = []

        for param in op_metadata.parameters:
            # Create parameter completion
            detail = f"{param.type}"
            documentation = param.description

            # Create snippet for key=value format
            insert_text = f"{param.name}=${{1:{param.default or ''}}}"

            item = CompletionItem(
                label=param.name,
                kind=CompletionItemKind.Property,
                detail=detail,
                documentation=documentation,
                insert_text=insert_text,
                insert_text_format=InsertTextFormat.Snippet,
            )

            items.append(item)

        return CompletionList(is_incomplete=False, items=items)

    def _compute_cache_key(self, analysis: CompletionAnalysis) -> str:
        """
        Compute cache key for completion analysis.

        Args:
            analysis: Completion analysis

        Returns:
            Cache key string
        """
        return f"{analysis.context.value}:{analysis.current_word}"

    def _get_cached_completion(
        self, cache_key: str
    ) -> CompletionList | None:
        """
        Get cached completion if not expired.

        Args:
            cache_key: Cache key

        Returns:
            Cached completion list or None if expired/not found
        """
        cached = self.cache.get(cache_key)
        if cached is None:
            return None

        age = time.time() - cached.timestamp

        # Check if expired
        if age > self.cache_ttl:
            del self.cache[cache_key]
            return None

        return cached.completions

    def _cache_completion(
        self, cache_key: str, completions: CompletionList
    ) -> None:
        """
        Cache completion result.

        Args:
            cache_key: Cache key
            completions: Completion list to cache
        """
        self.cache[cache_key] = CachedCompletion(
            completions=completions,
            timestamp=time.time(),
        )

    def clear_cache(self) -> None:
        """Clear all cached completions."""
        self.cache.clear()
