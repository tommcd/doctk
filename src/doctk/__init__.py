"""
doctk - A composable toolkit for structured document manipulation.

Inspired by category theory, set theory, and the Zen of Python.
"""

from doctk.core import Document, Heading, List, Node, Paragraph
from doctk.operations import (
    compose,
    demote,
    heading,
    lift,
    lower,
    nest,
    promote,
    select,
    unnest,
    where,
)
from doctk.outliner import outline, outline_headings_only

__version__ = "0.1.0"
__all__ = [
    "Document",
    "Node",
    "Heading",
    "Paragraph",
    "List",
    "compose",
    "select",
    "where",
    "heading",
    "promote",
    "demote",
    "lift",
    "lower",
    "nest",
    "unnest",
    "outline",
    "outline_headings_only",
]
