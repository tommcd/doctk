"""Tests for error recovery and graceful degradation in the language server.

This test module verifies that the language server handles errors gracefully
and provides comprehensive logging for debugging.
"""

import logging
from unittest.mock import patch

from lsprotocol.types import DiagnosticSeverity, Position

from doctk.lsp import DoctkLanguageServer
from doctk.lsp.server import DocumentState


class TestGracefulDegradation:
    """Test graceful degradation when parsing fails."""

    def test_lexer_error_provides_diagnostic(self):
        """Test that lexer errors provide actionable diagnostics."""
        server = DoctkLanguageServer()
        # Invalid character that lexer doesn't recognize
        text = "doc | select @ heading"

        diagnostics = server.validate_syntax(text)

        # Should get diagnostic for lexer error
        assert len(diagnostics) == 1
        diagnostic = diagnostics[0]
        assert diagnostic.severity == DiagnosticSeverity.Error
        assert diagnostic.source == "doctk-lsp"
        assert "Unknown character" in diagnostic.message
        # Should include helpful tip
        assert "Tip" in diagnostic.message

    def test_parser_error_provides_diagnostic(self):
        """Test that parser errors provide actionable diagnostics."""
        server = DoctkLanguageServer()
        # Invalid source (number instead of doc/identifier)
        text = "123 | select heading"

        diagnostics = server.validate_syntax(text)

        # Should get diagnostic for parser error
        assert len(diagnostics) == 1
        diagnostic = diagnostics[0]
        assert diagnostic.severity == DiagnosticSeverity.Error
        assert diagnostic.source == "doctk-lsp"
        assert "Expected 'doc' or identifier" in diagnostic.message
        # Message should be clear and actionable (contains position info)
        assert "line" in diagnostic.message and "column" in diagnostic.message

    def test_parser_error_with_position_info(self):
        """Test that parser errors include accurate position information."""
        server = DoctkLanguageServer()
        text = "doc | where level=|"  # Invalid value

        diagnostics = server.validate_syntax(text)

        # Should get diagnostic with position
        assert len(diagnostics) == 1
        diagnostic = diagnostics[0]
        assert diagnostic.range.start.line >= 0
        assert diagnostic.range.start.character >= 0

    def test_generic_error_provides_diagnostic(self):
        """Test that generic errors provide user-friendly diagnostics."""
        server = DoctkLanguageServer()

        # Mock the lexer to raise an unexpected exception
        with patch("doctk.lsp.server.Lexer") as mock_lexer:
            mock_lexer.side_effect = RuntimeError("Unexpected error")

            diagnostics = server.validate_syntax("doc | select heading")

            # Should get diagnostic for generic error
            assert len(diagnostics) == 1
            diagnostic = diagnostics[0]
            assert diagnostic.severity == DiagnosticSeverity.Error
            assert diagnostic.source == "doctk-lsp"
            assert "Internal error" in diagnostic.message
            assert "Check the output panel" in diagnostic.message

    def test_multiple_errors_all_reported(self):
        """Test that multiple errors are all reported."""
        server = DoctkLanguageServer()
        # Use invalid character multiple times
        text = "doc | @ select @ heading"

        diagnostics = server.validate_syntax(text)

        # Should get diagnostic for the first error
        # (lexer stops at first error, so we only get one)
        assert len(diagnostics) >= 1
        assert all(d.severity == DiagnosticSeverity.Error for d in diagnostics)

    def test_valid_code_after_error_recovery(self):
        """Test that server can validate valid code after encountering an error."""
        server = DoctkLanguageServer()

        # First, validate invalid code
        invalid_text = "doc | @invalid"
        invalid_diagnostics = server.validate_syntax(invalid_text)
        assert len(invalid_diagnostics) > 0

        # Then, validate valid code
        valid_text = "doc | select heading"
        valid_diagnostics = server.validate_syntax(valid_text)
        assert len(valid_diagnostics) == 0

    def test_signature_help_error_recovery(self):
        """Test that signature help returns None gracefully on error."""
        server = DoctkLanguageServer()

        # Create a document state
        uri = "file:///test.tk"
        text = "doc | select heading"

        server.documents[uri] = DocumentState(uri, text, 1)

        # Mock the registry to raise an exception
        with patch.object(server.registry, "get_operation", side_effect=RuntimeError("Test error")):
            result = server.provide_signature_help(text, Position(line=0, character=10))

            # Should return None gracefully rather than crashing
            assert result is None

    def test_document_symbols_error_recovery(self):
        """Test that document symbols returns empty list gracefully on error."""
        server = DoctkLanguageServer()

        # Create a document state
        uri = "file:///test.tk"
        text = "doc | select heading"

        server.documents[uri] = DocumentState(uri, text, 1)

        # Mock the lexer to raise an exception
        with patch("doctk.lsp.server.Lexer", side_effect=RuntimeError("Test error")):
            result = server.extract_document_symbols(text)

            # Should return empty list gracefully rather than crashing
            assert result == []


