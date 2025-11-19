"""Tests for completion provider."""

import time

from lsprotocol.types import (
    CompletionItemKind,
    InsertTextFormat,
    Position,
)

from doctk.lsp.completion import (
    CompletionContext,
    CompletionProvider,
)
from doctk.lsp.registry import OperationRegistry


class TestCompletionAnalysis:
    """Test context analysis for completions."""

    def test_start_of_line_empty(self):
        """Test context analysis at start of empty line."""
        provider = CompletionProvider(OperationRegistry())

        document = ""
        position = Position(line=0, character=0)

        analysis = provider._analyze_context(document, position)

        assert analysis.context == CompletionContext.START_OF_LINE
        assert analysis.current_word == ""
        assert analysis.line == 0
        assert analysis.character == 0

    def test_start_of_line_with_whitespace(self):
        """Test context analysis at start of line with whitespace."""
        provider = CompletionProvider(OperationRegistry())

        document = "   "
        position = Position(line=0, character=3)

        analysis = provider._analyze_context(document, position)

        assert analysis.context == CompletionContext.START_OF_LINE
        assert analysis.current_word == ""

    def test_after_pipe_operator(self):
        """Test context analysis after pipe operator."""
        provider = CompletionProvider(OperationRegistry())

        document = "doc |"
        position = Position(line=0, character=5)

        analysis = provider._analyze_context(document, position)

        assert analysis.context == CompletionContext.AFTER_PIPE
        assert analysis.current_word == ""

    def test_after_pipe_with_space(self):
        """Test context analysis after pipe with space."""
        provider = CompletionProvider(OperationRegistry())

        document = "doc | "
        position = Position(line=0, character=6)

        analysis = provider._analyze_context(document, position)

        assert analysis.context == CompletionContext.AFTER_PIPE
        assert analysis.current_word == ""

    def test_after_pipe_with_partial_word(self):
        """Test context analysis after pipe with partial word."""
        provider = CompletionProvider(OperationRegistry())

        document = "doc | sel"
        position = Position(line=0, character=9)

        analysis = provider._analyze_context(document, position)

        assert analysis.context == CompletionContext.AFTER_PIPE
        assert analysis.current_word == "sel"

    def test_in_operation_context(self):
        """Test context analysis inside operation parameters."""
        provider = CompletionProvider(OperationRegistry())

        document = "doc | select "
        position = Position(line=0, character=13)

        analysis = provider._analyze_context(document, position)

        assert analysis.context == CompletionContext.IN_OPERATION
        assert analysis.line_text == "doc | select "

    def test_partial_text_without_context(self):
        """Test context analysis with partial text (no pipe, not 'doc')."""
        provider = CompletionProvider(OperationRegistry())

        document = "pro"
        position = Position(line=0, character=3)

        analysis = provider._analyze_context(document, position)

        # Conservative behavior: unknown context for ambiguous text
        # User should type "doc" to start a valid pipeline
        assert analysis.context == CompletionContext.UNKNOWN
        assert analysis.current_word == "pro"


class TestStartOfLineCompletions:
    """Test completions at start of line."""

    def test_doc_keyword_completion(self):
        """Test that 'doc' keyword is suggested at start of line."""
        provider = CompletionProvider(OperationRegistry())

        document = ""
        position = Position(line=0, character=0)

        completions = provider.provide_completions(document, position)

        assert len(completions.items) == 1
        assert completions.items[0].label == "doc"
        assert completions.items[0].kind == CompletionItemKind.Keyword
        assert completions.items[0].insert_text == "doc"


