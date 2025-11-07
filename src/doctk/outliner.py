"""
Outliner functionality for viewing document structure.

Displays hierarchical document structure with beautiful formatting using Rich.
"""

from typing import Any

from rich.console import Console
from rich.tree import Tree

from doctk.core import (
    BlockQuote,
    CodeBlock,
    Document,
    Heading,
    List,
    ListItem,
    Node,
    NodeVisitor,
    Paragraph,
)


class OutlinerVisitor(NodeVisitor):
    """Visitor that builds outline tree."""

    def __init__(self, tree: Tree, show_content: bool = False, max_depth: int | None = None):
        self.tree = tree
        self.show_content = show_content
        self.max_depth = max_depth
        self.current_depth = 0

    def visit_heading(self, node: Heading) -> Tree:
        """Visit heading and add to tree."""
        # Use ASCII-safe icons for Windows console compatibility
        icon = "#"
        if node.level == 1:
            icon = "##"
        elif node.level == 2:
            icon = "##"
        elif node.level == 3:
            icon = "###"

        label = f"{icon} [bold]H{node.level}[/bold]: {node.text}"
        branch = self.tree.add(label)

        # Add children if any
        if node.children and (self.max_depth is None or self.current_depth < self.max_depth):
            self.current_depth += 1
            for child in node.children:
                visitor = OutlinerVisitor(branch, self.show_content, self.max_depth)
                visitor.current_depth = self.current_depth
                child.accept(visitor)
            self.current_depth -= 1

        return branch

    def visit_paragraph(self, node: Paragraph) -> Tree:
        """Visit paragraph and add to tree."""
        content = node.content[:50] + "..." if len(node.content) > 50 else node.content
        label = "P Paragraph"
        if self.show_content:
            label += f": [dim]{content}[/dim]"
        return self.tree.add(label)

    def visit_list(self, node: List) -> Tree:
        """Visit list and add to tree."""
        list_type = "ordered" if node.ordered else "unordered"
        icon = "1." if node.ordered else "*"
        label = f"{icon} List ({list_type}, {len(node.items)} items)"
        branch = self.tree.add(label)

        # Add items
        if self.max_depth is None or self.current_depth < self.max_depth:
            self.current_depth += 1
            for item in node.items:
                visitor = OutlinerVisitor(branch, self.show_content, self.max_depth)
                visitor.current_depth = self.current_depth
                item.accept(visitor)
            self.current_depth -= 1

        return branch

    def visit_list_item(self, node: ListItem) -> Tree:
        """Visit list item and add to tree."""
        label = "> Item"
        branch = self.tree.add(label)

        # Add content
        if self.max_depth is None or self.current_depth < self.max_depth:
            self.current_depth += 1
            for child in node.content:
                visitor = OutlinerVisitor(branch, self.show_content, self.max_depth)
                visitor.current_depth = self.current_depth
                child.accept(visitor)
            self.current_depth -= 1

        return branch

    def visit_code_block(self, node: CodeBlock) -> Tree:
        """Visit code block and add to tree."""
        lang = node.language or "plain"
        lines = node.code.count("\n") + 1
        label = f"``` Code block ({lang}, {lines} lines)"
        return self.tree.add(label)

    def visit_block_quote(self, node: BlockQuote) -> Tree:
        """Visit block quote and add to tree."""
        label = f'> Block quote ({len(node.content)} blocks)'
        branch = self.tree.add(label)

        # Add content
        if self.max_depth is None or self.current_depth < self.max_depth:
            self.current_depth += 1
            for child in node.content:
                visitor = OutlinerVisitor(branch, self.show_content, self.max_depth)
                visitor.current_depth = self.current_depth
                child.accept(visitor)
            self.current_depth -= 1

        return branch


def outline(
    doc: Document[Node],
    show_content: bool = False,
    max_depth: int | None = None,
    console: Console | None = None,
) -> None:
    """
    Display document outline.

    Args:
        doc: Document to outline
        show_content: Show preview of text content
        max_depth: Maximum depth to display (None for unlimited)
        console: Rich console to use (creates new if None)
    """
    if console is None:
        console = Console()

    tree = Tree(f"Document ({len(doc.nodes)} top-level nodes)")

    for node in doc.nodes:
        visitor = OutlinerVisitor(tree, show_content, max_depth)
        node.accept(visitor)

    console.print(tree)


def outline_headings_only(doc: Document[Node], console: Console | None = None) -> None:
    """
    Display outline of headings only (simplified view).

    Args:
        doc: Document to outline
        console: Rich console to use (creates new if None)
    """
    if console is None:
        console = Console()

    from doctk.operations import heading, select

    # Filter to headings only
    headings_doc = doc | select(lambda n: isinstance(n, Heading))

    if len(headings_doc) == 0:
        console.print("[dim]No headings found in document[/dim]")
        return

    tree = Tree(f"Document Structure ({len(headings_doc.nodes)} headings)")

    # Build hierarchical tree based on heading levels
    stack: list[tuple[int, Tree]] = [(0, tree)]  # (level, tree_node)

    for node in headings_doc.nodes:
        if not isinstance(node, Heading):
            continue

        # Pop stack until we find parent level
        while len(stack) > 1 and stack[-1][0] >= node.level:
            stack.pop()

        # Add to current parent
        parent_tree = stack[-1][1]
        label = f"[bold]H{node.level}[/bold]: {node.text}"
        branch = parent_tree.add(label)

        # Push onto stack for potential children
        stack.append((node.level, branch))

    console.print(tree)
