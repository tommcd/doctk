"""Tests for AI agent support module."""

from __future__ import annotations

import pytest

from doctk.lsp.ai_support import AIAgentSupport, OperationSuggestion, StructuredDocumentation
from doctk.lsp.registry import OperationRegistry


@pytest.fixture
def registry() -> OperationRegistry:
    """Create a test operation registry."""
    return OperationRegistry()


@pytest.fixture
def ai_support(registry: OperationRegistry) -> AIAgentSupport:
    """Create AI agent support with test registry."""
    return AIAgentSupport(registry)


class TestAIAgentSupport:
    """Test AI agent support initialization."""

    def test_init(self, registry: OperationRegistry) -> None:
        """Test AI agent support initialization."""
        support = AIAgentSupport(registry)
        assert support.registry is registry


class TestOperationCatalog:
    """Test operation catalog generation."""

    def test_get_operation_catalog(self, ai_support: AIAgentSupport) -> None:
        """Test getting complete operation catalog."""
        catalog = ai_support.get_operation_catalog()

        # Should be a dictionary
        assert isinstance(catalog, dict)

        # Should contain known operations
        assert "select" in catalog or "heading" in catalog

        # If catalog has operations, verify structure
        if catalog:
            first_op = next(iter(catalog.values()))
            assert "description" in first_op
            assert "parameters" in first_op
            assert "return_type" in first_op
            assert "examples" in first_op
            assert "category" in first_op

    def test_catalog_parameter_structure(self, ai_support: AIAgentSupport) -> None:
        """Test that catalog parameters have correct structure."""
        catalog = ai_support.get_operation_catalog()

        if not catalog:
            pytest.skip("No operations in catalog")

        # Find an operation with parameters
        op_with_params = None
        for op_name, op_data in catalog.items():
            if op_data["parameters"]:
                op_with_params = op_data
                break

        if not op_with_params:
            pytest.skip("No operations with parameters found")

        # Verify parameter structure
        param = op_with_params["parameters"][0]
        assert "name" in param
        assert "type" in param
        assert "required" in param
        assert "description" in param
        assert "default" in param

    def test_catalog_is_json_serializable(self, ai_support: AIAgentSupport) -> None:
        """Test that catalog can be serialized to JSON."""
        import json

        catalog = ai_support.get_operation_catalog()

        # Should be JSON-serializable
        try:
            json_str = json.dumps(catalog)
            assert isinstance(json_str, str)
            assert len(json_str) > 0
        except (TypeError, ValueError) as e:
            pytest.fail(f"Catalog is not JSON-serializable: {e}")


class TestStructuredDocumentation:
    """Test structured documentation generation."""

    def test_get_structured_docs_for_known_operation(
        self, ai_support: AIAgentSupport, registry: OperationRegistry
    ) -> None:
        """Test getting structured docs for a known operation."""
        # Get any operation from registry
        operations = registry.get_operation_names()
        if not operations:
            pytest.skip("No operations in registry")

        op_name = operations[0]
        docs = ai_support.get_structured_docs(op_name)

        assert docs is not None
        assert isinstance(docs, StructuredDocumentation)
        assert docs.operation == op_name
        assert docs.summary
        assert docs.description
        assert isinstance(docs.parameters, list)
        assert isinstance(docs.returns, dict)
        assert isinstance(docs.examples, list)
        assert isinstance(docs.related_operations, list)
        assert docs.category

    def test_get_structured_docs_for_unknown_operation(
        self, ai_support: AIAgentSupport
    ) -> None:
        """Test getting structured docs for unknown operation returns None."""
        docs = ai_support.get_structured_docs("nonexistent_operation_xyz")
        assert docs is None

    def test_structured_docs_examples_format(
        self, ai_support: AIAgentSupport, registry: OperationRegistry
    ) -> None:
        """Test that examples are in structured format."""
        operations = registry.get_operation_names()
        if not operations:
            pytest.skip("No operations in registry")

        op_name = operations[0]
        docs = ai_support.get_structured_docs(op_name)

        if docs and docs.examples:
            example = docs.examples[0]
            assert isinstance(example, dict)
            assert "code" in example
            assert "description" in example

    def test_structured_docs_related_operations(
        self, ai_support: AIAgentSupport, registry: OperationRegistry
    ) -> None:
        """Test that related operations are from same category."""
        # Find an operation with a category that has multiple operations
        operations = registry.get_all_operations()
        if len(operations) < 2:
            pytest.skip("Need at least 2 operations")

        # Find a category with multiple operations
        from collections import Counter

        category_counts = Counter(op.category for op in operations)
        multi_op_category = None
        for cat, count in category_counts.items():
            if count > 1:
                multi_op_category = cat
                break

        if not multi_op_category:
            pytest.skip("No category with multiple operations")

        # Get docs for an operation in this category
        op_in_category = next(op for op in operations if op.category == multi_op_category)
        docs = ai_support.get_structured_docs(op_in_category.name)

        assert docs is not None
        # Should have related operations (excluding self)
        if len([op for op in operations if op.category == multi_op_category]) > 1:
            assert len(docs.related_operations) > 0

            # Verify related operations are from same category
            for related_op_name in docs.related_operations:
                related_op = registry.get_operation(related_op_name)
                if related_op:  # May be truncated to 5
                    assert related_op.category == multi_op_category

    def test_structured_docs_limits_related_operations(
        self, ai_support: AIAgentSupport, registry: OperationRegistry
    ) -> None:
        """Test that related operations are limited to 5."""
        operations = registry.get_operation_names()
        if not operations:
            pytest.skip("No operations in registry")

        op_name = operations[0]
        docs = ai_support.get_structured_docs(op_name)

        assert docs is not None
        assert len(docs.related_operations) <= 5


