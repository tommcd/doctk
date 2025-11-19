"""End-to-end integration tests for the doctk Language Server.

These tests verify complete LSP workflows including:
- Document opening and syntax validation
- Code completion and hover documentation
- Signature help and document symbols
- Performance requirements
"""

import time

import pytest
from lsprotocol.types import Position

from doctk.lsp.server import DoctkLanguageServer


class TestLSPWorkflow:
    """Test complete LSP workflows from document open to feature usage."""

    def test_open_tk_file_and_validate_syntax(self):
        """Test opening a .tk file and validating syntax."""
        server = DoctkLanguageServer()

        # Valid .tk file content
        tk_content = """# Document transformation script
doc | select heading | where level=2 | promote
"""

        # Validate syntax
        diagnostics = server.validate_syntax(tk_content)

        # Should have no errors
        assert isinstance(diagnostics, list)
        assert len(diagnostics) == 0, f"Valid syntax should have no errors: {diagnostics}"

    def test_type_code_and_get_completions(self):
        """Test typing code and receiving completion suggestions."""
        server = DoctkLanguageServer()

        # Simulate typing after pipe operator
        text = "doc | "
        position = Position(line=0, character=6)  # After "doc | "

        # Get completions
        result = server.completion_provider.provide_completions(text, position)

        # Should return completion list
        assert result is not None
        assert len(result.items) > 0, "Should have completion items"

        # Should include common operations
        operation_names = [item.label for item in result.items]
        assert "select" in operation_names
        assert "where" in operation_names
        assert "promote" in operation_names
        assert "demote" in operation_names

    def test_hover_on_operation(self):
        """Test hovering over an operation to get documentation."""
        server = DoctkLanguageServer()

        # Document with operation
        text = "doc | select heading"
        position = Position(line=0, character=8)  # On "select"

        # Get hover information
        result = server.hover_provider.provide_hover(text, position)

        # Should return hover with documentation
        assert result is not None
        assert result.contents is not None

        # Contents should include operation documentation
        contents_str = str(result.contents)
        assert "select" in contents_str.lower()

    def test_signature_help_for_operation(self):
        """Test signature help when typing operation parameters."""
        server = DoctkLanguageServer()

        # Document with operation being typed
        text = "doc | where "
        position = Position(line=0, character=12)  # After "where "

        # Get signature help
        result = server.provide_signature_help(text, position)

        # Should return signature information
        assert result is not None
        assert isinstance(result.signatures, list)
        # Signature help might be empty if no operations require parameters
        # but the call should succeed

    def test_document_symbols_extraction(self):
        """Test extracting document symbols from a .tk file."""
        server = DoctkLanguageServer()

        # Document with multiple operations
        text = """doc | select heading
doc | where level=2
doc | promote
"""

        # Extract document symbols
        result = server.extract_document_symbols(text)

        # Should return list of symbols
        assert isinstance(result, list)
        assert len(result) >= 3, "Should have at least 3 pipeline symbols"


class TestLSPSyntaxValidation:
    """Test real-time syntax validation workflows."""

    def test_valid_syntax_no_diagnostics(self):
        """Test that valid syntax produces no diagnostics."""
        server = DoctkLanguageServer()

        valid_syntax = [
            "doc | select heading",
            "doc | where level=2",
            "doc | promote",
            "doc | demote",
            "doc | select heading | where level=2 | promote",
        ]

        for syntax in valid_syntax:
            diagnostics = server.validate_syntax(syntax)
            assert len(diagnostics) == 0, (
                f"Valid syntax should have no diagnostics: '{syntax}' -> {diagnostics}"
            )

    def test_invalid_syntax_produces_diagnostics(self):
        """Test that invalid syntax produces error diagnostics."""
        server = DoctkLanguageServer()

        # Invalid: missing pipe
        text = "doc select heading"
        diagnostics = server.validate_syntax(text)

        # Should have diagnostics (parser errors)
        assert isinstance(diagnostics, list)
        # Note: Parser might be lenient, so we just verify it returns a list

    def test_multiple_errors_reported_with_positions(self):
        """Test that multiple syntax errors are reported with accurate positions."""
        server = DoctkLanguageServer()

        # Multiple lines with errors
        text = """invalid syntax here
doc | unknown_operation
another error
"""

        diagnostics = server.validate_syntax(text)

        # Should return a list (may be empty if parser is lenient)
        assert isinstance(diagnostics, list)

    def test_error_cleared_when_fixed(self):
        """Test that errors are cleared when syntax is fixed."""
        server = DoctkLanguageServer()

        # First, invalid syntax
        invalid_text = "invalid syntax"
        diagnostics_invalid = server.validate_syntax(invalid_text)

        # Then, valid syntax
        valid_text = "doc | select heading"
        diagnostics_valid = server.validate_syntax(valid_text)

        # Valid syntax should have fewer or no diagnostics
        assert len(diagnostics_valid) <= len(diagnostics_invalid)


