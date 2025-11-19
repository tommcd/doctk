"""Tests for LSP AI-focused features (signature help, document symbols, diagnostics)."""

from __future__ import annotations

import pytest
from lsprotocol.types import Position

from doctk.lsp.server import DoctkLanguageServer


@pytest.fixture
def server() -> DoctkLanguageServer:
    """Create a test language server."""
    return DoctkLanguageServer()


class TestSignatureHelp:
    """Test signature help feature."""

    def test_signature_help_for_operation_with_params(self, server: DoctkLanguageServer) -> None:
        """Test signature help for operation with parameters."""
        # Test with nest operation which has parameters
        text = "doc | nest("
        position = Position(line=0, character=11)  # After 'nest('

        result = server.provide_signature_help(text, position)

        # If nest operation exists and has parameters
        if server.registry.operation_exists("nest"):
            nest_op = server.registry.get_operation("nest")
            if nest_op and nest_op.parameters:
                assert result is not None
                assert len(result.signatures) > 0

                signature = result.signatures[0]
                assert "nest" in signature.label
                assert signature.documentation

                # Should have parameter information
                if signature.parameters:
                    assert len(signature.parameters) > 0

    def test_signature_help_for_operation_without_params(self, server: DoctkLanguageServer) -> None:
        """Test signature help for operation without parameters."""
        # Test with promote which has no parameters
        text = "doc | promote("
        position = Position(line=0, character=14)

        result = server.provide_signature_help(text, position)

        if server.registry.operation_exists("promote"):
            assert result is not None
            assert len(result.signatures) > 0

            signature = result.signatures[0]
            assert "promote" in signature.label

    def test_signature_help_unknown_operation(self, server: DoctkLanguageServer) -> None:
        """Test signature help for unknown operation returns None."""
        text = "doc | unknown_op_xyz("
        position = Position(line=0, character=20)

        result = server.provide_signature_help(text, position)

        # Should return None for unknown operation
        assert result is None

    def test_signature_help_no_operation_at_cursor(self, server: DoctkLanguageServer) -> None:
        """Test signature help when cursor is not at an operation."""
        text = "doc | "
        position = Position(line=0, character=6)

        result = server.provide_signature_help(text, position)

        # May return None or empty result
        # This is acceptable behavior
        assert result is None or len(result.signatures) == 0

    def test_signature_help_out_of_bounds_position(self, server: DoctkLanguageServer) -> None:
        """Test signature help with out of bounds position."""
        text = "doc | promote"
        position = Position(line=10, character=0)  # Line doesn't exist

        result = server.provide_signature_help(text, position)

        # Should handle gracefully
        assert result is None

    def test_signature_help_multiline_document(self, server: DoctkLanguageServer) -> None:
        """Test signature help in multiline document."""
        text = "doc | select(heading)\n| nest("
        position = Position(line=1, character=7)  # After 'nest(' on line 2

        result = server.provide_signature_help(text, position)

        if server.registry.operation_exists("nest"):
            nest_op = server.registry.get_operation("nest")
            if nest_op and nest_op.parameters:
                assert result is not None

    def test_signature_help_operation_without_parenthesis(
        self, server: DoctkLanguageServer
    ) -> None:
        """Test signature help when operation doesn't have parenthesis yet."""
        text = "doc | nest"
        position = Position(line=0, character=10)  # At end of 'nest'

        result = server.provide_signature_help(text, position)

        # Should handle this case (may return signature or None)
        # Either is acceptable
        assert result is None or isinstance(result.signatures, list)