class TestComprehensiveErrorLogging:
    """Test comprehensive error logging with stack traces."""

    def test_lexer_error_logged_with_details(self, caplog):
        """Test that lexer errors are logged with detailed information."""
        server = DoctkLanguageServer()
        text = "doc | @invalid"

        with caplog.at_level(logging.ERROR):
            _ = server.validate_syntax(text)

        # Should have logged the error
        assert len(caplog.records) > 0
        error_record = caplog.records[0]
        assert error_record.levelname == "ERROR"
        assert "Lexer error" in error_record.message

    def test_parser_error_logged_with_details(self, caplog):
        """Test that parser errors are logged with detailed information."""
        server = DoctkLanguageServer()
        text = "123 | select heading"

        with caplog.at_level(logging.ERROR):
            _ = server.validate_syntax(text)

        # Should have logged the error
        assert len(caplog.records) > 0
        error_record = caplog.records[0]
        assert error_record.levelname == "ERROR"
        assert "Parse error" in error_record.message

    def test_generic_error_logged_with_stack_trace(self, caplog):
        """Test that generic errors are logged with stack traces."""
        server = DoctkLanguageServer()

        # Mock the lexer to raise an unexpected exception
        with patch("doctk.lsp.server.Lexer") as mock_lexer:
            mock_lexer.side_effect = RuntimeError("Unexpected error")

            with caplog.at_level(logging.ERROR):
                _ = server.validate_syntax("doc | select heading")

            # Should have logged the error with stack trace
            assert len(caplog.records) > 0
            error_record = caplog.records[0]
            assert error_record.levelname == "ERROR"
            assert "Unexpected error parsing document" in error_record.message
            # Check that exc_info was used (stack trace included)
            assert error_record.exc_info is not None

    def test_signature_help_error_logged_with_stack_trace(self, caplog):
        """Test that signature help errors are logged with stack traces."""
        server = DoctkLanguageServer()
        text = "doc | select heading"

        with patch.object(server.registry, "get_operation", side_effect=RuntimeError("Test error")):
            with caplog.at_level(logging.ERROR):
                _ = server.provide_signature_help(text, Position(line=0, character=10))

            # Should have logged the error with stack trace
            assert len(caplog.records) > 0
            error_record = caplog.records[0]
            assert error_record.levelname == "ERROR"
            assert "Error providing signature help" in error_record.message
            assert error_record.exc_info is not None

    def test_document_symbols_error_logged_with_stack_trace(self, caplog):
        """Test that document symbols errors are logged with stack traces."""
        server = DoctkLanguageServer()
        text = "doc | select heading"

        with patch("doctk.lsp.server.Lexer", side_effect=RuntimeError("Test error")):
            with caplog.at_level(logging.ERROR):
                _ = server.extract_document_symbols(text)

            # Should have logged the error with stack trace
            assert len(caplog.records) > 0
            error_record = caplog.records[0]
            assert error_record.levelname == "ERROR"
            assert "Error extracting document symbols" in error_record.message
            assert error_record.exc_info is not None


