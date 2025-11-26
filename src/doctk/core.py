"""
Core abstractions for doctk.

Implements the fundamental Document and Node classes following category theory principles.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Generic, TypeVar

if TYPE_CHECKING:
    from doctk.identity import NodeId, Provenance, SourceSpan, ViewSourceMapping

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
    id: "NodeId | None" = None
    provenance: "Provenance | None" = None
    source_span: "SourceSpan | None" = None

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

    def _with_updates(
        self,
        level: int | None = None,
        text: str | None = None,
        children: list[Node] | None = None,
        metadata: dict[str, Any] | None = None,
        regenerate_id: bool = False,
    ) -> "Heading":
        """Create a new Heading with updated attributes."""
        import copy

        from doctk.identity import NodeId

        new_heading = Heading(
            level=level if level is not None else self.level,
            text=text if text is not None else self.text,
            children=children if children is not None else self.children,
            metadata=copy.deepcopy(metadata)
            if metadata is not None
            else copy.deepcopy(self.metadata),
            provenance=self.provenance.with_modification() if self.provenance else None,
            source_span=self.source_span,
        )
        new_heading.id = NodeId.from_node(new_heading) if regenerate_id else self.id
        return new_heading

    def with_text(self, text: str) -> "Heading":
        """
        Create new heading with different text (generates new NodeId).

        Text is part of canonical form, so changing it generates a new ID.

        Args:
            text: New heading text

        Returns:
            New Heading with updated text and new NodeId
        """
        return self._with_updates(text=text, regenerate_id=True)

    def with_metadata(self, metadata: dict[str, Any]) -> "Heading":
        """
        Create new heading with different metadata (preserves NodeId).

        Metadata is NOT part of canonical form, so ID is preserved.

        Args:
            metadata: New metadata dictionary

        Returns:
            New Heading with updated metadata but same NodeId
        """
        return self._with_updates(metadata=metadata)

    def promote(self) -> "Heading":
        """
        Decrease heading level (h3 -> h2). Identity if already h1.

        Level is NOT part of canonical form, so NodeId is preserved.
        """
        return self._with_updates(level=max(1, self.level - 1))

    def demote(self) -> "Heading":
        """
        Increase heading level (h2 -> h3). Identity if already h6.

        Level is NOT part of canonical form, so NodeId is preserved.
        """
        return self._with_updates(level=min(6, self.level + 1))


@dataclass
class Paragraph(Node):
    """Paragraph node."""

    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    id: "NodeId | None" = None
    provenance: "Provenance | None" = None
    source_span: "SourceSpan | None" = None

    def accept(self, visitor: "NodeVisitor") -> Any:
        return visitor.visit_paragraph(self)

    def to_dict(self) -> dict[str, Any]:
        return {"type": "paragraph", "content": self.content, "metadata": self.metadata}

    def _with_updates(
        self,
        content: str | None = None,
        metadata: dict[str, Any] | None = None,
        regenerate_id: bool = False,
    ) -> "Paragraph":
        """Create a new Paragraph with updated attributes."""
        import copy

        from doctk.identity import NodeId

        new_paragraph = Paragraph(
            content=content if content is not None else self.content,
            metadata=copy.deepcopy(metadata)
            if metadata is not None
            else copy.deepcopy(self.metadata),
            provenance=self.provenance.with_modification() if self.provenance else None,
            source_span=self.source_span,
        )
        new_paragraph.id = NodeId.from_node(new_paragraph) if regenerate_id else self.id
        return new_paragraph

    def with_content(self, content: str) -> "Paragraph":
        """
        Create new paragraph with different content (generates new NodeId).

        Content is part of canonical form, so changing it generates a new ID.

        Args:
            content: New paragraph content

        Returns:
            New Paragraph with updated content and new NodeId
        """
        return self._with_updates(content=content, regenerate_id=True)

    def with_metadata(self, metadata: dict[str, Any]) -> "Paragraph":
        """
        Create new paragraph with different metadata (preserves NodeId).

        Metadata is NOT part of canonical form, so ID is preserved.

        Args:
            metadata: New metadata dictionary

        Returns:
            New Paragraph with updated metadata but same NodeId
        """
        return self._with_updates(metadata=metadata)


@dataclass
class List(Node):
    """List node (ordered or unordered)."""

    ordered: bool
    items: list[Node]
    metadata: dict[str, Any] = field(default_factory=dict)
    id: "NodeId | None" = None
    provenance: "Provenance | None" = None
    source_span: "SourceSpan | None" = None

    def accept(self, visitor: "NodeVisitor") -> Any:
        return visitor.visit_list(self)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "list",
            "ordered": self.ordered,
            "items": [item.to_dict() for item in self.items],
            "metadata": self.metadata,
        }

    def _with_updates(
        self,
        ordered: bool | None = None,
        items: list[Node] | None = None,
        metadata: dict[str, Any] | None = None,
        regenerate_id: bool = False,
    ) -> "List":
        """Create a new List with updated attributes."""
        import copy

        from doctk.identity import NodeId

        new_list = List(
            ordered=ordered if ordered is not None else self.ordered,
            items=items if items is not None else self.items,
            metadata=copy.deepcopy(metadata)
            if metadata is not None
            else copy.deepcopy(self.metadata),
            provenance=self.provenance.with_modification() if self.provenance else None,
            source_span=self.source_span,
        )
        new_list.id = NodeId.from_node(new_list) if regenerate_id else self.id
        return new_list

    def to_ordered(self) -> "List":
        """
        Convert to ordered list (preserves NodeId).

        List type (ordered/unordered) is NOT part of canonical form.
        """
        return self._with_updates(ordered=True)

    def to_unordered(self) -> "List":
        """
        Convert to unordered list (preserves NodeId).

        List type (ordered/unordered) is NOT part of canonical form.
        """
        return self._with_updates(ordered=False)

    def with_metadata(self, metadata: dict[str, Any]) -> "List":
        """
        Create new list with different metadata (preserves NodeId).

        Metadata is NOT part of canonical form, so ID is preserved.

        Args:
            metadata: New metadata dictionary

        Returns:
            New List with updated metadata but same NodeId
        """
        return self._with_updates(metadata=metadata)


@dataclass
class ListItem(Node):
    """List item node."""

    content: list[Node]
    metadata: dict[str, Any] = field(default_factory=dict)
    id: "NodeId | None" = None
    provenance: "Provenance | None" = None
    source_span: "SourceSpan | None" = None

    def accept(self, visitor: "NodeVisitor") -> Any:
        return visitor.visit_list_item(self)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "list_item",
            "content": [node.to_dict() for node in self.content],
            "metadata": self.metadata,
        }

    def _with_updates(
        self,
        content: list[Node] | None = None,
        metadata: dict[str, Any] | None = None,
        regenerate_id: bool = False,
    ) -> "ListItem":
        """Create a new ListItem with updated attributes."""
        import copy

        from doctk.identity import NodeId

        new_list_item = ListItem(
            content=content if content is not None else self.content,
            metadata=copy.deepcopy(metadata)
            if metadata is not None
            else copy.deepcopy(self.metadata),
            provenance=self.provenance.with_modification() if self.provenance else None,
            source_span=self.source_span,
        )
        new_list_item.id = NodeId.from_node(new_list_item) if regenerate_id else self.id
        return new_list_item

    def with_content(self, content: list[Node]) -> "ListItem":
        """
        Create new list item with different content (generates new NodeId).

        Content is part of canonical form, so changing it generates a new ID.

        Args:
            content: New list item content nodes

        Returns:
            New ListItem with updated content and new NodeId
        """
        return self._with_updates(content=content, regenerate_id=True)

    def with_metadata(self, metadata: dict[str, Any]) -> "ListItem":
        """
        Create new list item with different metadata (preserves NodeId).

        Metadata is NOT part of canonical form, so ID is preserved.

        Args:
            metadata: New metadata dictionary

        Returns:
            New ListItem with updated metadata but same NodeId
        """
        return self._with_updates(metadata=metadata)


@dataclass
class CodeBlock(Node):
    """Code block node."""

    code: str
    language: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    id: "NodeId | None" = None
    provenance: "Provenance | None" = None
    source_span: "SourceSpan | None" = None

    def accept(self, visitor: "NodeVisitor") -> Any:
        return visitor.visit_code_block(self)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "code_block",
            "code": self.code,
            "language": self.language,
            "metadata": self.metadata,
        }

    def _with_updates(
        self,
        code: str | None = None,
        language: str | None = None,
        metadata: dict[str, Any] | None = None,
        regenerate_id: bool = False,
    ) -> "CodeBlock":
        """Create a new CodeBlock with updated attributes."""
        import copy

        from doctk.identity import NodeId

        new_code_block = CodeBlock(
            code=code if code is not None else self.code,
            language=language if language is not None else self.language,
            metadata=copy.deepcopy(metadata)
            if metadata is not None
            else copy.deepcopy(self.metadata),
            provenance=self.provenance.with_modification() if self.provenance else None,
            source_span=self.source_span,
        )
        new_code_block.id = NodeId.from_node(new_code_block) if regenerate_id else self.id
        return new_code_block

    def with_code(self, code: str) -> "CodeBlock":
        """
        Create new code block with different code (generates new NodeId).

        Code is part of canonical form, so changing it generates a new ID.

        Args:
            code: New code content

        Returns:
            New CodeBlock with updated code and new NodeId
        """
        return self._with_updates(code=code, regenerate_id=True)

    def with_language(self, language: str | None) -> "CodeBlock":
        """
        Create new code block with different language (generates new NodeId).

        Language is part of canonical form, so changing it generates a new ID.

        Args:
            language: New language identifier

        Returns:
            New CodeBlock with updated language and new NodeId
        """
        return self._with_updates(language=language, regenerate_id=True)

    def with_metadata(self, metadata: dict[str, Any]) -> "CodeBlock":
        """
        Create new code block with different metadata (preserves NodeId).

        Metadata is NOT part of canonical form, so ID is preserved.

        Args:
            metadata: New metadata dictionary

        Returns:
            New CodeBlock with updated metadata but same NodeId
        """
        return self._with_updates(metadata=metadata)


@dataclass
class BlockQuote(Node):
    """Block quote node."""

    content: list[Node]
    metadata: dict[str, Any] = field(default_factory=dict)
    id: "NodeId | None" = None
    provenance: "Provenance | None" = None
    source_span: "SourceSpan | None" = None

    def accept(self, visitor: "NodeVisitor") -> Any:
        return visitor.visit_block_quote(self)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "block_quote",
            "content": [node.to_dict() for node in self.content],
            "metadata": self.metadata,
        }

    def _with_updates(
        self,
        content: list[Node] | None = None,
        metadata: dict[str, Any] | None = None,
        regenerate_id: bool = False,
    ) -> "BlockQuote":
        """Create a new BlockQuote with updated attributes."""
        import copy

        from doctk.identity import NodeId

        new_blockquote = BlockQuote(
            content=content if content is not None else self.content,
            metadata=copy.deepcopy(metadata)
            if metadata is not None
            else copy.deepcopy(self.metadata),
            provenance=self.provenance.with_modification() if self.provenance else None,
            source_span=self.source_span,
        )
        new_blockquote.id = NodeId.from_node(new_blockquote) if regenerate_id else self.id
        return new_blockquote

    def with_metadata(self, metadata: dict[str, Any]) -> "BlockQuote":
        """
        Create new block quote with different metadata (preserves NodeId).

        Metadata is NOT part of canonical form, so ID is preserved.

        Args:
            metadata: New metadata dictionary

        Returns:
            New BlockQuote with updated metadata but same NodeId
        """
        return self._with_updates(metadata=metadata)


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
        self._id_index: dict[NodeId, T] = {}
        self._view_mappings: list[ViewSourceMapping] = []
        self._build_id_index()

    def _build_id_index(self) -> None:
        """
        Build index of all nodes in the document tree by their IDs for O(1) lookup.

        Recursively traverses the entire document tree to index all nodes,
        including nested nodes within Lists, ListItems, and BlockQuotes.
        """
        self._id_index.clear()
        for node in self.nodes:
            self._index_node_recursive(node)

    def _index_node_recursive(self, node: Any) -> None:
        """
        Recursively index a node and all its children.

        Args:
            node: Node to index (along with all descendants)
        """
        # Index this node if it has an ID
        if hasattr(node, "id") and node.id is not None:
            self._id_index[node.id] = node

        # Recursively index children based on node type
        if hasattr(node, "children") and node.children:
            # Heading nodes have children
            for child in node.children:
                self._index_node_recursive(child)
        elif hasattr(node, "items") and node.items:
            # List nodes have items
            for item in node.items:
                self._index_node_recursive(item)
        elif hasattr(node, "content") and isinstance(node.content, list):
            # ListItem and BlockQuote nodes have content lists
            for child in node.content:
                self._index_node_recursive(child)

    def find_node(self, node_id: "NodeId") -> T | None:
        """
        Find any node in the document tree by ID with O(1) lookup.

        Searches all nodes in the tree, including nested nodes within
        Lists, ListItems, BlockQuotes, and Heading children.

        Args:
            node_id: NodeId to search for

        Returns:
            Node with matching ID, or None if not found

        Examples:
            >>> doc = Document([heading1, heading2])
            >>> node = doc.find_node(heading1.id)
            >>> assert node == heading1
            >>> # Also works for nested nodes
            >>> nested_item = doc.find_node(list_item.id)
            >>> assert nested_item == list_item
        """
        return self._id_index.get(node_id)

    def find_nodes(self, predicate: Callable[[T], bool]) -> "Document[T]":
        """
        Find all nodes matching predicate with O(n) search.

        Args:
            predicate: Function that returns True for matching nodes

        Returns:
            New Document containing matching nodes

        Examples:
            >>> doc = Document([heading1, paragraph1, heading2])
            >>> headings = doc.find_nodes(lambda n: isinstance(n, Heading))
            >>> assert len(headings.nodes) == 2
        """
        return Document([node for node in self.nodes if predicate(node)])

    def add_view_mapping(self, mapping: "ViewSourceMapping") -> None:
        """
        Register a view-to-source mapping.

        Args:
            mapping: ViewSourceMapping to add
        """
        self._view_mappings.append(mapping)

    def find_source_position(self, view_line: int, view_column: int) -> tuple[str, int, int] | None:
        """
        Find the source position for a given view position.

        Args:
            view_line: Line number in view (0-indexed)
            view_column: Column number in view (0-indexed)

        Returns:
            Tuple of (source_file, source_line, source_column) or None if not mapped
        """
        for mapping in self._view_mappings:
            if mapping.view_span.contains(view_line, view_column):
                return mapping.project_to_source(view_line, view_column)
        return None

    # Functor operations
    def map(self, f: Callable[[T], U]) -> "Document[U]":
        """
        Apply transformation to each node.

        Functor law: map(id) = id
        Functor law: map(f . g) = map(f) . map(g)
        """
        result = Document([f(node) for node in self.nodes])
        result._build_id_index()
        return result

    def filter(self, predicate: Callable[[T], bool]) -> "Document[T]":
        """
        Filter nodes by predicate (subset selection).

        This is set-theoretic filtering.
        """
        result = Document([node for node in self.nodes if predicate(node)])
        result._build_id_index()
        return result

    # Monad operations
    def flatmap(self, f: Callable[[T], "Document[U]"]) -> "Document[U]":
        """
        Map and flatten.

        Monad law: flatmap(return) = id
        Monad law: return(x).flatmap(f) = f(x)
        Monad law: m.flatmap(f).flatmap(g) = m.flatmap(lambda x: f(x).flatmap(g))
        """
        result_nodes = []
        for node in self.nodes:
            result_nodes.extend(f(node).nodes)
        result = Document(result_nodes)
        result._build_id_index()
        return result

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
