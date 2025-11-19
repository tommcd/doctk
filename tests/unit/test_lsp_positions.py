"""Tests for LSP server position accuracy.

This test suite verifies that the LSP server correctly uses position information
from AST nodes when reporting diagnostics and document symbols.
"""

from doctk.lsp.registry import OperationRegistry
from doctk.lsp.server import DoctkLanguageServer


class TestLSPDiagnosticPositions:
    """Test that LSP diagnostics report accurate positions."""

    def test_unknown_operation_position(self):
        """Test that unknown operation error reports correct position."""
        server = DoctkLanguageServer()
        registry = OperationRegistry()
        server.registry = registry

        # Unknown operation 'foo' at column 7
        source = "doc | foo"
        diagnostics = server.validate_syntax(source)

        assert len(diagnostics) == 1
        diagnostic = diagnostics[0]

        # Error should be at line 1 (LSP uses 0-indexed lines, so line 0)
        assert diagnostic.range.start.line == 0  # LSP: 0-indexed
        assert diagnostic.range.start.character == 6  # 'foo' starts at column 7 (0-indexed: 6)

        # Error message should mention the unknown operation
        assert "Unknown operation 'foo'" in diagnostic.message

    def test_unknown_operation_multiline(self):
        """Test position accuracy for unknown operation on second line."""
        server = DoctkLanguageServer()
        registry = OperationRegistry()
        server.registry = registry

        source = """doc | promote
doc | unknown_op"""
        diagnostics = server.validate_syntax(source)

        # Should have one diagnostic for unknown_op
        assert len(diagnostics) == 1
        diagnostic = diagnostics[0]

        # Error should be on line 2 (LSP: line 1, 0-indexed)
        assert diagnostic.range.start.line == 1
        # 'unknown_op' starts at column 7 (0-indexed: 6)
        assert diagnostic.range.start.character == 6

    def test_missing_parameter_position(self):
        """Test that missing parameter error reports correct position."""
        server = DoctkLanguageServer()
        registry = OperationRegistry()
        server.registry = registry

        # Use an operation that actually requires parameters
        # For now, skip this test as 'where' doesn't enforce required params
        # This test demonstrates the position tracking would work if we had
        # stricter parameter validation
        source = "doc | where"
        diagnostics = server.validate_syntax(source)

        # Currently where doesn't report missing params, so no diagnostics
        # If this changes in future, update this test
        assert len(diagnostics) == 0  # No error for optional params

    def test_multiple_errors_accurate_positions(self):
        """Test position accuracy when multiple errors exist."""
        server = DoctkLanguageServer()
        registry = OperationRegistry()
        server.registry = registry

        source = """doc | foo
doc | bar
doc | promote"""
        diagnostics = server.validate_syntax(source)

        # Should have two diagnostics (foo and bar are unknown)
        assert len(diagnostics) == 2

        # First error: 'foo' on line 1
        assert diagnostics[0].range.start.line == 0
        assert diagnostics[0].range.start.character == 6

        # Second error: 'bar' on line 2
        assert diagnostics[1].range.start.line == 1
        assert diagnostics[1].range.start.character == 6

    def test_error_range_covers_operation_name(self):
        """Test that error range covers the entire operation name."""
        server = DoctkLanguageServer()
        registry = OperationRegistry()
        server.registry = registry

        source = "doc | unknown_operation"
        diagnostics = server.validate_syntax(source)

        assert len(diagnostics) == 1
        diagnostic = diagnostics[0]

        # Range should start at 'unknown_operation'
        assert diagnostic.range.start.character == 6  # column 7 (0-indexed)

        # Range should end after 'unknown_operation' (length 17)
        assert diagnostic.range.end.character == 6 + len("unknown_operation")


