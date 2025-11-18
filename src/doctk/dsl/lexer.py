"""DSL Lexer - Tokenizes doctk DSL source code."""

from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    """Token types for the doctk DSL."""

    # Literals
    IDENTIFIER = auto()  # variable names, operation names
    STRING = auto()  # "text" or 'text'
    NUMBER = auto()  # 123, 3.14
    BOOLEAN = auto()  # true, false

    # Operators
    PIPE = auto()  # |
    EQUALS = auto()  # =
    NOT_EQUALS = auto()  # !=
    GREATER = auto()  # >
    LESS = auto()  # <
    GREATER_EQUAL = auto()  # >=
    LESS_EQUAL = auto()  # <=
    TILDE_EQUALS = auto()  # ~= (regex match)
    CARET_EQUALS = auto()  # ^= (starts with)
    DOLLAR_EQUALS = auto()  # $= (ends with)
    STAR_EQUALS = auto()  # *= (contains)

    # Keywords
    LET = auto()  # let
    DOC = auto()  # doc
    WHERE = auto()  # where
    SELECT = auto()  # select
    TRUE = auto()  # true
    FALSE = auto()  # false

    # Delimiters
    LPAREN = auto()  # (
    RPAREN = auto()  # )
    COMMA = auto()  # ,

    # Special
    EOF = auto()
    NEWLINE = auto()


@dataclass
class Token:
    """A single token in the DSL."""

    type: TokenType
    value: str
    line: int
    column: int

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.column})"


class LexerError(Exception):
    """Exception raised for lexical analysis errors."""

    def __init__(self, message: str, line: int, column: int):
        """
        Initialize lexer error.

        Args:
            message: Error message
            line: Line number where error occurred (1-indexed)
            column: Column number where error occurred (1-indexed)
        """
        super().__init__(f"{message} at line {line}, column {column}")
        self.line = line
        self.column = column


class Lexer:
    """Lexer for the doctk DSL."""

    def __init__(self, source: str):
        """
        Initialize lexer with source code.

        Args:
            source: DSL source code to tokenize
        """
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1

    def peek(self, offset: int = 0) -> str | None:
        """Peek at character at current position + offset."""
        pos = self.pos + offset
        if pos >= len(self.source):
            return None
        return self.source[pos]

    def advance(self) -> str | None:
        """Consume and return current character."""
        if self.pos >= len(self.source):
            return None

        char = self.source[self.pos]
        self.pos += 1

        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1

        return char

    def skip_whitespace(self) -> None:
        """Skip whitespace and comments."""
        while True:
            # Skip whitespace
            while self.peek() and self.peek() in " \t\r\n":
                # Track newlines but skip them for now (may add NEWLINE tokens later)
                self.advance()

            # Skip comments (# to end of line)
            if self.peek() == "#":
                while self.peek() and self.peek() != "\n":
                    self.advance()
                # Continue loop to skip the newline after the comment
            else:
                # No more whitespace or comments
                break

    def read_string(self) -> str:
        """Read a string literal."""
        quote = self.advance()  # Opening quote
        value = ""

        while self.peek() and self.peek() != quote:
            char = self.advance()
            if char == "\\":
                # Handle escape sequences
                next_char = self.advance()
                if next_char == "n":
                    value += "\n"
                elif next_char == "t":
                    value += "\t"
                elif next_char == "\\":
                    value += "\\"
                elif next_char == quote:
                    value += quote
                else:
                    value += next_char
            else:
                value += char

        if self.peek() == quote:
            self.advance()  # Closing quote

        return value

    def read_number(self) -> str:
        """Read a number literal."""
        value = ""
        has_dot = False

        while self.peek() and (self.peek().isdigit() or self.peek() == "."):
            char = self.peek()
            if char == ".":
                if has_dot:
                    # Multiple dots - stop parsing
                    break
                has_dot = True
            value += self.advance()

        return value

    def read_identifier(self) -> str:
        """Read an identifier or keyword."""
        value = ""

        while self.peek() and (self.peek().isalnum() or self.peek() in "_-"):
            value += self.advance()

        return value

    def next_token(self) -> Token:
        """Get next token from source."""
        self.skip_whitespace()

        # Track position for error reporting
        line = self.line
        column = self.column

        # EOF
        if self.pos >= len(self.source):
            return Token(TokenType.EOF, "", line, column)

        char = self.peek()

        # String literals
        if char in "\"'":
            value = self.read_string()
            return Token(TokenType.STRING, value, line, column)

        # Numbers
        if char.isdigit():
            value = self.read_number()
            return Token(TokenType.NUMBER, value, line, column)

        # Identifiers and keywords
        if char.isalpha() or char == "_":
            value = self.read_identifier()

            # Keywords
            keyword_map = {
                "let": TokenType.LET,
                "doc": TokenType.DOC,
                "where": TokenType.WHERE,
                "select": TokenType.SELECT,
                "true": TokenType.TRUE,
                "false": TokenType.FALSE,
            }

            token_type = keyword_map.get(value, TokenType.IDENTIFIER)
            return Token(token_type, value, line, column)

        # Two-character operators
        if char in "!~^$*" and self.peek(1) == "=":
            op_char = self.advance()
            self.advance()  # =
            op_map = {
                "!": TokenType.NOT_EQUALS,
                "~": TokenType.TILDE_EQUALS,
                "^": TokenType.CARET_EQUALS,
                "$": TokenType.DOLLAR_EQUALS,
                "*": TokenType.STAR_EQUALS,
            }
            return Token(op_map[op_char], op_char + "=", line, column)

        # >= and <=
        if char in "><" and self.peek(1) == "=":
            op_char = self.advance()
            self.advance()  # =
            op_type = TokenType.GREATER_EQUAL if op_char == ">" else TokenType.LESS_EQUAL
            return Token(op_type, op_char + "=", line, column)

        # Single-character tokens
        single_char_map = {
            "|": TokenType.PIPE,
            "=": TokenType.EQUALS,
            ">": TokenType.GREATER,
            "<": TokenType.LESS,
            "(": TokenType.LPAREN,
            ")": TokenType.RPAREN,
            ",": TokenType.COMMA,
        }

        if char in single_char_map:
            self.advance()
            return Token(single_char_map[char], char, line, column)

        # Unknown character - raise error
        raise LexerError(f"Unknown character '{char}'", line, column)

    def tokenize(self) -> list[Token]:
        """
        Tokenize entire source into list of tokens.

        Returns:
            List of tokens including EOF token at end
        """
        tokens = []

        while True:
            token = self.next_token()
            tokens.append(token)
            if token.type == TokenType.EOF:
                break

        return tokens
