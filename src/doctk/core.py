"""
Core abstractions for doctk.

Implements the fundamental Document and Node classes following category theory principles.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

T = TypeVar("T")
U = TypeVar("U")


class Node(ABC):
    """
    Base class for all document nodes.

    In category theory terms, Node is the base "object" in our document category.
    Nodes form a tree structure representing document hierarchy.
    """

    @abstractmethod
    def accept(self, visitor: "NodeVisitor") -> Any:
        """Accept a visitor (Visitor pattern for traversal)."""
        pass

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Convert node to dictionary representation."""
        pass


@dataclass
class Heading(Node):
    """Heading node (h1-h6)."""

    level: int  # 1-6
    text: str
    children: list[Node] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def accept(self, visitor: "NodeVisitor") -> Any:
        return visitor.visit_heading(self)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "heading",
            "level": self.level,
            "text": self.text,
            "children": [child.to_dict() for child in self.children],
            "metadata": self.metadata,
        }

    def promote(self) -> "Heading":
        """Decrease heading level (h3 -> h2). Identity if already h1."""
        return Heading(
            level=max(1, self.level - 1),
            text=self.text,
            children=self.children,
            metadata=self.metadata,
        )

    def demote(self) -> "Heading":
        """Increase heading level (h2 -> h3). Identity if already h6."""
        return Heading(
            level=min(6, self.level + 1),
            text=self.text,
            children=self.children,
            metadata=self.metadata,
        )


@dataclass
class Paragraph(Node):
    """Paragraph node."""

    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def accept(self, visitor: "NodeVisitor") -> Any:
        return visitor.visit_paragraph(self)

    def to_dict(self) -> dict[str, Any]:
        return {"type": "paragraph", "content": self.content, "metadata": self.metadata}


@dataclass
class List(Node):
    """List node (ordered or unordered)."""

    ordered: bool
    items: list[Node]
    metadata: dict[str, Any] = field(default_factory=dict)

    def accept(self, visitor: "NodeVisitor") -> Any:
        return visitor.visit_list(self)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "list",
            "ordered": self.ordered,
            "items": [item.to_dict() for item in self.items],
            "metadata": self.metadata,
        }

    def to_ordered(self) -> "List":
        """Convert to ordered list."""
        return List(ordered=True, items=self.items, metadata=self.metadata)

    def to_unordered(self) -> "List":
        """Convert to unordered list."""
        return List(ordered=False, items=self.items, metadata=self.metadata)


@dataclass
class ListItem(Node):
    """List item node."""

    content: list[Node]
    metadata: dict[str, Any] = field(default_factory=dict)

    def accept(self, visitor: "NodeVisitor") -> Any:
        return visitor.visit_list_item(self)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "list_item",
            "content": [node.to_dict() for node in self.content],
            "metadata": self.metadata,
        }


@dataclass
class CodeBlock(Node):
    """Code block node."""

    code: str
    language: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def accept(self, visitor: "NodeVisitor") -> Any:
        return visitor.visit_code_block(self)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "code_block",
            "code": self.code,
            "language": self.language,
            "metadata": self.metadata,
        }


@dataclass
class BlockQuote(Node):
    """Block quote node."""

    content: list[Node]
    metadata: dict[str, Any] = field(default_factory=dict)

    def accept(self, visitor: "NodeVisitor") -> Any:
        return visitor.visit_block_quote(self)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "block_quote",
            "content": [node.to_dict() for node in self.content],
            "metadata": self.metadata,
        }


class NodeVisitor(ABC):
    """Visitor interface for traversing nodes."""

    @abstractmethod
    def visit_heading(self, node: Heading) -> Any:
        pass

    @abstractmethod
    def visit_paragraph(self, node: Paragraph) -> Any:
        pass

    @abstractmethod
    def visit_list(self, node: List) -> Any:
        pass

    @abstractmethod
    def visit_list_item(self, node: ListItem) -> Any:
        pass

    @abstractmethod
    def visit_code_block(self, node: CodeBlock) -> Any:
        pass

    @abstractmethod
    def visit_block_quote(self, node: BlockQuote) -> Any:
        pass