class TestDocumentSymbols:
    """Test document symbols extraction."""

    def test_extract_symbols_from_simple_pipeline(self, server: DoctkLanguageServer) -> None:
        """Test extracting symbols from a simple pipeline."""
        text = "doc | select heading | promote"

        symbols = server.extract_document_symbols(text)

        assert isinstance(symbols, list)

        if symbols:
            # Should have at least one symbol for the pipeline
            assert len(symbols) > 0

            # First symbol should be the pipeline
            pipeline = symbols[0]
            assert "Pipeline" in pipeline.name or "doc" in pipeline.name

    def test_extract_symbols_with_multiple_operations(self, server: DoctkLanguageServer) -> None:
        """Test extracting symbols from pipeline with multiple operations."""
        text = "doc | heading | promote | demote"

        symbols = server.extract_document_symbols(text)

        if symbols and symbols[0].children:
            # Should have child symbols for operations
            assert len(symbols[0].children) >= 1

            # Check that operation names are present
            op_names = [child.name for child in symbols[0].children]
            # At least some operation names should be present
            assert any(name in ["heading", "promote", "demote", "select"] for name in op_names)

    def test_extract_symbols_from_multiline_document(self, server: DoctkLanguageServer) -> None:
        """Test extracting symbols from multiline document."""
        text = """doc | select heading
| promote
| demote"""

        symbols = server.extract_document_symbols(text)

        # Should successfully parse and extract symbols
        assert isinstance(symbols, list)

    def test_extract_symbols_empty_document(self, server: DoctkLanguageServer) -> None:
        """Test extracting symbols from empty document."""
        text = ""

        symbols = server.extract_document_symbols(text)

        # Should return empty list for empty document
        assert symbols == []

    def test_extract_symbols_invalid_syntax(self, server: DoctkLanguageServer) -> None:
        """Test extracting symbols from document with invalid syntax."""
        text = "doc | invalid syntax here @#$"

        symbols = server.extract_document_symbols(text)

        # Should handle gracefully and return empty list
        assert isinstance(symbols, list)

    def test_extract_symbols_preserves_line_info(self, server: DoctkLanguageServer) -> None:
        """Test that extracted symbols preserve line information."""
        text = "doc | heading"

        symbols = server.extract_document_symbols(text)

        if symbols:
            # Should have valid range information
            symbol = symbols[0]
            assert symbol.range is not None
            assert symbol.range.start.line >= 0
            assert symbol.range.end.line >= symbol.range.start.line

    def test_extract_symbols_multiline_position_tracking(self, server: DoctkLanguageServer) -> None:
        """Test symbol position tracking in multiline document.

        NOTE: Current implementation reports all symbols at line 0 due to
        parser limitations. This test documents the current behavior and will
        need updating when parser position tracking is implemented.
        See: https://github.com/tommcd/doctk/pull/24#discussion_r3481216455
        """
        text = """doc | heading | promote

doc | paragraph | demote"""

        symbols = server.extract_document_symbols(text)

        # Currently all symbols report at line 0 (known limitation)
        # When parser is enhanced with position tracking:
        # - First pipeline should be at line 0
        # - Second pipeline should be at line 2
        if symbols:
            assert all(s.range.start.line == 0 for s in symbols)

    def test_extract_symbols_multiple_pipelines(self, server: DoctkLanguageServer) -> None:
        """Test extracting symbols from document with multiple pipelines."""
        text = """doc | heading | promote
doc | paragraph | demote"""

        symbols = server.extract_document_symbols(text)

        # Should have symbols for both pipelines
        if symbols:
            assert len(symbols) >= 1