class TestContextAwareSuggestions:
    """Test context-aware operation suggestions."""

    def test_suggestions_for_promote_intent(self, ai_support: AIAgentSupport) -> None:
        """Test suggestions for promote-related intent."""
        suggestions = ai_support.get_context_aware_suggestions("promote heading level")

        # Should return suggestions
        assert isinstance(suggestions, list)

        # If promote operation exists, should suggest it
        if ai_support.registry.operation_exists("promote"):
            assert any(s.operation == "promote" for s in suggestions)

            # Check suggestion structure
            promote_sug = next(s for s in suggestions if s.operation == "promote")
            assert isinstance(promote_sug, OperationSuggestion)
            assert promote_sug.confidence > 0.0
            assert promote_sug.confidence <= 1.0
            assert promote_sug.reason
            assert promote_sug.example

    def test_suggestions_for_demote_intent(self, ai_support: AIAgentSupport) -> None:
        """Test suggestions for demote-related intent."""
        suggestions = ai_support.get_context_aware_suggestions("decrease heading level")

        if ai_support.registry.operation_exists("demote"):
            assert any(s.operation == "demote" for s in suggestions)

    def test_suggestions_for_selection_intent(self, ai_support: AIAgentSupport) -> None:
        """Test suggestions for selection-related intent."""
        suggestions = ai_support.get_context_aware_suggestions("select all headings")

        if ai_support.registry.operation_exists("heading"):
            assert any(s.operation == "heading" for s in suggestions)

        # Should also suggest paragraph if paragraph mentioned
        suggestions = ai_support.get_context_aware_suggestions("find all paragraphs")
        if ai_support.registry.operation_exists("paragraph"):
            assert any(s.operation == "paragraph" for s in suggestions)

    def test_suggestions_for_nesting_intent(self, ai_support: AIAgentSupport) -> None:
        """Test suggestions for nesting-related intent."""
        suggestions = ai_support.get_context_aware_suggestions("nest section under parent")

        if ai_support.registry.operation_exists("nest"):
            assert any(s.operation == "nest" for s in suggestions)

        suggestions = ai_support.get_context_aware_suggestions("unnest and move out")
        if ai_support.registry.operation_exists("unnest"):
            assert any(s.operation == "unnest" for s in suggestions)

    def test_suggestions_max_limit(self, ai_support: AIAgentSupport) -> None:
        """Test that suggestions respect max_suggestions parameter."""
        suggestions = ai_support.get_context_aware_suggestions(
            "select heading and promote", max_suggestions=3
        )

        assert len(suggestions) <= 3

    def test_suggestions_empty_for_unrelated_intent(
        self, ai_support: AIAgentSupport
    ) -> None:
        """Test that unrelated intent returns empty or minimal suggestions."""
        suggestions = ai_support.get_context_aware_suggestions(
            "random unrelated gibberish xyz123"
        )

        # Should return a list (even if empty)
        assert isinstance(suggestions, list)

    def test_suggestions_case_insensitive(self, ai_support: AIAgentSupport) -> None:
        """Test that intent matching is case-insensitive."""
        suggestions_lower = ai_support.get_context_aware_suggestions("promote")
        suggestions_upper = ai_support.get_context_aware_suggestions("PROMOTE")
        suggestions_mixed = ai_support.get_context_aware_suggestions("ProMote")

        # Should all produce same results
        assert len(suggestions_lower) == len(suggestions_upper) == len(suggestions_mixed)

    def test_suggestion_confidence_values(self, ai_support: AIAgentSupport) -> None:
        """Test that confidence values are within valid range."""
        suggestions = ai_support.get_context_aware_suggestions("promote heading")

        for suggestion in suggestions:
            assert 0.0 <= suggestion.confidence <= 1.0

    def test_suggestion_has_example(self, ai_support: AIAgentSupport) -> None:
        """Test that suggestions include usage examples."""
        suggestions = ai_support.get_context_aware_suggestions("select heading")

        if suggestions:
            for suggestion in suggestions:
                assert suggestion.example
                assert isinstance(suggestion.example, str)
                assert len(suggestion.example) > 0
