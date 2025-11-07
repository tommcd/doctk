"""
Composable operations for document transformation.

Operations are morphisms in the document category.
They compose naturally following category theory laws.
"""

from typing import Any, Callable, TypeVar

from doctk.core import CodeBlock, Document, Heading, List, Node, Paragraph

T = TypeVar("T")
U = TypeVar("U")


# Composition
def compose(*operations: Callable) -> Callable:
    """
    Compose operations right-to-left (mathematical composition).

    compose(f, g, h)(x) = f(g(h(x)))

    Category theory law: Associativity
    (f ∘ g) ∘ h = f ∘ (g ∘ h)
    """

    def composed(doc: Document) -> Document:
        result = doc
        for op in reversed(operations):
            result = op(result)
        return result

    return composed


# Selection primitives
def select(predicate: Callable[[Node], bool]) -> Callable[[Document[Node]], Document[Node]]:
    """
    Select nodes matching predicate.

    This is set-theoretic filtering: { x ∈ Doc | predicate(x) }
    """

    def selector(doc: Document[Node]) -> Document[Node]:
        return doc.filter(predicate)

    return selector


def where(**conditions: Any) -> Callable[[Document[Node]], Document[Node]]:
    """
    Convenient predicate builder for common conditions.

    Examples:
        where(type="heading")
        where(level=2)
        where(ordered=True)
    """

    def predicate(node: Node) -> bool:
        for key, value in conditions.items():
            if not hasattr(node, key):
                return False
            if getattr(node, key) != value:
                return False
        return True

    return select(predicate)


def first() -> Callable[[Document[T]], Document[T]]:
    """Take first element."""

    def take_first(doc: Document[T]) -> Document[T]:
        return Document(doc.nodes[:1] if doc.nodes else [])

    return take_first


def last() -> Callable[[Document[T]], Document[T]]:
    """Take last element."""

    def take_last(doc: Document[T]) -> Document[T]:
        return Document(doc.nodes[-1:] if doc.nodes else [])

    return take_last


def nth(n: int) -> Callable[[Document[T]], Document[T]]:
    """Take nth element (0-indexed)."""

    def take_nth(doc: Document[T]) -> Document[T]:
        return Document([doc.nodes[n]] if 0 <= n < len(doc.nodes) else [])

    return take_nth


def slice_nodes(start: int, end: int | None = None) -> Callable[[Document[T]], Document[T]]:
    """Take slice of nodes."""

    def take_slice(doc: Document[T]) -> Document[T]:
        return Document(doc.nodes[start:end])

    return take_slice


# Type predicates
def is_heading(node: Node) -> bool:
    """Check if node is a heading."""
    return isinstance(node, Heading)


def is_paragraph(node: Node) -> bool:
    """Check if node is a paragraph."""
    return isinstance(node, Paragraph)


def is_list(node: Node) -> bool:
    """Check if node is a list."""
    return isinstance(node, List)


def is_code_block(node: Node) -> bool:
    """Check if node is a code block."""
    return isinstance(node, CodeBlock)


def matches(pattern: str) -> Callable[[Node], bool]:
    """
    Create predicate that matches text content against pattern.

    For now, does simple substring matching.
    TODO: Add regex support.
    """

    def predicate(node: Node) -> bool:
        if isinstance(node, Heading):
            return pattern in node.text
        elif isinstance(node, Paragraph):
            return pattern in node.content
        elif isinstance(node, CodeBlock):
            return pattern in node.code
        return False

    return predicate


def contains(substring: str) -> Callable[[Node], bool]:
    """Alias for matches (more readable)."""
    return matches(substring)


# Structural transformations
def promote() -> Callable[[Document[Node]], Document[Node]]:
    """
    Promote heading levels (h3 -> h2).

    This is a morphism that preserves document structure.
    """

    def transform(doc: Document[Node]) -> Document[Node]:
        def promote_node(node: Node) -> Node:
            if isinstance(node, Heading):
                return node.promote()
            return node

        return doc.map(promote_node)

    return transform


def demote() -> Callable[[Document[Node]], Document[Node]]:
    """
    Demote heading levels (h2 -> h3).

    This is a morphism that preserves document structure.
    """

    def transform(doc: Document[Node]) -> Document[Node]:
        def demote_node(node: Node) -> Node:
            if isinstance(node, Heading):
                return node.demote()
            return node

        return doc.map(demote_node)

    return transform


# Type transformations
def to_ordered() -> Callable[[Document[Node]], Document[Node]]:
    """Convert lists to ordered."""

    def transform(doc: Document[Node]) -> Document[Node]:
        def convert_node(node: Node) -> Node:
            if isinstance(node, List):
                return node.to_ordered()
            return node

        return doc.map(convert_node)

    return transform


def to_unordered() -> Callable[[Document[Node]], Document[Node]]:
    """Convert lists to unordered."""

    def transform(doc: Document[Node]) -> Document[Node]:
        def convert_node(node: Node) -> Node:
            if isinstance(node, List):
                return node.to_unordered()
            return node

        return doc.map(convert_node)

    return transform


# Utility operations
def count() -> Callable[[Document[T]], int]:
    """Count nodes in document."""

    def counter(doc: Document[T]) -> int:
        return len(doc)

    return counter


def extract() -> Callable[[Document[T]], list[T]]:
    """Extract nodes as list."""

    def extractor(doc: Document[T]) -> list[T]:
        return list(doc.nodes)

    return extractor


# Convenient type-based selectors
heading = select(is_heading)
paragraph = select(is_paragraph)
list_node = select(is_list)
code_block = select(is_code_block)
