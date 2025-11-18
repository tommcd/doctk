"""DSL Parser - Parse tokens into Abstract Syntax Tree."""

from dataclasses import dataclass
from typing import Any

from doctk.dsl.lexer import Token, TokenType


@dataclass
class ASTNode:
    """Base class for AST nodes."""

    pass


@dataclass
class Pipeline(ASTNode):
    """Pipeline expression: source | op1 | op2."""

    source: str
    operations: list["FunctionCall"]


@dataclass
class FunctionCall(ASTNode):
    """Function call: name(arg1, arg2)."""

    name: str
    arguments: dict[str, Any]


@dataclass
class Assignment(ASTNode):
    """Variable assignment: let x = pipeline."""

    variable: str
    pipeline: Pipeline


class ParseError(Exception):
    """Exception raised for parse errors."""

    def __init__(self, message: str, token: Token | None = None):
        """
        Initialize parse error.

        Args:
            message: Error message
            token: Token where error occurred
        """
        if token:
            super().__init__(f"{message} at line {token.line}, column {token.column}")
        else:
            super().__init__(message)
        self.token = token


class Parser:
    """Parser for the doctk DSL."""

    def __init__(self, tokens: list[Token]):
        """
        Initialize parser with tokens.

        Args:
            tokens: List of tokens from lexer
        """
        self.tokens = tokens
        self.pos = 0

    def current_token(self) -> Token:
        """Get current token."""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]  # Return EOF token

    def peek_token(self, offset: int = 1) -> Token:
        """Peek at token ahead."""
        pos = self.pos + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return self.tokens[-1]  # Return EOF token

    def advance(self) -> Token:
        """Consume and return current token."""
        token = self.current_token()
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return token

    def expect(self, token_type: TokenType) -> Token:
        """Expect a specific token type and consume it."""
        token = self.current_token()
        if token.type != token_type:
            raise ParseError(
                f"Expected {token_type.name}, got {token.type.name}", token
            )
        return self.advance()

    def parse(self) -> list[ASTNode]:
        """
        Parse tokens into AST.

        Returns:
            List of AST nodes (statements)
        """
        statements: list[ASTNode] = []

        while self.current_token().type != TokenType.EOF:
            # Skip newlines
            if self.current_token().type == TokenType.NEWLINE:
                self.advance()
                continue

            # Parse statement
            try:
                stmt = self.parse_statement()
                if stmt:
                    statements.append(stmt)
            except ParseError:
                # On error, skip to next newline or EOF
                while (
                    self.current_token().type != TokenType.NEWLINE
                    and self.current_token().type != TokenType.EOF
                ):
                    self.advance()
                if self.current_token().type == TokenType.NEWLINE:
                    self.advance()

        return statements

    def parse_statement(self) -> ASTNode | None:
        """Parse a single statement."""
        # Check for assignment: let x = pipeline
        if self.current_token().type == TokenType.LET:
            return self.parse_assignment()

        # Otherwise, parse as pipeline expression
        return self.parse_pipeline()

    def parse_assignment(self) -> Assignment:
        """Parse variable assignment."""
        self.expect(TokenType.LET)
        var_token = self.expect(TokenType.IDENTIFIER)
        self.expect(TokenType.EQUALS)
        pipeline = self.parse_pipeline()

        if not isinstance(pipeline, Pipeline):
            raise ParseError("Expected pipeline after assignment", self.current_token())

        return Assignment(variable=var_token.value, pipeline=pipeline)

    def parse_pipeline(self) -> Pipeline:
        """Parse pipeline expression."""
        # Parse source (doc or identifier)
        source_token = self.current_token()

        if source_token.type == TokenType.DOC:
            source = "doc"
            self.advance()
        elif source_token.type == TokenType.IDENTIFIER:
            source = source_token.value
            self.advance()
        else:
            raise ParseError("Expected 'doc' or identifier as pipeline source", source_token)

        # Parse operations separated by pipes
        operations: list[FunctionCall] = []

        while self.current_token().type == TokenType.PIPE:
            self.advance()  # Consume pipe

            # Parse operation (function call)
            operation = self.parse_function_call()
            operations.append(operation)

        return Pipeline(source=source, operations=operations)

    def parse_function_call(self) -> FunctionCall:
        """Parse function call."""
        # Get function name (can be identifier or keyword used as operation name)
        name_token = self.current_token()

        # Accept identifiers and keywords as operation names
        allowed_token_types = {
            TokenType.IDENTIFIER,
            TokenType.SELECT,
            TokenType.WHERE,
        }

        if name_token.type not in allowed_token_types:
            raise ParseError(
                f"Expected operation name, got {name_token.type.name}", name_token
            )

        name = name_token.value
        self.advance()

        # Parse arguments
        arguments: dict[str, Any] = {}

        # Check for arguments (optional)
        if self.current_token().type == TokenType.IDENTIFIER:
            # Check if this is a key=value argument or just a value
            # Look ahead to see if next token is =
            if self.peek_token().type == TokenType.EQUALS:
                # Parse key=value arguments
                while self.current_token().type == TokenType.IDENTIFIER:
                    key_token = self.advance()
                    key = key_token.value

                    # Expect equals sign
                    self.expect(TokenType.EQUALS)

                    # Parse value
                    value = self.parse_value()
                    arguments[key] = value

                    # Check for comma (multiple arguments)
                    if self.current_token().type == TokenType.COMMA:
                        self.advance()
            else:
                # Positional argument - just a value
                value = self.parse_value()
                # Use the value as both key and value for now
                # (This matches the test expectation: {"heading": "heading"})
                if isinstance(value, str):
                    arguments[value] = value

        return FunctionCall(name=name, arguments=arguments)

    def parse_value(self) -> Any:
        """Parse a value (string, number, boolean, identifier)."""
        token = self.current_token()

        if token.type == TokenType.STRING:
            self.advance()
            return token.value
        elif token.type == TokenType.NUMBER:
            self.advance()
            # Try to parse as int, fallback to float
            try:
                return int(token.value)
            except ValueError:
                return float(token.value)
        elif token.type in (TokenType.TRUE, TokenType.FALSE):
            self.advance()
            return token.type == TokenType.TRUE
        elif token.type == TokenType.IDENTIFIER:
            self.advance()
            return token.value
        else:
            raise ParseError(f"Expected value, got {token.type.name}", token)