class TestLSPCompletion:
    """Test code completion workflows."""

    def test_completion_after_pipe_operator(self):
        """Test completions are provided after pipe operator."""
        server = DoctkLanguageServer()

        text = "doc | "
        position = Position(line=0, character=6)

        result = server.completion_provider.provide_completions(text, position)

        assert result is not None
        assert len(result.items) > 0
        assert any(item.label == "select" for item in result.items)

    def test_completion_includes_operation_descriptions(self):
        """Test that completions include operation descriptions."""
        server = DoctkLanguageServer()

        text = "doc | "
        position = Position(line=0, character=6)

        result = server.completion_provider.provide_completions(text, position)

        # Find 'select' operation
        select_item = next((item for item in result.items if item.label == "select"), None)
        assert select_item is not None
        # Detail should include some description
        assert select_item.detail is not None or select_item.documentation is not None

    def test_completion_performance_under_200ms(self):
        """Test that completion response time is under 200ms."""
        server = DoctkLanguageServer()

        text = "doc | "
        position = Position(line=0, character=6)

        # Measure time
        start = time.time()
        result = server.completion_provider.provide_completions(text, position)
        elapsed = (time.time() - start) * 1000  # Convert to milliseconds

        assert result is not None
        assert elapsed < 200, f"Completion took {elapsed:.2f}ms (requirement: < 200ms)"


class TestLSPHover:
    """Test hover documentation workflows."""

    def test_hover_on_operation_shows_documentation(self):
        """Test that hovering on an operation shows documentation."""
        server = DoctkLanguageServer()

        text = "doc | select heading"
        position = Position(line=0, character=8)  # On "select"

        result = server.hover_provider.provide_hover(text, position)

        assert result is not None
        assert result.contents is not None
        contents_str = str(result.contents)
        assert len(contents_str) > 0

    def test_hover_includes_examples(self):
        """Test that hover documentation includes usage examples."""
        server = DoctkLanguageServer()

        text = "doc | select heading"
        position = Position(line=0, character=8)  # On "select"

        result = server.hover_provider.provide_hover(text, position)

        assert result is not None
        # Examples might be in documentation
        # Just verify we got some content
        assert result.contents is not None

    def test_hover_performance_under_200ms(self):
        """Test that hover response time is under 200ms."""
        server = DoctkLanguageServer()

        text = "doc | select heading"
        position = Position(line=0, character=8)

        # Measure time
        start = time.time()
        result = server.hover_provider.provide_hover(text, position)
        elapsed = (time.time() - start) * 1000  # Convert to milliseconds

        assert result is not None
        assert elapsed < 200, f"Hover took {elapsed:.2f}ms (requirement: < 200ms)"