class TestOperationCompletions:
    """Test operation completions after pipe."""

    def test_all_operations_after_pipe(self):
        """Test that all operations are suggested after pipe."""
        provider = CompletionProvider(OperationRegistry())

        document = "doc |"
        position = Position(line=0, character=5)

        completions = provider.provide_completions(document, position)

        # Should have multiple operations
        assert len(completions.items) > 0

        # Check for known operations
        labels = {item.label for item in completions.items}
        assert "select" in labels
        assert "where" in labels
        assert "promote" in labels
        assert "demote" in labels

    def test_operations_filtered_by_prefix(self):
        """Test that operations are filtered by prefix."""
        provider = CompletionProvider(OperationRegistry())

        document = "doc | pro"
        position = Position(line=0, character=9)

        completions = provider.provide_completions(document, position)

        # Should only have operations starting with 'pro'
        for item in completions.items:
            assert item.label.lower().startswith("pro")

        # Check for promote
        labels = {item.label for item in completions.items}
        assert "promote" in labels

    def test_operation_with_parameters_has_snippet(self):
        """Test that operations with parameters have snippet insert text."""
        provider = CompletionProvider(OperationRegistry())

        document = "doc | sel"
        position = Position(line=0, character=9)

        completions = provider.provide_completions(document, position)

        # Find select operation
        select_item = next(
            (item for item in completions.items if item.label == "select"),
            None,
        )

        assert select_item is not None
        assert select_item.insert_text_format == InsertTextFormat.Snippet
        # Should have parameter placeholder in key=value format
        # Format: select(predicate=${1})
        assert "predicate=${1}" in select_item.insert_text or "${1}" in select_item.insert_text

    def test_operation_without_parameters_plain_text(self):
        """Test that operations without parameters have plain text."""
        provider = CompletionProvider(OperationRegistry())

        document = "doc | pro"
        position = Position(line=0, character=9)

        completions = provider.provide_completions(document, position)

        # Find promote operation (has no parameters)
        promote_item = next(
            (item for item in completions.items if item.label == "promote"),
            None,
        )

        assert promote_item is not None
        assert promote_item.insert_text_format == InsertTextFormat.PlainText
        # Zero-argument operations must include () for invocation
        assert promote_item.insert_text == "promote()"

    def test_operation_completion_has_documentation(self):
        """Test that operation completions include documentation."""
        provider = CompletionProvider(OperationRegistry())

        document = "doc | "
        position = Position(line=0, character=6)

        completions = provider.provide_completions(document, position)

        # All items should have documentation
        for item in completions.items:
            assert item.documentation is not None
            assert len(item.documentation) > 0

    def test_operation_completion_includes_examples(self):
        """Test that operation completions include examples in documentation."""
        provider = CompletionProvider(OperationRegistry())

        document = "doc | "
        position = Position(line=0, character=6)

        completions = provider.provide_completions(document, position)

        # Find select operation
        select_item = next(
            (item for item in completions.items if item.label == "select"),
            None,
        )

        assert select_item is not None
        # Should include example in documentation
        assert "Example:" in select_item.documentation

    def test_operation_completion_sorted(self):
        """Test that operation completions are sorted."""
        provider = CompletionProvider(OperationRegistry())

        document = "doc | "
        position = Position(line=0, character=6)

        completions = provider.provide_completions(document, position)

        # Items should be sorted by sort_text
        sort_keys = [item.sort_text or item.label for item in completions.items]
        assert sort_keys == sorted(sort_keys)


class TestParameterCompletions:
    """Test parameter completions."""

    def test_parameter_completions_for_operation(self):
        """Test parameter completions for operation with parameters."""
        provider = CompletionProvider(OperationRegistry())

        # select has a predicate parameter (but we need to test operations with
        # simpler parameters like where or nest)
        document = "doc | nest "
        position = Position(line=0, character=11)

        completions = provider.provide_completions(document, position)

        # Should have parameter completions
        # nest has 'under' parameter
        labels = {item.label for item in completions.items}
        assert "under" in labels

    def test_parameter_completion_has_type_info(self):
        """Test that parameter completions include type information."""
        provider = CompletionProvider(OperationRegistry())

        document = "doc | nest "
        position = Position(line=0, character=11)

        completions = provider.provide_completions(document, position)

        # Find under parameter
        under_item = next(
            (item for item in completions.items if item.label == "under"),
            None,
        )

        assert under_item is not None
        assert under_item.kind == CompletionItemKind.Property
        assert under_item.detail is not None  # Type info

    def test_parameter_completion_has_snippet(self):
        """Test that parameter completions have snippet format."""
        provider = CompletionProvider(OperationRegistry())

        document = "doc | nest "
        position = Position(line=0, character=11)

        completions = provider.provide_completions(document, position)

        # Find under parameter
        under_item = next(
            (item for item in completions.items if item.label == "under"),
            None,
        )

        assert under_item is not None
        assert under_item.insert_text_format == InsertTextFormat.Snippet
        # Should have key=value format with placeholder
        assert "under=" in under_item.insert_text

    def test_no_parameter_completions_for_operation_without_params(self):
        """Test no parameter completions for operations without parameters."""
        provider = CompletionProvider(OperationRegistry())

        # promote has no parameters
        document = "doc | promote "
        position = Position(line=0, character=14)

        completions = provider.provide_completions(document, position)

        # Should have no completions (or empty list)
        assert len(completions.items) == 0

    def test_no_parameter_completions_for_unknown_operation(self):
        """Test no parameter completions for unknown operations."""
        provider = CompletionProvider(OperationRegistry())

        document = "doc | unknown_op "
        position = Position(line=0, character=17)

        completions = provider.provide_completions(document, position)

        # Should have no completions
        assert len(completions.items) == 0


