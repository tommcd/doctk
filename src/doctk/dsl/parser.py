"""DSL Parser - Parse tokens into Abstract Syntax Tree."""

from dataclasses import dataclass
from typing import Any

from doctk.dsl.lexer import Token


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

    def parse(self) -> list[ASTNode]:
        """
        Parse tokens into AST.

        Returns:
            List of AST nodes (statements)
        """
        # Stub implementation
        return []