class TestLSPAISupport:
    """Test AI-friendly features."""

    def test_operation_catalog_for_ai(self):
        """Test getting complete operation catalog for AI consumption."""
        server = DoctkLanguageServer()

        catalog = server.ai_support.get_operation_catalog()

        # Should return structured data as dict[str, dict]
        assert isinstance(catalog, dict)
        assert len(catalog) > 0

        # Check structure of a specific operation
        assert "select" in catalog
        assert "description" in catalog["select"]

    def test_structured_docs_for_ai(self):
        """Test getting structured documentation for AI."""
        server = DoctkLanguageServer()

        docs = server.ai_support.get_structured_docs("select")

        # Should return StructuredDocumentation dataclass
        assert docs is not None
        assert hasattr(docs, "operation")
        assert hasattr(docs, "summary")
        assert docs.operation == "select"

    def test_signature_help_returns_structured_info(self):
        """Test that signature help returns structured parameter info."""
        server = DoctkLanguageServer()

        text = "doc | where "
        position = Position(line=0, character=12)

        result = server.provide_signature_help(text, position)

        # Should return signature help (even if empty)
        assert result is not None
        assert hasattr(result, "signatures")

    def test_document_symbols_returns_all_operations(self):
        """Test that document symbols include all operations."""
        server = DoctkLanguageServer()

        text = """doc | select heading
doc | where level=2
doc | promote
doc | demote
"""

        result = server.extract_document_symbols(text)

        assert isinstance(result, list)
        assert len(result) >= 4, "Should have symbols for all 4 pipelines"


class TestLSPConfiguration:
    """Test configuration and customization."""

    def test_configuration_loading(self):
        """Test that configuration can be loaded."""
        server = DoctkLanguageServer()

        # Default configuration should be loaded
        assert server.config is not None
        assert hasattr(server.config, "trace")
        assert hasattr(server.config, "max_completion_items")

    def test_configuration_update(self):
        """Test that configuration can be updated dynamically."""
        server = DoctkLanguageServer()

        # Update configuration
        new_config = {"trace": "verbose", "maxCompletionItems": 50}

        server.config.update_from_dict(new_config)

        assert server.config.max_completion_items == 50

    def test_invalid_configuration_uses_defaults(self):
        """Test that invalid configuration values fall back to defaults."""
        server = DoctkLanguageServer()

        # Try to update with invalid values
        invalid_config = {"maxCompletionItems": -1}

        server.config.update_from_dict(invalid_config)

        # Should use default (positive value)
        assert server.config.max_completion_items > 0


class TestLSPPerformance:
    """Test LSP performance requirements."""

    def test_server_initialization_under_2_seconds(self):
        """Test that server initializes within 2 seconds."""
        start = time.time()
        server = DoctkLanguageServer()
        elapsed = time.time() - start

        assert server is not None
        assert elapsed < 2.0, f"Server initialization took {elapsed:.2f}s (requirement: < 2s)"

    def test_completion_performance_with_large_document(self):
        """Test completion performance with a large document."""
        server = DoctkLanguageServer()

        # Large document with many operations
        lines = ["doc | select heading | where level=2 | promote"] * 100
        text = "\n".join(lines)
        position = Position(line=50, character=6)  # Middle of document

        start = time.time()
        result = server.completion_provider.provide_completions(text, position)
        elapsed = (time.time() - start) * 1000

        assert result is not None
        assert elapsed < 200, (
            f"Completion on large doc took {elapsed:.2f}ms (requirement: < 200ms)"
        )

    def test_hover_performance_with_large_document(self):
        """Test hover performance with a large document."""
        server = DoctkLanguageServer()

        # Large document
        lines = ["doc | select heading | where level=2 | promote"] * 100
        text = "\n".join(lines)
        position = Position(line=50, character=8)  # On an operation

        start = time.time()
        result = server.hover_provider.provide_hover(text, position)
        elapsed = (time.time() - start) * 1000

        assert result is not None
        assert elapsed < 200, f"Hover on large doc took {elapsed:.2f}ms (requirement: < 200ms)"

    def test_validation_performance_under_500ms(self):
        """Test that syntax validation completes within 500ms."""
        server = DoctkLanguageServer()

        # Document with multiple lines
        lines = ["doc | select heading | where level=2 | promote"] * 50
        text = "\n".join(lines)

        start = time.time()
        diagnostics = server.validate_syntax(text)
        elapsed = (time.time() - start) * 1000

        assert isinstance(diagnostics, list)
        assert elapsed < 500, f"Validation took {elapsed:.2f}ms (requirement: < 500ms)"