class TestCompletionCaching:
    """Test completion caching behavior."""

    def test_completions_are_cached(self):
        """Test that completions are cached."""
        provider = CompletionProvider(OperationRegistry())

        document = "doc | "
        position = Position(line=0, character=6)

        # First request
        completions1 = provider.provide_completions(document, position)

        # Should be cached now
        cache_key = "after_pipe:"
        assert cache_key in provider.cache

        # Second request should return cached result
        completions2 = provider.provide_completions(document, position)

        # Should be the same object (cached)
        assert completions1 is completions2

    def test_cache_expires_after_ttl(self):
        """Test that cache expires after TTL."""
        provider = CompletionProvider(OperationRegistry())
        provider.cache_ttl = 0.1  # 100ms TTL

        document = "doc | "
        position = Position(line=0, character=6)

        # First request
        completions1 = provider.provide_completions(document, position)

        # Wait for cache to expire
        time.sleep(0.2)

        # Second request should recompute
        completions2 = provider.provide_completions(document, position)

        # Should be different objects (cache expired)
        assert completions1 is not completions2

    def test_different_contexts_have_different_cache_keys(self):
        """Test that different contexts have different cache keys."""
        provider = CompletionProvider(OperationRegistry())

        # After pipe
        document1 = "doc | "
        position1 = Position(line=0, character=6)
        provider.provide_completions(document1, position1)

        # Start of line
        document2 = ""
        position2 = Position(line=0, character=0)
        provider.provide_completions(document2, position2)

        # Should have two cache entries
        assert len(provider.cache) == 2

    def test_cache_can_be_cleared(self):
        """Test that cache can be cleared."""
        provider = CompletionProvider(OperationRegistry())

        document = "doc | "
        position = Position(line=0, character=6)

        # Generate some cached completions
        provider.provide_completions(document, position)

        assert len(provider.cache) > 0

        # Clear cache
        provider.clear_cache()

        assert len(provider.cache) == 0

    def test_cache_cleanup_removes_expired_entries(self):
        """Test that cleanup_expired_cache removes only expired entries."""
        provider = CompletionProvider(OperationRegistry())
        provider.cache_ttl = 0.1  # 100ms TTL

        # Create some cached completions
        document1 = "doc | "
        position1 = Position(line=0, character=6)
        provider.provide_completions(document1, position1)

        # Wait a bit but not enough to expire
        time.sleep(0.05)

        # Create another cached completion
        document2 = "doc | pro"
        position2 = Position(line=0, character=9)
        provider.provide_completions(document2, position2)

        # Should have 2 cache entries
        assert len(provider.cache) == 2

        # Wait for first entry to expire
        time.sleep(0.06)  # Total 110ms for first, 60ms for second

        # Clean up expired entries
        provider.cleanup_expired_cache()

        # First entry should be removed, second should remain
        assert len(provider.cache) == 1

    def test_cache_key_includes_operation_name(self):
        """Test that cache key includes operation name to prevent incorrect reuse."""
        provider = CompletionProvider(OperationRegistry())

        # Request parameter completions for different operations
        # promote has no parameters, nest has parameters
        doc_promote = "doc | promote "
        pos_promote = Position(line=0, character=14)

        doc_nest = "doc | nest "
        pos_nest = Position(line=0, character=11)

        completions_promote = provider.provide_completions(doc_promote, pos_promote)
        completions_nest = provider.provide_completions(doc_nest, pos_nest)

        # Should have different cache entries (different operation names)
        assert len(provider.cache) == 2

        # Nest should have parameter completions, promote should not
        assert len(completions_promote.items) == 0
        assert len(completions_nest.items) > 0


class TestCompletionIntegration:
    """Integration tests for completion provider."""

    def test_completion_workflow_from_start_to_operation(self):
        """Test complete workflow: start -> doc -> pipe -> operation."""
        provider = CompletionProvider(OperationRegistry())

        # Step 1: Start of line - should suggest 'doc'
        completions = provider.provide_completions("", Position(line=0, character=0))
        assert any(item.label == "doc" for item in completions.items)

        # Step 2: After pipe - should suggest operations
        completions = provider.provide_completions("doc |", Position(line=0, character=5))
        assert any(item.label == "select" for item in completions.items)

        # Step 3: Inside operation - should suggest parameters (for operations that have them)
        completions = provider.provide_completions("doc | nest ", Position(line=0, character=11))
        # nest has parameters
        if len(completions.items) > 0:
            assert any(item.kind == CompletionItemKind.Property for item in completions.items)

    def test_multiline_document_completion(self):
        """Test completions in multiline documents."""
        provider = CompletionProvider(OperationRegistry())

        document = "doc | select heading\n| "
        position = Position(line=1, character=2)

        completions = provider.provide_completions(document, position)

        # Should suggest operations after pipe on second line
        assert len(completions.items) > 0
        assert any(item.label == "promote" for item in completions.items)

    def test_completion_performance_under_200ms(self):
        """Test that completions are generated quickly (under 200ms requirement)."""
        provider = CompletionProvider(OperationRegistry())

        document = "doc | "
        position = Position(line=0, character=6)

        # Measure time for first request (uncached)
        start = time.time()
        completions = provider.provide_completions(document, position)
        duration = time.time() - start

        # Should be fast (under 200ms)
        assert duration < 0.2, f"Completion took {duration*1000:.1f}ms (exceeds 200ms)"
        assert len(completions.items) > 0

    def test_cached_completion_performance_under_50ms(self):
        """Test that cached completions are very fast (under 50ms)."""
        provider = CompletionProvider(OperationRegistry())

        document = "doc | "
        position = Position(line=0, character=6)

        # First request to populate cache
        provider.provide_completions(document, position)

        # Measure time for cached request
        start = time.time()
        completions = provider.provide_completions(document, position)
        duration = time.time() - start

        # Should be very fast (under 50ms for cached)
        assert duration < 0.05, f"Cached completion took {duration*1000:.1f}ms (exceeds 50ms)"
        assert len(completions.items) > 0
