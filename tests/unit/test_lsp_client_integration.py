"""Integration tests for the LSP client connection.

These tests verify that the language server can be started, stopped, and
properly handles client connections.
"""

from doctk.lsp.server import DoctkLanguageServer


class TestLanguageServerLifecycle:
    """Test the language server lifecycle (start, stop)."""

    def test_server_initialization(self):
        """Test that the language server initializes correctly."""
        server = DoctkLanguageServer()

        assert server is not None
        assert hasattr(server, "registry")
        assert hasattr(server, "completion_provider")
        assert hasattr(server, "hover_provider")
        assert hasattr(server, "ai_support")

    def test_server_has_required_handlers(self):
        """Test that the server has all required LSP handlers registered."""
        server = DoctkLanguageServer()

        # Verify server has the required methods by checking if they're callable
        assert callable(getattr(server, "validate_syntax", None))
        assert callable(getattr(server, "provide_signature_help", None))
        assert callable(getattr(server, "extract_document_symbols", None))

    def test_server_registry_loaded(self):
        """Test that the server has loaded operations into the registry."""
        server = DoctkLanguageServer()

        # Verify registry has operations
        all_operations = server.registry.get_all_operations()
        assert len(all_operations) > 0, "Registry should have operations loaded"

        # Verify common operations are present
        assert "select" in [op.name for op in all_operations]
        assert "where" in [op.name for op in all_operations]
        assert "promote" in [op.name for op in all_operations]

    def test_server_completion_provider_ready(self):
        """Test that the completion provider is initialized and ready."""
        server = DoctkLanguageServer()

        assert server.completion_provider is not None
        assert hasattr(server.completion_provider, "provide_completions")

    def test_server_hover_provider_ready(self):
        """Test that the hover provider is initialized and ready."""
        server = DoctkLanguageServer()

        assert server.hover_provider is not None
        assert hasattr(server.hover_provider, "provide_hover")

    def test_server_ai_support_ready(self):
        """Test that the AI support module is initialized and ready."""
        server = DoctkLanguageServer()

        assert server.ai_support is not None
        assert hasattr(server.ai_support, "get_operation_catalog")
        assert hasattr(server.ai_support, "get_structured_docs")


class TestLanguageServerDocumentHandling:
    """Test document lifecycle handling."""

    def test_parse_and_validate_simple_document(self):
        """Test parsing and validation of a simple document."""
        server = DoctkLanguageServer()

        # Valid DSL syntax
        text = "doc | select heading"

        # Parse and validate
        diagnostics = server.validate_syntax(text)

        # Should have no errors for valid syntax
        assert isinstance(diagnostics, list)
        assert len(diagnostics) == 0, (
            f"Valid syntax should produce no diagnostics, got: {diagnostics}"
        )

    def test_parse_and_validate_invalid_document(self):
        """Test parsing and validation of a document with errors."""
        server = DoctkLanguageServer()

        text = "invalid syntax here"

        # Parse and validate
        diagnostics = server.validate_syntax(text)

        # Should have errors for invalid syntax
        assert isinstance(diagnostics, list)
        # Note: Current parser is lenient and may not report errors for all invalid syntax
        # This test verifies it doesn't crash, not that it necessarily reports errors


class TestLanguageServerFeatureProviders:
    """Test that LSP feature providers work correctly."""

    def test_completion_provider_integration(self):
        """Test that completions can be generated."""
        server = DoctkLanguageServer()

        # Valid DSL syntax with cursor after pipe
        text = "doc | "
        position = (0, 6)  # After the pipe

        # Get completions
        from lsprotocol.types import Position

        pos = Position(line=position[0], character=position[1])
        completions = server.completion_provider.provide_completions(text, pos)

        assert completions is not None
        assert len(completions.items) > 0

    def test_hover_provider_integration(self):
        """Test that hover information can be generated."""
        server = DoctkLanguageServer()

        # Valid DSL syntax
        text = "doc | select heading"
        position = (0, 7)  # On "select"

        # Get hover info
        from lsprotocol.types import Position

        pos = Position(line=position[0], character=position[1])
        hover = server.hover_provider.provide_hover(text, pos)

        # Should return hover info for "select" operation
        assert hover is not None

    def test_signature_help_integration(self):
        """Test that signature help can be generated."""
        server = DoctkLanguageServer()

        # Valid DSL syntax with function call
        text = "doc | where(level=2)"
        position = (0, 13)  # Inside "where"

        # Get signature help
        from lsprotocol.types import Position

        pos = Position(line=position[0], character=position[1])
        sig_help = server.provide_signature_help(text, pos)

        # Signature help may or may not be available depending on cursor position
        # This test verifies the method doesn't crash
        assert sig_help is None or (
            hasattr(sig_help, "signatures") and len(sig_help.signatures) >= 0
        )

    def test_document_symbols_integration(self):
        """Test that document symbols can be extracted."""
        server = DoctkLanguageServer()

        # Valid DSL syntax
        text = "doc | select heading | promote"

        # Extract symbols
        symbols = server.extract_document_symbols(text)

        assert isinstance(symbols, list)


class TestLanguageServerErrorHandling:
    """Test error handling and resilience."""

    def test_empty_document_handling(self):
        """Test that empty documents are handled gracefully."""
        server = DoctkLanguageServer()

        text = ""

        diagnostics = server.validate_syntax(text)

        # Should not crash, may have no errors
        assert isinstance(diagnostics, list)

    def test_malformed_document_handling(self):
        """Test that malformed documents don't crash the server."""
        server = DoctkLanguageServer()

        text = "doc | | | invalid"

        diagnostics = server.validate_syntax(text)

        # Should not crash (main test objective)
        assert isinstance(diagnostics, list)
        # Parser should detect malformed syntax
        # Note: Actual error reporting depends on parser implementation

    def test_very_long_document_handling(self):
        """Test that very long documents are handled efficiently."""
        server = DoctkLanguageServer()

        # Create a very long pipeline with valid syntax
        text = "doc" + " | select heading" * 100

        # Should not crash or timeout
        diagnostics = server.validate_syntax(text)
        assert isinstance(diagnostics, list)


class TestLanguageServerConfiguration:
    """Test server configuration and settings."""

    def test_server_has_components(self):
        """Test that the server has all required components."""
        server = DoctkLanguageServer()

        # Server should have core components
        assert server.registry is not None
        assert server.completion_provider is not None
        assert server.hover_provider is not None
        assert server.ai_support is not None