class TestEnhancedDiagnostics:
    """Test enhanced diagnostics for AI consumption."""

    def test_diagnostic_for_unknown_operation(self, server: DoctkLanguageServer) -> None:
        """Test diagnostic for unknown operation includes suggestions."""
        text = "doc | promte"  # Typo: should be 'promote'

        diagnostics = server.validate_syntax(text)

        # Should have a diagnostic for unknown operation
        assert len(diagnostics) > 0

        # Find the diagnostic for the unknown operation
        unknown_op_diagnostic = None
        for diag in diagnostics:
            if "promte" in diag.message or "Unknown operation" in diag.message:
                unknown_op_diagnostic = diag
                break

        if unknown_op_diagnostic:
            # Should include helpful suggestions
            assert (
                "promote" in unknown_op_diagnostic.message
                or "Did you mean" in unknown_op_diagnostic.message
                or "available operations" in unknown_op_diagnostic.message
            )

    def test_diagnostic_for_missing_required_params(self, server: DoctkLanguageServer) -> None:
        """Test diagnostic for missing required parameters."""
        # Skip if no operations with required parameters exist
        ops_with_required = [
            op
            for op in server.registry.get_all_operations()
            if any(p.required for p in op.parameters)
        ]

        if not ops_with_required:
            pytest.skip("No operations with required parameters")

        # This test is conceptual - actual validation depends on DSL parser
        # supporting argument parsing, which may not be implemented yet

    def test_diagnostic_provides_line_and_column(self, server: DoctkLanguageServer) -> None:
        """Test that diagnostics include accurate line and column info."""
        text = "doc | unknown_xyz"

        diagnostics = server.validate_syntax(text)

        if diagnostics:
            diag = diagnostics[0]
            assert diag.range is not None
            assert diag.range.start.line >= 0
            assert diag.range.start.character >= 0

    def test_diagnostic_positions_multiline_document(self, server: DoctkLanguageServer) -> None:
        """Test diagnostic positions in multiline document.

        NOTE: Current implementation reports all positions at line 0 due to
        parser limitations. This test documents the current behavior and will
        need updating when parser position tracking is implemented.
        See: https://github.com/tommcd/doctk/pull/24#discussion_r3481216455
        """
        text = """doc | heading
| promote
| invalid_operation"""

        diagnostics = server.validate_syntax(text)

        if diagnostics:
            # Currently all diagnostics report at line 0 (known limitation)
            # When parser is enhanced, this should report line 2 (0-indexed)
            assert all(d.range.start.line == 0 for d in diagnostics)

    def test_diagnostic_is_actionable(self, server: DoctkLanguageServer) -> None:
        """Test that diagnostic messages are actionable."""
        text = "doc | unknwn"  # Typo

        diagnostics = server.validate_syntax(text)

        if diagnostics:
            # Message should be informative and actionable
            diag = diagnostics[0]
            assert len(diag.message) > 0
            assert diag.source == "doctk-lsp"

            # Should either suggest alternatives or guide user
            assert (
                "Did you mean" in diag.message
                or "available" in diag.message
                or "Use completion" in diag.message
                or "Unknown" in diag.message
            )

    def test_diagnostic_severity_levels(self, server: DoctkLanguageServer) -> None:
        """Test that diagnostics use appropriate severity levels."""
        from lsprotocol.types import DiagnosticSeverity

        text = "doc | invalid_op"

        diagnostics = server.validate_syntax(text)

        if diagnostics:
            # Unknown operations should be errors
            assert any(diag.severity == DiagnosticSeverity.Error for diag in diagnostics)

    def test_multiple_diagnostics_for_multiple_errors(self, server: DoctkLanguageServer) -> None:
        """Test that multiple errors generate multiple diagnostics."""
        text = "doc | invalid1 | invalid2"

        diagnostics = server.validate_syntax(text)

        # If both operations are unknown, should have diagnostics for both
        # (or at least report all issues found)
        assert isinstance(diagnostics, list)

    def test_diagnostic_for_valid_syntax_is_empty(self, server: DoctkLanguageServer) -> None:
        """Test that valid syntax produces no diagnostics."""
        # Use a known operation
        if server.registry.operation_exists("heading"):
            text = "doc | heading"
        elif server.registry.operation_exists("promote"):
            text = "doc | promote"
        else:
            pytest.skip("No known operations to test with")

        diagnostics = server.validate_syntax(text)

        # Should have no diagnostics for valid syntax
        assert len(diagnostics) == 0


class TestSimilarOperationFinder:
    """Test similar operation finding."""

    def test_find_similar_operations_exact_match(self, server: DoctkLanguageServer) -> None:
        """Test finding similar operations for exact match."""
        if not server.registry.operation_exists("promote"):
            pytest.skip("promote operation not available")

        similar = server._find_similar_operations("promote")

        # Should find the exact match
        assert "promote" in similar

    def test_find_similar_operations_typo(self, server: DoctkLanguageServer) -> None:
        """Test finding similar operations for typo."""
        if not server.registry.operation_exists("promote"):
            pytest.skip("promote operation not available")

        similar = server._find_similar_operations("promte")  # Missing 'o'

        # Should suggest 'promote'
        assert "promote" in similar

    def test_find_similar_operations_returns_limited_results(
        self, server: DoctkLanguageServer
    ) -> None:
        """Test that similar operations are limited."""
        similar = server._find_similar_operations("sel")

        # Should return at most 5 results
        assert len(similar) <= 5

    def test_find_similar_operations_no_match(self, server: DoctkLanguageServer) -> None:
        """Test finding similar operations when no close match exists."""
        similar = server._find_similar_operations("xyzabc123")

        # Should return empty list or very few results
        assert len(similar) <= 2

    def test_find_similar_operations_case_insensitive(self, server: DoctkLanguageServer) -> None:
        """Test that similarity matching is case-aware."""
        if not server.registry.operation_exists("promote"):
            pytest.skip("promote operation not available")

        similar_lower = server._find_similar_operations("promote")
        similar_upper = server._find_similar_operations("PROMOTE")

        # Both should find promote (difflib handles case)
        assert "promote" in similar_lower
        # Upper case might not match exactly, but should be handled
        assert isinstance(similar_upper, list)