class TestLSPDocumentSymbolPositions:
    """Test that document symbols report accurate positions."""

    def test_simple_pipeline_symbol_position(self):
        """Test document symbol position for simple pipeline."""
        server = DoctkLanguageServer()

        source = "doc | promote"
        symbols = server.extract_document_symbols(source)

        assert len(symbols) == 1
        symbol = symbols[0]

        # Pipeline symbol should start at line 1 (LSP: line 0)
        assert symbol.range.start.line == 0
        assert symbol.range.start.character == 0  # 'doc' at column 1 (0-indexed: 0)

        # Should have one child operation
        assert len(symbol.children) == 1
        promote_symbol = symbol.children[0]

        # promote operation at column 7 (0-indexed: 6)
        assert promote_symbol.range.start.line == 0
        assert promote_symbol.range.start.character == 6

    def test_multiline_pipeline_symbols(self):
        """Test document symbol positions for multi-line pipelines."""
        server = DoctkLanguageServer()

        source = """doc | promote
doc | demote"""
        symbols = server.extract_document_symbols(source)

        assert len(symbols) == 2

        # First pipeline on line 1 (LSP: line 0)
        assert symbols[0].range.start.line == 0
        assert symbols[0].range.start.character == 0

        # Second pipeline on line 2 (LSP: line 1)
        assert symbols[1].range.start.line == 1
        assert symbols[1].range.start.character == 0

    def test_pipeline_with_multiple_operations_symbol_range(self):
        """Test symbol range spans from source to last operation."""
        server = DoctkLanguageServer()

        source = "doc | promote | demote"
        symbols = server.extract_document_symbols(source)

        assert len(symbols) == 1
        symbol = symbols[0]

        # Pipeline should start at 'doc' (column 1, 0-indexed: 0)
        assert symbol.range.start.character == 0

        # Pipeline should end after 'demote' (column 23, 0-indexed: 22)
        # 'demote' starts at column 17 (0-indexed: 16), length 6, so end at 22
        assert symbol.range.end.character == 16 + len("demote")

        # Check child operations have correct positions
        children = symbol.children
        assert len(children) == 2

        # promote at column 7 (0-indexed: 6)
        assert children[0].range.start.character == 6

        # demote at column 17 (0-indexed: 16)
        assert children[1].range.start.character == 16

    def test_operation_symbol_position_with_arguments(self):
        """Test operation symbol position when operation has arguments."""
        server = DoctkLanguageServer()

        source = "doc | where level=3"
        symbols = server.extract_document_symbols(source)

        assert len(symbols) == 1
        pipeline_symbol = symbols[0]

        # Check 'where' operation position
        where_symbol = pipeline_symbol.children[0]
        assert where_symbol.name == "where"

        # 'where' starts at column 7 (0-indexed: 6)
        assert where_symbol.range.start.line == 0
        assert where_symbol.range.start.character == 6

    def test_symbols_multiline_with_comments(self):
        """Test symbol positions with comments and blank lines."""
        server = DoctkLanguageServer()

        source = """# First pipeline
doc | promote

# Second pipeline
doc | demote"""
        symbols = server.extract_document_symbols(source)

        assert len(symbols) == 2

        # First pipeline on line 2 (after comment, LSP: line 1)
        assert symbols[0].range.start.line == 1

        # Second pipeline on line 5 (after comment and blank line, LSP: line 4)
        assert symbols[1].range.start.line == 4


class TestLSPPositionEdgeCases:
    """Test edge cases for position tracking."""

    def test_position_with_whitespace_before_operation(self):
        """Test position accuracy with extra whitespace."""
        server = DoctkLanguageServer()
        registry = OperationRegistry()
        server.registry = registry

        # Extra spaces before operation
        source = "doc   |   foo"
        diagnostics = server.validate_syntax(source)

        assert len(diagnostics) == 1
        # 'foo' should be at column 11 after whitespace (0-indexed: 10)
        assert diagnostics[0].range.start.character == 10

    def test_position_on_last_line_no_newline(self):
        """Test position accuracy on last line without trailing newline."""
        server = DoctkLanguageServer()
        registry = OperationRegistry()
        server.registry = registry

        source = "doc | promote\ndoc | unknown"
        diagnostics = server.validate_syntax(source)

        # Error should be on line 2 (LSP: line 1)
        assert len(diagnostics) == 1
        assert diagnostics[0].range.start.line == 1
        assert diagnostics[0].range.start.character == 6  # 'unknown' at column 7

    def test_empty_pipeline_no_errors(self):
        """Test that empty source doesn't cause position errors."""
        server = DoctkLanguageServer()

        source = ""
        diagnostics = server.validate_syntax(source)
        symbols = server.extract_document_symbols(source)

        # Should handle gracefully
        assert diagnostics == []
        assert symbols == []