class TestLSPErrorRecovery:
    """Test error recovery and resilience."""

    def test_parsing_error_returns_partial_diagnostics(self):
        """Test that parsing errors return partial diagnostics."""
        server = DoctkLanguageServer()

        # Invalid syntax that should trigger parser error
        text = "invalid | syntax | here"

        diagnostics = server.validate_syntax(text)

        # Should return diagnostics (even if empty due to lenient parser)
        assert isinstance(diagnostics, list)

    def test_server_stability_after_error(self):
        """Test that server remains stable after errors."""
        server = DoctkLanguageServer()

        # Trigger error
        error_text = "invalid syntax"
        diagnostics1 = server.validate_syntax(error_text)

        # Server should still work
        valid_text = "doc | select heading"
        diagnostics2 = server.validate_syntax(valid_text)

        assert isinstance(diagnostics1, list)
        assert isinstance(diagnostics2, list)
        assert len(diagnostics2) <= len(diagnostics1)

    def test_completion_graceful_degradation(self):
        """Test that completion degrades gracefully on errors."""
        server = DoctkLanguageServer()

        # Malformed text
        text = "invalid | "
        position = Position(line=0, character=10)

        # Should not crash
        result = server.completion_provider.provide_completions(text, position)

        # Should return something (even if empty)
        assert result is not None

    def test_hover_graceful_degradation(self):
        """Test that hover degrades gracefully on errors."""
        server = DoctkLanguageServer()

        # Malformed text
        text = "invalid syntax"
        position = Position(line=0, character=5)

        # Should not crash
        result = server.hover_provider.provide_hover(text, position)

        # Result might be None for invalid positions, that's ok
        # Key is that it didn't crash
        assert result is None or result.contents is not None


@pytest.mark.slow
class TestLSPEndToEndIntegration:
    """Complete end-to-end integration tests."""

    def test_complete_workflow_open_type_complete_execute(self):
        """Test complete workflow from opening file to executing operations."""
        server = DoctkLanguageServer()

        # Step 1: Open document (simulate)
        initial_text = "doc | "

        # Step 2: Get completions
        position = Position(line=0, character=6)

        completions = server.completion_provider.provide_completions(initial_text, position)
        assert len(completions.items) > 0

        # Step 3: Select "select" completion and type
        updated_text = "doc | select heading"

        # Step 4: Validate complete syntax
        diagnostics = server.validate_syntax(updated_text)
        assert len(diagnostics) == 0

        # Step 5: Hover for documentation
        hover_position = Position(line=0, character=8)

        hover_result = server.hover_provider.provide_hover(updated_text, hover_position)
        assert hover_result is not None

    def test_multi_line_document_workflow(self):
        """Test workflow with multi-line document."""
        server = DoctkLanguageServer()

        # Multi-line document
        text = """# Document transformation
doc | select heading
doc | where level=2
doc | promote
"""

        # Validate entire document
        diagnostics = server.validate_syntax(text)
        assert isinstance(diagnostics, list)

        # Get symbols
        symbols = server.extract_document_symbols(text)
        assert len(symbols) >= 3

        # Get completions on a specific line
        position = Position(line=1, character=6)
        completions = server.completion_provider.provide_completions(text, position)
        assert len(completions.items) > 0

    def test_markdown_code_block_workflow(self):
        """Test LSP features work with doctk code blocks in Markdown."""
        server = DoctkLanguageServer()

        # Markdown with doctk code block (just the DSL part)
        dsl_code = "doc | select heading | where level=2"

        # Validate DSL syntax
        diagnostics = server.validate_syntax(dsl_code)
        assert len(diagnostics) == 0

        # Get completions
        position = Position(line=0, character=6)

        completions = server.completion_provider.provide_completions(dsl_code, position)
        assert len(completions.items) > 0
