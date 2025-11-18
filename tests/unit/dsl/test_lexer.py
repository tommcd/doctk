"""Tests for DSL lexer."""

import pytest

from doctk.dsl.lexer import Lexer, Token, TokenType


def test_tokenize_identifiers():
    """Test tokenizing identifiers."""
    lexer = Lexer("foo bar_baz")
    tokens = lexer.tokenize()

    assert len(tokens) == 3  # foo, bar_baz, EOF
    assert tokens[0].type == TokenType.IDENTIFIER
    assert tokens[0].value == "foo"
    assert tokens[1].type == TokenType.IDENTIFIER
    assert tokens[1].value == "bar_baz"
    assert tokens[2].type == TokenType.EOF


def test_tokenize_keywords():
    """Test tokenizing keywords."""
    lexer = Lexer("let doc where select true false")
    tokens = lexer.tokenize()

    assert tokens[0].type == TokenType.LET
    assert tokens[1].type == TokenType.DOC
    assert tokens[2].type == TokenType.WHERE
    assert tokens[3].type == TokenType.SELECT
    assert tokens[4].type == TokenType.TRUE
    assert tokens[5].type == TokenType.FALSE


def test_tokenize_strings():
    """Test tokenizing string literals."""
    lexer = Lexer('"hello world" \'single quoted\'')
    tokens = lexer.tokenize()

    assert tokens[0].type == TokenType.STRING
    assert tokens[0].value == "hello world"
    assert tokens[1].type == TokenType.STRING
    assert tokens[1].value == "single quoted"


def test_tokenize_numbers():
    """Test tokenizing numbers."""
    lexer = Lexer("123 456.789")
    tokens = lexer.tokenize()

    assert tokens[0].type == TokenType.NUMBER
    assert tokens[0].value == "123"
    assert tokens[1].type == TokenType.NUMBER
    assert tokens[1].value == "456.789"


def test_tokenize_operators():
    """Test tokenizing operators."""
    lexer = Lexer("| = != > < >= <= ~= ^= $= *=")
    tokens = lexer.tokenize()

    assert tokens[0].type == TokenType.PIPE
    assert tokens[1].type == TokenType.EQUALS
    assert tokens[2].type == TokenType.NOT_EQUALS
    assert tokens[3].type == TokenType.GREATER
    assert tokens[4].type == TokenType.LESS
    assert tokens[5].type == TokenType.GREATER_EQUAL
    assert tokens[6].type == TokenType.LESS_EQUAL
    assert tokens[7].type == TokenType.TILDE_EQUALS
    assert tokens[8].type == TokenType.CARET_EQUALS
    assert tokens[9].type == TokenType.DOLLAR_EQUALS
    assert tokens[10].type == TokenType.STAR_EQUALS


def test_tokenize_delimiters():
    """Test tokenizing delimiters."""
    lexer = Lexer("( ) ,")
    tokens = lexer.tokenize()

    assert tokens[0].type == TokenType.LPAREN
    assert tokens[1].type == TokenType.RPAREN
    assert tokens[2].type == TokenType.COMMA


def test_tokenize_pipeline():
    """Test tokenizing a complete pipeline."""
    lexer = Lexer("doc | select heading | where level=3")
    tokens = lexer.tokenize()

    expected = [
        (TokenType.DOC, "doc"),
        (TokenType.PIPE, "|"),
        (TokenType.SELECT, "select"),
        (TokenType.IDENTIFIER, "heading"),
        (TokenType.PIPE, "|"),
        (TokenType.WHERE, "where"),
        (TokenType.IDENTIFIER, "level"),
        (TokenType.EQUALS, "="),
        (TokenType.NUMBER, "3"),
        (TokenType.EOF, ""),
    ]

    assert len(tokens) == len(expected)
    for token, (exp_type, exp_value) in zip(tokens, expected):
        assert token.type == exp_type
        assert token.value == exp_value


def test_tokenize_assignment():
    """Test tokenizing variable assignment."""
    lexer = Lexer('let headings = doc | select heading')
    tokens = lexer.tokenize()

    assert tokens[0].type == TokenType.LET
    assert tokens[1].type == TokenType.IDENTIFIER
    assert tokens[1].value == "headings"
    assert tokens[2].type == TokenType.EQUALS


def test_line_column_tracking():
    """Test that line and column positions are tracked."""
    source = """doc | select heading
where level=2"""
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    # First token should be at line 1, column 1
    assert tokens[0].line == 1
    assert tokens[0].column == 1

    # Find 'where' token (should be on line 2)
    where_token = next(t for t in tokens if t.type == TokenType.WHERE)
    assert where_token.line == 2


def test_skip_comments():
    """Test that comments are skipped."""
    lexer = Lexer("# This is a comment\ndoc | select heading")
    tokens = lexer.tokenize()

    # Should only have doc, |, select, heading, EOF
    assert len(tokens) == 5
    assert tokens[0].type == TokenType.DOC


def test_string_escape_sequences():
    """Test that string escape sequences are handled."""
    lexer = Lexer(r'"hello\nworld"')
    tokens = lexer.tokenize()

    assert tokens[0].type == TokenType.STRING
    assert tokens[0].value == "hello\nworld"


def test_empty_source():
    """Test tokenizing empty source."""
    lexer = Lexer("")
    tokens = lexer.tokenize()

    assert len(tokens) == 1
    assert tokens[0].type == TokenType.EOF


def test_whitespace_handling():
    """Test that whitespace is properly skipped."""
    lexer = Lexer("  doc   |   select  \t  heading  ")
    tokens = lexer.tokenize()

    # Should have doc, |, select, heading, EOF
    assert len(tokens) == 5
    assert all(t.type != TokenType.IDENTIFIER or t.value.strip() == t.value for t in tokens)
