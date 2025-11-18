"""Tests for DSL parser."""

import pytest

from doctk.dsl.lexer import Lexer
from doctk.dsl.parser import Assignment, ParseError, Parser, Pipeline


class TestParserBasics:
    """Test basic parser functionality."""

    def test_parse_empty_input(self):
        """Test parsing empty input."""
        lexer = Lexer("")
        tokens = lexer.tokenize()
        parser = Parser(tokens)

        result = parser.parse()

        assert result == []

    def test_parse_simple_pipeline(self):
        """Test parsing a simple pipeline."""
        source = "doc | select heading"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)

        result = parser.parse()

        assert len(result) == 1
        assert isinstance(result[0], Pipeline)
        pipeline = result[0]
        assert pipeline.source == "doc"
        assert len(pipeline.operations) == 1
        assert pipeline.operations[0].name == "select"
        # "heading" is a positional argument
        assert pipeline.operations[0].args == ["heading"]
        assert pipeline.operations[0].kwargs == {}

    def test_parse_pipeline_with_multiple_operations(self):
        """Test parsing pipeline with multiple operations."""
        source = "doc | select heading | promote"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)

        result = parser.parse()

        assert len(result) == 1
        pipeline = result[0]
        assert pipeline.source == "doc"
        assert len(pipeline.operations) == 2
        assert pipeline.operations[0].name == "select"
        assert pipeline.operations[1].name == "promote"

    def test_parse_operation_with_arguments(self):
        """Test parsing operation with key=value arguments."""
        source = "doc | where level=2"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)

        result = parser.parse()

        assert len(result) == 1
        pipeline = result[0]
        assert len(pipeline.operations) == 1
        operation = pipeline.operations[0]
        assert operation.name == "where"
        # Keyword arguments
        assert operation.args == []
        assert operation.kwargs == {"level": 2}

    def test_parse_operation_with_string_argument(self):
        """Test parsing operation with string argument."""
        source = 'doc | where text="Hello"'
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)

        result = parser.parse()

        pipeline = result[0]
        operation = pipeline.operations[0]
        assert operation.args == []
        assert operation.kwargs == {"text": "Hello"}

    def test_parse_operation_with_multiple_arguments(self):
        """Test parsing operation with multiple arguments."""
        source = "doc | operation level=2, text=foo"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)

        result = parser.parse()

        pipeline = result[0]
        operation = pipeline.operations[0]
        assert operation.name == "operation"
        assert operation.args == []
        assert operation.kwargs == {"level": 2, "text": "foo"}


class TestParserAssignment:
    """Test variable assignment parsing."""

    def test_parse_let_assignment(self):
        """Test parsing variable assignment."""
        source = "let result = doc | select heading"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)

        result = parser.parse()

        assert len(result) == 1
        assert isinstance(result[0], Assignment)
        assignment = result[0]
        assert assignment.variable == "result"
        assert isinstance(assignment.pipeline, Pipeline)
        assert assignment.pipeline.source == "doc"


class TestParserErrors:
    """Test parser error handling."""

    def test_parse_error_invalid_source(self):
        """Test parse error on invalid source."""
        source = "123 | select heading"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)

        # Parser should raise ParseError for invalid syntax
        with pytest.raises(ParseError) as exc_info:
            parser.parse()

        assert "Expected 'doc' or identifier" in str(exc_info.value)

    def test_parse_error_missing_pipe(self):
        """Test that missing pipe doesn't cause error (just empty operations)."""
        source = "doc"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)

        result = parser.parse()

        assert len(result) == 1
        pipeline = result[0]
        assert pipeline.source == "doc"
        assert len(pipeline.operations) == 0

    def test_parse_error_invalid_argument(self):
        """Test parse error on invalid argument value."""
        source = "doc | where level=|"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)

        # Parser should raise ParseError for invalid syntax
        with pytest.raises(ParseError) as exc_info:
            parser.parse()

        assert "Expected value" in str(exc_info.value)

    def test_parse_error_has_token_info(self):
        """Test that parse errors include token information."""
        source = "doc | 123"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)

        # Parser should raise ParseError with token info
        with pytest.raises(ParseError) as exc_info:
            parser.parse()

        error = exc_info.value
        assert error.token is not None
        assert error.token.line >= 1
        assert error.token.column >= 1


class TestParserComplexCases:
    """Test complex parsing scenarios."""

    def test_parse_with_comments(self):
        """Test parsing with comments (comments are skipped by lexer)."""
        source = """
        # This is a comment
        doc | select heading
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)

        result = parser.parse()

        assert len(result) == 1
        assert isinstance(result[0], Pipeline)

    def test_parse_multiple_statements(self):
        """Test parsing multiple statements."""
        source = """
        doc | select heading
        doc | promote
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)

        result = parser.parse()

        # Parser should handle newlines and parse both statements
        assert len(result) >= 1

    def test_parse_complex_pipeline(self):
        """Test parsing a complex pipeline."""
        source = "doc | select heading | where level=3 | promote"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)

        result = parser.parse()

        assert len(result) == 1
        pipeline = result[0]
        assert len(pipeline.operations) == 3
        assert pipeline.operations[0].name == "select"
        assert pipeline.operations[1].name == "where"
        assert pipeline.operations[1].args == []
        assert pipeline.operations[1].kwargs == {"level": 3}
        assert pipeline.operations[2].name == "promote"
