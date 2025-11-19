"""Tests for parser position tracking.

This test suite verifies that the DSL parser correctly captures and propagates
source position information (line and column numbers) for all AST nodes.
"""

from doctk.dsl.lexer import Lexer
from doctk.dsl.parser import Assignment, FunctionCall, Parser, Pipeline, Position


class TestParserPositionTracking:
    """Test that parser captures accurate position information."""

    def test_simple_pipeline_position(self):
        """Test position tracking for simple pipeline."""
        source = "doc | promote"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        statements = parser.parse()

        assert len(statements) == 1
        pipeline = statements[0]
        assert isinstance(pipeline, Pipeline)

        # Pipeline should start at line 1, column 1 (where 'doc' is)
        assert pipeline.position.line == 1
        assert pipeline.position.column == 1

        # First operation (promote) should be at line 1, column 7
        assert len(pipeline.operations) == 1
        promote_op = pipeline.operations[0]
        assert isinstance(promote_op, FunctionCall)
        assert promote_op.position.line == 1
        assert promote_op.position.column == 7

    def test_multi_operation_pipeline_positions(self):
        """Test position tracking for pipeline with multiple operations."""
        source = "doc | promote | demote | move_up"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        statements = parser.parse()

        assert len(statements) == 1
        pipeline = statements[0]

        # Check all operation positions
        operations = pipeline.operations
        assert len(operations) == 3

        # promote at column 7
        assert operations[0].position.line == 1
        assert operations[0].position.column == 7
        assert operations[0].name == "promote"

        # demote at column 17
        assert operations[1].position.line == 1
        assert operations[1].position.column == 17
        assert operations[1].name == "demote"

        # move_up at column 26
        assert operations[2].position.line == 1
        assert operations[2].position.column == 26
        assert operations[2].name == "move_up"

    def test_multiline_pipeline_positions(self):
        """Test position tracking for multi-line pipeline."""
        source = """doc | promote
doc | demote
doc | move_up"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        statements = parser.parse()

        assert len(statements) == 3

        # First pipeline on line 1
        assert statements[0].position.line == 1
        assert statements[0].position.column == 1
        assert statements[0].operations[0].position.line == 1
        assert statements[0].operations[0].position.column == 7

        # Second pipeline on line 2
        assert statements[1].position.line == 2
        assert statements[1].position.column == 1
        assert statements[1].operations[0].position.line == 2
        assert statements[1].operations[0].position.column == 7

        # Third pipeline on line 3
        assert statements[2].position.line == 3
        assert statements[2].position.column == 1
        assert statements[2].operations[0].position.line == 3
        assert statements[2].operations[0].position.column == 7

    def test_operation_with_arguments_position(self):
        """Test position tracking for operations with arguments."""
        source = "doc | where level=3"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        statements = parser.parse()

        pipeline = statements[0]
        where_op = pipeline.operations[0]

        # where operation should start at column 7
        assert where_op.position.line == 1
        assert where_op.position.column == 7
        assert where_op.name == "where"

        # Check arguments are parsed correctly (position doesn't include args)
        assert where_op.kwargs == {"level": 3}

    def test_assignment_position(self):
        """Test position tracking for variable assignments."""
        source = "let result = doc | promote"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        statements = parser.parse()

        assert len(statements) == 1
        assignment = statements[0]
        assert isinstance(assignment, Assignment)

        # Assignment should start at line 1, column 1 (where 'let' is)
        assert assignment.position.line == 1
        assert assignment.position.column == 1
        assert assignment.variable == "result"

        # Nested pipeline should start at column 14 (where 'doc' is)
        pipeline = assignment.pipeline
        assert pipeline.position.line == 1
        assert pipeline.position.column == 14

    def test_complex_multiline_with_comments(self):
        """Test position tracking with comments and multiple lines."""
        source = """# First operation
doc | promote

# Second operation
doc | demote | move_up"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        statements = parser.parse()

        assert len(statements) == 2

        # First pipeline (line 2, after comment)
        assert statements[0].position.line == 2
        assert statements[0].position.column == 1

        # Second pipeline (line 5, after comment and blank line)
        assert statements[1].position.line == 5
        assert statements[1].position.column == 1

        # Operations on line 5
        ops = statements[1].operations
        assert ops[0].position.line == 5  # demote
        assert ops[1].position.line == 5  # move_up

    def test_operation_with_string_argument_position(self):
        """Test position tracking for operations with string arguments."""
        source = "doc | select heading"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        statements = parser.parse()

        select_op = statements[0].operations[0]

        # select operation should start at column 7
        assert select_op.position.line == 1
        assert select_op.position.column == 7
        assert select_op.name == "select"

    def test_nested_positions_with_whitespace(self):
        """Test position tracking handles whitespace correctly."""
        source = "doc   |   promote   |   demote"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        statements = parser.parse()

        pipeline = statements[0]

        # Pipeline starts where 'doc' is (column 1)
        assert pipeline.position.line == 1
        assert pipeline.position.column == 1

        # Operations: lexer skips whitespace, so positions are after whitespace
        # promote starts at column 11
        assert pipeline.operations[0].position.line == 1
        assert pipeline.operations[0].position.column == 11

        # demote starts at column 25
        assert pipeline.operations[1].position.line == 1
        assert pipeline.operations[1].position.column == 25


class TestParserPositionDataclass:
    """Test Position dataclass functionality."""

    def test_position_creation(self):
        """Test Position dataclass can be created."""
        pos = Position(line=1, column=5)
        assert pos.line == 1
        assert pos.column == 5

    def test_position_equality(self):
        """Test Position equality comparison."""
        pos1 = Position(line=1, column=5)
        pos2 = Position(line=1, column=5)
        pos3 = Position(line=2, column=5)

        assert pos1 == pos2
        assert pos1 != pos3

    def test_position_repr(self):
        """Test Position has readable representation."""
        pos = Position(line=3, column=10)
        repr_str = repr(pos)
        assert "3" in repr_str
        assert "10" in repr_str