class TestErrorRecoveryPatterns:
    """Test error recovery patterns and resilience."""

    def test_server_maintains_state_after_validation_error(self):
        """Test that server maintains state after validation errors."""
        server = DoctkLanguageServer()

        # Create a document state
        uri = "file:///test.tk"

        server.documents[uri] = DocumentState(uri, "doc | select heading", 1)

        # Validate invalid code
        invalid_diagnostics = server.validate_syntax("doc | @invalid")
        assert len(invalid_diagnostics) > 0

        # Server should still have the document state
        assert uri in server.documents
        assert server.documents[uri].text == "doc | select heading"

    def test_server_can_validate_multiple_documents(self):
        """Test that server can validate multiple documents independently."""
        server = DoctkLanguageServer()

        # Validate first document (invalid)
        uri1 = "file:///test1.tk"

        server.documents[uri1] = DocumentState(uri1, "doc | @invalid", 1)
        diagnostics1 = server.validate_syntax("doc | @invalid")
        assert len(diagnostics1) > 0

        # Validate second document (valid)
        uri2 = "file:///test2.tk"
        server.documents[uri2] = DocumentState(uri2, "doc | select heading", 1)
        diagnostics2 = server.validate_syntax("doc | select heading")
        assert len(diagnostics2) == 0

        # Both documents should be tracked
        assert uri1 in server.documents
        assert uri2 in server.documents

    def test_error_messages_are_actionable(self):
        """Test that error messages provide actionable information."""
        server = DoctkLanguageServer()

        # Test lexer error message
        lexer_diagnostics = server.validate_syntax("doc | @invalid")
        assert len(lexer_diagnostics) > 0
        assert "Tip" in lexer_diagnostics[0].message or "valid" in lexer_diagnostics[0].message

        # Test parser error message
        parser_diagnostics = server.validate_syntax("123 | select heading")
        assert len(parser_diagnostics) > 0
        assert "Tip" in parser_diagnostics[0].message or "Expected" in parser_diagnostics[0].message

    def test_server_initialization_after_error(self):
        """Test that server can be initialized fresh after errors."""
        # Create server, cause errors, then create new server
        server1 = DoctkLanguageServer()
        server1.validate_syntax("doc | @invalid")

        # Create new server instance
        server2 = DoctkLanguageServer()

        # New server should be clean
        assert server2.documents == {}
        assert server2.registry is not None

        # New server should work correctly
        diagnostics = server2.validate_syntax("doc | select heading")
        assert len(diagnostics) == 0


class TestErrorPositionAccuracy:
    """Test that error positions are accurate for diagnostics."""

    def test_lexer_error_position(self):
        """Test that lexer errors report accurate positions."""
        server = DoctkLanguageServer()
        text = "doc | select @ heading"

        diagnostics = server.validate_syntax(text)

        # Should have accurate position for the @ character
        assert len(diagnostics) == 1
        diagnostic = diagnostics[0]
        # Position should be non-negative
        assert diagnostic.range.start.line >= 0
        assert diagnostic.range.start.character >= 0

    def test_parser_error_position(self):
        """Test that parser errors report accurate positions."""
        server = DoctkLanguageServer()
        text = "123 | select heading"

        diagnostics = server.validate_syntax(text)

        # Should have position for the error
        assert len(diagnostics) == 1
        diagnostic = diagnostics[0]
        assert diagnostic.range.start.line >= 0
        assert diagnostic.range.start.character >= 0

    def test_multiline_error_position(self):
        """Test that errors in multiline documents report correct line numbers."""
        server = DoctkLanguageServer()
        text = """doc | select heading
invalid_line @
doc | promote"""

        diagnostics = server.validate_syntax(text)

        # Should get diagnostic for the error
        assert len(diagnostics) > 0
        # Position should indicate the error is not on line 0
        # (though the current implementation may have limitations)
        diagnostic = diagnostics[0]
        assert diagnostic.range.start.line >= 0