class Document(Generic[T]):
    """
    Document container - the fundamental abstraction.

    A Document is a Functor and a Monad:
    - Functor: Can map transformations over nodes
    - Monad: Can chain operations that return Documents

    Supports pipe operator (|) for composition.
    """

    def __init__(self, nodes: list[T]):
        self.nodes = nodes

    # Functor operations
    def map(self, f: Callable[[T], U]) -> "Document[U]":
        """
        Apply transformation to each node.

        Functor law: map(id) = id
        Functor law: map(f . g) = map(f) . map(g)
        """
        return Document([f(node) for node in self.nodes])

    def filter(self, predicate: Callable[[T], bool]) -> "Document[T]":
        """
        Filter nodes by predicate (subset selection).

        This is set-theoretic filtering.
        """
        return Document([node for node in self.nodes if predicate(node)])

    # Monad operations
    def flatmap(self, f: Callable[[T], "Document[U]"]) -> "Document[U]":
        """
        Map and flatten.

        Monad law: flatmap(return) = id
        Monad law: return(x).flatmap(f) = f(x)
        Monad law: m.flatmap(f).flatmap(g) = m.flatmap(lambda x: f(x).flatmap(g))
        """
        result = []
        for node in self.nodes:
            result.extend(f(node).nodes)
        return Document(result)

    def reduce(self, f: Callable[[U, T], U], initial: U) -> U:
        """
        Fold operation (catamorphism).

        Reduce document to a single value.
        """
        result = initial
        for node in self.nodes:
            result = f(result, node)
        return result

    # Pipe operator support
    def __or__(self, operation: Callable[["Document[T]"], "Document[U]"]) -> "Document[U]":
        """
        Enable pipeline syntax: doc | operation

        This makes operations composable in a readable left-to-right flow.
        """
        return operation(self)

    # Fluent API (alternative to pipe operator)
    def select(self, predicate: Callable[[T], bool]) -> "Document[T]":
        """Fluent API for filter."""
        return self.filter(predicate)

    # Set operations
    def union(self, other: "Document[T]") -> "Document[T]":
        """Set union - combine two documents."""
        return Document(self.nodes + other.nodes)

    def intersect(
        self, other: "Document[T]", key: Callable[[T], Any] | None = None
    ) -> "Document[T]":
        """Set intersection based on key function."""
        if key is None:
            other_set = set(other.nodes)
            return Document([n for n in self.nodes if n in other_set])
        else:
            other_keys = {key(n) for n in other.nodes}
            return Document([n for n in self.nodes if key(n) in other_keys])

    def diff(self, other: "Document[T]", key: Callable[[T], Any] | None = None) -> "Document[T]":
        """Set difference - elements in self but not in other."""
        if key is None:
            other_set = set(other.nodes)
            return Document([n for n in self.nodes if n not in other_set])
        else:
            other_keys = {key(n) for n in other.nodes}
            return Document([n for n in self.nodes if key(n) not in other_keys])

    def concat(self, other: "Document[T]") -> "Document[T]":
        """Sequential composition (same as union for documents)."""
        return self.union(other)

    # IO operations
    @staticmethod
    def from_file(path: str) -> "Document[Node]":
        """Load document from file."""
        from doctk.parsers.markdown import MarkdownParser

        parser = MarkdownParser()
        return parser.parse_file(path)

    @staticmethod
    def from_string(content: str) -> "Document[Node]":
        """Parse document from string."""
        from doctk.parsers.markdown import MarkdownParser

        parser = MarkdownParser()
        return parser.parse_string(content)

    def to_file(self, path: str) -> None:
        """Write document to file."""
        from doctk.writers.markdown import MarkdownWriter

        writer = MarkdownWriter()
        writer.write_file(self, path)

    def to_string(self) -> str:
        """Convert document to string."""
        from doctk.writers.markdown import MarkdownWriter

        writer = MarkdownWriter()
        return writer.write_string(self)

    def __len__(self) -> int:
        """Number of nodes in document."""
        return len(self.nodes)

    def __iter__(self):
        """Iterate over nodes."""
        return iter(self.nodes)

    def __repr__(self) -> str:
        return f"Document({len(self.nodes)} nodes)"


# Identity morphism
def identity() -> Callable[[Document[T]], Document[T]]:
    """Identity transformation - returns document unchanged."""
    return lambda doc: doc
