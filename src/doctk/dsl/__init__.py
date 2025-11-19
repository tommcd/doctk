"""
DSL (Domain-Specific Language) for doctk transformations.

This package provides a DSL for writing document transformation scripts,
including lexer, parser, executor, and REPL components.
"""

from doctk.dsl.codeblock import CodeBlock, CodeBlockExecutor
from doctk.dsl.executor import ExecutionError, Executor, ScriptExecutor
from doctk.dsl.lexer import Lexer, LexerError, Token, TokenType
from doctk.dsl.parser import ParseError, Parser
from doctk.dsl.repl import REPL

__all__ = [
    "CodeBlock",
    "CodeBlockExecutor",
    "ExecutionError",
    "Executor",
    "Lexer",
    "LexerError",
    "ParseError",
    "Parser",
    "REPL",
    "ScriptExecutor",
    "Token",
    "TokenType",
]
