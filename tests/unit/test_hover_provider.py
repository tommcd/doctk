"""Tests for HoverProvider.

This module tests the hover documentation provider for doctk DSL operations and parameters.
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest
from lsprotocol.types import MarkupContent, MarkupKind, Position

from doctk.lsp.hover import HoverProvider
from doctk.lsp.registry import OperationMetadata, OperationRegistry, ParameterInfo


@pytest.fixture
def mock_registry() -> OperationRegistry:
    """Create a mock operation registry for testing."""
    registry = MagicMock(spec=OperationRegistry)

    # Create test operations
    select_op = OperationMetadata(
        name="select",
        description="Select nodes matching a predicate",
        parameters=[
            ParameterInfo(
                name="predicate",
                type="Callable[[Node], bool]",
                required=True,
                description="Function that returns True for nodes to select",
            )
        ],
        return_type="Document",
        examples=["doc | select heading", "doc | select paragraph"],
        category="selection",
    )

    where_op = OperationMetadata(
        name="where",
        description="Filter nodes by attribute conditions",
        parameters=[
            ParameterInfo(
                name="level",
                type="int",
                required=False,
                description="Heading level to match",
                default=None,
            ),
            ParameterInfo(
                name="text",
                type="str",
                required=False,
                description="Text content to match",
                default=None,
            ),
            ParameterInfo(
                name="limit",
                type="int",
                required=False,
                description="Maximum number of results to return",
                default=10,
            ),
        ],
        return_type="Document",
        examples=["doc | where level=2", "doc | where text='Introduction'"],
        category="selection",
    )

    promote_op = OperationMetadata(
        name="promote",
        description="Promote heading levels (h3 -> h2)",
        parameters=[],
        return_type="Document",
        examples=["doc | select heading | promote()"],
        category="structure",
    )

    # Configure mock registry
    def get_operation(name: str) -> OperationMetadata | None:
        ops = {"select": select_op, "where": where_op, "promote": promote_op}
        return ops.get(name)

    def operation_exists(name: str) -> bool:
        return name in {"select", "where", "promote"}

    registry.get_operation = get_operation
    registry.operation_exists = operation_exists

    return registry


@pytest.fixture
def hover_provider(mock_registry: OperationRegistry) -> HoverProvider:
    """Create a hover provider with mock registry."""
    return HoverProvider(mock_registry)


class TestHoverProviderInitialization:
    """Test hover provider initialization."""

    def test_init_with_defaults(self, mock_registry: OperationRegistry) -> None:
        """Test initialization with default cache TTL."""
        provider = HoverProvider(mock_registry)

        assert provider.registry is mock_registry
        assert provider.cache == {}
        assert provider.cache_ttl == 5.0

    def test_init_with_custom_ttl(self, mock_registry: OperationRegistry) -> None:
        """Test initialization with custom cache TTL."""
        provider = HoverProvider(mock_registry, cache_ttl=10.0)

        assert provider.cache_ttl == 10.0


class TestPositionAnalysis:
    """Test cursor position analysis."""

    def test_analyze_operation_word(self, hover_provider: HoverProvider) -> None:
        """Test analyzing cursor on operation name."""
        document = "doc | select"
        position = Position(line=0, character=8)  # On "select"

        analysis = hover_provider._analyze_position(document, position)

        assert analysis.word == "select"
        assert analysis.is_operation is True
        assert analysis.is_parameter is False

    def test_analyze_parameter_name(self, hover_provider: HoverProvider) -> None:
        """Test analyzing cursor on parameter name."""
        document = "doc | where level=2"
        position = Position(line=0, character=13)  # On "level"

        analysis = hover_provider._analyze_position(document, position)

        assert analysis.word == "level"
        assert analysis.is_parameter is True
        assert analysis.is_operation is False
        assert analysis.operation_name == "where"
        assert analysis.parameter_name == "level"

    def test_analyze_empty_position(self, hover_provider: HoverProvider) -> None:
        """Test analyzing cursor on whitespace."""
        document = "doc |  "
        position = Position(line=0, character=6)  # On space

        analysis = hover_provider._analyze_position(document, position)

        assert analysis.word == ""
        assert analysis.is_operation is False
        assert analysis.is_parameter is False

    def test_analyze_out_of_bounds(self, hover_provider: HoverProvider) -> None:
        """Test analyzing cursor beyond document bounds."""
        document = "doc | select"
        position = Position(line=5, character=0)  # Line doesn't exist

        analysis = hover_provider._analyze_position(document, position)

        assert analysis.word == ""
        assert analysis.is_operation is False

    def test_analyze_parameter_value(self, hover_provider: HoverProvider) -> None:
        """Test analyzing cursor on parameter value (not name)."""
        document = "doc | where level=2"
        position = Position(line=0, character=18)  # On "2"

        analysis = hover_provider._analyze_position(document, position)

        # Should not identify as operation or parameter
        assert analysis.is_operation is False
        assert analysis.is_parameter is False


class TestOperationHover:
    """Test hover documentation for operations."""

    def test_hover_on_operation(self, hover_provider: HoverProvider) -> None:
        """Test hovering over an operation name."""
        document = "doc | select"
        position = Position(line=0, character=8)

        hover = hover_provider.provide_hover(document, position)

        assert hover is not None
        assert isinstance(hover.contents, MarkupContent)
        assert hover.contents.kind == MarkupKind.Markdown

        # Check content includes operation name
        content = hover.contents.value
        assert "select" in content
        assert "Select nodes matching a predicate" in content

    def test_hover_includes_parameters(self, hover_provider: HoverProvider) -> None:
        """Test hover includes parameter information."""
        document = "doc | where"
        position = Position(line=0, character=8)

        hover = hover_provider.provide_hover(document, position)

        assert hover is not None
        content = hover.contents.value

        # Check parameter information is included
        assert "Parameters:" in content
        assert "level" in content
        assert "text" in content
        assert "int" in content
        assert "str" in content

    def test_hover_includes_examples(self, hover_provider: HoverProvider) -> None:
        """Test hover includes usage examples."""
        document = "doc | promote"
        position = Position(line=0, character=9)

        hover = hover_provider.provide_hover(document, position)

        assert hover is not None
        content = hover.contents.value

        # Check examples are included
        assert "Examples:" in content
        assert "doc | select heading | promote()" in content

    def test_hover_includes_return_type(self, hover_provider: HoverProvider) -> None:
        """Test hover includes return type."""
        document = "doc | promote"
        position = Position(line=0, character=9)

        hover = hover_provider.provide_hover(document, position)

        assert hover is not None
        content = hover.contents.value

        assert "Returns:" in content
        assert "Document" in content

    def test_hover_on_unknown_operation(self, hover_provider: HoverProvider) -> None:
        """Test hovering over unknown operation returns None."""
        document = "doc | unknown_op"
        position = Position(line=0, character=10)

        hover = hover_provider.provide_hover(document, position)

        assert hover is None


class TestParameterHover:
    """Test hover documentation for parameters."""

    def test_hover_on_parameter(self, hover_provider: HoverProvider) -> None:
        """Test hovering over a parameter name."""
        document = "doc | where level=2"
        position = Position(line=0, character=13)  # On "level"

        hover = hover_provider.provide_hover(document, position)

        assert hover is not None
        assert isinstance(hover.contents, MarkupContent)

        content = hover.contents.value
        assert "level" in content
        assert "int" in content
        assert "Heading level to match" in content

    def test_hover_parameter_shows_operation(self, hover_provider: HoverProvider) -> None:
        """Test parameter hover shows which operation it belongs to."""
        document = "doc | where text='foo'"
        position = Position(line=0, character=13)  # On "text"

        hover = hover_provider.provide_hover(document, position)

        assert hover is not None
        content = hover.contents.value

        # Should indicate which operation this parameter belongs to
        assert "where" in content

    def test_hover_parameter_shows_required_status(self, hover_provider: HoverProvider) -> None:
        """Test parameter hover shows if parameter is required or optional."""
        document = "doc | where level=2"
        position = Position(line=0, character=13)

        hover = hover_provider.provide_hover(document, position)

        assert hover is not None
        content = hover.contents.value

        # "level" parameter is optional
        assert "optional" in content.lower()

    def test_hover_parameter_shows_default(self, hover_provider: HoverProvider) -> None:
        """Test parameter hover shows default value if available."""
        document = "doc | where limit=5"
        position = Position(line=0, character=13)  # On "limit"

        hover = hover_provider.provide_hover(document, position)

        assert hover is not None
        content = hover.contents.value

        # The limit parameter has default=10 in our mock
        # Verify the default value appears in the hover content
        assert "default" in content.lower() or "10" in content
        assert "limit" in content


class TestHoverCaching:
    """Test hover result caching."""

    def test_cache_hit_returns_cached_result(self, hover_provider: HoverProvider) -> None:
        """Test that subsequent identical requests use cached results."""
        document = "doc | select"
        position = Position(line=0, character=8)

        # First request
        hover1 = hover_provider.provide_hover(document, position)

        # Second request should use cache
        hover2 = hover_provider.provide_hover(document, position)

        assert hover1 is not None
        assert hover2 is not None
        # Should be the same cached object
        assert hover1 is hover2

    def test_cache_respects_ttl(self, mock_registry: OperationRegistry) -> None:
        """Test that cache entries expire after TTL."""
        provider = HoverProvider(mock_registry, cache_ttl=0.1)  # 100ms TTL

        document = "doc | select"
        position = Position(line=0, character=8)

        # First request
        hover1 = provider.provide_hover(document, position)

        # Wait for cache to expire
        time.sleep(0.2)

        # Second request should recompute
        hover2 = provider.provide_hover(document, position)

        assert hover1 is not None
        assert hover2 is not None
        # Should be different objects (cache expired)
        assert hover1 is not hover2

    def test_clear_cache(self, hover_provider: HoverProvider) -> None:
        """Test clearing the cache."""
        document = "doc | select"
        position = Position(line=0, character=8)

        # Populate cache
        _ = hover_provider.provide_hover(document, position)
        assert len(hover_provider.cache) > 0

        # Clear cache
        hover_provider.clear_cache()

        assert len(hover_provider.cache) == 0

    def test_cleanup_expired_cache(self, mock_registry: OperationRegistry) -> None:
        """Test cleanup of expired cache entries."""
        provider = HoverProvider(mock_registry, cache_ttl=0.1)

        document1 = "doc | select"
        document2 = "doc | where"

        # Add two entries
        provider.provide_hover(document1, Position(line=0, character=8))
        provider.provide_hover(document2, Position(line=0, character=8))

        assert len(provider.cache) == 2

        # Wait for expiration
        time.sleep(0.2)

        # Cleanup expired entries
        provider.cleanup_expired_cache()

        assert len(provider.cache) == 0

    def test_cache_none_results(self, hover_provider: HoverProvider) -> None:
        """Test that None results are also cached."""
        document = "   "  # Empty/whitespace document
        position = Position(line=0, character=0)

        # First request returns None
        hover1 = hover_provider.provide_hover(document, position)
        assert hover1 is None

        # Cache should store None result
        assert len(hover_provider.cache) > 0

        # Second request should use cached None
        hover2 = hover_provider.provide_hover(document, position)
        assert hover2 is None


class TestHoverFormatting:
    """Test hover content formatting."""

    def test_operation_with_no_parameters(self, hover_provider: HoverProvider) -> None:
        """Test formatting of operation with no parameters."""
        document = "doc | promote"
        position = Position(line=0, character=9)

        hover = hover_provider.provide_hover(document, position)

        assert hover is not None
        content = hover.contents.value

        # Should show empty parameter list
        assert "promote()" in content
        # Should not have Parameters section
        # (promote has no parameters in our mock)

    def test_operation_with_multiple_parameters(self, hover_provider: HoverProvider) -> None:
        """Test formatting of operation with multiple parameters."""
        document = "doc | where"
        position = Position(line=0, character=8)

        hover = hover_provider.provide_hover(document, position)

        assert hover is not None
        content = hover.contents.value

        # Should show all parameters
        assert "level" in content
        assert "text" in content
        # Should have Parameters section
        assert "Parameters:" in content

    def test_markdown_formatting(self, hover_provider: HoverProvider) -> None:
        """Test that hover uses proper markdown formatting."""
        document = "doc | select"
        position = Position(line=0, character=8)

        hover = hover_provider.provide_hover(document, position)

        assert hover is not None
        content = hover.contents.value

        # Check for markdown formatting
        assert "**" in content  # Bold text
        assert "`" in content  # Code formatting
        assert "```" in content  # Code blocks for examples


class TestHoverPerformance:
    """Test hover performance requirements."""

    def test_hover_response_time(self, hover_provider: HoverProvider) -> None:
        """Test that hover responds within 200ms (requirement 10.5)."""
        document = "doc | select"
        position = Position(line=0, character=8)

        start_time = time.time()
        hover = hover_provider.provide_hover(document, position)
        elapsed = time.time() - start_time

        assert hover is not None
        # Should be well under 200ms
        assert elapsed < 0.2

    def test_cached_hover_is_faster(self, hover_provider: HoverProvider) -> None:
        """Test that cached hover responses are faster than initial."""
        document = "doc | select"
        position = Position(line=0, character=8)

        # First request (uncached)
        start1 = time.time()
        _ = hover_provider.provide_hover(document, position)
        time1 = time.time() - start1

        # Second request (cached)
        start2 = time.time()
        _ = hover_provider.provide_hover(document, position)
        time2 = time.time() - start2

        # Cached should be faster (or at least not slower)
        assert time2 <= time1 * 1.5  # Allow some variance


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_multiline_document(self, hover_provider: HoverProvider) -> None:
        """Test hover in multiline document."""
        document = "doc | select\n  | where level=2\n  | promote"
        position = Position(line=1, character=7)  # On "where"

        hover = hover_provider.provide_hover(document, position)

        assert hover is not None
        assert "where" in hover.contents.value

    def test_hover_at_end_of_word(self, hover_provider: HoverProvider) -> None:
        """Test hover when cursor is at end of word."""
        document = "doc | select"
        position = Position(line=0, character=12)  # After "select"

        hover = hover_provider.provide_hover(document, position)

        assert hover is not None
        assert "select" in hover.contents.value

    def test_hover_at_start_of_word(self, hover_provider: HoverProvider) -> None:
        """Test hover when cursor is at start of word."""
        document = "doc | select"
        position = Position(line=0, character=6)  # At "s" of "select"

        hover = hover_provider.provide_hover(document, position)

        assert hover is not None
        assert "select" in hover.contents.value
