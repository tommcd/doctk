"""
Composable operations for document transformation.

Operations are morphisms in the document category.
They compose naturally following category theory laws.
"""

import re
from collections.abc import Callable
from typing import Any, TypeVar

from doctk.core import CodeBlock, Document, Heading, List, Node, Paragraph

T = TypeVar("T")
U = TypeVar("U")


class Selector:
    """
    A named set of nodes, usable both as a predicate and as an operation.

    Set-theoretically, a selector denotes a set S of nodes:
    - Applied to a node, it is the characteristic function: heading(node) -> bool
    - Applied to a document (directly or piped), it selects the subset S ∩ Doc:
      doc | heading

    This duality makes the documented forms equivalent:
        doc | heading
        doc | select(heading)

    Example:
        >>> doc = Document.from_string("# Title\\n\\nText.\\n")
        >>> len((doc | heading).nodes)
        1
        >>> heading(doc.nodes[0])
        True
    """

    def __init__(self, predicate: Callable[[Node], bool], name: str = "selector"):
        self._predicate = predicate
        self.__name__ = name

    def __call__(self, target: "Document[Node] | Node") -> "Document[Node] | bool":
        if isinstance(target, Document):
            return target.filter(self._predicate)
        return self._predicate(target)

    def __repr__(self) -> str:
        return f"Selector({self.__name__})"


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
def select(predicate: "Callable[[Node], bool] | Selector") -> Selector:
    """
    Select nodes matching predicate.

    This is set-theoretic filtering: { x ∈ Doc | predicate(x) }

    Accepts a plain predicate or an existing Selector; select is idempotent,
    so select(heading) is heading.
    """
    if isinstance(predicate, Selector):
        return predicate
    return Selector(predicate, getattr(predicate, "__name__", "selector"))


def where(**conditions: Any) -> Selector:
    """
    Convenient predicate builder for common conditions.

    Examples:
        where(level=2)
        where(ordered=True)
        where(text="Introduction")
    """

    def predicate(node: Node) -> bool:
        for key, value in conditions.items():
            if not hasattr(node, key):
                return False
            if getattr(node, key) != value:
                return False
        return True

    condition_str = ", ".join(f"{k}={v!r}" for k, v in conditions.items())
    return Selector(predicate, f"where({condition_str})")


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


def matches(pattern: str) -> Selector:
    """
    Select nodes whose text content matches a regular expression.

    Uses re.search, so plain text patterns match as substrings anywhere in
    the node's text. Use contains() for literal substring matching without
    regex semantics.

    Examples:
        doc | matches(r"^Introduction")   # headings/paragraphs starting with it
        doc | matches("TODO")             # containing TODO anywhere
    """
    compiled = re.compile(pattern)

    def predicate(node: Node) -> bool:
        if isinstance(node, Heading):
            return compiled.search(node.text) is not None
        elif isinstance(node, Paragraph):
            return compiled.search(node.content) is not None
        elif isinstance(node, CodeBlock):
            return compiled.search(node.code) is not None
        return False

    return Selector(predicate, f"matches({pattern!r})")


def contains(substring: str) -> Selector:
    """Select nodes whose text content contains the literal substring."""
    return matches(re.escape(substring))


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


# Structural moves (nest, unnest, move_up, move_down) relocate one section
# addressed by node id, so they live in doctk.integration.StructureOperations
# and the DSL, not in this uniform-transformation pipeline vocabulary.


# Convenient type-based selectors
heading = Selector(is_heading, "heading")
paragraph = Selector(is_paragraph, "paragraph")
list_node = Selector(is_list, "list_node")
code_block = Selector(is_code_block, "code_block")
